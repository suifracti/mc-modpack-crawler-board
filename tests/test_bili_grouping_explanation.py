import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(REPO_ROOT, "build", "frontend_preview", "data", "bili_data.js")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    content = f.read()

json_str = content.split("=", 1)[1].strip()
if json_str.endswith(";"):
    json_str = json_str[:-1]
data = json.loads(json_str)

q = "机械动力"
filtered = []
for p in data:
    s = (
        (p.get("title") or "") + " " +
        (p.get("author") or "") + " " +
        (p.get("desc") or "") + " " +
        (p.get("mc_version") or "") + " " +
        " ".join(p.get("loaders") or []) + " " +
        " ".join(p.get("categories") or [])
    ).lower()
    if q in s:
        filtered.append(p)

print(f"Raw filtered videos count: {len(filtered)}")

BILI_GENERIC_PACK_KEYS = {
    "", "mc", "我的世界", "minecraft", "模组", "整合", "游戏", "自制", "包", "整合包",
    "全新", "纯净", "高配", "低配", "生存", "冒险", "科技", "魔法", "空岛", "大型",
    "超好玩", "免费", "客户端", "体验"
}

BILI_GENRE_BUZZWORDS = r"(?:rpg|冒险|高度定制|史诗战斗|魔法|枪械|科技|生存|剧情|硬核|沉浸式|高难|爽游|原版|魔改|养老|纯净|探索|空岛|地牢|格斗|战斗|拔刀剑|工业|建造|现代战争)"

def clean_pack_key(s):
    if not s:
        return ""
    title = str(s)
    title = re.sub(r"(?:我的世界|minecraft|mine\s*craft|mc)", " ", title, flags=re.I)
    title = re.sub(r"[【】\[\]（）(){}\u300C\u300D\u300E\u300F《》/|·~～!！?？:：\-—+*#]+", " ", title)
    title = re.sub(r"(?:mc|minecraft|我的世界)?\s*1\.\d{1,2}(?:\.\d+)?", " ", title, flags=re.I)
    title = re.sub(r"(?:v|ver|version)?\s*\d+(?:\.\d+)+(?:[a-zA-Z\d_\-.]*)?", " ", title, flags=re.I)
    title = re.sub(r"(?:v|ver|version)\s*\d+", " ", title, flags=re.I)
    title = re.sub(r"\b(?:forge|fabric|neoforge|quilt)\b", " ", title, flags=re.I)
    title = re.sub(r"(?:整合包|模组包|魔改包|懒人包|重制版|正式版|抢先版|公测版|抢先体验|测试版)", " ", title)
    title = re.sub(r"(?:最新|首发|公测|更新|发布|分享|下载|自制|自创|开坑|入坑|通关|介绍|演示|实况|推荐)", " ", title)
    title = re.sub(BILI_GENRE_BUZZWORDS, " ", title, flags=re.I)
    title = re.sub(r"(?:新的征途.*|从此刻开始.*|第一期.*|第二期.*|第\d+期.*|ep\d+.*)", " ", title, flags=re.I)
    title = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", " ", title).strip().lower()
    return re.sub(r"\s+", " ", title)

groups = []
mapping = {}
for p in filtered:
    raw_key = clean_pack_key(p.get("title"))
    author_key = (p.get("author") or "unknown").strip().lower()
    key = ""
    if not raw_key or len(raw_key) <= 3 or raw_key in BILI_GENERIC_PACK_KEYS:
        key = "__raw_" + str(p.get("bvid"))
    else:
        matched = None
        for k in mapping.keys():
            if k.startswith(author_key + "::"):
                exist_raw = k[len(author_key) + 2:]
                if exist_raw == raw_key or (len(exist_raw) >= 4 and exist_raw in raw_key) or (len(raw_key) >= 4 and raw_key in exist_raw):
                    matched = k
                    break
        if matched:
            key = matched
        else:
            key = f"{author_key}::{raw_key}"
    if key not in mapping:
        g = {"key": key, "items": []}
        mapping[key] = g
        groups.append(g)
    mapping[key]["items"].append(p)

print(f"Grouped cards count: {len(groups)}")
multi_groups = [g for g in groups if len(g["items"]) > 1]
print(f"Multi-item groups: {len(multi_groups)}")
for g in multi_groups:
    print(f"Group Key: {g['key']} ({len(g['items'])} items):")
    for it in g["items"]:
        bvid = it.get("bvid")
        title = it.get("title", "")
        print(f"  * {bvid} - {title[:40]}")

assert len(filtered) == 53, f"Expected 53 raw filtered items, got {len(filtered)}"
assert len(groups) == 47, f"Expected 47 grouped cards, got {len(groups)}"
print("VERIFICATION SUCCESS: 53 raw items exactly collapse into 47 grouped cards!")
