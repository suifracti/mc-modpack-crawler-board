import os
import sys
import re
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = r'd:\ai\work\我的世界整合包获取'
TABLE_ROWS_PATH = os.path.join(REPO_ROOT, 'converted_output', 'data', 'table_rows.js')
CACHE_PATH = os.path.join(REPO_ROOT, 'crawler_output', 'mcmod_details_cache.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Referer': 'https://www.mcmod.cn/'
}

def fetch_single_pack(mid):
    url = f"https://www.mcmod.cn/modpack/{mid}.html"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return mid, None
            html = resp.read().decode('utf-8', errors='ignore')
            
            # 1. extract mc_vers
            mc_vers = []
            m_sec = re.search(r'支持的MC版本[：:\s]*(?:<ul>.*?</ul>)+', html, re.S)
            if m_sec:
                mc_vers = list(dict.fromkeys(re.findall(r'mcver=([0-9.]+)', m_sec.group(0))))
            
            # 2. extract desc
            desc = ""
            m_desc = re.search(r'class="[^"]*text-area[^"]*common-text[^"]*"[^>]*>(.*?)</div>', html, re.S)
            if m_desc:
                raw = m_desc.group(1)
                # preserve paragraph breaks
                desc = re.sub(r'<br\s*/?>', '\n', raw)
                desc = re.sub(r'</p>\s*<p>', '\n\n', desc)
                desc = re.sub(r'<[^>]+>', '', desc).strip()
            
            # 3. extract intro images
            images = []
            if m_desc:
                for img_m in re.finditer(r'<img[^>]+src="([^"]+)"', m_desc.group(1)):
                    src = img_m.group(1).strip()
                    if src and not src.endswith(('blank.png', 'loading.gif')):
                        if src.startswith('//'):
                            src = 'https:' + src
                        images.append(src)

            return mid, {
                "mid": str(mid),
                "mc_versions": mc_vers,
                "desc": desc,
                "intro_images": images
            }
    except Exception as e:
        return mid, None

def run_cache_builder(limit=None, workers=5):
    cache = {}
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"[缓存] 已加载历史缓存 {len(cache)} 条记录", flush=True)
        except Exception:
            cache = {}

    with open(TABLE_ROWS_PATH, 'r', encoding='utf-8') as f:
        rows = json.loads(f.read().strip()[len('window.tableRowsData = '):].rstrip(';\n '))

    # Sort rows by views_n desc (top popular first)
    rows.sort(key=lambda x: int(x.get('views_n', 0) or 0), reverse=True)
    
    needed = [r['mid'] for r in rows if str(r['mid']) not in cache or not cache[str(r['mid'])].get('desc')]
    if limit:
        needed = needed[:limit]

    print(f"[采集] 待拉取详情整合包: {len(needed)} 款 (总存量 {len(rows)} 款)", flush=True)
    if not needed:
        print("[完成] 所有整合包均已完成缓存！", flush=True)
        return cache

    t0 = time.time()
    saved = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(fetch_single_pack, mid): mid for mid in needed}
        for fut in as_completed(futures):
            mid, res = fut.result()
            if res:
                cache[str(mid)] = res
                saved += 1
                if saved % 5 == 0 or saved == len(needed):
                    print(f"  -> 已完成 {saved}/{len(needed)} 款 ({time.time()-t0:.1f}s)", flush=True)
                    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
                        json.dump(cache, f, ensure_ascii=False, indent=2)

    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"[落盘] 成功采集并保存 {saved} 条新数据，当前总缓存: {len(cache)} 条 (耗时 {time.time()-t0:.1f}s)", flush=True)
    return cache

if __name__ == '__main__':
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    run_cache_builder(limit=limit, workers=workers)
