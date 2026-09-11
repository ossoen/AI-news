#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重建完整小说文件 - 按顺序合并已有内容和下载缺失章节
"""
import requests
from bs4 import BeautifulSoup
import time
import os
import re
from urllib.parse import urljoin

BASE_URL = "https://www.66kxs.net/book/3993/3993372/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

OLD_FILE = "凡人修仙记.txt"
NEW_FILE = "凡人修仙记_full.txt"
DELAY = 0.35


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
    print("重建完整小说文件")
    print("=" * 60)

    print("\n[1/4] 获取章节目录...")
    chapters = get_chapter_list()
    chapters.sort(key=lambda c: extract_chapter_number(c["title"]))
    print(f"共 {len(chapters)} 章")

    print("\n[2/4] 扫描已有内容...")
    existing = {}
    if os.path.exists(OLD_FILE):
        with open(OLD_FILE, "r", encoding="utf-8") as f:
            text = f.read()
        # 按章节分割
        parts = re.split(r"(={50}\n第\d+章[^\n]*\n={50})", text)
        current_title = None
        for part in parts:
            m = re.match(r"={50}\n(第\d+章[^\n]*)\n={50}", part)
            if m:
                current_title = m.group(1).strip()
            elif current_title and part.strip():
                existing[current_title] = part.strip()
    print(f"已有章节: {len(existing)}")

    # 检查哪些章节缺失
    need_download = [ch for ch in chapters if ch["title"] not in existing]
    print(f"需要下载: {len(need_download)}")

    print(f"\n[3/4] 开始重建文件，预计约 {len(need_download) * DELAY / 60:.1f} 分钟...")

    with open(NEW_FILE, "w", encoding="utf-8") as f:
        f.write("凡人修仙记\n作者：梧桐悠悠\n来源：66kxs.net\n")
        f.write("=" * 50 + "\n\n")

        success = 0
        failed = 0
        start = time.time()

        for i, ch in enumerate(chapters, 1):
            title = ch["title"]
            if title in existing:
                content = existing[title]
            else:
                try:
                    content = get_chapter_content(ch["url"])
                    success += 1
                    if success % 20 == 0:
                        elapsed = time.time() - start
                        speed = success / elapsed if elapsed > 0 else 0
                        remain = (len(need_download) - success) * DELAY / 60
                        print(f"  [{i}/{len(chapters)}] 已下载 {success}/{len(need_download)} | 速度 {speed:.1f}章/分 | 剩余 {remain:.1f} 分钟")
                    time.sleep(DELAY)
                except Exception as e:
                    content = f"【下载失败: {e}】"
                    failed += 1
                    print(f"  ✗ 失败: {title}")
                    time.sleep(2)

            f.write(f"\n{'='*50}\n{title}\n{'='*50}\n\n{content}\n\n")

    # 替换旧文件
    if os.path.exists(OLD_FILE):
        os.remove(OLD_FILE)
    os.rename(NEW_FILE, OLD_FILE)

    file_size = os.path.getsize(OLD_FILE)
    elapsed = time.time() - start
    print(f"\n[4/4] 完成!")
    print(f"文件: {os.path.abspath(OLD_FILE)}")
    print(f"大小: {file_size / 1024 / 1024:.2f} MB")
    print(f"成功: {success}, 失败: {failed}")
    print(f"耗时: {elapsed / 60:.1f} 分钟")


if __name__ == "__main__":
    main()
