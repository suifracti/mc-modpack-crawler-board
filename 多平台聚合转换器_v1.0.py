
def load_bilibili_data():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    bili_json = os.path.join(repo_root, "crawler_output", "bilibili_modpacks.json")
    if os.path.exists(bili_json):
        try:
            with open(bili_json, "r", encoding="utf-8") as f:
                raw = json.load(f)
            cleaned = []
            for item in raw:
                title = item.get("title", "")
                desc = item.get("desc", "")
                author = item.get("author", "")
                pinned = item.get("pinned_comment", "")
                sub = item.get("subtitle_text", "") or item.get("subtitle_summary", "")
                has_links = bool(item.get("download_links"))
                has_qq = bool(item.get("qq_group"))
                full_text = f"{title}\n{desc}\n{pinned}\n{sub}"

                # 0. 核心黄金准入准则：名字必须有 "整合包/懒人包"，并包含 "更新/发布/首发/公测"
                if not re.search(r'(?:整合包|模组包|懒人包)', title):
                    continue
                if not re.search(r'(?:更新|发布|首发|公测)', title):
                    continue

                # 1. 过滤纯材质包/光影包/资源包/皮肤包
                if re.search(r'(?:材质包|光影包|资源包|皮肤包|数据包|材质分享|光影分享|纯材质|手感材质|PVP材质|光影推荐|材质推荐|纹理包)', title, re.I) and not re.search(r'(?:整合包|模组包)', title, re.I):
                    continue

                # 2. 过滤纯实况录播、解说、试玩、分集(P/EP/第X期)、直播回放、一口气看完
                if re.search(r'(?:一口气(?:看完|了解|通关)?|(?:实况|通关|剧情|全流程|流程|深度|速通|纯享)?解说|通关全程|全程实况|通关实况|通关记录|全流程通关|实况全程|纯享版|完结撒花|[【\[\(](?:实况|纯享|解说|录播|切片|游戏实况|通关实况|全程实况|开箱|体验|试玩|整活)[】\]\)]|第\s*\d+\s*[集期话天P次]|(?:^|[^\w])P\d+(?:[^\w]|$)|(?:^|[^\w])EP\.?\s*\d+|Part\.?\s*\d+|录播|切片|直播回放|录像回放|直播录像|录播回放|主播被迫断更|开局(?:就)?[坐牢受难暴毙无敌神装起飞破防痛苦折磨]|坐牢[？！?!]|长视频|二周目|一周目|生存档|游玩记录)', title, re.I):
                    continue

                # 3. 过滤借包试玩
                if re.search(r'整合包(?:宣传|发布|原|原版)?视频\s*[:：]\s*(?:https?://[^\s]+|BV[a-zA-Z0-9]+)', desc, re.I):
                    continue

                # 4. 过滤外借作者且无网盘
                if not has_links and not has_qq:
                    cred = re.search(r'(?:整合包)?(?:原?作者|制作人|制作者)\s*[:：]\s*@([^\s，,。\n]+)', desc)
                    if cred:
                        c_name = cred.group(1).strip()
                        if author and c_name.lower() not in author.lower() and author.lower() not in c_name.lower():
                            continue

                # 5. 过滤整合包推荐/盘点合集/排行榜
                if re.search(r'(?:最全.*?(?:整合包|模组包)?推荐|必玩[^\n，。！？!?,]{0,15}?(?:整合包|模组包)?推荐|游玩推荐|(?:整合包|模组包)推荐榜|(?:整合包|模组包)盘点|(?:整合包|模组包)合集|(?:整合包|模组包)合辑|(?:整合包|模组包)排行|(?:盘点|推荐|精选)(?:\d+|几|[一二三四五六七八九十])款|有哪些.*?(?:整合包|模组包)|(?:整合包|模组包)漫谈|神仙整合包|宝藏整合包|好玩的整合包|^[【\[\(]?\s*(?:(?:MC|我的世界)?整合包|模组包)推荐\s*[】\]\)]?|^[【\[\(]?\s*(?:\d+月|[一二三四五六七八九十]+月|暑[假期]|年度|最新)?\s*推荐[！!：:\s])', title, re.I):
                    continue

                # 6. 过滤私信引流/虚假话术
                if re.search(r"""(?:私信(?:自动)?回复|自动私信|主动私信|私信发给你|打开和我的对话框|评论区(?:截图)?留言|回复["'“”][^"'“”]{1,10}["'“”].*?私信|点个免费三连关注\+一定要看完视频|请勿拖动进度条)""", full_text, re.I):
                    continue

                # 7. 过滤虚假双端/iOS直装/擦边吸睛
                if re.search(r'(?:(?:三端|双端|安卓\+)?(?:PC\+)?iOS(?:\+手机|\+安卓|\+PC)?(?:三端)?(?:直装|直接安装)|iOS直装|三端PC\+iOS|全CG(?:动态)?|3000\+娘化|动漫娘化|娘化内容|全清凉mod|爆衣皮肤|无限内购|手机\+PC双端(?:直装|分享)|手机/电脑都可玩\s*全互通|保姆级安卓\+联机教程~~附地址|天花板\d+\.\d+版本|最强最好玩顶级\d+\.\d+版本|无偿速存|火速存起来|免费白嫖啦|手慢真会错过|入坑血赚|玩嗨了！！！)', full_text, re.I):
                    continue

                # 8. 过滤批量机器账号与已知推销号
                if (re.match(r'^bili_\d{7,}$', author) or
                    re.match(r'^[a-z]{10,}$', author) or
                    re.match(r'^[a-zA-Z0-9][\u4e00-\u9fa5]{2,6}[a-zA-Z0-9]{3,}$', author) or
                    re.match(r'^[\u4e00-\u9fa5]{2}\d[A-Z]-[\u4e00-\u9fa5]{2}$', author) or
                    (re.search(r'^[a-zA-Z0-9].*?[\u4e00-\u9fa5].*?[a-zA-Z0-9]', author) and not re.match(r'^(?:MC|Minecraft|PCL|BBS|FPS|RPG|UP|AI|HD|VR|B站|3D)[\u4e00-\u9fa5]+$', author, re.I)) or
                    author in ['梦灵神奇宝贝', '我的世界神奇宝贝屁王', '我的世界旺仔', '我的世界神奇宝贝花火', '我的世界神奇宝贝阿宇', '我的世界神奇宝贝樱木']):
                    continue

                # 9. 过滤空壳无链假包 (0外链、0QQ群且简介完全为空、置顶也为空)
                desc_clean = desc.strip().replace('-', '').replace('无', '')
                pinned_clean = pinned.strip()
                if not has_links and not has_qq and not desc_clean and not pinned_clean:
                    continue

                # 10. 过滤非 MC 软件/AI整合包与其他独立游戏MOD
                if re.search(r'(?:comfyui|stable\s*diffusion|sd\s*webui|sd整合包|绘世(?:启动器)?|本地部署.*?大模型|支持\s*\d{4,}\s*显卡|ai绘画整合包|minimaxh3|秋叶.*?aaaki|秋叶comfyui|comfyui安装包)', full_text, re.I) or re.search(r'(?:【致命解药】|致命解药.*?整合包|黑神话.*?整合包|幻兽帕鲁.*?整合包|赛博朋克.*?整合包|艾尔登法环.*?整合包|valorant|无畏契约|战斗大师|三角洲行动|烽火地带|暗区突围|逃离塔科夫)', title, re.I):
                    continue

                # 11. 过滤单模组枪包/武器扩展包 (TacZ/TAC/PointBlank等)
                if re.search(r'(?:枪包|枪械包|武器包|弹药包|配件包|附属枪包|TacZ\s*(?:附属|扩展|枪包)|TAC\s*(?:附属|扩展|枪包)|TAC-Z\s*(?:附属|扩展)|Point\s*Blank\s*(?:附属|扩展)|自制枪包|原创枪包|重置枪包|多枪包整合|guns\s*and\s*targets枪包|三角洲枪包|冲锋陷阵枪包|源石武器包|冲锋陷阵扩展包)', title, re.I):
                    continue

                # 12. 过滤单模组模型包/动作包 (YSM/车万女仆等)
                if re.search(r'(?:YSM\s*模型|YSM\s*动作|YSM\s*整合|YSM.*?安装教程|车万女仆.*?模型|女仆模型包|CPM模型|自定义NPC模型|模型整合包|动作整合包|姿势包|骨骼动画包)', title, re.I):
                    continue

                # 13. 过滤服务器发布/宣传/纯开服教程/云服推广
                if re.search(r'(?:[【\[\(]?(?:服务器发布|服务器宣传|服务器招募|服务器招新|新服开荒|新服发布|开服宣传|开荒公测)[】\]\)]?)', title):
                    continue
                if re.search(r'(?:(?:全新|自制|大型|原创|公益|商业|高版本|生化|RPG|战争|空岛|生存|养老|纯净|模组|互通|进服)服务器|.*?服务器.*?(?:你确定不来看看吗|即将更新内容|进群|公测|招人|招募|招新|开服啦))', title, re.I) and not re.search(r'(?:整合包|模组包)\s*(?:发布|更新|下载|分享)', title):
                    continue
                if re.search(r'(?:(?:安装和)?开服(?:联机)?教程|服务器搭建教程|FRP开服联机|自己的电脑也能开服)', title) and (not re.search(r'(?:整合包|模组包)\s*(?:发布|更新|首发|公测)', title) or re.search(r'开服教程！|开服联机教程！|开服教程$|联机教程！', title)):
                    continue
                if re.search(r'服务器', title) and re.search(r'(?:进服|服务器ip|服务器群|服务器介绍|欢迎加入.*?服)', full_text) and not re.search(r'(?:整合包|模组包)\s*(?:发布|更新|首发)', title):
                    continue
                if re.search(r'(?:重铸服|所开的服|开局送神兽|加入官方Q群.*?群文件下载|企鹅群文件下载.*?免费)', full_text):
                    continue

                # 14. 过滤标题声明为【模组发布】/【Mod发布】的单模组发布
                if re.search(r'^[【\[\(]?(?:MC)?(?:模组|mod|Mod|MOD)发布[】\]\)]?', title):
                    continue

                # 15. 过滤单个模组更新而非整合包更新
                if re.search(r'(?:模组|mod|Mod)更新', title) and not re.search(r'(?:整合包|模组包)(?:.*?)(?:更新|发布)', title) and not re.search(r'(?:更新|发布)(?:.*?)(?:整合包|模组包)', title):
                    continue

                # 16. 过滤纯整合包制作教学/傻瓜式教学 (教你做整合包)
                if re.search(r'(?:整合包制作$|整合包制作[，,、\s]|制作自己的(?:宝可梦)?整合包|教你.*?制作.*?整合包|整合包制作教学|手把手教你做整合包|如何制作整合包)', title):
                    if not re.search(r'(?:正式)?发布|公测|首发|全新更新|v\d+\.\d+更新', title) or re.search(r'(?:2分钟做自己的|傻瓜式教学|制作自己的.*?整合包)', desc) or re.search(r'2分钟下载[，,]\s*整合包制作', title):
                        continue

                # 17. 过滤纯启动器/手机端安装教程
                if re.search(r'^[【\[\(]?(?:FCL|PCL|HMCL|BakaXL|折叠启动器|启动器)教程', title, re.I) or re.search(r'(?:启动器教程|教会你用手机玩Java版.*?整合包下载安装及更新教程)', title):
                    continue

                # 18. 过滤UP主视频调侃/催更/营销震惊体 (粉丝帮知名UP主更新/背后原因让人沉默)
                if re.search(r'(?:UP主不更新|粉丝帮.*?更新|为什么不更新|不更新视频|背后原因让人沉默|某粉丝怒了|某粉丝帮他更)', title):
                    continue

                # 19. 过滤含有手机号/推销号的批量营销号
                if re.search(r'1[3-9]\d{9}整合包', title) or (re.search(r'1[3-9]\d{9}', title) and not desc.strip()):
                    continue

                cleaned.append(item)
            return cleaned
        except Exception:
            pass
    return []

def load_bbsmc_data():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    bbsmc_json = os.path.join(repo_root, "crawler_output", "bbsmc_modpacks.json")
    if os.path.exists(bbsmc_json):
        try:
            with open(bbsmc_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def load_modrinth_data():
    """从 crawler_output/modrinth_modpacks.json 载入 Modrinth 整合包数据"""
    target = os.path.join("crawler_output", "modrinth_modpacks.json")
    if os.path.exists(target):
        try:
            with open(target, "r", encoding="utf-8") as f:
                packs = json.load(f)
            print("  [提示] 成功从 {} 读取 Modrinth 整合包 (共 {} 条)".format(target, len(packs)))
            return packs
        except Exception as e:
            print("  [警告] 读取 Modrinth 数据失败: {}".format(e))
    return []

def load_curseforge_data():
    """从 crawler_output/curseforge_modpacks.json 载入 CurseForge 整合包数据"""
    target = os.path.join("crawler_output", "curseforge_modpacks.json")
    if os.path.exists(target):
        try:
            with open(target, "r", encoding="utf-8") as f:
                packs = json.load(f)
            print("  [提示] 成功从 {} 读取 CurseForge 整合包 (共 {} 条)".format(target, len(packs)))
            return packs
        except Exception as e:
            print("  [警告] 读取 CurseForge 数据失败: {}".format(e))
    return []

def load_xyebbs_data():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    xyebbs_json = os.path.join(repo_root, "crawler_output", "xyebbs_modpacks.json")
    if os.path.exists(xyebbs_json):
        try:
            with open(xyebbs_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多平台整合包 JSONL 转 HTML 看板生成器。"""

# v10.4.2: 标签/分类列改宽并取消内部滚动；悬浮窗点 X 后冷却改为 5 秒；
#          文案补充：鼠标移出只会正常关闭，不触发冷却。
# v10.4.3: 评论悬浮窗头部改为和介绍窗一致的图标/操作区；增强 X 可见性；
#          增加跳转 MC百科原页面评论区入口。
# v10.4.4: 支持爬虫写入每条评论/楼中楼原站定位链接；评论卡片右上角增加跳转按钮。
# v10.4.5: 模组卡片主体点击筛选/再次点击取消，右上角箭头独立跳转；
#          评论仅在存在精确原站链接时显示单条跳转，并补充楼层/页内位置。
# v10.4.6: 爬虫结构化保存整合包分类/标签 URL；看板标签主体筛选、箭头跳转。
# v10.4.7: 稳定评论悬浮窗尺寸与关闭节奏；筛选区增加“排除所选”反向筛选；
#          转换器继续只读取当前新数据，不再兼容旧 JSON 结构。
# v10.4.8: 指数评分并入趋势列；趋势窗不再跟随鼠标移动；筛选选项补频次；
#          “动漫”主题改名为流光玻璃，评论窗关闭节奏改得更自然。
# v10.4.9: 趋势悬浮窗增加可进入缓冲；评论窗去掉本地条数口径，只显示官方楼层/官方评论数。
# v10.4.10: 趋势悬浮窗增加透明安全桥，便于鼠标移入；评分文案改为官方流行指数。
# v10.4.11: 趋势大窗改为默认点击打开，并增加悬浮开关；表格外层小波形支持直接读日期/指数。
# v10.4.12: 评论详情改为点击打开；评论列增加圆形详情入口；趋势/评论关闭按钮不再触发冷却；
#           顶部提示文案同步为当前点击/悬浮混合交互。
# v10.4.13: 评论列与趋势列支持再次点击原入口关闭；趋势列增加“点击看图”提示；
#           顶部说明改为覆盖当前看板主要操作。
# v10.4.14: 评论入口改为更轻的图标按钮；评论窗空白处可点击关闭；
#           删除“原站评论”等误导性回退文案，仅在有抓取楼层时显示第 X 楼。
# v10.4.15: 趋势弹窗按整合包标题识别开关，同一包趋势区域再次点击即可关闭；
#           弹窗空白处也可点击关闭。
# v10.4.16: 增加“悬浮评论窗”开关；趋势/评论均可在点击打开与悬浮打开之间切换；
#           清理爬虫旧楼层估算字段，评论楼层只保留真实抓取值。
# v10.4.17: 趋势列点击改用捕获兜底，同一包趋势区域任意位置再次点击都可关闭；
#           悬浮开关移动到对应趋势/评论区域，并统一为小圆角胶囊样式。
# v10.4.18: 修复表头悬浮开关被排序事件吞掉的问题；趋势/评论开关都内嵌到对应表头；
#           开关改为紧凑滑块样式，减少视觉占位。
# v10.4.19: 表头悬浮开关改为 class 绑定，兼容 DataTables 克隆表头；
#           模组详情展开后点击分类间隔/右侧空白可直接收起。
# v10.4.20: 表头悬浮开关改用捕获阶段拦截并手动切换，彻底避开 DataTables 表头排序。
# v10.4.21: 趋势弹窗按整行整合包 ID 开关，左右趋势格都能关闭同一弹窗；
#           介绍弹窗增加点击/悬浮模式开关；生成固定文件同时输出版本号副本。
# v10.4.22: Switches use the whole pill as the click target; trend popups close from either trend cell in the same row; default output filename carries APP_VERSION.
# v10.4.23: Move hover switches above the table; add modpack type filtering, two-line titles, comment totals, and fix 60-day trend filtering.
# v10.4.24: Merge total views into the title column, remove the standalone views column, and make the mod list grid fully adaptive for fullscreen density.
# v10.4.25: Stabilize the 7-column table after the views merge; restore readable 3-column mod grids; add title-column views sorting; refresh glass pagination.
# v10.4.26: Restyle filter/search/pagination controls; make the Flow theme neon-iridescent; add sortable mod-count column behavior.
# v10.4.27: Convert type/trend/search selectors to rounded glass Select2 controls and rebuild pagination as a theme-colored soft pill.
# v10.4.28: Add tag-count sorting, redesign collapsed mod summaries to fill the mod column, and force pagination colors to follow the active theme.
# v10.4.29: Fix tag sorting click handling, simplify tag header, fully expand collapsed mod summaries, and harden themed pagination color overrides.
# v10.5.0: Add compact category filter UI plus favorites, compare tray, and full-screen glass comparison matrix.
# v10.5.1: Move the favorite star to the upper-right of each title cell and keep the title text clear.
# v10.5.2: Render crawled cover/intro/comment images in popups and normalize image URLs for file:// dashboards.
# v10.5.3: Filter comment avatars, keep emotion images inline, enlarge image previews, and add an in-page image lightbox.
# v10.5.4: Show modpack cover thumbs in the title column, lift image previews above popups, and restore per-row mod scrolling.
# v10.5.5: Enlarge title-column cover thumbs and allow the title text to share a little of the cover area.
# v10.5.6: Make title-column covers larger, keep favorite stars above covers, and add delayed cover hover preview.
# v10.5.7: Restore a visible page-size selector; cap inline mod previews so local HTML opens smoothly on Windows.
# v10.5.8: Build each row's complete mod list only when that row is opened.
# v10.5.9: Load the full mod list directly from the summary click, including browsers that do not bubble toggle events.
# v10.5.10: Write the default dashboard only to its stable local entry; version copies go straight to local archive.
# v10.5.11: Lazily render the complete original grouped mod-card preview on row expansion.
# v10.5.12: Compact the oversized pagination controls into a quiet table footer.
# v10.5.13: Default the dashboard to 25 rows per page.
# v10.5.14: Split comments into per-pack API data, load on demand, add an
#           in-popup comment search field, and shorten cover preview delay.
# v10.5.15: Keep generated artifacts under one dashboard folder and serve table
#           rows plus detail payloads through the local API.
# v10.5.16: Fold the local API server into this converter; one command now
#           generates, opens, and serves the dashboard.
# v10.5.17: Flatten trend history into one file, simplify root folders, and
#           reuse an already-running local dashboard port.
# v10.5.18: Remove the remaining Python string-escape warning from generated JS.
# v10.5.19: Escape whitespace regexp in the generated JavaScript template.
# v10.5.20: Escape the remaining JavaScript regexp templates for clean startup.
# v10.5.21: Finish escaping ordered-list regexp literals in the HTML template.
import re
import sys
import os
import json
import html as _html
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from collections import Counter
from datetime import date
import shutil

APP_VERSION = "v10.6.6"
# 部署 Cloudflare Worker 后，将公开 Worker 地址填在这里；留空时反馈按钮会说明未配置。
# 不要把个人域名/私有 Worker 地址提交到公开仓库；本机可在本地改此值，勿 push。
FEEDBACK_URL = ""
DEFAULT_OUTPUT_STEM = "\u591a\u5e73\u53f0\u805a\u5408\u770b\u677f_V1.0"
GENERATED_DASHBOARD_DIR = "converted_output"
OPEN_DASHBOARD_NAME = "点击打开.html"

def default_output_file():
    return "{}_{}.html".format(DEFAULT_OUTPUT_STEM, APP_VERSION)

# ───────────────────────── 配置 ─────────────────────────

INPUT_FILE  = "多平台爬虫数据_v1.0.jsonl"

FALLBACK_INPUT_FILE = "MC百科整合包数据.json"

# The converter does not use browser cache or cookies. Browser state belongs to
# the crawler only, under ignored_local_files/browser_data.
TREND_HISTORY_FILE = "trend_history.jsonl"

MCMOD_BASE  = "https://www.mcmod.cn/modpack/"

MCMOD_CLASS_CATEGORY_NAMES = {
    "1": "科技",
    "2": "魔法",
    "3": "冒险",
    "4": "农业",
    "5": "装饰",
    "6": "安全",
    "7": "LIB",
    "8": "资源",
    "9": "世界",
    "10": "群系",
    "11": "生物",
    "12": "能源",
    "13": "存储",
    "14": "物流",
    "15": "道具",
    "16": "红石",
    "17": "食物",
    "18": "模型",
    "19": "指南",
    "20": "破坏",
    "21": "魔改",
    "22": "Meme",
    "23": "实用",
    "24": "辅助",
    "25": "中式",
    "26": "日式",
    "27": "西式",
    "28": "恐怖",
    "29": "建材",
    "30": "生存",
    "31": "指令",
    "32": "优化",
    "33": "国创",
    "34": "关卡",
    "35": "结构",
}

# ═══════════════════════ 工具函数 ═══════════════════════

def _s(val):
    if val is None:
        return ""
    return str(val).strip()

def normalize_image_url(url, base="https://www.mcmod.cn/"):
    raw = _s(url)
    if not raw:
        return ""
    if raw.startswith("//"):
        return "https:" + raw
    return urllib.parse.urljoin(base, raw)

def normalize_image_list(value):
    out = []
    seen = set()
    if not value:
        return out
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            value = parsed
        except (TypeError, ValueError):
            value = [value]
    if not isinstance(value, (list, tuple)):
        value = [value]
    for idx, item in enumerate(value):
        if isinstance(item, dict):
            url = normalize_image_url(item.get("url") or item.get("src") or item.get("data-src"))
            alt = _s(item.get("alt") or item.get("title"))
            source = _s(item.get("source"))
            kind = _s(item.get("kind"))
            section = _s(item.get("section") or item.get("heading"))
            width = _s(item.get("width"))
            height = _s(item.get("height"))
        else:
            url = normalize_image_url(item)
            alt = ""
            source = ""
            kind = ""
            section = ""
            width = ""
            height = ""
        if not url or url in seen:
            continue
        if "loading" in url.lower() or "loadfail" in url.lower():
            continue
        seen.add(url)
        out.append({
            "url": url,
            "src": url,
            "alt": alt,
            "source": source,
            "kind": kind,
            "section": section,
            "width": width,
            "height": height,
            "index": idx + 1,
        })
    return out

def esc(text):
    return _html.escape(str(text), quote=False)

def esc_attr(text):
    return _html.escape(str(text), quote=True)

def fmt_order(v):
    if isinstance(v, (int, float)):
        if v == int(v):
            return str(int(v))
        return "{:.4g}".format(v)
    return str(v)

def today_str():
    d = date.today()
    return "{}.{}.{}".format(d.year, d.month, d.day)

def fmt_views(count):
    try:
        n = int(count)
    except (ValueError, TypeError):
        return str(count)
    if n >= 10000:
        s = "{:.2f}".format(n / 10000.0).rstrip("0").rstrip(".")
        return s + "万"
    return str(n)

# ═══════════════════════ 解析函数 ═══════════════════════

def parse_tags(val):
    raw = _s(val)
    if not raw:
        return []
    if "<span" in raw.lower():
        tags = re.findall(r">([^<]+)<", raw)
        tags = [t.strip() for t in tags if t.strip()]
        if tags:
            return tags
    m = re.search(r'data-search="([^"]*)"', raw)
    if m:
        raw = m.group(1)
    if any(c in raw for c in [",", "，", "、", ";", "；", "|", "/"]):
        parts = re.split(r"[,，、;；|/]", raw)
        return [p.strip() for p in parts if p.strip()]
    parts = raw.split()
    if parts:
        return parts
    return [raw] if raw else []

def parse_tag_details(val, fallback_names=None):
    fallback_names = fallback_names or []
    raw_items = val
    if isinstance(val, str):
        if not val.strip():
            raw_items = []
        else:
            try:
                raw_items = json.loads(val)
            except Exception:
                raw_items = []
    if not isinstance(raw_items, (list, tuple)):
        raw_items = []
    details = []
    seen = set()
    for item in raw_items:
        if isinstance(item, dict):
            name = _s(item.get("name") or item.get("title") or item.get("标签") or item.get("分类"))
            url = _s(item.get("url") or item.get("href") or item.get("link") or item.get("链接"))
            tip = _s(item.get("title") or item.get("tooltip") or item.get("desc") or item.get("说明"))
            color = _s(item.get("color") or item.get("style"))
        else:
            name = _s(item)
            url = tip = color = ""
        if not name or name in seen:
            continue
        seen.add(name)
        details.append({"name": name, "url": url, "title": tip, "color": color})
    for name in fallback_names:
        if name and name not in seen:
            seen.add(name)
            details.append({"name": name, "url": "", "title": "", "color": ""})
    return details

def parse_mods(val):
    if not val:
        return []
    raw_items = val
    if isinstance(val, str):
        try:
            raw_items = json.loads(val)
        except Exception:
            names = parse_tags(val)
            return [{"name": n, "title": n, "url": "", "class_id": "", "version": ""} for n in names]
    if not isinstance(raw_items, (list, tuple)):
        return []
    mods = []
    seen = set()
    for item in raw_items:
        if isinstance(item, dict):
            name = _s(item.get("name") or item.get("名称") or item.get("title") or item.get("标题"))
            title = _s(item.get("title") or item.get("标题") or name)
            url = _s(item.get("url") or item.get("链接"))
            class_id = _s(item.get("class_id") or item.get("id") or item.get("模组ID"))
            version = _s(item.get("version") or item.get("版本"))
            category_id = _s(item.get("category_id") or item.get("分类ID"))
            category_name = _s(item.get("category_name") or item.get("分类"))
            category_url = _s(item.get("category_url") or item.get("分类链接"))
            group_name = _s(item.get("group_name") or item.get("分类组"))
        else:
            name = _s(item)
            title = name
            url = ""
            class_id = ""
            version = ""
            category_id = ""
            category_name = ""
            category_url = ""
            group_name = ""
        if not name and not title:
            continue
        if not url and class_id:
            url = "https://www.mcmod.cn/class/{}.html".format(class_id)
        if not category_name and category_id:
            category_name = MCMOD_CLASS_CATEGORY_NAMES.get(category_id, "分类 {}".format(category_id))
        if not category_url and category_id:
            category_url = "https://www.mcmod.cn/class/category/{}-1.html".format(category_id)
        key = url or class_id or name or title
        if key in seen:
            continue
        seen.add(key)
        mods.append({
            "name": name or title,
            "title": title or name,
            "url": url,
            "class_id": class_id,
            "version": version,
            "category_id": category_id,
            "category_name": category_name,
            "category_url": category_url,
            "group_name": group_name,
        })
    return mods

def parse_views(val):
    raw = _s(val)
    if not raw:
        return "", 0
    m = re.match(r"^([\d.]+)\s*万$", raw)
    if m:
        num = float(m.group(1))
        return raw, int(num * 10000)
    if "万" in raw:
        num_str = raw.replace("万", "").replace(",", "").strip()
        try:
            num = float(num_str)
            return raw, int(num * 10000)
        except ValueError:
            pass
    clean = raw.replace(",", "").replace("，", "").strip()
    try:
        num = float(clean)
        return raw, int(num)
    except ValueError:
        return raw, 0

def parse_views_count(val):
    raw = _s(val)
    if not raw:
        return "", 0
    if "万" in raw:
        try:
            num = float(raw.replace("万", "").replace(",", "").strip())
            return int(num * 10000), int(num * 10000)
        except ValueError:
            pass
    clean = raw.replace(",", "").replace("，", "").strip()
    try:
        num = float(clean)
        return int(num), int(num)
    except ValueError:
        return raw, 0

def parse_number(val):
    raw = _s(val)
    if not raw:
        return "", 0
    if "<" in raw:
        m = re.search(r'data-order="([^"]*)"', raw)
        display = re.sub(r"<[^>]+>", "", raw).strip()
        if m:
            try:
                return display, float(m.group(1))
            except ValueError:
                pass
        try:
            return display, float(display)
        except ValueError:
            return display, 0
    clean = raw.replace(",", "").replace("，", "").strip()
    try:
        return raw, float(clean)
    except ValueError:
        return raw, 0

def parse_pct(val):
    raw = _s(val)
    if not raw:
        return "", 0
    clean = raw.replace("%", "").replace("％", "").strip()
    try:
        return raw, float(clean)
    except ValueError:
        return raw, 0

def format_pct_display(val_str, val_num):
    if not val_str or val_str == "—":
        return "—"
    if "%" in str(val_str):
        return str(val_str)
    try:
        if val_num is not None:
            return "{:+.0f}%".format(val_num) if val_num != 0 else "0%"
    except (TypeError, ValueError):
        pass
    return str(val_str)

def parse_trend_json(val):
    raw = _s(val)
    if not raw:
        return []
    raw = raw.strip()
    try:
        arr = json.loads(raw)
    except (ValueError, TypeError):
        return []
    out = []
    if isinstance(arr, list):
        for it in arr:
            if isinstance(it, dict):
                d_v = it.get("日期") or it.get("date") or ""
                i_v = it.get("指数") if "指数" in it else it.get("index", 0)
                try:
                    i_v = float(i_v)
                except (ValueError, TypeError):
                    i_v = 0
                out.append((str(d_v), i_v))
    return out

def clean_intro_text(text):
    raw = _s(text).replace("\r\n", "\n").replace("\r", "\n")
    if not raw:
        return ""
    lines = []
    for line in raw.split("\n"):
        t = re.sub(r"\s+", " ", line.replace("\u00a0", " ")).strip()
        if t:
            lines.append(t)
    if not lines:
        return ""
    def is_toc(line):
        return line.startswith("目录:") or line.startswith("目录：") or line == "目录"
    def is_intro_heading(line):
        return re.match(r"^(?:\d+(?:\.\d+)*\s*)?简介[:：]?$", line) is not None
    heading_words = (
        "说明", "一些说明及建议", "配置需求", "DLC管理器相关", "特别鸣谢",
        "整合特征介绍", "性能优化", "功能辅助", "兼容版本", "整合内容摘要", "常见问题",
        "先来说点啥吧", "一些游戏内图片",
    )
    def is_heading(line):
        if is_intro_heading(line):
            return True
        if re.match(r"^\d+(?:\.\d+)*\s+\S{1,30}$", line):
            return True
        return any(line == w or line == w + "：" or line == w + ":" for w in heading_words)
    seen = set()
    compact = []
    for line in lines:
        key = re.sub(r"\s+", "", line)
        if not key or is_toc(line) or key in seen:
            continue
        seen.add(key)
        compact.append(line)
    start = -1
    for i, line in enumerate(compact):
        if is_intro_heading(line):
            start = i + 1
            break
    if start >= 0:
        picked = compact[start:]
    else:
        picked = compact
    noise_re = re.compile(r"^(过于丰富的|明确的阶段引导|数量庞大的|可制作的|丰富的BOSS指引)[:：]?$")
    cleaned = []
    max_intro_chars = 30000
    for line in picked:
        if is_toc(line) or noise_re.match(line):
            continue
        if len("\n".join(cleaned)) + len(line) > max_intro_chars:
            break
        cleaned.append(line)
    return "\n\n".join(cleaned).strip() or raw

def compute_growth_pct(trend, days):
    if not trend or len(trend) < 2:
        return "—", None
    latest = trend[-1][1]
    if len(trend) >= days + 1:
        base = trend[-(days + 1)][1]
    else:
        base = trend[0][1]
    if base == 0:
        if latest == 0:
            return "0%", 0.0
        return "—", None
    pct = (latest - base) / base * 100
    return "{:+.0f}%".format(round(pct)), round(pct, 2)

def compute_total_growth_pct(trend):
    if not trend or len(trend) < 2:
        return "—", None
    latest = trend[-1][1]
    base = trend[0][1]
    if base == 0:
        if latest == 0:
            return "0%", 0.0
        return "—", None
    pct = (latest - base) / base * 100
    return "{:+.0f}%".format(round(pct)), round(pct, 2)

def normalize_trend_points(points):
    by_date = {}
    for item in points or []:
        if isinstance(item, dict):
            day = _s(item.get("date") or item.get("日期") or item.get("captured_at") or item.get("抓取日期"))
            val = item.get("index") if "index" in item else item.get("指数")
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            day, val = item[0], item[1]
        else:
            continue
        day = _s(day)[:10]
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            continue
        by_date[day] = val
    return sorted(by_date.items(), key=lambda x: x[0])

def load_local_trend_history(history_file):
    """Load the compact single-file trend store once, indexed by platform/id."""
    history = {}
    if not history_file or not os.path.exists(history_file):
        return history
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                key = (str(obj.get("platform") or ""), str(obj.get("stable_id") or ""))
                if key[0] and key[1]:
                    history.setdefault(key, []).append(obj)
    except OSError:
        return {}
    return {key: normalize_trend_points(points) for key, points in history.items()}

def apply_local_trend_history(data, history_file=TREND_HISTORY_FILE):
    history = load_local_trend_history(history_file)
    applied = 0
    for d in data:
        mid = _extract_mid(d.get("url", ""))
        if not mid:
            continue
        local_trend = history.get(("mcmod", mid), [])
        if len(local_trend) < 2:
            continue
        existing = normalize_trend_points(d.get("trend_arr") or [])
        merged = normalize_trend_points(existing + local_trend)
        if len(merged) < 2:
            continue
        d["trend_arr"] = merged
        latest = merged[-1][1]
        vals = [x[1] for x in merged]
        d["lat_n"] = latest
        d["lat_d"] = str(int(latest)) if latest == int(latest) else "{:.2f}".format(latest).rstrip("0").rstrip(".")
        d["max_n"] = max(vals)
        d["max_d"] = str(int(d["max_n"])) if d["max_n"] == int(d["max_n"]) else "{:.2f}".format(d["max_n"]).rstrip("0").rstrip(".")
        avg = sum(vals) / len(vals)
        d["avg_n"] = round(avg, 2)
        d["avg_d"] = str(int(round(avg)))
        d["tc_n"] = len(merged)
        d["tc_d"] = str(len(merged))
        d["t7_d"], d["t7_n"] = compute_growth_pct(merged, 7)
        d["t30_d"], d["t30_n"] = compute_growth_pct(merged, 30)
        d["t60_d"], d["t60_n"] = compute_growth_pct(merged, 60)
        d["tall_d"], d["tall_n"] = compute_total_growth_pct(merged)
        applied += 1
    return applied

def parse_title_and_url(title_val, id_url_val=None):
    raw = _s(title_val).replace('\n', ' ')
    if not raw:
        return "", "#"
    if "<a" in raw.lower():
        href_m = re.search(r'href="([^"]+)"', raw)
        text_m = re.search(r'>([^<]*)</a>', raw)
        href = href_m.group(1).strip() if href_m else "#"
        text = text_m.group(1).strip() if text_m else re.sub(r"<[^>]+>", "", raw).strip()
        return text, href
    if id_url_val is not None:
        id_str = _s(id_url_val)
        if id_str:
            if id_str.isdigit():
                return raw, "{}{}.html".format(MCMOD_BASE, id_str)
            if id_str.startswith("http"):
                return raw, id_str
            m = re.search(r"/(\d+)\.html", id_str)
            if m:
                return raw, "{}{}.html".format(MCMOD_BASE, m.group(1))
    m = re.search(r"mcmod\.cn/modpack/(\d+)", raw)
    if m:
        title_text = re.sub(r"<[^>]+>", "", raw).strip()
        return title_text, "{}{}.html".format(MCMOD_BASE, m.group(1))
    return raw, "#"

# ═══════════════════════ JSON 读取 ═══════════════════════

def read_json(path):
    rows = []
    meta = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and item.get("source") == "mcmod":
                rows.append(item.get("normalized") or item.get("data") or item.get("raw") or {})
    meta = {"type": "multi-platform-jsonl", "version": "v1.0"}
    return rows, meta

def first_value(row, *keys, default=""):
    for key in keys:
        if isinstance(row, dict) and key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return default

def comments_to_json_text(val):
    if val in (None, ""):
        return ""
    if isinstance(val, str):
        return val
    try:
        return json.dumps(val, ensure_ascii=False)
    except TypeError:
        return ""

def data_quality(d):
    desc = _s(d.get("desc"))
    lines = [x.strip() for x in desc.splitlines() if x.strip()]
    numeric_lines = sum(1 for x in lines if re.match(r"^\d+(?:\.\d+)*$", x))
    chinese_sentence = 1 if re.search(r"[\u4e00-\u9fff]{8,}", desc) else 0
    score = 0
    score += chinese_sentence * 100
    score += min(len(desc), 500) / 10
    score -= numeric_lines * 20
    if float(d.get("score_n") or 0) > 0:
        score += 40
    score += min(int(d.get("tc_n") or 0), 60)
    score += min(len(d.get("pack") or []), 12) * 5
    score += min(len(d.get("cat") or []), 8) * 2
    score += int(float(d.get("com_n") or 0))
    if d.get("comments_raw"):
        score += 30
    return score

def dedupe_data(data):
    picked = {}
    order = []
    for d in data:
        key = d.get("url") or d.get("title")
        if not key:
            order.append(key)

def parse_title_and_url(title_val, id_url_val=None):
    raw = _s(title_val).replace('\n', ' ')
    if not raw:
        return "", "#"
    if "<a" in raw.lower():
        href_m = re.search(r'href="([^"]+)"', raw)
        text_m = re.search(r'>([^<]*)</a>', raw)
        href = href_m.group(1).strip() if href_m else "#"
        text = text_m.group(1).strip() if text_m else re.sub(r"<[^>]+>", "", raw).strip()
        return text, href
    if id_url_val is not None:
        id_str = _s(id_url_val)
        if id_str:
            if id_str.isdigit():
                return raw, "{}{}.html".format(MCMOD_BASE, id_str)
            if id_str.startswith("http"):
                return raw, id_url_val
            m = re.search(r"/(\d+)\.html", id_str)
            if m:
                return raw, "{}{}.html".format(MCMOD_BASE, m.group(1))
    m = re.search(r"mcmod\.cn/modpack/(\d+)", raw)
    if m:
        title_text = re.sub(r"<[^>]+>", "", raw).strip()
        return title_text, "{}{}.html".format(MCMOD_BASE, m.group(1))
    return raw, "#"

# ═══════════════════════ JSON 读取 ═══════════════════════

def read_json(path):
    rows = []
    if path.endswith('.js'):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        prefix = 'window.tableRowsData = '
        if text.startswith(prefix):
            items = json.loads(text[len(prefix):].rstrip(';\n '))
            return items, {"type": "table_rows_js", "version": "v1.0"}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict) and item.get("source") == "mcmod":
                rows.append(item.get("normalized") or item.get("data") or item.get("raw") or {})
    meta = {"type": "multi-platform-jsonl", "version": "v1.0"}
    return rows, meta

def first_value(row, *keys, default=""):
    for key in keys:
        if isinstance(row, dict) and key in row and row.get(key) not in (None, ""):
            return row.get(key)
    return default

def comments_to_json_text(val):
    if val in (None, ""):
        return ""
    if isinstance(val, str):
        return val
    try:
        return json.dumps(val, ensure_ascii=False)
    except TypeError:
        return ""

def data_quality(d):
    desc = _s(d.get("desc"))
    lines = [x.strip() for x in desc.splitlines() if x.strip()]
    numeric_lines = sum(1 for x in lines if re.match(r"^\d+(?:\.\d+)*$", x))
    chinese_sentence = 1 if re.search(r"[\u4e00-\u9fff]{8,}", desc) else 0
    score = 0
    score += chinese_sentence * 100
    score += min(len(desc), 500) / 10
    score -= numeric_lines * 20
    score += int(float(d.get("com_n") or 0))
    if d.get("comments_raw"):
        score += 30
    return score

def dedupe_data(data):
    picked = {}
    order = []
    for d in data:
        key = d.get("url") or d.get("title")
        if not key:
            order.append(key)
            continue
        if key not in picked:
            picked[key] = d
            order.append(key)
            continue
        old = picked[key]
        if data_quality(d) > data_quality(old):
            picked[key] = d
    return [picked[k] for k in order if k in picked]

def normalize_json_row(row):
    if not isinstance(row, dict):
        return None
    if "basic" in row and isinstance(row.get("basic"), dict):
        basic = dict(row.get("basic") or {})
        merged = dict(basic)
        merged["链接"] = row.get("url") or basic.get("链接", "")
        merged["整合包介绍"] = row.get("intro") or basic.get("整合包介绍", "")
        merged["评论总数"] = row.get("comment_total", basic.get("评论总数", 0))
        merged["评论详情"] = row.get("comments", basic.get("评论详情", []))
        merged["包含模组"] = row.get("mods") or basic.get("包含模组", [])
        merged["模组数量"] = row.get("mod_count") or basic.get("模组数量", 0)
        merged["intro_images"] = row.get("intro_images") or basic.get("intro_images") or []
        merged["comment_images"] = row.get("comment_images") or basic.get("comment_images") or []
        merged["cover_image"] = row.get("cover_image") or basic.get("cover_image") or ""
        if isinstance(row.get("trend"), dict):
            merged.update(row["trend"])
        row = merged
    return row

def process_data(raw_rows):
    data = []
    for row in raw_rows:
        row = normalize_json_row(row)
        if not row:
            continue
        if all(_s(v) == "" for v in row.values()):
            continue
        title, url = parse_title_and_url(first_value(row, "标题", "名称", "整合包名"), first_value(row, "链接", "url", "地址"))
        vc_d, vc_n = parse_views_count(first_value(row, "总浏览量"))
        if vc_n == 0:
            v_d, v_n = parse_views(first_value(row, "总浏览"))
            views_d = v_d
            views_n = v_n
        else:
            views_d = fmt_views(vc_n)
            views_n = vc_n
        comment_display = first_value(row, "评论总数", "评论数", "评论")
        score_d, score_n = parse_number(first_value(row, "指数评分", "评分"))
        rec_d, rec_n = parse_number(first_value(row, "推荐数", "推荐"))
        fav_d, fav_n = parse_number(first_value(row, "收藏数", "收藏"))
        com_d, com_n = parse_number(comment_display)
        max_d, max_n = parse_number(first_value(row, "走势最高指数", "最高指数", "最高"))
        avg_d, avg_n = parse_number(first_value(row, "走势平均指数", "平均指数", "平均"))
        lat_d, lat_n = parse_number(first_value(row, "走势最新指数", "最新指数", "最新", "昨日指数"))
        cat_tags = parse_tags(first_value(row, "分类标签", "分类"))
        pack_tags = parse_tags(first_value(row, "整合包标签", "标签"))
        cat_tag_details = parse_tag_details(first_value(row, "category_tag_details", "分类标签详情", "分类详情"), cat_tags)
        pack_tag_details = parse_tag_details(first_value(row, "pack_tag_details", "整合包标签详情", "标签详情"), pack_tags)
        modpack_type = _s(first_value(row, "modpack_type", "整合包类型", "类型")).strip() or "未标明"
        modpack_type_url = _s(first_value(row, "modpack_type_url", "整合包类型链接", "类型链接")).strip()
        mods = parse_mods(first_value(row, "包含模组", "mods", "模组"))
        mod_names = [m.get("name", "") for m in mods if m.get("name")]
        mod_categories = []
        seen_mod_categories = set()
        for m in mods:
            cname = m.get("category_name") or ""
            cid = m.get("category_id") or ""
            label = cname or ("分类 {}".format(cid) if cid else "")
            if label and label not in seen_mod_categories:
                seen_mod_categories.add(label)
                mod_categories.append(label)
        rv_d, rv_n = parse_number(first_value(row, "红票数"))
        rp_d, rp_n = parse_pct(first_value(row, "红票%"))
        bp_d_v, bp_n_v = parse_number(first_value(row, "黑票数"))
        bp_d, bp_n = parse_pct(first_value(row, "黑票%"))
        trend_data = first_value(row, "指数走势数据", "走势数据")
        if isinstance(trend_data, (list, tuple)):
            trend_data = json.dumps(trend_data, ensure_ascii=False)
        tc_d, tc_n = parse_number(first_value(row, "走势数据点"))
        trend_arr = parse_trend_json(trend_data)
        if tc_n == 0 and trend_arr:
            tc_d, tc_n = str(len(trend_arr)), len(trend_arr)
        t7_d, t7_n = parse_number(first_value(row, "走势涨幅_7天", "涨幅_7天", "涨幅7"))
        if t7_n == 0 and trend_arr:
            t7_d, t7_n = compute_growth_pct(trend_arr, 7)
        else:
            t7_d = format_pct_display(t7_d, t7_n)
        t30_d, t30_n = parse_number(first_value(row, "走势涨幅_30天", "涨幅_30天", "涨幅30"))
        if t30_n == 0 and trend_arr:
            t30_d, t30_n = compute_growth_pct(trend_arr, 30)
        else:
            t30_d = format_pct_display(t30_d, t30_n)
        t60_d, t60_n = parse_number(first_value(row, "走势涨幅_60天", "涨幅_60天", "涨幅60"))
        if t60_n == 0 and trend_arr:
            t60_d, t60_n = compute_growth_pct(trend_arr, 60)
        else:
            t60_d = format_pct_display(t60_d, t60_n)
        tall_d, tall_n = compute_total_growth_pct(trend_arr)
        desc_text = clean_intro_text(first_value(row, "整合包介绍", "介绍"))
        intro_images = normalize_image_list(first_value(row, "intro_images"))
        cover_image = normalize_image_url(first_value(row, "cover_image"))
        if cover_image:
            intro_images = normalize_image_list([{"url": cover_image, "alt": title, "source": "cover"}] + intro_images)
        comment_images = normalize_image_list(first_value(row, "comment_images"))
        comments_raw = comments_to_json_text(first_value(row, "评论详情", "comments"))
        data.append({
            "title": title, "url": url,
            "desc": desc_text, "comments_raw": comments_raw, "trend_arr": trend_arr,
            "intro_images": intro_images, "comment_images": comment_images, "cover_image": cover_image,
            "comment_total": _s(first_value(row, "评论总数", "评论数")),
            "score_d": score_d, "score_n": score_n,
            "views_d": views_d, "views_n": views_n,
            "rec_d": rec_d, "rec_n": rec_n,
            "fav_d": fav_d, "fav_n": fav_n,
            "com_d": com_d, "com_n": com_n,
            "max_d": max_d, "max_n": max_n,
            "avg_d": avg_d, "avg_n": avg_n,
            "lat_d": lat_d, "lat_n": lat_n,
            "cat": cat_tags, "pack": pack_tags,
            "cat_details": cat_tag_details, "pack_details": pack_tag_details,
            "modpack_type": modpack_type, "modpack_type_url": modpack_type_url,
            "mods": mods, "mod_names": mod_names, "mod_categories": mod_categories,
            "rv_d": rv_d, "rv_n": rv_n,
            "rp_d": rp_d, "rp_n": rp_n,
            "bp_d": bp_d, "bp_n": bp_n,
            "bpv_d": bp_d_v, "bpv_n": bp_n_v,
            "tc_d": tc_d, "tc_n": tc_n,
            "t7_d": t7_d, "t7_n": t7_n if t7_n is not None else 0,
            "t30_d": t30_d, "t30_n": t30_n if t30_n is not None else 0,
            "t60_d": t60_d, "t60_n": t60_n if t60_n is not None else 0,
            "tall_d": tall_d, "tall_n": tall_n if tall_n is not None else 0,
        })
    return dedupe_data(data)

# ═══════════════════════ 筛选选项 ═══════════════════════

def build_category_options(data):
    c = Counter()
    for d in data:
        c.update(d["cat"])
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))

def build_packtag_options(data):
    c = Counter()
    for d in data:
        c.update(d["pack"])
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))

def build_modpack_type_options(data):
    c = Counter()
    for d in data:
        c.update([d.get("modpack_type") or "未标明"])
    return sorted(c.items(), key=lambda x: (x[0] == "未标明", -x[1], x[0]))

def build_mod_options(data):
    c = Counter()
    for d in data:
        c.update(d.get("mod_names", []))
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))

def build_mod_category_options(data):
    c = Counter()
    for d in data:
        c.update(d.get("mod_categories", []))
    return sorted(c.items(), key=lambda x: (-x[1], x[0]))

def build_trend_filter_options(data):
    specs = [
        ("7_in", "7天内（刚出新包）", lambda n: n <= 7),
        ("7-14", "7-14天（两周内成长包）", lambda n: 8 <= n <= 14),
        ("14-30", "14-30天（半月到满月稳定包）", lambda n: 15 <= n <= 30),
        ("30_in", "30天内（大集合）", lambda n: n <= 30),
        ("30-59", "30-59天（成长中期包）", lambda n: 31 <= n <= 59),
        ("60", "至少60天（历史老包）", lambda n: n >= 60),
    ]
    out = []
    for value, label, pred in specs:
        count = sum(1 for d in data if pred(int(d.get("tc_n") or 0)))
        out.append((value, label, count))
    return out

# ═══════════════════════ 美化版行生成 ═══════════════════════

def _growth_class(num):
    if num is None or num == 0:
        return "td-flat"
    return "td-up" if num > 0 else "td-down"

def gen_sparkline_svg_path(trend_arr):
    if not trend_arr or len(trend_arr) < 2:
        return "M 0 12 L 100 12", "M 0 12 L 100 12 L 100 24 L 0 24 Z"
    vals = [it[1] for it in trend_arr]
    min_v = min(vals)
    max_v = max(vals)
    diff = max_v - min_v
    if diff == 0:
        diff = 1
    points = []
    n = len(vals)
    for i, val in enumerate(vals):
        x = (i / (n - 1)) * 100
        y = 22 - ((val - min_v) / diff) * 20
        points.append((x, y))
    
    sparkline_path = "M " + " L ".join("{:.1f} {:.1f}".format(x, y) for x, y in points)
    sparkline_closed = sparkline_path + " L {:.1f} 24 L {:.1f} 24 Z".format(points[-1][0], points[0][0])
    return sparkline_path, sparkline_closed

def _extract_mid(url):
    """从 url https://www.mcmod.cn/modpack/1159.html 提取 ID 1159"""
    m = re.search(r'/modpack/(\d+)', url or '')
    return m.group(1) if m else ''

def split_modpack_title(title):
    title = _s(title).strip()
    if not title:
        return "", ""
    m = re.match(r'^(.*?)\s*[\(（]([^()（）]{2,120})[\)）]\s*$', title)
    if m:
        cn = re.sub(r'\s+', ' ', m.group(1)).strip()
        en = re.sub(r'\s+', ' ', m.group(2)).strip()
        return cn or title, en
    return title, ""

def gen_row_pretty(d, idx=0):
    mid = _extract_mid(d.get("url", ""))
    title_cn, title_en = split_modpack_title(d.get("title", ""))
    title_en_html = esc(title_en) if title_en else "&nbsp;"
    cover_image = normalize_image_url(d.get("cover_image") or "")
    cover_html = ""
    title_extra_class = ""
    if cover_image:
        title_extra_class = " has-cover"
        cover_html = (
            '<button type="button" class="modpack-cover-thumb image-thumb" '
            'data-image-url="{cover}" title="{title} 封面（悬停 1 秒放大）" aria-label="查看整合包封面">'
            '<img src="{cover}" alt="{title} 封面" loading="lazy" referrerpolicy="no-referrer">'
            '</button>'
        ).format(cover=esc_attr(cover_image), title=esc_attr(title_cn or d.get("title", "")))
    type_name = d.get("modpack_type") or "未标明"
    type_url = d.get("modpack_type_url") or ""
    if type_url:
        type_badge = '<a class="modpack-type-badge" href="{}" target="_blank" title="打开 MC百科类型页">{}</a>'.format(esc_attr(type_url), esc(type_name))
    else:
        type_badge = '<span class="modpack-type-badge">{}</span>'.format(esc(type_name))
    views_badge = '<span class="modpack-views-badge" title="总浏览量">👁 {}</span>'.format(esc(d["views_d"]))
    L = []
    L.append('            <tr data-row="{}" data-mid="{}">'.format(idx, esc_attr(mid)))
    # 标题（链接，hover 触发预览卡片）
    L.append(
        '                <td class="td-title{title_extra_class}" data-type-search="{type_name}" data-name="{name_order}" data-order="{name_order}" data-views="{views_n}">'
        '<button type="button" class="fav-star" data-mid="{mid}" title="收藏用于对比" aria-label="收藏用于对比">★</button>'
        '{cover_html}'
        '<a href="{url}" target="_blank" class="modpack-link" data-url="{url}" data-mid="{mid}" data-full-title="{full_title}">'
        '<span class="modpack-title-cn">{title_cn}</span><span class="modpack-title-en">{title_en}</span></a>'
        '<div class="modpack-meta-row">{type_badge}{views_badge}</div></td>'.format(
            url=esc_attr(d["url"]), mid=mid, full_title=esc_attr(d["title"]),
            title_extra_class=title_extra_class, cover_html=cover_html,
            title_cn=esc(title_cn), title_en=title_en_html,
            name_order=esc_attr((title_cn or d.get("title", "")).lower()),
            views_n=int(d.get("views_n") or 0),
            type_name=esc_attr(type_name), type_badge=type_badge, views_badge=views_badge)
    )
    # 总浏览量

    # trend helper for tooltips
    trend_vals_str = ""
    trend_dates_str = ""
    if d.get("trend_arr"):
        trend_vals_str = ",".join(str(it[1]) for it in d["trend_arr"])
        trend_dates_str = ",".join(it[0] for it in d["trend_arr"])
    trend_data_attrs = 'data-trend="{}" data-dates="{}" data-title="{}"'.format(
        esc_attr(trend_vals_str), esc_attr(trend_dates_str), esc_attr(d["title"])
    )

    # Column 3: Index Trend
    sparkline_path, sparkline_closed = gen_sparkline_svg_path(d["trend_arr"])
    col3_html = (
        '                <td class="td-trend" data-score="{score_n}" data-lat="{lat_n}" data-max="{max_n}" data-avg="{avg_n}" data-days="{days_n}" data-order="{score_n}" {trend_data_attrs}>'
        '<div class="trend-consolidated-cell">'
        '<div class="trend-score-badge" title="官方流行指数评分"><span>流行</span><b>{score_d}</b></div>'
        '<div class="trend-main-row">'
        '<svg class="sparkline-svg" viewBox="0 0 100 24" width="118" height="34" style="opacity: 0.95;">'
        '<path d="{sparkline_closed}" fill="rgba(var(--primary-rgb), 0.1)"></path>'
        '<path d="{sparkline_path}" fill="none" stroke="var(--primary)" stroke-width="2" stroke-linecap="round"></path>'
        '</svg>'
        '<span class="trend-val-lat" title="最新指数" style="font-weight: 700; color: var(--primary-light);">最新: {lat_d}</span>'
        '<span class="trend-open-hint">点击看图</span>'
        '</div>'
        '<div class="trend-meta-row">'
        '<span class="trend-val-max" title="最高指数">高: {max_d}</span>'
        '<span class="trend-val-avg" title="平均指数">平: {avg_d}</span>'
        '<span class="trend-val-days" title="走势天数">{days_d}天</span>'
        '</div>'
        '</div></td>'
    ).format(
        score_n=fmt_order(d["score_n"]),
        lat_n=fmt_order(d["lat_n"]),
        max_n=fmt_order(d["max_n"]),
        avg_n=fmt_order(d["avg_n"]),
        days_n=fmt_order(d["tc_n"]),
        trend_data_attrs=trend_data_attrs,
        sparkline_closed=sparkline_closed,
        sparkline_path=sparkline_path,
        score_d=esc(d["score_d"]),
        lat_d=esc(d["lat_d"]),
        max_d=esc(d["max_d"]),
        avg_d=esc(d["avg_d"]),
        days_d=esc(d["tc_d"])
    )
    L.append(col3_html)

    # Column 4: Growth Rates
    col4_html = (
        '                <td class="td-trend" data-t7="{t7_n}" data-t30="{t30_n}" data-t60="{t60_n}" data-tall="{tall_n}" data-order="{t7_n}" {trend_data_attrs}>'
        '<div class="growth-consolidated-cell" style="display: flex; flex-direction: column; gap: 2px; font-size: 0.76rem;">'
        '<div style="display: flex; justify-content: space-between; gap: 8px;">'
        '<span class="growth-val-t7 {t7_cls}" title="7日涨幅">7日: {t7_d}</span>'
        '<span class="growth-val-t30 {t30_cls}" title="30日涨幅">30日: {t30_d}</span>'
        '</div>'
        '<div style="display: flex; justify-content: space-between; gap: 8px;">'
        '<span class="growth-val-t60 {t60_cls}" title="60日涨幅">60日: {t60_d}</span>'
        '<span class="growth-val-tall {tall_cls}" title="总涨幅">总幅: {tall_d}</span>'
        '</div>'
        '</div></td>'
    ).format(
        t7_n=fmt_order(d["t7_n"]),
        t30_n=fmt_order(d["t30_n"]),
        t60_n=fmt_order(d["t60_n"]),
        tall_n=fmt_order(d["tall_n"]),
        trend_data_attrs=trend_data_attrs,
        t7_cls=_growth_class(d["t7_n"]),
        t30_cls=_growth_class(d["t30_n"]),
        t60_cls=_growth_class(d["t60_n"]),
        tall_cls=_growth_class(d["tall_n"]),
        t7_d=esc(d["t7_d"]),
        t30_d=esc(d["t30_d"]),
        t60_d=esc(d["t60_d"]),
        tall_d=esc(d["tall_d"])
    )
    L.append(col4_html)

    # Column 5: Votes & Ratings
    col5_html = (
        '                <td class="td-votes" data-rv="{rv_n}" data-rp="{rp_n}" data-bv="{bv_n}" data-bp="{bp_n}" data-order="{rv_n}">'
        '<div class="votes-consolidated-cell" style="display: flex; flex-direction: column; gap: 4px; padding: 4px 0; font-size: 0.76rem;">'
        '<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">'
        '<span style="font-weight: 700; color: var(--success); font-size: 0.82rem;">{rv_d} 票</span>'
        '<span style="font-size: 0.72rem; padding: 1px 5px; border-radius: 6px; background: rgba(16, 185, 129, 0.12); color: var(--success); font-weight: 600;">{rp_d}% 红</span>'
        '</div>'
        '<div class="vote-ratio-bar" style="width: 100%; height: 5px; border-radius: 3px; background: rgba(128,128,128,0.15); display: flex; overflow: hidden; margin: 2px 0;" title="红占比: {rp_d}% | 黑占比: {bp_d}%">'
        '<div class="vote-ratio-red" style="height: 100%; width: {rp_d}%; background: var(--success);"></div>'
        '<div class="vote-ratio-black" style="height: 100%; width: {bp_d}%; background: #6b7280;"></div>'
        '</div>'
        '<div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted);">'
        '<span>黑票: {bv_d}</span>'
        '<span>占比: {bp_d}%</span>'
        '</div>'
        '</div></td>'
    ).format(
        rv_n=fmt_order(d["rv_n"]),
        rp_n=fmt_order(d["rp_n"]),
        bv_n=fmt_order(d["bpv_n"]),
        bp_n=fmt_order(d["bp_n"]),
        rv_d=esc(d["rv_d"]),
        rp_d=esc(d["rp_d"].rstrip('%') if d["rp_d"] else "0"),
        bv_d=esc(d["bpv_d"]),
        bp_d=esc(d["bp_d"].rstrip('%') if d["bp_d"] else "0")
    )
    L.append(col5_html)

    # 推荐 / 收藏 / 评论
    engagement_html = (
        '                <td class="td-engage td-comment" data-rec="{rec_n}" data-fav="{fav_n}" data-com="{com_n}" data-order="{com_n}" data-mid="{mid}">'
        '<div class="engage-cell">'
        '<span><b>{rec_d}</b><em>推</em></span>'
        '<span><b>{fav_d}</b><em>藏</em></span>'
        '<span class="engage-comment-trigger" role="button" tabindex="0" title="点击评论格打开 / 再点关闭"><b>{com_d}</b><em>评</em><i class="comment-open-dot" aria-hidden="true">⌕</i></span>'
        '</div></td>'
    ).format(
        rec_n=fmt_order(d["rec_n"]),
        fav_n=fmt_order(d["fav_n"]),
        com_n=fmt_order(d["com_n"]),
        mid=mid,
        rec_d=esc(d["rec_d"]),
        fav_d=esc(d["fav_d"]),
        com_d=esc(d["com_d"]),
    )
    L.append(engagement_html)
    # 分类标签 + 整合包标签
    search_cat = esc_attr(" ".join(d["cat"]))
    def render_filter_tag(item, cls):
        name = item.get("name", "") if isinstance(item, dict) else _s(item)
        url = item.get("url", "") if isinstance(item, dict) else ""
        tip = item.get("title", "") if isinstance(item, dict) else ""
        title = tip or name
        open_html = '<a class="tag-filter-open" href="{}" target="_blank" title="打开 MC百科标签页">↗</a>'.format(esc_attr(url)) if url else ''
        return '<span class="{}" data-tag="{}" title="{}"><span class="tag-filter-name">{}</span>{}</span>'.format(
            cls, esc_attr(name), esc_attr(title), esc(name), open_html
        )
    badges_cat = "".join(
        render_filter_tag(t, "tag-cat") for t in d.get("cat_details", [])
    )
    search_pack = esc_attr(" ".join(d["pack"]))
    badges_pack = "".join(
        render_filter_tag(t, "tag-pack") for t in d.get("pack_details", [])
    )
    tags_html = (
        '<div class="tag-group-block"><div class="tag-group-label tag-group-label-cat">整合包分类</div><div class="tag-group tag-group-cat">{}</div></div>'.format(badges_cat)
        if badges_cat else ''
    )
    tags_html += (
        '<div class="tag-group-block"><div class="tag-group-label tag-group-label-pack">整合包标签</div><div class="tag-group tag-group-pack">{}</div></div>'.format(badges_pack)
        if badges_pack else ''
    )
    tag_count = len(d.get("cat", [])) + len(d.get("pack", []))
    L.append('                <td class="td-tags" data-search="{}" data-cat-search="{}" data-pack-search="{}" data-count="{}" data-order="{}"><div class="tag-wrap tag-combo-container">{}</div></td>'.format(
        esc_attr(" ".join(d["cat"] + d["pack"])), search_cat, search_pack, tag_count, tag_count, tags_html if tags_html else '<span class="tag-empty">—</span>'))
    mod_search_parts = []
    mod_groups = []
    group_map = {}
    for m in d.get("mods", []):
        cat_name = m.get("category_name") or "未分类"
        cat_id = m.get("category_id") or ""
        key = "{}|{}".format(cat_id, cat_name)
        if key not in group_map:
            group_map[key] = {
                "name": cat_name,
                "url": m.get("category_url") or "",
                "mods": [],
            }
            mod_groups.append(group_map[key])
        group_map[key]["mods"].append(m)
        mod_search_parts.extend([
            m.get("name", ""),
            m.get("title", ""),
            m.get("version", ""),
            m.get("category_name", ""),
            m.get("group_name", ""),
        ])
    mod_sections = []
    mod_summary_chips = []
    preview_limit = 8
    preview_used = 0
    hidden_mod_count = 0
    for group_idx, group in enumerate(mod_groups):
        links = []
        for m in group["mods"]:
            name = m.get("name") or m.get("title") or ""
            if not name:
                continue
            title_bits = [m.get("title") or name]
            if m.get("version"):
                title_bits.append("版本: {}".format(m.get("version")))
            if m.get("category_name"):
                title_bits.append("分类: {}".format(m.get("category_name")))
            version_html = '<span class="tag-mod-version">{}</span>'.format(esc(m.get("version", ""))) if m.get("version") else ''
            if preview_used >= preview_limit:
                hidden_mod_count += 1
                continue
            preview_used += 1
            links.append(
                '<span class="tag-mod" role="button" tabindex="0" title="{title}" data-mod="{mod}" data-mod-cat="{cat}" data-mod-url="{href}"><span class="tag-mod-name">{name}</span>{version}<a class="tag-mod-open" href="{href}" target="_blank" title="打开 MC百科模组页">↗</a></span>'.format(
                    href=esc_attr(m.get("url") or "#"),
                    title=esc_attr(" · ".join([x for x in title_bits if x])),
                    mod=esc_attr(name),
                    cat=esc_attr(m.get("category_name", "")),
                    name=esc(name),
                    version=version_html,
                )
            )
        cat_label = esc(group["name"])
        if group.get("url"):
            cat_head = '<a class="mod-category-link" href="{}" target="_blank">{}</a>'.format(esc_attr(group["url"]), cat_label)
        else:
            cat_head = '<span>{}</span>'.format(cat_label)
        mod_summary_chips.append(
            '<button type="button" class="mod-summary-chip" data-mod-cat-key="{key}" title="跳到 {name} 分类">{name}<b>{count}</b></button>'.format(
                key="cat{}".format(group_idx), name=cat_label, count=len(group["mods"])
            )
        )
        if not links:
            continue
        mod_sections.append(
            '<section class="mod-category-section" data-mod-cat-key="{key}"><div class="mod-category-head">{head}<span>{count}</span></div><div class="mod-grid">{mods}</div></section>'.format(
                key="cat{}".format(group_idx), head=cat_head, count=len(group["mods"]), mods="".join(links)
            )
        )
    # 完整模组名只保留在 compareData 中供筛选/对比使用，避免在每行 HTML 属性里再复制一遍。
    search_mods = esc_attr(" ".join(sorted({m.get("category_name", "") for m in d.get("mods", []) if m.get("category_name")})))
    mod_count = len(d.get("mods", []))
    if mod_sections:
        mod_html = (
            '<details class="mod-details">'
            '<summary><span class="mod-summary-main">包含模组 <b>{count}</b></span><span class="mod-summary-cats">{chips}</span></summary>'
            '<div class="mod-details-body">{sections}{more}<div class="mod-full-list" data-loaded="0"></div></div>'
            '</details>'
        ).format(
            count=mod_count, chips="".join(mod_summary_chips), sections="".join(mod_sections),
            more=('<div class="tag-empty">折叠状态精选预览前 {} 个模组；展开抽屉或点击分类可查看全部 {} 款收录模组。</div>'.format(preview_limit, mod_count) if hidden_mod_count else '')
        )
    else:
        mod_html = '<span class="tag-empty">—</span>'
    L.append('                <td class="td-mods" data-search="{}" data-count="{}" data-order="{}"><div class="tag-wrap mod-container">{}</div></td>'.format(
        search_mods, mod_count, mod_count, mod_html))
    L.append('            </tr>')
    return "\n".join(L)

# ═══════════════════════════════════ 多主题配色系统 ═══════════════════════════════════
# 极致毛玻璃感重构版：降低透明度、增强底色透光率、强化阴影与对比

THEMES = {
    "warm": {
        "name": "暖色",
        "desc": "琥珀奶金 · 强效毛玻璃",
        "root": """            --primary: #d97706;
            --primary-light: #f59e0b;
            --primary-dark: #b45309;
            --secondary: #0d9488;
            --secondary-light: #14b8a6;
            --accent: #ea580c;
            --emerald: #059669;
            --gold: #b45309;
            --gold-light: #d4a574;
            --coral: #dc2626;
            --danger: #dc2626;
            --success: #059669;
            --glass-bg: rgba(253, 246, 230, 0.55);
            --glass-bg-solid: rgba(253, 246, 230, 0.7);
            --glass-border: rgba(217, 119, 6, 0.25);
            --glass-hover: rgba(217, 119, 6, 0.15);
            --glass-shadow: rgba(61, 43, 31, 0.18);
            --bg-main: #f5ead8;
            --bg-gradient-1: #fbf1e0;
            --bg-gradient-2: #e9d5b5;
            --bg-gradient-3: #ddc199;
            --text: #3d2b1f;
            --text-secondary: #4a3525;
            --text-muted: rgba(61, 43, 31, 0.55);
            --border: rgba(217, 119, 6, 0.2);
            --shadow: 0 8px 32px 0 rgba(61, 43, 31, 0.12);
            --shadow-lg: 0 16px 48px 0 rgba(61, 43, 31, 0.2);
            --radius: 24px;
            --radius-sm: 14px;
            --primary-rgb: 217, 119, 6;
            --primary-light-rgb: 245, 158, 11;
            --primary-dark-rgb: 180, 83, 9;
            --secondary-rgb: 13, 148, 136;
            --accent-rgb: 234, 88, 12;
            --gold-light-rgb: 212, 165, 116;
            --shadow-rgb: 61, 43, 31;
            --glass-tint-rgb: 253, 246, 230;
            --glass-tint2-rgb: 233, 213, 181;
            --line-rgb: 217, 119, 6;
            --th-bg-1: rgba(254, 249, 239, 0.6);
            --th-bg-2: rgba(243, 227, 201, 0.5);
            --th-sort-bg-1: rgba(255, 238, 199, 0.7);
            --th-sort-bg-2: rgba(243, 214, 168, 0.6);
            --th-sort-active-bg-1: rgba(255, 228, 168, 0.8);
            --th-sort-active-bg-2: rgba(240, 198, 130, 0.7);""",
    },
    "dark": {
        "name": "暗色",
        "desc": "靛蓝深空 · 暗色毛玻璃",
        "root": """            --primary: #6366f1;
            --primary-light: #818cf8;
            --primary-dark: #4f46e5;
            --secondary: #0ea5e9;
            --secondary-light: #38bdf8;
            --accent: #f59e0b;
            --emerald: #10b981;
            --gold: #d4a574;
            --gold-light: #e8c9a0;
            --coral: #e07a5f;
            --danger: #ef4444;
            --success: #10b981;
            --glass-bg: rgba(10, 14, 26, 0.6);
            --glass-bg-solid: rgba(19, 26, 46, 0.75);
            --glass-border: rgba(255, 255, 255, 0.12);
            --glass-hover: rgba(255, 255, 255, 0.12);
            --glass-shadow: rgba(0, 0, 0, 0.4);
            --bg-main: #0a0e1a;
            --bg-gradient-1: #0d1320;
            --bg-gradient-2: #131a2e;
            --bg-gradient-3: #1a2340;
            --text: #f1f5f9;
            --text-secondary: rgba(241, 245, 249, 0.85);
            --text-muted: rgba(241, 245, 249, 0.5);
            --border: rgba(255, 255, 255, 0.1);
            --shadow: 0 8px 32px 0 rgba(0,0,0,.3);
            --shadow-lg: 0 16px 48px 0 rgba(0,0,0,.45);
            --radius: 24px;
            --radius-sm: 14px;
            --primary-rgb: 99, 102, 241;
            --primary-light-rgb: 129, 140, 248;
            --primary-dark-rgb: 79, 70, 229;
            --secondary-rgb: 14, 165, 233;
            --accent-rgb: 245, 158, 11;
            --gold-light-rgb: 232, 201, 160;
            --shadow-rgb: 0, 0, 0;
            --glass-tint-rgb: 255, 255, 255;
            --glass-tint2-rgb: 241, 245, 249;
            --line-rgb: 255, 255, 255;
            --th-bg-1: rgba(15, 20, 35, 0.6);
            --th-bg-2: rgba(20, 28, 48, 0.5);
            --th-sort-bg-1: rgba(30, 38, 60, 0.7);
            --th-sort-bg-2: rgba(35, 43, 70, 0.6);
            --th-sort-active-bg-1: rgba(99, 102, 241, 0.35);
            --th-sort-active-bg-2: rgba(129, 140, 248, 0.25);""",
    },
    "light": {
        "name": "亮色",
        "desc": "冰蓝白银 · 强效毛玻璃",
        "root": """            --primary: #2563eb;
            --primary-light: #3b82f6;
            --primary-dark: #1d4ed8;
            --secondary: #0891b2;
            --secondary-light: #06b6d4;
            --accent: #8b5cf6;
            --emerald: #059669;
            --gold: #6366f1;
            --gold-light: #a5b4fc;
            --coral: #f43f5e;
            --danger: #ef4444;
            --success: #10b981;
            --glass-bg: rgba(240, 246, 255, 0.55);
            --glass-bg-solid: rgba(240, 246, 255, 0.7);
            --glass-border: rgba(37, 99, 235, 0.18);
            --glass-hover: rgba(37, 99, 235, 0.12);
            --glass-shadow: rgba(37, 99, 235, 0.12);
            --bg-main: #e2e8f0;
            --bg-gradient-1: #f8fafc;
            --bg-gradient-2: #cbd5e1;
            --bg-gradient-3: #94a3b8;
            --text: #0f172a;
            --text-secondary: #1e293b;
            --text-muted: rgba(15, 23, 42, 0.55);
            --border: rgba(37, 99, 235, 0.12);
            --shadow: 0 8px 32px 0 rgba(37, 99, 235, .08);
            --shadow-lg: 0 16px 48px 0 rgba(37, 99, 235, .15);
            --radius: 24px;
            --radius-sm: 14px;
            --primary-rgb: 37, 99, 235;
            --primary-light-rgb: 59, 130, 246;
            --primary-dark-rgb: 29, 78, 216;
            --secondary-rgb: 8, 145, 178;
            --accent-rgb: 139, 92, 246;
            --gold-light-rgb: 165, 180, 252;
            --shadow-rgb: 37, 99, 235;
            --glass-tint-rgb: 255, 255, 255;
            --glass-tint2-rgb: 241, 245, 249;
            --line-rgb: 37, 99, 235;
            --th-bg-1: rgba(255, 255, 255, 0.6);
            --th-bg-2: rgba(241, 245, 249, 0.5);
            --th-sort-bg-1: rgba(224, 242, 254, 0.7);
            --th-sort-bg-2: rgba(186, 230, 253, 0.6);
            --th-sort-active-bg-1: rgba(186, 230, 253, 0.8);
            --th-sort-active-bg-2: rgba(125, 211, 252, 0.7);""",
    },
    "eye": {
        "name": "护眼",
        "desc": "低蓝光暖米色 · 阅读友好",
        "root": """            --primary: #8a6a28;
            --primary-light: #a98534;
            --primary-dark: #6f531d;
            --secondary: #6f7d3a;
            --secondary-light: #87974a;
            --accent: #b86b3f;
            --emerald: #607a36;
            --gold: #8a6a28;
            --gold-light: #d4b46a;
            --coral: #b25b4b;
            --danger: #b25b4b;
            --success: #607a36;
            --glass-bg: rgba(255, 249, 235, 0.82);
            --glass-bg-solid: rgba(255, 252, 242, 0.97);
            --glass-border: rgba(138, 106, 40, 0.16);
            --glass-hover: rgba(138, 106, 40, 0.08);
            --glass-shadow: rgba(73, 61, 42, 0.12);
            --bg-main: #f5ecd8;
            --bg-gradient-1: #fff8e8;
            --bg-gradient-2: #f3e6c9;
            --bg-gradient-3: #e7d8b8;
            --text: #251f15;
            --text-secondary: #493d2a;
            --text-muted: rgba(73, 61, 42, 0.62);
            --border: rgba(138, 106, 40, 0.16);
            --shadow: 0 14px 36px rgba(73, 61, 42, 0.10);
            --shadow-lg: 0 24px 60px rgba(73, 61, 42, 0.14);
            --radius: 14px;
            --radius-sm: 10px;
            --primary-rgb: 138, 106, 40;
            --primary-light-rgb: 169, 133, 52;
            --primary-dark-rgb: 111, 83, 29;
            --secondary-rgb: 111, 125, 58;
            --accent-rgb: 184, 107, 63;
            --gold-light-rgb: 212, 180, 106;
            --shadow-rgb: 73, 61, 42;
            --glass-tint-rgb: 255, 252, 242;
            --glass-tint2-rgb: 243, 230, 201;
            --line-rgb: 138, 106, 40;
            --th-bg-1: rgba(255, 250, 237, 0.98);
            --th-bg-2: rgba(244, 232, 207, 0.96);
            --th-sort-bg-1: rgba(255, 242, 204, 0.88);
            --th-sort-bg-2: rgba(238, 218, 174, 0.72);
            --th-sort-active-bg-1: rgba(246, 224, 181, 0.92);
            --th-sort-active-bg-2: rgba(224, 196, 136, 0.78);""",
    },
    "pink": {
        "name": "粉色",
        "desc": "樱粉莓白 · 现代柔和",
        "root": """            --primary: #e84a8a;
            --primary-light: #ff7ab1;
            --primary-dark: #c72f70;
            --secondary: #8b5cf6;
            --secondary-light: #a78bfa;
            --accent: #06b6d4;
            --emerald: #10b981;
            --gold: #e84a8a;
            --gold-light: #f9a8d4;
            --coral: #fb7185;
            --danger: #e11d48;
            --success: #10b981;
            --glass-bg: rgba(255, 247, 251, 0.84);
            --glass-bg-solid: rgba(255, 250, 253, 0.98);
            --glass-border: rgba(232, 74, 138, 0.16);
            --glass-hover: rgba(232, 74, 138, 0.08);
            --glass-shadow: rgba(126, 34, 86, 0.12);
            --bg-main: #fdf2f8;
            --bg-gradient-1: #fffafd;
            --bg-gradient-2: #fce7f3;
            --bg-gradient-3: #eef2ff;
            --text: #20101a;
            --text-secondary: #4a263b;
            --text-muted: rgba(74, 38, 59, 0.58);
            --border: rgba(232, 74, 138, 0.14);
            --shadow: 0 14px 36px rgba(126, 34, 86, 0.09);
            --shadow-lg: 0 24px 60px rgba(126, 34, 86, 0.14);
            --radius: 14px;
            --radius-sm: 10px;
            --primary-rgb: 232, 74, 138;
            --primary-light-rgb: 255, 122, 177;
            --primary-dark-rgb: 199, 47, 112;
            --secondary-rgb: 139, 92, 246;
            --accent-rgb: 6, 182, 212;
            --gold-light-rgb: 249, 168, 212;
            --shadow-rgb: 126, 34, 86;
            --glass-tint-rgb: 255, 250, 253;
            --glass-tint2-rgb: 252, 231, 243;
            --line-rgb: 232, 74, 138;
            --th-bg-1: rgba(255, 250, 253, 0.98);
            --th-bg-2: rgba(252, 231, 243, 0.96);
            --th-sort-bg-1: rgba(253, 242, 248, 0.94);
            --th-sort-bg-2: rgba(251, 207, 232, 0.72);
            --th-sort-active-bg-1: rgba(251, 207, 232, 0.9);
            --th-sort-active-bg-2: rgba(244, 114, 182, 0.48);""",
    },
    "anime": {
        "name": "流光",
        "desc": "流光玻璃 · 香槟紫褐",
        "root": """            --primary: #d98f5b;
            --primary-light: #ffd7a1;
            --primary-dark: #9f5a3b;
            --secondary: #8c6bb1;
            --secondary-light: #c4a7e7;
            --accent: #b8875d;
            --emerald: #b46a5d;
            --gold: #b8875d;
            --gold-light: #f1c894;
            --coral: #c96f58;
            --danger: #d26b72;
            --success: #c98a5d;
            --glass-bg: rgba(54, 41, 45, 0.28);
            --glass-bg-solid: rgba(54, 41, 45, 0.62);
            --glass-border: rgba(255, 215, 161, 0.34);
            --glass-hover: rgba(255, 215, 161, 0.12);
            --glass-shadow: rgba(24, 18, 22, 0.34);
            --bg-main: #2f2830;
            --bg-gradient-1: #2f2830;
            --bg-gradient-2: #4b3734;
            --bg-gradient-3: #6a4738;
            --text: #fff3dc;
            --text-secondary: #ecd6b8;
            --text-muted: rgba(236, 214, 184, 0.72);
            --border: rgba(255, 215, 161, 0.22);
            --shadow: 0 18px 54px rgba(24, 18, 22, 0.30);
            --shadow-lg: 0 30px 88px rgba(24, 18, 22, 0.42);
            --radius: 14px;
            --radius-sm: 10px;
            --primary-rgb: 217, 143, 91;
            --primary-light-rgb: 255, 215, 161;
            --primary-dark-rgb: 159, 90, 59;
            --secondary-rgb: 140, 107, 177;
            --accent-rgb: 184, 135, 93;
            --gold-light-rgb: 241, 200, 148;
            --shadow-rgb: 24, 18, 22;
            --glass-tint-rgb: 71, 54, 54;
            --glass-tint2-rgb: 102, 71, 56;
            --line-rgb: 217, 143, 91;
            --th-bg-1: rgba(54, 41, 45, 0.62);
            --th-bg-2: rgba(102, 71, 56, 0.48);
            --th-sort-bg-1: rgba(217, 143, 91, 0.18);
            --th-sort-bg-2: rgba(140, 107, 177, 0.12);
            --th-sort-active-bg-1: rgba(255, 215, 161, 0.26);
            --th-sort-active-bg-2: rgba(217, 143, 91, 0.18);""",
    },
}

# ═══════════════════════ 美化版模板 v2.0 ═══════════════════════

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "template.html")
WEB_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "assets")


def load_html_template():
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"未找到模板文件: {TEMPLATE_PATH}")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def render_template(template_str, replacements):
    html = template_str
    for k, v in replacements.items():
        html = html.replace("{" + k + "}", str(v))
    return html

def gen_pretty_html(data, theme_name="light", comment_api_base="/api"):
    # 直接从爬虫 JSON 行中构建介绍/评论预览数据
    _ill_re = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
    desc_data = {}
    comment_data = {}
    for d in data:
        mid = _extract_mid(d.get("url", ""))
        if not mid:
            continue
        # 介绍：直接从 JSON 的整合包介绍字段读取
        desc_text = _ill_re.sub('', d.get("desc") or "")
        desc_images = normalize_image_list(d.get("intro_images") or [])
        if desc_text or desc_images:
            desc_data[mid] = {"text": desc_text, "images": desc_images}
        # 评论：page_count = JSON 评论数字段（页面统计的总数）
        cmt_page_val = int(d.get("com_n") or 0)
        if d.get("comments_raw") and d["comments_raw"].strip():
            try:
                # 1. 先用正则剔除掉恶心的低位非法控制字符
                clean_comments = _ill_re.sub('', d["comments_raw"])
                # 2. 增加 strict=False 允许合法的换行符/制表符等控制字符直接解析
                cmt_list = json.loads(clean_comments, strict=False)
                # 诱饵数据清洗：实际提取数 = 楼层数 + 楼中楼回复数
                actual_scraped = len(cmt_list) + sum(len(c.get('replies', [])) for c in cmt_list if isinstance(c, dict))
                cmt_total = max(int(d.get("comment_total") or 0), actual_scraped)
                cmt_page_val = max(cmt_page_val, cmt_total)
                comment_data[mid] = {"true_count": cmt_total, "page_count": cmt_page_val, "comments": cmt_list}
                d["com_n"] = cmt_total
                d["com_d"] = str(cmt_total)
                continue
            except (ValueError, TypeError) as e:
                # 临时打印一下到底是哪个整合包的 JSON 格式写错了，方便排查
                print(f"[提示] 整合包 ID {mid} 评论 JSON 解析失败，原因: {e}")
                pass
        if cmt_page_val > 0:
            comment_data[mid] = {"true_count": 0, "page_count": cmt_page_val, "comments": []}
    print("  -> 介绍数据: {} 条 | 评论数据: {} 条".format(len(desc_data), len(comment_data)))
    desc_json_str = json.dumps(desc_data, ensure_ascii=False)
    comment_json_str = json.dumps(comment_data, ensure_ascii=False)
    compare_data = {}
    # 完整模组卡片数据只作为延迟渲染源存在：页面初始不把它们插进 DOM。
    mod_detail_data = {}
    for d in data:
        mid = _extract_mid(d.get("url", ""))
        if not mid:
            continue
        title_cn, title_en = split_modpack_title(d.get("title", ""))
        mods = []
        mod_categories = []
        detail_groups = []
        detail_group_map = {}
        seen_mod = set()
        seen_cat = set()
        for m in d.get("mods", []):
            if not isinstance(m, dict):
                continue
            name = _s(m.get("name") or m.get("title"))
            if not name:
                continue
            key = name.lower()
            if key not in seen_mod:
                seen_mod.add(key)
                # 对比只需要模组名称；链接和重复元数据会让单文件看板膨胀到数百 MB。
                mods.append(name)
            cat_name = _s(m.get("category_name") or "未分类")
            if cat_name and cat_name not in seen_cat:
                seen_cat.add(cat_name)
                mod_categories.append(cat_name)
            cat_id = _s(m.get("category_id"))
            group_key = "{}|{}".format(cat_id, cat_name)
            if group_key not in detail_group_map:
                detail_group_map[group_key] = {
                    "k": "cat{}".format(len(detail_groups)),
                    "n": cat_name,
                    "u": _s(m.get("category_url")),
                    "m": [],
                }
                detail_groups.append(detail_group_map[group_key])
            detail_group_map[group_key]["m"].append([
                name,
                _s(m.get("version")),
                _s(m.get("url")),
                _s(m.get("title") or name),
            ])
        compare_data[mid] = {
            "mid": mid,
            "title": d.get("title", ""),
            "title_cn": title_cn or d.get("title", ""),
            "title_en": title_en,
            "url": d.get("url", ""),
            "type": d.get("modpack_type") or "未标明",
            "views": int(d.get("views_n") or 0),
            "score": int(d.get("score_n") or 0),
            "trend_latest": int(d.get("lat_n") or 0),
            "trend_days": int(d.get("trend_days") or 0),
            "comments": int(d.get("com_n") or 0),
            "recommend": int(d.get("rec_n") or 0),
            "favorite": int(d.get("fav_n") or 0),
            "red_votes": int(d.get("rv_n") or 0),
            "black_votes": int(d.get("bpv_n") or 0),
            "growth7": d.get("t7_d") or "",
            "growth30": d.get("t30_d") or "",
            "growth60": d.get("t60_d") or "",
            "categories": list(d.get("cat", [])),
            "tags": list(d.get("pack", [])),
            "mods": mods,
            "mod_categories": mod_categories,
        }
        mod_detail_data[mid] = detail_groups
    compare_json_str = json.dumps(compare_data, ensure_ascii=False)
    mod_detail_json_str = json.dumps(mod_detail_data, ensure_ascii=False, separators=(',', ':'))
    cat_opts = "\n".join(
        '                    <option value="{}">{} ({})</option>'.format(esc_attr(tag), esc(tag), count)
        for tag, count in build_category_options(data)
    )
    pack_opts = "\n".join(
        '                    <option value="{}">{} ({})</option>'.format(esc_attr(tag), esc(tag), count)
        for tag, count in build_packtag_options(data)
    )
    type_opts = (
        '                    <option value="">全部整合包类型</option>\n' +
        "\n".join(
            '                    <option value="{}">{} ({})</option>'.format(esc_attr(tag), esc(tag), count)
            for tag, count in build_modpack_type_options(data)
        )
    )
    mod_cat_opts = "\n".join(
        '                    <option value="{}">{} ({})</option>'.format(esc_attr(tag), esc(tag), count)
        for tag, count in build_mod_category_options(data)
    )
    mod_opts = ""
    trend_opts = (
        '                    <option value="">全部走势周期</option>\n' +
        "\n".join(
            '                    <option value="{}">{} ({})</option>'.format(esc_attr(value), esc(label), count)
            for value, label, count in build_trend_filter_options(data)
        )
    )
    rows_html = ""  # 采用 DataTables 延迟动态驱动，释放 15MB 静态 DOM
    total = len(data)
    total_views = sum(d["views_n"] for d in data)
    if total_views >= 10000:
        total_views_str = "{:.1f}万".format(total_views / 10000.0)
    else:
        total_views_str = str(total_views)
    total_comments = int(sum(d["com_n"] for d in data))
    total_comments_str = "{:,}".format(total_comments)
    title = "{} mcmod 整合包数据（仅供参考）".format(today_str())
    theme = THEMES.get(theme_name, THEMES["light"])
    replacements = {
        "title": title,
        "cat_opts": cat_opts,
        "pack_opts": pack_opts,
        "type_opts": type_opts,
        "trend_opts": trend_opts,
        "mod_cat_opts": mod_cat_opts,
        "mod_opts": mod_opts,
        "rows": rows_html,
        "total": str(total),
        "total_views": total_views_str,
        "total_comments": total_comments_str,
        "default_theme": theme_name,
    }
    return render_template(load_html_template(), replacements), comment_data, rows_html, mod_detail_data


def dashboard_data_dir_for_html(html_path):
    """All generated data for one dashboard stays in its sibling data folder."""
    return os.path.join(os.path.dirname(os.path.abspath(html_path)), "data")


# ── 增量写入工具 ─────────────────────────────────────────────
# 每次构建都会产出主页面 + 5 份平台数据 + 介绍数据 + 审计数据 + 近 3000 份评论/模组侧车，
# 其中绝大多数内容与上一轮完全一致。无条件重写既慢又会让文件时间戳全部变动
# （不利于 git diff、增量备份与「只看真正变化」的判断）。
# 这里统一走「内容一致就跳过」的写入路径，并统计真实写入量。
_INCREMENTAL_STATS = {"written": 0, "skipped": 0, "bytes_written": 0, "bytes_skipped": 0}


def write_text_if_changed(path, body, encoding="utf-8", errors="replace"):
    """内容与磁盘完全一致时跳过写入，返回 True 表示真的写了。

    比较与落盘都按字节做（二进制模式），这是关键：
    文本模式在 Windows 上会把 \\n 翻译成 \\r\\n，导致「刚写出去的内容」
    和「下次读回来的内容」永远不相等，增量判断会彻底失效。
    统一按 LF 字节落盘，跨平台结果也稳定。
    """
    payload = body.encode(encoding, errors=errors)
    try:
        if os.path.isfile(path):
            with open(path, "rb") as f:
                if f.read() == payload:
                    _INCREMENTAL_STATS["skipped"] += 1
                    _INCREMENTAL_STATS["bytes_skipped"] += len(payload)
                    return False
    except OSError:
        pass  # 读不到（权限/占用）就当需要写入，交给下面的 open 报错
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as f:
        f.write(payload)
    _INCREMENTAL_STATS["written"] += 1
    _INCREMENTAL_STATS["bytes_written"] += len(payload)
    return True


def reset_incremental_stats():
    _INCREMENTAL_STATS.update({"written": 0, "skipped": 0, "bytes_written": 0, "bytes_skipped": 0})


# 字段完整度报告：六平台的字段名并不统一（MC百科 用 c0/mc_versions/views_n，
# 其余平台用 categories/all_versions/downloads），所以按「候选键」解析，
# 任一候选键有值即视为该条已填。这份表是「有就做、没有就不做」的依据。
COVERAGE_FIELDS = [
    ("categories", "玩法分类"),
    ("loaders", "加载器"),
    ("mc_version", "MC 版本"),
    ("all_versions", "历史版本"),
    ("popularity", "热度值"),
]
COVERAGE_ALIASES = {
    "categories": ("categories", "c0", "cat"),
    "loaders": ("loaders",),
    "mc_version": ("mc_version", "mc_versions"),
    "all_versions": ("all_versions", "mc_versions"),
    "popularity": ("downloads", "views_n", "views", "views_d"),
}


def mcmod_rows_for_coverage(data, archive_path="crawler_output/mcmod_modpacks.json"):
    """MC百科 的看板行数据只保留看板所需字段，版本信息在爬虫归档里。
    这里把归档合并回来，完整度统计才不会误报成 0%。"""
    meta = {}
    if os.path.exists(archive_path):
        try:
            with open(archive_path, "r", encoding="utf-8") as f:
                for rec in json.load(f):
                    mid = str(rec.get("mid") or "")
                    if mid:
                        meta[mid] = rec
        except Exception:
            pass
    rows = []
    for it in (data or []):
        m = meta.get(str(it.get("mid") or ""), {})
        row = dict(it)
        row["mc_version"] = m.get("mc_version")
        row["mc_versions"] = m.get("mc_versions") or m.get("all_versions")
        row["loaders"] = m.get("loaders")
        rows.append(row)
    return rows


def _has_value(v):
    """空列表 / 空字符串 / 0 / 未知 都算「没有数据」。"""
    if v is None:
        return False
    if isinstance(v, (list, tuple, dict, set)):
        return len(v) > 0
    if isinstance(v, str):
        s = v.strip()
        return bool(s) and s not in ("未知", "None", "null", "-")
    if isinstance(v, (int, float)):
        return v != 0
    return True


def _coverage_ratio(items, field):
    if not items:
        return 0, 0
    keys = COVERAGE_ALIASES.get(field, (field,))
    hit = 0
    for it in items:
        for k in keys:
            if _has_value(it.get(k)):
                hit += 1
                break
    return hit, len(items)


def report_data_coverage(platform_packs):
    """打印六平台的字段完整度表格。

    这张表是「有就做、没有就不做」这条原则的依据：
    完整度高的字段才值得在 UI 上做筛选/展示，完整度低的一律不硬凑。
    """
    rows = []
    for name, packs in platform_packs:
        cells = []
        for field, _label in COVERAGE_FIELDS:
            hit, total = _coverage_ratio(packs, field)
            cells.append(0.0 if not total else hit * 100.0 / total)
        rows.append((name, len(packs), cells))
    if not rows:
        return

    print("\n  六平台字段完整度（判断哪些筛选/展示值得做，低于 60% 的字段不强行跨平台一致）：")
    header = "    {:<12}{:>8}".format("平台", "条目数")
    for _f, label in COVERAGE_FIELDS:
        header += "{:>10}".format(label)
    print(header)
    print("    " + "-" * (20 + 10 * len(COVERAGE_FIELDS)))
    for name, total, cells in rows:
        line = "    {:<12}{:>8,}".format(name, total)
        for pct in cells:
            line += "{:>9.1f}%".format(pct)
        print(line)

    for idx, (_f, label) in enumerate(COVERAGE_FIELDS):
        avg = sum(r[2][idx] for r in rows) / len(rows)
        if avg < 60:
            missing = [r[0] for r in rows if r[2][idx] < 20]
            note = "（{} 该字段基本缺失）".format("、".join(missing)) if missing else ""
            print("    [i] {} 全网平均 {:.0f}%，暂不做跨平台强一致 {}".format(label, avg, note))


def incremental_summary():
    w, sk = _INCREMENTAL_STATS["written"], _INCREMENTAL_STATS["skipped"]
    total = w + sk
    if not total:
        return ""
    saved_mb = _INCREMENTAL_STATS["bytes_skipped"] / 1048576.0
    return "  增量写入: 实写 {:,} 个 / 跳过 {:,} 个（{:.1f}% 未变动，省下 {:.1f} MB 落盘）".format(
        w, sk, sk * 100.0 / total, saved_mb)


def comment_data_dir_for_html(html_path):
    return os.path.join(dashboard_data_dir_for_html(html_path), "comments")


def write_dashboard_sidecars(comment_data, mod_detail_data, html_path):
    """Write one local script payload per pack; file:// pages can lazy-load scripts without CORS."""
    comment_dir = comment_data_dir_for_html(html_path)
    os.makedirs(comment_dir, exist_ok=True)
    for mid, payload in comment_data.items():
        safe_mid = str(mid)
        if not safe_mid.isdigit():
            continue
        body = "window.__registerCommentData({},{});".format(
            json.dumps(safe_mid), json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        write_text_if_changed(os.path.join(comment_dir, safe_mid + ".js"), body)
    mod_dir = os.path.join(dashboard_data_dir_for_html(html_path), "mods")
    os.makedirs(mod_dir, exist_ok=True)
    for mid, payload in mod_detail_data.items():
        safe_mid = str(mid)
        if not safe_mid.isdigit():
            continue
        body = "window.__registerModDetailData({},{});".format(
            json.dumps(safe_mid), json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        write_text_if_changed(os.path.join(mod_dir, safe_mid + ".js"), body)
    return comment_dir, len(comment_data)

# ═══════════════════════ 主程序 ═══════════════════════

def list_themes():
    """列出所有可用主题"""
    print("可用主题：")
    for key, t in THEMES.items():
        print("  {:<10}  {}  -  {}".format(key, t["name"], t["desc"]))


class DashboardHandler(SimpleHTTPRequestHandler):
    """The converter's built-in local API for generated table/comment data."""
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/health":
            return self._send_json({"ok": True, "version": APP_VERSION})
        match = re.fullmatch(r"/api/data/([^/]+)/(table|comments/(\d+))", path)
        if not match:
            return super().do_GET()
        dataset, resource, mid = urllib.parse.unquote(match.group(1)), match.group(2), match.group(3)
        parts = dataset.replace("\\", "/").split("/")
        if (not parts or parts[-1] != "data" or any(x in ("", ".", "..") for x in parts) or
                (mid is not None and not mid.isdigit())):
            return self.send_error(HTTPStatus.BAD_REQUEST, "非法数据请求")
        target = os.path.join(self.directory, dataset, "table_rows.html" if resource == "table" else os.path.join("comments", mid + ".json"))
        if os.path.commonpath([os.path.abspath(self.directory), os.path.abspath(target)]) != os.path.abspath(self.directory):
            return self.send_error(HTTPStatus.FORBIDDEN, "非法数据路径")
        if not os.path.isfile(target):
            return self.send_error(HTTPStatus.NOT_FOUND, "未找到看板数据")
        with open(target, "rb") as f:
            body = f.read()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8" if resource == "table" else "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve_dashboard(host, port, html_path, open_browser=True):
    root = os.path.dirname(os.path.abspath(__file__))
    handler = lambda *a, **kw: DashboardHandler(*a, directory=root, **kw)
    relative_url = urllib.parse.quote(os.path.relpath(html_path, root).replace(os.sep, "/"))
    url = "http://{}:{}/{}".format(host, port, relative_url)
    # 旧版本可能仍占着默认端口；绝不复用它，自动找一个当前版本可用的端口。
    server = None
    actual_port = port
    for candidate in range(port, port + 20):
        try:
            server = ThreadingHTTPServer((host, candidate), handler)
            actual_port = candidate
            break
        except OSError as exc:
            if getattr(exc, "errno", None) != 48:
                raise
    if server is None:
        raise OSError("端口 {} 到 {} 均被占用，请关闭旧转换器后重试。".format(port, port + 19))
    url = "http://{}:{}/{}".format(host, actual_port, relative_url)
    if actual_port != port:
        print("\n默认端口 {} 正被旧版本占用，已改用端口 {}。".format(port, actual_port))
    print("\n看板已打开：\n  {}\n\n保持此窗口运行；按 Ctrl+C 关闭看板。".format(url))
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n看板已关闭。")
    finally:
        server.server_close()

def adapt_table_rows_js_record(r, existing_compare=None, details_cache=None):
    mid = str(r.get("mid", ""))
    url = "https://www.mcmod.cn/modpack/{}.html".format(mid) if mid else ""
    views_n = int(r.get("views_n") or 0)
    views_d = "{:.2f}万".format(views_n / 10000.0) if views_n >= 10000 else str(views_n)
    cat = [c.strip() for c in (r.get("cat_search") or "").split() if c.strip()]
    pack = [p.strip() for p in (r.get("pack_search") or "").split() if p.strip()]
    if not pack and cat:
        pack = [t.strip() for t in (r.get("tags_search") or "").split() if t.strip() and t.strip() not in cat]
    
    trend_arr = []
    if r.get("trend_dates") and r.get("trend_vals"):
        d_list = str(r["trend_dates"]).split(",")
        v_list = str(r["trend_vals"]).split(",")
        for d_str, v_str in zip(d_list, v_list):
            try:
                trend_arr.append((d_str, float(v_str)))
            except ValueError:
                pass
    
    c0 = r.get("c0", "")
    cover_m = re.search(r'data-image-url="([^"]+)"', c0)
    cover_image = cover_m.group(1) if cover_m else ""
    
    t7_n = r.get("t7_n")
    t30_n = r.get("t30_n")
    t60_n = r.get("t60_n")
    tall_n = r.get("tall_n")

    c6 = r.get("c6", "")
    p_data = (existing_compare or {}).get(mid, {})
    all_mod_names = p_data.get("mods", [])
    mod_categories = p_data.get("mod_categories", [])
    if not mod_categories:
        mod_categories = [m.strip() for m in (r.get("mods_search") or "").split() if m.strip()]

    chips = re.findall(r'class="mod-summary-chip"[^>]*data-mod-cat-key="([^"]+)"[^>]*>([^<]+)<b>(\d+)</b>', c6)
    cat_urls = dict(re.findall(r'data-mod-cat-key="([^"]+)"[^>]*>.*?href="([^"]+)"', c6))
    
    preview_dict = {}
    for p in re.finditer(r'<span class="tag-mod"[^>]*data-mod="([^"]+)"[^>]*data-mod-cat="([^"]+)"[^>]*data-mod-url="([^"]+)"[^>]*>(.*?)</span>\s*<a class="tag-mod-open"', c6):
        m_name = p.group(1).replace('&amp;', '&')
        m_cat = p.group(2)
        m_url = p.group(3)
        inner = p.group(4)
        ver_m = re.search(r'class="tag-mod-version">([^<]+)<', inner)
        m_ver = ver_m.group(1) if ver_m else ""
        preview_dict[m_name.lower()] = (m_ver, m_url, m_cat)

    if not all_mod_names and preview_dict:
        all_mod_names = [p.group(1).replace('&amp;', '&') for p in re.finditer(r'<span class="tag-mod"[^>]*data-mod="([^"]+)"', c6)]

    mods = []
    if all_mod_names:
        mod_ptr = 0
        if chips:
            for chip_k, chip_n, chip_c in chips:
                cnt = int(chip_c)
                cat_mods = all_mod_names[mod_ptr:mod_ptr+cnt]
                mod_ptr += cnt
                for m_name in cat_mods:
                    ver, mod_url, _ = preview_dict.get(m_name.lower(), ("", "", chip_n))
                    if not mod_url:
                        mod_url = "https://www.mcmod.cn/s?key={}".format(urllib.parse.quote(m_name))
                    mods.append({
                        "name": m_name,
                        "title": m_name,
                        "version": ver,
                        "url": mod_url,
                        "category_name": chip_n,
                        "category_url": cat_urls.get(chip_k, ""),
                        "category_id": chip_k
                    })
            if mod_ptr < len(all_mod_names):
                for m_name in all_mod_names[mod_ptr:]:
                    mod_url = "https://www.mcmod.cn/s?key={}".format(urllib.parse.quote(m_name))
                    mods.append({
                        "name": m_name,
                        "title": m_name,
                        "version": "",
                        "url": mod_url,
                        "category_name": "其他",
                        "category_url": "",
                        "category_id": "cat_other"
                    })
        else:
            for m_name in all_mod_names:
                ver, mod_url, cat_n = preview_dict.get(m_name.lower(), ("", "", "未分类"))
                if not mod_url:
                    mod_url = "https://www.mcmod.cn/s?key={}".format(urllib.parse.quote(m_name))
                mods.append({
                    "name": m_name,
                    "title": m_name,
                    "version": ver,
                    "url": mod_url,
                    "category_name": cat_n,
                    "category_url": "",
                    "category_id": "cat0"
                })

    cached = (details_cache or {}).get(mid, {})
    desc = cached.get("desc", "")
    intro_images = cached.get("intro_images", [])
    mc_versions = cached.get("mc_versions", [])
    if mc_versions and not r.get("mc_versions"):
        r["mc_versions"] = mc_versions

    return {
        "mid": mid,
        "url": url,
        "title": r.get("title", ""),
        "desc": desc,
        "comments_raw": "",
        "intro_images": intro_images,
        "comment_images": [],
        "cover_image": cover_image,
        "comment_total": str(r.get("com_n") or 0),
        "score_d": str(r.get("score_n") or 0),
        "score_n": int(r.get("score_n") or 0),
        "views_d": views_d,
        "views_n": views_n,
        "rec_d": str(r.get("rec_n") or 0),
        "rec_n": int(r.get("rec_n") or 0),
        "fav_d": str(r.get("fav_n") or 0),
        "fav_n": int(r.get("fav_n") or 0),
        "com_d": str(r.get("com_n") or 0),
        "com_n": int(r.get("com_n") or 0),
        "max_d": str(r.get("max_n") or 0),
        "max_n": int(r.get("max_n") or 0),
        "avg_d": str(r.get("avg_n") or 0),
        "avg_n": int(r.get("avg_n") or 0),
        "lat_d": str(r.get("lat_n") or 0),
        "lat_n": int(r.get("lat_n") or 0),
        "cat": cat,
        "pack": pack,
        "cat_details": [],
        "pack_details": [],
        "modpack_type": r.get("type_name") or "未标明",
        "modpack_type_url": "",
        "mods": mods,
        "mod_names": all_mod_names,
        "mod_categories": mod_categories,
        "rv_d": str(r.get("rv_n") or 0),
        "rv_n": int(r.get("rv_n") or 0),
        "rp_d": str(r.get("rp_n") or 0),
        "rp_n": int(r.get("rp_n") or 0),
        "bp_d": str(r.get("bp_n") or 0),
        "bp_n": int(r.get("bp_n") or 0),
        "bpv_d": str(r.get("bv_n") or 0),
        "bpv_n": int(r.get("bv_n") or 0),
        "tc_d": str(r.get("days_n") or 0),
        "tc_n": int(r.get("days_n") or 0),
        "t7_d": "{:+.1f}%".format(t7_n) if t7_n is not None else "",
        "t7_n": t7_n if t7_n is not None else 0,
        "t30_d": "{:+.1f}%".format(t30_n) if t30_n is not None else "",
        "t30_n": t30_n if t30_n is not None else 0,
        "t60_d": "{:+.1f}%".format(t60_n) if t60_n is not None else "",
        "t60_n": t60_n if t60_n is not None else 0,
        "tall_d": "{:+.1f}%".format(tall_n) if tall_n is not None else "",
        "tall_n": tall_n if tall_n is not None else 0,
        "trend_arr": trend_arr,
    }


def compute_and_save_audit_diff(data, bili_packs, bbsmc_packs, xyebbs_packs, modrinth_packs, curseforge_packs, data_dir):
    """自动比对当前抓取与历史快照，生成变动审计数据"""
    import datetime
    snapshot_path = "crawler_output/snapshot_history.json"
    prev_snapshot = {}
    if os.path.exists(snapshot_path):
        try:
            with open(snapshot_path, "r", encoding="utf-8") as f:
                prev_snapshot = json.load(f)
        except Exception as e:
            print("  [!] 读取快照历史失败: {}".format(e))

    # MC百科 的版本号 / 更新时间不在看板行数据里：process_data() 只保留看板需要的
    # 字段（title/url/views_n/cat/pack...），没有 latest_version / last_update_date。
    # 因此必须回读爬虫归档 mcmod_modpacks.json，否则版本与时间维度的变更永远比不出来。
    mcmod_meta = {}
    mcmod_meta_path = "crawler_output/mcmod_modpacks.json"
    if os.path.exists(mcmod_meta_path):
        try:
            with open(mcmod_meta_path, "r", encoding="utf-8") as f:
                for rec in json.load(f):
                    meta_mid = str(rec.get("mid") or "")
                    if meta_mid:
                        mcmod_meta[meta_mid] = rec
        except Exception as e:
            print("  [!] 读取 mcmod_modpacks.json 失败: {}".format(e))

    current_items = {}
    for item in (data or []):
        mid = str(item.get("mid") or _extract_mid(item.get("url", "")) or "")
        if mid:
            meta = mcmod_meta.get(mid, {})
            current_items["mcmod::" + mid] = {
                "platform": "mcmod", "id": mid,
                "title": _s(item.get("title") or item.get("name") or meta.get("title")),
                "version": _s(meta.get("latest_version") or item.get("latest_version") or item.get("mc_version")),
                "author": _s(item.get("author") or meta.get("author")),
                "date": _s(meta.get("last_update_date") or item.get("last_update_date") or item.get("release_date")),
                "url": item.get("url") or item.get("link") or f"https://www.mcmod.cn/modpack/{mid}.html"
            }

    for bp in (bili_packs or []):
        bvid = bp.get("bvid") or ""
        if bvid:
            current_items["bilibili::" + bvid] = {
                "platform": "bilibili", "id": bvid,
                "title": bp.get("title") or "",
                "version": bp.get("mc_version") or "",
                "author": bp.get("author") or "",
                "date": str(bp.get("pub_time") or ""),
                "url": bp.get("arcurl") or f"https://www.bilibili.com/video/{bvid}"
            }

    for bb in (bbsmc_packs or []):
        # bbsmc 爬虫产出的主键字段是 project_id，没有 id；原先只读 id 会取到空串，
        # 导致整个平台被 if bid: 静默跳过（1,802 条从不参与审计）。
        bid = str(bb.get("project_id") or bb.get("id") or bb.get("slug") or "")
        if bid:
            current_items["bbsmc::" + bid] = {
                "platform": "bbsmc", "id": bid,
                "title": bb.get("title") or "",
                "version": bb.get("mc_version") or "",
                "author": bb.get("author") or "",
                "date": str(bb.get("date_modified") or bb.get("date_created") or ""),
                "url": bb.get("url") or f"https://www.bbsmc.net/item/{bid}"
            }

    for xp in (xyebbs_packs or []):
        # 同 bbsmc：xyebbs 爬虫用的也是 project_id，没有 tid。
        tid = str(xp.get("project_id") or xp.get("tid") or xp.get("slug") or "")
        if tid:
            current_items["xyebbs::" + tid] = {
                "platform": "xyebbs", "id": tid,
                "title": xp.get("title") or "",
                "version": xp.get("mc_version") or "",
                "author": xp.get("author") or "",
                "date": str(xp.get("date_modified") or xp.get("date_created") or ""),
                "url": xp.get("url") or f"https://www.xyebbs.com/thread-{tid}-1-1.html"
            }

    for mp in (modrinth_packs or []):
        mid = str(mp.get("id") or mp.get("slug") or "")
        if mid:
            current_items["modrinth::" + mid] = {
                "platform": "modrinth", "id": mid,
                "title": mp.get("title") or "",
                "version": mp.get("mc_version") or "",
                "author": mp.get("author") or "",
                "date": str(mp.get("date_modified") or mp.get("date_created") or ""),
                "url": mp.get("url") or f"https://modrinth.com/modpack/{mp.get('slug') or mid}"
            }

    for cp in (curseforge_packs or []):
        cid = str(cp.get("id") or cp.get("slug") or "")
        if cid:
            current_items["curseforge::" + cid] = {
                "platform": "curseforge", "id": cid,
                "title": cp.get("title") or "",
                "version": cp.get("mc_version") or "",
                "author": cp.get("author") or "",
                "date": str(cp.get("date_modified") or cp.get("date_created") or ""),
                "url": cp.get("url") or f"https://www.curseforge.com/minecraft/modpacks/{cp.get('slug') or cid}"
            }

    added = []
    updated = []
    removed = []
    # "从无到有"的版本 / 更新时间：过去抓取失败导致字段缺失、这次补回来了。
    # 它不是版本升级（旧值不存在，无从比较），但属于监测数据实质变好，所以单独归类。
    # 否则这类补全在审计里完全不可见（实测被救回的 mid=1145 就是这种情况）。
    version_gained = []

    # 某个平台首次纳入监测时，它的全部条目对快照而言都是"新键"。那是覆盖范围
    # 发生变化，不是真实的内容变动，所以单独标记、不计入"新增"。
    new_platforms = set()
    if prev_snapshot:
        prev_platforms = set(v.get("platform") for v in prev_snapshot.values())
        new_platforms = set(v.get("platform") for v in current_items.values()) - prev_platforms

    if prev_snapshot:
        for k, curr in current_items.items():
            if k not in prev_snapshot:
                if curr.get("platform") in new_platforms:
                    continue
                added.append(curr)
            else:
                prev = prev_snapshot[k]
                prev_ver, curr_ver = _s(prev.get("version")), _s(curr.get("version"))
                prev_date, curr_date = _s(prev.get("date")), _s(curr.get("date"))
                diffs = []
                if curr_ver and prev_ver and curr_ver != prev_ver:
                    diffs.append(f"版本: {prev_ver} ➔ {curr_ver}")
                if curr_date and prev_date and curr_date != prev_date:
                    diffs.append(f"更新时间: {prev_date} ➔ {curr_date}")
                if curr.get("title") and prev.get("title") and curr["title"] != prev["title"]:
                    diffs.append(f"标题变更: {prev['title']} ➔ {curr['title']}")

                # 旧值为空、新值有值 => 这是"补全"，不是"升级"。必须与 updated 互斥，
                # 否则同一条目会既算补全又算更新，徽标数被重复计数。
                gained = []
                if curr_ver and not prev_ver:
                    gained.append(f"版本: (无) ➔ {curr_ver}")
                if curr_date and not prev_date:
                    gained.append(f"更新时间: (无) ➔ {curr_date}")

                if gained:
                    curr_copy = dict(curr)
                    curr_copy["diff_details"] = gained + diffs
                    version_gained.append(curr_copy)
                elif diffs:
                    curr_copy = dict(curr)
                    curr_copy["diff_details"] = diffs
                    updated.append(curr_copy)

        for k, prev in prev_snapshot.items():
            if k not in current_items:
                removed.append(prev)
    # 旧版在没有真实变动时会按平台各挑 8 条塞进 added/updated 并伪造
    # "最近抓取同步" 说明，导致徽标长期显示一个不存在的变动数（实测虚报 64）。
    # 变动审计必须如实反映真实差异，无变动就报 0，因此该兜底逻辑已移除。

    diff_result = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stats": {
            "total_current": len(current_items),
            "total_prev": len(prev_snapshot) if prev_snapshot else len(current_items),
            "added_count": len(added),
            "updated_count": len(updated),
            "removed_count": len(removed),
            "version_gained_count": len(version_gained)
        },
        "new_platforms": sorted(new_platforms),
        "added": added[:100],
        "updated": updated[:100],
        "removed": removed[:100],
        "version_gained": version_gained[:100]
    }

    try:
        os.makedirs("crawler_output", exist_ok=True)
        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(current_items, f, ensure_ascii=False)
    except Exception as e:
        print("  [!] 写入快照历史失败: {}".format(e))

    audit_js_path = os.path.join(data_dir, "audit_diff.js")
    try:
        with open(audit_js_path, "w", encoding="utf-8") as f:
            f.write("window.auditDiffData = " + json.dumps(diff_result, ensure_ascii=False) + ";\n")
        if new_platforms:
            print("  [i] 新纳入监测的平台（其条目不计入新增）: {}".format("、".join(sorted(new_platforms))))
        print("  [OK] 数据变动审计数据已生成 (监测 {} 款 · 新增 {} · 更新 {} · 补全版本 {} · 下架 {} -> {})".format(
            len(current_items), len(added), len(updated), len(version_gained), len(removed), audit_js_path))
    except Exception as e:
        print("  [!] 写入 audit_diff.js 失败: {}".format(e))

def main():
    import argparse
    parser = argparse.ArgumentParser(description="整合包 JSON 转 HTML 生成器（多主题版）")
    parser.add_argument("-i", "--input", default=None,
                        help="输入 JSONL 文件（默认: 多平台爬虫数据_v1.0.jsonl）")
    parser.add_argument("-o", "--output", default=os.path.join(GENERATED_DASHBOARD_DIR, OPEN_DASHBOARD_NAME),
                        help="输出 HTML 文件（默认 generated_dashboard/打开这个看板.html）")
    parser.add_argument("-t", "--theme", default="light",
                        choices=list(THEMES.keys()),
                        help="选择配色主题（默认: light）")
    parser.add_argument("--trend-history-file", default=TREND_HISTORY_FILE,
                        help="本地长期趋势历史文件（默认: trend_history.jsonl）")
    parser.add_argument("-l", "--list", action="store_true",
                        help="列出所有可用主题")
    args = parser.parse_args()
    if args.list:
        list_themes()
        return
    theme = THEMES[args.theme]
    output_html = args.output
    print("=" * 55)
    print("  整合包 JSON 转 HTML 生成器 {}  [{}]".format(APP_VERSION, theme["name"]))
    print("=" * 55)
    input_file = args.input
    if not input_file:
        if os.path.exists(INPUT_FILE):
            input_file = INPUT_FILE
        elif os.path.exists(FALLBACK_INPUT_FILE):
            input_file = FALLBACK_INPUT_FILE
        else:
            fallback_js = os.path.join(GENERATED_DASHBOARD_DIR, "data", "table_rows.js")
            if os.path.exists(fallback_js):
                print("  [提示] 自动从现存看板数据源读取: {}".format(fallback_js))
                input_file = fallback_js
    if not os.path.exists(input_file):
        print("\n[错误] 找不到数据文件：{}".format(input_file))
        print("  请先运行爬虫生成 '{}'，或使用 --input 指定文件。".format(INPUT_FILE))
        sys.exit(1)
    print("\n[1/3] 正在读取 {} ...".format(input_file))
    raw_rows, meta = read_json(input_file)
    if meta:
        meta_preview = ", ".join("{}={}".format(k, v) for k, v in list(meta.items())[:4])
        print("  元信息: {}".format(meta_preview))
    print("  JSON记录: {} 条".format(len(raw_rows)))
    print("\n[2/3] 正在解析数据 ...")
    if meta.get("type") == "table_rows_js":
        existing_compare = {}
        app_data_file = os.path.join(os.path.dirname(input_file), "app_data.js")
        if os.path.exists(app_data_file):
            try:
                with open(app_data_file, "r", encoding="utf-8", errors="ignore") as af:
                    for line in af:
                        if line.startswith("window.compareData = "):
                            existing_compare = json.loads(line[len("window.compareData = "):].rstrip(";\n "))
                            break
                print("  [提示] 成功从 app_data.js 读取全量模组映射数据 ({} 款)".format(len(existing_compare)))
            except Exception as e:
                print("  [警告] 读取 app_data.js 失败: {}".format(e))
        details_cache = {}
        cache_file = "crawler_output/mcmod_details_cache.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as cf:
                    details_cache = json.load(cf)
                print("  [提示] 成功从 mcmod_details_cache.json 读取介绍缓存 ({} 款)".format(len(details_cache)))
            except Exception as e:
                print("  [警告] 读取 mcmod_details_cache.json 失败: {}".format(e))
        data = [adapt_table_rows_js_record(r, existing_compare, details_cache) for r in raw_rows]
    else:
        data = process_data(raw_rows)
    trend_history_applied = apply_local_trend_history(data, args.trend_history_file)
    if trend_history_applied:
        print("  本地长期趋势: 已增强 {} 条记录（文件: {}）".format(trend_history_applied, args.trend_history_file))
    else:
        print("  本地长期趋势: 未发现可用历史，沿用当前抓取数据")
    # [V1.0 新增] 为应对异步并发抓取导致的乱序写入，在此进行强制后处理排序
    data.sort(key=lambda x: x.get("views_n", 0), reverse=True)
    print("  解析成功：{} 条记录（已按浏览量降序）".format(len(data)))
    if not data:
        print("[警告] 未解析到任何有效数据，请检查 JSON 是否包含 packs 或 results。")
        sys.exit(1)
    print("\n  首条记录预览：")
    print("    标题: {}".format(data[0]["title"]))
    print("    总浏览量: {}  -> data-order={}".format(data[0]["views_d"], data[0]["views_n"]))
    print("    分类: {}".format(data[0]["cat"]))
    pack_preview = data[0]["pack"][:5]
    print("    标签: {}{}".format(pack_preview, "..." if len(data[0]["pack"]) > 5 else ""))
    print("    红票: {} ({}%)  黑票: {} ({}%)".format(
        data[0]["rv_d"], data[0]["rp_d"], data[0]["bpv_d"], data[0]["bp_d"]))
    print("    走势天数: {}  7日:{} 30日:{} 60日:{}".format(
        data[0]["tc_d"], data[0]["t7_d"], data[0]["t30_d"], data[0]["t60_d"]))
    print("\n[3/3] 生成 [{}] -> {}".format(theme["name"], output_html))
    # 本轮构建的增量写入统计从这里开始计数
    reset_incremental_stats()
    # 同步 B站自制整合包数据源到 converted_output/data/bili_data.js
    bili_packs = load_bilibili_data()
    if bili_packs:
        data_dir = dashboard_data_dir_for_html(output_html)
        os.makedirs(data_dir, exist_ok=True)
        bili_js_target = os.path.join(data_dir, "bili_data.js")
        write_text_if_changed(bili_js_target, "window.biliModpacksData = " + json.dumps(bili_packs, ensure_ascii=False) + ";\n")
        print("  [OK] B站自制整合包数据源已就绪 (共 {} 条 -> {})".format(len(bili_packs), bili_js_target))

    # 同步 BBSMC 整合包数据源到 converted_output/data/bbsmc_data.js
    bbsmc_packs = load_bbsmc_data()
    if bbsmc_packs:
        data_dir = dashboard_data_dir_for_html(output_html)
        os.makedirs(data_dir, exist_ok=True)
        bbsmc_js_target = os.path.join(data_dir, "bbsmc_data.js")
        write_text_if_changed(bbsmc_js_target, "window.bbsmcModpacksData = " + json.dumps(bbsmc_packs, ensure_ascii=False) + ";\n")
        print("  [OK] BBSMC 整合包数据源已就绪 (共 {} 条 -> {})".format(len(bbsmc_packs), bbsmc_js_target))
    # 同步 XYEBBS 整合包数据源到 converted_output/data/xyebbs_data.js
    xyebbs_packs = load_xyebbs_data()
    if xyebbs_packs:
        data_dir = dashboard_data_dir_for_html(output_html)
        os.makedirs(data_dir, exist_ok=True)
        xyebbs_js_target = os.path.join(data_dir, "xyebbs_data.js")
        write_text_if_changed(xyebbs_js_target, "window.xyebbsModpacksData = " + json.dumps(xyebbs_packs, ensure_ascii=False) + ";\n")
        print("  [OK] XYEBBS 整合包数据源已就绪 (共 {} 条 -> {})".format(len(xyebbs_packs), xyebbs_js_target))
    # 同步 Modrinth 整合包数据源到 converted_output/data/modrinth_data.js
    modrinth_packs = load_modrinth_data()
    if modrinth_packs:
        data_dir = dashboard_data_dir_for_html(output_html)
        os.makedirs(data_dir, exist_ok=True)
        modrinth_js_target = os.path.join(data_dir, "modrinth_data.js")
        write_text_if_changed(modrinth_js_target, "window.modrinthModpacksData = " + json.dumps(modrinth_packs, ensure_ascii=False) + ";\n")
        print("  [OK] Modrinth 整合包数据源已就绪 (共 {} 条 -> {})".format(len(modrinth_packs), modrinth_js_target))

    # 同步 CurseForge 整合包数据源到 converted_output/data/curseforge_data.js
    curseforge_packs = load_curseforge_data()
    if curseforge_packs:
        data_dir = dashboard_data_dir_for_html(output_html)
        os.makedirs(data_dir, exist_ok=True)
        curseforge_js_target = os.path.join(data_dir, "curseforge_data.js")
        write_text_if_changed(curseforge_js_target, "window.curseforgeModpacksData = " + json.dumps(curseforge_packs, ensure_ascii=False) + ";\n")
        print("  [OK] CurseForge 整合包数据源已就绪 (共 {} 条 -> {})".format(len(curseforge_packs), curseforge_js_target))

    # 同步 MC百科 介绍与描述数据源到 converted_output/data/desc_data.js
    data_dir = dashboard_data_dir_for_html(output_html)
    os.makedirs(data_dir, exist_ok=True)
    desc_js_target = os.path.join(data_dir, "desc_data.js")
    if os.path.exists("crawler_output/mcmod_details_cache.json"):
        try:
            with open("crawler_output/mcmod_details_cache.json", "r", encoding="utf-8") as f:
                d_cache = json.load(f)
            write_text_if_changed(desc_js_target, "window.descData = " + json.dumps(d_cache, ensure_ascii=False) + ";\n")
            print("  [OK] MC百科介绍数据源已就绪 (共 {} 条 -> {})".format(len(d_cache), desc_js_target))
        except Exception as e:
            print("  [警告] 写入 desc_data.js 失败: {}".format(e))
    compute_and_save_audit_diff(data, bili_packs, bbsmc_packs, xyebbs_packs, modrinth_packs, curseforge_packs, data_dir)
    html_template, comment_data, rows_html, mod_detail_data = gen_pretty_html(data, args.theme, "__COMMENT_API_BASE__")
    output_dir = os.path.dirname(output_html) or "."
    os.makedirs(output_dir, exist_ok=True)
    output_assets_dir = os.path.join(output_dir, "assets")
    if os.path.exists(WEB_ASSETS_DIR):
        shutil.copytree(WEB_ASSETS_DIR, output_assets_dir, dirs_exist_ok=True)
        print("  [OK] 静态资源已同步至: {}".format(output_assets_dir))
    stable_html = os.path.join(output_dir, OPEN_DASHBOARD_NAME)
    output_targets = []
    for target in (output_html, stable_html):
        target_abs = os.path.abspath(target)
        if target_abs not in [os.path.abspath(x) for x in output_targets]:
            output_targets.append(target)
    extra_outputs = [x for x in output_targets if os.path.abspath(x) != os.path.abspath(output_html)]
    for target_html in output_targets:
        html_out = html_template.encode('utf-8', errors='replace').decode('utf-8')
        write_text_if_changed(target_html, html_out)
        write_dashboard_sidecars(comment_data, mod_detail_data, target_html)
    print("  [OK] 主页面完成（{:,} 字节；评论按需加载）".format(len(html_out)))
    report_data_coverage([
        ("MC百科", mcmod_rows_for_coverage(data)),
        ("B站自制", bili_packs),
        ("BBSMC", bbsmc_packs),
        ("XYEBBS", xyebbs_packs),
        ("Modrinth", modrinth_packs),
        ("CurseForge", curseforge_packs),
    ])
    _inc = incremental_summary()
    if _inc:
        print(_inc)
    print("\n" + "=" * 55)
    print("  生成完毕！[{}] {}".format(theme["name"], theme["desc"]))
    print("  -> {}".format(output_html))
    for extra_html in extra_outputs:
        print("  -> {}".format(extra_html))
    print("=" * 55)

if __name__ == "__main__":
    main()
