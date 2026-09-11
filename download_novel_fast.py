#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载 66kxs.net 小说到本地 - 多线程加速版
"""
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import json
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

BASE_URL = "https://www.66kxs.net/book/3993/3993372/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

OUTPUT_FILE = "凡人修仙记.txt"
PROGRESS_FILE = "download_progress.json"
MAX_WORKERS = 15  # 并发数

# 线程安全的锁
lock = threading.Lock()


def fetch_html(url, retries=3):
    for i in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.encoding = "gbk"
            return resp.text
        except Exception as e:
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


def extract_chapter_number(title):
    m = re.search(r"第(\d+)章", title)
    if m:
        return int(m.group(1))
    return 99999


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
    with lock:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump({"completed": completed}, f, ensure_ascii=False)


def download_one(chapter, completed_set, counter, total):
    url = chapter["url"]
    if url in completed_set:
        return None
    try:
        content = get_chapter_content(url)
        with lock:
            counter[0] += 1
            c = counter[0]
        if c % 50 == 0:
            print(f"  进度: {c}/{total}")
        return {"title": chapter["title"], "url": url, "content": content}
    except Exception as e:
        with lock:
            counter[0] += 1
        print(f"  ✗ 失败: {chapter['title']} - {e}")
        return {"title": chapter["title"], "url": url, "content": f"\n【下载失败: {e}】\n", "failed": True}


def main():
    print("=" * 60)
    print("小说下载器 - 凡人修仙记 (多线程加速版)")
    print("=" * 60)

    print("\n[1/4] 正在获取章节目录...")
    chapters = get_chapter_list()
    chapters.sort(key=lambda c: extract_chapter_number(c["title"]))
    print(f"共找到 {len(chapters)} 章")

    progress = load_progress()
    completed = set(progress.get("completed", []))
    print(f"已下载: {len(completed)} 章, 剩余: {len(chapters) - len(completed)} 章")

    todo = [c for c in chapters if c["url"] not in completed]
    if not todo:
        print("\n所有章节已下载完成！")
        return

    print(f"\n[2/4] 开始多线程下载 {len(todo)} 章 (线程数: {MAX_WORKERS})...")
    results = []
    failed = []
    counter = [0]
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {
            executor.submit(download_one, ch, completed, counter, len(todo)): ch["url"]
            for ch in todo
        }

        for future in as_completed(future_to_url):
            result = future.result()
            if result:
                results.append(result)
                if result.get("failed"):
                    failed.append(result["url"])
                else:
                    completed.add(result["url"])

            # 每完成100章保存一次进度
            if len(results) % 100 == 0:
                save_progress(list(completed))

    save_progress(list(completed))

    elapsed = time.time() - start_time
    print(f"\n下载完成! 耗时: {elapsed:.1f}秒, 平均: {len(todo)/elapsed:.1f}章/秒")

    # 写入文件
    print(f"\n[3/4] 正在写入文件...")

    content_map = {r["url"]: r for r in results}

    # 检查是否需要写头部
    need_header = not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) < 100

    with open(OUTPUT_FILE, "a" if not need_header else "w", encoding="utf-8") as f:
        if need_header:
            f.write("凡人修仙记\n")
            f.write("作者：梧桐悠悠\n")
            f.write("来源：66kxs.net\n")
            f.write("=" * 50 + "\n\n")

        for ch in chapters:
            if ch["url"] in content_map:
                r = content_map[ch["url"]]
                f.write(f"\n{'='*50}\n")
                f.write(f"{r['title']}\n")
                f.write(f"{'='*50}\n\n")
                f.write(r["content"])
                f.write("\n\n")

    # 统计文件大小
    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"\n[4/4] 完成!")
    print(f"文件: {os.path.abspath(OUTPUT_FILE)}")
    print(f"大小: {file_size / 1024 / 1024:.2f} MB")
    print(f"总章节: {len(chapters)}, 已下载: {len(completed)}, 失败: {len(failed)}")

    if failed:
        print(f"\n失败章节 ({len(failed)} 个):")
        for url in failed[:10]:
            print(f"  - {url}")


if __name__ == "__main__":
    main()
