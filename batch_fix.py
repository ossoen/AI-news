#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分批补全缺失章节 - 每批100章，自动保存进度
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

MERGED = "凡人修仙记_merged.txt"
FINAL = "凡人修仙记.txt"
BATCH_STATE = "batch_state.json"
DELAY = 0.35
BATCH_SIZE = 100


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


def extract_chapter_number(title):
    m = re.search(r"第(\d+)章", title)
    return int(m.group(1)) if m else 99999


def get_chapter_content(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    content_div = (
        soup.find("div", id="content")
        or soup.find("div", class_="content")
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


def load_state():
    if os.path.exists(BATCH_STATE):
        with open(BATCH_STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"done_titles": []}


def save_state(done_titles):
    with open(BATCH_STATE, "w", encoding="utf-8") as f:
        json.dump({"done_titles": done_titles}, f, ensure_ascii=False)


def main():
    print("=" * 60)
    print("分批补全缺失章节")
    print("=" * 60)

    print("\n[1/3] 获取章节目录...")
    chapters = get_chapter_list()
    chapters.sort(key=lambda c: extract_chapter_number(c["title"]))

    # 读取已合并文件中的章节
    print("\n[2/3] 扫描已有章节...")
    existing_titles = set()
    if os.path.exists(MERGED):
        with open(MERGED, "r", encoding="utf-8") as f:
            txt = f.read()
        for ch in chapters:
            if ch["title"] in txt:
                existing_titles.add(ch["title"])

    state = load_state()
    done_titles = set(state.get("done_titles", []))
    existing_titles |= done_titles

    print(f"已有章节: {len(existing_titles)}")

    missing = [ch for ch in chapters if ch["title"] not in existing_titles]
    print(f"缺失章节: {len(missing)}")

    if not missing:
        print("\n无需补全！")
        return

    # 分批处理
    total_batches = (len(missing) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n[3/3] 开始下载，共 {total_batches} 批，每批 {BATCH_SIZE} 章...")

    # 复制合并文件作为基础
    if not os.path.exists(FINAL):
        import shutil
        shutil.copy(MERGED, FINAL)

    with open(FINAL, "a", encoding="utf-8") as f:
        batch_num = 0
        success = 0
        failed = 0
        start = time.time()

        for i, ch in enumerate(missing, 1):
            try:
                content = get_chapter_content(ch["url"])
                f.write(f"\n{'='*50}\n{ch['title']}\n{'='*50}\n\n{content}\n\n")
                done_titles.add(ch["title"])
                success += 1

                if success % 50 == 0:
                    f.flush()
                    save_state(list(done_titles))

                if i % BATCH_SIZE == 0 or i == len(missing):
                    batch_num += 1
                    save_state(list(done_titles))
                    elapsed = time.time() - start
                    print(f"  批次 {batch_num}/{total_batches} 完成 | 已下载 {success} 章 | 耗时 {elapsed/60:.1f} 分钟")

                time.sleep(DELAY)

            except Exception as e:
                failed += 1
                print(f"  ✗ 失败: {ch['title']} - {e}")
                time.sleep(1)

    save_state(list(done_titles))

    # 统计
    with open(FINAL, "r", encoding="utf-8") as f:
        text = f.read()
    chs = re.findall(r'第\d+章', text)
    unique = len(set(chs))

    print(f"\n完成!")
    print(f"文件: {os.path.abspath(FINAL)}")
    print(f"大小: {os.path.getsize(FINAL) / 1024 / 1024:.2f} MB")
    print(f"成功: {success}, 失败: {failed}")
    print(f"txt 中总章节数（含重复）: {len(chs)}, 唯一章节: {unique}")


if __name__ == "__main__":
    main()
