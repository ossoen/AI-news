#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补全 txt 中缺失的章节 - 根据进度文件中的已完成 URL 重新下载内容
"""
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import json
from urllib.parse import urljoin

BASE_URL = "https://www.66kxs.net/book/3993/3993372/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

OUTPUT_FILE = "凡人修仙记.txt"
PROGRESS_FILE = "download_progress.json"
DELAY = 0.4


def fetch_html(url, retries=3):
    for i in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.encoding = "gbk"
            return resp.text
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(2)


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


def extract_chapter_number(title):
    m = re.search(r"第(\d+)章", title)
    return int(m.group(1)) if m else 99999


def get_chapter_content(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    content_div = (
        soup.find("div", id="content")
        or soup.find("div", class_="content")
        or soup.find("div", id="article")
        or soup.find("div", class_="read-content")
        or soup.find("div", id="booktext")
    )
    if not content_div:
        max_len = 0
        for div in soup.find_all("div"):
            text_len = len(div.get_text())
            if text_len > max_len:
                max_len = text_len
                content_div = div
    if content_div:
        for tag in content_div.find_all(["script", "style", "a", "div"]):
            t = tag.get_text()
            if any(k in t for k in ["下一章", "上一章", "返回目录", "加入书签"]):
                tag.decompose()
        text = content_div.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
    return ""


def main():
    print("=" * 60)
    print("补全缺失章节")
    print("=" * 60)

    # 获取章节列表
    print("\n[1/3] 获取章节目录...")
    chapters = get_chapter_list()
    chapters.sort(key=lambda c: extract_chapter_number(c["title"]))
    print(f"共 {len(chapters)} 章")

    # 读取进度文件（已完成下载但可能未写入txt的URL）
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        progress = json.load(f)
    completed_urls = set(progress.get("completed", []))
    print(f"进度文件记录已完成: {len(completed_urls)} 章")

    # 读取 txt 已有内容
    print("\n[2/3] 扫描 txt 文件已有章节...")
    existing_titles = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            txt_content = f.read()
        for ch in chapters:
            if ch["title"] in txt_content:
                existing_titles.add(ch["title"])
    print(f"txt 中已有: {len(existing_titles)} 章")

    # 需要补的：进度中已完成但 txt 中没有的
    need_fix = [ch for ch in chapters if ch["url"] in completed_urls and ch["title"] not in existing_titles]
    print(f"需要补全: {len(need_fix)} 章")

    if not need_fix:
        print("无需补全！")
        return

    print(f"\n[3/3] 开始补全，预计约 {len(need_fix) * DELAY / 60:.1f} 分钟...")
    success = 0
    failed = 0
    start = time.time()

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for i, ch in enumerate(need_fix, 1):
            try:
                content = get_chapter_content(ch["url"])
                f.write(f"\n{'='*50}\n{ch['title']}\n{'='*50}\n\n{content}\n\n")
                success += 1
                if i % 20 == 0:
                    f.flush()
                    elapsed = time.time() - start
                    speed = i / elapsed if elapsed > 0 else 0
                    print(f"  [{i}/{len(need_fix)}] 已补 {success} 章 | 速度 {speed:.1f}章/分")
                time.sleep(DELAY)
            except Exception as e:
                failed += 1
                print(f"  ✗ 失败: {ch['title']} - {e}")
                time.sleep(2)

    elapsed = time.time() - start
    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"\n完成!")
    print(f"文件: {os.path.abspath(OUTPUT_FILE)}")
    print(f"大小: {file_size / 1024 / 1024:.2f} MB")
    print(f"成功: {success}, 失败: {failed}")
    print(f"耗时: {elapsed / 60:.1f} 分钟")


if __name__ == "__main__":
    main()
