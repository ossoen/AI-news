#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并两个文件的内容，然后去重，得到一个尽可能完整的版本
"""
import os
import re

OLD = "凡人修仙记.txt"
NEW = "凡人修仙记_full.txt"
MERGED = "凡人修仙记_merged.txt"

def extract_chapters(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    chapters = {}
    # 按章节标题分割
    parts = re.split(r"(={50}\n第\d+章[^\n]*\n={50})", text)
    current_title = None
    for part in parts:
        m = re.match(r"={50}\n(第\d+章[^\n]*)\n={50}", part)
        if m:
            current_title = m.group(1).strip()
        elif current_title and part.strip():
            if current_title not in chapters or len(part.strip()) > len(chapters.get(current_title, "")):
                chapters[current_title] = part.strip()
    return chapters

print("读取旧文件...")
old_ch = extract_chapters(OLD)
print(f"旧文件章节: {len(old_ch)}")

print("读取新文件...")
new_ch = extract_chapters(NEW)
print(f"新文件章节: {len(new_ch)}")

# 合并，优先用内容更长的
merged = dict(old_ch)
for title, content in new_ch.items():
    if title not in merged or len(content) > len(merged[title]):
        merged[title] = content

print(f"合并后: {len(merged)} 章")

# 按章节号排序
def get_num(title):
    m = re.search(r"第(\d+)章", title)
    return int(m.group(1)) if m else 99999

sorted_titles = sorted(merged.keys(), key=get_num)

with open(MERGED, "w", encoding="utf-8") as f:
    f.write("凡人修仙记\n作者：梧桐悠悠\n来源：66kxs.net\n")
    f.write("=" * 50 + "\n\n")
    for title in sorted_titles:
        f.write(f"\n{'='*50}\n{title}\n{'='*50}\n\n{merged[title]}\n\n")

print(f"已保存: {MERGED} ({os.path.getsize(MERGED)/1024/1024:.2f} MB)")

# 统计
nums = [get_num(t) for t in sorted_titles]
print(f"范围: {nums[0]} - {nums[-1]}")
gaps = [i for i in range(1, nums[-1]+1) if i not in nums]
print(f"缺失: {len(gaps)} 章")
if len(gaps) <= 20:
    print(gaps)
else:
    print(f"前10: {gaps[:10]}, 后10: {gaps[-10:]}")
