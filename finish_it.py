#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 merged 文件继续，下载剩余缺失章节
"""
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import json
from urllib.parse import urljoin
import shutil

BASE_URL = "https://www.66kxs.net/book/3993/3993372/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

MERGED = "凡人修仙记_merged.txt"
FINAL = "凡人修仙记.txt"
BATCH_STATE = "batch_state.json"
DELAY = 0.35


def fetch_html(url, retries=2):
    for i in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.encoding = "gbk"
            return resp.text
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(1)


def get_chapter_list():
    html = fetch_html(BASE_URL)
    soup = BeautifulSoup(html, "html.parser")
    chapters = []
    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if re.match(r"/book/3993/3993372/\d+\.html", href):
            full_url = urljoin(BASE_URL, href)
            chapters.append({"title": text, "url": full_url})
    seen = set()
    unique = []
    for c in chapters:
        if c["url"] not in seen:
            seen.add(c["url"])
            unique.append(c)
    return unique


def extract_num(title):
    m = re.search(r"第(\d+)章", title)
    return int(m.group(1)) if m else 99999


def get_content(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", id="content") or soup.find("div", class_="content")
    if not div:
        max_len = 0
        for d in soup.find_all("div"):
            if len(d.get_text()) > max_len:
                max_len = len(d.get_text())
                div = d
    if div:
        for tag in div.find_all(["script", "style", "a", "div"]):
            t = tag.get_text()
            if any(k in t for k in ["下一章", "上一章", "返回目录", "加入书签"]):
                tag.decompose()
        text = div.get_text(separator="\n", strip=True)
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return ""


def main():
    print("=" * 60)
    print("从 merged 文件继续补全")
    print("=" * 60)

    chapters = get_chapter_list()
    chapters.sort(key=lambda c: extract_num(c["title"]))
    print(f"网站共 {len(chapters)} 章")

    # 读取 merged 文件中的已有章节
    existing = set()
    with open(MERGED, "r", encoding="utf-8") as f:
        txt = f.read()
    for ch in chapters:
        if ch["title"] in txt:
            existing.add(ch["title"])
    print(f"merged 中已有: {len(existing)} 章")

    # 复制 merged 到最终文件
    shutil.copy(MERGED, FINAL)
    print(f"已复制到 {FINAL}")

    missing = [ch for ch in chapters if ch["title"] not in existing]
    print(f"缺失: {len(missing)} 章")

    if not missing:
        print("无需补全!")
        return

    print(f"\n开始下载，预计约 {len(missing) * DELAY / 60:.1f} 分钟...")
    success = 0
    failed = 0
    start = time.time()

    with open(FINAL, "a", encoding="utf-8") as f:
        for i, ch in enumerate(missing, 1):
            try:
                content = get_content(ch["url"])
                f.write(f"\n{'='*50}\n{ch['title']}\n{'='*50}\n\n{content}\n\n")
                success += 1
                if i % 50 == 0:
                    f.flush()
                    elapsed = time.time() - start
                    speed = i / elapsed if elapsed > 0 else 0
                    remain = (len(missing) - i) * DELAY / 60
                    print(f"  [{i}/{len(missing)}] 已下载 {success} 章 | 速度 {speed:.1f}章/分 | 剩余 {remain:.1f} 分钟")
                time.sleep(DELAY)
            except Exception as e:
                failed += 1
                print(f"  ✗ {ch['title']}: {e}")
                time.sleep(1)

    # 验证
    with open(FINAL, "r", encoding="utf-8") as f:
        text = f.read()
    chs = set(re.findall(r'第\d+章', text))
    unique = len(chs)

    print(f"\n完成!")
    print(f"文件: {os.path.abspath(FINAL)}")
    print(f"大小: {os.path.getsize(FINAL) / 1024 / 1024:.2f} MB")
    print(f"成功: {success}, 失败: {failed}")
    print(f"唯一章节: {unique}/1982")


if __name__ == "__main__":
    main()
