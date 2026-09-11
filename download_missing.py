import requests
from bs4 import BeautifulSoup
import time
import os

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

missing = [
    ('第1971章 泉鸣之殇', 'https://www.66kxs.net/book/3993/3993372/33930810.html'),
    ('第1972章 剑仙之名', 'https://www.66kxs.net/book/3993/3993372/33904058.html'),
    ('第1973章 剑气之殇', 'https://www.66kxs.net/book/3993/3993372/33878578.html'),
    ('第1974章 夜色中的黑衣人', 'https://www.66kxs.net/book/3993/3993372/33858269.html'),
    ('第1975章 最后一个任务', 'https://www.66kxs.net/book/3993/3993372/33829329.html'),
    ('第1976章 魔域之门', 'https://www.66kxs.net/book/3993/3993372/33803862.html'),
    ('第1977章 最不简单的黑龙', 'https://www.66kxs.net/book/3993/3993372/33780900.html'),
    ('第1978章 不值一提', 'https://www.66kxs.net/book/3993/3993372/33755997.html'),
    ('第1979章 师尊', 'https://www.66kxs.net/book/3993/3993372/33738585.html'),
    ('第1980章 神兵的线索', 'https://www.66kxs.net/book/3993/3993372/33712257.html'),
    ('第1981章 神谕碑', 'https://www.66kxs.net/book/3993/3993372/33692154.html'),
    ('第1982章 水龙吟', 'https://www.66kxs.net/book/3993/3993372/33666594.html'),
]

def fetch_html(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.encoding = 'gbk'
    return resp.text

def get_content(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    content_div = soup.find('div', id='content') or soup.find('div', class_='content')
    if content_div:
        for tag in content_div.find_all(['script', 'style', 'a', 'div']):
            t = tag.get_text()
            if any(k in t for k in ['下一章', '上一章', '返回目录', '加入书签']):
                tag.decompose()
        text = content_div.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return '\n'.join(lines)
    return ''

# Find txt file
fname = None
for f in os.listdir('.'):
    if f.endswith('.txt'):
        fname = f
        break

sep = '=' * 50
with open(fname, 'a', encoding='utf-8') as f:
    for title, url in missing:
        try:
            content = get_content(url)
            f.write('\n' + sep + '\n')
            f.write(title + '\n')
            f.write(sep + '\n\n')
            f.write(content)
            f.write('\n\n')
            print('OK:', title)
            time.sleep(0.5)
        except Exception as e:
            print('FAIL:', title, '-', e)

print('Done!')
