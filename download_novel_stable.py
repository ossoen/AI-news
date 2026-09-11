#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载 66kxs.net 小说 - 稳健单线程版，支持断点续传
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

OUTPUT_FILE = "凡人修仙记.txt"
PROGRESS_FILE = "download_progress.json"
DELAY = 0.4  # 每章延迟秒数


def fetch_html(url, retries=3):
    for i in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.encoding = "gbk"
            return resp.text
        except Exception as e:
            print(f"    请求失败 ({i+1}/{retries}): {e}")
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
    # 去重
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


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed": []}


def save_progress(completed):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"completed": completed}, f, ensure_ascii=False)


def ensure_header():
    if not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) < 100:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("凡人修仙记\n作者：梧桐悠悠\n来源：66kxs.net\n")
            f.write("=" * 50 + "\n\n")
        return True
    return False


def write_chapter(f, title, content):
    f.write(f"\n{'='*50}\n{title}\n{'='*50}\n\n{content}\n\n")


def main():
    print("=" * 60)
    print("小说下载器 - 凡人修仙记 (稳健版)")
    print("=" * 60)

    print("\n[1/3] 获取章节目录...")
    chapters = get_chapter_list()
    chapters.sort(key=lambda c: extract_chapter_number(c["title"]))
    total = len(chapters)
    print(f"共 {total} 章")

    progress = load_progress()
    completed_urls = set(progress.get("completed", []))
    print(f"已下载: {len(completed_urls)} 章, 待下载: {total - len(completed_urls)} 章")

    ensure_header()

    # 先扫描 txt 里已有的章节，避免重复写入
    existing_urls = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            txt = f.read()
        # 简单判断：如果章节标题在文件中就认为已存在
        for ch in chapters:
            if ch["title"] in txt:
                existing_urls.add(ch["url"])
    print(f"TXT中已有: {len(existing_urls)} 章")

    # 合并已完成的和已写入的
    all_done = completed_urls | existing_urls

    print(f"\n[2/3] 开始下载，共需处理 {total - len(all_done)} 章...")
    print(f"每章延迟 {DELAY} 秒，预计约 {(total - len(all_done)) * DELAY / 60:.1f} 分钟\n")

    start = time.time()
    success = 0
    failed = 0
    failed_list = []

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for i, ch in enumerate(chapters, 1):
            if ch["url"] in all_done:
                continue

            try:
                content = get_chapter_content(ch["url"])
                write_chapter(f, ch["title"], content)
                completed_urls.add(ch["url"])
                success += 1

                if success % 20 == 0:
                    f.flush()
                    save_progress(list(completed_urls))
                    elapsed = time.time() - start
                    speed = success / elapsed if elapsed > 0 else 0
                    remain = (total - len(completed_urls)) * DELAY / 60
                    print(f"  [{i}/{total}] 已处理 {success} 章 | 速度 {speed:.1f}章/分 | 预计剩余 {remain:.1f} 分钟")

                time.sleep(DELAY)

            except Exception as e:
                failed += 1
                failed_list.append((ch["title"], str(e)))
                print(f"  ✗ 失败: {ch['title']} - {e}")
                time.sleep(2)

    # 最终保存
    save_progress(list(completed_urls))

    elapsed = time.time() - start
    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"\n[3/3] 完成!")
    print(f"文件: {os.path.abspath(OUTPUT_FILE)}")
    print(f"大小: {file_size / 1024 / 1024:.2f} MB")
    print(f"成功: {success}, 失败: {failed}, 总计完成: {len(completed_urls)}/{total}")
    print(f"耗时: {elapsed / 60:.1f} 分钟")

    if failed_list:
        print(f"\n失败的 {min(10, len(failed_list))} 章:")
        for title, err in failed_list[:10]:
            print(f"  - {title}: {err}")


if __name__ == "__main__":
    main()
