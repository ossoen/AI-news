#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import time
import os
import re
from urllib.parse import urljoin

BASE = "https://www.66kxs.net/book/3993/3993372/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.encoding = "gbk"
    return r.text

def get_chapters():
    soup = BeautifulSoup(fetch(BASE), "html.parser")
    chapters = []
    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if re.match(r"/book/3993/3993372/\d+\.html", href):
            chapters.append((text, urljoin(BASE, href)))
    seen = set()
    out = []
    for t, u in chapters:
        if u not in seen:
            seen.add(u)
            out.append((t, u))
    out.sort(key=lambda x: int(re.search(r"第(\d+)章", x[0]).group(1)) if re.search(r"第(\d+)章", x[0]) else 99999)
    return out

def get_content(url):
    soup = BeautifulSoup(fetch(url), "html.parser")
    div = soup.find("div", id="content") or soup.find("div", class_="content")
    if not div:
        m, d = 0, None
        for x in soup.find_all("div"):
            if len(x.get_text()) > m:
                m, div = len(x.get_text()), x
    if div:
        for t in div.find_all(["script", "style", "a", "div"]):
            if any(k in t.get_text() for k in ["下一章", "上一章", "返回目录"]):
                t.decompose()
        return "\n".join(line.strip() for line in div.get_text(separator="\n").splitlines() if line.strip())
    return ""

all_ch = get_chapters()
print(f"Total: {len(all_ch)} chapters")

# Read existing
with open("凡人修仙记.txt", "r", encoding="utf-8") as f:
    txt = f.read()

existing = set()
for t, u in all_ch:
    if t in txt:
        existing.add(t)

missing = [(t, u) for t, u in all_ch if t not in existing]
print(f"Existing: {len(existing)}, Missing: {len(missing)}")

if not missing:
    print("All done!")
    exit(0)

sep = "=" * 50
with open("凡人修仙记.txt", "a", encoding="utf-8") as f:
    for i, (title, url) in enumerate(missing, 1):
        try:
            content = get_content(url)
            f.write(f"\n{sep}\n{title}\n{sep}\n\n{content}\n\n")
            if i % 50 == 0:
                f.flush()
                print(f"  [{i}/{len(missing)}] done")
            time.sleep(0.35)
        except Exception as e:
            print(f"  FAIL {title}: {e}")
            time.sleep(1)

# Verify
with open("凡人修仙记.txt", "r", encoding="utf-8") as f:
    text = f.read()
unique = len(set(re.findall(r"第\d+章", text)))
print(f"\nDone! Unique chapters: {unique}/1982")
print(f"File: {os.path.abspath('凡人修仙记.txt')}")
print(f"Size: {os.path.getsize('凡人修仙记.txt')/1024/1024:.2f} MB")
