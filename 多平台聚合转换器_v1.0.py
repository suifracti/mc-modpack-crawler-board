
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

PRETTY_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN" data-theme="{default_theme}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="referrer" content="no-referrer">
    <title>{title}</title>
    <!-- ★ 防闪烁 (Anti-FOUC)：在渲染 DOM 前立即加载保存的主题 -->
    <script>
        (function() {{
            var theme = localStorage.getItem('mcmod-theme-v2') || 'light';
            if (theme) document.documentElement.setAttribute('data-theme', theme);
        }})();
    </script>
    <link href="data/vendor/bootstrap.min.css" rel="stylesheet">
    <link href="data/vendor/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link href="data/vendor/select2.min.css" rel="stylesheet" />
    <link href="data/vendor/select2-bootstrap-5-theme.min.css" rel="stylesheet" />
    
    <style>
        /* ════════ CSS 变量：玻璃态暗色主题 ════════ */
        /* ═══ 默认: 冷白现代风 ═══ */
        :root {{
            --primary: #2563eb;
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
            --th-sort-active-bg-2: rgba(125, 211, 252, 0.7);
        }}
        /* ═══ 暗色毛玻璃 ═══ */
        :root[data-theme="dark"] {{
            --primary: #6366f1;
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
            --th-sort-active-bg-2: rgba(129, 140, 248, 0.25);
        }}
        :root[data-theme="warm"] {{
            --primary: #d97706;
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
            --th-sort-active-bg-2: rgba(240, 198, 130, 0.7);
        }}
        /* ═══ 亮色毛玻璃 ═══ */
        :root[data-theme="light"] {{
            --primary: #2563eb;
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
            --th-sort-active-bg-2: rgba(125, 211, 252, 0.7);
        }}
        :root[data-theme="eye"] {{
            --primary: #8a6a28;
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
            --th-sort-active-bg-2: rgba(224, 196, 136, 0.78);
        }}
        :root[data-theme="pink"] {{
            --primary: #e84a8a;
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
            --th-sort-active-bg-2: rgba(244, 114, 182, 0.48);
        }}
        :root[data-theme="anime"] {{
            --primary: #d98f5b;
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
            --th-sort-active-bg-2: rgba(217, 143, 91, 0.18);
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html {{ scroll-behavior: smooth; }}
        body {{
        font-family: 'Plus Jakarta Sans', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg-main);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        /* ════════ 动画背景 + 浮动光球 ════════ */
        .bg-layer {{
            position: fixed; top: 0; left: 0;
            width: 100%; height: 100%; z-index: -2;
            background: linear-gradient(135deg, var(--bg-gradient-1) 0%, var(--bg-gradient-2) 50%, var(--bg-gradient-3) 100%);
        }}
        .bg-layer::before {{
            content: ''; position: absolute; inset: 0;
            background:
                radial-gradient(ellipse 80% 50% at 20% 30%, rgba(var(--primary-rgb), 0.12) 0%, transparent 50%),
                radial-gradient(ellipse 60% 40% at 80% 70%, rgba(var(--secondary-rgb), 0.10) 0%, transparent 50%),
                radial-gradient(ellipse 50% 30% at 50% 80%, rgba(var(--gold-light-rgb), 0.08) 0%, transparent 50%);
        }}
        .orb {{
            position: fixed; border-radius: 50%;
            filter: blur(120px);
            z-index: -1; animation: orb-float 20s ease-in-out infinite;
        }}
        .orb-1 {{ width: 380px; height: 380px; background: rgba(var(--primary-light-rgb),0.2); top: 8%; left: 5%; animation-delay: 0s; }}
        .orb-2 {{ width: 320px; height: 320px; background: rgba(var(--secondary-rgb),0.12); top: 55%; right: 5%; animation-delay: -5s; }}
        .orb-3 {{ width: 280px; height: 280px; background: rgba(var(--gold-light-rgb),0.15); bottom: 8%; left: 30%; animation-delay: -10s; }}
                @keyframes orb-float {{
            0%, 100% {{ transform: translate(0, 0) scale(1); }}
            25% {{ transform: translate(30px, -30px) scale(1.05); }}
            50% {{ transform: translate(-20px, 20px) scale(0.95); }}
            75% {{ transform: translate(20px, 10px) scale(1.02); }}
        }}
        /* ════════ Hero 区域 ════════ */
        .hero {{
            background: linear-gradient(135deg, rgba(var(--glass-tint-rgb),0.8), rgba(var(--glass-tint2-rgb),0.6));
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--glass-border);
            padding: 2.5rem 2rem 3.5rem;
            position: relative; overflow: hidden;
        }}
        .hero::before {{
            content: ''; position: absolute;
            top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
        }}
        .hero-inner {{ max-width: 2400px; margin: 0 auto; position: relative; z-index: 1; }}
        .hero-title {{
            font-size: 2.4rem; font-weight: 800;
            letter-spacing: -1px;
            background: linear-gradient(135deg, var(--primary-dark), var(--accent), var(--secondary));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .hero-sub {{
            font-size: 0.95rem; opacity: 0.8; margin-top: 0.5rem;
            color: var(--text-secondary);
        }}
        .hero-sub a {{
            color: var(--gold-light); text-decoration: underline;
            text-underline-offset: 2px; font-weight: 600;
        }}
        .hero-sub a:hover {{ color: var(--text); }}
        /* ════════ 统计卡片 ════════ */
        .stats-bar {{
            display: flex; gap: 1.5rem; flex-wrap: wrap;
            max-width: 2400px; margin: -3rem auto 1.5rem;
            padding: 0 2rem; position: relative; z-index: 2;
        }}
        .stat-card {{
            flex: 1; min-width: 240px;
            background: var(--glass-bg);
            backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius);
            padding: 1.5rem 1.8rem;
            box-shadow: var(--shadow-lg);
            display: flex; align-items: center; gap: 1.2rem;
            transition: transform .3s, box-shadow .3s;
            position: relative; overflow: hidden;
        }}
        .stat-card::before {{
            content: ''; position: absolute;
            top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-dark-rgb), 0.15), transparent);
        }}
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 50px rgba(0,0,0,.3), 0 0 40px rgba(var(--primary-rgb),.1);
        }}
        .stat-icon {{
            width: 56px; height: 56px; border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.6rem; flex-shrink: 0;
        }}
        .stat-icon.s1 {{ background: linear-gradient(135deg, rgba(var(--primary-light-rgb),.2), rgba(var(--primary-light-rgb),.05)); box-shadow: 0 8px 32px rgba(var(--primary-light-rgb),.15); }}
        .stat-icon.s2 {{ background: linear-gradient(135deg, rgba(var(--secondary-rgb),.2), rgba(var(--secondary-rgb),.05)); box-shadow: 0 8px 32px rgba(var(--secondary-rgb),.15); }}
        .stat-icon.s3 {{ background: linear-gradient(135deg, rgba(var(--accent-rgb),.2), rgba(var(--accent-rgb),.05)); box-shadow: 0 8px 32px rgba(var(--accent-rgb),.15); }}
        .stat-label {{ font-size: 0.8rem; color: var(--text-muted); font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }}
        .stat-value {{
            font-size: 1.8rem; font-weight: 800; margin-top: 2px;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text);
            background-clip: text;
        }}
        /* ════════ 免责声明 + 提示 ════════ */
        .notice-wrap {{ max-width: 2400px; margin: 0 auto 1rem; padding: 0 2rem; }}
        .disclaimer-inner {{
            background: var(--glass-bg);
            backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(var(--primary-light-rgb), 0.2);
            border-radius: var(--radius-sm);
            padding: 1rem 1.5rem; font-size: 0.85rem;
            color: var(--text-secondary); line-height: 1.7;
        }}
        .disclaimer-inner strong {{ color: var(--primary-dark); }}
        .disclaimer-inner a {{ color: var(--secondary); text-decoration: underline; }}
        .sort-hint-inner {{
            background: var(--glass-bg);
            backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(var(--primary-light-rgb), 0.2);
            border-radius: var(--radius-sm);
            padding: 0.7rem 1.2rem; font-size: 0.85rem;
            color: var(--text-secondary); font-weight: 500;
            display: flex; align-items: center; gap: 0.55rem; line-height: 1.6;
        }}
        .sort-hint-inner b {{ color: var(--accent); }}
        .stats-bar {{
            margin: -2.25rem auto 0.75rem !important;
            gap: 0.55rem !important;
            align-items: stretch;
        }}
        .stat-card {{
            min-width: 170px !important;
            padding: 0.65rem 0.85rem !important;
            border-radius: 14px !important;
            gap: 0.65rem !important;
            box-shadow: var(--shadow) !important;
        }}
        .stat-icon {{
            width: 34px !important;
            height: 34px !important;
            border-radius: 10px !important;
            font-size: 1rem !important;
        }}
        .stat-label {{
            font-size: 0.68rem !important;
            letter-spacing: 0.2px !important;
        }}
        .stat-value {{
            font-size: 1.12rem !important;
            margin-top: 0 !important;
            line-height: 1.15;
        }}
        .notice-compact {{
            display: block;
            max-width: 2400px;
            margin: 0 auto 0.75rem;
            padding: 0 2rem;
        }}
        .notice-compact > summary {{
            list-style: none;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.38rem 0.72rem;
            border-radius: 999px;
            border: 1px solid rgba(var(--primary-rgb), 0.16);
            background: rgba(var(--glass-tint-rgb), 0.54);
            color: var(--text-secondary);
            font-size: 0.78rem;
            font-weight: 850;
            cursor: pointer;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
        }}
        .notice-compact > summary::-webkit-details-marker {{
            display: none;
        }}
        .notice-compact[open] > summary {{
            margin-bottom: 0.55rem;
            color: var(--primary-dark);
            background: rgba(var(--primary-rgb), 0.10);
        }}
        .notice-compact .disclaimer-inner,
        .notice-compact .sort-hint-inner {{
            font-size: 0.78rem !important;
            padding: 0.55rem 0.85rem !important;
            line-height: 1.45 !important;
            border-radius: 12px !important;
        }}
        /* ════════ 主容器 ════════ */
        .main-wrap {{
            max-width: 2400px; margin: 0 auto;
            padding: 0 2rem 3rem;
        }}
        /* ════════ 筛选卡片 ════════ */
        .filter-card {{
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), 0.56), rgba(var(--glass-tint2-rgb), 0.28)),
                rgba(var(--glass-tint-rgb), 0.22);
            backdrop-filter: blur(38px) saturate(175%);
            -webkit-backdrop-filter: blur(38px) saturate(175%);
            border: 1px solid rgba(var(--primary-rgb), 0.18);
            border-radius: calc(var(--radius) + 4px);
            padding: 1.35rem; box-shadow: 0 18px 56px rgba(var(--shadow-rgb), 0.13), inset 0 1px 0 rgba(255,255,255,.18);
            margin-bottom: 1.5rem; position: relative; overflow: hidden;
        }}
        .filter-card::before {{
            content: ''; position: absolute;
            top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-dark-rgb), 0.15), transparent);
        }}
        .filter-row {{
            display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end;
        }}
        .filter-col {{ flex: 1; min-width: 200px; }}
        .filter-col-type {{ flex: 0 0 150px; min-width: 150px; }}
        .filter-col-btn {{ flex: 0 0 auto; }}
        .filter-label {{
            display: block; font-size: 0.76rem; font-weight: 850;
            color: var(--text-secondary); margin-bottom: 0.42rem;
            text-transform: none; letter-spacing: 0;
        }}
        .filter-card .form-select,
        #searchScope,
        .dataTables_wrapper .dataTables_filter input {{
            min-height: 38px;
            border-radius: 16px !important;
            border: 1px solid rgba(var(--primary-rgb), 0.22) !important;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), 0.72), rgba(var(--glass-tint2-rgb), 0.42)),
                rgba(var(--glass-tint-rgb), 0.28) !important;
            color: var(--text) !important;
            box-shadow: 0 10px 28px rgba(var(--shadow-rgb), 0.08), inset 0 1px 0 rgba(255,255,255,.18) !important;
            backdrop-filter: blur(22px) saturate(165%);
            -webkit-backdrop-filter: blur(22px) saturate(165%);
            font-weight: 750;
            transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease, background .18s ease;
        }}
        .filter-card .form-select:hover,
        #searchScope:hover,
        .dataTables_wrapper .dataTables_filter input:hover {{
            border-color: rgba(var(--primary-rgb), 0.38) !important;
            box-shadow: 0 14px 34px rgba(var(--shadow-rgb), 0.12), inset 0 1px 0 rgba(255,255,255,.22) !important;
        }}
        .filter-card .form-select:focus,
        #searchScope:focus,
        .dataTables_wrapper .dataTables_filter input:focus {{
            border-color: rgba(var(--primary-rgb), 0.56) !important;
            box-shadow: 0 0 0 4px rgba(var(--primary-rgb), 0.14), 0 14px 36px rgba(var(--shadow-rgb), 0.14) !important;
            outline: none !important;
        }}
        .filter-card .form-select option,
        #searchScope option {{
            background: var(--glass-bg-solid);
            color: var(--text);
            font-weight: 700;
        }}
        .filter-header-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-height: 22px;
            margin-bottom: 0.28rem;
        }}
        .filter-header-row .filter-label {{
            margin-bottom: 0 !important;
            font-size: 0.76rem !important;
            font-weight: 700;
        }}
        .exclude-pill-toggle {{
            display: inline-flex;
            align-items: center;
            cursor: pointer;
            user-select: none;
            margin: 0;
        }}
        .exclude-pill-toggle input {{
            position: absolute;
            opacity: 0;
            width: 0;
            height: 0;
        }}
        .exclude-pill-tag {{
            display: inline-flex;
            align-items: center;
            font-size: 0.68rem;
            line-height: 1;
            padding: 2px 7px;
            border-radius: 999px;
            background: rgba(var(--glass-tint-rgb), 0.35);
            color: var(--text-muted);
            border: 1px solid rgba(128,128,128, 0.25);
            transition: all 0.18s ease;
            font-weight: 700;
        }}
        .exclude-pill-toggle:hover .exclude-pill-tag {{
            color: var(--danger, #ef4444);
            border-color: rgba(239, 68, 68, 0.4);
            background: rgba(239, 68, 68, 0.08);
        }}
        .exclude-pill-toggle input:checked + .exclude-pill-tag {{
            background: rgba(239, 68, 68, 0.18) !important;
            color: #ef4444 !important;
            border-color: #ef4444 !important;
            box-shadow: 0 0 6px rgba(239, 68, 68, 0.3);
        }}
        .filter-tools {{
            display: none !important;
        }}
        .exclude-toggle {{
            display: inline-flex; align-items: center; gap: 0.25rem;
            border: 1px solid rgba(var(--primary-rgb), 0.18);
            background: rgba(var(--glass-tint-rgb), 0.45);
            color: var(--text-secondary);
            border-radius: 999px; padding: 0.12rem 0.5rem;
            font-size: 0.72rem; font-weight: 800; cursor: pointer; user-select: none;
            transition: background .16s ease, color .16s ease, border-color .16s ease, transform .16s ease;
        }}
        .exclude-toggle:hover {{
            transform: translateY(-1px);
            border-color: rgba(var(--primary-rgb), 0.34);
            color: var(--primary-dark);
        }}
        .exclude-toggle input {{
            width: 13px; height: 13px; margin: 0; accent-color: var(--danger);
        }}
        .exclude-toggle:has(input:checked) {{
            background: rgba(225, 29, 72, 0.12);
            border-color: rgba(225, 29, 72, 0.34);
            color: var(--danger);
        }}
        .hover-mode-panel {{
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.45rem;
            flex-wrap: wrap;
            margin-top: 0.85rem;
            padding-top: 0.75rem;
            border-top: 1px solid rgba(var(--primary-rgb), 0.12);
        }}
        .hover-mode-label {{
            font-size: 0.76rem;
            font-weight: 900;
            color: var(--text-muted);
            margin-right: 0.1rem;
        }}
        .mode-toggle {{
            display: inline-flex; align-items: center; justify-content: center; gap: 0.35rem;
            border: 1px solid rgba(var(--primary-rgb), 0.20);
            background: rgba(var(--glass-tint-rgb), 0.50);
            color: var(--text-secondary);
            border-radius: 999px; padding: 0.38rem 0.7rem;
            font-size: 0.76rem; font-weight: 850; cursor: pointer; user-select: none;
            white-space: nowrap;
            transition: background .16s ease, color .16s ease, border-color .16s ease, transform .16s ease;
        }}
        .mode-toggle:hover {{
            transform: translateY(-1px);
            color: var(--primary-dark);
            border-color: rgba(var(--primary-rgb), 0.34);
        }}
        .mode-toggle input {{
            width: 14px; height: 14px; margin: 0; accent-color: var(--primary);
        }}
        .mode-toggle:has(input:checked) {{
            background: rgba(var(--primary-rgb), 0.13);
            color: var(--primary-dark);
        }}
        .mode-toggle-mini {{
            padding: 0.25rem 0.55rem;
            font-size: 0.72rem;
            border-radius: 8px;
        }}
        .mode-toggle-header {{
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            z-index: 30;
            margin-top: 4px;
            min-width: 58px;
            height: 24px;
            padding: 0 10px 0 25px;
            border-radius: 999px;
            background: rgba(var(--primary-rgb), 0.08);
            vertical-align: middle;
            pointer-events: auto;
            cursor: pointer;
            user-select: none;
            line-height: 1;
            overflow: visible;
        }}
        .mode-toggle-header > span {{
            position: relative;
            z-index: 2;
            font-size: 0.68rem;
            line-height: 1;
            font-weight: 900;
            color: var(--text-muted);
            pointer-events: none;
            white-space: nowrap;
        }}
        .mode-toggle-header input {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
            pointer-events: none;
        }}
        .mode-toggle-header::before {{
            content: "";
            position: absolute;
            left: 7px;
            top: 50%;
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: rgba(100, 116, 139, 0.72);
            box-shadow: 0 1px 3px rgba(var(--shadow-rgb), 0.18);
            transform: translateY(-50%);
            transition: background .16s ease, box-shadow .16s ease, transform .16s ease;
        }}
        .mode-toggle-header.is-on,
        .mode-toggle-header:has(input:checked) {{
            background: rgba(var(--primary-rgb), 0.18);
            border-color: rgba(var(--primary-rgb), 0.38);
        }}
        .mode-toggle-header.is-on::before,
        .mode-toggle-header:has(input:checked)::before {{
            transform: translateY(-50%) scale(1.18);
            background: var(--primary);
            box-shadow: 0 0 0 4px rgba(var(--primary-rgb), 0.14);
        }}
        .mode-toggle-header.is-on > span,
        .mode-toggle-header:has(input:checked) > span {{
            color: var(--primary);
        }}
        /* ════════ 表格卡片 ════════ */
        .table-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(28px); -webkit-backdrop-filter: blur(28px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius);
            padding: 1.25rem; box-shadow: var(--shadow-lg);
            position: relative; overflow: visible;
        }}
        .table-card::before {{
            content: ''; position: absolute;
            top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-dark-rgb), 0.15), transparent);
        }}
        .table-responsive {{ overflow-x: auto !important; -webkit-overflow-scrolling: touch; }}
        /* DataTables scrollBody 滚动条美化 */
        .dataTables_scrollBody {{
            scrollbar-width: thin;
            scrollbar-color: rgba(var(--primary-rgb),.3) transparent;
        }}
        .dataTables_scrollBody::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        .dataTables_scrollBody::-webkit-scrollbar-track {{ background: transparent; }}
        .dataTables_scrollBody::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, var(--primary), var(--secondary));
            border-radius: 6px;
        }}
        .dataTables_wrapper {{ width: 100% !important; }}
        /* ★★★ 覆盖 Bootstrap 表格 CSS 变量：修复暗色主题下文字不可见 ★★★ */
        .table {{
            --bs-table-color: var(--text-secondary) !important;
            --bs-table-bg: transparent !important;
            --bs-table-striped-color: var(--text-secondary) !important;
            --bs-table-striped-bg: transparent !important;
            --bs-table-hover-color: var(--text) !important;
            --bs-table-hover-bg: rgba(var(--primary-light-rgb),0.06) !important;
            color: var(--text-secondary) !important;
            background-color: transparent !important;
            border-color: var(--border) !important;
        }}
        table.dataTable {{
            border-collapse: separate !important;
            border-spacing: 0;
            width: 100% !important;
        }}
        /* ★★★ 修复表头 UI：glassmorphism sticky 表头 ★★★ */
        table.dataTable thead th {{
            background: linear-gradient(135deg, var(--th-bg-1), var(--th-bg-2)) !important;
            color: var(--text) !important;
            font-weight: 700;
            font-size: 0.78rem;
            letter-spacing: 0.3px;
            border: none !important;
            border-bottom: 0 !important;
            padding: 0.85rem 2.15rem 0.85rem 0.8rem !important;
            white-space: nowrap;
            cursor: pointer;
            transition: background 0.2s;
            position: relative;
            min-width: 72px;
        }}
        table.dataTable thead th:hover {{
            background: linear-gradient(135deg, var(--th-sort-bg-1), var(--th-sort-bg-2)) !important;
        }}
        table.dataTable thead th.sorting::after,
        table.dataTable thead th.sorting::before,
        table.dataTable thead th.sorting_asc::after,
        table.dataTable thead th.sorting_asc::before,
        table.dataTable thead th.sorting_desc::after,
        table.dataTable thead th.sorting_desc::before {{
            position: absolute !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            font-size: 0.58em !important;
            width: auto !important;
            text-align: center;
            line-height: 1;
        }}
        table.dataTable thead th.sorting::before,
        table.dataTable thead th.sorting_asc::before,
        table.dataTable thead th.sorting_desc::before {{
            right: 0.92rem !important;
            content: "▲" !important;
            opacity: 0.15;
            color: var(--text-muted);
        }}
        table.dataTable thead th.sorting::after,
        table.dataTable thead th.sorting_asc::after,
        table.dataTable thead th.sorting_desc::after {{
            right: 0.42rem !important;
            content: "▼" !important;
            opacity: 0.15;
            color: var(--text-muted);
        }}
        table.dataTable thead th.sorting_asc {{
            background: linear-gradient(135deg, var(--th-sort-active-bg-1), var(--th-sort-active-bg-2)) !important;
            color: var(--primary-dark) !important;
        }}
        table.dataTable thead th.sorting_desc {{
            background: linear-gradient(135deg, var(--th-sort-active-bg-1), var(--th-sort-active-bg-2)) !important;
            color: var(--primary-dark) !important;
        }}
        table.dataTable thead th.sorting_asc::before {{
            opacity: 1 !important; color: var(--primary) !important;
        }}
        table.dataTable thead th.sorting_desc::after {{
            opacity: 1 !important; color: var(--primary) !important;
        }}
        table.dataTable thead th.sorting_asc,
        table.dataTable thead th.sorting_desc,
        table.dataTable thead th.dt-active-sort {{
            box-shadow: inset 0 0 0 999px rgba(var(--primary-rgb), 0.055) !important;
        }}
        .dataTables_scrollHead th {{
            cursor: pointer !important;
        }}
        .dataTables_scrollHead th.dt-active-sort::after {{
            z-index: 2;
        }}
        .sort-strip {{
            position: relative;
            z-index: 3;
            overflow: hidden;
            height: 26px;
            border-top: 0;
            border-bottom: 0;
            background: linear-gradient(180deg, rgba(var(--primary-rgb), 0.075), rgba(var(--primary-rgb), 0.045));
            pointer-events: auto;
        }}
        .sort-strip::before {{
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            top: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(var(--primary-rgb), 0.24), transparent);
            pointer-events: none;
        }}
        .sort-strip-inner {{
            position: relative;
            height: 100%;
            white-space: nowrap;
        }}
        .sort-strip-seg {{
            position: absolute;
            top: 0;
            height: 100%;
            margin: 0;
            padding: 0;
            border: 0;
            border-right: 0;
            background: transparent;
            cursor: pointer;
            appearance: none;
            -webkit-appearance: none;
            transition: background .16s ease, box-shadow .16s ease, opacity .16s ease;
        }}
        .sort-strip-seg:hover {{
            background: rgba(var(--primary-rgb), 0.10);
        }}
        .sort-strip-seg.active {{
            background: linear-gradient(180deg, rgba(var(--primary-rgb), 0.18), rgba(var(--primary-rgb), 0.26));
            box-shadow: none;
        }}
        .sort-strip-seg.active::after {{
            content: "";
            position: absolute;
            left: 50%;
            top: 50%;
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--primary);
            transform: translate(-50%, -50%);
            box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.12), 0 8px 18px rgba(var(--primary-rgb), 0.25);
        }}
        table.dataTable tbody td.dt-active-sort {{
            background: linear-gradient(180deg, rgba(var(--primary-rgb), 0.045), rgba(var(--primary-rgb), 0.018)) !important;
        }}
        table.dataTable tbody tr:hover td.dt-active-sort {{
            background: linear-gradient(180deg, rgba(var(--primary-rgb), 0.085), rgba(var(--primary-rgb), 0.035)) !important;
        }}
        table.dataTable tbody td {{
            padding: 0.45rem 0.5rem !important;
            font-size: 0.8rem;
            border-bottom: 1px solid rgba(var(--line-rgb), 0.04);
            vertical-align: middle;
            color: var(--text-secondary) !important;
        }}
        table.dataTable tbody tr {{
            transition: background 0.15s;
        }}
        table.dataTable tbody tr:nth-child(odd) {{
            background: rgba(var(--primary-light-rgb),0.02);
        }}
        table.dataTable tbody tr:hover {{
            background: rgba(var(--primary-light-rgb),0.08) !important;
        }}
        /* ★★★ 表格列样式 ★★★ */
        .td-title {{ min-width: 220px; position: relative; }}
        .td-title.has-cover {{
            padding-right: 122px !important;
        }}
        .modpack-cover-thumb {{
            position: absolute !important;
            right: 2px;
            top: 50%;
            transform: translateY(-50%);
            width: 124px !important;
            height: 78px !important;
            aspect-ratio: 480 / 300 !important;
            padding: 0;
            border: 1px solid rgba(var(--primary-rgb), 0.20);
            border-radius: 18px;
            background: rgba(var(--glass-tint-rgb), 0.46);
            box-shadow: 0 12px 26px rgba(var(--shadow-rgb), 0.18);
            overflow: hidden;
            z-index: 2;
            cursor: zoom-in;
        }}
        .modpack-cover-thumb img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}
        .modpack-cover-thumb:hover {{
            transform: translateY(-50%) scale(1.06);
            border-color: rgba(var(--primary-rgb), 0.45);
        }}
        .td-title .modpack-link {{
            color: var(--primary-light); text-decoration: none;
            font-weight: 600; transition: all 0.2s; cursor: pointer;
            display: flex; flex-direction: column; gap: 2px;
            padding: 2px 0 5px;
            line-height: 1.24;
            max-width: 100%;
        }}
        .modpack-title-cn {{
            color: var(--text);
            font-weight: 850;
            font-size: 0.9rem;
            white-space: normal;
        }}
        .modpack-title-en {{
            color: var(--text-muted);
            font-weight: 650;
            font-size: 0.74rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .modpack-type-badge {{
            display: inline-flex;
            align-items: center;
            width: fit-content;
            max-width: 100%;
            margin-top: 2px;
            padding: 1px 7px;
            border-radius: 999px;
            border: 1px solid rgba(var(--primary-rgb), 0.18);
            background: rgba(var(--primary-rgb), 0.08);
            color: var(--primary-dark);
            font-size: 0.68rem;
            font-weight: 850;
            text-decoration: none;
        }}
        a.modpack-type-badge:hover {{
            background: rgba(var(--primary-rgb), 0.16);
            color: var(--primary);
        }}
        .modpack-meta-row {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
            margin-top: 1px;
        }}
        .modpack-views-badge {{
            display: inline-flex;
            align-items: center;
            width: fit-content;
            padding: 1px 7px;
            border-radius: 999px;
            border: 1px solid rgba(var(--secondary-rgb), 0.16);
            background: rgba(var(--secondary-rgb), 0.07);
            color: var(--text-muted);
            font-size: 0.68rem;
            font-weight: 850;
            white-space: nowrap;
        }}
        .td-title .modpack-link:hover {{
            color: var(--text); text-decoration: underline;
            text-underline-offset: 2px;
        }}
        .td-num {{
            text-align: right; font-variant-numeric: tabular-nums;
            font-weight: 500; white-space: nowrap;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-secondary) !important;
        }}
        .td-engage {{
            min-width: 132px;
            max-width: 150px;
            cursor: pointer;
        }}
        .engage-cell {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 4px;
            align-items: stretch;
        }}
        .engage-cell span {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-width: 0;
            padding: 3px 4px;
            border-radius: 7px;
            background: rgba(var(--primary-rgb), .055);
            border: 1px solid rgba(var(--primary-rgb), .10);
            position: relative;
        }}
        .engage-comment-trigger {{
            cursor: pointer;
            padding-right: 22px !important;
            background: linear-gradient(135deg, rgba(var(--primary-rgb), .12), rgba(var(--secondary-rgb), .08)) !important;
            border-color: rgba(var(--primary-rgb), .22) !important;
            outline: none;
            transition: transform .16s ease, border-color .16s ease, background .16s ease, box-shadow .16s ease;
        }}
        .engage-comment-trigger:hover,
        .engage-comment-trigger:focus-visible {{
            transform: translateY(-1px);
            border-color: rgba(var(--primary-rgb), .42) !important;
            background: linear-gradient(135deg, rgba(var(--primary-rgb), .18), rgba(var(--secondary-rgb), .12)) !important;
            box-shadow: 0 8px 18px rgba(var(--primary-rgb), .12);
        }}
        .comment-open-dot {{
            position: absolute;
            right: 4px;
            top: 50%;
            transform: translateY(-50%);
            width: 18px;
            height: 18px;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, var(--primary), var(--primary-light));
            color: #fff;
            font-size: 0.72rem;
            line-height: 1;
            font-style: normal;
            font-weight: 900;
            box-shadow: 0 5px 12px rgba(var(--primary-rgb), .26), inset 0 1px 0 rgba(255,255,255,.32);
        }}
        .engage-comment-trigger:hover .comment-open-dot,
        .engage-comment-trigger:focus-visible .comment-open-dot {{
            transform: translateY(-50%) scale(1.08);
        }}
        .engage-cell b {{
            color: var(--text);
            font-family: 'JetBrains Mono', monospace;
            font-size: .78rem;
            line-height: 1.05;
        }}
        .engage-cell em {{
            color: var(--text-muted);
            font-style: normal;
            font-size: .64rem;
            line-height: 1.1;
        }}
        .td-score {{ color: var(--success) !important; font-weight: 700; font-size: 0.92rem; }}
        .td-views {{ color: var(--secondary) !important; font-weight: 800; min-width: 86px; white-space: nowrap; }}
        .td-max {{ color: var(--coral) !important; font-weight: 600; }}
        .td-latest {{ color: var(--primary-light) !important; font-weight: 600; }}
        .td-avg {{ color: var(--text) !important; font-weight: 500; }}
        .td-days {{ color: var(--text-muted) !important; font-weight: 500; font-size: 0.78rem; }}
        .td-up {{ color: var(--success) !important; font-weight: 700; }}
        .td-down {{ color: var(--danger) !important; font-weight: 700; }}
        .td-flat {{ color: var(--text-muted) !important; font-weight: 500; }}
        .td-trend {{
            min-width: 190px;
            position: relative;
        }}
        .trend-consolidated-cell {{
            position: relative;
            display: flex;
            flex-direction: column;
            gap: 4px;
            min-height: 64px;
            justify-content: center;
            padding-top: 4px;
        }}
        .trend-score-badge {{
            position: absolute;
            left: 0;
            top: 0;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 7px;
            border-radius: 999px;
            border: 1px solid rgba(var(--primary-rgb), 0.22);
            background: rgba(var(--primary-rgb), 0.10);
            color: var(--primary-dark);
            font-size: 0.66rem;
            font-weight: 850;
            line-height: 1.1;
            box-shadow: 0 6px 16px rgba(var(--primary-rgb), 0.08);
        }}
        .trend-score-badge span {{
            color: var(--text-muted);
            font-weight: 750;
        }}
        .trend-score-badge b {{
            color: var(--primary);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
        }}
        .trend-main-row {{
            display: grid;
            grid-template-columns: minmax(120px, 1fr) auto;
            align-items: center;
            gap: 10px;
            margin-top: 14px;
        }}
        .trend-val-lat {{
            align-self: end;
        }}
        .trend-open-hint {{
            grid-column: 2;
            justify-self: end;
            margin-top: -6px;
            padding: 1px 6px;
            border-radius: 999px;
            border: 1px solid rgba(var(--primary-rgb), .18);
            background: rgba(var(--primary-rgb), .08);
            color: var(--primary);
            font-size: 0.64rem;
            font-weight: 800;
            line-height: 1.35;
            white-space: nowrap;
        }}
        .td-trend:hover .trend-open-hint {{
            background: rgba(var(--primary-rgb), .16);
            border-color: rgba(var(--primary-rgb), .32);
        }}
        .sparkline-svg {{
            width: 100%;
            max-width: 150px;
            min-width: 118px;
            height: 42px;
            filter: drop-shadow(0 5px 10px rgba(var(--primary-rgb), .10));
            cursor: crosshair;
        }}
        .trend-inline-probe {{
            position: absolute;
            z-index: 20;
            min-width: 92px;
            padding: 5px 7px;
            border-radius: 9px;
            border: 1px solid rgba(var(--primary-rgb), 0.24);
            background: rgba(var(--glass-tint-rgb), 0.92);
            color: var(--text);
            box-shadow: 0 10px 24px rgba(var(--shadow-rgb), 0.16);
            font-size: 0.72rem;
            line-height: 1.25;
            pointer-events: none;
            backdrop-filter: blur(14px) saturate(150%);
            -webkit-backdrop-filter: blur(14px) saturate(150%);
        }}
        .trend-inline-probe b {{
            display: block;
            color: var(--primary);
            font-size: 0.78rem;
            font-family: 'JetBrains Mono', monospace;
        }}
        .trend-meta-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.72rem;
            color: var(--text-muted);
            gap: 8px;
            padding-left: 2px;
        }}
        .header-consolidated {{
            padding: 0.4rem 0.5rem !important;
            vertical-align: middle;
        }}
        .header-sort-switcher {{
            display: inline-flex;
            gap: 2px;
            background: rgba(var(--primary-rgb), 0.08);
            border: 1px solid rgba(var(--line-rgb), 0.15);
            border-radius: 6px;
            padding: 2px;
        }}
        .header-mode-title {{
            display: inline-flex;
            align-items: center;
            min-height: 24px;
            padding: 2px 7px;
            border-radius: 6px;
            background: rgba(var(--primary-rgb), 0.08);
            border: 1px solid rgba(var(--line-rgb), 0.15);
            color: var(--text);
            font-size: 0.72rem;
            font-weight: 800;
        }}
        .sort-option {{
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--text-secondary);
            font-weight: 600;
            user-select: none;
        }}
        .sort-option:hover {{
            background: rgba(var(--primary-rgb), 0.12);
            color: var(--text);
        }}
        .sort-option.active {{
            background: var(--primary);
            color: #fff !important;
            box-shadow: 0 2px 6px rgba(var(--primary-rgb), 0.25);
        }}
        /* 标签 */
        .tag-wrap {{
            display: flex; flex-wrap: wrap;
            gap: 6px 5px; align-content: flex-start;
            line-height: 1.5; max-height: 280px;
            overflow-y: auto; padding: 2px;
            scrollbar-width: thin; scrollbar-color: rgba(var(--primary-rgb),.3) transparent;
        }}
        .tag-wrap::-webkit-scrollbar {{ width: 4px; }}
        .tag-wrap::-webkit-scrollbar-thumb {{ background: rgba(var(--primary-rgb),.3); border-radius: 4px; }}
        .tag-combo-container {{
            max-height: none;
            min-width: 280px;
            overflow: visible;
            display: grid;
            gap: 8px;
        }}
        .tag-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        .tag-group-block + .tag-group-block {{
            padding-top: 7px;
            border-top: 1px solid rgba(var(--line-rgb), .12);
        }}
        .tag-group-label {{
            display: flex;
            align-items: center;
            gap: 5px;
            margin: 0 0 4px;
            font-size: 0.68rem;
            font-weight: 800;
            color: var(--text-muted);
            letter-spacing: 0;
        }}
        .tag-group-label::before {{
            content: "";
            width: 5px;
            height: 5px;
            border-radius: 999px;
            background: var(--primary);
            box-shadow: 0 0 0 3px rgba(var(--primary-rgb), .10);
        }}
        .tag-group-label-pack::before {{
            background: var(--secondary);
            box-shadow: 0 0 0 3px rgba(var(--secondary-rgb), .10);
        }}
        .mod-container {{
            max-height: 420px;
            min-width: 0;
            width: 100%;
            display: block;
            padding-right: 4px;
        }}
        .mod-details {{
            display: block;
            width: 100%;
        }}
        .mod-details > summary {{
            list-style: none;
            cursor: pointer;
            display: grid;
            grid-template-columns: auto minmax(0, 1fr) auto;
            gap: 8px;
            align-items: center;
            padding: 5px 7px;
            border: 1px solid rgba(var(--primary-rgb), .18);
            border-radius: 8px;
            background: rgba(var(--primary-rgb), .06);
            user-select: none;
        }}
        .mod-details > summary::-webkit-details-marker {{
            display: none;
        }}
        .mod-details > summary::after {{
            content: "展开";
            justify-self: end;
            color: var(--primary-light);
            font-size: .68rem;
            font-weight: 800;
            padding-left: 6px;
        }}
        .mod-details[open] > summary::after {{
            content: "收起";
        }}
        .mod-summary-main {{
            white-space: nowrap;
            font-size: .78rem;
            font-weight: 800;
            color: var(--text);
        }}
        .mod-summary-main b {{
            color: var(--primary-light);
            font-family: 'JetBrains Mono', monospace;
        }}
        .mod-summary-cats {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            min-width: 0;
            max-height: 54px;
            overflow-y: auto;
        }}
        .mod-summary-chip {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            color: var(--text-secondary);
            background: rgba(var(--secondary-rgb), .08);
            border: 1px solid rgba(var(--secondary-rgb), .13);
            border-radius: 6px;
            padding: 1px 5px;
            font-size: .68rem;
            white-space: nowrap;
            cursor: pointer;
            font: inherit;
            line-height: 1.35;
            transition: all .16s ease;
        }}
        .mod-summary-chip:hover {{
            color: var(--primary-light);
            background: rgba(var(--primary-rgb), .14);
            border-color: rgba(var(--primary-rgb), .28);
        }}
        .mod-summary-chip b {{
            color: var(--primary-light);
            font-family: 'JetBrains Mono', monospace;
        }}
        .mod-details-body {{
            margin-top: 8px;
        }}
        .mod-category-section.jump-focus {{
            animation: modJumpFocus 1.25s ease;
        }}
        @keyframes modJumpFocus {{
            0%, 100% {{ box-shadow: none; }}
            18% {{ box-shadow: 0 0 0 2px rgba(var(--primary-rgb), .28), 0 12px 28px rgba(var(--primary-rgb), .18); }}
            55% {{ box-shadow: 0 0 0 1px rgba(var(--primary-rgb), .18), 0 8px 18px rgba(var(--primary-rgb), .12); }}
        }}
        .tag-cat {{
            position: relative;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: linear-gradient(135deg, rgba(var(--primary-light-rgb),.15), rgba(var(--primary-rgb),.05));
            color: var(--primary-light);
            border: 1px solid rgba(var(--primary-rgb),.25);
            border-radius: 7px; padding: 2px 7px;
            font-size: 0.8rem; font-weight: 600; white-space: nowrap;
            cursor: pointer;
            transition: all .2s ease;
        }}
        .tag-cat:hover {{
            background: linear-gradient(135deg, rgba(var(--primary-light-rgb),.25), rgba(var(--primary-rgb),.1));
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(var(--primary-rgb),.15);
        }}
        .tag-pack {{
            position: relative;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: rgba(var(--secondary-rgb),.06);
            color: var(--text-secondary);
            border: 1px solid rgba(var(--secondary-rgb),.15);
            border-radius: 7px; padding: 2px 7px;
            font-size: 0.78rem; font-weight: 500; white-space: nowrap;
            cursor: pointer;
            transition: all .2s ease;
        }}
        .tag-pack:hover {{
            background: rgba(var(--secondary-rgb),.12);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(var(--secondary-rgb),.15);
        }}
        .tag-filter-name {{
            pointer-events: none;
        }}
        .tag-filter-open {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 17px;
            height: 17px;
            border-radius: 5px;
            border: 1px solid rgba(var(--line-rgb), .14);
            background: rgba(var(--glass-tint-rgb), .42);
            color: var(--text-secondary) !important;
            text-decoration: none;
            font-size: .66rem;
            font-weight: 850;
            opacity: .78;
        }}
        .tag-filter-open:hover {{
            opacity: 1;
            background: rgba(var(--primary-rgb), .18);
            color: var(--primary-dark) !important;
        }}
        .tag-mod {{
            position: relative;
            display: inline-flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 1px;
            background: rgba(var(--primary-rgb),.055);
            color: var(--text);
            border: 1px solid rgba(var(--primary-rgb),.12);
            border-radius: 7px; padding: 4px 28px 4px 7px;
            font-size: 0.75rem; font-weight: 550;
            min-width: 0;
            text-decoration: none;
            transition: all .2s ease;
            cursor: pointer;
        }}
        .tag-mod:hover {{
            background: rgba(var(--primary-rgb),.16);
            color: var(--primary-light);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(var(--primary-rgb),.14);
        }}
        .tag-mod.active-tag {{
            background: rgba(var(--secondary-rgb),.18);
            border-color: rgba(var(--secondary-rgb),.42);
            color: var(--secondary);
            box-shadow: 0 0 0 2px rgba(var(--secondary-rgb),.10);
        }}
        .tag-mod-name {{
            padding-right: 2px;
        }}
        .tag-mod-open {{
            position: absolute;
            top: 4px;
            right: 4px;
            width: 20px;
            height: 20px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 6px;
            border: 1px solid rgba(var(--line-rgb), .14);
            background: rgba(var(--glass-tint-rgb), .46);
            color: var(--text-secondary) !important;
            text-decoration: none;
            font-size: .72rem;
            font-weight: 850;
            opacity: .78;
            transition: all .16s ease;
        }}
        .tag-mod-open:hover {{
            opacity: 1;
            background: rgba(var(--primary-rgb), .18);
            color: var(--primary-dark) !important;
            transform: translateY(-1px);
        }}
        .tag-mod-version {{
            color: var(--text-muted);
            font-size: 0.66rem;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1.15;
        }}
        .mod-category-section {{
            margin: 0 0 9px 0;
        }}
        .mod-category-section:last-child {{
            margin-bottom: 0;
        }}
        .mod-category-head {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            margin: 0 0 5px 0;
            padding: 2px 8px;
            border-radius: 7px;
            color: #fff;
            background: linear-gradient(135deg, rgba(var(--primary-rgb), .9), rgba(var(--secondary-rgb), .72));
            box-shadow: 0 4px 14px rgba(var(--primary-rgb), .14);
            font-size: 0.72rem;
            font-weight: 750;
        }}
        .mod-category-head a {{
            color: #fff;
            text-decoration: none;
        }}
        .mod-category-head span:last-child {{
            opacity: .78;
            font-family: 'JetBrains Mono', monospace;
            font-size: .66rem;
        }}
        .mod-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 5px 7px;
        }}
        .tag-empty {{
            color: var(--text-muted); font-size: 0.78rem; opacity: 0.5;
        }}
        /* 按钮 */
        .mod-details > summary {{
            width: 100%;
            grid-template-columns: auto minmax(0, 1fr) 26px !important;
            gap: 10px !important;
            padding: 7px 9px !important;
            min-height: 38px;
            border-radius: 12px !important;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .58), rgba(var(--glass-tint2-rgb), .30)),
                rgba(var(--primary-rgb), .045) !important;
            border-color: rgba(var(--primary-rgb), .20) !important;
            box-shadow: 0 8px 20px rgba(var(--shadow-rgb), .08), inset 0 1px 0 rgba(255,255,255,.16);
            backdrop-filter: blur(14px) saturate(145%);
            -webkit-backdrop-filter: blur(14px) saturate(145%);
        }}
        .mod-details > summary::after {{
            content: "⌄" !important;
            width: 26px;
            height: 26px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            background: rgba(var(--primary-rgb), .12);
            border: 1px solid rgba(var(--primary-rgb), .20);
            padding: 0 !important;
            font-size: .9rem !important;
        }}
        .mod-details[open] > summary::after {{
            content: "⌃" !important;
        }}
        .mod-summary-cats {{
            justify-content: flex-end;
            max-height: 28px !important;
            overflow: hidden !important;
            min-width: 0;
        }}
        .mod-details[open] .mod-summary-cats {{
            justify-content: flex-start;
            max-height: 52px !important;
        }}
        .mod-details-body {{
            margin-top: 6px !important;
        }}
        .mod-grid {{
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            gap: 5px 8px !important;
            align-items: stretch;
        }}
        .tag-mod {{
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            min-height: 28px;
            padding: 4px 30px 4px 8px !important;
            border-radius: 6px !important;
            background: rgba(var(--glass-tint-rgb), .34) !important;
            border: 1px solid rgba(var(--line-rgb), .12) !important;
            box-shadow: none !important;
        }}
        .tag-mod:hover {{
            background: rgba(var(--primary-rgb), .09) !important;
            box-shadow: 0 4px 12px rgba(var(--shadow-rgb), .08) !important;
        }}
        .tag-mod-name {{
            display: block;
            min-width: 0;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            padding-right: 0 !important;
        }}
        .tag-mod-version {{
            flex: 0 0 auto;
            margin-left: 4px;
            white-space: nowrap;
        }}
        .tag-mod-open {{
            position: absolute !important;
            top: 50% !important;
            right: 4px !important;
            transform: translateY(-50%) !important;
            width: 20px !important;
            height: 20px !important;
        }}
        .tag-mod-open:hover {{
            transform: translateY(-50%) scale(1.05) !important;
        }}
        .btn-reset {{
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            color: var(--text-secondary); font-weight: 700;
            padding: 0.6rem 1.4rem; border-radius: 10px;
            transition: all 0.2s; cursor: pointer; white-space: nowrap;
        }}
        .btn-reset:hover {{
            background: var(--primary); color: #fff; border-color: var(--primary);
            box-shadow: 0 8px 24px rgba(var(--primary-rgb),.25);
        }}
        /* Select2 玻璃态 */
        .select2-container--bootstrap-5 .select2-selection {{
            border-radius: 16px !important;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), 0.72), rgba(var(--glass-tint2-rgb), 0.42)),
                rgba(var(--glass-tint-rgb), 0.28) !important;
            border: 1px solid rgba(var(--primary-rgb), 0.22) !important;
            color: var(--text) !important;
            min-height: 40px;
            box-shadow: 0 10px 28px rgba(var(--shadow-rgb), 0.08), inset 0 1px 0 rgba(255,255,255,.18) !important;
            backdrop-filter: blur(22px) saturate(165%);
            -webkit-backdrop-filter: blur(22px) saturate(165%);
            transition: border-color .18s ease, box-shadow .18s ease, background .18s ease;
        }}
        .select2-container--bootstrap-5.select2-container--focus .select2-selection,
        .select2-container--bootstrap-5.select2-container--open .select2-selection {{
            border-color: rgba(var(--primary-rgb), 0.56) !important;
            box-shadow: 0 0 0 4px rgba(var(--primary-rgb), 0.14), 0 14px 36px rgba(var(--shadow-rgb), 0.14) !important;
        }}
        .select2-container--bootstrap-5 .select2-selection--multiple {{
            max-height: 98px;
            overflow-y: auto;
            padding: 3px 8px !important;
        }}
        .select2-container--bootstrap-5 .select2-selection--multiple .select2-selection__choice {{
            background: linear-gradient(135deg, rgba(var(--primary-rgb), .92), rgba(var(--secondary-rgb), .76)) !important;
            border: 1px solid rgba(255,255,255,.24) !important;
            color: #fff !important;
            border-radius: 999px !important;
            box-shadow: 0 6px 16px rgba(var(--primary-rgb), .18);
            font-weight: 800;
        }}
        .select2-container--bootstrap-5 .select2-selection--single .select2-selection__rendered {{
            line-height: 38px; color: var(--text) !important; font-weight: 750;
        }}
        .select2-container--bootstrap-5 .select2-results__option {{
            color: var(--text) !important;
            font-weight: 700;
            padding: 8px 12px !important;
        }}
        .select2-dropdown {{
            background: rgba(var(--glass-tint-rgb), 0.86) !important;
            backdrop-filter: blur(28px) saturate(180%);
            -webkit-backdrop-filter: blur(28px) saturate(180%);
            border: 1px solid rgba(var(--primary-rgb), 0.25) !important;
            border-radius: 16px !important;
            overflow: hidden;
            box-shadow: 0 18px 46px rgba(var(--shadow-rgb), .18);
        }}
        .select2-container--bootstrap-5 .select2-results__option--selected {{
            background: rgba(var(--primary-rgb),.14) !important;
        }}
        .select2-container--bootstrap-5 .select2-results__option--highlighted {{
            background: linear-gradient(135deg, rgba(var(--primary-rgb),.86), rgba(var(--secondary-rgb),.72)) !important; color: #fff !important;
        }}
        /* DataTables 控件 */
        .dataTables_wrapper {{
            background: transparent !important;
        }}
        .dataTables_wrapper > div {{
            background: transparent !important;
            padding: 0 !important;
        }}
        .dataTables_wrapper > .row:not(.dt-row) {{
            padding: 0.5rem 0 !important;
        }}
        .dataTables_wrapper .dataTables_scroll {{
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        .dataTables_wrapper .dataTables_scrollHead {{
            background: transparent !important;
            border-bottom: none !important;
            padding-bottom: 0 !important;
        }}
        .dataTables_wrapper .dataTables_scrollBody {{
            background: transparent !important;
            border: none !important;
            padding-top: 0 !important;
            margin-top: 0 !important;
        }}
        .dataTables_wrapper .dataTables_scrollBody thead,
        .dataTables_wrapper .dataTables_scrollBody thead tr,
        .dataTables_wrapper .dataTables_scrollBody thead th {{
            height: 0 !important;
            max-height: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            border: 0 !important;
            line-height: 0 !important;
            overflow: hidden !important;
            visibility: collapse !important;
        }}
        .dataTables_wrapper .dataTables_scrollHead table.dataTable thead th {{
            background: linear-gradient(135deg, var(--th-bg-1), var(--th-bg-2)) !important;
        }}
        .dataTables_wrapper .dataTables_processing {{
            background: transparent !important;
            color: var(--text-secondary) !important;
        }}
        .dataTables_wrapper .dataTables_filter,
        .dataTables_wrapper .dataTables_info,
        .dataTables_wrapper .dataTables_paginate {{
            font-size: 0.82rem; color: var(--text-secondary);
            margin: 0.4rem 0;
        }}
        .dataTables_wrapper .dataTables_filter > label,
        .dataTables_wrapper .dataTables_info,
        .dataTables_wrapper .dataTables_paginate {{
            color: var(--text-secondary) !important;
        }}
        .dataTables_wrapper .dataTables_length {{
            display: inline-flex !important;
            align-items: center !important;
            color: var(--text-secondary) !important;
            font-size: 0.82rem;
            vertical-align: middle;
            margin-right: 0.85rem !important;
        }}
        .dataTables_wrapper .dataTables_length label {{
            display: inline-flex !important;
            align-items: center !important;
            font-size: 0.82rem !important;
            color: var(--text-secondary) !important;
            margin: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            padding: 0 !important;
        }}
        .dataTables_wrapper .dataTables_length select {{
            background: var(--glass-bg-solid) !important;
            color: var(--text) !important;
            border: 1px solid var(--glass-border) !important;
            border-radius: 8px !important;
            padding: 4px 10px !important;
            margin: 0 4px !important;
            font-size: 0.82rem;
            cursor: pointer;
        }}
        .dataTables_wrapper .dataTables_length select option {{
            background: var(--glass-bg-solid) !important;
            color: var(--text) !important;
        }}
        .dataTables_wrapper .dataTables_filter input {{
            min-width: 250px;
            padding: 0.42rem 0.78rem;
            margin-left: 0.45rem;
        }}
        .dataTables_wrapper .dataTables_filter input:focus {{
            border-color: var(--primary-light);
            box-shadow: 0 0 0 .2rem rgba(var(--primary-light-rgb),.15);
            outline: none;
        }}
        .dataTables_wrapper .dataTables_filter input::placeholder {{ color: var(--text-muted); }}
        .dataTables_wrapper .dataTables_filter > label {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px;
            border-radius: 22px;
            background: rgba(var(--glass-tint-rgb), 0.22);
            border: 1px solid rgba(var(--primary-rgb), 0.10);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
            backdrop-filter: blur(18px) saturate(150%);
            -webkit-backdrop-filter: blur(18px) saturate(150%);
        }}
        #searchScope {{
            width: auto !important;
            min-width: 190px;
            padding: 0.42rem 2.25rem 0.42rem 0.78rem !important;
            margin-right: 0 !important;
        }}
        /* 分页器样式已统一收敛至后方专用样式区（支持全套主题自适应） */

/* ───── 整合包介绍预览窗（优雅雾化淡入淡出版） ───── */
        .pv-popup {{
            position: fixed; z-index: 99999;
            width: 700px;
            height: 650px;
            max-height: calc(100vh - 40px); max-width: calc(100vw - 24px);
            background: var(--glass-bg-solid);
            border: 2px solid var(--primary);
            border-radius: var(--radius);
            box-shadow: 0 28px 75px rgba(var(--shadow-rgb), 0.35), 0 0 40px rgba(var(--primary-rgb), 0.1);
            overflow: hidden;
            opacity: 0;
            transform: scale(0.9) translateY(12px);
            backdrop-filter: blur(0px) saturate(100%);
            -webkit-backdrop-filter: blur(0px) saturate(100%);
            pointer-events: none;
            display: flex; flex-direction: column;
            transition: opacity .25s cubic-bezier(0.34, 1.56, 0.64, 1), 
                        transform .25s cubic-bezier(0.34, 1.56, 0.64, 1),
                        backdrop-filter .25s ease,
                        -webkit-backdrop-filter .25s ease;
        }}
        .pv-popup.show {{
            opacity: 1;
            transform: scale(1) translateY(0);
            backdrop-filter: blur(28px) saturate(160%) contrast(112%);
            -webkit-backdrop-filter: blur(28px) saturate(160%) contrast(112%);
            pointer-events: auto;
        }}
        .pv-head {{
            display: flex; align-items: center; justify-content: space-between;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            padding: 0.8rem 1.2rem; gap: 0.5rem; flex-shrink: 0;
        }}
        .pv-head-icon {{
            width: 36px; height: 36px; border-radius: 10px;
            background: rgba(255,255,255,.2);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.1rem; flex-shrink: 0;
        }}
        .pv-head-title {{
            flex: 1; overflow: hidden; text-overflow: ellipsis;
            white-space: nowrap; color: #fff; font-weight: 700; font-size: 0.95rem;
            letter-spacing: 0.5px;
        }}
        .pv-actions {{ display: flex; gap: 0.4rem; flex-shrink: 0; }}
        .pv-actions a, .pv-actions span, .pv-actions button {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 28px; height: 28px; border-radius: 7px;
            border: 0;
            background: rgba(255,255,255,.2); color: #fff;
            cursor: pointer; font-size: 0.85rem;
            transition: background 0.15s; text-decoration: none;
        }}
        .pv-actions a:hover, .pv-actions span:hover, .pv-actions button:hover {{ background: rgba(255,255,255,.4); }}
        .pv-body {{
            padding: 1.2rem 1.5rem; overflow-y: auto; flex: 1;
            font-size: 0.95rem; line-height: 1.75;
            color: var(--text) !important;
            word-break: break-word;
        }}
        .pv-para {{
            margin-bottom: 0.6rem;
            line-height: 1.7;
            color: var(--text-main);
            text-align: justify;
        }}
        .intro-blockquote {{
            border-left: 4px solid var(--primary);
            padding: 0.6rem 1rem;
            margin: 0.8rem 0;
            background: rgba(180, 140, 100, 0.08);
            border-radius: 0 4px 4px 0;
            color: var(--text-main);
            font-size: 0.92rem;
            line-height: 1.6;
        }}
        [data-theme="dark"] .intro-blockquote {{
            background: rgba(220, 180, 120, 0.08);
        }}
        .intro-p {{
            margin-bottom: 0.8rem;
            text-align: justify;
        }}
        .pv-section-title {{
            font-weight: 700; font-size: 1.05rem; color: var(--primary);
            margin: 1.2rem 0 0.6rem 0; padding-left: 0.8rem;
            position: relative;
        }}
        .pv-section-title::before {{
            content: ""; position: absolute; left: 0; top: 0.15rem; bottom: 0.15rem;
            width: 4px; background: var(--primary); border-radius: 2px;
        }}
        .pv-list-item {{
            margin-bottom: 0.4rem; padding-left: 1.5rem;
            position: relative; line-height: 1.6;
            color: var(--text-main);
        }}
        .pv-list-item::before {{
            content: "•"; position: absolute; left: 0.5rem; color: var(--primary);
            font-weight: bold; font-size: 1.2rem; line-height: 1.2;
        }}
        .pv-body::-webkit-scrollbar {{ width: 6px; }}
        .pv-body::-webkit-scrollbar-thumb {{ background: rgba(var(--primary-rgb),.3); border-radius: 3px; }}
        .pv-body-empty {{ text-align: center; padding: 2.5rem; color: var(--text-muted); }}
        .pv-body-empty a {{
            display: inline-block; margin-top: 0.5rem; padding: 0.4rem 1rem;
            background: var(--primary); color: #fff; border-radius: 8px;
            text-decoration: none; font-size: 0.85rem;
        }}
        .pv-tip {{
            padding: 0.5rem 1.2rem; background: var(--bg-gradient-2);
            font-size: 0.75rem; color: var(--text-muted);
            border-top: 1px solid var(--border); flex-shrink: 0;
        }}
        .mcmod-consent {{
            position: absolute;
            left: 0; right: 0; bottom: 0; top: auto;
            height: auto;
            z-index: 30;
            display: none;
            padding: 0;
            background: transparent !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
        }}
        .pv-popup.needs-consent .mcmod-consent,
        .comment-popup.needs-consent .mcmod-consent {{
            display: block;
        }}
        .mcmod-consent-panel {{
            width: 100% !important;
            max-width: 100% !important;
            border: none !important;
            border-top: 1px solid var(--glass-border) !important;
            border-radius: 0 0 var(--radius) var(--radius) !important;
            padding: 1rem 1.25rem;
            background: rgba(var(--glass-tint-rgb), 0.85) !important;
            backdrop-filter: blur(20px) saturate(160%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(160%) !important;
            box-shadow: 0 -10px 30px rgba(var(--shadow-rgb), 0.15) !important;
            text-align: center;
            transform: translateY(100%);
            animation: consentSlideUp 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
        }}
        @keyframes consentSlideUp {{
            to {{ transform: translateY(0); }}
        }}
        .pv-popup.needs-consent .mcmod-consent,
        .comment-popup.needs-consent .mcmod-consent {{
            display: flex;
        }}
        .mcmod-consent-panel {{
            width: min(420px, 92%);
            border: 1px solid rgba(var(--primary-rgb), 0.35);
            border-radius: 18px;
            padding: 1.2rem 1.25rem;
            background: rgba(var(--glass-tint-rgb), 0.76);
            box-shadow: 0 18px 44px rgba(var(--shadow-rgb), 0.24);
            text-align: center;
        }}
        .mcmod-consent-brand {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 128px;
            height: 42px;
            padding: 0 16px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            color: #fff;
            font-weight: 800;
            letter-spacing: 0.02em;
            margin-bottom: 0.9rem;
            box-shadow: 0 10px 24px rgba(var(--primary-rgb), 0.28);
        }}
        .mcmod-consent-title {{
            font-size: 1rem;
            font-weight: 800;
            color: var(--text);
            margin-bottom: 0.45rem;
        }}
        .mcmod-consent-text {{
            color: var(--text-secondary);
            font-size: 0.86rem;
            line-height: 1.65;
            margin-bottom: 1rem;
        }}
        .mcmod-consent-ok {{
            border: 0;
            border-radius: 10px;
            background: var(--primary);
            color: #fff;
            padding: 0.55rem 1.2rem;
            font-size: 0.9rem;
            font-weight: 800;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(var(--primary-rgb), 0.28);
        }}
        .mcmod-consent-ok:hover {{
            background: var(--primary-dark);
        }}
        /* ───── 迷你走势悬浮窗（微缩 ECharts 风格 SVG 版） ───── */
        .trend-tooltip {{
            position: fixed; z-index: 100000;
            width: 320px; padding: 12px;
            background: var(--glass-bg-solid);
            border: 2px solid var(--primary);
            border-radius: var(--radius-sm);
            box-shadow: 0 16px 45px rgba(var(--shadow-rgb), 0.4);
            pointer-events: auto;
            display: flex; flex-direction: column; gap: 8px;
            opacity: 0; 
            transform: scale(0.9) translateY(8px);
            backdrop-filter: blur(0px) saturate(100%);
            -webkit-backdrop-filter: blur(0px) saturate(100%);
            transition: opacity 0.25s cubic-bezier(0.34, 1.56, 0.64, 1),
                        transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1),
                        backdrop-filter 0.25s ease,
                        -webkit-backdrop-filter 0.25s ease;
        }}
        .trend-tooltip.show {{
            opacity: 1; 
            transform: scale(1) translateY(0);
            backdrop-filter: blur(28px) saturate(160%) contrast(112%);
            -webkit-backdrop-filter: blur(28px) saturate(160%) contrast(112%);
        }}
        .trend-tooltip.hiding,
        .comment-popup.hiding,
        .pv-popup.hiding {{
            opacity: 0 !important;
            transform: scale(0.98) translateY(8px) !important;
            pointer-events: none !important;
        }}
        .trend-hover-bridge {{
            position: fixed;
            z-index: 99999;
            display: none;
            background: rgba(0, 0, 0, 0.001);
            pointer-events: auto;
        }}
        .trend-tooltip-title {{
            font-size: 0.9rem; font-weight: 700; color: var(--text);
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            padding-right: 28px;
        }}
        .hover-close {{
            width: 26px;
            height: 26px;
            border: 0;
            border-radius: 999px;
            display: inline-grid;
            place-items: center;
            background: rgba(var(--primary-rgb), .12);
            color: var(--primary-dark);
            font-weight: 900;
            cursor: pointer;
            line-height: 1;
            transition: background .16s ease, transform .16s ease;
        }}
        .hover-close:hover {{
            background: rgba(var(--primary-rgb), .22);
            transform: translateY(-1px);
        }}
        .trend-tooltip .hover-close {{
            position: absolute;
            right: 8px;
            top: 8px;
        }}
        .hover-cooldown-tip {{
            font-size: 0.68rem;
            color: var(--text-muted);
            line-height: 1.35;
        }}
        .trend-tooltip-subtitle {{
            font-size: 0.72rem; color: var(--text-secondary);
        }}
        .trend-tooltip-chart-container {{
            width: 100%; height: 130px; position: relative;
        }}
        .trend-tooltip-footer {{
            display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--text-secondary);
            border-top: 1px solid var(--glass-border); padding-top: 6px;
        }}
        .trend-tooltip-footer span {{
            font-weight: 600; color: var(--text);
        }}
        /* ───── 评论悬浮窗（加高 + 优雅雾化淡入淡出版） ───── */
        .comment-popup {{
            position: fixed; z-index: 99999;
            width: 580px;
            height: min(720px, calc(100vh - 48px));
            max-height: min(720px, calc(100vh - 48px)); max-width: calc(100vw - 24px);
            background: var(--glass-bg-solid);
            border: 2px solid var(--primary);
            border-radius: var(--radius-sm);
            box-shadow: 0 28px 75px rgba(var(--shadow-rgb), 0.35);
            overflow: hidden;
            opacity: 0;
            transform: scale(0.9) translateY(12px);
            backdrop-filter: blur(0px) saturate(100%);
            -webkit-backdrop-filter: blur(0px) saturate(100%);
            pointer-events: none;
            display: flex; flex-direction: column;
            transition: opacity .25s cubic-bezier(0.34, 1.56, 0.64, 1), 
                        transform .25s cubic-bezier(0.34, 1.56, 0.64, 1),
                        backdrop-filter .25s ease,
                        -webkit-backdrop-filter .25s ease;
        }}
        .comment-popup.show {{
            opacity: 1; 
            transform: scale(1) translateY(0);
            backdrop-filter: blur(28px) saturate(160%) contrast(112%);
            -webkit-backdrop-filter: blur(28px) saturate(160%) contrast(112%);
            pointer-events: auto;
        }}
        .comment-head {{
            display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
            background: linear-gradient(135deg, var(--primary-dark), var(--primary));
            padding: 0.6rem 1rem; color: #fff; font-size: 0.9rem; font-weight: 700;
        }}
        .comment-head-icon {{
            width: 36px; height: 36px; border-radius: 10px;
            background: rgba(255,255,255,.2);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.1rem; flex-shrink: 0;
        }}
        .comment-head-title {{
            flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis;
            white-space: nowrap; color: #fff; font-weight: 700; font-size: 0.95rem;
            letter-spacing: 0.5px;
        }}
        .comment-head #commentCount {{
            flex-shrink: 0;
            color: inherit;
            font-size: 0.84rem;
        }}
        .comment-search-input {{
            width: min(260px, 35vw); height: 32px; padding: 0 10px;
            border: 2px solid rgba(255,255,255,.82); border-radius: 10px;
            background: rgba(255,255,255,.96); color: #1b3445;
            outline: none; font: inherit; font-size: 0.8rem; font-weight: 500;
        }}
        .comment-search-input::placeholder {{ color: #6c8290; }}
        .comment-search-input:focus {{ border-color: #fff; box-shadow: 0 0 0 3px rgba(255,255,255,.24); }}
        .comment-body {{
            padding: 0.8rem 1.2rem 0.8rem 0.8rem; /* 右边距稍微加大，给滚动条留出安全视觉空间 */
            overflow-y: auto; flex: 1 1 auto; min-height: 0; background: transparent;
            overscroll-behavior: contain;
            position: relative;
        }}
        mark.comment-highlight {{
            background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.28), rgba(var(--secondary-rgb), 0.18)) !important;
            color: var(--text) !important;
            border: 1px solid rgba(var(--primary-rgb), 0.34);
            border-radius: 6px;
            padding: 0 4px;
            font-weight: 850;
            box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.07), 0 6px 16px rgba(var(--primary-rgb), 0.12);
        }}
        .search-nav {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            margin-left: 0.55rem;
            padding: 0.18rem 0.25rem 0.18rem 0.55rem;
            border: 1px solid rgba(var(--primary-rgb), 0.18);
            border-radius: 999px;
            background: rgba(var(--glass-tint-rgb), 0.52);
            color: var(--text-secondary);
            vertical-align: middle;
            box-shadow: 0 8px 20px rgba(var(--shadow-rgb), 0.08);
        }}
        .search-nav-info {{
            min-width: 4.4rem;
            font-size: 0.75rem;
            font-weight: 750;
            text-align: center;
            color: var(--text-secondary);
        }}
        .search-nav-btn {{
            width: 26px;
            height: 26px;
            border: 0;
            border-radius: 999px;
            background: rgba(var(--primary-rgb), 0.12);
            color: var(--primary-dark);
            font-weight: 900;
            line-height: 1;
            cursor: pointer;
            transition: transform .16s ease, background .16s ease, opacity .16s ease;
        }}
        .search-nav-btn:hover {{
            transform: translateY(-1px);
            background: rgba(var(--primary-rgb), 0.22);
        }}
        .search-nav-btn:disabled {{
            opacity: 0.38;
            cursor: default;
            transform: none;
        }}
        table.dataTable tbody tr.search-hit-row > td {{
            box-shadow: inset 3px 0 0 rgba(var(--primary-rgb), 0.5);
        }}
        table.dataTable tbody tr.search-current-row > td {{
            background: linear-gradient(90deg, rgba(var(--primary-rgb), 0.16), rgba(var(--secondary-rgb), 0.08)) !important;
            box-shadow: inset 3px 0 0 var(--primary), inset 0 0 0 999px rgba(var(--primary-rgb), 0.035);
        }}
        /* ───── 滚动条终极视觉高亮（常驻轨道版） ───── */
        /* 1. 宽度锁定 8px */
        .comment-body::-webkit-scrollbar {{
            width: 8px;
        }}
        /* 2. 核心改动：让轨道常驻可见，使用微弱的主题反差色，像一条“滑道”一样标示出来 */
        .comment-body::-webkit-scrollbar-track {{
            background: rgba(var(--primary-rgb), 0.08);
            border-radius: 4px;
            margin: 4px 0;
        }}
        /* 3. 滑块本体：不再使用高透明度，直接给到 0.55 的基础不透明度，确保一眼看得见 */
        .comment-body::-webkit-scrollbar-thumb {{
            background: rgba(var(--primary-rgb), 0.55);
            border-radius: 20px;
            border: 1px solid transparent;
        }}
        /* 4. 鼠标悬停或拖拽时，颜色直接拉满到接近纯色 */
        .comment-body::-webkit-scrollbar-thumb:hover {{
            background: rgba(var(--primary-rgb), 0.9);
            box-shadow: 0 0 8px rgba(var(--primary-rgb), 0.5);
        }}
        /* ───── 新增：底部滑动提示器动画 ───── */
        .scroll-hint-arrow {{
            position: absolute;
            bottom: 55px; /* 定位在分页栏上方一点点 */
            right: 20px;
            background: var(--primary);
            color: #fff !important;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 4px;
            pointer-events: none; /* 穿透鼠标，不干扰点击 */
            box-shadow: 0 4px 10px rgba(var(--primary-rgb), 0.3);
            opacity: 0;
            transform: translateY(5px);
            transition: opacity 0.3s, transform 0.3s;
            z-index: 10;
            animation: hintBounce 1.6s infinite ease-in-out; /* 呼吸浮动动画 */
        }}
        /* 只有当内容溢出、需要滚动时，通过 JS 给 comment-popup 加上 .has-overflow 类名才显示 */
        .comment-popup.has-overflow .scroll-hint-arrow {{
            opacity: 0.85;
            transform: translateY(0);
        }}
        /* 浮动微动动画 */
        @keyframes hintBounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-4px); }}
        }}
        /* ──────────────────────────────────────────────────────── */
        .comment-floor {{
            border-bottom: 1px solid var(--border); padding: 0.8rem 0.4rem;
            background: rgba(var(--primary-light-rgb), 0.02);
        }}
        .comment-floor:last-child {{ border-bottom: none; }}
        .comment-floor-head {{
            font-size: 0.82rem; color: var(--primary-dark); font-weight: 700;
            margin-bottom: 0.3rem; display: flex; gap: 0.5rem; align-items: center; justify-content: space-between;
        }}
        .comment-floor-main {{
            min-width: 0; display: inline-flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;
        }}
        .comment-floor-head .floor-num {{
            background: var(--primary); color: #fff; padding: 1px 7px; border-radius: 4px; font-size: 0.72rem; font-weight: 600;
        }}
        .comment-floor-link, .comment-reply-link {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 24px; height: 24px; border-radius: 7px;
            border: 1px solid rgba(var(--line-rgb), 0.14);
            background: rgba(var(--primary-rgb), 0.08);
            color: var(--text-secondary) !important;
            text-decoration: none; flex-shrink: 0; font-weight: 800;
            transition: background .16s ease, transform .16s ease, color .16s ease;
        }}
        .comment-floor-link:hover, .comment-reply-link:hover {{
            background: rgba(var(--primary-rgb), 0.18);
            color: var(--primary-dark) !important;
            transform: translateY(-1px);
        }}
        .comment-origin-meta {{
            color: var(--text-muted);
            font-size: 0.72rem;
            font-weight: 650;
        }}
        .comment-floor-text {{ font-size: 0.9rem; color: var(--text) !important; line-height: 1.6; font-weight: 500; }}
        .image-gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
            gap: 0.8rem;
            margin: 0.85rem 0 0.35rem;
        }}
        .pv-image-gallery {{
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            margin: 1rem 0 1.05rem;
        }}
        .pv-image-gallery.section-bound {{
            margin-top: 0.7rem;
            margin-bottom: 1.1rem;
        }}
        .pv-cover-wrap {{
            margin: 0.2rem 0 1rem;
        }}
        .pv-cover-wrap .image-thumb {{
            max-width: 360px;
            aspect-ratio: 480 / 300;
        }}
        .comment-image-gallery {{
            grid-template-columns: repeat(auto-fit, minmax(220px, 320px));
            justify-content: start;
        }}
        .image-thumb {{
            display: block;
            position: relative;
            overflow: hidden;
            border-radius: 14px;
            border: 1px solid rgba(var(--line-rgb), 0.12);
            background: rgba(var(--glass-tint-rgb), 0.42);
            box-shadow: 0 10px 24px rgba(var(--shadow-rgb), 0.10);
            aspect-ratio: 16 / 9;
            text-decoration: none;
            cursor: zoom-in;
        }}
        .image-thumb img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
            transition: transform .22s ease, filter .22s ease;
        }}
        .image-thumb:hover img {{
            transform: scale(1.035);
            filter: saturate(1.08) contrast(1.04);
        }}
        .image-caption {{
            position: absolute;
            left: 8px;
            right: 8px;
            bottom: 8px;
            padding: 3px 8px;
            border-radius: 999px;
            background: rgba(var(--glass-tint-rgb), 0.78);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            color: var(--text);
            font-size: 0.68rem;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .inline-emotions {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-left: 6px;
            vertical-align: middle;
        }}
        .inline-emotion {{
            width: 30px;
            height: 30px;
            object-fit: contain;
            vertical-align: middle;
        }}
        .image-lightbox {{
            position: fixed;
            inset: 0;
            z-index: 2147483600;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 4vh 4vw;
            background: rgba(8, 12, 24, 0.58);
            backdrop-filter: blur(24px) saturate(145%);
            -webkit-backdrop-filter: blur(24px) saturate(145%);
        }}
        .image-lightbox.show {{ display: flex; }}
        .image-lightbox-panel {{
            position: relative;
            max-width: min(1180px, 94vw);
            max-height: 92vh;
            padding: 14px;
            border-radius: 22px;
            border: 1px solid rgba(var(--glass-tint-rgb), 0.28);
            background: rgba(var(--glass-tint-rgb), 0.20);
            box-shadow: 0 34px 90px rgba(0, 0, 0, 0.34);
        }}
        .image-lightbox-img {{
            display: block;
            max-width: calc(94vw - 28px);
            max-height: calc(86vh - 72px);
            object-fit: contain;
            border-radius: 14px;
            background: rgba(0, 0, 0, 0.18);
        }}
        .image-lightbox-caption {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            color: #fff;
            margin-top: 10px;
            font-size: 0.86rem;
            font-weight: 700;
        }}
        .image-lightbox-caption a {{
            color: #fff !important;
            text-decoration: none;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
        }}
        .image-lightbox-close {{
            position: absolute;
            right: 12px;
            top: 12px;
            width: 38px;
            height: 38px;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.28);
            background: rgba(255, 255, 255, 0.22);
            color: #fff;
            font-size: 1.4rem;
            line-height: 1;
            cursor: pointer;
        }}
        .comment-reply {{
            margin-left: 1.2rem; padding: 0.5rem 0.8rem;
            background: rgba(var(--shadow-rgb), 0.04); border-left: 3px solid var(--primary-light);
            border-radius: 4px; margin-top: 0.4rem;
        }}
        .comment-reply-head {{ font-size: 0.78rem; color: var(--secondary); font-weight: 700; margin-bottom: 0.2rem; }}
        .comment-reply-head {{
            display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
        }}
        .comment-reply-link {{
            width: 22px; height: 22px; font-size: 0.76rem;
            background: rgba(var(--secondary-rgb), 0.08);
        }}
        .comment-reply-text {{ font-size: 0.84rem; color: var(--text-secondary) !important; line-height: 1.5; }}
        .comment-page-bar {{
            display: flex; align-items: center; justify-content: center; gap: 0.5rem;
            padding: 0.6rem 0.8rem; background: rgba(var(--glass-tint-rgb), 0.25);
            border-top: 1px solid var(--glass-border); flex-shrink: 0; height: 44px;
        }}
        .comment-page-btn {{
            display: inline-flex; align-items: center; justify-content: center;
            min-width: 30px; height: 30px; padding: 0 10px; border-radius: 6px;
            border: 1px solid var(--glass-border); background: var(--glass-bg);
            color: var(--text); font-size: 0.8rem; cursor: pointer;
            transition: all 0.15s; user-select: none; font-weight: 600;
        }}
        .comment-page-btn:hover:not(.disabled) {{ background: rgba(var(--primary-light-rgb), 0.2); border-color: var(--primary); }}
        .comment-page-btn.active {{ background: var(--primary); color: #fff; border-color: var(--primary); }}
        .comment-page-btn.disabled {{ opacity: 0.3; cursor: default; pointer-events: none; }}
        .comment-page-info {{ font-size: 0.78rem; color: var(--text-muted); padding: 0 0.4rem; font-weight: 600; }}
        .comment-empty-hint {{ text-align: center; padding: 2.5rem; color: var(--text-muted); font-size: 0.85rem; }}
        .comment-empty-hint a {{
            display: inline-block; margin-top: 0.5rem; padding: 0.4rem 1rem;
            background: var(--primary); color: #fff; border-radius: 6px;
            text-decoration: none; font-size: 0.8rem;
        }}
    .comment-search-nav {{
        display: flex; align-items: center; justify-content: center; gap: 0.6rem;
        padding: 0.5rem 0.8rem; background: rgba(var(--primary-rgb), 0.05);
        border-top: 1px solid var(--glass-border); flex-shrink: 0;
    }}
    .search-nav-btn {{
        display: inline-flex; align-items: center; justify-content: center;
        height: 26px; padding: 0 10px; border-radius: 6px;
        border: 1px solid rgba(var(--primary-rgb), 0.2); background: rgba(var(--glass-tint-rgb), 0.6);
        color: var(--primary); font-size: 0.74rem; cursor: pointer;
        transition: all 0.2s; user-select: none; font-weight: 600;
    }}
    .search-nav-btn:hover {{
        background: var(--primary) !important; color: #fff !important; border-color: var(--primary) !important;
        transform: translateY(-1px);
    }}
    .search-nav-info {{ font-size: 0.74rem; color: var(--text-secondary); font-weight: 600; margin-right: 0.4rem; }}
    .comment-floor.matched-active {{
        border: 1.5px solid var(--primary) !important;
        background: rgba(var(--primary-rgb), 0.08) !important;
        box-shadow: 0 0 10px rgba(var(--primary-rgb), 0.15) !important;
        transform: scale(1.005);
        transition: all 0.2s ease;
    }}
    .comment-tip {{
            padding: 0.5rem 1rem;
            background: rgba(var(--glass-tint-rgb), 0.15);
            font-size: 0.75rem;
            line-height: 1.6;
            border-top: 1px solid var(--glass-border);
            text-align: center;
        }}
        .comment-tip a {{
            color: var(--primary-dark);
            font-weight: 600;
            text-decoration: none;
        }}
        .comment-tip a:hover {{
            text-decoration: underline;
        }}
        /* ════════ 主题切换器 ════════ */
        .theme-switcher {{
            display: inline-flex;
            gap: 6px;
            background: rgba(var(--glass-tint-rgb), 0.35);
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            border: 1px solid rgba(var(--line-rgb), 0.2);
            border-radius: 16px !important;
            padding: 6px !important;
            box-shadow: 0 8px 32px rgba(var(--shadow-rgb), 0.15), inset 0 1px 0 rgba(255,255,255,0.2) !important;
            vertical-align: middle;
            margin-left: 1rem;
        }}
        .theme-btn {{
            width: auto !important;
            height: 28px !important;
            padding: 4px 10px !important;
            font-size: 0.75rem !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            border: 1px solid rgba(var(--line-rgb), 0.12) !important;
            cursor: pointer;
            transition: all 0.25s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: var(--text-secondary);
            background: rgba(var(--glass-tint2-rgb), 0.4) !important;
        }}
        .theme-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            transition: transform 0.2s ease;
        }}
        .theme-btn:hover {{
            transform: translateY(-1px);
            color: var(--text);
            background: rgba(var(--glass-tint2-rgb), 0.7) !important;
            border-color: rgba(var(--line-rgb), 0.24) !important;
        }}
        .theme-btn.active {{
            border-color: var(--primary) !important;
            background: rgba(var(--primary-rgb), 0.12) !important;
            color: var(--primary) !important;
            box-shadow: 0 0 10px rgba(var(--primary-rgb), 0.2) !important;
            font-weight: 600 !important;
        }}
        .theme-btn.active .theme-dot {{
            transform: scale(1.2);
        }}
        .theme-btn-warm {{ background: linear-gradient(135deg, #f59e0b, #d97706); }}
        .theme-btn-dark {{ background: linear-gradient(135deg, #6366f1, #1a2340); }}
        .theme-btn-light {{ background: linear-gradient(135deg, #ffffff, #e2e8f0); border: 2px solid var(--border); }}
        .theme-btn-anime {{ background: conic-gradient(from 210deg, #2f2830, #d98f5b, #8c6bb1, #b8875d, #4b3734, #ffd7a1, #2f2830); }}
        /* 入场动画 */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .stat-card {{ animation: fadeInUp 0.6s ease-out backwards; }}
        .stats-bar .stat-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .stats-bar .stat-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .stats-bar .stat-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .filter-card {{ animation: fadeInUp 0.6s ease-out 0.3s backwards; }}
        .table-card {{ animation: fadeInUp 0.6s ease-out 0.4s backwards; }}
        /* 响应式 */
        @media (max-width: 768px) {{
            .hero {{ padding: 2rem 1rem 3.5rem; }}
            .hero-title {{ font-size: 1.5rem; }}
            .stats-bar {{ padding: 0 1rem; }}
            .stat-card {{ min-width: 100%; padding: 1rem; }}
            .stat-value {{ font-size: 1.3rem; }}
            .main-wrap {{ padding: 0 1rem 2rem; }}
            .notice-wrap {{ padding: 0 1rem; }}
            .filter-col {{ min-width: 100%; }}
            .pv-popup {{ width: 92vw; }}
            .comment-popup {{ width: 92vw !important; max-width: 580px; }}
            /* DataTables 小屏响应式堆叠与对齐 */
            .dataTables_wrapper .dataTables_length,
            .dataTables_wrapper .dataTables_filter {{
                display: block !important;
                float: none !important;
                text-align: left !important;
                width: 100% !important;
                margin-bottom: 0.5rem !important;
            }}
            .dataTables_wrapper .dataTables_filter input {{
                width: 100% !important;
                margin-left: 0 !important;
                margin-top: 0.25rem !important;
            }}
            .dataTables_wrapper .dataTables_paginate {{
                text-align: center !important;
                float: none !important;
                width: 100% !important;
                display: flex !important;
                justify-content: center !important;
                flex-wrap: wrap !important;
                gap: 4px !important;
            }}
            .dataTables_wrapper .dataTables_paginate .paginate_button {{
                padding: 4px 8px !important;
                margin: 0 !important;
            }}
        }}
        .tag-cat.active-tag {{
            outline: 2px solid var(--primary) !important;
            box-shadow: 0 0 8px rgba(var(--primary-rgb),.6) !important;
            background: linear-gradient(135deg, rgba(var(--primary-light-rgb),.4), rgba(var(--primary-rgb),.15)) !important;
        }}
        .tag-pack.active-tag {{
            outline: 2px solid var(--secondary) !important;
            box-shadow: 0 0 8px rgba(var(--secondary-rgb),.6) !important;
            background: rgba(var(--secondary-rgb),.2) !important;
        }}
        .tag-cat.exclude-active-tag,
        .tag-pack.exclude-active-tag,
        .tag-mod.exclude-active-tag {{
            outline: 2px solid var(--danger) !important;
            box-shadow: 0 0 8px rgba(225, 29, 72, .38) !important;
            background: rgba(225, 29, 72, .12) !important;
            color: var(--danger) !important;
        }}
        /* ════════ 2026 数据终端视觉覆盖层 ════════ */
        :root {{
            --primary: #006adc;
            --primary-light: #248cff;
            --primary-dark: #004fb3;
            --secondary: #00a884;
            --secondary-light: #00c99d;
            --accent: #d946ef;
            --success: #009e73;
            --danger: #e11d48;
            --glass-bg: rgba(255, 255, 255, 0.78);
            --glass-bg-solid: rgba(255, 255, 255, 0.96);
            --glass-border: rgba(0, 83, 179, 0.12);
            --glass-hover: rgba(0, 106, 220, 0.08);
            --glass-shadow: rgba(15, 23, 42, 0.08);
            --bg-main: #eef4fb;
            --bg-gradient-1: #f8fbff;
            --bg-gradient-2: #e9f2ff;
            --bg-gradient-3: #dce8f7;
            --text: #0b1220;
            --text-secondary: #243447;
            --text-muted: rgba(36, 52, 71, 0.6);
            --border: rgba(0, 83, 179, 0.12);
            --shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
            --shadow-lg: 0 24px 60px rgba(15, 23, 42, 0.11);
            --radius: 14px;
            --radius-sm: 10px;
            --primary-rgb: 0, 106, 220;
            --primary-light-rgb: 36, 140, 255;
            --primary-dark-rgb: 0, 79, 179;
            --secondary-rgb: 0, 168, 132;
            --accent-rgb: 217, 70, 239;
            --gold-light-rgb: 165, 180, 252;
            --shadow-rgb: 15, 23, 42;
            --line-rgb: 0, 83, 179;
            --glass-tint-rgb: 255, 255, 255;
            --glass-tint2-rgb: 248, 251, 255;
            --th-bg-1: rgba(248, 251, 255, 0.98);
            --th-bg-2: rgba(233, 242, 255, 0.98);
            --th-sort-bg-1: rgba(224, 242, 254, 0.9);
            --th-sort-bg-2: rgba(186, 230, 253, 0.72);
            --th-sort-active-bg-1: rgba(186, 230, 253, 0.9);
            --th-sort-active-bg-2: rgba(125, 211, 252, 0.78);
        }}
        :root[data-theme="light"] {{
            --primary: #006adc;
            --primary-light: #248cff;
            --primary-dark: #004fb3;
            --secondary: #00a884;
            --secondary-light: #00c99d;
            --accent: #d946ef;
            --success: #009e73;
            --danger: #e11d48;
            --glass-bg: rgba(255, 255, 255, 0.78);
            --glass-bg-solid: rgba(255, 255, 255, 0.96);
            --glass-border: rgba(0, 83, 179, 0.12);
            --glass-hover: rgba(0, 106, 220, 0.08);
            --glass-shadow: rgba(15, 23, 42, 0.08);
            --bg-main: #eef4fb;
            --bg-gradient-1: #f8fbff;
            --bg-gradient-2: #e9f2ff;
            --bg-gradient-3: #dce8f7;
            --text: #0b1220;
            --text-secondary: #243447;
            --text-muted: rgba(36, 52, 71, 0.6);
            --border: rgba(0, 83, 179, 0.12);
            --shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
            --shadow-lg: 0 24px 60px rgba(15, 23, 42, 0.11);
            --primary-rgb: 0, 106, 220;
            --primary-light-rgb: 36, 140, 255;
            --primary-dark-rgb: 0, 79, 179;
            --secondary-rgb: 0, 168, 132;
            --accent-rgb: 217, 70, 239;
            --line-rgb: 0, 83, 179;
            --glass-tint-rgb: 255, 255, 255;
            --glass-tint2-rgb: 248, 251, 255;
            --th-bg-1: rgba(248, 251, 255, 0.98);
            --th-bg-2: rgba(233, 242, 255, 0.98);
            --th-sort-bg-1: rgba(221, 236, 255, 0.96);
            --th-sort-bg-2: rgba(202, 226, 255, 0.88);
            --th-sort-active-bg-1: rgba(188, 219, 255, 0.96);
            --th-sort-active-bg-2: rgba(147, 197, 253, 0.86);
        }}
        :root[data-theme="warm"] {{
            --primary: #008c7a;
            --primary-light: #18b7a1;
            --primary-dark: #006b61;
            --secondary: #2563eb;
            --secondary-light: #60a5fa;
            --accent: #7c3aed;
            --success: #059669;
            --danger: #e11d48;
            --glass-bg: rgba(248, 253, 251, 0.86);
            --glass-bg-solid: rgba(252, 255, 254, 0.98);
            --glass-border: rgba(0, 140, 122, 0.12);
            --glass-hover: rgba(0, 140, 122, 0.075);
            --bg-main: #edf7f5;
            --bg-gradient-1: #fbfffd;
            --bg-gradient-2: #e8f7f2;
            --bg-gradient-3: #dceef4;
            --text: #0b1718;
            --text-secondary: #233b3d;
            --text-muted: rgba(35, 59, 61, 0.58);
            --primary-rgb: 0, 140, 122;
            --primary-light-rgb: 24, 183, 161;
            --primary-dark-rgb: 0, 107, 97;
            --secondary-rgb: 37, 99, 235;
            --accent-rgb: 124, 58, 237;
            --line-rgb: 0, 140, 122;
            --glass-tint-rgb: 252, 255, 254;
            --glass-tint2-rgb: 232, 247, 242;
            --th-bg-1: rgba(252, 255, 254, 0.98);
            --th-bg-2: rgba(234, 247, 244, 0.98);
            --th-sort-bg-1: rgba(214, 246, 240, 0.96);
            --th-sort-bg-2: rgba(188, 235, 226, 0.88);
            --th-sort-active-bg-1: rgba(171, 226, 216, 0.96);
            --th-sort-active-bg-2: rgba(118, 207, 193, 0.84);
        }}
        :root[data-theme="dark"] {{
            --primary: #22d3ee;
            --primary-light: #67e8f9;
            --primary-dark: #0891b2;
            --secondary: #a78bfa;
            --secondary-light: #c4b5fd;
            --accent: #34d399;
            --success: #34d399;
            --danger: #fb7185;
            --glass-bg: rgba(17, 24, 39, 0.82);
            --glass-bg-solid: rgba(20, 28, 42, 0.97);
            --glass-border: rgba(148, 163, 184, 0.18);
            --glass-hover: rgba(34, 211, 238, 0.11);
            --bg-main: #0b1018;
            --bg-gradient-1: #0b1018;
            --bg-gradient-2: #111827;
            --bg-gradient-3: #182033;
            --text: #f8fafc;
            --text-secondary: #d3dee9;
            --text-muted: rgba(211, 222, 233, 0.62);
            --primary-rgb: 34, 211, 238;
            --primary-light-rgb: 103, 232, 249;
            --primary-dark-rgb: 8, 145, 178;
            --secondary-rgb: 167, 139, 250;
            --accent-rgb: 52, 211, 153;
            --line-rgb: 34, 211, 238;
            --glass-tint-rgb: 20, 28, 42;
            --glass-tint2-rgb: 17, 24, 39;
            --th-bg-1: rgba(18, 26, 39, 0.98);
            --th-bg-2: rgba(24, 35, 52, 0.98);
            --th-sort-bg-1: rgba(20, 49, 66, 0.98);
            --th-sort-bg-2: rgba(20, 61, 76, 0.92);
            --th-sort-active-bg-1: rgba(18, 93, 112, 0.72);
            --th-sort-active-bg-2: rgba(34, 211, 238, 0.34);
        }}
        :root[data-theme="eye"] {{
            --primary: #7a6a34;
            --primary-light: #9b894c;
            --primary-dark: #5f5228;
            --secondary: #4f7d67;
            --secondary-light: #6ea38a;
            --accent: #9a6b54;
            --success: #4f7d67;
            --danger: #b45f5a;
            --glass-bg: rgba(255, 252, 243, 0.9);
            --glass-bg-solid: rgba(255, 253, 247, 0.985);
            --glass-border: rgba(122, 106, 52, 0.13);
            --glass-hover: rgba(122, 106, 52, 0.065);
            --bg-main: #f4efe3;
            --bg-gradient-1: #fffdf7;
            --bg-gradient-2: #f3ecdd;
            --bg-gradient-3: #e9e1d0;
            --text: #201d16;
            --text-secondary: #403b2f;
            --text-muted: rgba(64, 59, 47, 0.6);
            --primary-rgb: 122, 106, 52;
            --primary-light-rgb: 155, 137, 76;
            --primary-dark-rgb: 95, 82, 40;
            --secondary-rgb: 79, 125, 103;
            --accent-rgb: 154, 107, 84;
            --line-rgb: 122, 106, 52;
            --glass-tint-rgb: 255, 253, 247;
            --glass-tint2-rgb: 243, 236, 221;
            --th-bg-1: rgba(255, 253, 247, 0.98);
            --th-bg-2: rgba(244, 238, 224, 0.98);
            --th-sort-bg-1: rgba(246, 238, 214, 0.98);
            --th-sort-bg-2: rgba(232, 219, 188, 0.9);
            --th-sort-active-bg-1: rgba(221, 205, 162, 0.96);
            --th-sort-active-bg-2: rgba(194, 171, 113, 0.82);
        }}
        :root[data-theme="pink"] {{
            --primary: #e84a8a;
            --primary-light: #ff7ab1;
            --primary-dark: #c72f70;
            --secondary: #8b5cf6;
            --secondary-light: #a78bfa;
            --accent: #06b6d4;
            --success: #0f9f7a;
            --danger: #e11d48;
            --glass-bg: rgba(255, 247, 251, 0.86);
            --glass-bg-solid: rgba(255, 250, 253, 0.98);
            --glass-border: rgba(232, 74, 138, 0.14);
            --glass-hover: rgba(232, 74, 138, 0.08);
            --bg-main: #fdf2f8;
            --bg-gradient-1: #fffafd;
            --bg-gradient-2: #fce7f3;
            --bg-gradient-3: #eef2ff;
            --text: #20101a;
            --text-secondary: #4a263b;
            --text-muted: rgba(74, 38, 59, 0.58);
            --primary-rgb: 232, 74, 138;
            --primary-light-rgb: 255, 122, 177;
            --primary-dark-rgb: 199, 47, 112;
            --secondary-rgb: 139, 92, 246;
            --accent-rgb: 6, 182, 212;
            --line-rgb: 232, 74, 138;
            --glass-tint-rgb: 255, 250, 253;
            --glass-tint2-rgb: 252, 231, 243;
            --th-bg-1: rgba(255, 250, 253, 0.98);
            --th-bg-2: rgba(252, 231, 243, 0.98);
            --th-sort-bg-1: rgba(253, 226, 240, 0.98);
            --th-sort-bg-2: rgba(251, 207, 232, 0.9);
            --th-sort-active-bg-1: rgba(251, 190, 221, 0.96);
            --th-sort-active-bg-2: rgba(244, 114, 182, 0.72);
        }}
        :root[data-theme="anime"] {{
            --primary: #d98f5b;
            --primary-light: #ffd7a1;
            --primary-dark: #9f5a3b;
            --secondary: #8c6bb1;
            --secondary-light: #c4a7e7;
            --accent: #b8875d;
            --success: #c98a5d;
            --danger: #d26b72;
            --glass-bg: rgba(54, 41, 45, 0.28);
            --glass-bg-solid: rgba(54, 41, 45, 0.62);
            --glass-border: rgba(255, 215, 161, 0.34);
            --glass-hover: rgba(255, 215, 161, 0.12);
            --bg-main: #2f2830;
            --bg-gradient-1: #2f2830;
            --bg-gradient-2: #4b3734;
            --bg-gradient-3: #6a4738;
            --text: #fff3dc;
            --text-secondary: #ecd6b8;
            --text-muted: rgba(236, 214, 184, 0.72);
            --primary-rgb: 217, 143, 91;
            --primary-light-rgb: 255, 215, 161;
            --primary-dark-rgb: 159, 90, 59;
            --secondary-rgb: 140, 107, 177;
            --accent-rgb: 184, 135, 93;
            --line-rgb: 217, 143, 91;
            --glass-tint-rgb: 71, 54, 54;
            --glass-tint2-rgb: 102, 71, 56;
            --th-bg-1: rgba(54, 41, 45, 0.62);
            --th-bg-2: rgba(102, 71, 56, 0.48);
            --th-sort-bg-1: rgba(217, 143, 91, 0.18);
            --th-sort-bg-2: rgba(140, 107, 177, 0.12);
            --th-sort-active-bg-1: rgba(255, 215, 161, 0.26);
            --th-sort-active-bg-2: rgba(217, 143, 91, 0.18);
        }}
        body {{
            background-color: var(--bg) !important;
            background-image:
                radial-gradient(ellipse 80% 50% at 50% -20%, rgba(var(--primary-rgb), 0.10), transparent 70%),
                radial-gradient(ellipse 60% 40% at 90% 10%, rgba(var(--secondary-rgb), 0.06), transparent 60%) !important;
            background-attachment: fixed !important;
            background-size: auto !important;
        }}
        .bg-layer {{
            background:
                linear-gradient(120deg, transparent 0 38%, rgba(var(--primary-rgb), 0.08) 38% 39%, transparent 39% 100%),
                linear-gradient(180deg, rgba(var(--glass-tint-rgb), 0.28), transparent 42%) !important;
        }}
        .bg-layer::before {{
            background: linear-gradient(90deg, rgba(var(--primary-rgb), 0.16), rgba(var(--secondary-rgb), 0.1), rgba(var(--accent-rgb), 0.12)) !important;
            height: 3px; bottom: auto;
        }}
        :root[data-theme="anime"] body {{
            background:
                radial-gradient(circle at 15% 8%, rgba(255, 215, 161, 0.18), transparent 30%),
                radial-gradient(circle at 84% 18%, rgba(196, 167, 231, 0.12), transparent 34%),
                radial-gradient(circle at 20% 86%, rgba(184, 135, 93, 0.20), transparent 36%),
                linear-gradient(135deg, #2f2830, #4b3734 52%, #6a4738) !important;
            background-size: auto !important;
        }}
        :root[data-theme="anime"] .bg-layer {{
            background:
                linear-gradient(115deg, transparent 0 18%, rgba(255, 215, 161, 0.16) 28% 34%, transparent 50%),
                linear-gradient(42deg, transparent 0 52%, rgba(196, 167, 231, 0.10) 62% 68%, transparent 84%),
                radial-gradient(circle at 22% 8%, rgba(255, 243, 220, 0.16), transparent 18%),
                linear-gradient(180deg, rgba(47, 40, 48, 0.50), transparent 48%) !important;
        }}
        :root[data-theme="anime"] .bg-layer::after {{
            content: "";
            position: fixed;
            inset: -20%;
            z-index: -1;
            pointer-events: none;
            background:
                linear-gradient(104deg, transparent 0 8%, rgba(255, 215, 161, 0.20) 18%, transparent 36%),
                linear-gradient(24deg, transparent 0 56%, rgba(184, 135, 93, 0.18) 68%, transparent 88%);
            filter: none;
            opacity: 0.85;
            mix-blend-mode: screen;
            animation: none;
        }}
        @keyframes animeFlow {{
            0% {{ transform: translate3d(-14%, -8%, 0) rotate(-7deg) scale(1.18); filter: hue-rotate(0deg) blur(12px) saturate(260%); }}
            45% {{ transform: translate3d(9%, 7%, 0) rotate(8deg) scale(1.30); filter: hue-rotate(24deg) blur(16px) saturate(330%); }}
            100% {{ transform: translate3d(15%, -9%, 0) rotate(-5deg) scale(1.24); filter: hue-rotate(-18deg) blur(13px) saturate(290%); }}
        }}
        @keyframes animeSheen {{
            0% {{ transform: translateX(-120%) skewX(-18deg); opacity: 0; }}
            18% {{ opacity: 0.42; }}
            100% {{ transform: translateX(120%) skewX(-18deg); opacity: 0; }}
        }}
        :root[data-theme="anime"] .stat-card,
        :root[data-theme="anime"] .filter-card,
        :root[data-theme="anime"] .table-card,
        :root[data-theme="anime"] .disclaimer-inner,
        :root[data-theme="anime"] .sort-hint-inner {{
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, rgba(80, 24, 52, 0.58), rgba(156, 63, 34, 0.28)) !important;
            border: 1px solid rgba(255, 138, 36, 0.40) !important;
            box-shadow: 0 24px 80px rgba(97, 20, 58, 0.44), inset 0 1px 0 rgba(255,247,239,0.18), inset 0 0 56px rgba(143, 53, 255, 0.12) !important;
            backdrop-filter: blur(36px) saturate(230%) contrast(118%) !important;
            -webkit-backdrop-filter: blur(36px) saturate(230%) contrast(118%) !important;
        }}
        :root[data-theme="anime"] .stat-card::after,
        :root[data-theme="anime"] .filter-card::after,
        :root[data-theme="anime"] .table-card::after,
        :root[data-theme="anime"] .disclaimer-inner::after,
        :root[data-theme="anime"] .sort-hint-inner::after {{
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            background:
                linear-gradient(108deg, transparent 0 16%, rgba(255, 138, 36, 0.36) 30%, rgba(143, 53, 255, 0.24) 44%, transparent 66%),
                linear-gradient(72deg, transparent 0 44%, rgba(184, 115, 51, 0.26) 58%, transparent 80%),
                radial-gradient(circle at 18% 0%, rgba(255,247,239,0.18), transparent 24%);
            mix-blend-mode: screen;
            animation: none;
            opacity: 0.42;
        }}
        :root[data-theme="anime"] .table-card {{
            background:
                linear-gradient(135deg, rgba(80, 24, 52, 0.62), rgba(156, 63, 34, 0.32)),
                linear-gradient(90deg, rgba(255, 77, 31, 0.20), transparent 28%, rgba(143, 53, 255, 0.16), transparent 58%, rgba(184, 115, 51, 0.18)) !important;
        }}
        :root[data-theme="anime"] .dataTables_scrollHead,
        :root[data-theme="anime"] .sort-strip {{
            background: linear-gradient(90deg, rgba(255, 77, 31, 0.26), rgba(184, 115, 51, 0.18), rgba(143, 53, 255, 0.18)) !important;
        }}
        :root[data-theme="anime"] table.dataTable tbody td {{
            color: rgba(255, 247, 239, 0.86) !important;
            border-bottom-color: rgba(255, 138, 36, 0.12) !important;
        }}
        :root[data-theme="anime"] table.dataTable tbody tr:hover {{
            background: linear-gradient(90deg, rgba(255, 77, 31, 0.22), rgba(143, 53, 255, 0.12), rgba(184, 115, 51, 0.16)) !important;
        }}
        :root[data-theme="anime"] .hero-title,
        :root[data-theme="anime"] .stat-value,
        :root[data-theme="anime"] .modpack-link {{
            background: linear-gradient(90deg, #ff8a24, #fff7ef, #ff2d16, #8f35ff, #b87333, #ff8a24) !important;
            background-size: 320% 100% !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            color: transparent !important;
            -webkit-text-fill-color: transparent !important;
            animation: none;
        }}
        @keyframes animeTextFlow {{
            0% {{ background-position: 0% 50%; }}
            100% {{ background-position: 320% 50%; }}
        }}
        :root[data-theme="anime"] .theme-switcher {{
            background: rgba(80, 24, 52, 0.68) !important;
            border-color: rgba(255, 138, 36, 0.42) !important;
            box-shadow: 0 12px 34px rgba(255, 77, 31, 0.20), inset 0 1px 0 rgba(255,247,239,0.16) !important;
        }}
        :root[data-theme="anime"] .theme-btn.active {{
            border-color: #ff8a24 !important;
            box-shadow: 0 0 0 2px rgba(255, 77, 31, 0.34), 0 0 24px rgba(143, 53, 255, 0.38) !important;
        }}
        :root[data-theme="anime"] .dataTables_scrollBody::-webkit-scrollbar-thumb,
        :root[data-theme="anime"] .comment-body::-webkit-scrollbar-thumb,
        :root[data-theme="anime"] .pv-body::-webkit-scrollbar-thumb {{
            background: linear-gradient(180deg, #ff8a24, #8f35ff 52%, #b87333) !important;
            box-shadow: 0 0 18px rgba(255, 77, 31, 0.44) !important;
        }}
        :root[data-theme="anime"] .tag-cat {{
            background: rgba(255, 77, 31, 0.20) !important;
            border-color: rgba(255, 138, 36, 0.34) !important;
            color: #ffd5bd !important;
        }}
        :root[data-theme="anime"] .tag-pack {{
            background: rgba(143, 53, 255, 0.18) !important;
            border-color: rgba(189, 120, 255, 0.30) !important;
            color: #e5c8ff !important;
        }}
        .orb {{ display: none !important; }}
        .hero {{
            padding: 1.55rem 2rem 4rem !important;
            background: linear-gradient(180deg, rgba(var(--glass-tint-rgb), 0.62), rgba(var(--glass-tint2-rgb), 0.2)) !important;
            border-bottom: 1px solid var(--glass-border) !important;
        }}
        .hero-title {{
            font-size: clamp(1.65rem, 2.2vw, 2.45rem) !important;
            letter-spacing: 0 !important;
            -webkit-text-fill-color: unset !important;
            background: none !important;
            color: var(--text) !important;
        }}
        .hero-sub {{ color: var(--text-muted) !important; }}
        .stats-bar {{ gap: 0.9rem !important; margin-top: -2.45rem !important; }}
        .stat-card, .filter-card, .table-card, .disclaimer-inner, .sort-hint-inner {{
            border-radius: var(--radius) !important;
            background: var(--glass-bg) !important;
            border: 1px solid var(--glass-border) !important;
            box-shadow: var(--shadow) !important;
        }}
        .stat-card {{ min-width: 220px !important; padding: 1.05rem 1.2rem !important; }}
        .stat-card:hover {{ transform: translateY(-2px) !important; box-shadow: var(--shadow-lg) !important; }}
        .stat-icon {{
            width: 44px !important; height: 44px !important; border-radius: 10px !important;
            font-size: 1.18rem !important;
        }}
        .stat-label {{ letter-spacing: 0 !important; text-transform: none !important; }}
        .stat-value {{ font-size: 1.45rem !important; }}
        .filter-card {{ padding: 1rem !important; }}
        .filter-label {{ letter-spacing: 0 !important; text-transform: none !important; }}
        .table-card {{ padding: 0.8rem !important; }}
        table.dataTable thead th {{
            border-bottom: 0 !important;
            font-size: 0.74rem !important;
            letter-spacing: 0 !important;
            padding: 0.72rem 2.1rem 0.72rem 0.72rem !important;
            min-width: 78px;
        }}
        table.dataTable tbody td {{
            padding: 0.42rem 0.55rem !important;
            border-bottom: 1px solid rgba(var(--line-rgb), 0.07) !important;
        }}
        table.dataTable tbody tr:hover {{
            background: linear-gradient(90deg, rgba(var(--primary-rgb), 0.12), rgba(var(--secondary-rgb), 0.06)) !important;
        }}
        .td-trend {{
            cursor: crosshair;
            text-decoration: underline;
            text-decoration-style: dotted;
            text-decoration-color: rgba(var(--primary-rgb), 0.42);
            text-underline-offset: 3px;
        }}
        .td-up, .td-down, .td-flat {{
            position: relative;
        }}
        .td-up::before, .td-down::before, .td-flat::before {{
            display: inline-block;
            margin-right: 0.25rem;
            font-size: 0.72rem;
            opacity: 0.9;
        }}
        .td-up::before {{ content: "▲"; }}
        .td-down::before {{ content: "▼"; }}
        .td-flat::before {{ content: "●"; font-size: 0.56rem; }}
        .trend-tooltip {{
            width: 380px !important;
            padding: 14px !important;
            border: 1px solid rgba(var(--primary-rgb), 0.42) !important;
            border-radius: 14px !important;
            background: color-mix(in srgb, var(--glass-bg-solid) 94%, transparent) !important;
            box-shadow: 0 24px 80px rgba(0,0,0,.38), 0 0 0 1px rgba(255,255,255,.04) inset !important;
            pointer-events: auto !important;
        }}
        .trend-tooltip-title {{ font-size: 0.86rem !important; }}
        .trend-tooltip-subtitle {{ font-size: 0.72rem !important; color: var(--text-muted) !important; }}
        .trend-tooltip-chart-container {{ height: 150px !important; }}
        .trend-tooltip-chart-container svg {{ overflow: visible; cursor: crosshair; }}
        .trend-chart-capture {{ cursor: crosshair; pointer-events: all; }}
        .trend-point-hit {{ cursor: crosshair; pointer-events: all; }}
        .trend-guide-line {{
            visibility: hidden;
            pointer-events: none;
            stroke: var(--primary);
            stroke-width: 1.2;
            stroke-dasharray: 3 4;
            opacity: 0.58;
        }}
        .trend-point-visible {{
            filter: drop-shadow(0 2px 5px rgba(0,0,0,.22));
            pointer-events: none;
        }}
        .trend-point-label {{
            display: none;
            position: absolute;
            z-index: 3;
            min-width: 108px;
            padding: 6px 8px;
            border: 1px solid rgba(var(--line-rgb), 0.18);
            border-radius: 8px;
            background: var(--glass-bg-solid);
            color: var(--text);
            box-shadow: 0 10px 28px rgba(0,0,0,.16);
            font-size: 0.72rem;
            line-height: 1.35;
            pointer-events: none;
        }}
        .trend-point-label b {{ color: var(--primary); font-weight: 800; }}
        .trend-tooltip-footer {{ display: grid !important; grid-template-columns: repeat(3, 1fr); gap: 6px; border-top: 0 !important; }}
        .trend-tooltip-footer span {{
            display: block;
            padding: 6px 8px;
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            background: rgba(var(--primary-rgb), 0.07);
            color: var(--text) !important;
        }}
        .trend-tooltip-footer b,
        .trend-tooltip-footer em {{
            display: block;
            font-style: normal;
            line-height: 1.35;
            white-space: nowrap;
        }}
        .trend-tooltip-footer em {{
            margin-top: 2px;
            color: var(--primary-light);
            font-weight: 800;
        }}
        /* theme-switcher overrides removed */
        .theme-btn-warm {{ background: linear-gradient(135deg, #fafffd, #18b7a1 58%, #2563eb) !important; }}
        .theme-btn-dark {{ background: linear-gradient(135deg, #0b1018, #22d3ee 58%, #a78bfa) !important; }}
        .theme-btn-light {{ background: linear-gradient(135deg, #ffffff, #248cff) !important; }}
        .theme-btn-eye {{ background: linear-gradient(135deg, #fffdf7, #9b894c 58%, #6ea38a) !important; }}
        .theme-btn-pink {{ background: linear-gradient(135deg, #fffafd, #ff7ab1 58%, #8b5cf6) !important; }}
        .theme-btn-anime {{ background: conic-gradient(from 210deg, #2f2830, #d98f5b, #8c6bb1, #b8875d, #4b3734, #ffd7a1, #2f2830) !important; }}
        .pv-popup, .comment-popup {{
            border: 1px solid rgba(var(--line-rgb), 0.18) !important;
            border-radius: 14px !important;
            background: color-mix(in srgb, var(--glass-bg-solid) 96%, transparent) !important;
            box-shadow: 0 24px 70px rgba(0,0,0,.34), 0 0 0 1px rgba(255,255,255,.04) inset !important;
            backdrop-filter: blur(18px) saturate(130%) !important;
            -webkit-backdrop-filter: blur(18px) saturate(130%) !important;
        }}
        .pv-popup {{ width: 620px !important; max-height: min(720px, calc(100vh - 32px)) !important; }}
        .comment-popup {{
            width: clamp(620px, 58vw, 900px) !important;
            height: min(720px, calc(100vh - 48px)) !important;
            max-height: min(720px, calc(100vh - 48px)) !important;
        }}
        .pv-head, .comment-head {{
            min-height: 46px !important;
            padding: 0.72rem 0.95rem !important;
            background: linear-gradient(90deg, rgba(var(--primary-rgb), 0.16), rgba(var(--secondary-rgb), 0.08)) !important;
            color: var(--text) !important;
            border-bottom: 1px solid rgba(var(--line-rgb), 0.12) !important;
        }}
        .pv-title, .comment-title {{
            color: var(--text) !important;
            font-size: 0.92rem !important;
            font-weight: 750 !important;
            letter-spacing: 0 !important;
            text-shadow: none !important;
        }}
        .pv-head-title, .comment-head-title {{
            color: var(--text) !important;
            font-size: 0.98rem !important;
            font-weight: 850 !important;
            letter-spacing: 0 !important;
            text-shadow: none !important;
        }}
        .pv-head-icon, .comment-head-icon {{
            background: rgba(var(--primary-rgb), 0.11) !important;
            color: var(--primary-dark) !important;
            box-shadow: none !important;
        }}
        .pv-actions a, .pv-actions span, .pv-actions button {{
            background: rgba(var(--primary-rgb), 0.08) !important;
            border: 1px solid rgba(var(--line-rgb), 0.14) !important;
            color: var(--text-secondary) !important;
            border-radius: 8px !important;
        }}
        .pv-body, .comment-body {{
            background: transparent !important;
            color: var(--text-secondary) !important;
            padding: 1rem 1.05rem !important;
        }}
        .comment-body {{
            max-height: min(600px, calc(100vh - 280px)) !important;
            overflow: auto !important;
        }}
        :root[data-theme="light"] .pv-head,
        :root[data-theme="light"] .comment-head {{
            background: linear-gradient(90deg, rgba(255, 255, 255, 0.96), rgba(232, 244, 255, 0.94)) !important;
            box-shadow: inset 4px 0 0 #006adc, inset 0 -1px 0 rgba(0, 83, 179, 0.12) !important;
        }}
        :root[data-theme="light"] .pv-head-icon,
        :root[data-theme="light"] .comment-head-icon {{
            background: #e7f1ff !important;
            color: #0053b3 !important;
        }}
        :root[data-theme="light"] .pv-head-title,
        :root[data-theme="light"] .comment-head-title {{
            color: #0b1220 !important;
        }}
        :root[data-theme="light"] .pv-title,
        :root[data-theme="light"] .comment-title {{
            color: #0b1220 !important;
            text-shadow: none !important;
        }}
        :root[data-theme="light"] .pv-actions a,
        :root[data-theme="light"] .pv-actions span,
        :root[data-theme="light"] .pv-actions button {{
            color: #1e293b !important;
        }}
        .pv-body {{
            font-size: 0.92rem !important;
            line-height: 1.78 !important;
        }}
        .pv-section-title {{
            margin: 1rem 0 0.45rem !important;
            padding-left: 0.65rem !important;
            border-left: 3px solid var(--primary) !important;
            color: var(--text) !important;
            background: transparent !important;
            font-size: 0.95rem !important;
        }}
        .pv-para {{
            margin: 0.45rem 0 !important;
            padding: 0 !important;
            background: transparent !important;
            border: 0 !important;
        }}
        .comment-floor {{
            margin: 0 0 0.65rem !important;
            padding: 0.78rem 0.85rem !important;
            border: 1px solid rgba(var(--line-rgb), 0.1) !important;
            border-radius: 10px !important;
            background: rgba(var(--primary-rgb), 0.045) !important;
        }}
        .comment-floor:last-child {{ margin-bottom: 0 !important; }}
        .comment-floor-head {{
            color: var(--text) !important;
            font-size: 0.8rem !important;
            margin-bottom: 0.38rem !important;
        }}
        .comment-floor-head .floor-num {{
            border-radius: 999px !important;
            background: rgba(var(--primary-rgb), 0.16) !important;
            color: var(--primary-light) !important;
        }}
        .comment-floor-text {{
            color: var(--text-secondary) !important;
            font-size: 0.9rem !important;
            line-height: 1.66 !important;
            font-weight: 450 !important;
        }}
        .comment-reply {{
            margin-left: 0.75rem !important;
            border-left: 2px solid rgba(var(--secondary-rgb), 0.45) !important;
            background: rgba(var(--secondary-rgb), 0.055) !important;
            border-radius: 8px !important;
        }}
        .comment-page-bar, .comment-tip {{
            background: rgba(var(--glass-tint-rgb), 0.16) !important;
            border-top: 1px solid rgba(var(--line-rgb), 0.1) !important;
        }}
        .mcmod-consent {{
            background: transparent !important;
        }}
        .mcmod-consent-panel {{
            background: rgba(var(--glass-tint-rgb), 0.85) !important;
        }}
        /* 最终毛玻璃统一增强：所有主题更透，同时保留文字底色与阴影 */
        :root,
        :root[data-theme] {{
            --radius: 12px;
            --radius-sm: 8px;
        }}
        :root[data-theme="light"],
        :root[data-theme="warm"],
        :root[data-theme="eye"],
        :root[data-theme="pink"] {{
            --glass-bg: rgba(var(--glass-tint-rgb), 0.34);
            --glass-bg-solid: rgba(var(--glass-tint-rgb), 0.58);
        }}
        :root[data-theme="dark"] {{
            --glass-bg: rgba(17, 24, 39, 0.34);
            --glass-bg-solid: rgba(20, 28, 42, 0.58);
        }}
        :root[data-theme="anime"] {{
            --glass-bg: rgba(54, 41, 45, 0.24);
            --glass-bg-solid: rgba(54, 41, 45, 0.54);
            --text: #fff4de;
            --text-secondary: #ecd6b8;
            --text-muted: rgba(236, 214, 184, 0.76);
        }}
        .stat-card, .filter-card, .table-card, .disclaimer-inner, .sort-hint-inner,
        .theme-switcher, .pv-popup, .comment-popup, .trend-tooltip {{
            background-color: transparent !important;
            border-radius: var(--radius) !important;
            backdrop-filter: blur(34px) saturate(190%) contrast(112%) !important;
            -webkit-backdrop-filter: blur(34px) saturate(190%) contrast(112%) !important;
            box-shadow:
                var(--shadow),
                inset 0 1px 0 rgba(255,255,255,0.24),
                inset 0 0 0 1px rgba(255,255,255,0.07) !important;
        }}
        .stat-card, .filter-card, .table-card, .disclaimer-inner, .sort-hint-inner {{
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), 0.24), rgba(var(--glass-tint2-rgb), 0.10)),
                linear-gradient(180deg, rgba(255,255,255,0.18), rgba(255,255,255,0.04)) !important;
        }}
        .pv-popup, .comment-popup, .trend-tooltip {{
            background: color-mix(in srgb, var(--glass-bg-solid) 58%, transparent) !important;
        }}
        table.dataTable tbody td,
        .filter-label, .stat-label, .hero-sub, .pv-body, .comment-body {{
            text-shadow: 0 1px 2px rgba(0,0,0,0.22);
        }}
        :root[data-theme="anime"] body,
        :root[data-theme="anime"] body *:not(input):not(select):not(option):not(textarea):not(svg):not(path),
        :root[data-theme="anime"] table.dataTable tbody td,
        :root[data-theme="anime"] .filter-label,
        :root[data-theme="anime"] .hero-sub,
        :root[data-theme="anime"] .pv-body,
        :root[data-theme="anime"] .comment-body,
        :root[data-theme="anime"] .comment-floor-text,
        :root[data-theme="anime"] .sort-hint-inner,
        :root[data-theme="anime"] .disclaimer-inner {{
            color: #fff4de !important;
            text-shadow:
                0 1px 1px rgba(30, 22, 24, 0.75),
                0 0 8px rgba(255, 215, 161, 0.26) !important;
        }}
        :root[data-theme="anime"] .hero-title,
        :root[data-theme="anime"] .stat-value,
        :root[data-theme="anime"] .modpack-link,
        :root[data-theme="anime"] table.dataTable thead th,
        :root[data-theme="anime"] .filter-label,
        :root[data-theme="anime"] .pv-title,
        :root[data-theme="anime"] .comment-title {{
            background: linear-gradient(90deg, #fff6df, #ffd7a1, #ffffff, #dbc6f0, #fff6df) !important;
            background-size: 180% 100% !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            color: transparent !important;
            -webkit-text-fill-color: transparent !important;
            text-shadow:
                0 0 2px rgba(255, 247, 223, 0.96),
                0 0 9px rgba(255, 215, 161, 0.46),
                0 2px 4px rgba(30, 22, 24, 0.62) !important;
            -webkit-text-stroke: 0.35px rgba(255, 247, 223, 0.52);
            animation: none;
        }}
        :root[data-theme="anime"] .hero-title,
        :root[data-theme="anime"] .stat-value {{
            filter: drop-shadow(0 0 5px rgba(255, 215, 161, 0.36));
        }}
        :root[data-theme="anime"] .stat-card,
        :root[data-theme="anime"] .filter-card,
        :root[data-theme="anime"] .table-card,
        :root[data-theme="anime"] .disclaimer-inner,
        :root[data-theme="anime"] .sort-hint-inner {{
            background:
                linear-gradient(135deg, rgba(54, 41, 45, 0.22), rgba(102, 71, 56, 0.12)),
                linear-gradient(180deg, rgba(255,255,255,0.16), rgba(255,255,255,0.03)) !important;
            border-color: rgba(255, 215, 161, 0.30) !important;
        }}
        :root[data-theme="anime"] .table-card {{
            background:
                linear-gradient(135deg, rgba(54, 41, 45, 0.20), rgba(102, 71, 56, 0.12)),
                linear-gradient(180deg, rgba(255,255,255,0.16), rgba(255,255,255,0.03)) !important;
        }}
        /* 流光主题终版：刻意脱离其它主题的“普通玻璃卡片”观感 */
        :root[data-theme="anime"] {{
            --primary: #ff2bd6;
            --primary-light: #79f7ff;
            --primary-dark: #a100ff;
            --secondary: #00ff9d;
            --secondary-light: #fff05a;
            --accent: #ff7a00;
            --success: #00ff9d;
            --danger: #ff2d55;
            --glass-bg: rgba(15, 8, 38, 0.24);
            --glass-bg-solid: rgba(22, 10, 54, 0.66);
            --glass-border: rgba(121, 247, 255, 0.36);
            --glass-hover: rgba(255, 43, 214, 0.16);
            --bg-main: #070313;
            --text: #fff8ff;
            --text-secondary: #dffcff;
            --text-muted: rgba(223, 252, 255, 0.72);
            --primary-rgb: 255, 43, 214;
            --primary-light-rgb: 121, 247, 255;
            --primary-dark-rgb: 161, 0, 255;
            --secondary-rgb: 0, 255, 157;
            --accent-rgb: 255, 122, 0;
            --line-rgb: 121, 247, 255;
            --shadow-rgb: 255, 43, 214;
            --glass-tint-rgb: 18, 9, 46;
            --glass-tint2-rgb: 55, 12, 86;
            --radius: 28px;
            --radius-sm: 18px;
            --th-bg-1: rgba(17, 9, 48, 0.76);
            --th-bg-2: rgba(67, 12, 92, 0.56);
            --th-sort-bg-1: rgba(255, 43, 214, 0.18);
            --th-sort-bg-2: rgba(0, 255, 157, 0.12);
            --th-sort-active-bg-1: rgba(255, 43, 214, 0.44);
            --th-sort-active-bg-2: rgba(121, 247, 255, 0.26);
        }}
        :root[data-theme="anime"] body {{
            background:
                radial-gradient(circle at 12% 10%, rgba(255, 43, 214, 0.42), transparent 26%),
                radial-gradient(circle at 88% 7%, rgba(0, 255, 157, 0.30), transparent 24%),
                radial-gradient(circle at 58% 92%, rgba(255, 122, 0, 0.34), transparent 32%),
                conic-gradient(from 210deg at 50% 45%, rgba(255, 43, 214, .26), rgba(121, 247, 255, .20), rgba(0,255,157,.18), rgba(255,240,90,.18), rgba(161,0,255,.24), rgba(255,43,214,.26)),
                #070313 !important;
            background-attachment: fixed !important;
        }}
        :root[data-theme="anime"] .bg-layer {{
            opacity: 1 !important;
            background:
                repeating-linear-gradient(100deg, rgba(255,255,255,.08) 0 1px, transparent 1px 18px),
                linear-gradient(115deg, transparent 0 20%, rgba(121,247,255,.24) 31%, transparent 42%, rgba(255,43,214,.22) 56%, transparent 70%),
                radial-gradient(circle at 20% 12%, rgba(255,255,255,.22), transparent 18%) !important;
            mix-blend-mode: screen;
        }}
        :root[data-theme="anime"] .bg-layer::after {{
            background:
                linear-gradient(96deg, transparent 0 12%, rgba(255, 43, 214, .42) 22%, rgba(121,247,255,.34) 34%, transparent 48%),
                linear-gradient(28deg, transparent 0 50%, rgba(0,255,157,.32) 62%, rgba(255,240,90,.22) 70%, transparent 86%) !important;
            filter: blur(18px) saturate(190%) !important;
            opacity: .9 !important;
        }}
        :root[data-theme="anime"] .hero {{
            background:
                linear-gradient(135deg, rgba(255,43,214,.22), rgba(121,247,255,.12) 45%, rgba(0,255,157,.10)),
                rgba(7, 3, 19, .38) !important;
            border-bottom: 1px solid rgba(121,247,255,.28) !important;
        }}
        :root[data-theme="anime"] .stat-card,
        :root[data-theme="anime"] .filter-card,
        :root[data-theme="anime"] .table-card,
        :root[data-theme="anime"] .disclaimer-inner,
        :root[data-theme="anime"] .sort-hint-inner {{
            border-radius: 28px !important;
            border: 1px solid rgba(121,247,255,.34) !important;
            background:
                linear-gradient(135deg, rgba(255,43,214,.20), rgba(121,247,255,.10) 34%, rgba(0,255,157,.09) 64%, rgba(255,122,0,.14)),
                rgba(10, 5, 28, .34) !important;
            box-shadow:
                0 24px 80px rgba(255,43,214,.26),
                0 0 42px rgba(121,247,255,.16),
                inset 0 1px 0 rgba(255,255,255,.32),
                inset 0 0 60px rgba(255,255,255,.06) !important;
            backdrop-filter: blur(42px) saturate(240%) contrast(122%) !important;
            -webkit-backdrop-filter: blur(42px) saturate(240%) contrast(122%) !important;
        }}
        :root[data-theme="anime"] .hero-title,
        :root[data-theme="anime"] .stat-value,
        :root[data-theme="anime"] .modpack-link,
        :root[data-theme="anime"] table.dataTable thead th,
        :root[data-theme="anime"] .filter-label {{
            background: linear-gradient(90deg, #fff, #79f7ff, #ff2bd6, #fff05a, #00ff9d, #fff) !important;
            background-size: 260% 100% !important;
            -webkit-background-clip: text !important;
            background-clip: text !important;
            color: transparent !important;
            -webkit-text-fill-color: transparent !important;
            text-shadow: 0 0 12px rgba(121,247,255,.35), 0 0 24px rgba(255,43,214,.24) !important;
            filter: drop-shadow(0 0 10px rgba(255,43,214,.20));
        }}
        :root[data-theme="anime"] .dataTables_scrollHead,
        :root[data-theme="anime"] .sort-strip {{
            background:
                linear-gradient(90deg, rgba(255,43,214,.30), rgba(121,247,255,.18), rgba(0,255,157,.18), rgba(255,122,0,.22)),
                rgba(7,3,19,.40) !important;
            border-color: rgba(121,247,255,.30) !important;
            box-shadow: 0 18px 54px rgba(255,43,214,.22), inset 0 1px 0 rgba(255,255,255,.28) !important;
        }}
        :root[data-theme="anime"] .header-sort-switcher,
        :root[data-theme="anime"] .filter-card .form-select,
        :root[data-theme="anime"] #searchScope,
        :root[data-theme="anime"] .dataTables_wrapper .dataTables_filter input,
        :root[data-theme="anime"] .select2-container--bootstrap-5 .select2-selection,
        :root[data-theme="anime"] .mod-details > summary {{
            border-color: rgba(121,247,255,.34) !important;
            background:
                linear-gradient(135deg, rgba(255,43,214,.18), rgba(121,247,255,.12), rgba(0,255,157,.08)),
                rgba(9, 4, 26, .42) !important;
            box-shadow: 0 10px 30px rgba(255,43,214,.14), inset 0 1px 0 rgba(255,255,255,.22) !important;
        }}
        :root[data-theme="anime"] .sort-option.active,
        :root[data-theme="anime"] .pagination .page-item.active .page-link,
        :root[data-theme="anime"] .dataTables_wrapper .dataTables_paginate .paginate_button.current {{
            background: linear-gradient(135deg, #ff2bd6, #a100ff 42%, #79f7ff) !important;
            box-shadow: 0 0 22px rgba(255,43,214,.46), 0 0 14px rgba(121,247,255,.32) !important;
        }}
        :root[data-theme="anime"] .tag-cat,
        :root[data-theme="anime"] .tag-pack,
        :root[data-theme="anime"] .tag-mod,
        :root[data-theme="anime"] .mod-summary-chip {{
            border-radius: 999px !important;
            border-color: rgba(121,247,255,.24) !important;
            background: linear-gradient(135deg, rgba(255,43,214,.18), rgba(121,247,255,.10), rgba(0,255,157,.10)) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.18), 0 5px 16px rgba(255,43,214,.10) !important;
        }}
        /* 最终控件重塑：筛选/搜索单选框与分页统一为圆润主题玻璃 */
        .filter-card {{
            border-radius: 30px !important;
            background:
                radial-gradient(circle at 18% 0%, rgba(var(--primary-rgb), .12), transparent 34%),
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .62), rgba(var(--glass-tint2-rgb), .30)),
                rgba(var(--glass-tint-rgb), .20) !important;
            border: 1px solid rgba(var(--primary-rgb), .20) !important;
            box-shadow: 0 22px 70px rgba(var(--shadow-rgb), .14), inset 0 1px 0 rgba(255,255,255,.24) !important;
            backdrop-filter: blur(46px) saturate(190%) contrast(112%) !important;
            -webkit-backdrop-filter: blur(46px) saturate(190%) contrast(112%) !important;
        }}
        .filter-col-type {{
            flex-basis: 190px !important;
            min-width: 190px !important;
        }}
        .filter-label {{
            font-size: .82rem !important;
            margin-bottom: .5rem !important;
            color: var(--text-secondary) !important;
            text-shadow: 0 1px 2px rgba(0,0,0,.16);
        }}
        .select2-container--bootstrap-5 .select2-selection.select2-glass-selection,
        .select2-container--bootstrap-5 .select2-selection.select2-glass-selection.select2-selection--single {{
            min-height: 54px !important;
            border-radius: 999px !important;
            padding: 0 42px 0 18px !important;
            background:
                linear-gradient(180deg, rgba(255,255,255,.30), rgba(255,255,255,.08)),
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .78), rgba(var(--glass-tint2-rgb), .46)) !important;
            border: 2px solid rgba(var(--primary-rgb), .26) !important;
            box-shadow:
                0 12px 30px rgba(var(--shadow-rgb), .12),
                inset 0 1px 0 rgba(255,255,255,.34),
                inset 0 -10px 24px rgba(var(--primary-rgb), .04) !important;
            backdrop-filter: blur(28px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
        }}
        .select2-container--bootstrap-5.select2-container--open .select2-selection.select2-glass-selection,
        .select2-container--bootstrap-5.select2-container--focus .select2-selection.select2-glass-selection {{
            border-color: rgba(var(--primary-rgb), .52) !important;
            box-shadow:
                0 0 0 5px rgba(var(--primary-rgb), .13),
                0 18px 44px rgba(var(--shadow-rgb), .18),
                inset 0 1px 0 rgba(255,255,255,.38) !important;
        }}
        .select2-container--bootstrap-5 .select2-selection.select2-glass-selection .select2-selection__rendered {{
            line-height: 52px !important;
            padding-left: 0 !important;
            color: var(--text) !important;
            font-size: 1rem !important;
            font-weight: 900 !important;
        }}
        .select2-container--bootstrap-5 .select2-selection.select2-glass-selection .select2-selection__arrow {{
            width: 38px !important;
            height: 52px !important;
            right: 8px !important;
        }}
        .select2-container--bootstrap-5 .select2-selection.select2-glass-selection .select2-selection__arrow b {{
            border-color: var(--primary) transparent transparent transparent !important;
            border-width: 6px 5px 0 5px !important;
            filter: drop-shadow(0 2px 4px rgba(var(--primary-rgb), .22));
        }}
        .select2-container--bootstrap-5.select2-container--open .select2-selection.select2-glass-selection .select2-selection__arrow b {{
            border-color: transparent transparent var(--primary) transparent !important;
            border-width: 0 5px 6px 5px !important;
        }}
        .select2-dropdown.select2-glass-dropdown {{
            margin-top: 8px;
            border-radius: 26px !important;
            border: 1px solid rgba(var(--primary-rgb), .24) !important;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .88), rgba(var(--glass-tint2-rgb), .68)),
                rgba(var(--glass-tint-rgb), .82) !important;
            box-shadow: 0 28px 74px rgba(var(--shadow-rgb), .22), inset 0 1px 0 rgba(255,255,255,.25) !important;
            backdrop-filter: blur(34px) saturate(190%) !important;
            -webkit-backdrop-filter: blur(34px) saturate(190%) !important;
            overflow: hidden;
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__options {{
            max-height: 360px !important;
            padding: 8px !important;
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__options::-webkit-scrollbar {{
            width: 12px;
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__options::-webkit-scrollbar-thumb {{
            border: 3px solid transparent;
            border-radius: 999px;
            background: linear-gradient(180deg, var(--primary), var(--secondary)) border-box;
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__option {{
            border-radius: 16px !important;
            padding: 11px 14px !important;
            margin: 2px 0 !important;
            font-size: 1rem !important;
            font-weight: 850 !important;
            color: var(--text) !important;
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__option--highlighted {{
            background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
            color: #fff !important;
            box-shadow: 0 8px 22px rgba(var(--primary-rgb), .22);
        }}
        .select2-dropdown.select2-glass-dropdown .select2-results__option--selected {{
            background: rgba(var(--primary-rgb), .14) !important;
            color: var(--text) !important;
        }}
        .dataTables_wrapper .dataTables_filter > label {{
            border-radius: 999px !important;
            padding: 8px !important;
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .52), rgba(var(--glass-tint2-rgb), .22)),
                rgba(var(--glass-tint-rgb), .18) !important;
            border: 1px solid rgba(var(--primary-rgb), .16) !important;
            backdrop-filter: blur(30px) saturate(170%) !important;
            -webkit-backdrop-filter: blur(30px) saturate(170%) !important;
        }}
        .dataTables_wrapper .dataTables_filter input {{
            height: 54px !important;
            min-width: 280px !important;
            border-radius: 999px !important;
            padding: 0 18px !important;
            font-size: .96rem !important;
            font-weight: 800 !important;
        }}
        /* DataTables 分页样式已统一收敛至后方专用样式区 */

        .mod-container {{
            height: 100%;
            width: 100%;
            padding-right: 4px !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            overscroll-behavior: contain;
            scrollbar-gutter: stable;
        }}
        .td-mods {{
            height: 100%;
            min-width: 0;
        }}
        .td-mods .tag-wrap {{
            min-width: 100% !important;
        }}
        .mod-details {{
            width: 100%;
            min-height: 72px;
        }}
        .mod-details:not([open]) {{
            max-height: 84px;
            overflow: hidden;
        }}
        .mod-details:not([open]) .mod-details-body {{
            display: none !important;
        }}
        .mod-details[open] {{
            max-height: min(520px, 66vh);
            overflow: hidden;
        }}
        .mod-details[open] .mod-details-body {{
            max-height: calc(min(520px, 66vh) - 92px);
            overflow-y: auto;
            overflow-x: hidden;
            overscroll-behavior: contain;
            padding-right: 6px;
            scrollbar-width: thin;
            scrollbar-color: rgba(var(--primary-rgb), .35) transparent;
        }}
        .mod-details[open] .mod-details-body::-webkit-scrollbar {{
            width: 7px;
        }}
        .mod-details[open] .mod-details-body::-webkit-scrollbar-thumb {{
            background: rgba(var(--primary-rgb), .35);
            border-radius: 999px;
        }}
        .mod-details > summary {{
            min-height: 72px !important;
            height: auto;
            width: 100%;
            grid-template-columns: minmax(86px, auto) minmax(0, 1fr) 34px !important;
            gap: 12px !important;
            padding: 10px 12px !important;
            border-radius: 18px !important;
            background:
                radial-gradient(circle at 8% 20%, rgba(var(--primary-rgb), .18), transparent 34%),
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .66), rgba(var(--glass-tint2-rgb), .32)),
                rgba(var(--primary-rgb), .05) !important;
            border: 1px solid rgba(var(--primary-rgb), .24) !important;
            box-shadow:
                0 12px 30px rgba(var(--shadow-rgb), .10),
                inset 0 1px 0 rgba(255,255,255,.22),
                inset 0 -14px 30px rgba(var(--primary-rgb), .035) !important;
            backdrop-filter: blur(22px) saturate(165%) !important;
            -webkit-backdrop-filter: blur(22px) saturate(165%) !important;
        }}
        .mod-summary-main {{
            display: inline-flex !important;
            flex-direction: column;
            align-items: flex-start;
            gap: 3px;
            line-height: 1.05;
            font-size: .76rem !important;
            color: var(--text-secondary) !important;
        }}
        .mod-summary-main b {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 40px;
            padding: 2px 8px;
            border-radius: 999px;
            color: #fff !important;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 8px 18px rgba(var(--primary-rgb), .20);
            font-size: .82rem;
        }}
        .mod-summary-cats {{
            width: 100%;
            max-height: none !important;
            display: flex !important;
            flex-wrap: wrap;
            align-items: center;
            justify-content: flex-start !important;
            gap: 5px;
            overflow: visible !important;
        }}
        .mod-details:not([open]) .mod-summary-cats {{
            mask-image: none;
            -webkit-mask-image: none;
        }}
        .mod-details[open] .mod-summary-cats {{
            max-height: none !important;
            mask-image: none;
            -webkit-mask-image: none;
        }}
        .mod-summary-chip {{
            padding: 3px 8px !important;
            border-radius: 999px !important;
            font-size: .72rem !important;
            background: rgba(var(--primary-rgb), .10) !important;
            border: 1px solid rgba(var(--primary-rgb), .18) !important;
        }}
        .mod-details > summary::after {{
            width: 34px !important;
            height: 34px !important;
            border-radius: 14px !important;
            background: linear-gradient(135deg, rgba(var(--primary-rgb), .18), rgba(var(--secondary-rgb), .12)) !important;
            color: var(--primary) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.22);
        }}
        .filter-card-compact {{
            padding: 0.85rem !important;
        }}
        .filter-card-compact .filter-row {{
            display: grid !important;
            grid-template-columns: minmax(160px, .72fr) repeat(4, minmax(180px, 1fr)) minmax(160px, .72fr) auto;
            gap: 0.7rem !important;
            align-items: start !important;
        }}
        .filter-card-compact .filter-col,
        .filter-card-compact .filter-col-type {{
            min-width: 0 !important;
            flex: none !important;
        }}
        .filter-card-compact .filter-label {{
            display: inline-flex;
            align-items: center;
            min-height: 18px;
            margin-bottom: 0.26rem !important;
            font-size: .72rem !important;
            opacity: .9;
        }}
        .filter-card-compact .filter-tools {{
            min-height: 18px !important;
            margin-top: .22rem !important;
            justify-content: flex-start !important;
        }}
        .filter-card-compact .exclude-toggle {{
            padding: .08rem .46rem !important;
            font-size: .66rem !important;
        }}
        .filter-card-compact .select2-container--bootstrap-5 .select2-selection {{
            min-height: 36px !important;
        }}
        .filter-card-compact .select2-container--bootstrap-5 .select2-selection.select2-glass-selection,
        .filter-card-compact .select2-container--bootstrap-5 .select2-selection.select2-glass-selection.select2-selection--single {{
            min-height: 42px !important;
        }}
        .filter-card-compact .select2-container--bootstrap-5 .select2-selection.select2-glass-selection .select2-selection__rendered {{
            line-height: 40px !important;
            font-size: .88rem !important;
        }}
        .filter-card-compact .select2-container--bootstrap-5 .select2-selection.select2-glass-selection .select2-selection__arrow {{
            height: 40px !important;
        }}
        .filter-card-compact .hover-mode-panel {{
            margin-top: .65rem;
            padding-top: .65rem;
            border-top: 1px solid rgba(var(--line-rgb), .12);
        }}
        @media (max-width: 1600px) {{
            .filter-card-compact .filter-row {{
                grid-template-columns: repeat(3, minmax(180px, 1fr));
            }}
        }}
        @media (max-width: 900px) {{
            .filter-card-compact .filter-row {{
                grid-template-columns: 1fr;
            }}
        }}
        .td-title {{
            padding-left: 0.75rem !important;
            padding-right: 42px !important;
        }}
        table.dataTable tbody td.td-title {{
            padding-left: 0.75rem !important;
            padding-right: 42px !important;
        }}
        table.dataTable tbody td.td-title.has-cover {{
            padding-right: 122px !important;
        }}
        .fav-star {{
            position: absolute;
            right: 10px;
            top: 9px;
            transform: none;
            width: 28px;
            height: 28px;
            border-radius: 999px;
            border: 1px solid rgba(var(--primary-rgb), .18);
            background: rgba(var(--glass-tint-rgb), .38);
            color: var(--text-muted);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: .94rem;
            line-height: 1;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.14);
            transition: transform .16s ease, color .16s ease, background .16s ease, box-shadow .16s ease;
            z-index: 8;
        }}
        .fav-star:hover {{
            transform: scale(1.08);
            color: var(--primary);
            background: rgba(var(--primary-rgb), .12);
        }}
        .fav-star.active {{
            color: #fff;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-color: rgba(var(--primary-rgb), .42);
            box-shadow: 0 8px 22px rgba(var(--primary-rgb), .24), inset 0 1px 0 rgba(255,255,255,.24);
        }}
        .compare-tray {{
            position: fixed;
            left: 50%;
            bottom: 18px;
            top: auto;
            right: auto;
            transform: translateX(-50%) translateY(120%);
            z-index: 2147483000;
            width: min(860px, calc(100vw - 28px));
            min-height: 76px;
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 14px;
            align-items: center;
            padding: 12px 14px 12px 16px;
            border-radius: 24px;
            border: 1px solid rgba(var(--primary-rgb), .24);
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .76), rgba(var(--glass-tint2-rgb), .38)),
                rgba(var(--glass-tint-rgb), .32);
            box-shadow: 0 24px 70px rgba(var(--shadow-rgb), .22), inset 0 1px 0 rgba(255,255,255,.25);
            backdrop-filter: blur(34px) saturate(190%);
            -webkit-backdrop-filter: blur(34px) saturate(190%);
            opacity: 0;
            pointer-events: none;
            transition: transform .28s ease, opacity .22s ease;
            overflow: hidden;
        }}
        .compare-tray.show {{
            transform: translateX(-50%) translateY(0);
            opacity: 1;
            pointer-events: auto;
        }}
        .compare-tray-glow {{
            position: absolute;
            inset: -40% auto auto -8%;
            width: 260px;
            height: 160px;
            background: radial-gradient(circle, rgba(var(--primary-rgb), .24), transparent 68%);
            pointer-events: none;
        }}
        .compare-tray-main, .compare-tray-actions {{
            position: relative;
            z-index: 1;
        }}
        .compare-tray-kicker, .compare-kicker {{
            display: block;
            color: var(--primary);
            font-size: .68rem;
            font-weight: 950;
            letter-spacing: .04em;
            text-transform: uppercase;
        }}
        .compare-tray-main strong {{
            display: block;
            color: var(--text);
            font-size: 1rem;
            margin: 1px 0 5px;
        }}
        .compare-tray-names {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            max-height: 28px;
            overflow: hidden;
        }}
        .compare-mini-chip {{
            padding: 3px 8px;
            border-radius: 999px;
            background: rgba(var(--primary-rgb), .10);
            border: 1px solid rgba(var(--primary-rgb), .16);
            color: var(--text-secondary);
            font-size: .72rem;
            font-weight: 800;
        }}
        .compare-tray-actions {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .compare-primary-btn, .compare-ghost-btn, .compare-close-btn {{
            border: 0;
            border-radius: 999px;
            padding: 10px 14px;
            font-weight: 950;
            cursor: pointer;
            color: var(--text);
        }}
        .compare-primary-btn {{
            color: #fff;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 12px 28px rgba(var(--primary-rgb), .28);
        }}
        .compare-ghost-btn {{
            background: rgba(var(--glass-tint-rgb), .40);
            border: 1px solid rgba(var(--line-rgb), .14);
            color: var(--text-secondary);
        }}
        .compare-close-btn {{
            width: 42px;
            height: 42px;
            padding: 0;
            background: rgba(var(--glass-tint-rgb), .42);
            border: 1px solid rgba(var(--line-rgb), .14);
        }}
        .compare-overlay {{
            position: fixed;
            inset: 0;
            z-index: 2147483001;
            display: none;
            padding: 22px;
            background:
                radial-gradient(circle at 18% 0%, rgba(var(--primary-rgb), .18), transparent 34%),
                rgba(5, 8, 16, .42);
            backdrop-filter: blur(28px) saturate(170%);
            -webkit-backdrop-filter: blur(28px) saturate(170%);
        }}
        .compare-overlay.show {{
            display: block;
        }}
        .compare-shell {{
            height: calc(100vh - 44px);
            border-radius: 28px;
            border: 1px solid rgba(var(--primary-rgb), .24);
            background:
                linear-gradient(135deg, rgba(var(--glass-tint-rgb), .74), rgba(var(--glass-tint2-rgb), .34)),
                rgba(var(--glass-tint-rgb), .24);
            box-shadow: 0 30px 110px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.24);
            backdrop-filter: blur(42px) saturate(190%);
            -webkit-backdrop-filter: blur(42px) saturate(190%);
            display: grid;
            grid-template-rows: auto minmax(0, 1fr);
            overflow: hidden;
        }}
        .compare-head {{
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: center;
            padding: 18px 20px;
            border-bottom: 1px solid rgba(var(--line-rgb), .12);
        }}
        .compare-head h2 {{
            margin: 3px 0 0;
            color: var(--text);
            font-size: clamp(1.2rem, 2vw, 1.8rem);
            letter-spacing: 0;
        }}
        .compare-head-actions {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .compare-body {{
            overflow: auto;
            padding: 18px;
        }}
        .compare-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin-bottom: 14px;
        }}
        .compare-card, .compare-section {{
            border-radius: 18px;
            border: 1px solid rgba(var(--line-rgb), .13);
            background: rgba(var(--glass-tint-rgb), .30);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.12);
        }}
        .compare-card {{
            padding: 12px;
        }}
        .compare-card h3 {{
            margin: 0 0 8px;
            color: var(--text);
            font-size: .98rem;
        }}
        .compare-metric {{
            display: grid;
            grid-template-columns: 90px minmax(0, 1fr);
            gap: 8px;
            font-size: .78rem;
            color: var(--text-secondary);
            margin: 4px 0;
        }}
        .compare-metric b {{
            color: var(--primary);
            font-family: 'JetBrains Mono', monospace;
        }}
        .compare-section {{
            padding: 14px;
            margin: 12px 0;
        }}
        .compare-section h3 {{
            margin: 0 0 10px;
            font-size: 1rem;
            color: var(--text);
        }}
        .compare-chip-cloud {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .compare-chip {{
            border-radius: 999px;
            padding: 4px 9px;
            background: rgba(var(--primary-rgb), .10);
            border: 1px solid rgba(var(--primary-rgb), .15);
            color: var(--text-secondary);
            font-size: .76rem;
            font-weight: 800;
        }}
        .compare-columns {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 12px;
        }}
        .compare-table-wrap {{
            overflow: auto;
            border-radius: 16px;
            border: 1px solid rgba(var(--line-rgb), .12);
        }}
        .compare-table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 720px;
            font-size: .8rem;
        }}
        .compare-table th,
        .compare-table td {{
            padding: 8px 10px;
            border-bottom: 1px solid rgba(var(--line-rgb), .10);
            text-align: left;
            color: var(--text-secondary);
        }}
        .compare-table th {{
            position: sticky;
            top: 0;
            z-index: 1;
            background: rgba(var(--glass-tint-rgb), .78);
            color: var(--text);
            backdrop-filter: blur(18px);
        }}
        .compare-hit {{
            color: var(--primary);
            font-weight: 950;
        }}
        .compare-miss {{
            color: var(--text-muted);
            opacity: .55;
        }}
        .top-action-btn {{
            display: inline-flex;
            align-items: center;
            gap: 3px;
            background: var(--surface, rgba(255,255,255,0.08));
            border: 1px solid var(--border, rgba(255,255,255,0.15));
            color: var(--text, #e2e8f0);
            padding: 3px 7px;
            border-radius: 7px;
            font-size: 0.72rem;
            font-weight: 650;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.18s ease;
        }}
        .top-action-btn:hover, .top-action-btn.active {{
            background: var(--primary, #3b82f6);
            color: #fff;
            border-color: var(--primary, #3b82f6);
            box-shadow: 0 2px 10px rgba(59, 130, 246, 0.35);
        }}
        body.hide-tag-counts .s-chip-count,
        body.hide-tag-counts .tag-count,
        body.hide-tag-counts .chip-count,
        body.hide-tag-counts .picker-option b,
        body.hide-tag-counts .cat-count {{
            display: none !important;
        }}
        .cross-item-actions {{
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 6px;
        }}
        .cross-action-btn {{
            font-size: 0.72rem;
            padding: 2px 7px;
            border-radius: 6px;
            border: 1px solid var(--border-color, rgba(255,255,255,0.15));
            background: var(--btn-bg, rgba(255,255,255,0.06));
            color: var(--text, #fff);
            text-decoration: none;
            cursor: pointer;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 3px;
            line-height: 1.2;
        }}
        .cross-action-btn:hover {{
            background: var(--primary, #3b82f6);
            color: #fff;
            border-color: var(--primary, #3b82f6);
        }}
        .cross-btn-ext {{
            color: var(--text-muted, #94a3b8);
        }}
        .cross-btn-ext:hover {{
            color: #fff;
            background: rgba(16, 185, 129, 0.85);
            border-color: #10b981;
        }}
        .audit-modal-overlay {{
            position: fixed;
            inset: 0;
            z-index: 100000;
            display: none;
            align-items: center;
            justify-content: center;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(8px);
            padding: 20px;
        }}
        .audit-modal-overlay.show {{ display: flex; }}
        .audit-filter-chip {{
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.78rem;
            border: 1px solid var(--border, rgba(255,255,255,0.15));
            background: var(--surface, rgba(255,255,255,0.05));
            color: var(--text-muted, #94a3b8);
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .audit-filter-chip.active {{
            background: var(--primary, #3b82f6);
            color: #fff;
            border-color: var(--primary, #3b82f6);
        }}
        .audit-item-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            border-radius: 10px;
            background: var(--surface, rgba(255,255,255,0.04));
            border: 1px solid var(--border, rgba(255,255,255,0.08));
            gap: 12px;
            transition: all 0.15s ease;
        }}
        .audit-item-row:hover {{
            background: var(--surface-hover, rgba(255,255,255,0.08));
            border-color: var(--primary, #3b82f6);
        }}
        .feedback-fab {{ position: fixed; right: 18px; bottom: 18px; z-index: 99990; width: 34px; height: 34px; border-radius: 50%; padding: 0; display: flex; align-items: center; justify-content: center; background: var(--surface, #1e293b); border: 1px solid var(--border, #334155); box-shadow: 0 4px 14px rgba(0,0,0,0.25); color: var(--text-muted, #94a3b8); font-size: 15px; cursor: pointer; opacity: 0.65; transition: all 0.2s ease; }}
        .feedback-fab:hover {{ opacity: 1; transform: scale(1.12); border-color: var(--primary); color: var(--primary); }}
        .feedback-modal {{ position: fixed; inset: 0; z-index: 100000; display: none; align-items: center; justify-content: center; background: rgba(16,37,51,.42); padding: 18px; }}
        .feedback-modal.show {{ display: flex; }}
        .feedback-panel {{ width: min(480px, 100%); padding: 22px; border-radius: 18px; background: var(--glass-bg-solid); border: 1px solid var(--glass-border); box-shadow: 0 24px 70px rgba(var(--shadow-rgb), .32); }}
        .feedback-panel h3 {{ margin: 0 0 14px; }}
        .feedback-panel label {{ display:block; margin: 12px 0 5px; font-weight: 700; }}
        .feedback-panel select, .feedback-panel textarea, .feedback-panel input {{ width:100%; box-sizing:border-box; border:1px solid var(--glass-border); border-radius:9px; padding:9px 10px; background:rgba(255,255,255,.78); color:#183041; font:inherit; }}
        .feedback-panel textarea {{ min-height:120px; resize:vertical; }}
        .feedback-actions {{ display:flex; justify-content:flex-end; gap:8px; margin-top:15px; }}
        .feedback-actions button {{ border:0; border-radius:9px; padding:9px 14px; cursor:pointer; font-weight:700; }}
        #feedbackSubmit {{ background:var(--primary); color:#fff; }}
        #feedbackStatus {{ min-height:18px; margin-top:10px; font-size:.82rem; color:var(--text-secondary); }}
    
        /* 原生现代系统字体栈优化：0延迟、无外网依赖、全平台丝滑渲染 */
        body, button, input, select, textarea, .dataTables_wrapper, .modpack-title-cn {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", sans-serif !important;
        }}
        /* 移除或降低非必要的表格内部单元格 backdrop-filter blur 计算，大幅提升 GPU 滚动帧率 */
        .td-title, .td-trend, .td-votes, .td-engage, .td-tags, .td-mods, .tag-mod, .tag-cat, .tag-pack {{
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
        }}
        /* 保留顶部栏、模态框、悬停卡片的毛玻璃质感 */
        .dashboard-header, .search-container, .preview-card, .desc-popup-card, .comment-popup-card, .compare-tray {{
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
        }}

    
.copy-toast.show {{
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}}


/* ═══════════ 多页面/平台切换导航 ═══════════ */
.platform-tabs-nav {{
    display: inline-flex;
    gap: 10px;
    padding: 6px;
    background: rgba(var(--glass-tint-rgb), 0.2);
    border: 1px solid rgba(var(--line-rgb), 0.15);
    border-radius: 16px;
    backdrop-filter: blur(10px);
    margin-top: 14px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}}
.plat-tab-btn {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 18px;
    border-radius: 12px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    user-select: none;
}}
.plat-tab-btn:hover {{
    color: var(--text);
    background: rgba(var(--glass-tint-rgb), 0.25);
}}
.plat-tab-btn.active {{
    background: var(--primary);
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(var(--primary-rgb), 0.4);
}}
.plat-tab-btn.plat-bili.active {{
    background: #fb7299 !important;
    box-shadow: 0 4px 14px rgba(251, 114, 153, 0.45);
}}
.plat-tab-count {{
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.22);
}}
.plat-tab-btn:not(.active) .plat-tab-count {{
    background: rgba(var(--glass-tint-rgb), 0.18);
    color: var(--text-secondary);
}}

/* ═══════════ B站专属视图容器 ═══════════ */
.bili-view-wrap {{
    width: 100%;
    max-width: 1600px;
    margin: 0 auto;
    padding: 0 1.5rem 3rem;
}}
.bili-filter-card {{
    background: var(--glass-bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    backdrop-filter: blur(12px);
    box-shadow: var(--shadow);
    margin-bottom: 1.5rem;
}}
.bili-filter-row {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px;
}}
.bili-search-box {{
    flex: 1 1 260px;
    position: relative;
}}
.bili-search-input {{
    width: 100%;
    padding: 9px 16px 9px 38px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: rgba(var(--glass-tint-rgb), 0.15);
    color: var(--text);
    font-size: 0.9rem;
    outline: none;
    transition: all 0.2s;
}}
.bili-search-input:focus {{
    border-color: #fb7299;
    box-shadow: 0 0 0 3px rgba(251, 114, 153, 0.2);
    background: rgba(var(--glass-tint-rgb), 0.3);
}}
.bili-search-icon {{
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    pointer-events: none;
}}
.bili-select {{
    padding: 8px 14px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: var(--glass-bg);
    color: var(--text);
    font-size: 0.88rem;
    font-weight: 500;
    outline: none;
    cursor: pointer;
}}
.bili-chips-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
    align-items: center;
}}
.bili-chip-label {{
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-muted);
    margin-right: 4px;
}}
.bili-chip {{
    padding: 4px 12px;
    border-radius: 20px;
    border: 1px solid var(--border);
    background: rgba(var(--glass-tint-rgb), 0.1);
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    user-select: none;
}}
.bili-chip:hover {{
    border-color: #fb7299;
    color: #fb7299;
}}
.bili-chip.active {{
    background: #fb7299;
    border-color: #fb7299;
    color: #fff !important;
}}

/* ═══════════ B站整合包卡片网格 ═══════════ */
.bili-cards-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 1.25rem;
}}
.bili-pack-card {{
    background: var(--glass-bg);
    border: 1px solid var(--border);
    border-radius: 18px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    transition: transform 0.22s, box-shadow 0.22s, border-color 0.22s;
}}
.bili-pack-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.14);
    border-color: rgba(251, 114, 153, 0.4);
}}
.bili-card-cover {{
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #111;
    overflow: hidden;
}}
.bili-card-img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
}}
.bili-pack-card:hover .bili-card-img {{
    transform: scale(1.04);
}}
.bili-card-dur {{
    position: absolute;
    right: 8px;
    bottom: 8px;
    padding: 2px 6px;
    background: rgba(0, 0, 0, 0.75);
    color: #fff;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 4px;
    backdrop-filter: blur(4px);
}}
.bili-card-stats {{
    position: absolute;
    left: 8px;
    bottom: 8px;
    display: flex;
    gap: 10px;
    padding: 2px 8px;
    background: rgba(0, 0, 0, 0.65);
    color: #fff;
    font-size: 0.75rem;
    border-radius: 4px;
    backdrop-filter: blur(4px);
}}
.bili-card-body {{
    padding: 1rem 1.15rem;
    display: flex;
    flex-direction: column;
    flex: 1;
}}
.bili-card-title {{
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.45;
    color: var(--text);
    margin-bottom: 0.5rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-decoration: none;
}}
.bili-card-title:hover {{
    color: #fb7299;
}}
.bili-card-meta {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 0.75rem;
}}
.bili-author-tag {{
    font-weight: 600;
    color: var(--text-secondary);
}}
.bili-card-tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 0.85rem;
}}
.bili-badge-ver {{
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid rgba(16, 185, 129, 0.3);
}}
.bili-badge-loader {{
    background: rgba(14, 165, 233, 0.15);
    color: #0ea5e9;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid rgba(14, 165, 233, 0.3);
}}
.bili-badge-cat {{
    background: rgba(var(--glass-tint-rgb), 0.1);
    color: var(--text-secondary);
    font-size: 0.72rem;
    font-weight: 500;
    padding: 2px 7px;
    border-radius: 6px;
    border: 1px solid var(--border);
}}
.bili-download-zone {{
    margin-top: auto;
    background: rgba(var(--glass-tint-rgb), 0.1);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem 0.85rem;
}}
.bili-dl-header {{
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text-muted);
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.bili-dl-btns {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 6px;
}}
.bili-dl-btn {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s;
}}
.bili-dl-btn-quark {{
    background: rgba(255, 122, 0, 0.15);
    color: #ff7a00;
    border: 1px solid rgba(255, 122, 0, 0.3);
}}
.bili-dl-btn-quark:hover {{
    background: #ff7a00;
    color: #fff;
}}
.bili-dl-btn-baidu {{
    background: rgba(33, 115, 255, 0.15);
    color: #2173ff;
    border: 1px solid rgba(33, 115, 255, 0.3);
}}
.bili-dl-btn-baidu:hover {{
    background: #2173ff;
    color: #fff;
}}
.bili-dl-btn-lanzou {{
    background: rgba(6, 182, 212, 0.15);
    color: #06b6d4;
    border: 1px solid rgba(6, 182, 212, 0.3);
}}
.bili-dl-btn-lanzou:hover {{
    background: #06b6d4;
    color: #fff;
}}
.bili-dl-btn-pan123 {{
    background: rgba(139, 92, 246, 0.15);
    color: #8b5cf6;
    border: 1px solid rgba(139, 92, 246, 0.3);
}}
.bili-dl-btn-pan123:hover {{
    background: #8b5cf6;
    color: #fff;
}}
.bili-dl-btn-other {{
    background: rgba(var(--glass-tint-rgb), 0.15);
    color: var(--text);
    border: 1px solid var(--border);
}}
.bili-dl-btn-other:hover {{
    background: var(--primary);
    color: #fff;
}}
.bili-copy-pill {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    background: rgba(var(--glass-tint-rgb), 0.15);
    border: 1px dashed var(--border);
    color: var(--text-secondary);
    cursor: pointer;
    user-select: none;
    transition: all 0.2s;
    margin-right: 6px;
    margin-top: 4px;
}}
.bili-copy-pill:hover {{
    background: rgba(251, 114, 153, 0.15);
    border-color: #fb7299;
    color: #fb7299;
}}
.bili-desc-collapse {{
    margin-top: 0.6rem;
    font-size: 0.78rem;
    color: var(--text-muted);
}}
.bili-desc-summary {{
    cursor: pointer;
    user-select: none;
    font-weight: 600;
}}
.bili-desc-full {{
    margin-top: 6px;
    padding: 8px 10px;
    background: rgba(0,0,0,0.1);
    border-radius: 8px;
    max-height: 140px;
    overflow-y: auto;
    font-size: 0.75rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-all;
}}

/* 复制成功气泡 Toast */
.copy-toast {{
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: rgba(16, 185, 129, 0.9);
    color: #fff;
    padding: 8px 18px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    opacity: 0;
    transition: all 0.25s ease;
    pointer-events: none;
    z-index: 999999;
}}
.copy-toast.show {{
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}}


/* ═══════════ 聚合模式开关与版本折叠 ═══════════ */
.bili-mode-toggle {{
    display: inline-flex;
    padding: 3px;
    background: rgba(var(--glass-tint-rgb), 0.15);
    border: 1px solid var(--border);
    border-radius: 12px;
    gap: 4px;
}}
.bili-mode-btn {{
    padding: 5px 12px;
    border-radius: 9px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    user-select: none;
}}
.bili-mode-btn:hover {{
    color: var(--text);
    background: rgba(var(--glass-tint-rgb), 0.2);
}}
.bili-mode-btn.active {{
    background: #fb7299;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(251, 114, 153, 0.4);
}}

.bili-multi-badge {{
    position: absolute;
    top: 8px;
    left: 8px;
    padding: 3px 9px;
    background: linear-gradient(135deg, rgba(251, 114, 153, 0.92), rgba(236, 72, 153, 0.95));
    color: #fff;
    font-size: 0.72rem;
    font-weight: 700;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(251, 114, 153, 0.4);
    backdrop-filter: blur(6px);
    z-index: 2;
    letter-spacing: 0.3px;
}}

.bili-versions-collapse {{
    margin-top: 0.65rem;
    background: rgba(var(--glass-tint-rgb), 0.12);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
}}
.bili-versions-summary {{
    padding: 6px 10px;
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text);
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    user-select: none;
    background: rgba(var(--glass-tint-rgb), 0.08);
}}
.bili-versions-summary:hover {{
    background: rgba(251, 114, 153, 0.12);
    color: #fb7299;
}}
.bili-versions-list {{
    padding: 6px 8px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    max-height: 180px;
    overflow-y: auto;
}}
.bili-version-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 8px;
    border-radius: 6px;
    background: rgba(0,0,0,0.06);
    text-decoration: none;
    font-size: 0.75rem;
    color: var(--text-secondary);
    transition: all 0.18s;
}}
.bili-version-item:hover {{
    background: rgba(251, 114, 153, 0.15);
    color: #fb7299;
    transform: translateX(3px);
}}
.bili-ver-date {{
    font-weight: 700;
    color: var(--text-muted);
    font-size: 0.72rem;
    min-width: 42px;
}}
.bili-ver-author {{
    font-weight: 600;
    color: var(--text-secondary);
    min-width: 70px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.bili-ver-title {{
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.bili-ver-views {{
    color: var(--text-muted);
    font-size: 0.72rem;
    white-space: nowrap;
}}
.bili-ver-badge-top {{
    font-size: 0.68rem;
    padding: 1px 5px;
    border-radius: 4px;
    background: rgba(251, 114, 153, 0.2);
    color: #fb7299;
    font-weight: 700;
}}


/* ═════════════════ 现代设计系统 (Linear + Modrinth 顶级设计规范) ═════════════════ */
:root {{
    --bg: #f8fafc;
    --surface: #ffffff;
    --surface-glass: rgba(255, 255, 255, 0.88);
    --surface-hover: #f1f5f9;
    --text: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --line: rgba(0, 0, 0, 0.07);
    --border: rgba(0, 0, 0, 0.08);
    --accent: #4f46e5;
    --accent-light: #6366f1;
    --soft: #f1f5f9;
    --hero: #eef2ff;
    --radius-sm: 8px;
    --radius: 14px;
    --radius-lg: 18px;
    --shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05), 0 1px 3px rgba(15, 23, 42, 0.02);
    --shadow-hover: 0 16px 36px -4px rgba(15, 23, 42, 0.10), 0 2px 6px rgba(15, 23, 42, 0.04);
    --primary: #4f46e5;
    --primary-rgb: 79, 70, 229;
    --primary-light: #6366f1;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --baidu: #3b5bdb;
    --quark: #0f766e;
    --lanzou: #0284c7;
    --pan123: #7c3aed;
    --color-all: #6366f1;
    --color-mcmod: #f59e0b;
    --color-bilibili: #f43f5e;
    --color-bbsmc: #0284c7;
    --color-xyebbs: #10b981;
    --color-modrinth: #00af5c;
    --color-curseforge: #ea580c;
    --sidebar-w: 240px;
    color-scheme: light;
}}

:root[data-theme="dark"] {{
    --bg: #090d16;
    --surface: #111726;
    --surface-glass: rgba(17, 23, 38, 0.90);
    --surface-hover: #192236;
    --text: #f9fafb;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --line: rgba(255, 255, 255, 0.08);
    --border: rgba(255, 255, 255, 0.09);
    --accent: #6366f1;
    --accent-light: #818cf8;
    --soft: #161e30;
    --hero: #101624;
    --shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    --shadow-hover: 0 20px 45px rgba(0, 0, 0, 0.55), 0 0 24px rgba(99, 102, 241, 0.15);
    --primary: #6366f1;
    --primary-rgb: 99, 102, 241;
    --primary-light: #818cf8;
    color-scheme: dark;
}}

:root[data-theme="eye"] {{
    --bg: #f2f7f4;
    --surface: #ffffff;
    --surface-glass: rgba(255, 255, 255, 0.92);
    --surface-hover: #e8f3ec;
    --text: #132318;
    --text-secondary: #304838;
    --text-muted: #587563;
    --line: #d1e2d6;
    --border: #d1e2d6;
    --accent: #2d6a4f;
    --accent-light: #40916c;
    --soft: #e5f1e8;
    --hero: #e6f0e9;
    --primary: #2d6a4f;
    --primary-rgb: 45, 106, 79;
    --primary-light: #52b788;
    color-scheme: light;
}}

:root[data-theme="warm"] {{
    --bg: #faf6ef;
    --surface: #ffffff;
    --surface-glass: rgba(255, 255, 255, 0.92);
    --surface-hover: #f5ede1;
    --text: #261e14;
    --text-secondary: #54412e;
    --text-muted: #826e55;
    --line: #e6d7c3;
    --border: #e6d7c3;
    --accent: #d97706;
    --accent-light: #f59e0b;
    --soft: #f7ebdb;
    --hero: #f8eee0;
    --primary: #d97706;
    --primary-rgb: 217, 119, 6;
    --primary-light: #f59e0b;
    color-scheme: light;
}}

:root[data-theme="light"] {{
    --bg: #f8fafc;
    --surface: #ffffff;
    --surface-glass: rgba(255, 255, 255, 0.90);
    --surface-hover: #f1f5f9;
    --text: #0f172a;
    --text-secondary: #334155;
    --text-muted: #64748b;
    --line: #e2e8f0;
    --border: #e2e8f0;
    --accent: #0284c7;
    --accent-light: #38bdf8;
    --soft: #f0f9ff;
    --hero: #e0f2fe;
    --primary: #0284c7;
    --primary-rgb: 2, 132, 199;
    --primary-light: #38bdf8;
    color-scheme: light;
}}

:root[data-theme="pink"] {{
    --bg: #fff1f5;
    --surface: #ffffff;
    --surface-glass: rgba(255, 255, 255, 0.90);
    --surface-hover: #fee2e8;
    --text: #361724;
    --text-secondary: #633246;
    --text-muted: #966b80;
    --line: #fad2df;
    --border: #fad2df;
    --accent: #e11d48;
    --accent-light: #fb7185;
    --soft: #ffe4ed;
    --hero: #ffe9f1;
    --primary: #e11d48;
    --primary-rgb: 225, 29, 72;
    --primary-light: #fb7185;
    color-scheme: light;
}}

/* ═════════════════ 主体 App 布局 (Sidebar + Main Content) ═════════════════ */
body {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Roboto, sans-serif !important;
    letter-spacing: -0.01em;
    margin: 0;
    padding: 0;
}}

.app-layout {{
    display: block;
    width: 100%;
    min-height: 100vh;
}}

/* 彻底移除左侧边栏，视线 100% 居中聚集 */
.sidebar {{
    display: none !important;
}}

/* 黄金居中主容器 (1560px 宽屏视野，左右优雅对称) */
.main-content {{
    margin-left: 0 !important;
    max-width: 1560px !important;
    margin: 0 auto !important;
    padding: 20px 24px 60px !important;
    width: 100% !important;
    box-sizing: border-box !important;
}}

/* 顶栏样式在下方全局统一维护 */

/* ═════════ 现代分层中央控制台 (Multi-Tier Central Control Hub) ═════════ */
.central-hub {{
    background: var(--surface-glass);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 16px 22px;
    margin-bottom: 22px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.03);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
}}

/* 第一层：搜索与平台核心动作 */
.hub-tier-search {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    flex-wrap: wrap;
    margin-bottom: 14px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(var(--primary-rgb), 0.12);
}}
.hub-stat-badge {{
    font-size: 13px;
    font-weight: 750;
    color: var(--text-secondary);
    display: inline-flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}}
.hub-stat-badge strong {{
    color: var(--primary);
    font-size: 16px;
    font-weight: 850;
}}
.hub-search-box {{
    flex: 1;
    min-width: 280px;
    max-width: 650px;
    position: relative;
}}
.hub-search-input {{
    width: 100%;
    padding: 9px 38px 9px 38px;
    border-radius: 999px;
    border: 1.5px solid rgba(var(--primary-rgb), 0.25);
    background: rgba(var(--glass-tint-rgb, 120, 120, 120), 0.06);
    color: var(--text);
    font-size: 0.9rem;
    font-weight: 600;
    outline: none;
    transition: all 0.2s;
    box-sizing: border-box;
}}
.hub-search-input:focus {{
    border-color: var(--primary);
    background: var(--surface);
    box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.16);
}}
.hub-search-icon {{
    position: absolute;
    left: 13px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 14px;
    pointer-events: none;
}}
.hub-clear-btn {{
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(128,128,128,0.22);
    border: none;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    font-size: 10px;
    line-height: 18px;
    text-align: center;
    color: var(--text);
    cursor: pointer;
    transition: background 0.15s;
}}
.hub-clear-btn:hover {{
    background: var(--primary);
    color: #fff;
}}
.hub-actions-cluster {{
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}}
.hub-select {{
    height: 36px;
    min-height: 36px;
    border-radius: 12px;
    padding: 0 30px 0 13px;
    border: 1px solid var(--line);
    background-color: var(--surface);
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 10px center;
    background-size: 11px;
    color: var(--text);
    font-size: 12.5px;
    font-weight: 600;
    outline: none;
    cursor: pointer;
    transition: all 0.18s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    box-sizing: border-box;
}}
.hub-select:hover {{
    border-color: var(--primary);
    background-color: var(--soft);
}}
.hub-select:focus {{
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.15);
}}
.hub-reset-btn {{
    height: 36px;
    padding: 0 14px;
    border-radius: 12px;
    border: 1px solid var(--line);
    background: var(--soft);
    color: var(--text-secondary);
    font-size: 12.5px;
    font-weight: 650;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    transition: all 0.16s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    box-sizing: border-box;
}}
.hub-reset-btn:hover {{
    border-color: var(--danger);
    color: var(--danger);
    background: rgba(239, 68, 68, 0.08);
}}

/* 第二层与第三层：胶囊流式布局 (Flow Filter Rows) */
.hub-tier-filters {{
    display: flex;
    flex-direction: column;
    gap: 12px;
}}
.hub-filter-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    position: relative;
    min-height: 32px;
}}
.hub-filter-label {{
    font-size: 13px;
    font-weight: 750;
    color: var(--text-secondary);
    white-space: nowrap;
    width: 92px;
    min-width: 92px;
    height: 32px;
    line-height: 32px;
    padding: 0;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
}}
/* 默认只显示一行，自适应当前容器宽度，超出部分隐藏且不折行 */
.hub-chips-wrap {{
    display: flex;
    flex-wrap: nowrap;
    overflow: hidden;
    height: 32px;
    max-height: 32px;
    gap: 6px;
    align-items: center;
    flex: 1;
    min-width: 0;
}}
.hub-chips-wrap .s-chip {{
    flex-shrink: 0;
}}
.discovery-actions {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
    margin-left: auto;
    height: 32px;
}}
.discovery-btn {{
    height: 28px;
    padding: 0 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 650;
    background: var(--surface);
    border: 1px solid var(--line);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
    display: inline-flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}}
.discovery-btn:hover {{
    background: var(--soft);
    color: var(--primary);
    border-color: var(--primary);
    transform: translateY(-1px);
}}
.discovery-btn-primary {{
    background: var(--soft);
    color: var(--primary);
    border-color: rgba(var(--primary-rgb), 0.35);
}}
.discovery-btn-primary:hover {{
    background: var(--primary);
    color: #ffffff;
    border-color: var(--primary);
    box-shadow: 0 2px 8px rgba(var(--primary-rgb), 0.25);
}}

/* 展开状态：换行并作为独立滚轮面板展开 */
.hub-chips-wrap.expanded-chips {{
    display: flex;
    flex-wrap: wrap;
    flex-basis: 100%;
    width: 100%;
    height: auto;
    max-height: 240px;
    overflow-y: auto;
    padding: 10px 12px;
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--surface-glass, var(--surface));
    align-content: flex-start;
    scrollbar-width: thin;
    margin-top: 8px;
    order: 3;
}}
.hub-chips-wrap.expanded-chips .s-chip {{
    flex-shrink: initial;
}}
.hub-filter-row:has(.expanded-chips),
.hub-filter-row.row-expanded {{
    flex-wrap: wrap;
    align-items: center;
}}
.hub-filter-row:has(.expanded-chips) .hub-filter-label,
.hub-filter-row.row-expanded .hub-filter-label {{
    order: 1;
}}
.hub-filter-row:has(.expanded-chips) .discovery-actions,
.hub-filter-row.row-expanded .discovery-actions {{
    order: 2;
    margin-left: auto;
}}

/* 已激活筛选胶囊栏 (Active Filters Strip) */
.active-filters-bar {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    margin-top: 4px;
    border-radius: 12px;
    background: var(--soft);
    border: 1.5px dashed rgba(var(--primary-rgb, 46, 117, 89), 0.35);
    animation: modPillFadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}}
.active-filter-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px 3px 12px;
    border-radius: 999px;
    background: var(--surface);
    border: 1px solid rgba(var(--primary-rgb, 46, 117, 89), 0.4);
    color: var(--primary);
    font-size: 0.78rem;
    font-weight: 650;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    cursor: pointer;
    transition: all 0.15s ease;
}}
.active-filter-badge:hover {{
    background: var(--primary);
    color: #ffffff;
    border-color: var(--primary);
}}
.active-filter-badge .badge-del {{
    font-size: 13px;
    font-weight: bold;
    margin-left: 2px;
    line-height: 1;
}}
.active-filters-clear-all {{
    margin-left: auto;
    font-size: 11.5px;
    font-weight: 600;
    color: var(--text-secondary);
    background: none;
    border: none;
    cursor: pointer;
    text-decoration: underline;
    padding: 2px 6px;
}}
.active-filters-clear-all:hover {{
    color: var(--danger, #ef4444);
}}

/* 模态弹窗组件 (Picker Modal Dialog) */
dialog.picker-modal {{
    position: fixed !important;
    inset: 0 !important;
    margin: auto !important;
    max-width: min(860px, 92vw) !important;
    max-height: min(80vh, 720px) !important;
    width: 100% !important;
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 22px 26px;
    background: var(--surface);
    color: var(--text);
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    z-index: 99999;
    box-sizing: border-box;
}}
dialog.picker-modal::backdrop {{
    background: rgba(15, 23, 42, 0.55);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
}}
.picker-modal-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}}
.picker-modal-eyebrow {{
    font-size: 11px;
    font-weight: 750;
    letter-spacing: 1px;
    color: var(--primary);
    text-transform: uppercase;
}}
.picker-close-btn {{
    background: var(--soft);
    color: var(--primary);
    border: 1px solid var(--line);
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
}}
.picker-close-btn:hover {{
    background: var(--primary);
    color: #ffffff;
}}
.picker-toolbar {{
    padding: 6px 0 12px;
}}
.picker-toolbar input {{
    width: 100%;
    padding: 11px 16px;
    background: var(--surface);
    border: 1.5px solid var(--line);
    border-radius: 12px;
    color: var(--text);
    font: inherit;
    font-size: 13.5px;
    box-sizing: border-box;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}}
.picker-toolbar input:focus {{
    border-color: var(--primary);
    box-shadow: 0 0 0 3px var(--soft);
    outline: none;
}}
.picker-toolbar p {{
    margin: 8px 2px 0;
    font-size: 12px;
    color: var(--text-secondary);
}}
.picker-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
    gap: 8px;
    max-height: 50dvh;
    overflow-y: auto;
    margin: 8px 0 16px;
    padding: 4px 6px 4px 2px;
    align-content: start;
    scrollbar-width: thin;
}}
.picker-option {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    min-height: 40px;
    padding: 8px 12px;
    text-align: left;
    border: 1px solid var(--line);
    border-radius: 10px;
    background: var(--surface);
    color: var(--text);
    font: inherit;
    font-size: 12px;
    cursor: pointer;
    overflow-wrap: anywhere;
    transition: all 0.15s ease;
}}
.picker-option > b {{
    flex-shrink: 0;
    padding: 2px 6px;
    border-radius: 6px;
    background: var(--soft);
    color: var(--primary);
    font-size: 11px;
}}
.picker-option:hover {{
    border-color: var(--primary);
    background: var(--soft);
}}
.picker-option.active {{
    background: var(--soft);
    border-color: var(--primary);
    color: var(--primary);
    font-weight: 700;
    box-shadow: inset 3px 0 var(--primary);
}}
.picker-footer {{
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    border-top: 1px solid var(--line);
    padding-top: 14px;
}}
.picker-footer > span {{
    margin-right: auto;
    color: var(--text-secondary);
    font-size: 12px;
}}
.picker-footer button {{
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
}}
.picker-clear-btn {{
    background: transparent;
    border: 1px solid var(--line);
    color: var(--text-secondary);
}}
.picker-clear-btn:hover {{
    border-color: var(--primary);
    color: var(--primary);
}}
.picker-done-btn {{
    background: var(--primary);
    border: 1px solid var(--primary);
    color: #ffffff;
}}
.picker-done-btn:hover {{
    filter: brightness(1.1);
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
}}
@keyframes modPillFadeIn {{
    from {{ opacity: 0; transform: scale(0.92); }}
    to {{ opacity: 1; transform: scale(1); }}
}}
.s-chip {{
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    background: var(--soft);
    color: var(--text-secondary);
    border: 1px solid var(--line);
    cursor: pointer;
    transition: all 0.15s ease;
    user-select: none;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
}}
.s-chip:hover {{
    border-color: var(--primary);
    color: var(--primary);
    background: rgba(var(--primary-rgb), 0.08);
    transform: translateY(-1px);
}}
.s-chip.active {{
    background: var(--primary) !important;
    border-color: var(--primary) !important;
    color: #ffffff !important;
    font-weight: 750;
    box-shadow: 0 3px 10px rgba(var(--primary-rgb), 0.28);
}}
.s-chip-count {{
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 99px;
    background: rgba(var(--glass-tint-rgb, 120, 120, 120), 0.16);
    color: var(--text-muted);
}}
.s-chip.active .s-chip-count {{
    background: rgba(255, 255, 255, 0.25);
    color: #ffffff;
}}

/* 第四层：高阶参数栏 (Advanced Settings Strip) */
.hub-tier-advanced {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px dashed rgba(var(--primary-rgb), 0.15);
    flex-wrap: wrap;
    font-size: 12px;
}}
.hub-adv-group {{
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}}
.hub-exclude-toggle {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    cursor: pointer;
    font-weight: 700;
    color: var(--text-secondary);
    padding: 3px 8px;
    border-radius: 6px;
    background: var(--soft);
    border: 1px solid var(--line);
    transition: all 0.15s;
}}
.hub-exclude-toggle input {{
    accent-color: var(--danger);
}}
.hub-hover-switches {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
}}


.brand {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 8px 18px;
    border-bottom: 1px solid var(--line);
    margin-bottom: 16px;
}}
.brand-icon {{
    font-size: 26px;
    line-height: 1;
}}
.brand-title {{
    font-size: 16px;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.3px;
}}
.brand-sub {{
    font-size: 10px;
    color: var(--text-muted);
    font-weight: 600;
    letter-spacing: 0.5px;
}}

.nav-section-title {{
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--text-muted);
    padding: 10px 8px 6px;
    letter-spacing: 0.6px;
}}

.sidebar-nav {{
    display: flex;
    flex-direction: column;
    gap: 6px;
}}

.nav-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    font-size: 13.5px;
    font-weight: 600;
    color: var(--text-secondary);
    background: transparent;
    border: none;
    cursor: pointer;
    text-align: left;
    transition: all 0.18s ease;
    width: 100%;
}}
.nav-item:hover {{
    color: var(--text);
    background: var(--soft);
}}
.nav-item.active {{
    color: #ffffff !important;
    background: var(--accent) !important;
    box-shadow: 0 4px 12px color-mix(in srgb, var(--accent) 40%, transparent);
}}
.nav-item.active .nav-badge {{
    background: rgba(255, 255, 255, 0.25);
    color: #ffffff;
}}

.nav-icon {{
    font-size: 17px;
}}
.nav-text {{
    flex: 1;
}}
.nav-badge {{
    font-size: 11px;
    padding: 2px 7px;
    border-radius: 99px;
    background: var(--soft);
    color: var(--text-muted);
    font-weight: 700;
}}

.sidebar-line {{
    height: 1px;
    background: var(--line);
    margin: 14px 4px;
}}

.sidebar-tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 4px;
}}
.s-tag {{
    padding: 4px 9px;
    border-radius: 7px;
    font-size: 11.5px;
    font-weight: 500;
    background: var(--soft);
    color: var(--text-secondary);
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.15s;
}}
.s-tag:hover {{
    border-color: var(--accent);
    color: var(--accent);
    background: #ffffff;
}}

.sidebar-bottom {{
    margin-top: auto;
    padding-top: 14px;
    border-top: 1px solid var(--line);
}}

.theme-switch-row {{
    display: flex;
    gap: 8px;
    padding: 6px 8px;
    align-items: center;
    justify-content: space-between;
}}
.theme-dot {{
    width: 28px;
    height: 28px;
    border-radius: 50%;
    border: 2px solid transparent;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    background: var(--soft);
    transition: transform 0.2s, border-color 0.2s;
}}
.theme-dot:hover {{
    transform: scale(1.15);
}}
.theme-dot.active {{
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--bg);
}}

.offline-status {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--text-muted);
    padding: 10px 8px 4px;
}}
.status-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--success);
    box-shadow: 0 0 8px var(--success);
}}

/* 右侧主内容区域 */
.main-content {{
    margin-left: var(--sidebar-w);
    flex: 1;
    min-width: 0;
    padding: 0 28px 40px;
}}

/* 顶栏样式在下方全局统一维护 */

.breadcrumb {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
}}
.crumb-root {{
    color: var(--text-muted);
    font-weight: 500;
}}
.crumb-sep {{
    color: var(--line);
}}
.breadcrumb strong {{
    color: var(--text);
    font-weight: 700;
}}
.breadcrumb .muted {{
    color: var(--text-muted);
    font-size: 12px;
}}

.mobile-menu-btn {{
    display: none;
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: var(--text);
    padding: 4px 8px;
    margin-right: 8px;
}}

.top-actions {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.view-mode-toggle {{
    display: inline-flex;
    background: var(--soft);
    padding: 3px;
    border-radius: 9px;
    border: 1px solid var(--line);
}}
.vmode-btn {{
    padding: 5px 12px;
    border-radius: 7px;
    border: none;
    background: transparent;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.18s;
}}
.vmode-btn.active {{
    background: #ffffff;
    color: var(--text);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}}
:root[data-theme="dark"] .vmode-btn.active {{
    background: var(--surface);
    color: var(--accent-light);
}}

/* ═════════════════ 全宽沉浸式顶级导航条 (Modrinth/Steam 现代规范) ═════════════════ */
.topbar {{
    position: sticky !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    height: 54px !important;
    z-index: 1000 !important;
    margin: 0 !important;
    padding: 0 !important;
    border-radius: 0 !important;
    background: var(--surface-glass) !important;
    backdrop-filter: blur(24px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
    border-bottom: 1px solid var(--line) !important;
    box-shadow: 0 2px 14px -2px rgba(0, 0, 0, 0.04) !important;
    display: flex !important;
    align-items: center !important;
}}
:root[data-theme="dark"] .topbar {{
    background: rgba(13, 17, 26, 0.90) !important;
    border-bottom-color: rgba(255, 255, 255, 0.09) !important;
    box-shadow: 0 4px 28px -2px rgba(0, 0, 0, 0.5) !important;
}}
:root[data-theme="eye"] .topbar {{
    background: rgba(242, 247, 244, 0.94) !important;
    border-bottom-color: rgba(16, 185, 129, 0.16) !important;
}}
:root[data-theme="warm"] .topbar {{
    background: rgba(250, 246, 239, 0.94) !important;
    border-bottom-color: rgba(217, 119, 6, 0.16) !important;
}}
:root[data-theme="pink"] .topbar {{
    background: rgba(255, 241, 245, 0.94) !important;
    border-bottom-color: rgba(244, 114, 182, 0.18) !important;
}}

.topbar-inner {{
    max-width: 1560px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 0 24px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    height: 100% !important;
    box-sizing: border-box !important;
    gap: 16px !important;
}}

/* 左侧品牌区 (自然收缩，不抢占中轴空间) */
.topbar-left {{
    flex: 0 0 auto !important;
    display: flex !important;
    align-items: center !important;
}}
.topbar-brand {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 7px !important;
    cursor: pointer !important;
    text-decoration: none !important;
    user-select: none !important;
    padding: 4px 0 !important;
    transition: opacity 0.15s ease !important;
    flex-shrink: 0 !important;
}}
.topbar-brand:hover {{
    opacity: 0.85 !important;
}}
.brand-cube {{
    font-size: 19px !important;
    line-height: 1 !important;
    filter: drop-shadow(0 2px 6px rgba(99, 102, 241, 0.35)) !important;
}}
.brand-title {{
    font-size: 13.5px !important;
    font-weight: 800 !important;
    letter-spacing: -0.01em !important;
    color: var(--text) !important;
    white-space: nowrap !important;
}}
.brand-badge {{
    font-size: 9px !important;
    font-weight: 800 !important;
    padding: 1.5px 5px !important;
    border-radius: 4px !important;
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #ffffff !important;
    line-height: 1 !important;
    letter-spacing: 0.04em !important;
}}

/* 中间平台胶囊导航 (左右均分剩余空间，居中对齐，绝不压迫两侧) */
.topbar-center {{
    flex: 1 1 auto !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    min-width: 0 !important;
}}
.topbar-platform-nav {{
    display: inline-flex !important;
    align-items: center !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.04) !important;
    border: 1px solid var(--line) !important;
    border-radius: 9px !important;
    padding: 2.5px 3px !important;
    gap: 2.5px !important;
    flex-wrap: nowrap !important;
    box-sizing: border-box !important;
    flex-shrink: 0 !important;
}}
:root[data-theme="dark"] .topbar-platform-nav {{
    background: rgba(255, 255, 255, 0.04) !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
}}

.top-plat-btn {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 3.5px !important;
    padding: 4.5px 7.5px !important;
    height: 31px !important;
    border-radius: 7px !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: var(--text-secondary) !important;
    font-size: 11.5px !important;
    font-weight: 650 !important;
    line-height: 1 !important;
    cursor: pointer !important;
    transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1) !important;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
    box-sizing: border-box !important;
}}
.top-plat-btn:hover {{
    color: var(--text) !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.05) !important;
    transform: translateY(-1px) !important;
}}
:root[data-theme="dark"] .top-plat-btn:hover {{
    background: rgba(255, 255, 255, 0.08) !important;
    color: #f1f5f9 !important;
}}

.top-plat-btn.active {{
    color: #ffffff !important;
    font-weight: 700 !important;
    border-color: transparent !important;
    transform: none !important;
}}
.top-plat-btn[data-tab="all"].active {{
    background: linear-gradient(135deg, #4f46e5, #4338ca) !important;
    box-shadow: 0 3px 10px rgba(79, 70, 229, 0.35) !important;
}}
.top-plat-btn[data-tab="mcmod"].active {{
    background: linear-gradient(135deg, #d97706, #b45309) !important;
    box-shadow: 0 3px 10px rgba(217, 119, 6, 0.35) !important;
}}
.top-plat-btn[data-tab="bilibili"].active {{
    background: linear-gradient(135deg, #fb7299, #e11d48) !important;
    box-shadow: 0 3px 10px rgba(251, 114, 153, 0.35) !important;
}}
.top-plat-btn[data-tab="bbsmc"].active {{
    background: linear-gradient(135deg, #0284c7, #0369a1) !important;
    box-shadow: 0 3px 10px rgba(2, 132, 199, 0.35) !important;
}}
.top-plat-btn[data-tab="xyebbs"].active {{
    background: linear-gradient(135deg, #059669, #047857) !important;
    box-shadow: 0 3px 10px rgba(5, 150, 105, 0.35) !important;
}}
.top-plat-btn[data-tab="modrinth"].active {{
    background: linear-gradient(135deg, #10b981, #059669) !important;
    box-shadow: 0 3px 10px rgba(16, 185, 129, 0.35) !important;
}}
.top-plat-btn[data-tab="curseforge"].active {{
    background: linear-gradient(135deg, #ea580c, #c2410c) !important;
    box-shadow: 0 3px 10px rgba(234, 88, 12, 0.35) !important;
}}

.top-plat-btn .pnav-badge {{
    font-size: 9.5px !important;
    font-weight: 700 !important;
    padding: 1px 4px !important;
    border-radius: 4.5px !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.07) !important;
    color: var(--text-muted) !important;
    line-height: 1 !important;
    margin-left: 2px !important;
}}
:root[data-theme="dark"] .top-plat-btn .pnav-badge {{
    background: rgba(255, 255, 255, 0.12) !important;
    color: #94a3b8 !important;
}}
.top-plat-btn.active .pnav-badge {{
    background: rgba(255, 255, 255, 0.28) !important;
    color: #ffffff !important;
}}

/* 右侧工具区 (靠右对齐，紧凑精致) */
.topbar-actions {{
    flex: 0 0 auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-end !important;
    gap: 6px !important;
    margin-left: auto !important;
}}
.top-action-btn {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 3.5px !important;
    background: var(--surface, #ffffff) !important;
    border: 1px solid var(--line) !important;
    color: var(--text-secondary) !important;
    padding: 0 8px !important;
    border-radius: 7px !important;
    font-size: 11.5px !important;
    font-weight: 650 !important;
    white-space: nowrap !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    height: 31px !important;
    box-sizing: border-box !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    flex-shrink: 0 !important;
}}
:root[data-theme="dark"] .top-action-btn {{
    background: rgba(255, 255, 255, 0.05) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
    color: #cbd5e1 !important;
}}
.top-action-btn:hover {{
    color: var(--text) !important;
    background: var(--soft, rgba(0, 0, 0, 0.03)) !important;
    border-color: var(--primary-light) !important;
    transform: translateY(-1px) !important;
}}

.top-theme-pills {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 1.5px !important;
    background: var(--surface, #ffffff) !important;
    padding: 2px 3.5px !important;
    border-radius: 7px !important;
    border: 1px solid var(--line) !important;
    height: 31px !important;
    box-sizing: border-box !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    flex-shrink: 0 !important;
}}
:root[data-theme="dark"] .top-theme-pills {{
    background: rgba(255, 255, 255, 0.05) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
}}
.top-tdot {{
    border: none !important;
    background: transparent !important;
    font-size: 11.5px !important;
    line-height: 1 !important;
    cursor: pointer !important;
    padding: 2.5px !important;
    border-radius: 4px !important;
    transition: transform 0.15s, opacity 0.15s, background 0.15s !important;
    opacity: 0.65 !important;
}}
.top-tdot:hover, .top-tdot.active {{
    opacity: 1 !important;
    transform: scale(1.18) !important;
}}
.top-tdot.active {{
    background: rgba(var(--text-rgb, 0, 0, 0), 0.08) !important;
}}

/* 宽屏超大分辨率 (>= 1600px) */
@media (min-width: 1600px) {{
    .top-plat-btn {{
        padding: 5px 9px !important;
        font-size: 12px !important;
        gap: 4px !important;
    }}
    .top-plat-btn .pnav-badge {{
        font-size: 10px !important;
        padding: 1px 4.5px !important;
    }}
}}

/* 中屏自适应 (1281px - 1440px) */
@media (max-width: 1440px) {{
    .topbar-inner {{
        padding: 0 16px !important;
        gap: 10px !important;
    }}
    .top-plat-btn {{
        padding: 4px 6px !important;
        font-size: 11px !important;
        gap: 2.5px !important;
    }}
    .top-plat-btn .pnav-badge {{
        font-size: 9px !important;
        padding: 1px 3.5px !important;
    }}
    .topbar-platform-nav {{
        gap: 2px !important;
        padding: 2px !important;
    }}
    .top-action-btn {{
        padding: 0 6.5px !important;
        font-size: 11px !important;
    }}
}}

/* 紧凑小屏自适应 (<= 1280px) */
@media (max-width: 1280px) {{
    .topbar-inner {{
        padding: 0 12px !important;
        gap: 8px !important;
    }}
    .brand-title {{
        display: none !important;
    }}
    .top-plat-btn {{
        padding: 3.5px 5px !important;
        font-size: 10.5px !important;
        gap: 2px !important;
    }}
    .top-plat-btn .pnav-badge {{
        font-size: 8.5px !important;
        padding: 1px 3px !important;
    }}
    .topbar-platform-nav {{
        gap: 1.5px !important;
        padding: 1.5px !important;
    }}
    .top-action-btn {{
        padding: 0 5.5px !important;
        font-size: 10.5px !important;
    }}
}}
/* ═════════════════ MC百科专属搜索条 ═════════════════ */
.mcmod-search-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(var(--line-rgb), 0.15);
}}
.mcmod-search-box {{
    flex: 1;
    position: relative;
    max-width: 720px;
}}
.mcmod-search-icon {{
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 15px;
    pointer-events: none;
}}
.mcmod-search-input {{
    width: 100%;
    padding: 10px 38px 10px 40px;
    border-radius: 14px;
    border: 1px solid rgba(var(--primary-rgb), 0.25);
    background: rgba(var(--glass-tint-rgb), 0.22);
    color: var(--text);
    font-size: 0.92rem;
    font-weight: 600;
    outline: none;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.03);
}}
.mcmod-search-input:focus {{
    border-color: var(--primary);
    background: rgba(var(--glass-tint-rgb), 0.45);
    box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.18), 0 8px 24px rgba(0, 0, 0, 0.06);
}}
.mcmod-search-clear-btn {{
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(128,128,128, 0.25);
    border: none;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    font-size: 11px;
    line-height: 20px;
    text-align: center;
    color: var(--text);
    cursor: pointer;
    padding: 0;
}}
.mcmod-search-clear-btn:hover {{
    background: var(--primary);
    color: #fff;
}}
.mcmod-search-feedback {{
    display: flex;
    align-items: center;
    gap: 8px;
}}
.mcmod-count-pill {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.82rem;
    color: var(--text-secondary);
    background: rgba(var(--primary-rgb), 0.08);
    border: 1px solid rgba(var(--primary-rgb), 0.18);
    padding: 5px 12px;
    border-radius: 999px;
    font-weight: 600;
}}
.mcmod-count-pill strong {{
    color: var(--primary);
    font-weight: 850;
}}

/* ═════════════════ 响应式弹性自适应筛选栅格 ═════════════════ */
.filter-grid-layout {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 12px 14px;
    align-items: end;
}}
.filter-grid-layout .filter-col-wide {{
    grid-column: span 2;
    min-width: 280px;
}}
@media (max-width: 1200px) {{
    .filter-grid-layout .filter-col-wide {{
        grid-column: span 1;
    }}
}}
.filter-grid-layout .filter-col-btn {{
    display: flex;
    align-items: flex-end;
}}
.btn-reset {{
    height: 42px;
    padding: 0 18px;
    border-radius: 12px;
    border: 1px solid rgba(var(--line-rgb), 0.3);
    background: rgba(var(--glass-tint-rgb), 0.3);
    color: var(--text-secondary);
    font-weight: 750;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
}}
.btn-reset:hover {{
    background: var(--primary);
    color: #fff;
    border-color: var(--primary);
    box-shadow: 0 4px 14px rgba(var(--primary-rgb), 0.3);
}}

/* ═════════════════ 卡片加载更多动作条 ═════════════════ */
.mcmod-load-more-bar {{
    grid-column: 1 / -1;
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 14px;
    padding: 2.2rem 1rem;
}}
.btn-card-load-more {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 24px;
    border-radius: 12px;
    border: 1px solid rgba(var(--primary-rgb), 0.35);
    background: linear-gradient(135deg, rgba(var(--primary-rgb), 0.12), rgba(var(--glass-tint-rgb), 0.45));
    color: var(--primary);
    font-size: 0.92rem;
    font-weight: 750;
    cursor: pointer;
    transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 16px rgba(var(--shadow-rgb), 0.08);
}}
.btn-card-load-more:hover {{
    background: var(--primary);
    color: #ffffff;
    box-shadow: 0 6px 20px rgba(var(--primary-rgb), 0.38);
    transform: translateY(-2px);
}}
.btn-card-load-all {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 10px 18px;
    border-radius: 12px;
    border: 1px solid rgba(var(--line-rgb), 0.25);
    background: rgba(var(--glass-tint-rgb), 0.25);
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-weight: 650;
    cursor: pointer;
    transition: all 0.2s;
}}
.btn-card-load-all:hover {{
    background: rgba(var(--glass-tint-rgb), 0.5);
    color: var(--text);
}}

/* ═════════════════ 左侧分层结构化分类体系 ═════════════════ */
.sidebar-tax-container {{
    display: flex;
    flex-direction: column;
    gap: 12px;
}}
.sidebar-tax-group {{
    display: flex;
    flex-direction: column;
    gap: 4px;
}}
.tax-group-title {{
    font-size: 11px;
    font-weight: 750;
    color: var(--text-muted);
    letter-spacing: 0.5px;
    padding: 0 4px 2px;
    text-transform: uppercase;
}}
.tax-group-items {{
    display: flex;
    flex-direction: column;
    gap: 3px;
}}
.s-tax-btn {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 6px 10px;
    border-radius: 8px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.18s;
    text-align: left;
}}
.s-tax-btn:hover {{
    background: rgba(var(--glass-tint-rgb), 0.25);
    color: var(--text);
    padding-left: 12px;
}}
.s-tax-btn.active {{
    background: rgba(var(--primary-rgb), 0.14);
    color: var(--primary) !important;
    font-weight: 750;
    box-shadow: inset 3px 0 0 var(--primary);
    padding-left: 12px;
}}
.s-tax-left {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
}}
.s-tax-icon {{
    font-size: 13px;
}}
.s-tax-count {{
    font-size: 11px;
    color: var(--text-muted);
    background: rgba(0,0,0,0.06);
    padding: 1px 6px;
    border-radius: 10px;
    font-weight: 600;
}}
.s-tax-btn.active .s-tax-count {{
    background: var(--primary);
    color: #fff;
}}
.sidebar-tax-reset {{
    padding: 4px 8px;
    border-radius: 6px;
    border: 1px dashed rgba(var(--line-rgb), 0.4);
    background: transparent;
    color: var(--text-muted);
    font-size: 11px;
    cursor: pointer;
    text-align: center;
    width: 100%;
    transition: all 0.15s;
    margin-bottom: 6px;
}}
.sidebar-tax-reset:hover {{
    color: var(--primary);
    border-color: var(--primary);
    background: rgba(var(--primary-rgb), 0.08);
}}

.hero {{
    background: linear-gradient(135deg, var(--hero), var(--surface));
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 24px 28px;
    margin-bottom: 24px;
    box-shadow: var(--shadow);
}}
.hero-text {{
    max-width: 900px;
}}
.hero-eyebrow {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.8px;
    color: var(--accent);
    margin-bottom: 8px;
}}
.hero-eyebrow span {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
}}
.hero h1 {{
    font-size: 24px;
    font-weight: 800;
    margin: 0 0 6px;
    color: var(--text);
    letter-spacing: -0.4px;
}}
.hero p {{
    font-size: 13px;
    color: var(--text-secondary);
    margin: 0 0 16px;
    line-height: 1.5;
}}
.quick-pills {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}}
.quick-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    font-size: 12px;
    color: var(--text-secondary);
}}
.quick-pill b {{
    color: var(--text);
}}

/* ═════════════════ 活动筛选条 (Active Filters Bar) ═════════════════ */
.active-filters-bar {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: var(--surface);
    border: 1px dashed var(--border);
    border-radius: 12px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}}
.active-filters-label {{
    font-size: 12px;
    font-weight: 700;
    color: var(--text-muted);
}}
.active-filters-list {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}}
.active-pill {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 9px;
    background: var(--soft);
    color: var(--accent);
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
    transition: all 0.18s;
}}
.active-pill:hover {{
    background: color-mix(in srgb, var(--accent) 15%, var(--soft));
}}
.active-pill-remove {{
    font-size: 12px;
    opacity: 0.7;
    margin-left: 2px;
}}
.clear-filters-btn {{
    margin-left: auto;
    font-size: 11px;
    color: var(--text-muted);
    background: none;
    border: none;
    cursor: pointer;
    text-decoration: underline;
}}
.clear-filters-btn:hover {{
    color: var(--accent);
}}

/* ═════════════════ MC百科「📜 历史改动对比」按钮与版本徽章 ═════════════════ */
.modpack-diff-link {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 7px;
    border-radius: 5px;
    background: rgba(var(--primary-rgb), 0.08);
    border: 1px solid rgba(var(--primary-rgb), 0.2);
    color: var(--primary);
    font-size: 0.72rem;
    font-weight: 700;
    text-decoration: none;
    margin-left: 6px;
    vertical-align: middle;
    transition: all 0.18s;
}}
.modpack-diff-link:hover {{
    background: var(--primary);
    color: #fff !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(var(--primary-rgb), 0.3);
}}

.modpack-ver-badge {{
    display: inline-block;
    padding: 2px 6px;
    border-radius: 5px;
    background: #e0e7ff;
    color: #3730a3;
    font-size: 0.72rem;
    font-weight: 700;
    margin-right: 6px;
    vertical-align: middle;
}}
:root[data-theme="dark"] .modpack-ver-badge {{
    background: #312e81;
    color: #c7d2fe;
}}

/* ───── MCMod 版本更新日志模态弹窗系统 ───── */
.version-modal-overlay {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 100002;
    background: rgba(15, 23, 42, 0.72);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.22s ease;
}}
.version-modal-overlay.show {{
    opacity: 1;
    pointer-events: auto;
}}
.version-modal-card {{
    background: var(--glass-bg-solid, #ffffff);
    border: 1.5px solid var(--glass-border, rgba(226, 232, 240, 0.8));
    border-radius: 16px;
    box-shadow: 0 25px 60px -12px rgba(0, 0, 0, 0.35);
    width: min(1120px, 94vw);
    height: min(840px, 90vh);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transform: scale(0.96) translateY(12px);
    transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}}
.version-modal-overlay.show .version-modal-card {{
    transform: scale(1) translateY(0);
}}

/* ── 版本弹窗内的「MC 版本支持分布」条 ──
   把 all_versions 按大版本族聚合成横向条形，条长 = 该族收录的具体版本数。
   数据 100% 来自抓取结果，纯呈现，不做推断补全。 */
.mcver-strip {{
    background: var(--soft, rgba(148, 163, 184, 0.08));
    border: 1px solid var(--line, rgba(148, 163, 184, 0.25));
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 20px;
}}
.mcver-head {{
    display: flex;
    align-items: baseline;
    gap: 10px;
    flex-wrap: wrap;
    font-size: 0.82rem;
    font-weight: 750;
    color: var(--text);
    margin-bottom: 10px;
}}
.mcver-sub {{
    font-size: 0.72rem;
    font-weight: 500;
    color: var(--text-muted);
}}
.mcver-row {{
    display: grid;
    grid-template-columns: 48px 1fr 52px;
    align-items: center;
    gap: 10px;
    padding: 3px 0;
}}
.mcver-fam {{
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
}}
.mcver-track {{
    height: 9px;
    border-radius: 999px;
    background: rgba(var(--line-rgb), 0.3);
    overflow: hidden;
}}
.mcver-fill {{
    display: block;
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--primary), var(--accent, #8b5cf6));
    transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}}
.mcver-n {{
    font-size: 0.72rem;
    color: var(--text-muted);
    text-align: right;
    font-variant-numeric: tabular-nums;
}}
.version-modal-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 22px;
    border-bottom: 1px solid var(--glass-border, #e2e8f0);
    background: rgba(var(--primary-rgb), 0.04);
    gap: 16px;
}}
.version-modal-header-left {{
    flex: 1;
    min-width: 0;
}}
.version-modal-badge {{
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 750;
    color: var(--primary);
    background: rgba(var(--primary-rgb), 0.1);
    padding: 2px 8px;
    border-radius: 6px;
    margin-bottom: 4px;
}}
.version-modal-title {{
    margin: 0;
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--text, #0f172a);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.version-modal-meta {{
    display: flex;
    gap: 10px;
    margin-top: 6px;
    font-size: 0.78rem;
    color: var(--text-secondary, #64748b);
    flex-wrap: wrap;
}}
.version-meta-tag {{
    background: rgba(0, 0, 0, 0.05);
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
}}
:root[data-theme="dark"] .version-meta-tag {{
    background: rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
}}
.version-modal-header-right {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.version-modal-ext-btn {{
    display: inline-flex;
    align-items: center;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 8px;
    border: 1px solid rgba(var(--primary-rgb), 0.3);
    background: rgba(var(--primary-rgb), 0.06);
    color: var(--primary);
    text-decoration: none;
    transition: all 0.15s;
}}
.version-modal-ext-btn:hover {{
    background: var(--primary);
    color: #fff !important;
}}
.version-modal-body {{
    position: relative;
    flex: 1;
    width: 100%;
    height: 100%;
    background: #fff;
    overflow: hidden;
}}
.version-modal-iframe {{
    width: 100%;
    height: 100%;
    border: 0;
    display: block;
}}
.version-modal-loading {{
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    background: rgba(255, 255, 255, 0.92);
    z-index: 10;
    color: var(--text-secondary, #64748b);
    font-size: 0.88rem;
    font-weight: 600;
}}
.version-modal-spinner {{
    width: 32px;
    height: 32px;
    border: 3px solid rgba(var(--primary-rgb), 0.2);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}}

/* ───── 整合包结构化概览卡片（介绍兜底与强化） ───── */
.pv-overview-card {{
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 4px;
}}
.pv-card-header {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
}}
.pv-card-type {{
    background: rgba(var(--primary-rgb), 0.12);
    color: var(--primary);
    font-size: 0.78rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
}}
.pv-card-ver {{
    background: #e0e7ff;
    color: #3730a3;
    font-size: 0.78rem;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
}}
:root[data-theme="dark"] .pv-card-ver {{
    background: #312e81;
    color: #c7d2fe;
}}
.pv-card-stat {{
    background: rgba(0, 0, 0, 0.05);
    color: var(--text-secondary);
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
}}
:root[data-theme="dark"] .pv-card-stat {{
    background: rgba(255, 255, 255, 0.07);
    color: #cbd5e1;
}}
.pv-card-tags {{
    font-size: 0.8rem;
    color: var(--text-secondary);
    line-height: 1.5;
}}
.pv-tag-mini {{
    display: inline-block;
    background: rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 4px;
    padding: 1px 6px;
    margin: 2px;
    font-size: 0.74rem;
    color: var(--text);
}}
.pv-card-mods {{
    background: rgba(0, 0, 0, 0.02);
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    padding: 10px;
}}
.pv-card-section-label {{
    font-size: 0.76rem;
    font-weight: 700;
    color: var(--text-secondary);
    margin-bottom: 6px;
}}
.pv-mod-chips-box {{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
}}
.pv-card-mod-chip {{
    display: inline-block;
    background: rgba(var(--primary-rgb), 0.08);
    color: var(--primary);
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 0.73rem;
    font-weight: 600;
}}
.pv-card-footer {{
    display: flex;
    gap: 10px;
    margin-top: 6px;
}}
.pv-card-btn-primary {{
    flex: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--primary);
    color: #fff !important;
    font-size: 0.82rem;
    font-weight: 700;
    padding: 8px 12px;
    border-radius: 8px;
    text-decoration: none;
    transition: filter 0.16s ease;
}}
.pv-card-btn-primary:hover {{
    filter: brightness(1.1);
}}
.pv-card-btn-sec {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(var(--primary-rgb), 0.08);
    border: 1px solid rgba(var(--primary-rgb), 0.25);
    color: var(--primary);
    font-size: 0.82rem;
    font-weight: 700;
    padding: 8px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.16s ease;
}}
.pv-card-btn-sec:hover {{
    background: var(--primary);
    color: #fff !important;
}}

/* ───── 评论区直达与嵌入式门户卡片 ───── */
.comment-portal-card {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 28px 20px;
    background: var(--surface);
    border-radius: 12px;
    border: 1px solid var(--glass-border);
    margin: 8px;
}}
.comment-portal-icon {{
    font-size: 2.4rem;
    margin-bottom: 8px;
    line-height: 1;
}}
.comment-portal-title {{
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 6px;
}}
.comment-portal-meta {{
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-bottom: 12px;
}}
.comment-portal-meta b {{
    color: var(--primary);
}}
.comment-portal-desc {{
    font-size: 0.84rem;
    color: var(--text-muted);
    max-width: 480px;
    line-height: 1.6;
    margin-bottom: 18px;
}}
.comment-portal-actions {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    justify-content: center;
}}
.btn-comment-portal-primary {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--primary);
    color: #fff !important;
    font-size: 0.85rem;
    font-weight: 700;
    padding: 9px 18px;
    border-radius: 8px;
    text-decoration: none;
    box-shadow: 0 4px 12px rgba(var(--primary-rgb), 0.25);
    transition: filter 0.16s ease, transform 0.16s ease;
}}
.btn-comment-portal-primary:hover {{
    filter: brightness(1.1);
    transform: translateY(-1px);
}}
.btn-comment-portal-sec {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(var(--primary-rgb), 0.08);
    border: 1px solid rgba(var(--primary-rgb), 0.25);
    color: var(--primary);
    font-size: 0.85rem;
    font-weight: 700;
    padding: 9px 16px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.16s ease;
}}
.btn-comment-portal-sec:hover {{
    background: var(--primary);
    color: #fff !important;
}}

/* ═════════════════ MC百科画廊卡片视图 (Cards Gallery) ═════════════════ */
.mcmod-cards-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
    gap: 18px;
    margin-top: 14px;
}}
.mcmod-grid-card {{
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--shadow);
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    display: flex;
    flex-direction: column;
}}
.mcmod-grid-card:hover {{
    transform: translateY(-3px);
    box-shadow: var(--shadow-hover);
    border-color: color-mix(in srgb, var(--accent) 45%, var(--border));
}}
.mcmod-card-top {{
    position: relative;
    height: 140px;
    background: #242938;
    overflow: hidden;
}}
.mcmod-card-cover {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
}}
.mcmod-grid-card:hover .mcmod-card-cover {{
    transform: scale(1.04);
}}
.mcmod-card-overlay {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 6px 10px;
    background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #fff;
    font-size: 0.75rem;
    font-weight: 600;
}}
.mcmod-card-body {{
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
}}
.mcmod-card-title {{
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.4;
    text-decoration: none;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}}
.mcmod-card-title:hover {{
    color: var(--accent);
}}
.mcmod-card-badges {{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    font-size: 0.72rem;
}}
.mcmod-badge-type {{
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(var(--primary-rgb), 0.12);
    color: var(--primary);
    font-weight: 700;
}}
.mcmod-badge-score {{
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(245, 158, 11, 0.15);
    color: #d97706;
    font-weight: 700;
}}
.mcmod-badge-mods {{
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(16, 185, 129, 0.15);
    color: #059669;
    font-weight: 700;
}}
.mcmod-card-foot {{
    margin-top: auto;
    padding-top: 10px;
    border-top: 1px solid var(--line);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}}

/* 响应式断点 */
@media (max-width: 992px) {{
    .sidebar {{
        transform: translateX(-100%);
    }}
    .sidebar.open {{
        transform: translateX(0);
    }}
    .main-content {{
        margin-left: 0;
        padding: 0 16px 24px;
    }}
    .mobile-menu-btn {{
        display: inline-block;
    }}
}}


/* ═════════════════ V3 平台彻底解耦与全平台总览样式 ═════════════════ */
.channel-hero {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, var(--surface), var(--soft));
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 20px 26px;
    margin-bottom: 22px;
    box-shadow: var(--shadow);
}}
.channel-hero-left {{
    max-width: 62%;
}}
.channel-badge-tag {{
    display: inline-block;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.6px;
    color: var(--primary);
    background: var(--soft);
    padding: 3px 10px;
    border-radius: 6px;
    margin-bottom: 8px;
    border: 1px solid var(--line);
}}
.channel-title {{
    font-size: 22px;
    font-weight: 800;
    color: var(--text);
    margin: 0 0 6px;
    letter-spacing: -0.3px;
}}
.channel-desc {{
    font-size: 13px;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.5;
}}
.channel-quick-stats {{
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}}
.cstat-item {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 10px 18px;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 12px;
    min-width: 84px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}}
.cstat-item .cs-num {{
    font-size: 17px;
    font-weight: 800;
    color: var(--primary);
}}
.cstat-item .cs-lbl {{
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 2px;
}}

/* ═════════════════ 6 大平台专属展示卡片顶级质感 (实质内容门户化重构) ═════════════════ */
/* Hero 宏观聚合指标 (替代重复的单平台数量小标签) */
.hero-stats-row {{
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    margin-top: 18px !important;
    flex-wrap: wrap !important;
}}
.hero-stat-item {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 9px !important;
    padding: 7px 14px !important;
    border-radius: 9px !important;
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03) !important;
    transition: transform 0.15s ease, border-color 0.15s ease !important;
}}
.hero-stat-item:hover {{
    transform: translateY(-1px) !important;
    border-color: var(--primary-light) !important;
}}
.hstat-icon {{
    font-size: 18px !important;
    line-height: 1 !important;
}}
.hstat-content {{
    display: flex !important;
    flex-direction: column !important;
}}
.hstat-val {{
    font-size: 14px !important;
    font-weight: 800 !important;
    color: var(--text) !important;
    line-height: 1.2 !important;
}}
.hstat-unit {{
    font-size: 11px !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
}}
.hstat-lbl {{
    font-size: 11px !important;
    font-weight: 550 !important;
    color: var(--text-secondary) !important;
}}

/* 6 平台网格: 3列 x 2行黄金比例布局 */
.all-platforms-grid {{
    display: grid !important;
    grid-template-columns: repeat(3, 1fr) !important;
    gap: 18px !important;
    margin: 22px 0 32px !important;
}}
@media (max-width: 1200px) {{
    .all-platforms-grid {{
        grid-template-columns: repeat(2, 1fr) !important;
    }}
}}
@media (max-width: 768px) {{
    .all-platforms-grid {{
        grid-template-columns: 1fr !important;
    }}
}}

.platform-showcase-card {{
    background: var(--surface) !important;
    border-radius: 14px !important;
    border: 1px solid var(--line) !important;
    padding: 20px 20px 18px !important;
    display: flex !important;
    flex-direction: column !important;
    position: relative !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05) !important;
    transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.22s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.22s ease !important;
}}
.platform-showcase-card::before {{
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    height: 3.5px !important;
    background: var(--card-accent, var(--primary)) !important;
    box-shadow: 0 2px 10px var(--card-glow, rgba(99, 102, 241, 0.3)) !important;
    border-radius: 14px 14px 0 0 !important;
}}
.platform-showcase-card::after {{
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    right: 0 !important;
    width: 160px !important;
    height: 160px !important;
    background: radial-gradient(circle at top right, var(--card-glow, rgba(99, 102, 241, 0.15)) 0%, transparent 70%) !important;
    pointer-events: none !important;
    opacity: 0.6 !important;
    transition: opacity 0.25s ease !important;
}}
.platform-showcase-card:hover {{
    transform: translateY(-4px) !important;
    box-shadow: 0 14px 34px -4px rgba(0, 0, 0, 0.09) !important;
    border-color: rgba(var(--text-rgb, 0, 0, 0), 0.15) !important;
}}
.platform-showcase-card:hover::after {{
    opacity: 0.95 !important;
}}
:root[data-theme="dark"] .platform-showcase-card {{
    background: rgba(18, 24, 38, 0.85) !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.45) !important;
}}
:root[data-theme="dark"] .platform-showcase-card:hover {{
    box-shadow: 0 14px 34px -4px rgba(0, 0, 0, 0.7) !important;
    border-color: rgba(255, 255, 255, 0.18) !important;
}}

.showcase-header {{
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    margin-bottom: 14px !important;
}}
.showcase-icon {{
    width: 40px !important;
    height: 40px !important;
    border-radius: 10px !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.04) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 20px !important;
    flex-shrink: 0 !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
}}
:root[data-theme="dark"] .showcase-icon {{
    background: rgba(255, 255, 255, 0.06) !important;
}}
.showcase-title {{
    font-size: 14.5px !important;
    font-weight: 800 !important;
    color: var(--text) !important;
    margin: 0 0 2px !important;
    line-height: 1.25 !important;
}}
.showcase-badge {{
    font-size: 10px !important;
    font-weight: 700 !important;
    padding: 1.5px 6px !important;
    border-radius: 4px !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.05) !important;
    color: var(--text-secondary) !important;
    display: inline-block !important;
    letter-spacing: 0.02em !important;
}}
:root[data-theme="dark"] .showcase-badge {{
    background: rgba(255, 255, 255, 0.08) !important;
    color: #94a3b8 !important;
}}

.showcase-metrics {{
    display: grid !important;
    grid-template-columns: repeat(3, 1fr) !important;
    gap: 8px !important;
    padding: 10px 12px !important;
    border-radius: 9px !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.025) !important;
    border: 1px solid rgba(var(--text-rgb, 0, 0, 0), 0.04) !important;
    margin-bottom: 12px !important;
}}
:root[data-theme="dark"] .showcase-metrics {{
    background: rgba(255, 255, 255, 0.03) !important;
    border-color: rgba(255, 255, 255, 0.05) !important;
}}
.smetric-val {{
    font-size: 13.5px !important;
    font-weight: 800 !important;
    color: var(--text) !important;
    line-height: 1.2 !important;
}}
.smetric-lbl {{
    font-size: 10.5px !important;
    color: var(--text-muted) !important;
    margin-top: 1px !important;
    white-space: nowrap !important;
}}

/* 平台实质内容: TOP 3 精选代表作微缩清单 */
.showcase-featured-box {{
    margin-bottom: 11px !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 4.5px !important;
}}
.showcase-box-header {{
    font-size: 10.5px !important;
    font-weight: 750 !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.03em !important;
    margin-bottom: 2px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
}}
.featured-item {{
    display: flex !important;
    align-items: center !important;
    gap: 7px !important;
    padding: 4px 6px !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    border: 1px solid transparent !important;
}}
.featured-item:hover {{
    background: rgba(var(--text-rgb, 0, 0, 0), 0.045) !important;
    border-color: rgba(var(--text-rgb, 0, 0, 0), 0.08) !important;
    transform: translateX(2px) !important;
}}
:root[data-theme="dark"] .featured-item:hover {{
    background: rgba(255, 255, 255, 0.06) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
}}
.featured-rank {{
    width: 15px !important;
    height: 15px !important;
    border-radius: 4px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 9.5px !important;
    font-weight: 850 !important;
    flex-shrink: 0 !important;
    line-height: 1 !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.08) !important;
    color: var(--text-secondary) !important;
}}
.featured-item:nth-child(1) .featured-rank {{
    background: linear-gradient(135deg, #f59e0b, #d97706) !important;
    color: #ffffff !important;
}}
.featured-item:nth-child(2) .featured-rank {{
    background: linear-gradient(135deg, #94a3b8, #64748b) !important;
    color: #ffffff !important;
}}
.featured-item:nth-child(3) .featured-rank {{
    background: linear-gradient(135deg, #b45309, #78350f) !important;
    color: #ffffff !important;
}}
.featured-name {{
    font-size: 11.5px !important;
    font-weight: 650 !important;
    color: var(--text) !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
}}
.featured-meta {{
    font-size: 10px !important;
    color: var(--text-muted) !important;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
    font-variant-numeric: tabular-nums !important;
}}

/* 快捷特色标签直达胶囊 */
.showcase-tags-box {{
    display: flex !important;
    align-items: center !important;
    gap: 4px !important;
    flex-wrap: wrap !important;
    margin-bottom: 14px !important;
    margin-top: auto !important;
}}
.showcase-tag-chip {{
    font-size: 10.5px !important;
    font-weight: 600 !important;
    padding: 2.5px 6.5px !important;
    border-radius: 5px !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.035) !important;
    border: 1px solid rgba(var(--text-rgb, 0, 0, 0), 0.06) !important;
    color: var(--text-secondary) !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    line-height: 1.2 !important;
}}
:root[data-theme="dark"] .showcase-tag-chip {{
    background: rgba(255, 255, 255, 0.05) !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
    color: #cbd5e1 !important;
}}
.showcase-tag-chip:hover {{
    color: var(--text) !important;
    border-color: var(--card-accent) !important;
    background: var(--soft) !important;
    transform: translateY(-1px) !important;
}}

.showcase-btn {{
    width: 100% !important;
    padding: 8px 14px !important;
    border-radius: 8px !important;
    border: none !important;
    background: var(--card-accent, var(--primary)) !important;
    color: #ffffff !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 6px !important;
    box-shadow: 0 3px 10px var(--card-glow, rgba(99, 102, 241, 0.3)) !important;
    margin-top: 0 !important;
}}
.showcase-btn:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px var(--card-glow, rgba(99, 102, 241, 0.45)) !important;
    filter: brightness(1.06) !important;
}}
.showcase-btn:active {{
    transform: translateY(0) !important;
}}
/* 跨平台全局联合穿透搜索 (顶级命令中心体验) */
.cross-search-section {{
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    padding: 20px 22px 18px !important;
    margin-bottom: 22px !important;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05) !important;
    position: relative !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}}
:root[data-theme="dark"] .cross-search-section {{
    background: rgba(18, 24, 38, 0.85) !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
    box-shadow: 0 4px 24px -2px rgba(0, 0, 0, 0.45) !important;
}}

.csearch-top-row {{
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    margin-bottom: 14px !important;
    flex-wrap: wrap !important;
    gap: 10px !important;
}}
.csearch-title-group {{
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
}}
.csearch-badge {{
    font-size: 10px !important;
    font-weight: 800 !important;
    padding: 2.5px 7px !important;
    border-radius: 5px !important;
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #ffffff !important;
    letter-spacing: 0.04em !important;
    line-height: 1 !important;
}}
.csearch-heading {{
    font-size: 16px !important;
    font-weight: 850 !important;
    color: var(--text) !important;
    letter-spacing: -0.01em !important;
    margin: 0 !important;
    line-height: 1 !important;
}}
.csearch-platforms-hint {{
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    flex-wrap: wrap !important;
}}
.cplat-pill {{
    font-size: 10.5px !important;
    font-weight: 650 !important;
    padding: 2px 7px !important;
    border-radius: 5px !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.04) !important;
    border: 1px solid var(--line) !important;
    color: var(--text-secondary) !important;
    line-height: 1.3 !important;
}}
:root[data-theme="dark"] .cplat-pill {{
    background: rgba(255, 255, 255, 0.05) !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
}}

.cross-search-input-wrap {{
    position: relative !important;
    display: flex !important;
    align-items: center !important;
    margin-bottom: 12px !important;
}}
.cross-search-icon {{
    position: absolute !important;
    left: 16px !important;
    font-size: 17px !important;
    color: var(--text-muted) !important;
    pointer-events: none !important;
}}
.cross-search-input {{
    width: 100% !important;
    height: 48px !important;
    padding: 0 95px 0 46px !important;
    border: 1.5px solid var(--line) !important;
    border-radius: 11px !important;
    background: var(--bg) !important;
    color: var(--text) !important;
    font-size: 13.5px !important;
    font-weight: 550 !important;
    outline: none !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-sizing: border-box !important;
}}
.cross-search-input:focus {{
    border-color: var(--primary) !important;
    background: var(--surface) !important;
    box-shadow: 0 0 0 4px rgba(var(--primary-rgb, 99, 102, 241), 0.14) !important;
}}
.cross-search-clear {{
    position: absolute !important;
    right: 58px !important;
    width: 24px !important;
    height: 24px !important;
    border-radius: 50% !important;
    border: none !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.08) !important;
    color: var(--text-secondary) !important;
    font-size: 12px !important;
    line-height: 1 !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.15s !important;
    padding: 0 !important;
}}
.cross-search-clear:hover {{
    background: rgba(239, 68, 68, 0.15) !important;
    color: #ef4444 !important;
    transform: scale(1.08) !important;
}}
.cross-search-kbd {{
    position: absolute !important;
    right: 12px !important;
    display: flex !important;
    align-items: center !important;
    gap: 3px !important;
    pointer-events: none !important;
}}
.cross-search-kbd kbd {{
    font-family: inherit !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    padding: 2px 5px !important;
    border-radius: 4px !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.06) !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--line) !important;
    line-height: 1 !important;
}}
:root[data-theme="dark"] .cross-search-kbd kbd {{
    background: rgba(255, 255, 255, 0.08) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
}}

/* 热门快搜标签条 */
.cross-hot-tags {{
    display: flex !important;
    align-items: center !important;
    gap: 5px !important;
    flex-wrap: wrap !important;
}}
.hot-label {{
    font-size: 11px !important;
    font-weight: 700 !important;
    color: var(--text-muted) !important;
    margin-right: 2px !important;
}}
.hot-chip {{
    font-size: 11px !important;
    font-weight: 600 !important;
    padding: 2.5px 8px !important;
    border-radius: 6px !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.035) !important;
    border: 1px solid var(--line) !important;
    color: var(--text-secondary) !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    line-height: 1.3 !important;
}}
:root[data-theme="dark"] .hot-chip {{
    background: rgba(255, 255, 255, 0.05) !important;
    border-color: rgba(255, 255, 255, 0.08) !important;
    color: #cbd5e1 !important;
}}
.hot-chip:hover {{
    color: var(--primary) !important;
    border-color: var(--primary) !important;
    background: var(--soft) !important;
    transform: translateY(-1px) !important;
}}

/* 6 平台实时结果展开抽屉 */
.cross-results-grid {{
    display: none;
    grid-template-columns: repeat(3, 1fr) !important;
    gap: 14px !important;
    margin-top: 16px !important;
    padding-top: 16px !important;
    border-top: 1px dashed var(--line) !important;
}}
.cross-results-grid.active {{
    display: grid !important;
}}
@media (max-width: 1200px) {{
    .cross-results-grid {{
        grid-template-columns: repeat(2, 1fr) !important;
    }}
}}
@media (max-width: 768px) {{
    .cross-results-grid {{
        grid-template-columns: 1fr !important;
    }}
}}

.cross-col {{
    background: var(--bg) !important;
    border: 1px solid var(--line) !important;
    border-top: 3px solid var(--col-theme, var(--primary)) !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
    display: flex !important;
    flex-direction: column !important;
}}
:root[data-theme="dark"] .cross-col {{
    background: rgba(255, 255, 255, 0.025) !important;
    border-color: rgba(255, 255, 255, 0.07) !important;
}}
.cross-col-header {{
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    font-size: 12px !important;
    font-weight: 750 !important;
    color: var(--text) !important;
    padding-bottom: 8px !important;
    border-bottom: 1px solid var(--line) !important;
    margin-bottom: 10px !important;
}}
.col-more {{
    font-size: 11px !important;
    font-weight: 650 !important;
    color: var(--primary) !important;
    text-decoration: none !important;
    transition: opacity 0.15s !important;
}}
.col-more:hover {{
    text-decoration: underline !important;
}}
.cross-result-item {{
    display: flex !important;
    align-items: center !important;
    gap: 9px !important;
    padding: 6px 8px !important;
    border-radius: 7px !important;
    background: var(--surface) !important;
    margin-bottom: 6px !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    border: 1px solid var(--line) !important;
}}
.cross-result-item:hover {{
    background: var(--soft) !important;
    border-color: var(--primary-light) !important;
    transform: translateX(2px) !important;
}}
.cross-thumb {{
    width: 48px !important;
    height: 34px !important;
    border-radius: 5px !important;
    object-fit: cover !important;
    flex-shrink: 0 !important;
    background: rgba(var(--text-rgb, 0, 0, 0), 0.05) !important;
}}
.cross-item-info {{
    flex: 1 1 auto !important;
    min-width: 0 !important;
}}
.cross-item-title {{
    font-size: 12px !important;
    font-weight: 700 !important;
    color: var(--text) !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
}}
.cross-item-sub {{
    font-size: 10.5px !important;
    color: var(--text-muted) !important;
    margin-top: 1px !important;
    display: flex !important;
    gap: 8px !important;
}}
/* 视频字幕抽屉 */
.bili-sub-wrap {{
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px dashed var(--line);
}}
.bili-sub-btn {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--soft);
    color: var(--primary);
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 11px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.15s;
}}
.bili-sub-btn:hover {{
    background: var(--primary);
    color: #ffffff;
}}
.bili-sub-panel {{
    display: none;
    margin-top: 8px;
    padding: 10px 12px;
    background: var(--bg);
    border: 1px solid var(--line);
    border-radius: 8px;
    font-size: 12px;
    color: var(--text-secondary);
    line-height: 1.6;
    max-height: 160px;
    overflow-y: auto;
    white-space: pre-wrap;
}}

/* ═══════════ BBSMC 模组包卡片网格与专属交互 ═══════════ */
.bbsmc-channel-hero {{
    background: linear-gradient(135deg, rgba(0, 175, 92, 0.12), rgba(27, 217, 106, 0.05));
    border-color: rgba(0, 175, 92, 0.25);
}}
.bbsmc-cards-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 1.25rem;
}}
.bbsmc-pack-card {{
    background: var(--glass-bg);
    border: 1px solid var(--border);
    border-radius: 18px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    transition: transform 0.22s, box-shadow 0.22s, border-color 0.22s;
}}
.bbsmc-pack-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.14);
    border-color: rgba(0, 175, 92, 0.45);
}}
.bbsmc-card-cover {{
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #111;
    overflow: hidden;
    display: block;
}}
.bbsmc-card-img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
}}
.bbsmc-pack-card:hover .bbsmc-card-img {{
    transform: scale(1.04);
}}
.bbsmc-card-stats {{
    position: absolute;
    left: 8px;
    bottom: 8px;
    display: flex;
    gap: 10px;
    padding: 3px 9px;
    background: rgba(0, 0, 0, 0.72);
    color: #fff;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 6px;
    backdrop-filter: blur(4px);
}}
.bbsmc-card-ver-badge {{
    position: absolute;
    right: 8px;
    bottom: 8px;
    padding: 2px 7px;
    background: rgba(0, 175, 92, 0.88);
    color: #fff;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 4px;
    backdrop-filter: blur(4px);
}}
.bbsmc-card-body {{
    padding: 1rem 1.15rem;
    display: flex;
    flex-direction: column;
    flex: 1;
}}
.bbsmc-card-title {{
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.45;
    color: var(--text);
    margin-bottom: 0.4rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-decoration: none;
}}
.bbsmc-card-title:hover {{
    color: #00af5c;
}}
.bbsmc-card-meta {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
}}
.bbsmc-author-tag {{
    font-weight: 600;
    color: var(--text-secondary);
}}
.bbsmc-card-desc {{
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.5;
    margin-bottom: 0.75rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}
.bbsmc-card-tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 0.85rem;
}}
.bbsmc-badge-ver {{
    background: rgba(0, 175, 92, 0.15);
    color: #00af5c;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid rgba(0, 175, 92, 0.3);
}}
.bbsmc-badge-loader {{
    background: rgba(14, 165, 233, 0.15);
    color: #0ea5e9;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid rgba(14, 165, 233, 0.3);
}}
.bbsmc-badge-cat {{
    background: rgba(var(--glass-tint-rgb), 0.1);
    color: var(--text-secondary);
    font-size: 0.72rem;
    font-weight: 500;
    padding: 2px 7px;
    border-radius: 6px;
    border: 1px solid var(--border);
}}
.bbsmc-gallery-strip {{
    display: flex;
    gap: 6px;
    overflow-x: auto;
    padding: 4px 0 8px;
    scrollbar-width: thin;
    margin-bottom: 8px;
}}
.bbsmc-gallery-thumb {{
    width: 68px;
    height: 44px;
    border-radius: 6px;
    object-fit: cover;
    flex-shrink: 0;
    cursor: pointer;
    border: 1px solid var(--border);
    transition: transform 0.15s, border-color 0.15s;
}}
.bbsmc-gallery-thumb:hover {{
    transform: scale(1.06);
    border-color: #00af5c;
}}
.bbsmc-download-zone {{
    margin-top: auto;
    background: rgba(var(--glass-tint-rgb), 0.1);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem 0.85rem;
}}
.bbsmc-more-links {{
    margin-top: 6px;
    font-size: 0.78rem;
}}
.bbsmc-more-summary {{
    cursor: pointer;
    color: var(--primary);
    font-weight: 600;
    padding: 2px 0;
    user-select: none;
}}
.bbsmc-more-body {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px dashed var(--line);
}}
.pan-btn-modrinth {{
    background: rgba(0, 175, 92, 0.15);
    color: #00af5c;
    border: 1px solid rgba(0, 175, 92, 0.3);
}}
.pan-btn-modrinth:hover {{
    background: #00af5c;
    color: #fff;
}}
.pan-btn-curseforge {{
    background: rgba(241, 100, 54, 0.15);
    color: #f16436;
    border: 1px solid rgba(241, 100, 54, 0.3);
}}
.pan-btn-curseforge:hover {{
    background: #f16436;
    color: #fff;
}}
.pan-btn-xunlei {{
    background: rgba(0, 162, 255, 0.15);
    color: #00a2ff;
    border: 1px solid rgba(0, 162, 255, 0.3);
}}
.pan-btn-xunlei:hover {{
    background: #00a2ff;
    color: #fff;
}}

/* ═══════════ XYEBBS 像素世界模组包卡片网格与专属交互 ═══════════ */
/* ═══════════ Modrinth 专属样式 ═══════════ */
.modrinth-channel-hero {{
    background: linear-gradient(135deg, rgba(27, 217, 106, 0.12), rgba(20, 184, 166, 0.05));
    border-color: rgba(27, 217, 106, 0.25);
}}
.modrinth-cards-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 1.25rem;
}}
.modrinth-pack-card {{
    background: var(--glass-bg);
    border: 1px solid var(--border);
    border-radius: 18px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    transition: transform 0.22s, box-shadow 0.22s, border-color 0.22s;
}}
.modrinth-pack-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.14);
    border-color: rgba(27, 217, 106, 0.45);
}}
.modrinth-badge-ver {{
    background: rgba(27, 217, 106, 0.15);
    color: #1bd96a;
    border: 1px solid rgba(27, 217, 106, 0.3);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}}
.modrinth-badge-loader {{
    background: rgba(56, 189, 248, 0.12);
    color: #0284c7;
    border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}}
.modrinth-badge-cat {{
    background: rgba(168, 85, 247, 0.1);
    color: #9333ea;
    border: 1px solid rgba(168, 85, 247, 0.25);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
}}

/* ═══════════ CurseForge 专属样式 ═══════════ */
.curseforge-channel-hero {{
    background: linear-gradient(135deg, rgba(241, 100, 54, 0.12), rgba(234, 88, 12, 0.05));
    border-color: rgba(241, 100, 54, 0.25);
}}
.curseforge-cards-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 1.25rem;
}}
.curseforge-pack-card {{
    background: var(--glass-bg);
    border: 1px solid var(--border);
    border-radius: 18px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    transition: transform 0.22s, box-shadow 0.22s, border-color 0.22s;
}}
.curseforge-pack-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.14);
    border-color: rgba(241, 100, 54, 0.45);
}}
.curseforge-badge-ver {{
    background: rgba(241, 100, 54, 0.15);
    color: #f16436;
    border: 1px solid rgba(241, 100, 54, 0.3);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}}
.curseforge-badge-loader {{
    background: rgba(245, 158, 11, 0.12);
    color: #d97706;
    border: 1px solid rgba(245, 158, 11, 0.3);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
}}
.curseforge-badge-cat {{
    background: rgba(236, 72, 153, 0.1);
    color: #db2777;
    border: 1px solid rgba(236, 72, 153, 0.25);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
}}

.xyebbs-channel-hero {{
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.12), rgba(22, 163, 74, 0.05));
    border-color: rgba(34, 197, 94, 0.25);
}}
.xyebbs-cards-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 1.25rem;
}}
.xyebbs-pack-card {{
    background: var(--glass-bg);
    border: 1px solid var(--border);
    border-radius: 18px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    transition: transform 0.22s, box-shadow 0.22s, border-color 0.22s;
}}
.xyebbs-pack-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.14);
    border-color: rgba(34, 197, 94, 0.45);
}}
.xyebbs-card-cover {{
    position: relative;
    width: 100%;
    aspect-ratio: 16 / 9;
    background: #111;
    overflow: hidden;
    display: block;
}}
.xyebbs-card-img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
}}
.xyebbs-pack-card:hover .xyebbs-card-img {{
    transform: scale(1.04);
}}
.xyebbs-card-stats {{
    position: absolute;
    left: 8px;
    bottom: 8px;
    display: flex;
    gap: 10px;
    padding: 3px 9px;
    background: rgba(0, 0, 0, 0.72);
    color: #fff;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 6px;
    backdrop-filter: blur(4px);
}}
.xyebbs-card-ver-badge {{
    position: absolute;
    right: 8px;
    bottom: 8px;
    padding: 2px 7px;
    background: rgba(34, 197, 94, 0.88);
    color: #fff;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 4px;
    backdrop-filter: blur(4px);
}}
.xyebbs-card-body {{
    padding: 1rem 1.15rem;
    display: flex;
    flex-direction: column;
    flex: 1;
}}
.xyebbs-card-title {{
    font-size: 1rem;
    font-weight: 700;
    line-height: 1.45;
    color: var(--text);
    margin-bottom: 0.4rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-decoration: none;
}}
.xyebbs-card-title:hover {{
    color: #16a34a;
}}
.xyebbs-card-meta {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
}}
.xyebbs-author-tag {{
    font-weight: 600;
    color: var(--text-secondary);
}}
.xyebbs-card-desc {{
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.5;
    margin-bottom: 0.75rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}
.xyebbs-card-tags {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 0.85rem;
}}
.xyebbs-badge-ver {{
    background: rgba(34, 197, 94, 0.15);
    color: #16a34a;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid rgba(34, 197, 94, 0.3);
}}
.xyebbs-badge-loader {{
    background: rgba(14, 165, 233, 0.15);
    color: #0ea5e9;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    border: 1px solid rgba(14, 165, 233, 0.3);
}}
.xyebbs-badge-cat {{
    background: rgba(var(--glass-tint-rgb), 0.1);
    color: var(--text-secondary);
    font-size: 0.72rem;
    font-weight: 500;
    padding: 2px 7px;
    border-radius: 6px;
    border: 1px solid var(--border);
}}
.xyebbs-download-zone {{
    margin-top: auto;
    background: rgba(var(--glass-tint-rgb), 0.1);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem 0.85rem;
}}
.xyebbs-more-links {{
    margin-top: 6px;
    font-size: 0.78rem;
}}
.xyebbs-more-summary {{
    cursor: pointer;
    color: #16a34a;
    font-weight: 600;
    padding: 2px 0;
    user-select: none;
}}
.xyebbs-more-body {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px dashed var(--line);
}}
.pan-btn-xyebbs {{
    background: rgba(34, 197, 94, 0.15);
    color: #16a34a;
    border: 1px solid rgba(34, 197, 94, 0.3);
}}
.pan-btn-xyebbs:hover {{
    background: #16a34a;
    color: #fff;
}}

@media (max-width: 900px) {{
    .all-platforms-grid, .cross-results-grid {{
        grid-template-columns: 1fr;
    }}
    .channel-hero {{
        flex-direction: column;
        align-items: flex-start;
        gap: 14px;
    }}
    .channel-hero-left {{
        max-width: 100%;
    }}
}}


/* 异步流式加载态骨架 */
.platform-loading-box {{
    grid-column: 1 / -1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    background: var(--surface);
    border: 1.5px dashed var(--line);
    border-radius: var(--radius);
    text-align: center;
    margin: 20px 0;
}}
/* ═════════════════ 侧边栏融合筛选器体系 ═════════════════ */
.sidebar {{
    scrollbar-width: thin;
}}
.sidebar-scrollable {{
    flex: 1;
    overflow-y: auto;
    padding-right: 4px;
}}
.sidebar-filter-panel {{
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid var(--line);
}}
.sidebar-panel-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding: 0 2px;
}}
.sidebar-panel-title {{
    font-size: 11px;
    font-weight: 800;
    color: var(--text-muted);
    letter-spacing: 0.6px;
    text-transform: uppercase;
}}
.sidebar-reset-btn {{
    background: transparent;
    border: 1px dashed rgba(var(--line-rgb), 0.4);
    border-radius: 6px;
    padding: 2px 7px;
    font-size: 11px;
    font-weight: 650;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.15s;
}}
.sidebar-reset-btn:hover {{
    color: var(--primary);
    border-color: var(--primary);
    background: rgba(var(--primary-rgb), 0.08);
}}
.sidebar-control-group {{
    margin-bottom: 12px;
}}
.sidebar-label {{
    display: block;
    font-size: 11px;
    font-weight: 700;
    color: var(--text-secondary);
    margin-bottom: 5px;
}}
.sidebar-select {{
    width: 100%;
    padding: 6px 10px;
    border-radius: 8px;
    border: 1px solid var(--line);
    background: var(--surface);
    color: var(--text);
    font-size: 12px;
    font-weight: 600;
    outline: none;
    cursor: pointer;
    transition: border-color 0.18s, box-shadow 0.18s;
}}
.sidebar-select:focus {{
    border-color: var(--primary);
    box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.15);
}}
.sidebar-chip-grid {{
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
}}
.s-chip {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    border-radius: 6px;
    background: var(--soft);
    border: 1px solid transparent;
    color: var(--text-secondary);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    user-select: none;
}}
.s-chip:hover {{
    background: rgba(var(--primary-rgb), 0.12);
    color: var(--text);
    border-color: rgba(var(--primary-rgb), 0.2);
}}
.s-chip.active {{
    background: var(--primary) !important;
    color: #ffffff !important;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(var(--primary-rgb), 0.35);
}}
.s-chip-count {{
    font-size: 9.5px;
    opacity: 0.75;
    background: rgba(0, 0, 0, 0.08);
    padding: 0 4px;
    border-radius: 8px;
}}
.s-chip.active .s-chip-count {{
    background: rgba(255, 255, 255, 0.25);
    color: #ffffff;
    opacity: 1;
}}
.sidebar-hover-panel {{
    display: flex;
    gap: 4px;
    background: var(--soft);
    padding: 3px;
    border-radius: 8px;
    border: 1px solid var(--line);
}}
.sidebar-hover-panel .mode-toggle {{
    flex: 1;
    justify-content: center;
    font-size: 11px;
    padding: 4px 0;
}}

/* ═════════════════ 右侧极简精美工具栏 (告别沉重筛选卡片) ═════════════════ */
.mcmod-content-toolbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 14px;
    padding: 8px 16px;
    border-radius: 12px;
    background: var(--surface-glass);
    backdrop-filter: blur(14px);
    border: 1px solid var(--line);
    box-shadow: 0 3px 12px rgba(0, 0, 0, 0.03);
}}
.mcmod-matched-badge {{
    font-size: 13px;
    font-weight: 650;
    color: var(--text-secondary);
    white-space: nowrap;
}}
.mcmod-matched-badge strong {{
    color: var(--primary);
    font-weight: 850;
}}
.mcmod-toolbar-search {{
    flex: 1;
    max-width: 600px;
    position: relative;
}}
.mcmod-toolbar-search .mcmod-search-input {{
    width: 100%;
    padding: 7px 34px 7px 36px;
    border-radius: 999px;
    border: 1px solid rgba(var(--primary-rgb), 0.25);
    background: rgba(var(--glass-tint-rgb), 0.2);
    color: var(--text);
    font-size: 0.88rem;
    font-weight: 600;
    outline: none;
    transition: all 0.2s;
}}
.mcmod-toolbar-search .mcmod-search-input:focus {{
    border-color: var(--primary);
    background: var(--surface);
    box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.16);
}}
.mcmod-toolbar-search .mcmod-search-icon {{
    position: absolute;
    left: 13px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    font-size: 13px;
    pointer-events: none;
}}
.mcmod-toolbar-search .mcmod-search-clear-btn {{
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(128,128,128,0.22);
    border: none;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    font-size: 10px;
    line-height: 18px;
    text-align: center;
    color: var(--text);
    cursor: pointer;
}}
.mcmod-toolbar-search .mcmod-search-clear-btn:hover {{
    background: var(--primary);
    color: #fff;
}}


/* ═══════════ B站 6维指标栏与卡片微调 ═══════════ */
.bili-metrics-bar {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px 12px;
    margin: 8px 0 10px;
    padding: 6px 10px;
    background: rgba(var(--glass-tint-rgb), 0.12);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.78rem;
    color: var(--text-secondary);
}}
.bmb-item {{
    display: inline-flex;
    align-items: center;
    gap: 3px;
    white-space: nowrap;
}}
.bmb-item strong {{
    color: var(--text);
    font-weight: 750;
}}
.bili-card-stats {{
    position: absolute;
    left: 8px;
    bottom: 8px;
    display: flex;
    gap: 8px;
    padding: 2px 8px;
    background: rgba(0, 0, 0, 0.7);
    color: #fff;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 4px;
    backdrop-filter: blur(4px);
    max-width: calc(100% - 90px);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}


/* ═════════════════ 全局原生控件深度主题化 (消除 Windows 原生质感) ═════════════════ */

/* 1. 消除 Windows 粗灰方块滚动条，全局注入自适应主题晶透细条 */
* {{
    scrollbar-width: thin !important;
    scrollbar-color: rgba(var(--primary-rgb), 0.3) transparent !important;
}}
::-webkit-scrollbar {{
    width: 7px !important;
    height: 7px !important;
}}
::-webkit-scrollbar-track {{
    background: transparent !important;
}}
::-webkit-scrollbar-thumb {{
    background: rgba(var(--primary-rgb), 0.28) !important;
    border-radius: 999px !important;
    border: 1px solid transparent !important;
}}
::-webkit-scrollbar-thumb:hover {{
    background: var(--primary) !important;
}}

/* 2. 原生下拉与 Select2 Glass 深度毛玻璃定制（彻底消除 Windows 原生系统黑框蓝条） */
/* 隐藏已初始化的原生 select，防止双重叠框 */
select.select2-hidden-accessible {{
    display: none !important;
    opacity: 0 !important;
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: 0 !important;
    pointer-events: none !important;
}}

/* 精致现代圆角选择器（1:1 复刻 B站规范与优雅设计，彻底告别粗笨大椭圆胶囊） */
select, .hub-select, .form-select, .sidebar-select {{
    appearance: none !important;
    -webkit-appearance: none !important;
    -moz-appearance: none !important;
    background-color: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    height: 36px !important;
    min-height: 36px !important;
    padding: 0 30px 0 13px !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: right 10px center !important;
    background-size: 11px !important;
    outline: none !important;
    font-size: 12.5px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
}}

/* Select2 Glass 现代质感单选框（1:1 复刻 Image 4 优雅规整规范） */
.hub-actions-cluster .select2-container--bootstrap-5 .select2-selection--single,
#mcmodCentralHub .select2-container--bootstrap-5 .select2-selection--single,
#sidebarBiliFilters .select2-container--bootstrap-5 .select2-selection--single,
.select2-container--bootstrap-5 .select2-selection.hub-select2-selection {{
    height: 36px !important;
    min-height: 36px !important;
    border-radius: 12px !important;
    padding: 0 32px 0 13px !important;
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    color: var(--text) !important;
    display: inline-flex !important;
    align-items: center !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    cursor: pointer !important;
    position: relative !important;
    box-sizing: border-box !important;
}}
.hub-actions-cluster .select2-container--bootstrap-5 .select2-selection--single:hover,
#mcmodCentralHub .select2-container--bootstrap-5 .select2-selection--single:hover,
#sidebarBiliFilters .select2-container--bootstrap-5 .select2-selection--single:hover,
.select2-container--bootstrap-5 .select2-selection.hub-select2-selection:hover {{
    border-color: var(--primary) !important;
    background: var(--soft) !important;
}}
.hub-actions-cluster .select2-container--bootstrap-5.select2-container--open .select2-selection--single,
.hub-actions-cluster .select2-container--bootstrap-5.select2-container--focus .select2-selection--single,
#mcmodCentralHub .select2-container--bootstrap-5.select2-container--open .select2-selection--single,
#mcmodCentralHub .select2-container--bootstrap-5.select2-container--focus .select2-selection--single,
.select2-container--bootstrap-5.select2-container--open .select2-selection.hub-select2-selection,
.select2-container--bootstrap-5.select2-container--focus .select2-selection.hub-select2-selection {{
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.15) !important;
}}
.hub-actions-cluster .select2-container--bootstrap-5 .select2-selection--single .select2-selection__rendered,
#mcmodCentralHub .select2-container--bootstrap-5 .select2-selection--single .select2-selection__rendered,
#sidebarBiliFilters .select2-container--bootstrap-5 .select2-selection--single .select2-selection__rendered,
.select2-container--bootstrap-5 .select2-selection.hub-select2-selection .select2-selection__rendered {{
    line-height: 34px !important;
    padding: 0 !important;
    color: var(--text) !important;
    font-size: 12.5px !important;
    font-weight: 600 !important;
}}
.hub-actions-cluster .select2-container--bootstrap-5 .select2-selection--single .select2-selection__arrow,
#mcmodCentralHub .select2-container--bootstrap-5 .select2-selection--single .select2-selection__arrow,
#sidebarBiliFilters .select2-container--bootstrap-5 .select2-selection--single .select2-selection__arrow,
.select2-container--bootstrap-5 .select2-selection.hub-select2-selection .select2-selection__arrow {{
    height: 34px !important;
    width: 24px !important;
    right: 6px !important;
    top: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}}
.hub-actions-cluster .select2-container--bootstrap-5 .select2-selection--single .select2-selection__arrow b,
#mcmodCentralHub .select2-container--bootstrap-5 .select2-selection--single .select2-selection__arrow b,
#sidebarBiliFilters .select2-container--bootstrap-5 .select2-selection--single .select2-selection__arrow b,
.select2-container--bootstrap-5 .select2-selection.hub-select2-selection .select2-selection__arrow b {{
    display: none !important;
}}
.hub-actions-cluster .select2-container--bootstrap-5 .select2-selection--single .select2-selection__arrow:after,
#mcmodCentralHub .select2-container--bootstrap-5 .select2-selection--single .select2-selection__arrow:after,
#sidebarBiliFilters .select2-container--bootstrap-5 .select2-selection--single .select2-selection__arrow:after,
.select2-container--bootstrap-5 .select2-selection.hub-select2-selection .select2-selection__arrow:after {{
    content: '' !important;
    display: block !important;
    width: 12px !important;
    height: 12px !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-size: 11px !important;
    transition: transform 0.2s ease !important;
}}
.hub-actions-cluster .select2-container--bootstrap-5.select2-container--open .select2-selection--single .select2-selection__arrow:after,
#mcmodCentralHub .select2-container--bootstrap-5.select2-container--open .select2-selection--single .select2-selection__arrow:after,
.select2-container--bootstrap-5.select2-container--open .select2-selection.hub-select2-selection .select2-selection__arrow:after {{
    transform: rotate(180deg) !important;
}}

/* 紧凑尺寸（用于表格每页条数） */
.select2-container--bootstrap-5 .select2-selection.hub-select2-sm {{
    height: 30px !important;
    min-height: 30px !important;
    padding: 0 24px 0 10px !important;
    min-width: 58px !important;
}}
.select2-container--bootstrap-5 .select2-selection.hub-select2-sm .select2-selection__rendered {{
    line-height: 28px !important;
    font-size: 12px !important;
}}
.select2-container--bootstrap-5 .select2-selection.hub-select2-sm .select2-selection__arrow {{
    height: 28px !important;
    width: 18px !important;
    right: 4px !important;
}}

/* Select2 Glass 展开下拉菜单浮层（纯 DOM 级晶透毛玻璃，彻底告别 Win32 系统弹层） */
.select2-dropdown.hub-select2-dropdown {{
    border-radius: 14px !important;
    border: 1.5px solid var(--line) !important;
    background: var(--surface) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    box-shadow: 0 16px 40px rgba(0,0,0,0.18), 0 2px 8px rgba(0,0,0,0.06) !important;
    overflow: hidden !important;
    padding: 6px !important;
    margin-top: 4px !important;
    z-index: 999999 !important;
}}
.select2-dropdown.hub-select2-dropdown .select2-search--dropdown {{
    padding: 4px 6px 8px !important;
}}
.select2-dropdown.hub-select2-dropdown .select2-search__field {{
    border-radius: 8px !important;
    border: 1px solid var(--line) !important;
    background: var(--surface-glass, var(--surface)) !important;
    color: var(--text) !important;
    font-size: 12px !important;
    padding: 5px 8px !important;
    outline: none !important;
}}
.select2-dropdown.hub-select2-dropdown .select2-search__field:focus {{
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(var(--primary-rgb), 0.18) !important;
}}
.select2-dropdown.hub-select2-dropdown .select2-results__options {{
    max-height: 280px !important;
    padding: 2px !important;
}}
.select2-dropdown.hub-select2-dropdown .select2-results__option {{
    border-radius: 8px !important;
    padding: 7px 12px !important;
    margin: 2px 0 !important;
    font-size: 12.5px !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    cursor: pointer !important;
    transition: background 0.12s ease, color 0.12s ease !important;
}}
.select2-dropdown.hub-select2-dropdown .select2-results__option--highlighted {{
    background: var(--soft) !important;
    color: var(--primary) !important;
    font-weight: 750 !important;
}}
.select2-dropdown.hub-select2-dropdown .select2-results__option--selected {{
    background: linear-gradient(135deg, var(--primary), var(--secondary, var(--primary))) !important;
    background-color: var(--primary) !important;
    color: #ffffff !important;
    font-weight: 800 !important;
    box-shadow: 0 2px 8px rgba(var(--primary-rgb), 0.28) !important;
}}
.select2-dropdown.hub-select2-dropdown .select2-results__options::-webkit-scrollbar {{
    width: 6px !important;
}}
.select2-dropdown.hub-select2-dropdown .select2-results__options::-webkit-scrollbar-thumb {{
    background: rgba(var(--primary-rgb), 0.3) !important;
    border-radius: 999px !important;
}}

/* 3. 修复“每页显示 [25] 条”文字换行与排版错乱 Bug */
#mcmodPageSizeSlot,
.mcmod-pagesize-slot,
.page-size-control,
.dataTables_length {{
    display: inline-flex !important;
    align-items: center !important;
    white-space: nowrap !important;
    margin: 0 !important;
    padding: 0 !important;
    flex-shrink: 0 !important;
}}
.dataTables_length label {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    white-space: nowrap !important;
    margin: 0 !important;
    font-size: 12.5px !important;
    color: var(--text-secondary) !important;
    font-weight: 650 !important;
    line-height: 1 !important;
}}
.dataTables_length .select2-container {{
    margin: 0 2px !important;
    vertical-align: middle !important;
}}

/* 4. 消除 Windows 原生锐角复选框，重塑为主题开关 */
input[type="checkbox"] {{
    appearance: none !important;
    -webkit-appearance: none !important;
    width: 17px !important;
    height: 17px !important;
    border: 1.5px solid var(--line) !important;
    border-radius: 5px !important;
    background: var(--surface) !important;
    cursor: pointer !important;
    position: relative !important;
    display: inline-block !important;
    vertical-align: middle !important;
    margin: 0 4px 0 0 !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03) !important;
}}
input[type="checkbox"]:hover {{
    border-color: var(--primary) !important;
    background: var(--soft) !important;
}}
input[type="checkbox"]:checked {{
    background-color: var(--primary) !important;
    border-color: var(--primary) !important;
    box-shadow: 0 2px 8px rgba(var(--primary-rgb), 0.35) !important;
}}
input[type="checkbox"]:checked::after {{
    content: '' !important;
    position: absolute !important;
    left: 4.5px !important;
    top: 1.5px !important;
    width: 4.5px !important;
    height: 8.5px !important;
    border: solid #ffffff !important;
    border-width: 0 2.2px 2.2px 0 !important;
    transform: rotate(45deg) !important;
}}

/* 5. 消除 Windows 原生黑三角 details/summary，改造为优雅毛玻璃收折卡片 */
details summary {{
    list-style: none !important;
    cursor: pointer !important;
    user-select: none !important;
}}
details summary::-webkit-details-marker {{
    display: none !important;
}}
.notice-wrap {{
    background: var(--surface-glass) !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    margin-bottom: 18px !important;
    overflow: hidden !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
}}
.notice-wrap summary {{
    padding: 8px 18px !important;
    font-size: 13px !important;
    font-weight: 750 !important;
    color: var(--text-secondary) !important;
    background: var(--soft) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    transition: all 0.15s ease !important;
}}
.notice-wrap summary:hover {{
    color: var(--primary) !important;
}}
.notice-wrap summary::after {{
    content: '▾' !important;
    font-size: 13px !important;
    font-weight: 800 !important;
    color: var(--text-muted) !important;
    transition: transform 0.2s ease !important;
}}
.notice-wrap[open] summary::after {{
    transform: rotate(180deg) !important;
}}
.notice-wrap .disclaimer-inner,
.notice-wrap .sort-hint-inner {{
    padding: 12px 18px !important;
    border: none !important;
    background: transparent !important;
    font-size: 12.5px !important;
}}

/* 6. 全局文字选中与光标颜色 */
::selection {{
    background: rgba(var(--primary-rgb), 0.28) !important;
    color: var(--text) !important;
}}
input, textarea {{
    caret-color: var(--primary) !important;
}}

/* 7. DataTables Bootstrap 5 分页器全量深度主题化（彻底清除 Bootstrap 原生亮蓝 #0d6efd 与刺眼白块） */
.dataTables_wrapper .dataTables_paginate,
.dataTables_wrapper .dataTables_paginate.paging_simple_numbers {{
    float: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    margin: 22px auto 26px !important;
    width: 100% !important;
}}

/* 唯一的圆角胶囊容器 */
.dataTables_wrapper .pagination,
.pagination {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 4px !important;
    background: var(--surface-glass, var(--surface)) !important;
    padding: 5px 8px !important;
    border-radius: 999px !important;
    border: 1px solid var(--line) !important;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    backdrop-filter: blur(16px) saturate(160%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(160%) !important;
    margin: 0 auto !important;
    list-style: none !important;
}}

/* 清除 li 上的任何旧样式污染 */
.dataTables_wrapper .pagination .page-item,
.dataTables_wrapper .dataTables_paginate .paginate_button,
.dataTables_wrapper .dataTables_paginate.paging_simple_numbers .paginate_button,
.pagination .page-item {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    width: auto !important;
    min-width: unset !important;
    height: auto !important;
}}

/* 单个页码按钮与前进后退 */
.dataTables_wrapper .pagination .page-item .page-link,
.dataTables_wrapper .pagination .page-link,
.pagination .page-item .page-link {{
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: 34px !important;
    height: 34px !important;
    padding: 0 8px !important;
    border-radius: 999px !important;
    border: 1px solid transparent !important;
    background: transparent !important;
    color: var(--text-secondary) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    line-height: 1 !important;
    text-decoration: none !important;
    cursor: pointer !important;
    transition: all 0.16s ease !important;
    box-shadow: none !important;
    outline: none !important;
}}

/* 悬浮状态：柔和主题微光 */
.dataTables_wrapper .pagination .page-item:not(.active):not(.disabled) .page-link:hover,
.pagination .page-item:not(.active):not(.disabled) .page-link:hover {{
    background: var(--soft) !important;
    color: var(--primary) !important;
    border-color: rgba(var(--primary-rgb), 0.25) !important;
    transform: translateY(-1px) !important;
}}

/* 当前高亮页码：主题色实心圆润胶囊 */
.dataTables_wrapper .pagination .page-item.active .page-link,
.pagination .page-item.active .page-link,
.dataTables_wrapper .dataTables_paginate .paginate_button.current,
.dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {{
    background: var(--primary) !important;
    background-color: var(--primary) !important;
    color: #ffffff !important;
    border-color: var(--primary) !important;
    border-radius: 999px !important;
    font-weight: 800 !important;
    box-shadow: 0 3px 12px rgba(var(--primary-rgb), 0.38) !important;
    transform: scale(1.05) !important;
    z-index: 2 !important;
}}

/* 禁用状态 */
.dataTables_wrapper .pagination .page-item.disabled .page-link,
.pagination .page-item.disabled .page-link {{
    opacity: 0.28 !important;
    cursor: not-allowed !important;
    background: transparent !important;
    border-color: transparent !important;
    color: var(--text-muted) !important;
    pointer-events: none !important;
    box-shadow: none !important;
    transform: none !important;
}}

/* 省略号 */
.dataTables_wrapper .pagination .page-item.disabled .page-link[data-dt-idx="ellipsis"],
.dataTables_wrapper .pagination .ellipsis,
.pagination .page-item.disabled span.page-link {{
    min-width: 22px !important;
    padding: 0 2px !important;
    font-weight: 700 !important;
    color: var(--text-muted) !important;
    opacity: 0.55 !important;
    cursor: default !important;
    pointer-events: none !important;
}}

/* 前后翻页箭头 (‹ 与 ›) 强化显示 */
.dataTables_wrapper .pagination .page-item.previous .page-link,
.dataTables_wrapper .pagination .page-item.next .page-link,
.pagination .page-item.previous .page-link,
.pagination .page-item.next .page-link {{
    font-size: 19px !important;
    font-weight: 800 !important;
    line-height: 1 !important;
    min-width: 34px !important;
    height: 34px !important;
    padding: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: var(--text-secondary) !important;
}}
.dataTables_wrapper .pagination .page-item.previous:not(.disabled) .page-link:hover,
.dataTables_wrapper .pagination .page-item.next:not(.disabled) .page-link:hover {{
    background: var(--soft) !important;
    color: var(--primary) !important;
    border-color: rgba(var(--primary-rgb), 0.25) !important;
}}

/* 8. 悬浮窗模式三连胶囊 (介绍/趋势/评论) 触控美化 */
.mode-toggle {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    padding: 4px 11px !important;
    border-radius: 999px !important;
    border: 1.5px solid var(--line) !important;
    background: var(--surface) !important;
    color: var(--text-secondary) !important;
    font-size: 12px !important;
    font-weight: 750 !important;
    cursor: pointer !important;
    transition: all 0.16s ease !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.02) !important;
}}
.mode-toggle:hover {{
    border-color: var(--primary) !important;
    background: var(--soft) !important;
    color: var(--primary) !important;
}}
.mode-toggle input[type="checkbox"] {{
    width: 14px !important;
    height: 14px !important;
    margin: 0 !important;
}}


/* ═════════════════ 现代游戏模组包卡片全局精修 ═════════════════ */
.xyebbs-pack-card,
.bbsmc-pack-card,
.modrinth-pack-card,
.curseforge-pack-card,
.mcmod-pack-card {{
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    box-shadow: var(--shadow) !important;
    transition: transform 0.24s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.24s, border-color 0.24s !important;
}}
.xyebbs-pack-card:hover,
.bbsmc-pack-card:hover,
.modrinth-pack-card:hover,
.curseforge-pack-card:hover,
.mcmod-pack-card:hover {{
    transform: translateY(-5px) !important;
    box-shadow: var(--shadow-hover) !important;
}}
.xyebbs-card-cover,
.bbsmc-card-cover {{
    position: relative !important;
    width: 100% !important;
    aspect-ratio: 16 / 9 !important;
    background: #090d16 !important;
    overflow: hidden !important;
    display: block !important;
}}
.xyebbs-card-img,
.bbsmc-card-img {{
    width: 100% !important;
    height: 100% !important;
    object-fit: cover !important;
    transition: transform 0.35s ease !important;
}}
.xyebbs-pack-card:hover .xyebbs-card-img,
.bbsmc-pack-card:hover .bbsmc-card-img,
.modrinth-pack-card:hover .xyebbs-card-img,
.curseforge-pack-card:hover .xyebbs-card-img {{
    transform: scale(1.04) !important;
}}
.xyebbs-card-stats,
.bbsmc-card-stats {{
    position: absolute !important;
    left: 8px !important;
    bottom: 8px !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 3px 8px !important;
    background: rgba(9, 13, 22, 0.78) !important;
    color: #ffffff !important;
    font-size: 0.74rem !important;
    font-weight: 700 !important;
    border-radius: 6px !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}}
.xyebbs-card-ver-badge,
.bbsmc-card-ver-badge {{
    position: absolute !important;
    right: 8px !important;
    bottom: 8px !important;
    padding: 2.5px 7px !important;
    background: rgba(9, 13, 22, 0.82) !important;
    color: #ffffff !important;
    font-size: 0.74rem !important;
    font-weight: 750 !important;
    border-radius: 6px !important;
    backdrop-filter: blur(8px) !important;
    -webkit-backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}}
.xyebbs-card-body,
.bbsmc-card-body {{
    padding: 14px 16px !important;
    display: flex !important;
    flex-direction: column !important;
    flex: 1 !important;
}}
.xyebbs-card-title,
.bbsmc-card-title {{
    font-size: 0.98rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.015em !important;
    line-height: 1.4 !important;
    color: var(--text) !important;
    margin-bottom: 0.35rem !important;
    text-decoration: none !important;
}}
.xyebbs-card-title:hover,
.bbsmc-card-title:hover {{
    color: var(--primary) !important;
}}
.xyebbs-card-desc,
.bbsmc-card-desc {{
    font-size: 0.82rem !important;
    color: var(--text-secondary) !important;
    line-height: 1.55 !important;
    margin-bottom: 0.6rem !important;
}}


/* ═════════════════ 全局 Hero 专区与 Quick Pills ═════════════════ */
.quick-pills {{
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    margin-top: 14px !important;
}}
.quick-pill {{
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    padding: 5px 12px !important;
    background: var(--surface) !important;
    border: 1px solid var(--line) !important;
    border-radius: 999px !important;
    font-size: 12.5px !important;
    color: var(--text-secondary) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03) !important;
    transition: transform 0.15s, border-color 0.15s !important;
}}
.quick-pill:hover {{
    transform: translateY(-1px) !important;
    border-color: var(--primary) !important;
    color: var(--text) !important;
}}
.quick-pill b {{
    color: var(--text) !important;
    font-weight: 800 !important;
}}

</style>

    <!-- 本地解耦高性能数据源：离线秒开、零 DOM 阻塞 -->
    
    

</head>
<body>
<!-- 动画背景 -->
<div class="bg-layer"></div>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>

<div class="app-layout">
    <!-- 仅保活 DataTables Select2 多选解析引擎所需的底层隐藏标签，无任何冲突ID -->
    <div id="hiddenEngineSlots" style="display:none !important;" aria-hidden="true">
        <select id="categoryFilter" class="form-select" multiple="multiple" style="display:none;">
{cat_opts}
        </select>
        <select id="packTagFilter" class="form-select" multiple="multiple" style="display:none;">
{pack_opts}
        </select>
        <select id="modCategoryFilter" class="form-select" multiple="multiple" style="display:none;">
{mod_cat_opts}
        </select>
        <select id="modFilter" class="form-select" multiple="multiple" style="display:none;">
{mod_opts}
        </select>
    </div>

    <!-- 全宽沉浸式顶栏 Full-Width Sticky Navbar (现代游戏官网一体化) -->
    <header class="topbar">
        <div class="topbar-inner">
            <div class="topbar-left">
                <a href="#all" class="topbar-brand" onclick="switchPlatformTab('all'); return false;" title="返回全平台总览">
                    <span class="brand-cube">📦</span>
                    <span class="brand-title">我的世界整合包聚合</span>
                    <span class="brand-badge">PRO</span>
                </a>
            </div>

            <div class="topbar-center">
                <nav class="topbar-platform-nav" aria-label="全端聚合多平台导航">
                    <button type="button" class="top-plat-btn active" data-tab="all" id="topNavAll">
                        <span>🌐</span> 全平台总览 <span class="pnav-badge" id="topNavAllBadge">73,521</span>
                    </button>
                    <button type="button" class="top-plat-btn" data-tab="mcmod" id="topNavMcmod">
                        <span>📦</span> MC百科 <span class="pnav-badge" id="topNavMcmodBadge">1,484</span>
                    </button>
                    <button type="button" class="top-plat-btn" data-tab="bilibili" id="topNavBili">
                        <span>📺</span> B站自制 <span class="pnav-badge" id="topNavBiliBadge">935</span>
                    </button>
                    <button type="button" class="top-plat-btn" data-tab="bbsmc" id="topNavBbsmc">
                        <span>💎</span> BBSMC <span class="pnav-badge" id="topNavBbsmcBadge">1,802</span>
                    </button>
                    <button type="button" class="top-plat-btn" data-tab="xyebbs" id="topNavXyebbs">
                        <span>🍃</span> XYEBBS <span class="pnav-badge" id="topNavXyebbsBadge">5,175</span>
                    </button>
                    <button type="button" class="top-plat-btn" data-tab="modrinth" id="topNavModrinth">
                        <span>🌐</span> Modrinth <span class="pnav-badge" id="topNavModrinthBadge">18,328</span>
                    </button>
                    <button type="button" class="top-plat-btn" data-tab="curseforge" id="topNavCurseforge">
                        <span>🔥</span> CurseForge <span class="pnav-badge" id="topNavCurseforgeBadge">45,797</span>
                    </button>
                </nav>
            </div>

            <div class="topbar-actions">
                <!-- 抓取变动审计入口 -->
                <button type="button" class="top-action-btn" id="openAuditModalBtn" title="查看抓取变动与前后对比统计">📊 变动审计 <span class="badge" id="auditBadgeCount" style="display:none; background:#ef4444; color:#fff; border-radius:10px; font-size:10px; padding:0 5px; margin-left:2px;">0</span></button>
                <!-- 标签数量显隐独立开关 -->
                <button type="button" class="top-action-btn" id="toggleTagCountsBtn" title="切换所有标签后的数量显示与隐藏">🏷️ <span id="toggleTagCountsLabel">标签数量</span></button>
                <!-- 顶栏快捷主题微调 -->
                <div class="top-theme-pills" title="快速切换色彩主题">
                    <button type="button" class="top-tdot active" data-theme="eye" title="🌿 护眼森绿">🌿</button>
                    <button type="button" class="top-tdot" data-theme="dark" title="🌙 极夜暗黑">🌙</button>
                    <button type="button" class="top-tdot" data-theme="warm" title="☕ 温暖木质">☕</button>
                    <button type="button" class="top-tdot" data-theme="light" title="❄️ 冷白素雅">❄️</button>
                    <button type="button" class="top-tdot" data-theme="pink" title="🌸 樱粉霓光">🌸</button>
                </div>
            </div>
        </div>
    </header>

    <!-- 主区域 Main Content (1560px 黄金居中，单轴流视线) -->
    <main class="main-content">

        <!-- Hero 欢迎与宏观统计卡片 -->
        
        <!-- ═══════════════ [新增] 全平台综合总览视图 ═══════════════ -->
        <div id="view-all" class="tab-view active">
        <!-- 跨平台全局穿透联合搜索 (居顶命令中心) -->
        <div class="cross-search-section">
            <div class="csearch-top-row">
                <div class="csearch-title-group">
                    <span class="csearch-badge">全网穿透联合检索</span>
                    <h2 class="csearch-heading">跨平台全局极速搜索</h2>
                </div>
                <div class="csearch-platforms-hint">
                    <span class="cplat-pill" style="--cp-c:#f59e0b;">📦 MC百科</span>
                    <span class="cplat-pill" style="--cp-c:#fb7299;">📺 B站自制</span>
                    <span class="cplat-pill" style="--cp-c:#0284c7;">💎 BBSMC</span>
                    <span class="cplat-pill" style="--cp-c:#059669;">🍃 XYEBBS</span>
                    <span class="cplat-pill" style="--cp-c:#10b981;">🌐 Modrinth</span>
                    <span class="cplat-pill" style="--cp-c:#ea580c;">🔥 CurseForge</span>
                </div>
            </div>

            <!-- 搜索主输入框 -->
            <div class="cross-search-input-wrap">
                <span class="cross-search-icon">🔍</span>
                <input type="text" id="crossSearchInput" class="cross-search-input" placeholder="输入模组包名称、UP主/作者、玩法类型、模组名进行全网联合检索..." autocomplete="off">
                <button type="button" id="crossSearchClear" class="cross-search-clear" title="清空搜索 (Esc)" style="display:none;">✕</button>
                <div class="cross-search-kbd" title="快捷键聚焦搜索"><kbd>Ctrl</kbd> <kbd>K</kbd></div>
            </div>

            <!-- 热门快搜标签条 -->
            <div class="cross-hot-tags">
                <span class="hot-label">🔥 热门快搜：</span>
                <button type="button" class="hot-chip" data-query="RLCraft">RLCraft</button>
                <button type="button" class="hot-chip" data-query="机械动力">机械动力</button>
                <button type="button" class="hot-chip" data-query="脆骨症">脆骨症</button>
                <button type="button" class="hot-chip" data-query="Fabulously Optimized">极速提帧</button>
                <button type="button" class="hot-chip" data-query="低配光影">低配光影</button>
                <button type="button" class="hot-chip" data-query="拔刀剑">拔刀剑</button>
                <button type="button" class="hot-chip" data-query="宝可梦">宝可梦</button>
                <button type="button" class="hot-chip" data-query="空岛">空岛生存</button>
                <button type="button" class="hot-chip" data-query="All the Mods">ATM 终极大作</button>
            </div>

            <!-- 6 平台实时结果展开抽屉 (输入时展开，清空时收起) -->
            <div class="cross-results-grid" id="crossResultsGrid">
                <div class="cross-col" style="--col-theme: #f59e0b;">
                    <div class="cross-col-header">
                        <span>📦 MC百科 权威词条</span>
                        <a href="javascript:void(0)" onclick="jumpToPlatformWithCurrentSearch('mcmod')" class="col-more">查看全部 ➔</a>
                    </div>
                    <div id="crossMcmodResults"></div>
                </div>
                <div class="cross-col" style="--col-theme: #fb7299;">
                    <div class="cross-col-header">
                        <span>📺 B站自制 视频与直链</span>
                        <a href="javascript:void(0)" onclick="jumpToPlatformWithCurrentSearch('bilibili')" class="col-more">查看全部 ➔</a>
                    </div>
                    <div id="crossBiliResults"></div>
                </div>
                <div class="cross-col" style="--col-theme: #0284c7;">
                    <div class="cross-col-header">
                        <span>💎 BBSMC 优质开源库</span>
                        <a href="javascript:void(0)" onclick="jumpToPlatformWithCurrentSearch('bbsmc')" class="col-more">查看全部 ➔</a>
                    </div>
                    <div id="crossBbsmcResults"></div>
                </div>
                <div class="cross-col" style="--col-theme: #059669;">
                    <div class="cross-col-header">
                        <span>🍃 XYEBBS 像素世界</span>
                        <a href="javascript:void(0)" onclick="jumpToPlatformWithCurrentSearch('xyebbs')" class="col-more">查看全部 ➔</a>
                    </div>
                    <div id="crossXyebbsResults"></div>
                </div>
                <div class="cross-col" style="--col-theme: #10b981;">
                    <div class="cross-col-header">
                        <span>🌐 Modrinth 极速开源包</span>
                        <a href="javascript:void(0)" onclick="jumpToPlatformWithCurrentSearch('modrinth')" class="col-more">查看全部 ➔</a>
                    </div>
                    <div id="crossModrinthResults"></div>
                </div>
                <div class="cross-col" style="--col-theme: #ea580c;">
                    <div class="cross-col-header">
                        <span>🔥 CurseForge 热门大作</span>
                        <a href="javascript:void(0)" onclick="jumpToPlatformWithCurrentSearch('curseforge')" class="col-more">查看全部 ➔</a>
                    </div>
                    <div id="crossCurseforgeResults"></div>
                </div>
            </div>
        </div>

        <!-- 多平台实质内容门户矩阵 (注入热门代表作与快捷直达标签) -->
        <div class="all-platforms-grid">
            <!-- 1. MC百科看板卡片 -->
            <div class="platform-showcase-card" style="--card-accent: #f59e0b; --card-glow: rgba(245, 158, 11, 0.28);">
                <div class="showcase-header">
                    <div class="showcase-icon" style="background: rgba(245, 158, 11, 0.15); color: #d97706;">📦</div>
                    <div>
                        <h3 class="showcase-title">MC百科整合包看板</h3>
                        <span class="showcase-badge" style="background: rgba(245, 158, 11, 0.15); color: #d97706;">MCMOD.CN · 权威技术数据库</span>
                    </div>
                </div>
                <div class="showcase-metrics">
                    <div>
                        <div class="smetric-val">1,417 款</div>
                        <div class="smetric-lbl">整合包全收录</div>
                    </div>
                    <div>
                        <div class="smetric-val">1.25 亿</div>
                        <div class="smetric-lbl">总累计浏览</div>
                    </div>
                    <div>
                        <div class="smetric-val">双视图</div>
                        <div class="smetric-lbl">画廊 / 专业表格</div>
                    </div>
                </div>
                <!-- 热门代表作 TOP 3 -->
                <div class="showcase-featured-box">
                    <div class="showcase-box-header"><span>🔥 热门深度代表作</span><span>点击直达</span></div>
                    <div class="featured-item" onclick="jumpToMcmodSearch('脆骨症')" title="直达脆骨症详情与数据看板">
                        <span class="featured-rank">1</span>
                        <span class="featured-name">[NFWC] 脆骨症 (No Flesh Within Chest)</span>
                        <span class="featured-meta">272.4万浏览 · 96%好评</span>
                    </div>
                    <div class="featured-item" onclick="jumpToMcmodSearch('勇者之章')" title="直达勇者之章详情与数据看板">
                        <span class="featured-rank">2</span>
                        <span class="featured-name">[CY3] 勇者之章 Ⅲ (Chapter of Yuusha)</span>
                        <span class="featured-meta">207.5万浏览 · 魔法冒险</span>
                    </div>
                    <div class="featured-item" onclick="jumpToMcmodSearch('超现实')" title="直达超现实详情与数据看板">
                        <span class="featured-rank">3</span>
                        <span class="featured-name">[RLC] 超现实 x 虚拟生存 (RLCraft)</span>
                        <span class="featured-meta">177.5万浏览 · 极致硬核神作</span>
                    </div>
                </div>
                <!-- 快捷特色标签 -->
                <div class="showcase-tags-box">
                    <span class="showcase-tag-chip" onclick="jumpToMcmodSearch('硬核')">🏷️ 硬核魔改</span>
                    <span class="showcase-tag-chip" onclick="jumpToMcmodSearch('空岛')">☁️ 空岛生存</span>
                    <span class="showcase-tag-chip" onclick="jumpToMcmodSearch('科技')">⚙️ 科技制造</span>
                    <span class="showcase-tag-chip" onclick="jumpToMcmodSearch('魔法')">✨ 魔法神秘</span>
                </div>
                <button type="button" class="showcase-btn" style="background: linear-gradient(135deg, #f59e0b, #d97706);" onclick="switchPlatformTab('mcmod')">
                    🚀 进入 MC百科技术看板 ➔
                </button>
            </div>

            <!-- 2. 哔哩哔哩看板卡片 -->
            <div class="platform-showcase-card" style="--card-accent: #fb7299; --card-glow: rgba(251, 114, 153, 0.28);">
                <div class="showcase-header">
                    <div class="showcase-icon" style="background: rgba(251, 114, 153, 0.15); color: #fb7299;">📺</div>
                    <div>
                        <h3 class="showcase-title">哔哩哔哩自制发布流</h3>
                        <span class="showcase-badge" style="background: rgba(251, 114, 153, 0.15); color: #fb7299;">BILIBILI · UP主自制/首发/更新</span>
                    </div>
                </div>
                <div class="showcase-metrics">
                    <div>
                        <div class="smetric-val">935 款</div>
                        <div class="smetric-lbl">自制发布 (5,397流)</div>
                    </div>
                    <div>
                        <div class="smetric-val">1,780+ 条</div>
                        <div class="smetric-lbl">已析出网盘直链</div>
                    </div>
                    <div>
                        <div class="smetric-val">双模式</div>
                        <div class="smetric-lbl">同包聚合 / 视频流</div>
                    </div>
                </div>
                <!-- 热门代表作 TOP 3 -->
                <div class="showcase-featured-box">
                    <div class="showcase-box-header"><span>🔥 UP 主高热自制发布</span><span>点击直达</span></div>
                    <div class="featured-item" onclick="jumpToBiliSearch('异界生活')" title="直达异界生活幻想自制发布流">
                        <span class="featured-rank">1</span>
                        <span class="featured-name">【1.16.5】大型生活向：异界生活幻想 v1.3</span>
                        <span class="featured-meta">457.2万播放 · 史诗级大型生活向</span>
                    </div>
                    <div class="featured-item" onclick="jumpToBiliSearch('方可梦')" title="直达方可梦大师自制发布流">
                        <span class="featured-rank">2</span>
                        <span class="featured-name">去吧，方可梦大师 4.0 双版本</span>
                        <span class="featured-meta">262.9万播放 · 全Mega全图鉴</span>
                    </div>
                    <div class="featured-item" onclick="jumpToBiliSearch('愚者')" title="直达愚者自制发布流">
                        <span class="featured-rank">3</span>
                        <span class="featured-name">【1.20.1】愚者 (The Fool) 欺诈盛宴</span>
                        <span class="featured-meta">228.5万播放 · 深度扮演RPG</span>
                    </div>
                </div>
                <!-- 快捷特色标签 -->
                <div class="showcase-tags-box">
                    <span class="showcase-tag-chip" onclick="jumpToBiliSearch('宝可梦')">🐾 宝可梦</span>
                    <span class="showcase-tag-chip" onclick="jumpToBiliSearch('光影')">🌄 低配光影</span>
                    <span class="showcase-tag-chip" onclick="jumpToBiliSearch('生存')">💀 生存大作</span>
                    <span class="showcase-tag-chip" onclick="jumpToBiliSearch('网盘')">⚡ 直链网盘</span>
                </div>
                <button type="button" class="showcase-btn" style="background: linear-gradient(135deg, #fb7299, #e11d48);" onclick="switchPlatformTab('bilibili')">
                    🚀 进入 B站自制发布流 ➔
                </button>
            </div>

            <!-- 3. BBSMC 开放资源卡片 -->
            <div class="platform-showcase-card" style="--card-accent: #0284c7; --card-glow: rgba(2, 132, 199, 0.28);">
                <div class="showcase-header">
                    <div class="showcase-icon" style="background: rgba(2, 132, 199, 0.15); color: #0284c7;">💎</div>
                    <div>
                        <h3 class="showcase-title">BBSMC 开放资源专区</h3>
                        <span class="showcase-badge" style="background: rgba(2, 132, 199, 0.15); color: #0284c7;">BBSMC.NET · 优质开源模组包库</span>
                    </div>
                </div>
                <div class="showcase-metrics">
                    <div>
                        <div class="smetric-val">1,802 款</div>
                        <div class="smetric-lbl">整合包全收录</div>
                    </div>
                    <div>
                        <div class="smetric-val">1,710 万+</div>
                        <div class="smetric-lbl">总累计下载</div>
                    </div>
                    <div>
                        <div class="smetric-val">9,600+</div>
                        <div class="smetric-lbl">直链与网盘</div>
                    </div>
                </div>
                <!-- 热门代表作 TOP 3 -->
                <div class="showcase-featured-box">
                    <div class="showcase-box-header"><span>🔥 社区精选开放资源</span><span>点击直达</span></div>
                    <div class="featured-item" onclick="jumpToBbsmcSearch('乌托邦')" title="直达BBSMC乌托邦探险之旅">
                        <span class="featured-rank">1</span>
                        <span class="featured-name">[1.20.1] 乌托邦探险之旅 (Utopia)</span>
                        <span class="featured-meta">229.7万下载 · 社区霸榜榜首</span>
                    </div>
                    <div class="featured-item" onclick="jumpToBbsmcSearch('愚者')" title="直达BBSMC愚者整合包">
                        <span class="featured-rank">2</span>
                        <span class="featured-name">[1.20.1] 愚者 - The Fool (欺诈盛宴)</span>
                        <span class="featured-meta">162.8万下载 · 深度剧情扮演</span>
                    </div>
                    <div class="featured-item" onclick="jumpToBbsmcSearch('香草纪元')" title="直达BBSMC香草纪元整合包">
                        <span class="featured-rank">3</span>
                        <span class="featured-name">[1.20.1] 香草纪元:食旅纪行</span>
                        <span class="featured-meta">114.8万下载 · 唯美美食纪行</span>
                    </div>
                </div>
                <!-- 快捷特色标签 -->
                <div class="showcase-tags-box">
                    <span class="showcase-tag-chip" onclick="jumpToBbsmcSearch('机械动力')">⚙️ 机械动力</span>
                    <span class="showcase-tag-chip" onclick="jumpToBbsmcSearch('RPG')">⚔️ RPG冒险</span>
                    <span class="showcase-tag-chip" onclick="jumpToBbsmcSearch('1.20.1')">📦 1.20.1</span>
                    <span class="showcase-tag-chip" onclick="jumpToBbsmcSearch('冒险')">🗺️ 探险冒险</span>
                </div>
                <button type="button" class="showcase-btn" style="background: linear-gradient(135deg, #0284c7, #0369a1);" onclick="switchPlatformTab('bbsmc')">
                    🚀 进入 BBSMC 开放资源专区 ➔
                </button>
            </div>

            <!-- 4. XYEBBS 像素世界看板卡片 -->
            <div class="platform-showcase-card" style="--card-accent: #059669; --card-glow: rgba(5, 150, 105, 0.28);">
                <div class="showcase-header">
                    <div class="showcase-icon" style="background: rgba(5, 150, 105, 0.15); color: #059669;">🍃</div>
                    <div>
                        <h3 class="showcase-title">XYEBBS 像素世界专区</h3>
                        <span class="showcase-badge" style="background: rgba(5, 150, 105, 0.15); color: #059669;">XYEBBS.COM · 综合社区资源库</span>
                    </div>
                </div>
                <div class="showcase-metrics">
                    <div>
                        <div class="smetric-val">5,175 款</div>
                        <div class="smetric-lbl">整合包全收录</div>
                    </div>
                    <div>
                        <div class="smetric-val">580 万+</div>
                        <div class="smetric-lbl">总累计下载</div>
                    </div>
                    <div>
                        <div class="smetric-val">3 亿+</div>
                        <div class="smetric-lbl">社区累计浏览</div>
                    </div>
                </div>
                <!-- 热门代表作 TOP 3 -->
                <div class="showcase-featured-box">
                    <div class="showcase-box-header"><span>🔥 论坛热帖与精选整合</span><span>点击直达</span></div>
                    <div class="featured-item" onclick="jumpToXyebbsSearch('魔之逆鳞')" title="直达XYEBBS魔之逆鳞整合包">
                        <span class="featured-rank">1</span>
                        <span class="featured-name">[1.20.1] 魔之逆鳞-(Nemesis of Demons)</span>
                        <span class="featured-meta">34.6万下载 · 97.6万浏览</span>
                    </div>
                    <div class="featured-item" onclick="jumpToXyebbsSearch('香草纪元')" title="直达XYEBBS香草纪元整合包">
                        <span class="featured-rank">2</span>
                        <span class="featured-name">[1.20.1] 香草纪元:食旅纪行</span>
                        <span class="featured-meta">28.7万下载 · 76.2万浏览</span>
                    </div>
                    <div class="featured-item" onclick="jumpToXyebbsSearch('乌托邦')" title="直达XYEBBS乌托邦探险之旅">
                        <span class="featured-rank">3</span>
                        <span class="featured-name">[1.20.1] 乌托邦探险之旅</span>
                        <span class="featured-meta">27.5万下载 · 23.7万浏览</span>
                    </div>
                </div>
                <!-- 快捷特色标签 -->
                <div class="showcase-tags-box">
                    <span class="showcase-tag-chip" onclick="jumpToXyebbsSearch('拔刀')">🗡️ 拔刀剑</span>
                    <span class="showcase-tag-chip" onclick="jumpToXyebbsSearch('工业')">🏭 工业时代</span>
                    <span class="showcase-tag-chip" onclick="jumpToXyebbsSearch('汉化')">🀄 深度汉化</span>
                    <span class="showcase-tag-chip" onclick="jumpToXyebbsSearch('冒险')">🧭 冒险探索</span>
                </div>
                <button type="button" class="showcase-btn" style="background: linear-gradient(135deg, #059669, #047857);" onclick="switchPlatformTab('xyebbs')">
                    🚀 进入 XYEBBS 像素世界 ➔
                </button>
            </div>

            <!-- 5. Modrinth 国际服开源看板卡片 -->
            <div class="platform-showcase-card" style="--card-accent: #10b981; --card-glow: rgba(16, 185, 129, 0.28);">
                <div class="showcase-header">
                    <div class="showcase-icon" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">🌐</div>
                    <div>
                        <h3 class="showcase-title">Modrinth 开源专区</h3>
                        <span class="showcase-badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981;">MODRINTH.COM · 极速开源生态</span>
                    </div>
                </div>
                <div class="showcase-metrics">
                    <div>
                        <div class="smetric-val">18,328 款</div>
                        <div class="smetric-lbl">开源包全收录</div>
                    </div>
                    <div>
                        <div class="smetric-val">1.76 亿+</div>
                        <div class="smetric-lbl">总累计下载</div>
                    </div>
                    <div>
                        <div class="smetric-val">全量直链</div>
                        <div class="smetric-lbl">CDN 官方极速分发</div>
                    </div>
                </div>
                <!-- 热门代表作 TOP 3 -->
                <div class="showcase-featured-box">
                    <div class="showcase-box-header"><span>🔥 全球顶级开源标杆</span><span>点击直达</span></div>
                    <div class="featured-item" onclick="jumpToModrinthSearch('Fabulously Optimized')" title="直达Fabulously Optimized详情">
                        <span class="featured-rank">1</span>
                        <span class="featured-name">Fabulously Optimized (极致轻量提帧)</span>
                        <span class="featured-meta">1,712万+ 下 · 原版增强</span>
                    </div>
                    <div class="featured-item" onclick="jumpToModrinthSearch('Zombie Invade')" title="直达Zombie Invade详情">
                        <span class="featured-rank">2</span>
                        <span class="featured-name">Zombie Invade 100 Days (丧尸围城百天)</span>
                        <span class="featured-meta">1,429万+ 下 · 生存挑战</span>
                    </div>
                    <div class="featured-item" onclick="jumpToModrinthSearch('Cobblemon')" title="直达Cobblemon详情">
                        <span class="featured-rank">3</span>
                        <span class="featured-name">Cobblemon Official Modpack (宝可梦)</span>
                        <span class="featured-meta">1,054万+ 下 · 开源大作</span>
                    </div>
                </div>
                <!-- 快捷特色标签 -->
                <div class="showcase-tags-box">
                    <span class="showcase-tag-chip" onclick="jumpToModrinthSearch('Optimized')">🚀 FPS极致优化</span>
                    <span class="showcase-tag-chip" onclick="jumpToModrinthSearch('Fabric')">🧵 Fabric</span>
                    <span class="showcase-tag-chip" onclick="jumpToModrinthSearch('NeoForge')">⚡ NeoForge</span>
                    <span class="showcase-tag-chip" onclick="jumpToModrinthSearch('Multiplayer')">🌐 联机友好</span>
                </div>
                <button type="button" class="showcase-btn" style="background: linear-gradient(135deg, #10b981, #059669);" onclick="switchPlatformTab('modrinth')">
                    🚀 进入 Modrinth 开源专区 ➔
                </button>
            </div>

            <!-- 6. CurseForge 国际服大作看板卡片 -->
            <div class="platform-showcase-card" style="--card-accent: #ea580c; --card-glow: rgba(234, 88, 12, 0.28);">
                <div class="showcase-header">
                    <div class="showcase-icon" style="background: rgba(234, 88, 12, 0.15); color: #ea580c;">🔥</div>
                    <div>
                        <h3 class="showcase-title">CurseForge 热门大作专区</h3>
                        <span class="showcase-badge" style="background: rgba(234, 88, 12, 0.15); color: #ea580c;">CURSEFORGE.COM · 全球最大模组生态</span>
                    </div>
                </div>
                <div class="showcase-metrics">
                    <div>
                        <div class="smetric-val">45,797 款</div>
                        <div class="smetric-lbl">热门大作全收录</div>
                    </div>
                    <div>
                        <div class="smetric-val">8.45 亿+</div>
                        <div class="smetric-lbl">总累计下载</div>
                    </div>
                    <div>
                        <div class="smetric-val">全版本覆盖</div>
                        <div class="smetric-lbl">1.7.10 ~ 1.21.x</div>
                    </div>
                </div>
                <!-- 热门代表作 TOP 3 -->
                <div class="showcase-featured-box">
                    <div class="showcase-box-header"><span>🔥 全球殿堂级大作 TOP</span><span>点击直达</span></div>
                    <div class="featured-item" onclick="jumpToCurseforgeSearch('RLCraft')" title="直达RLCraft详情">
                        <span class="featured-rank">1</span>
                        <span class="featured-name">RLCraft (全球第一硬核神作)</span>
                        <span class="featured-meta">3,010万+ 下 · 极限硬核</span>
                    </div>
                    <div class="featured-item" onclick="jumpToCurseforgeSearch('All the Mods')" title="直达ATM全家桶详情">
                        <span class="featured-rank">2</span>
                        <span class="featured-name">All the Mods 10 (ATM 终极全家桶)</span>
                        <span class="featured-meta">2,164万+ 下 · 全模组</span>
                    </div>
                    <div class="featured-item" onclick="jumpToCurseforgeSearch('Pixelmon')" title="直达Pixelmon详情">
                        <span class="featured-rank">3</span>
                        <span class="featured-name">The Pixelmon Modpack (宝可梦殿堂整合)</span>
                        <span class="featured-meta">2,009万+ 下 · 探索冒险</span>
                    </div>
                </div>
                <!-- 快捷特色标签 -->
                <div class="showcase-tags-box">
                    <span class="showcase-tag-chip" onclick="jumpToCurseforgeSearch('All the Mods')">🍱 大型全家桶</span>
                    <span class="showcase-tag-chip" onclick="jumpToCurseforgeSearch('Quest')">📜 任务驱动</span>
                    <span class="showcase-tag-chip" onclick="jumpToCurseforgeSearch('RPG')">🛡️ 探索与RPG</span>
                    <span class="showcase-tag-chip" onclick="jumpToCurseforgeSearch('Skyblock')">☁️ 空岛科技</span>
                </div>
                <button type="button" class="showcase-btn" style="background: linear-gradient(135deg, #ea580c, #c2410c);" onclick="switchPlatformTab('curseforge')">
                    🚀 进入 CurseForge 热门专区 ➔
                </button>
            </div>
        </div>
    </div>

<div id="view-mcmod" class="tab-view" style="display:none;">

    <!-- 📦 MC百科专属频道 Header (一体化微缩指标，告别千篇一律大 Hero) -->
    <div class="channel-hero mcmod-channel-hero">
        <div class="channel-hero-left">
            <span class="channel-badge-tag">MCMOD.CN · 权威技术资料库</span>
            <h2 class="channel-title">📦 MC百科整合包技术看板</h2>
            <p class="channel-desc">专注 MC百科 1,417 款模组包深度行情追踪、60日指数波动走势、模组依赖展开抽屉与官方历史改动对比</p>
        </div>
        <div class="channel-quick-stats">
            <div class="cstat-item"><span class="cs-num" id="statTotal">{total}</span><span class="cs-lbl">收录整合包</span></div>
            <div class="cstat-item"><span class="cs-num" id="statViews">{total_views}</span><span class="cs-lbl">总累计浏览</span></div>
            <div class="cstat-item"><span class="cs-num" id="statComments">{total_comments}</span><span class="cs-lbl">总社区评论</span></div>
            <div class="cstat-item"><span class="cs-num">100%</span><span class="cs-lbl">改动对比直达</span></div>
        </div>
    </div>
<details class="notice-wrap notice-compact">
    <summary>ℹ️ 说明与免责声明</summary>
    <div class="disclaimer-inner" style="margin-bottom:0.55rem;">
        <strong>📋 免责声明</strong><br>
        本页面仅为个人整理与学习交流用途，不涉及任何商业用途。排序、热度等数据均基于公开信息整理或统计，<strong>仅供参考，不代表任何作品或作者的实际质量评价，也不构成排名高低优劣的结论。</strong>如涉及版权、数据使用或其他权益问题，请联系我处理，我会第一时间修改或删除相关内容。本项目与<a href="https://www.mcmod.cn/" target="_blank">MC百科</a>（mcmod.cn）及相关作者无官方关联。
    </div>
    <div class="sort-hint-inner">
        <span style="font-size:1rem;">💡</span>单文件离线版 · 双击即可打开
        <span><b>排序：</b>点击表头排序，再次点击切换 ↑升序 / ↓降序，蓝色条内的小项可直接切换同组排序。<b>详情：</b>整合包名称悬停查看介绍；趋势列小波形可直接读日期/指数，默认点击趋势格打开或关闭大图，可开启悬浮模式；评论列默认点击打开或关闭详情，也可开启悬浮模式。<b>筛选：</b>分类、标签、模组分类和模组可多选，也可开启「排除所选」反向筛选；分页可切换每页 25 / 50 / 100 / 200 条。</span>
    </div>
</details>
<div class="main-wrap">
    <!-- 视线中央：MC百科多维一体化控制台 -->
    <div class="central-hub" id="mcmodCentralHub">
        <!-- 1. 搜索与核心动作 -->
        <div class="hub-tier-search">
            <div class="hub-stat-badge">
                <span>📦</span>
                <span>匹配 <strong id="mcmodMatchedCount">1,417</strong> 款整合包</span>
            </div>
            <div class="hub-search-box">
                <span class="hub-search-icon">🔍</span>
                <input type="text" id="mcmodUnifiedSearch" class="hub-search-input" placeholder="输入名称、模组名、作者或玩法标签实时穿透速搜..." autocomplete="off">
                <button type="button" id="mcmodSearchClear" class="hub-clear-btn" style="display:none;" title="清空搜索">✕</button>
            </div>
            <div class="hub-actions-cluster">
                <select id="typeFilter" class="hub-select select2-hub" title="按整合包类型筛选">
{type_opts}
                </select>
                <select id="trendFilter" class="hub-select select2-hub" title="按走势周期筛选">
{trend_opts}
                </select>
                <select id="hubPageSize" class="hub-select select2-hub" title="每页显示条数">
                    <option value="25" selected>每页 25 条 ▾</option>
                    <option value="50">每页 50 条 ▾</option>
                    <option value="100">每页 100 条 ▾</option>
                    <option value="99999">全部展示 ▾</option>
                </select>
                <div class="view-mode-toggle" id="mcmodViewToggle" style="margin:0;">
                    <button type="button" class="vmode-btn" data-vmode="cards" title="画廊卡片视图">🎨 画廊</button>
                    <button type="button" class="vmode-btn active" data-vmode="table" title="专业表格视图">📊 表格</button>
                </div>
                <button type="button" id="sidebarResetFilters" class="hub-reset-btn" title="一键重置所有MC百科筛选">
                    <span>↺</span> 重置
                </button>
            </div>
        </div>

        <!-- 2. 分类与标签维度 (官方专区 + 核心标签 + 模组分类 + 包含模组) -->
        <div class="hub-tier-filters">
            <!-- 官方权威主分类 -->
            <div class="hub-filter-row">
                <span class="hub-filter-label">🏷️ 官方专区：</span>
                <div class="hub-chips-wrap" id="mcmodCategoryChips"></div>
            </div>

            <!-- 核心玩法标签 (带展开全部和全部标签/多选) -->
            <div class="hub-filter-row discovery-row">
                <span class="hub-filter-label">🔥 核心标签：</span>
                <div class="hub-chips-wrap" id="mcmodTagChips"></div>
                <div class="discovery-actions">
                    <button type="button" id="expandTags" class="discovery-btn" aria-expanded="false" title="在当前行展开或收起全部标签">展开全部 ↓</button>
                    <button type="button" id="allTags" class="discovery-btn discovery-btn-primary" title="打开全部标签弹窗支持搜索与多选">全部标签 / 多选 ↗</button>
                </div>
            </div>

            <!-- 模组分类 (科技、冒险、农业、装饰、实用、辅助、魔改、LIB、魔法...) -->
            <div class="hub-filter-row">
                <span class="hub-filter-label">📦 模组分类：</span>
                <div class="hub-chips-wrap" id="mcmodModCatChips"></div>
            </div>

            <!-- 包含模组 (带热门模组胶囊、展开热门、全部模组多选搜索) -->
            <div class="hub-filter-row discovery-row">
                <span class="hub-filter-label">🧩 包含模组：</span>
                <div class="hub-chips-wrap" id="mcmodHotModChips"></div>
                <div class="discovery-actions">
                    <button type="button" id="expandMods" class="discovery-btn" aria-expanded="false" title="展开/收起常用高频模组快捷筛选，如需搜索全部1.1万款模组请点击右侧按钮">常用模组(前60) ▾</button>
                    <button type="button" id="allMods" class="discovery-btn discovery-btn-primary" title="打开全量 1.1 万款模组检索弹窗支持搜索与多选">全部模组 / 搜索多选 ↗</button>
                </div>
            </div>
        </div>

        <!-- 3. 已激活筛选指示栏 (参考黄游 active-filters) -->
        <div id="activeFilters" class="active-filters-bar" style="display:none;"></div>

        <!-- 3. 高阶参数与悬浮设置 -->
        <div class="hub-tier-advanced">
            <div class="hub-adv-group">
                <span style="font-weight:750; color:var(--text-secondary);">⚙️ 高阶过滤：</span>
                <label class="hub-exclude-toggle" title="开启后，选中的分类将作为排除项进行反向过滤">
                    <input type="checkbox" id="categoryExclude">
                    <span>反向排除模式</span>
                </label>
            </div>
            <div class="hub-adv-group">
                <span style="font-weight:750; color:var(--text-secondary);">👁️ 悬浮窗模式：</span>
                <div class="hub-hover-switches">
                    <label class="mode-toggle" title="开启后悬停整合包名称显示介绍；关闭后点击打开"><span>介绍</span><input type="checkbox" class="js-desc-hover-toggle"></label>
                    <label class="mode-toggle" title="开启后悬停趋势格显示趋势图；关闭后点击打开"><span>趋势</span><input type="checkbox" class="js-trend-hover-toggle"></label>
                    <label class="mode-toggle" title="开启后悬停评论格显示评论详情；关闭后点击打开"><span>评论</span><input type="checkbox" class="js-comment-hover-toggle"></label>
                </div>
            </div>
        </div>
    </div>
    <div class="table-card">
        <div class="table-responsive">
            <table id="modpackTable" class="table table-hover align-middle" style="width:100%">
                <thead>
                    <tr>
                        <th class="header-consolidated" style="min-width:220px">
                            <div class="header-sort-switcher title-sort-switcher" data-col="0">
                                <span class="sort-option active" data-subkey="name">名称</span>
                                <span class="sort-option" data-subkey="views">浏览</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:170px">
                            <div class="header-sort-switcher" data-col="1">
                                <span class="sort-option active" data-subkey="score">流行</span>
                                <span class="sort-option" data-subkey="lat">最新</span>
                                <span class="sort-option" data-subkey="max">最高</span>
                                <span class="sort-option" data-subkey="avg">平均</span>
                                <span class="sort-option" data-subkey="days">天数</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:140px">
                            <div class="header-sort-switcher" data-col="2">
                                <span class="sort-option active" data-subkey="t7">7日</span>
                                <span class="sort-option" data-subkey="t30">30日</span>
                                <span class="sort-option" data-subkey="t60">60日</span>
                                <span class="sort-option" data-subkey="tall">总幅</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:140px">
                            <div class="header-sort-switcher" data-col="3">
                                <span class="sort-option active" data-subkey="rv">红票</span>
                                <span class="sort-option" data-subkey="rp">红占比</span>
                                <span class="sort-option" data-subkey="bv">黑票</span>
                                <span class="sort-option" data-subkey="bp">黑占比</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:132px">
                            <div class="header-sort-switcher" data-col="4">
                                <span class="sort-option active" data-subkey="com">评论</span>
                                <span class="sort-option" data-subkey="rec">推荐</span>
                                <span class="sort-option" data-subkey="fav">收藏</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:280px">
                            <div class="header-sort-switcher" data-col="5">
                                <span class="sort-option active" data-subkey="count">标签</span>
                            </div>
                        </th>
                        <th class="header-consolidated" style="min-width:420px;width:38vw">
                            <div class="header-sort-switcher" data-col="6">
                                <span class="sort-option active" data-subkey="count">包含模组</span>
                            </div>
                        </th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
    </div>
</div>
        <!-- MC百科画廊卡片容器 (Cards Gallery) -->
        <div id="mcmodCardsContainer" style="display:none; margin-top: 18px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin:14px 0 10px;">
                <div style="font-size:0.85rem; color:var(--text-secondary);">
                    画廊卡片视图 · 当前匹配 <strong id="mcmodCardCountBadge">1,484 款</strong>
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted);">
                    点击卡片标题直接跳转原站 · 点击“📜 改动对比”查看历史正文变动
                </div>
            </div>
            <div id="mcmodCardsGrid" class="mcmod-cards-grid"></div>
        </div>

<div id="compareTray" class="compare-tray" aria-live="polite">
    <div class="compare-tray-glow"></div>
    <div class="compare-tray-main">
        <span class="compare-tray-kicker">收藏对比</span>
        <strong id="compareTrayCount">0 个整合包</strong>
        <div id="compareTrayNames" class="compare-tray-names"></div>
    </div>
    <div class="compare-tray-actions">
        <button type="button" id="compareClear" class="compare-ghost-btn">清空</button>
        <button type="button" id="compareOpen" class="compare-primary-btn">全面对比</button>
    </div>
</div>
<div id="compareOverlay" class="compare-overlay" aria-hidden="true">
    <div class="compare-shell" role="dialog" aria-modal="true" aria-labelledby="compareTitle">
        <div class="compare-head">
            <div>
                <span class="compare-kicker">Modpack Intelligence</span>
                <h2 id="compareTitle">收藏整合包全面对比</h2>
            </div>
            <div class="compare-head-actions">
                <button type="button" id="compareCopy" class="compare-ghost-btn">复制摘要</button>
                <button type="button" id="compareClose" class="compare-close-btn" aria-label="关闭">✕</button>
            </div>
        </div>
        <div id="compareBody" class="compare-body"></div>
    </div>
</div>
</div>
<!-- ─── 整合包介绍预览窗 ─── -->
<div id="pvPopup" class="pv-popup" role="dialog" aria-hidden="true">
    <div class="pv-head">
        <div class="pv-head-icon">📦</div>
        <span class="pv-head-title" id="pvTitle"></span>
        <div class="pv-actions">
            <a id="pvOpen" href="#" target="_blank" title="在新标签页打开 ↗">↗</a>
            <button type="button" class="hover-close" id="pvClose" title="关闭，短时间内不再弹出这个整合包">✕</button>
        </div>
    </div>
    <div class="pv-body" id="pvBody"></div>
    <div class="pv-tip" style="line-height:1.6;">
        📋 本页面仅作信息整理预览，含已抓取图片预览但不保证完整排版 · 鼠标移出会正常关闭且不进入冷却 · 点 ✕ 后 5 秒内悬停同一整合包不会再弹出 · 详细内容请访问 <a href="https://www.mcmod.cn/" target="_blank" style="color:var(--primary-dark);font-weight:600;">MC百科 mcmod.cn</a> 原页面查看
    </div>
    <div class="mcmod-consent">
        <div class="mcmod-consent-panel">
            <div class="mcmod-consent-brand">MC百科</div>
            <div class="mcmod-consent-title">内容来自 mcmod.cn 公开页面</div>
            <div class="mcmod-consent-text">这里显示的是本地整理预览，图片为已抓取链接预览，完整排版与最新修订请以 MC百科 原页面为准。确认后继续查看介绍内容。</div>
            <button type="button" class="mcmod-consent-ok">知道了</button>
        </div>
    </div>
</div>
<!-- ─── 评论悬浮窗 ─── -->
<div id="commentPopup" class="comment-popup">
    <div class="comment-head">
        <div class="comment-head-icon">💬</div>
        <span class="comment-head-title">评论详情</span>
        <input id="commentSearchInput" class="comment-search-input" type="search" placeholder="搜索当前整合包的评论内容" autocomplete="off">
        <span id="commentCount"></span>
        <div class="pv-actions">
            <a id="commentOpen" href="#" target="_blank" title="打开 MC百科原页面 ↗">↗</a>
            <button type="button" class="hover-close" id="commentClose" title="关闭评论详情">✕</button>
        </div>
    </div>
    <div class="comment-body" id="commentBody"></div>
    <div class="scroll-hint-arrow"><span>滚动查看更多</span> ↓</div>
    <div class="comment-search-nav" id="commentSearchNav" style="display:none;">
        <span class="search-nav-info" id="searchNavInfo"></span>
        <span class="search-nav-btn" id="searchNavPrev" title="上一个匹配">上一个匹配</span>
        <span class="search-nav-btn" id="searchNavNext" title="下一个匹配">下一个匹配</span>
    </div>
    <div class="comment-page-bar" id="commentPageBar" style="display:none;">
        <span class="comment-page-btn" id="cmtFirst" title="第一页">«</span>
        <span class="comment-page-btn" id="cmtPrev" title="上一页">‹</span>
        <span class="comment-page-info" id="cmtPageInfo"></span>
        <span class="comment-page-btn" id="cmtNext" title="下一页">›</span>
        <span class="comment-page-btn" id="cmtLast" title="最后一页">»</span>
    </div>
    <div class="comment-tip">
        ⚠️ 当前仍在补抓评论，评论不完整属于正常情况 · 按 Esc、点窗外或点评论格可关闭 · 完整内容请访问 <a href="https://www.mcmod.cn/" target="_blank" id="commentModpackLink">MC百科 mcmod.cn</a>
    </div>
    <div class="mcmod-consent">
        <div class="mcmod-consent-panel">
            <div class="mcmod-consent-brand">MC百科</div>
            <div class="mcmod-consent-title">评论来自 mcmod.cn 公开页面</div>
            <div class="mcmod-consent-text">评论仅作整理与检索辅助，完整上下文请以 MC百科原页面为准。确认后继续查看评论。</div>
            <button type="button" class="mcmod-consent-ok">知道了</button>
        </div>
    </div>
</div>
</div> <!-- /#view-mcmod -->

<!-- ═══════════════ B站自制整合包发布独立视图 ═══════════════ -->
<div id="view-bilibili" class="tab-view" style="display:none;">

    <!-- 📺 哔哩哔哩专属频道 Header (告别千篇一律大 Hero) -->
    <div class="channel-hero bili-channel-hero">
        <div class="channel-hero-left">
            <span class="channel-badge-tag" style="background: rgba(251, 114, 153, 0.15); color: #fb7299; border-color: rgba(251, 114, 153, 0.3);">BILIBILI · 自制整合包发布流</span>
            <h2 class="channel-title">📺 哔哩哔哩自制整合包发布流</h2>
            <p class="channel-desc">汇聚 B站 UP 主首发与更新作品 · 智能同包多版本聚合 · 网盘直达链接与提取码 · 8维互动排序 · 视频字幕速读</p>
        </div>
        <div class="channel-quick-stats">
            <div class="cstat-item"><span class="cs-num" id="biliStatTotal">935 款</span><span class="cs-lbl">独立整合包</span></div>
            <div class="cstat-item"><span class="cs-num" id="biliStatViews">584.8万+</span><span class="cs-lbl">视频总播放</span></div>
            <div class="cstat-item"><span class="cs-num" id="biliStatLinks">1,782+ 个</span><span class="cs-lbl">解析网盘直链</span></div>
            <div class="cstat-item"><span class="cs-num" id="biliStatGroups">70 个</span><span class="cs-lbl">玩家交流群</span></div>
        </div>
    </div>

    <div class="bili-view-wrap">
        <!-- 视线中央：B站自制多维一体化控制台 -->
        <div class="central-hub" id="biliCentralHub">
            <!-- 1. 搜索与核心动作 -->
            <div class="hub-tier-search">
                <div class="hub-stat-badge">
                    <span style="color:#fb7299;">📺</span>
                    <span id="biliMatchInfo">正在展示 B站精选整合包...</span>
                </div>
                <div class="hub-search-box">
                    <span class="hub-search-icon">🔍</span>
                    <input type="text" id="biliSearchInput" class="hub-search-input" placeholder="输入名称、UP主、版本、模组或网盘实时速搜..." autocomplete="off">
                    <button type="button" id="biliSearchClear" class="hub-clear-btn" style="display:none;" title="清空搜索">✕</button>
                </div>
                <div class="hub-actions-cluster">
                    <select id="biliSortSelect" class="hub-select select2-hub" title="排序规则">
                        <option value="pubdate_desc">最新发布 ↓</option>
                        <option value="views_desc">播放最多 ↓</option>
                        <option value="likes_desc">点赞最多 ↓</option>
                        <option value="favs_desc">收藏最多 ↓</option>
                        <option value="coins_desc">投币最多 ↓</option>
                        <option value="share_desc">分享最多 ↓</option>
                        <option value="reply_desc">评论最多 ↓</option>
                        <option value="danmaku_desc">弹幕最多 ↓</option>
                    </select>
                    <select id="biliVerSelect" class="hub-select select2-hub" title="按MC版本筛选">
                        <option value="">全部 MC 版本</option>
                    </select>
                    <select id="biliLoaderSelect" class="hub-select select2-hub" title="按模组加载器筛选">
                        <option value="">全部加载器</option>
                        <option value="Fabric">Fabric</option>
                        <option value="Forge">Forge</option>
                        <option value="NeoForge">NeoForge</option>
                        <option value="Quilt">Quilt</option>
                    </select>
                    <div class="bili-mode-toggle" id="biliViewToggle" style="margin:0; display:flex; gap:6px;">
                        <button type="button" class="bili-mode-btn active" data-mode="grouped" data-bmode="grouped" title="同名整合包自动归并，折叠历史版本">
                            ✨ 同包聚合
                        </button>
                        <button type="button" class="bili-mode-btn" data-mode="flat" data-bmode="flat" title="平铺展示每一条独立视频">
                            📋 视频平铺
                        </button>
                    </div>
                    <button type="button" id="sidebarBiliReset" class="hub-reset-btn" title="一键重置所有B站筛选">
                        <span>↺</span> 重置
                    </button>
                </div>
            </div>

            <!-- 2. 玩法与网盘与发布时间 -->
            <div class="hub-tier-filters">
                <div class="hub-filter-row">
                    <span class="hub-filter-label">🏷️ 玩法专区：</span>
                    <div class="hub-chips-wrap" id="biliCategoryChips"></div>
                </div>

                <div class="hub-filter-row">
                    <span class="hub-filter-label">💾 网盘渠道：</span>
                    <div class="hub-chips-wrap" id="biliPanChips">
                        <span class="s-chip active" data-pan="">全部网盘</span>
                        <span class="s-chip" data-pan="百度">百度网盘</span>
                        <span class="s-chip" data-pan="夸克">夸克网盘</span>
                        <span class="s-chip" data-pan="蓝奏">蓝奏云</span>
                        <span class="s-chip" data-pan="123">123云盘</span>
                    </div>
                </div>

                <div class="hub-filter-row">
                    <span class="hub-filter-label">📅 发布时间：</span>
                    <div class="hub-chips-wrap" id="biliDateChips"></div>
                </div>
            </div>

            <!-- 高阶过滤与悬浮设置（向 MCMod 看齐） -->
            <div class="hub-tier-advanced">
                <div class="hub-adv-group">
                    <span style="font-weight:750; color:var(--text-secondary);">⚙️ 高阶过滤：</span>
                    <label class="hub-exclude-toggle" title="开启后，选中的分类将作为排除项进行反向过滤">
                        <input type="checkbox" class="js-cat-exclude" data-plat="bilibili">
                        <span>反向排除模式</span>
                    </label>
                </div>
                <div class="hub-adv-group">
                    <span style="font-weight:750; color:var(--text-secondary);">👁️ 悬浮窗模式：</span>
                    <div class="hub-hover-switches">
                        <label class="mode-toggle" title="开启后悬停整合包名称显示介绍；关闭后点击打开"><span>介绍</span><input type="checkbox" class="js-desc-hover-toggle"></label>
                    </div>
                </div>
            </div>
        </div>

        <!-- 活动过滤项标签条 (Active Filters Bar - 仅在用户筛选时显示) -->
        <div class="active-filters-bar" id="biliActiveFilters" style="display:none; margin-bottom: 12px;">
            <span class="active-filters-label">当前筛选:</span>
            <div class="active-filters-list" id="biliActiveFiltersList"></div>
            <button type="button" class="clear-filters-btn" id="biliClearFiltersBtn">清空全部筛选</button>
        </div>

        <!-- 卡片网格 -->
        <div class="bili-cards-grid" id="biliCardsGrid">
            <!-- 动态生成 -->
        </div>

        <!-- 底部轻量高效分页栏 -->
        <div id="biliPaginationWrap" style="text-align:center; padding: 24px 0 12px; display:flex; justify-content:center; gap:12px; align-items:center;">
            <button type="button" class="showcase-btn js-bili-load-more" style="max-width:240px; background:var(--surface); color:var(--text); border:1px solid var(--border);">
                加载更多 (剩余 <span id="biliRemainingCount">0</span> 款) ↓
            </button>
            <button type="button" class="showcase-btn js-bili-load-all" style="max-width:200px; background:#fb7299; color:#fff;">
                全部展开 (<span id="biliTotalFilteredCount">0</span> 款) 🚀
            </button>
        </div>
    </div>
</div>

<!-- ═══════════════ BBSMC 开放资源独立视图 ═══════════════ -->
<div id="view-bbsmc" class="tab-view" style="display:none;">

    <!-- 💎 BBSMC专属频道 Header -->
    <div class="channel-hero bbsmc-channel-hero">
        <div class="channel-hero-left">
            <span class="channel-badge-tag" style="background: rgba(0, 175, 92, 0.15); color: #00af5c; border-color: rgba(0, 175, 92, 0.3);">BBSMC.NET · 优质开源模组包库</span>
            <h2 class="channel-title">💎 BBSMC 开放资源专区</h2>
            <p class="channel-desc">汇聚 BBSMC 1,802 款整合包全量资源 · 官方 Modrinth 格式直链与国内主流网盘 · 多维加载器与版本穿透 · 高清实机画廊</p>
        </div>
        <div class="channel-quick-stats">
            <div class="cstat-item"><span class="cs-num" id="bbsmcStatTotal">1,802 款</span><span class="cs-lbl">收录整合包</span></div>
            <div class="cstat-item"><span class="cs-num" id="bbsmcStatDownloads">1,711.8万</span><span class="cs-lbl">累计下载量</span></div>
            <div class="cstat-item"><span class="cs-num" id="bbsmcStatFollowers">3.29万</span><span class="cs-lbl">社区关注数</span></div>
            <div class="cstat-item"><span class="cs-num" id="bbsmcStatLinks">9,639 个</span><span class="cs-lbl">解析直链/网盘</span></div>
        </div>
    </div>

    <div class="bili-view-wrap">
        <!-- BBSMC 多维一体化控制台 -->
        <div class="central-hub" id="bbsmcCentralHub">
            <!-- 1. 搜索与核心动作 -->
            <div class="hub-tier-search">
                <div class="hub-stat-badge">
                    <span style="color:#00af5c;">💎</span>
                    <span id="bbsmcMatchInfo">正在展示 BBSMC 开放整合包...</span>
                </div>
                <div class="hub-search-box">
                    <span class="hub-search-icon">🔍</span>
                    <input type="text" id="bbsmcSearchInput" class="hub-search-input" placeholder="输入名称、作者、版本、模组或玩法实时速搜..." autocomplete="off">
                    <button type="button" id="bbsmcSearchClear" class="hub-clear-btn" style="display:none;" title="清空搜索">✕</button>
                </div>
                <div class="hub-actions-cluster">
                    <select id="bbsmcSortSelect" class="hub-select select2-hub" title="排序规则">
                        <option value="downloads_desc">下载最多 ↓</option>
                        <option value="followers_desc">关注最多 ↓</option>
                        <option value="modified_desc">最新更新 ↓</option>
                        <option value="created_desc">最新发布 ↓</option>
                        <option value="title_asc">名称字母 A-Z</option>
                    </select>
                    <select id="bbsmcVerSelect" class="hub-select select2-hub" title="按MC版本筛选">
                        <option value="">全部 MC 版本</option>
                    </select>
                    <select id="bbsmcLoaderSelect" class="hub-select select2-hub" title="按模组加载器筛选">
                        <option value="">全部加载器</option>
                        <option value="Forge">Forge</option>
                        <option value="Fabric">Fabric</option>
                        <option value="NeoForge">NeoForge</option>
                        <option value="Quilt">Quilt</option>
                    </select>
                    <button type="button" id="bbsmcResetBtn" class="hub-reset-btn" title="一键重置所有BBSMC筛选">
                        <span>↺</span> 重置
                    </button>
                </div>
            </div>

            <!-- 2. 玩法与下载渠道 -->
            <div class="hub-tier-filters">
                <div class="hub-filter-row">
                    <span class="hub-filter-label">🏷️ 玩法专区：</span>
                    <div class="hub-chips-wrap" id="bbsmcCategoryChips"></div>
                    <button type="button" id="bbsmcExpandCats" class="discovery-btn" style="display:none; margin-left:6px; font-size:11px; padding:2px 8px;" title="展开/收起全部玩法分类">展开全部 ▾</button>
                </div>

                <div class="hub-filter-row">
                    <span class="hub-filter-label">💾 资源渠道：</span>
                    <div class="hub-chips-wrap" id="bbsmcPanChips">
                        <span class="s-chip active" data-pan="">全部渠道</span>
                        <span class="s-chip" data-pan="modrinth">⚡ 官方直链 (.mrpack)</span>
                        <span class="s-chip" data-pan="curseforge">🔥 CurseForge</span>
                        <span class="s-chip" data-pan="夸克">夸克网盘</span>
                        <span class="s-chip" data-pan="百度">百度网盘</span>
                        <span class="s-chip" data-pan="123">123云盘</span>
                        <span class="s-chip" data-pan="迅雷">迅雷云盘</span>
                    </div>
                </div>
            </div>

            <!-- 高阶过滤与悬浮设置（向 MCMod 看齐） -->
            <div class="hub-tier-advanced">
                <div class="hub-adv-group">
                    <span style="font-weight:750; color:var(--text-secondary);">⚙️ 高阶过滤：</span>
                    <label class="hub-exclude-toggle" title="开启后，选中的分类将作为排除项进行反向过滤">
                        <input type="checkbox" class="js-cat-exclude" data-plat="bbsmc">
                        <span>反向排除模式</span>
                    </label>
                </div>
                <div class="hub-adv-group">
                    <span style="font-weight:750; color:var(--text-secondary);">👁️ 悬浮窗模式：</span>
                    <div class="hub-hover-switches">
                        <label class="mode-toggle" title="开启后悬停整合包名称显示介绍；关闭后点击打开"><span>介绍</span><input type="checkbox" class="js-desc-hover-toggle"></label>
                    </div>
                </div>
            </div>
        </div>

        <!-- 活动过滤项标签条 -->
        <div class="active-filters-bar" id="bbsmcActiveFilters" style="display:none; margin-bottom: 12px;">
            <span class="active-filters-label">当前筛选:</span>
            <div class="active-filters-list" id="bbsmcActiveFiltersList"></div>
            <button type="button" class="clear-filters-btn" id="bbsmcClearFiltersBtn">清空全部筛选</button>
        </div>

        <!-- 卡片网格 -->
        <div class="bbsmc-cards-grid" id="bbsmcCardsGrid">
            <!-- 动态生成 -->
        </div>

        <!-- 底部轻量高效分页栏 -->
        <div id="bbsmcPaginationWrap" style="text-align:center; padding: 24px 0 12px; display:flex; justify-content:center; gap:12px; align-items:center;">
            <button type="button" class="showcase-btn js-bbsmc-load-more" style="max-width:240px; background:var(--surface); color:var(--text); border:1px solid var(--border);">
                加载更多 (剩余 <span id="bbsmcRemainingCount">0</span> 款) ↓
            </button>
            <button type="button" class="showcase-btn js-bbsmc-load-all" style="max-width:180px; background: #00af5c;">
                展开全部 (共 <span id="bbsmcTotalFilteredCount">0</span> 款) 🚀
            </button>
        </div>
    </div>
</div>

<!-- ═══════════════ XYEBBS 像素世界独立视图 ═══════════════ -->
<div id="view-xyebbs" class="tab-view" style="display:none;">

    <!-- 🍃 XYEBBS专属频道 Header -->
    <div class="channel-hero xyebbs-channel-hero">
        <div class="channel-hero-left">
            <span class="channel-badge-tag" style="background: rgba(34, 197, 94, 0.15); color: #16a34a; border-color: rgba(34, 197, 94, 0.3);">XYEBBS.COM · 像素世界综合整合包专区</span>
            <h2 class="channel-title">🍃 XYEBBS 像素世界专区</h2>
            <p class="channel-desc">收录 XYEBBS 5,175 款玩家自制与社区精选整合包 · 覆盖夸克/百度/迅雷等主流网盘直转 · 模组加载器与版本穿透 · 社区活跃评分</p>
        </div>
        <div class="channel-quick-stats">
            <div class="cstat-item"><span class="cs-num" id="xyebbsStatTotal">5,175 款</span><span class="cs-lbl">收录整合包</span></div>
            <div class="cstat-item"><span class="cs-num" id="xyebbsStatDownloads">584.9万</span><span class="cs-lbl">累计下载量</span></div>
            <div class="cstat-item"><span class="cs-num" id="xyebbsStatViews">3.01亿</span><span class="cs-lbl">社区总浏览</span></div>
            <div class="cstat-item"><span class="cs-num" id="xyebbsStatLinks">10,793 个</span><span class="cs-lbl">网盘转存直达</span></div>
        </div>
    </div>

    <div class="bili-view-wrap">
        <!-- XYEBBS 多维一体化控制台 -->
        <div class="central-hub" id="xyebbsCentralHub">
            <!-- 1. 搜索与核心动作 -->
            <div class="hub-tier-search">
                <div class="hub-stat-badge">
                    <span style="color:#16a34a;">🍃</span>
                    <span id="xyebbsMatchInfo">正在展示 XYEBBS 像素世界整合包...</span>
                </div>
                <div class="hub-search-box">
                    <span class="hub-search-icon">🔍</span>
                    <input type="text" id="xyebbsSearchInput" class="hub-search-input" placeholder="输入名称、作者、版本、模组或玩法实时速搜..." autocomplete="off">
                    <button type="button" id="xyebbsSearchClear" class="hub-clear-btn" style="display:none;" title="清空搜索">✕</button>
                </div>
                <div class="hub-actions-cluster">
                    <select id="xyebbsSortSelect" class="hub-select select2-hub" title="排序规则">
                        <option value="hot_desc">综合热度 ↓</option>
                        <option value="downloads_desc">下载最多 ↓</option>
                        <option value="views_desc">浏览最多 ↓</option>
                        <option value="modified_desc">最新更新 ↓</option>
                        <option value="created_desc">最新发布 ↓</option>
                        <option value="comments_desc">评论最多 ↓</option>
                        <option value="title_asc">名称字母 A-Z</option>
                    </select>
                    <select id="xyebbsVerSelect" class="hub-select select2-hub" title="按MC版本筛选">
                        <option value="">全部 MC 版本</option>
                    </select>
                    <select id="xyebbsLoaderSelect" class="hub-select select2-hub" title="按模组加载器筛选">
                        <option value="">全部加载器</option>
                        <option value="Forge">Forge</option>
                        <option value="Fabric">Fabric</option>
                        <option value="NeoForge">NeoForge</option>
                        <option value="Quilt">Quilt</option>
                    </select>
                    <button type="button" id="xyebbsResetBtn" class="hub-reset-btn" title="一键重置所有XYEBBS筛选">
                        <span>↺</span> 重置
                    </button>
                </div>
            </div>

            <!-- 2. 玩法与下载渠道 -->
            <div class="hub-tier-filters">
                <div class="hub-filter-row">
                    <span class="hub-filter-label">🏷️ 玩法专区：</span>
                    <div class="hub-chips-wrap" id="xyebbsCategoryChips"></div>
                    <button type="button" id="xyebbsExpandCats" class="discovery-btn" style="display:none; margin-left:6px; font-size:11px; padding:2px 8px;" title="展开/收起全部玩法分类">展开全部 ▾</button>
                </div>

                <div class="hub-filter-row">
                    <span class="hub-filter-label">💾 下载渠道：</span>
                    <div class="hub-chips-wrap" id="xyebbsPanChips">
                        <span class="s-chip active" data-pan="">全部渠道</span>
                        <span class="s-chip" data-pan="夸克">夸克网盘</span>
                        <span class="s-chip" data-pan="百度">百度网盘</span>
                        <span class="s-chip" data-pan="123">123云盘</span>
                        <span class="s-chip" data-pan="迅雷">迅雷网盘</span>
                        <span class="s-chip" data-pan="蓝奏">蓝奏云</span>
                        <span class="s-chip" data-pan="official">官方发布页</span>
                    </div>
                </div>
            </div>

            <!-- 高阶过滤与悬浮设置（向 MCMod 看齐） -->
            <div class="hub-tier-advanced">
                <div class="hub-adv-group">
                    <span style="font-weight:750; color:var(--text-secondary);">⚙️ 高阶过滤：</span>
                    <label class="hub-exclude-toggle" title="开启后，选中的分类将作为排除项进行反向过滤">
                        <input type="checkbox" class="js-cat-exclude" data-plat="xyebbs">
                        <span>反向排除模式</span>
                    </label>
                </div>
                <div class="hub-adv-group">
                    <span style="font-weight:750; color:var(--text-secondary);">👁️ 悬浮窗模式：</span>
                    <div class="hub-hover-switches">
                        <label class="mode-toggle" title="开启后悬停整合包名称显示介绍；关闭后点击打开"><span>介绍</span><input type="checkbox" class="js-desc-hover-toggle"></label>
                    </div>
                </div>
            </div>
        </div>

        <!-- 活动过滤项标签条 -->
        <div class="active-filters-bar" id="xyebbsActiveFilters" style="display:none; margin-bottom: 12px;">
            <span class="active-filters-label">当前筛选:</span>
            <div class="active-filters-list" id="xyebbsActiveFiltersList"></div>
            <button type="button" class="clear-filters-btn" id="xyebbsClearFiltersBtn">清空全部筛选</button>
        </div>

        <!-- 卡片网格 -->
        <div class="xyebbs-cards-grid" id="xyebbsCardsGrid">
            <!-- 动态生成 -->
        </div>

        <!-- 底部轻量高效分页栏 -->
        <div id="xyebbsPaginationWrap" style="text-align:center; padding: 24px 0 12px; display:flex; justify-content:center; gap:12px; align-items:center;">
            <button type="button" class="showcase-btn js-xyebbs-load-more" style="max-width:240px; background:var(--surface); color:var(--text); border:1px solid var(--border);">
                加载更多 (剩余 <span id="xyebbsRemainingCount">0</span> 款) ↓
            </button>
            <button type="button" class="showcase-btn js-xyebbs-load-all" style="max-width:180px; background: #16a34a;">
                展开全部 (共 <span id="xyebbsTotalFilteredCount">0</span> 款) 🚀
            </button>
        </div>
    </div>
</div>

<div id="view-modrinth" class="tab-view" style="display:none;">
    <!-- 🌐 Modrinth 专属频道 Header -->
    <div class="channel-hero modrinth-channel-hero">
        <div class="channel-hero-left">
            <span class="channel-badge-tag" style="background: rgba(27, 217, 106, 0.15); color: #1bd96a; border-color: rgba(27, 217, 106, 0.3);">MODRINTH.COM · 新一代开源极速整合包社区</span>
            <h2 class="channel-title">🌐 Modrinth 国际服专区</h2>
            <p class="channel-desc">收录 Modrinth 全量 18,328 款开源轻量与硬核整合包 · 覆盖优化/冒险/多人/科技等现代模组包 · 官方一键导入支持</p>
        </div>
        <div class="channel-quick-stats">
            <div class="cstat-item"><span class="cs-num" id="modrinthStatTotal">18,328 款</span><span class="cs-lbl">精选热门包</span></div>
            <div class="cstat-item"><span class="cs-num" id="modrinthStatDownloads">1.76亿</span><span class="cs-lbl">累计下载量</span></div>
            <div class="cstat-item"><span class="cs-num" id="modrinthStatFollows">9.19万</span><span class="cs-lbl">社区关注度</span></div>
            <div class="cstat-item" id="modrinthStatTopLoaderItem" title="主流加载器"><span class="cs-num" id="modrinthStatTopLoader">Fabric</span><span class="cs-lbl">主流加载器</span></div>
        </div>
    </div>

    <div class="bili-view-wrap">
        <div class="central-hub" id="modrinthCentralHub">
            <div class="hub-tier-search">
                <div class="hub-stat-badge">
                    <span style="color:#1bd96a;">🌐</span>
                    <span id="modrinthMatchInfo">正在展示 Modrinth 热门整合包...</span>
                </div>
                <div class="hub-search-box">
                    <span class="hub-search-icon">🔍</span>
                    <input type="text" id="modrinthSearchInput" class="hub-search-input" placeholder="输入名称、作者、版本、模组或玩法实时速搜..." autocomplete="off">
                    <button type="button" id="modrinthSearchClear" class="hub-clear-btn" style="display:none;" title="清空搜索">✕</button>
                </div>
                <div class="hub-actions-cluster">
                    <select id="modrinthSortSelect" class="hub-select select2-hub" title="排序规则">
                        <option value="downloads_desc">下载最多 ↓</option>
                        <option value="follows_desc">关注最多 ↓</option>
                        <option value="modified_desc">最新更新 ↓</option>
                        <option value="title_asc">名称字母 A-Z</option>
                    </select>
                    <select id="modrinthVerSelect" class="hub-select select2-hub" title="按MC版本筛选">
                        <option value="">全部 MC 版本</option>
                    </select>
                    <select id="modrinthLoaderSelect" class="hub-select select2-hub" title="按模组加载器筛选">
                        <option value="">全部加载器</option>
                        <option value="Fabric">Fabric</option>
                        <option value="Forge">Forge</option>
                        <option value="NeoForge">NeoForge</option>
                        <option value="Quilt">Quilt</option>
                    </select>
                    <button type="button" id="modrinthResetBtn" class="hub-reset-btn" title="重置筛选">
                        <span>↺</span> 重置
                    </button>
                </div>
            </div>

            <div class="hub-tier-filters">
                <div class="hub-filter-row">
                    <span class="hub-filter-label">🏷️ 玩法分类：</span>
                    <div class="hub-chips-wrap" id="modrinthCategoryChips"></div>
                    <button type="button" id="modrinthExpandCats" class="discovery-btn" style="display:none; margin-left:6px; font-size:11px; padding:2px 8px;" title="展开/收起全部玩法分类">展开全部 ▾</button>
                </div>
            </div>

            <!-- 高阶过滤与悬浮设置（向 MCMod 看齐） -->
            <div class="hub-tier-advanced">
                <div class="hub-adv-group">
                    <span style="font-weight:750; color:var(--text-secondary);">⚙️ 高阶过滤：</span>
                    <label class="hub-exclude-toggle" title="开启后，选中的分类将作为排除项进行反向过滤">
                        <input type="checkbox" class="js-cat-exclude" data-plat="modrinth">
                        <span>反向排除模式</span>
                    </label>
                </div>
                <div class="hub-adv-group">
                    <span style="font-weight:750; color:var(--text-secondary);">👁️ 悬浮窗模式：</span>
                    <div class="hub-hover-switches">
                        <label class="mode-toggle" title="开启后悬停整合包名称显示介绍；关闭后点击打开"><span>介绍</span><input type="checkbox" class="js-desc-hover-toggle"></label>
                    </div>
                </div>
            </div>
        </div>

        <div class="active-filters-bar" id="modrinthActiveFilters" style="display:none; margin-bottom: 12px;">
            <span class="active-filters-label">当前筛选:</span>
            <div class="active-filters-list" id="modrinthActiveFiltersList"></div>
            <button type="button" class="clear-filters-btn" id="modrinthClearFiltersBtn">清空全部筛选</button>
        </div>

        <div class="modrinth-cards-grid" id="modrinthCardsGrid"></div>

        <div id="modrinthPaginationWrap" style="text-align:center; padding: 24px 0 12px; display:flex; justify-content:center; gap:12px; align-items:center;">
            <button type="button" class="showcase-btn js-modrinth-load-more" style="max-width:240px; background:var(--surface); color:var(--text); border:1px solid var(--border);">
                加载更多 (剩余 <span id="modrinthRemainingCount">0</span> 款) ↓
            </button>
            <button type="button" class="showcase-btn js-modrinth-load-all" style="max-width:180px; background: #1bd96a;">
                展开全部 (共 <span id="modrinthTotalFilteredCount">0</span> 款) 🚀
            </button>
        </div>
    </div>
</div>

<div id="view-curseforge" class="tab-view" style="display:none;">
    <!-- 🔥 CurseForge 专属频道 Header -->
    <div class="channel-hero curseforge-channel-hero">
        <div class="channel-hero-left">
            <span class="channel-badge-tag" style="background: rgba(241, 100, 54, 0.15); color: #f16436; border-color: rgba(241, 100, 54, 0.3);">CURSEFORGE.COM · 全球最大老牌整合包发源地</span>
            <h2 class="channel-title">🔥 CurseForge 国际服专区</h2>
            <p class="channel-desc">突破官方限制，穷尽收录 CurseForge 全量 45,797 款世界殿堂级整合包 · ATM全家桶、RLCraft、Better MC 等重磅大作 · 官方客户端一键拉起</p>
        </div>
        <div class="channel-quick-stats">
            <div class="cstat-item"><span class="cs-num" id="curseforgeStatTotal">45,797 款</span><span class="cs-lbl">热门大作包</span></div>
            <div class="cstat-item"><span class="cs-num" id="curseforgeStatDownloads">8.45亿</span><span class="cs-lbl">累计下载量</span></div>
            <div class="cstat-item"><span class="cs-num" id="curseforgeStatLikes">2.5万+</span><span class="cs-lbl">社区点赞</span></div>
            <div class="cstat-item" id="curseforgeStatTopLoaderItem" title="主流加载器"><span class="cs-num" id="curseforgeStatTopLoader">Forge</span><span class="cs-lbl">主流加载器</span></div>
        </div>
    </div>

    <div class="bili-view-wrap">
        <div class="central-hub" id="curseforgeCentralHub">
            <div class="hub-tier-search">
                <div class="hub-stat-badge">
                    <span style="color:#f16436;">🔥</span>
                    <span id="curseforgeMatchInfo">正在展示 CurseForge 热门整合包...</span>
                </div>
                <div class="hub-search-box">
                    <span class="hub-search-icon">🔍</span>
                    <input type="text" id="curseforgeSearchInput" class="hub-search-input" placeholder="输入名称、作者、版本、模组或玩法实时速搜..." autocomplete="off">
                    <button type="button" id="curseforgeSearchClear" class="hub-clear-btn" style="display:none;" title="清空搜索">✕</button>
                </div>
                <div class="hub-actions-cluster">
                    <select id="curseforgeSortSelect" class="hub-select select2-hub" title="排序规则">
                        <option value="downloads_desc">下载最多 ↓</option>
                        <option value="followers_desc">点赞最多 ↓</option>
                        <option value="modified_desc">最新更新 ↓</option>
                        <option value="title_asc">名称字母 A-Z</option>
                    </select>
                    <select id="curseforgeVerSelect" class="hub-select select2-hub" title="按MC版本筛选">
                        <option value="">全部 MC 版本</option>
                    </select>
                    <select id="curseforgeLoaderSelect" class="hub-select select2-hub" title="按模组加载器筛选">
                        <option value="">全部加载器</option>
                        <option value="Forge">Forge</option>
                        <option value="Fabric">Fabric</option>
                        <option value="NeoForge">NeoForge</option>
                        <option value="Quilt">Quilt</option>
                    </select>
                    <button type="button" id="curseforgeResetBtn" class="hub-reset-btn" title="重置筛选">
                        <span>↺</span> 重置
                    </button>
                </div>
            </div>

            <div class="hub-tier-filters">
                <div class="hub-filter-row">
                    <span class="hub-filter-label">🏷️ 玩法分类：</span>
                    <div class="hub-chips-wrap" id="curseforgeCategoryChips"></div>
                    <button type="button" id="curseforgeExpandCats" class="discovery-btn" style="display:none; margin-left:6px; font-size:11px; padding:2px 8px;" title="展开/收起全部玩法分类">展开全部 ▾</button>
                </div>
            </div>

            <!-- 高阶过滤与悬浮设置（向 MCMod 看齐） -->
            <div class="hub-tier-advanced">
                <div class="hub-adv-group">
                    <span style="font-weight:750; color:var(--text-secondary);">⚙️ 高阶过滤：</span>
                    <label class="hub-exclude-toggle" title="开启后，选中的分类将作为排除项进行反向过滤">
                        <input type="checkbox" class="js-cat-exclude" data-plat="curseforge">
                        <span>反向排除模式</span>
                    </label>
                </div>
                <div class="hub-adv-group">
                    <span style="font-weight:750; color:var(--text-secondary);">👁️ 悬浮窗模式：</span>
                    <div class="hub-hover-switches">
                        <label class="mode-toggle" title="开启后悬停整合包名称显示介绍；关闭后点击打开"><span>介绍</span><input type="checkbox" class="js-desc-hover-toggle"></label>
                    </div>
                </div>
            </div>
        </div>

        <div class="active-filters-bar" id="curseforgeActiveFilters" style="display:none; margin-bottom: 12px;">
            <span class="active-filters-label">当前筛选:</span>
            <div class="active-filters-list" id="curseforgeActiveFiltersList"></div>
            <button type="button" class="clear-filters-btn" id="curseforgeClearFiltersBtn">清空全部筛选</button>
        </div>

        <div class="curseforge-cards-grid" id="curseforgeCardsGrid"></div>

        <div id="curseforgePaginationWrap" style="text-align:center; padding: 24px 0 12px; display:flex; justify-content:center; gap:12px; align-items:center;">
            <button type="button" class="showcase-btn js-curseforge-load-more" style="max-width:240px; background:var(--surface); color:var(--text); border:1px solid var(--border);">
                加载更多 (剩余 <span id="curseforgeRemainingCount">0</span> 款) ↓
            </button>
            <button type="button" class="showcase-btn js-curseforge-load-all" style="max-width:180px; background: #f16436;">
                展开全部 (共 <span id="curseforgeTotalFilteredCount">0</span> 款) 🚀
            </button>
        </div>
    </div>
</div>

<!-- 复制气泡 -->
<div id="copyToast" class="copy-toast">✅ 复制成功！</div>

    </main>
</div>

<div id="imageLightbox" class="image-lightbox" aria-hidden="true">
    <div class="image-lightbox-panel">
        <button type="button" class="image-lightbox-close" id="imageLightboxClose" aria-label="关闭">×</button>
        <img class="image-lightbox-img" id="imageLightboxImg" src="" alt="">
        <div class="image-lightbox-caption">
            <span id="imageLightboxTitle"></span>
            <a id="imageLightboxOpen" href="#" target="_blank" rel="noreferrer">打开原图 ↗</a>
        </div>
    </div>
</div>

<script src="data/vendor/jquery.min.js"></script>
<script src="data/vendor/bootstrap.bundle.min.js"></script>
<script src="data/vendor/select2.min.js"></script>
<script src="data/vendor/jquery.dataTables.min.js"></script>
<script src="data/vendor/dataTables.bootstrap5.min.js"></script>
<script src="data/app_data.js"></script>
<script src="data/desc_data.js"></script>
    <script src="data/audit_diff.js"></script>

    <!-- 6大平台数据源元信息声明 (MC百科首屏直接载入，其余由 PlatformLoader 异步流式按需加载) -->
    <script src="data/table_rows.js"></script>
    <!-- <script src="data/bili_data.js"></script> -->
    <!-- <script src="data/bbsmc_data.js"></script> -->
    <!-- <script src="data/xyebbs_data.js"></script> -->
    <!-- <script src="data/modrinth_data.js"></script> -->
    <!-- <script src="data/curseforge_data.js"></script> -->
<script>
$(document).ready(function() {{

    /* 全局通用安全 HTML 转义与多选辅助函数（提前声明，保证所有组件和生命周期全局可用） */
    function escHtml(str, noFormat) {{
        if (str === null || str === undefined) return "";
        var d = document.createElement('div');
        d.textContent = str;
        var raw = d.innerHTML;
        var LF = String.fromCharCode(10);
        var CR = String.fromCharCode(13);
        var text = raw.split(CR + LF).join(LF).split(CR).join(LF);
        if (noFormat) {{
            return text.split(LF).join('<br>');
        }}
        return text;
    }}
    window.escHtml = escHtml;

    function escAttrJs(str) {{
        return escHtml(str || '', true).replace(/<br>/g, '&#10;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }}
    window.escAttrJs = escAttrJs;

    function toggleMultiSelect(selector, val) {{
        var $sel = $(selector);
        var current = $sel.val() || [];
        if (!Array.isArray(current)) current = current ? [current] : [];
        var idx = current.indexOf(val);
        if (idx >= 0) {{
            current.splice(idx, 1);
            $sel.find('option').filter(function() {{ return $(this).val() === val; }}).remove();
        }} else {{
            if ($sel.find('option').filter(function() {{ return $(this).val() === val; }}).length === 0) {{
                $sel.append($('<option>', {{ value: val, text: val, selected: true }}));
            }}
            current.push(val);
        }}
        $sel.val(current).trigger('change');
    }}
    window.toggleMultiSelect = toggleMultiSelect;

    


    /* ═════════════════ 非阻塞流式平台数据加载引擎 V3.0 ═════════════════ */
    var PLATFORMS = {{
        'mcmod': {{ id: 'mcmod', name: 'MC百科', src: 'data/table_rows.js', globalVar: 'tableRowsData', count: 1484, loaded: false, loading: false, callbacks: [] }},
        'bilibili': {{ id: 'bilibili', name: 'B站自制', src: 'data/bili_data.js', globalVar: 'biliModpacksData', count: 606, loaded: false, loading: false, callbacks: [] }},
        'bbsmc': {{ id: 'bbsmc', name: 'BBSMC', src: 'data/bbsmc_data.js', globalVar: 'bbsmcModpacksData', count: 1802, loaded: false, loading: false, callbacks: [] }},
        'xyebbs': {{ id: 'xyebbs', name: 'XYEBBS', src: 'data/xyebbs_data.js', globalVar: 'xyebbsModpacksData', count: 5175, loaded: false, loading: false, callbacks: [] }},
        'modrinth': {{ id: 'modrinth', name: 'Modrinth', src: 'data/modrinth_data.js', globalVar: 'modrinthModpacksData', count: 18328, loaded: false, loading: false, callbacks: [] }},
        'curseforge': {{ id: 'curseforge', name: 'CurseForge', src: 'data/curseforge_data.js', globalVar: 'curseforgeModpacksData', count: 45797, loaded: false, loading: false, callbacks: [] }}
    }};
    window.PlatformLoader = PLATFORMS;

    function onPlatformLoaded(platId) {{
        if (platId === 'mcmod') {{
            enhanceMcmodRows();
            if (activeMcmodVMode === 'cards') {{
                renderMcmodCards();
            }} else if (window.initMcmodTable) {{
                window.initMcmodTable();
            }}
        }} else if (platId === 'bilibili') {{
            biliPacks = window.biliModpacksData || [];
            initBiliDateChips();
            initBiliStats();
            if (currentTab === 'bilibili') renderBiliView();
        }} else if (platId === 'bbsmc') {{
            bbsmcPacks = window.bbsmcModpacksData || [];
            initBbsmcStats();
            if (currentTab === 'bbsmc') renderBbsmcView();
        }} else if (platId === 'xyebbs') {{
            xyebbsPacks = window.xyebbsModpacksData || [];
            initXyebbsStats();
            if (currentTab === 'xyebbs') renderXyebbsView();
        }} else if (platId === 'modrinth') {{
            modrinthPacks = window.modrinthModpacksData || [];
            initModrinthStats();
            if (currentTab === 'modrinth') renderModrinthView();
        }} else if (platId === 'curseforge') {{
            curseforgePacks = window.curseforgeModpacksData || [];
            initCurseforgeStats();
            if (currentTab === 'curseforge') renderCurseforgeView();
        }}
        updateAllPlatformsTotalBadge();
        var q = ($('#crossSearchInput').val() || '').trim();
        if (q) $('#crossSearchInput').trigger('input');
    }}

    function loadPlatformScript(platId, callback) {{
        var p = PLATFORMS[platId];
        if (!p) {{ if (callback) callback(); return; }}
        if (window[p.globalVar] && window[p.globalVar].length) {{
            p.loaded = true;
            if (callback) callback();
            return;
        }}
        if (callback) p.callbacks.push(callback);
        if (p.loading) return;
        p.loading = true;

        var script = document.createElement('script');
        script.src = p.src;
        script.async = true;
        script.onload = function() {{
            p.loaded = true;
            p.loading = false;
            onPlatformLoaded(platId);
            var cbs = p.callbacks.slice();
            p.callbacks = [];
            cbs.forEach(function(fn) {{
                try {{ fn(); }} catch(e) {{ console.error(e); }}
            }});
        }};
        script.onerror = function() {{
            console.error('加载 ' + p.name + ' 数据源失败: ' + p.src);
            p.loading = false;
        }};
        document.body.appendChild(script);
    }}

    function startIdlePrefetch() {{
        var queue = ['bilibili', 'bbsmc', 'xyebbs', 'mcmod', 'modrinth', 'curseforge'];
        function step() {{
            if (!queue.length) return;
            var nextId = queue.shift();
            if (PLATFORMS[nextId].loaded || PLATFORMS[nextId].loading) {{
                step();
                return;
            }}
            loadPlatformScript(nextId, function() {{
                setTimeout(step, 150);
            }});
        }}
        setTimeout(step, 300);
    }}

    /* ═════════════════ 平台变量与状态管理 ═════════════════ */
    var biliPacks = window.biliModpacksData || [];
    var bbsmcPacks = window.bbsmcModpacksData || [];
    var xyebbsPacks = window.xyebbsModpacksData || [];
    var activeCat = [];
    var activePan = '';
    var activeDate = '';
    var bbsmcActiveCat = [];
    var bbsmcActivePan = '';
    var currentBbsmcCardLimit = 48;
    var xyebbsActiveCat = [];
    var xyebbsActivePan = '';
    var currentXyebbsCardLimit = 48;
    var modrinthPacks = window.modrinthModpacksData || [];
    var curseforgePacks = window.curseforgeModpacksData || [];
    var modrinthActiveCat = [];
    var currentModrinthCardLimit = 48;
    var curseforgeActiveCat = [];
    var currentCurseforgeCardLimit = 48;
    var activeGroupMode = 'grouped'; // 'grouped' | 'flat'
    var activeMcmodVMode = 'table';   // 'table' | 'cards'
    var currentTab = 'all';          // 'all' | 'mcmod' | 'bilibili' | 'bbsmc' | 'xyebbs' | 'modrinth' | 'curseforge'

    /* ════════════ 分类多选引擎（5 个平台向 MCMod 看齐） ════════════
       原先 Bilibili/BBSMC/XYEBBS/Modrinth/CurseForge 的「分类」筛选都是单选
       （点一个会把其它清掉），这里统一升级为多选，并补上 MCMod 的「反向排除」语义。 */
    var __catExclude = {{ bilibili: false, bbsmc: false, xyebbs: false, modrinth: false, curseforge: false }};

    /* 分类命中判定：
       - 未选任何分类 => 全部命中；
       - exclude 为假 => 条目分类命中任一所选即通过（并集语义）；
       - exclude 为真 => 命中任一所选即排除（MCMod 的「反向排除模式」）。 */
    function catHitMulti(sel, cats, exclude) {{
        if (!sel || !sel.length) return true;
        cats = cats || [];
        var hit = false;
        for (var i = 0; i < cats.length; i++) {{
            if (sel.indexOf(cats[i]) !== -1) {{ hit = true; break; }}
        }}
        return exclude ? !hit : hit;
    }}

    /* ════════════ 分类 / 加载器 的中文展示层 ════════════
       Modrinth 与 CurseForge 的分类是英文原文（multiplayer / Exploration …），
       直接铺在看板上对中文用户不友好。这里只做「展示名」映射：
       筛选、统计、data-cat 一律仍用原始英文值，保证逻辑与数据零改动。
       没收录的值原样返回 —— 不猜、不硬凑。 */
    var __CAT_LABEL = {{
        // Modrinth
        'multiplayer': '多人游戏', 'optimization': '性能优化', 'adventure': '冒险',
        'lightweight': '轻量', 'combat': '战斗', 'technology': '科技',
        'challenging': '硬核挑战', 'magic': '魔法', 'kitchen-sink': '综合整合',
        'quests': '任务', 'game-mechanics': '游戏机制', 'equipment': '装备',
        'decoration': '装饰', 'worldgen': '世界生成', 'food': '食物', 'mobs': '生物',
        'utility': '实用工具', 'storage': '存储', 'management': '管理',
        'library': '前置库', 'transportation': '交通', 'social': '社交',
        'iris': '光影支持', 'minecraft': '原版风格', 'cursed': '搞怪',
        'economy': '经济', 'datapack': '数据包', 'modloader': '加载器',
        'minigame': '小游戏',
        // CurseForge
        'Exploration': '探索', 'Adventure and RPG': '冒险与RPG', 'Tech': '科技',
        'Multiplayer': '多人游戏', 'Magic': '魔法', 'Combat / PvP': '战斗 / PvP',
        'Small / Light': '小型轻量', 'Vanilla+': '原版增强', 'Quests': '任务',
        'Hardcore': '硬核', 'Extra Large': '大型整合', 'Sci-Fi': '科幻',
        'Horror': '恐怖', 'Map Based': '地图驱动', 'Skyblock': '空岛',
        'Mini Game': '小游戏', 'Expert': '专家模式',
        'FTB Official Pack': 'FTB 官方包', 'RLCraft': 'RLCraft 系'
    }};
    // 加载器统一大小写（B站 数据里是 Neoforge，其余平台是 NeoForge）
    var __LOADER_LABEL = {{ 'Neoforge': 'NeoForge', 'neoforge': 'NeoForge', 'neoForge': 'NeoForge' }};
    function catLabel(v) {{ return (v === null || v === undefined || v === '') ? '' : (__CAT_LABEL[v] || v); }}
    function loaderLabel(v) {{ return (v === null || v === undefined || v === '') ? '' : (__LOADER_LABEL[v] || v); }}
    function catLabelList(arr) {{ return (arr || []).map(catLabel).join(' · '); }}
    function loaderLabelList(arr) {{ return (arr || []).map(loaderLabel).join(' · '); }}

    /* 「反向排除」开关的委托绑定：各平台高阶过滤里的 .js-cat-exclude 复选框共用一套逻辑 */
    $(document).on('change', '.js-cat-exclude', function() {{
        var plat = $(this).data('plat');
        if (!plat || !(plat in __catExclude)) return;
        __catExclude[plat] = $(this).is(':checked');
        if (plat === 'bilibili') renderBiliView();
        else if (plat === 'bbsmc') {{ currentBbsmcCardLimit = 48; renderBbsmcView(); }}
        else if (plat === 'xyebbs') {{ currentXyebbsCardLimit = 48; renderXyebbsView(); }}
        else if (plat === 'modrinth') {{ currentModrinthCardLimit = 48; renderModrinthView(); }}
        else if (plat === 'curseforge') {{ currentCurseforgeCardLimit = 48; renderCurseforgeView(); }}
    }});

    /* ════════════ 卡片平台的「版本与详情」弹窗桥接（向 MCMod 看齐） ════════════
       5 个卡片平台的字段各不相同：B站 有 pub_time / views / mod_count，
       BBSMC/XYEBBS/Modrinth/CurseForge 有 date_created / date_modified / downloads，
       但都没有 MCMod 那种逐版本的改动日志。
       所以这里只做「有就做」：把真实存在的字段组织进同一个弹窗，
       没有的字段一律留空，绝不编造。
       实现上不往 DOM 里塞一长串 data-*（标题含引号会直接破坏属性），
       改为按 url 建索引，点击时回查原始对象。 */
    window.__packByUrl = window.__packByUrl || {{}};
    function registerPackForModal(p) {{
        if (p && p.url) window.__packByUrl[p.url] = p;
        return p;
    }}

    /* 各平台弹窗标签覆盖表：字段语义不同，标签也必须跟着不同，
       否则会出现「累计历史版本数: 2297419」这种明显错位。 */
    var __CARD_PLAT_LABELS = {{
        bilibili:   {{ verLabel: '🎮 支持版本', countLabel: '📺 关联发布记录', countUnit: ' 期', typeLabel: '🏷️ 分区与标签', countTagLabel: '累计发布', countTagUnit: ' 期' }},
        bbsmc:      {{ verLabel: '🏷️ 最新支持版本', countLabel: '📥 累计下载量', countUnit: '次', typeLabel: '🏷️ 玩法分类', countTagLabel: '累计下载', countTagUnit: '次' }},
        xyebbs:     {{ verLabel: '🏷️ 最新支持版本', countLabel: '📥 累计下载量', countUnit: '次', typeLabel: '🏷️ 玩法分类', countTagLabel: '累计下载', countTagUnit: '次' }},
        modrinth:   {{ verLabel: '🏷️ 最新支持版本', countLabel: '📥 累计下载量', countUnit: '次', typeLabel: '🏷️ 分类标签', countTagLabel: '累计下载', countTagUnit: '次' }},
        curseforge: {{ verLabel: '🏷️ 最新支持版本', countLabel: '📥 累计下载量', countUnit: '次', typeLabel: '🏷️ 分类标签', countTagLabel: '累计下载', countTagUnit: '次' }}
    }};

    /* 把原始 pack 对象整理成弹窗所需的 extra，字段缺失就留空 */
    function buildCardModalExtra(plat, p) {{
        var lab = __CARD_PLAT_LABELS[plat] || {{}};
        var ten = function(s) {{ return s ? String(s).substring(0, 10) : ''; }};
        var vers = (p.all_versions && p.all_versions.length) ? p.all_versions : (p.mc_version ? [p.mc_version] : []);
        var mcVers = vers.length ? vers.slice(0, 15).join(', ') + (vers.length > 15 ? ' 等 ' + vers.length + ' 个版本' : '') : '';
        var cats = catLabelList(p.categories);
        var loaders = loaderLabelList(p.loaders);
        var typeParts = [];
        if (cats) typeParts.push(cats);
        if (loaders) typeParts.push('加载器: ' + loaders);
        var dl = (typeof p.downloads === 'number') ? p.downloads : (typeof p.views === 'number' ? p.views : null);
        var links = p.download_links || [];

        // 提取整合包真实发布版本号（如 BBSMC 的 lk.version、XYEBBS 的 lk.label）
        var packVer = '';
        for (var li = 0; li < links.length; li++) {{
            var lk = links[li];
            if (lk && (lk.version || lk.label)) {{
                packVer = (lk.version || lk.label || '').trim();
                break;
            }}
        }}
        var displayVer = packVer ? (packVer + (p.mc_version ? ' (MC ' + p.mc_version + ')' : '')) : (p.mc_version || (vers[0] || '通用 / 最新'));

        return {{
            platform: plat,
            title: p.title || '',
            url: p.url || '#',
            ver: displayVer,
            date: ten(p.date_modified || p.pub_time) || '暂无记录',
            date_created: ten(p.date_created || p.pub_time) || '',
            count: dl,
            mcVers: mcVers,
            mcVersList: vers,
            links: links,
            typeName: typeParts.join(' · ') || '未标注分类',
            verLabel: lab.verLabel, countLabel: lab.countLabel, countUnit: lab.countUnit,
            typeLabel: lab.typeLabel, countTagLabel: lab.countTagLabel, countTagUnit: lab.countTagUnit
        }};
    }}


    /* 版本号与 Minecraft 运行版本识别算法 */
    function extractVersion(r) {{
        if (!r) return '';
        // 1. 优先读取已解析的官方 MC 运行版本 (支持多版本展示，如 ATM10: 1.21.1 / 1.21)
        if (r.mc_versions && Array.isArray(r.mc_versions) && r.mc_versions.length > 0) {{
            if (r.mc_versions.length > 2) {{
                return 'MC ' + r.mc_versions[0] + ' (+' + (r.mc_versions.length - 1) + ')';
            }}
            return 'MC ' + r.mc_versions.join(' / ');
        }}
        if (r.mc_version) {{
            return 'MC ' + r.mc_version;
        }}
        // 2. ATM 家族智能识别 (确保 ATM 无论如何都能准确点亮运行版本徽章)
        var title = r.title || '';
        var mAtm = title.match(/\\[ATM([0-9A-Za-z]+)\\]/i) || title.match(/All [Tt]he Mods\\s*(\\d+)/i);
        if (mAtm) {{
            var atmKey = mAtm[1].toLowerCase();
            var atmMap = {{
                '10': 'MC 1.21.1 / 1.21', '10s': 'MC 1.21.1 / 1.21', '11': 'MC 1.21.1',
                '9': 'MC 1.20.1', '9s': 'MC 1.20.1', '9nf': 'MC 1.20.1', 'g2': 'MC 1.20.1',
                '8': 'MC 1.19.2', '7': 'MC 1.18.2', '7s': 'MC 1.18.2',
                '6': 'MC 1.16.5', '6s': 'MC 1.16.5', '5': 'MC 1.15.2', '4': 'MC 1.14.4',
                '3': 'MC 1.12.2', '3e': 'MC 1.12.2', '3l': 'MC 1.12.2', '3r': 'MC 1.12.2',
                '2': 'MC 1.11.2', '1': 'MC 1.10.2', '0': 'MC 1.7.10', 'ar': 'MC 1.18.2'
            }};
            if (atmMap[atmKey]) return atmMap[atmKey];
        }}
        // 3. 标题中的明确 Minecraft 版本 (如 [1.20.1] 或 1.12.2)
        var mTitleMC = title.match(/\\b(1\\.(?:[7-9]|1\\d|2\\d)(?:\\.\\d+)?)\\b/);
        if (mTitleMC) return 'MC ' + mTitleMC[1];
        // 4. 标题中的整合包大版本号 (如 v1.2.0)
        var mVer = title.match(/\\bv(\\d+(?:\\.\\d+)*)\\b/i);
        if (mVer) return mVer[0];
        // 5. 标签中的版本
        var mTagsMC = (r.tags_search || '').match(/\\b(1\\.(?:[7-9]|1\\d|2\\d)(?:\\.\\d+)?)\\b/);
        if (mTagsMC) return 'MC ' + mTagsMC[1];
        return '';
    }}

    /* 增强所有 MCMod 行：提取统一封面 URL、加入 [📜 历史改动对比] 链接与版本号徽章 */
    var MC_COVER_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 75' width='120' height='75'%3E%3Crect width='120' height='75' fill='%231e293b'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%2394a3b8' font-family='sans-serif' font-size='12' font-weight='bold'%3E📦 MC百科%3C/text%3E%3C/svg%3E";
    var BILI_COVER_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 75' width='120' height='75'%3E%3Crect width='120' height='75' fill='%232c1c24'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23fb7299' font-family='sans-serif' font-size='12' font-weight='bold'%3E📺 B站自制%3C/text%3E%3C/svg%3E";
    var BBSMC_COVER_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 75' width='120' height='75'%3E%3Crect width='120' height='75' fill='%23122119'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%2300af5c' font-family='sans-serif' font-size='12' font-weight='bold'%3E💎 BBSMC%3C/text%3E%3C/svg%3E";
    var XYEBBS_COVER_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 75' width='120' height='75'%3E%3Crect width='120' height='75' fill='%230f291e'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%2322c55e' font-family='sans-serif' font-size='12' font-weight='bold'%3E🍃 XYEBBS%3C/text%3E%3C/svg%3E";
    var MODRINTH_COVER_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 75' width='120' height='75'%3E%3Crect width='120' height='75' fill='%230b2e1f'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%231bd96a' font-family='sans-serif' font-size='12' font-weight='bold'%3E🌐 Modrinth%3C/text%3E%3C/svg%3E";
    var CURSEFORGE_COVER_FALLBACK = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 120 75' width='120' height='75'%3E%3Crect width='120' height='75' fill='%23381608'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%23f16436' font-family='sans-serif' font-size='12' font-weight='bold'%3E🔥 CurseForge%3C/text%3E%3C/svg%3E";
    window.MC_COVER_FALLBACK = MC_COVER_FALLBACK;
    window.BILI_COVER_FALLBACK = BILI_COVER_FALLBACK;
    window.BBSMC_COVER_FALLBACK = BBSMC_COVER_FALLBACK;
    window.XYEBBS_COVER_FALLBACK = XYEBBS_COVER_FALLBACK;
    window.MODRINTH_COVER_FALLBACK = MODRINTH_COVER_FALLBACK;
    window.CURSEFORGE_COVER_FALLBACK = CURSEFORGE_COVER_FALLBACK;

    function enhanceMcmodRows() {{
        if (!window.tableRowsData) return;
        window.tableRowsData.forEach(function(r) {{
            // 提取封面 URL，确保各模块随时可用且自带防盗链与 fallback
            if (!r.cover_url && r.c0) {{
                var mCover = r.c0.match(/data-image-url="([^"]+)"/);
                if (mCover && mCover[1]) {{
                    r.cover_url = mCover[1];
                }}
            }}
            if (r.c0) {{
                var verStr = extractVersion(r);
                if (verStr && r.c0.indexOf('modpack-ver-badge') === -1) {{
                    var verBadge = '<span class="modpack-ver-badge">' + verStr + '</span>';
                    r.c0 = r.c0.replace('<div class="modpack-meta-row">', '<div class="modpack-meta-row">' + verBadge + ' ');
                }}
            }}
        }});
    }}
    enhanceMcmodRows();

    var currentMcmodCardLimit = 48;
    var currentBiliCardLimit = 48;
    var renderedTabs = {{}};

    /* 渲染 MCMod 画廊卡片 */
    function renderMcmodCards() {{
        var $grid = $('#mcmodCardsGrid');
        $grid.empty();
        
        var rows = [];
        if (window.table) {{
            rows = window.table.rows({{ search: 'applied' }}).data().toArray();
        }} else if ($.fn.DataTable && $.fn.DataTable.isDataTable('#modpackTable')) {{
            var table = $('#modpackTable').DataTable();
            rows = table.rows({{ search: 'applied' }}).data().toArray();
        }} else {{
            rows = window.tableRowsData || [];
        }}

        $('#mcmodCardCountBadge').text(rows.length + ' 款');
        $('#mcmodMatchedCount').text(rows.length);

        if (rows.length === 0) {{
            $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted); font-size:1.1rem;">🔍 未匹配到任何 MC百科整合包</div>');
            return;
        }}

        var limit = Math.min(rows.length, currentMcmodCardLimit);
        var htmlArr = [];
        for (var i = 0; i < limit; i++) {{
            var r = rows[i];
            var mid = r.mid;
            var title = r.title || '';
            var coverImg = r.cover_url || '';
            if (!coverImg) {{
                var mCover = (r.c0 || '').match(/data-image-url="([^"]+)"/);
                if (mCover && mCover[1]) coverImg = mCover[1];
            }}
            var coverSrc = coverImg || window.MC_COVER_FALLBACK || MC_COVER_FALLBACK;

            var verStr = extractVersion(r);
            var viewsStr = r.views_n > 10000 ? (r.views_n / 10000).toFixed(1) + '万' : (r.views_n || 0);
            var scoreStr = r.score_n ? r.score_n + '★' : '流行';
            var modCount = r.mod_count || 0;
            var goodPct = r.rp_n || 90;

            var cardHtml = '<div class="mcmod-grid-card" data-mid="' + mid + '">' +
                '<div class="mcmod-card-top">' +
                    '<img src="' + coverSrc + '" class="mcmod-card-cover image-thumb" data-image-url="' + (coverImg || coverSrc) + '" style="cursor:pointer;" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=window.MC_COVER_FALLBACK;" alt="' + escAttrJs(title) + '" title="' + escAttrJs(title) + ' 封面预览（点击放大）">' +
                    '<div class="mcmod-card-overlay">' +
                        '<span>👁️ ' + viewsStr + '</span>' +
                        '<span>' + scoreStr + '</span>' +
                    '</div>' +
                '</div>' +
                '<div class="mcmod-card-body">' +
                    '<a href="https://www.mcmod.cn/modpack/' + mid + '.html" target="_blank" class="mcmod-card-title modpack-link" data-mid="' + mid + '" data-full-title="' + escAttrJs(title) + '" title="' + escAttrJs(title) + '">' +
                        (verStr ? '<span class="modpack-ver-badge">' + verStr + '</span> ' : '') +
                        title +
                    '</a>' +
                    '<div class="mcmod-card-badges">' +
                        '<span class="mcmod-badge-type">' + (r.type_name || '魔改') + '</span>' +
                        '<span class="mcmod-badge-mods js-open-version-modal" data-mid="' + mid + '" style="cursor:pointer;" title="点击查看版本与参数详情">🧩 ' + modCount + ' 个模组</span>' +
                        '<span class="mcmod-badge-score">👍 ' + goodPct + '% 好评</span>' +
                    '</div>' +
                    '<div style="font-size:0.75rem; color:var(--text-muted); line-height:1.4;">' +
                        '<span>推: ' + (r.rec_n || 0) + '</span> · ' +
                        '<span>藏: ' + (r.fav_n || 0) + '</span> · ' +
                        '<span>评: ' + (r.com_n || 0) + '</span>' +
                    '</div>' +
                    '<div class="mcmod-card-foot">' +
                        '<button type="button" class="modpack-diff-link js-open-version-modal" data-mid="' + mid + '" data-title="' + escAttrJs(title) + '" data-ver="' + escAttrJs(r.latest_version || '') + '" data-date="' + escAttrJs(r.last_update_date || '') + '" data-count="' + (r.version_count || 0) + '" title="在看板内查看真实版本发布与更新日志">📜 更新日志 ↗</button>' +
                        '<button type="button" class="btn btn-sm btn-outline-primary show-comment-btn" data-mid="' + mid + '" data-order="' + (r.com_n || 0) + '" style="font-size:0.75rem; padding:2px 8px; border-radius:6px; cursor:pointer;">💬 详情评论</button>' +
                    '</div>' +
                '</div>' +
            '</div>';
            htmlArr.push(cardHtml);
        }}

        if (rows.length > limit) {{
            var remain = rows.length - limit;
            var loadNext = Math.min(remain, 48);
            var loadMoreHtml = '<div class="mcmod-load-more-bar">' +
                '<button type="button" class="btn-card-load-more js-load-more-cards">📥 加载更多 ' + loadNext + ' 款 (剩余 ' + remain + ' 款) ▾</button>' +
                '<button type="button" class="btn-card-load-all js-load-all-cards">⚡ 全部展开 (' + rows.length + ' 款)</button>' +
                '</div>';
            htmlArr.push(loadMoreHtml);
        }}
        $grid.html(htmlArr.join(''));
    }}

    /* 官方真实分类数据集 (绝不胡乱自创，100% 取自官方数据) */
    var MC_REAL_CATEGORIES = [
        {{cat: '科技', count: 936 }},
        {{cat: '冒险', count: 929 }},
        {{cat: '任务', count: 897 }},
        {{cat: '魔法', count: 700 }},
        {{cat: '国创', count: 630 }},
        {{cat: '大型', count: 514 }},
        {{cat: '硬核', count: 448 }},
        {{cat: '轻量', count: 405 }},
        {{cat: '休闲', count: 365 }},
        {{cat: '空岛', count: 249 }},
        {{cat: '建筑', count: 188 }},
        {{cat: '剧情', count: 155 }},
        {{cat: '地图', count: 107 }},
        {{cat: 'PvP', count: 41 }}
    ];

    var BILI_REAL_CATEGORIES = [
        {{cat: '冒险', count: 87 }},
        {{cat: '科技', count: 47 }},
        {{cat: '休闲/建筑', count: 40 }},
        {{cat: '宝可梦', count: 37 }},
        {{cat: '魔改', count: 30 }},
        {{cat: '战斗/枪械', count: 22 }},
        {{cat: '魔法', count: 16 }},
        {{cat: '末日/生存', count: 16 }},
        {{cat: '空岛', count: 10 }}
    ];

    var ALL_REAL_CATEGORIES = [
        {{cat: '科技', count: 983 }},
        {{cat: '冒险', count: 1016 }},
        {{cat: '魔法', count: 716 }},
        {{cat: '任务', count: 897 }},
        {{cat: '国创', count: 630 }},
        {{cat: '硬核', count: 448 }},
        {{cat: '宝可梦', count: 122 }},
        {{cat: '空岛', count: 259 }},
        {{cat: '休闲', count: 405 }}
    ];

    /* 初始化侧边栏分类 Chips */
    var MC_HOT_TAGS = [
        {{tag: '机械动力', count: 69}},
        {{tag: 'FTB', count: 49}},
        {{tag: '优化', count: 45}},
        {{tag: '生存', count: 37}},
        {{tag: 'RPG', count: 31}},
        {{tag: '格雷科技', count: 26}},
        {{tag: '养老', count: 25}},
        {{tag: '战斗', count: 25}},
        {{tag: '魔改', count: 24}},
        {{tag: '枪械', count: 23}},
        {{tag: '末日', count: 19}},
        {{tag: '僵尸', count: 18}},
        {{tag: '探索', count: 18}},
        {{tag: '恐怖', count: 16}},
        {{tag: '自动化', count: 16}},
        {{tag: '拔刀剑', count: 15}},
        {{tag: '暮色森林', count: 15}},
        {{tag: '应用能源2', count: 14}},
        {{tag: '植物魔法', count: 14}},
        {{tag: '等价交换', count: 12}},
        {{tag: '龙之研究', count: 12}},
        {{tag: '无尽贪婪', count: 11}},
        {{tag: '冰与火之歌', count: 11}},
        {{tag: '宝可梦', count: 10}}
    ];

    /* ══════════════ MCMod 多维一体化分类/标签/模组引擎 (参考黄游 Discovery 逻辑) ══════════════ */
    var tagCountsMap = new Map();
    var modCatCountsMap = new Map();
    var modCountsMap = new Map();
    var allTagsList = [];
    var allModCatsList = [];
    var allModsList = [];
    var tagListExpanded = false;
    var modListExpanded = false;

    function analyzeCompareData() {{
        tagCountsMap.clear();
        modCatCountsMap.clear();
        modCountsMap.clear();
        if (!window.compareData) return;
        for (var mid in window.compareData) {{
            var item = window.compareData[mid];
            if (!item) continue;
            // 1. 玩法标签
            var tags = item.tags || [];
            for (var i = 0; i < tags.length; i++) {{
                var t = String(tags[i] || '').trim();
                if (t) tagCountsMap.set(t, (tagCountsMap.get(t) || 0) + 1);
            }}
            // 2. 模组分类
            var mcs = item.mod_categories || [];
            for (var j = 0; j < mcs.length; j++) {{
                var mc = String(mcs[j] || '').trim();
                if (mc) modCatCountsMap.set(mc, (modCatCountsMap.get(mc) || 0) + 1);
            }}
            // 3. 收录模组
            var mods = item.mods || [];
            for (var k = 0; k < mods.length; k++) {{
                var m = mods[k];
                var mName = typeof m === 'string' ? m : (m && m.name ? m.name : '');
                mName = String(mName || '').trim();
                if (mName) modCountsMap.set(mName, (modCountsMap.get(mName) || 0) + 1);
            }}
        }}

        allTagsList = Array.from(tagCountsMap.keys()).sort(function(a, b) {{
            return (tagCountsMap.get(b) - tagCountsMap.get(a)) || a.localeCompare(b, 'zh-CN');
        }});

        var standardOrder = ['辅助', 'LIB', '实用', '装饰', '魔改', '冒险', '农业', '科技', '魔法', '未分类'];
        allModCatsList = Array.from(modCatCountsMap.keys()).sort(function(a, b) {{
            var ia = standardOrder.indexOf(a), ib = standardOrder.indexOf(b);
            if (ia !== -1 && ib !== -1) return ia - ib;
            if (ia !== -1) return -1;
            if (ib !== -1) return 1;
            return (modCatCountsMap.get(b) - modCatCountsMap.get(a));
        }});

        allModsList = Array.from(modCountsMap.keys()).sort(function(a, b) {{
            return (modCountsMap.get(b) - modCountsMap.get(a)) || a.localeCompare(b, 'zh-CN');
        }});
    }}

    function renderCategoryChips() {{
        var $mcBox = $('#mcmodCategoryChips');
        $mcBox.empty();
        $mcBox.append('<span class="s-chip active" data-cat="">全部</span>');
        MC_REAL_CATEGORIES.forEach(function(item) {{
            $mcBox.append('<span class="s-chip" data-cat="' + escHtml(item.cat, true) + '">' + escHtml(item.cat, true) + ' <span class="s-chip-count">' + item.count + '</span></span>');
        }});
    }}

    function renderTagChips() {{
        var $tagBox = $('#mcmodTagChips');
        if (!$tagBox.length) return;
        $tagBox.empty();
        $tagBox.toggleClass('expanded-chips', tagListExpanded);
        $tagBox.closest('.hub-filter-row').toggleClass('row-expanded', tagListExpanded);
        $tagBox.append('<span class="s-chip active" data-tag="">全部</span>');
        var items = tagListExpanded ? allTagsList : (allTagsList.length ? allTagsList.slice(0, 40) : MC_HOT_TAGS.map(function(x) {{ return x.tag; }}));
        for (var i = 0; i < items.length; i++) {{
            var t = items[i];
            var cnt = tagCountsMap.get(t) || 0;
            $tagBox.append('<span class="s-chip" data-tag="' + escHtml(t, true) + '">' + escHtml(t, true) + ' <span class="s-chip-count">' + cnt + '</span></span>');
        }}
        syncAllFilterUI();
    }}

    function renderModCatChips() {{
        var $modCatBox = $('#mcmodModCatChips');
        if (!$modCatBox.length) return;
        $modCatBox.empty();
        $modCatBox.append('<span class="s-chip active" data-mod-cat="">全部</span>');
        for (var i = 0; i < allModCatsList.length; i++) {{
            var mc = allModCatsList[i];
            var cnt = modCatCountsMap.get(mc) || 0;
            $modCatBox.append('<span class="s-chip" data-mod-cat="' + escHtml(mc, true) + '">' + escHtml(mc, true) + ' <span class="s-chip-count">' + cnt + '</span></span>');
        }}
        syncAllFilterUI();
    }}

    function renderHotModChips() {{
        var $modBox = $('#mcmodHotModChips');
        if (!$modBox.length) return;
        $modBox.empty();
        $modBox.toggleClass('expanded-chips', modListExpanded);
        $modBox.closest('.hub-filter-row').toggleClass('row-expanded', modListExpanded);
        $modBox.append('<span class="s-chip active" data-mod="">全部</span>');
        var items = modListExpanded ? allModsList.slice(0, 100) : allModsList.slice(0, 40);
        for (var i = 0; i < items.length; i++) {{
            var m = items[i];
            var cnt = modCountsMap.get(m) || 0;
            $modBox.append('<span class="s-chip" data-mod="' + escHtml(m, true) + '">' + escHtml(m, true) + ' <span class="s-chip-count">' + cnt + '</span></span>');
        }}
        syncAllFilterUI();
    }}

    function syncAllFilterUI() {{
        var selCats = $('#categoryFilter').val() || [];
        if (!Array.isArray(selCats)) selCats = selCats ? [selCats] : [];
        var selTags = $('#packTagFilter').val() || [];
        if (!Array.isArray(selTags)) selTags = selTags ? [selTags] : [];
        var selModCats = $('#modCategoryFilter').val() || [];
        if (!Array.isArray(selModCats)) selModCats = selModCats ? [selModCats] : [];
        var selMods = $('#modFilter').val() || [];
        if (!Array.isArray(selMods)) selMods = selMods ? [selMods] : [];
        var selType = $('#typeFilter').val() || '';
        var selTrend = $('#trendFilter').val() || '';

        // 1. 同步官方专区 Chips
        $('#mcmodCategoryChips .s-chip').each(function() {{
            var c = $(this).data('cat');
            if (!c) {{
                $(this).toggleClass('active', selCats.length === 0);
            }} else {{
                $(this).toggleClass('active', selCats.indexOf(c) !== -1);
            }}
        }});

        // 2. 同步核心标签 Chips
        $('#mcmodTagChips .s-chip').each(function() {{
            var t = $(this).data('tag');
            if (!t) {{
                $(this).toggleClass('active', selTags.length === 0);
            }} else {{
                $(this).toggleClass('active', selTags.indexOf(t) !== -1);
            }}
        }});

        // 3. 同步模组分类 Chips
        $('#mcmodModCatChips .s-chip').each(function() {{
            var mc = $(this).data('mod-cat');
            if (!mc) {{
                $(this).toggleClass('active', selModCats.length === 0);
            }} else {{
                $(this).toggleClass('active', selModCats.indexOf(mc) !== -1);
            }}
        }});

        // 4. 同步包含模组 Chips
        $('#mcmodHotModChips .s-chip').each(function() {{
            var m = $(this).data('mod');
            if (!m) {{
                $(this).toggleClass('active', selMods.length === 0);
            }} else {{
                $(this).toggleClass('active', selMods.indexOf(m) !== -1);
            }}
        }});

        // 5. 渲染 activeFilters 胶囊指示栏 (参考黄游 active-filters)
        var $activeBox = $('#activeFilters');
        var badges = [];
        selCats.forEach(function(c) {{ badges.push({{ field: 'cat', label: '🏷️ 专区: ' + c, val: c }}); }});
        selTags.forEach(function(t) {{ badges.push({{ field: 'tag', label: '🔥 标签: ' + t, val: t }}); }});
        selModCats.forEach(function(mc) {{ badges.push({{ field: 'modcat', label: '📦 模组分类: ' + mc, val: mc }}); }});
        selMods.forEach(function(m) {{ badges.push({{ field: 'mod', label: '🧩 模组: ' + m, val: m }}); }});
        if (selType) {{
            badges.push({{ field: 'type', label: '类型: ' + selType, val: selType }});
        }}
        if (selTrend) {{
            var trendText = $('#trendFilter option:selected').text() || selTrend;
            badges.push({{ field: 'trend', label: '走势: ' + trendText, val: selTrend }});
        }}

        if (badges.length === 0) {{
            $activeBox.empty().hide();
        }} else {{
            var badgeHtml = '<span style="font-size:12px; font-weight:750; color:var(--text-secondary); margin-right:4px;">已筛选：</span>';
            badgeHtml += badges.map(function(b) {{
                return '<span class="active-filter-badge" data-field="' + b.field + '" data-val="' + escHtml(b.val, true) + '" title="点击移除该条件">' +
                    escHtml(b.label, true) +
                    '<span class="badge-del">×</span>' +
                '</span>';
            }}).join('');
            if (badges.length >= 2) {{
                badgeHtml += '<button type="button" class="active-filters-clear-all" id="clearAllActiveFilters">清空全部筛选 ↺</button>';
            }}
            $activeBox.html(badgeHtml).show();
        }}
    }}

    function openPicker(field, list, countMap, title, eyebrow, ruleHint) {{
        var $modal = $('#mcmodPickerModal');
        var modalEl = $modal[0];
        if (!modalEl) return;
        $('#pickerModalEyebrow').text(eyebrow || 'DISCOVERY');
        var selector = field === 'tag' ? '#packTagFilter' : '#modFilter';
        var selected = $(selector).val() || [];
        if (!Array.isArray(selected)) selected = selected ? [selected] : [];

        var html = '<h3 id="pickerModalTitle" style="font-size:1.25rem; font-weight:800; margin:0 0 6px; color:var(--text);">' + escHtml(title, true) + '</h3>' +
            '<div class="picker-toolbar">' +
                '<input id="pickerModalSearch" type="search" placeholder="输入名称实时模糊搜索（支持中英文）…" autocomplete="off">' +
                '<p>' + escHtml(ruleHint, true) + '</p>' +
            '</div>' +
            '<div class="picker-grid" id="pickerModalGrid"></div>' +
            '<div class="picker-footer">' +
                '<span id="pickerModalStatus">已选 ' + selected.length + ' 项 · 共 ' + list.length + ' 项</span>' +
                '<button type="button" class="picker-clear-btn" id="pickerModalClear">清空选择</button>' +
                '<button type="button" class="picker-done-btn" id="pickerModalDone">完成</button>' +
            '</div>';

        $('#pickerModalBody').html(html);

        var currentCap = 300;
        var filtered = list;

        function buildItemHtml(item, curSelected) {{
            var name = typeof item === 'string' ? item : (item.name || '');
            var count = countMap ? (countMap.get(name) || (typeof item === 'object' ? item.count : 0) || 0) : 0;
            var isActive = curSelected.indexOf(name) !== -1;
            return '<button type="button" class="picker-option' + (isActive ? ' active' : '') + '" data-picker-val="' + escHtml(name, true) + '">' +
                '<span>' + escHtml(name, true) + '</span>' +
                (count ? '<b class="tag-count">(' + count + ')</b>' : '') +
            '</button>';
        }}

        function updateStatus() {{
            var curSelected = $(selector).val() || [];
            if (!Array.isArray(curSelected)) curSelected = curSelected ? [curSelected] : [];
            var shown = Math.min(filtered.length, currentCap);
            var statusText = '已选 ' + curSelected.length + ' 项 · 找到 ' + filtered.length + ' 项';
            if (filtered.length > shown) {{
                statusText += '（已呈现前 ' + shown + ' 项 · 下滑或点击底部自动加载更多）';
            }} else {{
                statusText += '（已全部呈现）';
            }}
            $('#pickerModalStatus').text(statusText);
        }}

        function renderGrid() {{
            var query = ($('#pickerModalSearch').val() || '').trim().toLowerCase();
            var curSelected = $(selector).val() || [];
            if (!Array.isArray(curSelected)) curSelected = curSelected ? [curSelected] : [];

            filtered = list;
            if (query) {{
                filtered = list.filter(function(item) {{
                    var name = typeof item === 'string' ? item : (item.name || '');
                    return name.toLowerCase().indexOf(query) !== -1;
                }});
            }}

            currentCap = query ? 500 : 300;
            var displayItems = filtered.slice(0, currentCap);

            var gridHtml = '';
            if (displayItems.length === 0) {{
                gridHtml = '<div style="grid-column:1/-1; padding:2.5rem; text-align:center; color:var(--text-muted);">🔍 没有找到匹配项，试试其他关键词</div>';
            }} else {{
                for (var i = 0; i < displayItems.length; i++) {{
                    gridHtml += buildItemHtml(displayItems[i], curSelected);
                }}
                if (filtered.length > currentCap) {{
                    gridHtml += '<div id="pickerMoreBar" style="grid-column:1/-1; text-align:center; padding:12px 0;">' +
                        '<button type="button" id="btnPickerLoadMore" style="background:var(--primary); color:#fff; border:none; border-radius:8px; padding:8px 20px; font-weight:700; cursor:pointer; font-size:0.88rem; box-shadow:0 3px 10px rgba(0,0,0,0.15);">' +
                            '📥 加载更多 200 项 (剩余 ' + (filtered.length - currentCap) + ' 项) ▾' +
                        '</button>' +
                    '</div>';
                }}
            }}
            $('#pickerModalGrid').html(gridHtml);
            updateStatus();
        }}

        function loadMoreBatch() {{
            if (currentCap >= filtered.length) return;
            var curSelected = $(selector).val() || [];
            if (!Array.isArray(curSelected)) curSelected = curSelected ? [curSelected] : [];
            var start = currentCap;
            var end = Math.min(filtered.length, currentCap + 200);
            currentCap = end;

            $('#pickerMoreBar').remove();
            var appendHtml = '';
            for (var i = start; i < end; i++) {{
                appendHtml += buildItemHtml(filtered[i], curSelected);
            }}
            if (filtered.length > currentCap) {{
                appendHtml += '<div id="pickerMoreBar" style="grid-column:1/-1; text-align:center; padding:12px 0;">' +
                    '<button type="button" id="btnPickerLoadMore" style="background:var(--primary); color:#fff; border:none; border-radius:8px; padding:8px 20px; font-weight:700; cursor:pointer; font-size:0.88rem; box-shadow:0 3px 10px rgba(0,0,0,0.15);">' +
                        '📥 加载更多 200 项 (剩余 ' + (filtered.length - currentCap) + ' 项) ▾' +
                    '</button>' +
                '</div>';
            }}
            $('#pickerModalGrid').append(appendHtml);
            updateStatus();
        }}

        renderGrid();

        // 触底自动滚动加载 + 按钮手动点击加载，平滑展现所有万级模组
        $('#pickerModalGrid').off('scroll').on('scroll', function() {{
            var el = this;
            if (el.scrollHeight - el.scrollTop - el.clientHeight < 260) {{
                loadMoreBatch();
            }}
        }});

        $('#pickerModalGrid').off('click', '#btnPickerLoadMore').on('click', '#btnPickerLoadMore', function(e) {{
            e.preventDefault();
            loadMoreBatch();
        }});

        $('#pickerModalSearch').on('input', function() {{
            renderGrid();
        }});

        $('#pickerModalGrid').off('click', '.picker-option').on('click', '.picker-option', function() {{
            var val = $(this).attr('data-picker-val');
            toggleMultiSelect(selector, val);
            var curSelected = $(selector).val() || [];
            if (!Array.isArray(curSelected)) curSelected = curSelected ? [curSelected] : [];
            $(this).toggleClass('active', curSelected.indexOf(val) !== -1);
            updateStatus();
            syncAllFilterUI();
        }});

        $('#pickerModalClear').off('click').on('click', function() {{
            $(selector).val(null).trigger('change');
            $('#pickerModalGrid .picker-option').removeClass('active');
            updateStatus();
            syncAllFilterUI();
        }});

        $('#pickerModalDone').off('click').on('click', function() {{
            if (modalEl.close) modalEl.close();
            else $modal.hide();
            syncAllFilterUI();
        }});

        if (modalEl.showModal) modalEl.showModal();
        else $modal.show();
        setTimeout(function() {{ $('#pickerModalSearch').focus(); }}, 100);
    }}

    function initSidebarChips() {{
        analyzeCompareData();
        renderCategoryChips();
        renderTagChips();
        renderModCatChips();
        renderHotModChips();

        // 5. B站自制玩法分类 Chips
        var $biliBox = $('#biliCategoryChips');
        $biliBox.empty();
        $biliBox.append('<span class="s-chip active" data-cat="">全部</span>');
        BILI_REAL_CATEGORIES.forEach(function(item) {{
            $biliBox.append('<span class="s-chip" data-cat="' + escHtml(item.cat, true) + '">' + escHtml(item.cat, true) + ' <span class="s-chip-count">' + item.count + '</span></span>');
        }});

        // 6. 全平台热门分类 Chips
        var $allBox = $('#allCategoryChips');
        if ($allBox.length) {{
            $allBox.empty();
            ALL_REAL_CATEGORIES.forEach(function(item) {{
                $allBox.append('<span class="s-chip" data-cat="' + escHtml(item.cat, true) + '">' + escHtml(item.cat, true) + ' <span class="s-chip-count">' + item.count + '</span></span>');
            }});
        }}
    }}
    initSidebarChips();

    window.renderSidebarTags = function(tab) {{
        if (tab === 'mcmod') {{
            $('#sidebarMcmodFilters').show();
            $('#sidebarBiliFilters').hide();
            $('#sidebarAllFilters').hide();
            // 同步 MCMod 激活分类
            var curVals = $('#categoryFilter').val() || [];
            if (!Array.isArray(curVals)) curVals = [curVals];
            $('#mcmodCategoryChips .s-chip').each(function() {{
                var c = $(this).data('cat');
                if (curVals.indexOf(c) !== -1) {{
                    $(this).addClass('active');
                }} else {{
                    $(this).removeClass('active');
                }}
            }});
        }} else if (tab === 'bilibili') {{
            $('#sidebarBiliFilters').show();
            $('#sidebarMcmodFilters').hide();
            $('#sidebarAllFilters').hide();
            $('#biliCategoryChips .s-chip').each(function() {{
                var c = $(this).data('cat');
                if (activeCat.indexOf(c) !== -1) {{
                    $(this).addClass('active');
                }} else {{
                    $(this).removeClass('active');
                }}
            }});
            $('#biliDateChips .s-chip').each(function() {{
                var d = $(this).data('date') || '';
                if (activeDate === d) {{
                    $(this).addClass('active');
                }} else {{
                    $(this).removeClass('active');
                }}
            }});
            $('#biliPanChips .s-chip').each(function() {{
                var p = $(this).data('pan') || '';
                if (activePan === p) {{
                    $(this).addClass('active');
                }} else {{
                    $(this).removeClass('active');
                }}
            }});
        }} else {{
            $('#sidebarAllFilters').show();
            $('#sidebarMcmodFilters').hide();
            $('#sidebarBiliFilters').hide();
        }}
    }};

        /* 全局跨标签页搜索同步与穿透跳转引擎 */
    function getActiveSearchQuery() {{
        if (currentTab === 'all') return ($('#crossSearchInput').val() || '').trim();
        if (currentTab === 'bilibili') return ($('#biliSearchInput').val() || '').trim();
        if (currentTab === 'bbsmc') return ($('#bbsmcSearchInput').val() || '').trim();
        if (currentTab === 'xyebbs') return ($('#xyebbsSearchInput').val() || '').trim();
        if (currentTab === 'modrinth') return ($('#modrinthSearchInput').val() || '').trim();
        if (currentTab === 'curseforge') return ($('#curseforgeSearchInput').val() || '').trim();
        if (currentTab === 'mcmod') {{
            return ($('#mcmodUnifiedSearch').val() || (window.table ? window.table.search() : '') || '').trim();
        }}
        return '';
    }}

    window.jumpToPlatformSearch = function(plat, query) {{
        var qStr = (query !== undefined && query !== null) ? String(query).trim() : '';
        if (plat === 'mcmod') {{
            $('#mcmodUnifiedSearch').val(qStr);
        }} else if (plat === 'bilibili') {{
            $('#biliSearchInput').val(qStr);
            if (qStr) $('#biliSearchClear').show(); else $('#biliSearchClear').hide();
        }} else if (plat === 'bbsmc') {{
            $('#bbsmcSearchInput').val(qStr);
            if (qStr) $('#bbsmcSearchClear').show(); else $('#bbsmcSearchClear').hide();
        }} else if (plat === 'xyebbs') {{
            $('#xyebbsSearchInput').val(qStr);
            if (qStr) $('#xyebbsSearchClear').show(); else $('#xyebbsSearchClear').hide();
        }} else if (plat === 'modrinth') {{
            $('#modrinthSearchInput').val(qStr);
            if (qStr) $('#modrinthSearchClear').show(); else $('#modrinthSearchClear').hide();
        }} else if (plat === 'curseforge') {{
            $('#curseforgeSearchInput').val(qStr);
            if (qStr) $('#curseforgeSearchClear').show(); else $('#curseforgeSearchClear').hide();
        }}

        switchPlatformTab(plat);

        loadPlatformScript(plat, function() {{
            if (plat === 'mcmod') {{
                if (window.table && qStr) {{
                    window.table.search(qStr).draw();
                }}
                if (typeof renderMcmodCards === 'function' && activeMcmodVMode === 'cards') {{
                    renderMcmodCards();
                }}
            }} else if (plat === 'bilibili') {{
                if (typeof renderBiliView === 'function') renderBiliView();
            }} else if (plat === 'bbsmc') {{
                if (typeof renderBbsmcView === 'function') renderBbsmcView();
            }} else if (plat === 'xyebbs') {{
                if (typeof renderXyebbsView === 'function') renderXyebbsView();
            }} else if (plat === 'modrinth') {{
                if (typeof renderModrinthView === 'function') renderModrinthView();
            }} else if (plat === 'curseforge') {{
                if (typeof renderCurseforgeView === 'function') renderCurseforgeView();
            }}
        }});
    }};

    function syncSearchQueryToTab(targetTab, query) {{
        if (!query) return;
        window.jumpToPlatformSearch(targetTab, query);
    }}

    window.jumpToPlatformWithCurrentSearch = function(plat) {{
        var q = ($('#crossSearchInput').val() || '').trim();
        window.jumpToPlatformSearch(plat, q);
    }};

    $(document).on('click', '.js-jump-platform-search', function(e) {{
        e.stopPropagation();
        var plat = $(this).data('platform');
        var query = $(this).data('query');
        window.jumpToPlatformSearch(plat, query);
    }});

    window.switchPlatformTab = function(tab) {{
        $('.nav-item').removeClass('active');
        $('.nav-item[data-tab="' + tab + '"]').addClass('active');
        $('.top-plat-btn').removeClass('active');
        $('.top-plat-btn[data-tab="' + tab + '"]').addClass('active');
        currentTab = tab;
        window.scrollTo(0, 0);

        renderSidebarTags(tab);

        if (tab === 'all') {{
            $('#view-all').show().addClass('active');
            $('#view-mcmod, #view-bilibili, #view-bbsmc, #view-xyebbs, #view-modrinth, #view-curseforge').hide().removeClass('active');
            $('#mcmodViewToggle, #biliViewToggle').hide();
            $('#crumbCurrentTab').text('全平台总览');
            $('#crumbCurrentView').text('综合大盘');
            window.location.hash = '#all';
        }} else if (tab === 'bilibili') {{
            $('#view-all, #view-mcmod, #view-bbsmc, #view-xyebbs, #view-modrinth, #view-curseforge').hide().removeClass('active');
            $('#view-bilibili').show().addClass('active');
            $('#mcmodViewToggle').hide();
            $('#biliViewToggle').show();
            $('#crumbCurrentTab').text('B站自制整合包');
            $('#crumbCurrentView').text(activeGroupMode === 'grouped' ? '同包聚合' : '单条平铺');
            window.location.hash = '#bilibili';
            if (!renderedTabs['bilibili']) {{
                if (!PLATFORMS['bilibili'].loaded && (!window.biliModpacksData || !window.biliModpacksData.length)) {{
                    $('#biliCardsGrid').html('<div class="platform-loading-box" style="grid-column:1/-1; text-align:center; padding:3.5rem; color:var(--text-secondary);"><div style="font-size:2rem; margin-bottom:0.5rem; animation:pulse 1s infinite;">📺</div>正在极速接入 B站 935 款自制整合包发布流...</div>');
                }}
                loadPlatformScript('bilibili', function() {{
                    renderBiliView();
                    renderedTabs['bilibili'] = true;
                }});
            }}
        }} else if (tab === 'bbsmc') {{
            $('#view-all, #view-mcmod, #view-bilibili, #view-xyebbs, #view-modrinth, #view-curseforge').hide().removeClass('active');
            $('#view-bbsmc').show().addClass('active');
            $('#mcmodViewToggle, #biliViewToggle').hide();
            $('#crumbCurrentTab').text('BBSMC开放资源');
            $('#crumbCurrentView').text('开源模组包库');
            window.location.hash = '#bbsmc';
            if (!renderedTabs['bbsmc']) {{
                if (!PLATFORMS['bbsmc'].loaded && (!window.bbsmcModpacksData || !window.bbsmcModpacksData.length)) {{
                    $('#bbsmcCardsGrid').html('<div class="platform-loading-box" style="grid-column:1/-1; text-align:center; padding:3.5rem; color:var(--text-secondary);"><div style="font-size:2rem; margin-bottom:0.5rem; animation:pulse 1s infinite;">💎</div>正在极速接入 BBSMC 1,802 款开源模组包...</div>');
                }}
                loadPlatformScript('bbsmc', function() {{
                    renderBbsmcView();
                    renderedTabs['bbsmc'] = true;
                }});
            }}
        }} else if (tab === 'xyebbs') {{
            $('#view-all, #view-mcmod, #view-bilibili, #view-bbsmc, #view-modrinth, #view-curseforge').hide().removeClass('active');
            $('#view-xyebbs').show().addClass('active');
            $('#mcmodViewToggle, #biliViewToggle').hide();
            $('#crumbCurrentTab').text('XYEBBS像素世界');
            $('#crumbCurrentView').text('社区资源专区');
            window.location.hash = '#xyebbs';
            if (!renderedTabs['xyebbs']) {{
                if (!PLATFORMS['xyebbs'].loaded && (!window.xyebbsModpacksData || !window.xyebbsModpacksData.length)) {{
                    $('#xyebbsCardsGrid').html('<div class="platform-loading-box" style="grid-column:1/-1; text-align:center; padding:3.5rem; color:var(--text-secondary);"><div style="font-size:2rem; margin-bottom:0.5rem; animation:pulse 1s infinite;">🍃</div>正在极速接入 XYEBBS 5,175 款社区整合包...</div>');
                }}
                loadPlatformScript('xyebbs', function() {{
                    renderXyebbsView();
                    renderedTabs['xyebbs'] = true;
                }});
            }}
        }} else if (tab === 'modrinth') {{
            $('#view-all, #view-mcmod, #view-bilibili, #view-bbsmc, #view-xyebbs, #view-curseforge').hide().removeClass('active');
            $('#view-modrinth').show().addClass('active');
            $('#mcmodViewToggle, #biliViewToggle').hide();
            $('#crumbCurrentTab').text('Modrinth国际服');
            $('#crumbCurrentView').text('开源模组包库');
            window.location.hash = '#modrinth';
            if (!renderedTabs['modrinth']) {{
                if (!PLATFORMS['modrinth'].loaded && (!window.modrinthModpacksData || !window.modrinthModpacksData.length)) {{
                    $('#modrinthCardsGrid').html('<div class="platform-loading-box" style="grid-column:1/-1; text-align:center; padding:3.5rem; color:var(--text-secondary);"><div style="font-size:2rem; margin-bottom:0.5rem; animation:pulse 1s infinite;">🌐</div>正在极速接入 Modrinth 18,328 款开源模组包...</div>');
                }}
                loadPlatformScript('modrinth', function() {{
                    renderModrinthView();
                    renderedTabs['modrinth'] = true;
                }});
            }}
        }} else if (tab === 'curseforge') {{
            $('#view-all, #view-mcmod, #view-bilibili, #view-bbsmc, #view-xyebbs, #view-modrinth').hide().removeClass('active');
            $('#view-curseforge').show().addClass('active');
            $('#mcmodViewToggle, #biliViewToggle').hide();
            $('#crumbCurrentTab').text('CurseForge国际服');
            $('#crumbCurrentView').text('全球殿堂包专区');
            window.location.hash = '#curseforge';
            if (!renderedTabs['curseforge']) {{
                if (!PLATFORMS['curseforge'].loaded && (!window.curseforgeModpacksData || !window.curseforgeModpacksData.length)) {{
                    $('#curseforgeCardsGrid').html('<div class="platform-loading-box" style="grid-column:1/-1; text-align:center; padding:3.5rem; color:var(--text-secondary);"><div style="font-size:2rem; margin-bottom:0.5rem; animation:pulse 1s infinite;">🔥</div>正在极速接入 CurseForge 45,797 款全球殿堂巨作...</div>');
                }}
                loadPlatformScript('curseforge', function() {{
                    renderCurseforgeView();
                    renderedTabs['curseforge'] = true;
                }});
            }}
        }} else {{
            $('#view-all, #view-bilibili, #view-bbsmc, #view-xyebbs, #view-modrinth, #view-curseforge').hide().removeClass('active');
            $('#view-mcmod').show().addClass('active');
            $('#mcmodViewToggle').show();
            $('#biliViewToggle').hide();
            $('#crumbCurrentTab').text('MC百科整合包');
            $('#crumbCurrentView').text(activeMcmodVMode === 'cards' ? '画廊卡片' : '专业多维表格');
            window.location.hash = '#mcmod';
            if (!renderedTabs['mcmod']) {{
                loadPlatformScript('mcmod', function() {{
                    if (activeMcmodVMode === 'cards') {{
                        renderMcmodCards();
                    }} else if (window.initMcmodTable) {{
                        window.initMcmodTable();
                    }}
                    renderedTabs['mcmod'] = true;
                }});
            }} else {{
                if (activeMcmodVMode === 'cards') {{
                    renderMcmodCards();
                }} else if (!$.fn.DataTable.isDataTable('#modpackTable') && window.initMcmodTable) {{
                    window.initMcmodTable();
                }} else if (window.table) {{
                    window.table.columns.adjust();
                }}
            }}
        }}
    }};

    $(document).on('click', '.nav-item', function() {{
        var tab = $(this).data('tab');
        if (tab) switchPlatformTab(tab);
    }});

    if (window.location.hash === '#mcmod') {{
        switchPlatformTab('mcmod');
    }} else if (window.location.hash === '#modrinth') {{
        switchPlatformTab('modrinth');
    }} else if (window.location.hash === '#curseforge') {{
        switchPlatformTab('curseforge');
    }} else if (window.location.hash === '#bilibili') {{
        switchPlatformTab('bilibili');
    }} else if (window.location.hash === '#bbsmc') {{
        switchPlatformTab('bbsmc');
    }} else if (window.location.hash === '#xyebbs') {{
        switchPlatformTab('xyebbs');
    }} else {{
        switchPlatformTab('all');
    }}

    /* 跨平台联合穿透搜索交互 */
        // 热门快搜标签点击即搜
    $(document).on('click', '.hot-chip', function() {{
        var q = $(this).data('query');
        $('#crossSearchInput').val(q).trigger('input').focus();
    }});

    // 清空搜索按钮点击
    $('#crossSearchClear').on('click', function() {{
        $('#crossSearchInput').val('').trigger('input').focus();
    }});

    // 全局快捷键 Ctrl+K / '/' 聚焦跨平台搜索框
    $(document).on('keydown', function(e) {{
        if ((e.ctrlKey && (e.key === 'k' || e.key === 'K')) || (e.key === '/' && !$(e.target).is('input, textarea, select'))) {{
            e.preventDefault();
            if ($('#view-all').is(':visible')) {{
                $('#crossSearchInput').focus().select();
            }} else {{
                switchPlatformTab('all');
                setTimeout(function() {{
                    $('#crossSearchInput').focus().select();
                }}, 150);
            }}
        }} else if (e.key === 'Escape' && $('#crossSearchInput').is(':focus')) {{
            $('#crossSearchInput').val('').trigger('input').blur();
        }}
    }});

    /* 跨平台联合穿透搜索交互 */
    $('#crossSearchInput').on('input', function() {{
        var query = $(this).val().trim().toLowerCase();
        var $clearBtn = $('#crossSearchClear');
        var $grid = $('#crossResultsGrid');
        var $mcBox = $('#crossMcmodResults');
        var $biliBox = $('#crossBiliResults');
        var $bbsmcBox = $('#crossBbsmcResults');
        var $xyebbsBox = $('#crossXyebbsResults');
        var $modrinthBox = $('#crossModrinthResults');
        var $curseforgeBox = $('#crossCurseforgeResults');

        if (!query) {{
            $clearBtn.hide();
            $grid.removeClass('active').hide().css('display', 'none');
            $mcBox.empty();
            $biliBox.empty();
            $bbsmcBox.empty();
            $xyebbsBox.empty();
            $modrinthBox.empty();
            $curseforgeBox.empty();
            return;
        }}

        $clearBtn.show();
        $grid.addClass('active').show().css('display', 'grid');

        // 1. 搜索 MC百科
        var mcMatches = [];
        var mcRows = window.tableRowsData || [];
        for (var i = 0; i < mcRows.length; i++) {{
            var r = mcRows[i];
            var searchTxt = ((r.title || '') + ' ' + (r.title_en || '') + ' ' + (r.category || '') + ' ' + (r.tags_search || '') + ' ' + (r.c6 || '')).toLowerCase();
            if (searchTxt.indexOf(query) !== -1) {{
                mcMatches.push(r);
                if (mcMatches.length >= 4) break;
            }}
        }}

        if (mcMatches.length === 0) {{
            $mcBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 MC百科 词条</div>');
        }} else {{
            var mcHtml = '';
            mcMatches.forEach(function(item) {{
                var ver = extractVersion(item);
                var safeTitle = $('<div>').text(item.title || '').html();
                var coverSrc = item.cover_url || window.MC_COVER_FALLBACK || MC_COVER_FALLBACK;
                var extUrl = item.link || ('https://www.mcmod.cn/modpack/' + item.mid + '.html');
                mcHtml += '<div class="cross-result-item js-cross-mc-item" data-title="' + safeTitle + '">';
                mcHtml += '  <img class="cross-thumb" src="' + coverSrc + '" referrerpolicy="no-referrer" loading="lazy" onerror="this.onerror=null;this.src=window.MC_COVER_FALLBACK;">';
                mcHtml += '  <div class="cross-item-info">';
                mcHtml += '    <div class="cross-item-title">' + safeTitle + '</div>';
                mcHtml += '    <div class="cross-item-sub">';
                if (ver) mcHtml += '<span style="color:var(--primary); font-weight:700;">' + ver + '</span>';
                mcHtml += '<span>' + (item.category || '整合') + '</span>';
                mcHtml += '<span>👁️ ' + (item.views_display || item.views || 0) + '</span>';
                mcHtml += '    </div>';
                mcHtml += '    <div class="cross-item-actions">';
                mcHtml += '      <button type="button" class="cross-action-btn cross-btn-in js-jump-platform-search" data-platform="mcmod" data-query="' + safeTitle + '" title="在站内筛选查看该项目">站内 ➔</button>';
                mcHtml += '      <a href="' + extUrl + '" target="_blank" rel="noopener noreferrer" class="cross-action-btn cross-btn-ext" onclick="event.stopPropagation();" title="在新标签页直接打开原站网页">原站 ↗</a>';
                mcHtml += '    </div>';
                mcHtml += '  </div>';
                mcHtml += '</div>';
            }});
            $mcBox.html(mcHtml);
        }}

        // 2. 搜索 B站
        var biliMatches = [];
        var bPacks = window.biliModpacksData || [];
        if ((!window.biliModpacksData || !window.biliModpacksData.length) && typeof loadPlatformScript === 'function') {{
            loadPlatformScript('bilibili');
        }}
        if (PLATFORMS['bilibili'] && !PLATFORMS['bilibili'].loaded && (!bPacks || !bPacks.length)) {{
            $biliBox.html('<div style="font-size:12px; color:var(--primary); padding:10px 0;">⏳ B站自制数据加载中...</div>');
        }} else {{
            for (var j = 0; j < bPacks.length; j++) {{
                var bp = bPacks[j];
                var bTxt = ((bp.title || '') + ' ' + (bp.author || '') + ' ' + (bp.desc || '') + ' ' + (bp.mc_version || '') + ' ' + (bp.subtitle_text || '')).toLowerCase();
                if (bTxt.indexOf(query) !== -1) {{
                    biliMatches.push(bp);
                    if (biliMatches.length >= 4) break;
                }}
            }}

            if (biliMatches.length === 0) {{
                $biliBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 B站 视频</div>');
            }} else {{
                var bHtml = '';
                biliMatches.forEach(function(bp) {{
                    var vStr = bp.views > 10000 ? (bp.views / 10000).toFixed(1) + '万' : bp.views;
                    var pic = bp.pic ? (bp.pic.replace('http://', 'https://') + '@200w_125h_1c.webp') : window.BILI_COVER_FALLBACK;
                    var safeTitle = $('<div>').text(bp.title || '').html();
                    bHtml += '<div class="cross-result-item js-cross-bili-item" data-title="' + safeTitle + '">';
                    bHtml += '  <img class="cross-thumb" src="' + pic + '" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=window.BILI_COVER_FALLBACK;">';
                    bHtml += '  <div class="cross-item-info">';
                    bHtml += '    <div class="cross-item-title">' + safeTitle + '</div>';
                    var bExtUrl = bp.arcurl || ('https://www.bilibili.com/video/' + bp.bvid);
                    bHtml += '    <div class="cross-item-sub">';
                    bHtml += '<span style="color:#fb7299; font-weight:700;">UP: ' + $('<div>').text(bp.author || '未知').html() + '</span>';
                    bHtml += '<span>👁️ ' + vStr + '</span>';
                    if (bp.download_links && bp.download_links.length > 0) {{
                        bHtml += '<span style="color:#10b981; font-weight:700;">📦 网盘可用</span>';
                    }}
                    bHtml += '    </div>';
                    bHtml += '    <div class="cross-item-actions">';
                    bHtml += '      <button type="button" class="cross-action-btn cross-btn-in js-jump-platform-search" data-platform="bilibili" data-query="' + safeTitle + '" title="在站内筛选查看该项目">站内 ➔</button>';
                    bHtml += '      <a href="' + bExtUrl + '" target="_blank" rel="noopener noreferrer" class="cross-action-btn cross-btn-ext" onclick="event.stopPropagation();" title="在新标签页直接打开 B站 视频">原站 ↗</a>';
                    bHtml += '    </div>';
                    bHtml += '  </div>';
                    bHtml += '</div>';
                }});
                $biliBox.html(bHtml);
            }}
        }}

        // 3. 搜索 BBSMC
        var bbsmcMatches = [];
        var bPacksBbs = window.bbsmcModpacksData || [];
        if ((!window.bbsmcModpacksData || !window.bbsmcModpacksData.length) && typeof loadPlatformScript === 'function') {{
            loadPlatformScript('bbsmc');
        }}
        if (PLATFORMS['bbsmc'] && !PLATFORMS['bbsmc'].loaded && (!bPacksBbs || !bPacksBbs.length)) {{
            $bbsmcBox.html('<div style="font-size:12px; color:var(--primary); padding:10px 0;">⏳ BBSMC数据加载中...</div>');
        }} else {{
            for (var k = 0; k < bPacksBbs.length; k++) {{
                var bb = bPacksBbs[k];
                var bbTxt = ((bb.title || '') + ' ' + (bb.author || '') + ' ' + (bb.description || '') + ' ' + (bb.mc_version || '') + ' ' + (bb.loaders || []).join(' ') + ' ' + (bb.categories || []).join(' ')).toLowerCase();
                if (bbTxt.indexOf(query) !== -1) {{
                    bbsmcMatches.push(bb);
                    if (bbsmcMatches.length >= 4) break;
                }}
            }}

            if (bbsmcMatches.length === 0) {{
                $bbsmcBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 BBSMC 资源</div>');
            }} else {{
                var bbHtml = '';
                bbsmcMatches.forEach(function(bb) {{
                    var dlStr = bb.downloads > 10000 ? (bb.downloads / 10000).toFixed(1) + '万' : bb.downloads;
                    var pic = bb.featured_gallery || (bb.gallery && bb.gallery[0]) || bb.icon_url || window.BBSMC_COVER_FALLBACK;
                    var safeTitle = $('<div>').text(bb.title || '').html();
                    var bbExtUrl = bb.url || ('https://www.bbsmc.net/item/' + bb.id);
                    bbHtml += '<div class="cross-result-item js-cross-bbsmc-item" data-title="' + safeTitle + '">';
                    bbHtml += '  <img class="cross-thumb" src="' + pic + '" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=window.BBSMC_COVER_FALLBACK;">';
                    bbHtml += '  <div class="cross-item-info">';
                    bbHtml += '    <div class="cross-item-title">' + safeTitle + '</div>';
                    bbHtml += '    <div class="cross-item-sub">';
                    bbHtml += '<span style="color:#00af5c; font-weight:700;">' + (bb.mc_version || '1.20.1') + '</span>';
                    bbHtml += '<span>作者: ' + $('<div>').text(bb.author || '未知').html() + '</span>';
                    bbHtml += '<span>📥 ' + dlStr + '</span>';
                    bbHtml += '    </div>';
                    bbHtml += '    <div class="cross-item-actions">';
                    bbHtml += '      <button type="button" class="cross-action-btn cross-btn-in js-jump-platform-search" data-platform="bbsmc" data-query="' + safeTitle + '" title="在站内筛选查看该项目">站内 ➔</button>';
                    bbHtml += '      <a href="' + bbExtUrl + '" target="_blank" rel="noopener noreferrer" class="cross-action-btn cross-btn-ext" onclick="event.stopPropagation();" title="在新标签页直接打开 BBSMC 原始页面">原站 ↗</a>';
                    bbHtml += '    </div>';
                    bbHtml += '  </div>';
                    bbHtml += '</div>';
                }});
                $bbsmcBox.html(bbHtml);
            }}
        }}

        // 4. 搜索 XYEBBS
        var xyebbsMatches = [];
        var bPacksXye = window.xyebbsModpacksData || [];
        if ((!window.xyebbsModpacksData || !window.xyebbsModpacksData.length) && typeof loadPlatformScript === 'function') {{
            loadPlatformScript('xyebbs');
        }}
        if (PLATFORMS['xyebbs'] && !PLATFORMS['xyebbs'].loaded && (!bPacksXye || !bPacksXye.length)) {{
            $xyebbsBox.html('<div style="font-size:12px; color:var(--primary); padding:10px 0;">⏳ XYEBBS数据加载中...</div>');
        }} else {{
            for (var m = 0; m < bPacksXye.length; m++) {{
                var xp = bPacksXye[m];
                var xpTxt = ((xp.title || '') + ' ' + (xp.author || '') + ' ' + (xp.description || '') + ' ' + (xp.mc_version || '') + ' ' + (xp.loaders || []).join(' ') + ' ' + (xp.categories || []).join(' ')).toLowerCase();
                if (xpTxt.indexOf(query) !== -1) {{
                    xyebbsMatches.push(xp);
                    if (xyebbsMatches.length >= 4) break;
                }}
            }}

            if (xyebbsMatches.length === 0) {{
                $xyebbsBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 XYEBBS 资源</div>');
            }} else {{
                var xpHtml = '';
                xyebbsMatches.forEach(function(xp) {{
                    var dlStr = xp.downloads > 10000 ? (xp.downloads / 10000).toFixed(1) + '万' : xp.downloads;
                    var pic = xp.head_url || xp.icon_url || window.XYEBBS_COVER_FALLBACK || window.BBSMC_COVER_FALLBACK;
                    var safeTitle = $('<div>').text(xp.title || '').html();
                    var xpExtUrl = xp.url || ('https://www.xyebbs.com/thread-' + xp.tid + '-1-1.html');
                    xpHtml += '<div class="cross-result-item js-cross-xyebbs-item" data-title="' + safeTitle + '">';
                    xpHtml += '  <img class="cross-thumb" src="' + pic + '" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=(window.XYEBBS_COVER_FALLBACK||window.BBSMC_COVER_FALLBACK);">';
                    xpHtml += '  <div class="cross-item-info">';
                    xpHtml += '    <div class="cross-item-title">' + safeTitle + '</div>';
                    xpHtml += '    <div class="cross-item-sub">';
                    xpHtml += '<span style="color:#16a34a; font-weight:700;">' + (xp.mc_version || '1.20.1') + '</span>';
                    xpHtml += '<span>作者: ' + $('<div>').text(xp.author || '未知').html() + '</span>';
                    xpHtml += '<span>📥 ' + dlStr + '</span>';
                    xpHtml += '    </div>';
                    xpHtml += '    <div class="cross-item-actions">';
                    xpHtml += '      <button type="button" class="cross-action-btn cross-btn-in js-jump-platform-search" data-platform="xyebbs" data-query="' + safeTitle + '" title="在站内筛选查看该项目">站内 ➔</button>';
                    xpHtml += '      <a href="' + xpExtUrl + '" target="_blank" rel="noopener noreferrer" class="cross-action-btn cross-btn-ext" onclick="event.stopPropagation();" title="在新标签页直接打开 XYEBBS 原始帖子">原站 ↗</a>';
                    xpHtml += '    </div>';
                    xpHtml += '  </div>';
                    xpHtml += '</div>';
                }});
                $xyebbsBox.html(xpHtml);
            }}
        }}

        // 5. 搜索 Modrinth
        var modrinthMatches = [];
        var mPacks = window.modrinthModpacksData || [];
        if ((!window.modrinthModpacksData || !window.modrinthModpacksData.length) && typeof loadPlatformScript === 'function') {{
            loadPlatformScript('modrinth');
        }}
        if (PLATFORMS['modrinth'] && !PLATFORMS['modrinth'].loaded && (!mPacks || !mPacks.length)) {{
            $modrinthBox.html('<div style="font-size:12px; color:var(--primary); padding:10px 0;">⏳ Modrinth数据加载中...</div>');
        }} else {{
            for (var mi = 0; mi < mPacks.length; mi++) {{
                var mp = mPacks[mi];
                var mTarget = ((mp.title || '') + ' ' + (mp.slug || '') + ' ' + (mp.author || '') + ' ' + (mp.description || '') + ' ' + (mp.categories || []).join(' ')).toLowerCase();
                if (mTarget.indexOf(query) !== -1) {{
                    modrinthMatches.push(mp);
                    if (modrinthMatches.length >= 4) break;
                }}
            }}

            if (modrinthMatches.length === 0) {{
                $modrinthBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 Modrinth 项目</div>');
            }} else {{
                var mHtml = '';
                modrinthMatches.forEach(function(mp) {{
                    var dlStr = mp.downloads > 10000 ? (mp.downloads / 10000).toFixed(1) + '万' : mp.downloads;
                    var pic = mp.icon_url || window.MODRINTH_COVER_FALLBACK;
                    var safeTitle = $('<div>').text(mp.title || '').html();
                    var mpExtUrl = mp.url || ('https://modrinth.com/modpack/' + (mp.slug || mp.id));
                    mHtml += '<div class="cross-result-item js-cross-modrinth-item" data-title="' + safeTitle + '">';
                    mHtml += '  <img class="cross-thumb" src="' + pic + '" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=window.MODRINTH_COVER_FALLBACK;">';
                    mHtml += '  <div class="cross-item-info">';
                    mHtml += '    <div class="cross-item-title">' + safeTitle + '</div>';
                    mHtml += '    <div class="cross-item-sub">';
                    mHtml += '<span style="color:#1bd96a; font-weight:700;">' + (mp.mc_version || '1.20.1') + '</span>';
                    mHtml += '<span>作者: ' + $('<div>').text(mp.author || '未知').html() + '</span>';
                    mHtml += '<span>📥 ' + dlStr + '</span>';
                    mHtml += '    </div>';
                    mHtml += '    <div class="cross-item-actions">';
                    mHtml += '      <button type="button" class="cross-action-btn cross-btn-in js-jump-platform-search" data-platform="modrinth" data-query="' + safeTitle + '" title="在站内筛选查看该项目">站内 ➔</button>';
                    mHtml += '      <a href="' + mpExtUrl + '" target="_blank" rel="noopener noreferrer" class="cross-action-btn cross-btn-ext" onclick="event.stopPropagation();" title="在新标签页直接打开 Modrinth 原始页面">原站 ↗</a>';
                    mHtml += '    </div>';
                    mHtml += '  </div>';
                    mHtml += '</div>';
                }});
                $modrinthBox.html(mHtml);
            }}
        }}

        // 6. 搜索 CurseForge
        var curseforgeMatches = [];
        var cfPacks = window.curseforgeModpacksData || [];
        if ((!window.curseforgeModpacksData || !window.curseforgeModpacksData.length) && typeof loadPlatformScript === 'function') {{
            loadPlatformScript('curseforge');
        }}
        if (PLATFORMS['curseforge'] && !PLATFORMS['curseforge'].loaded && (!cfPacks || !cfPacks.length)) {{
            $curseforgeBox.html('<div style="font-size:12px; color:var(--primary); padding:10px 0;">⏳ CurseForge数据加载中...</div>');
        }} else {{
            for (var cfi = 0; cfi < cfPacks.length; cfi++) {{
                var cp = cfPacks[cfi];
                var cpTarget = ((cp.title || '') + ' ' + (cp.slug || '') + ' ' + (cp.author || '') + ' ' + (cp.description || '') + ' ' + (cp.categories || []).join(' ')).toLowerCase();
                if (cpTarget.indexOf(query) !== -1) {{
                    curseforgeMatches.push(cp);
                    if (curseforgeMatches.length >= 4) break;
                }}
            }}

            if (curseforgeMatches.length === 0) {{
                $curseforgeBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 CurseForge 项目</div>');
            }} else {{
                var cfHtml = '';
                curseforgeMatches.forEach(function(cp) {{
                    var dlStr = cp.downloads > 10000 ? (cp.downloads / 10000).toFixed(1) + '万' : cp.downloads;
                    var pic = cp.icon_url || window.CURSEFORGE_COVER_FALLBACK;
                    var safeTitle = $('<div>').text(cp.title || '').html();
                    cfHtml += '<div class="cross-result-item js-cross-curseforge-item" data-title="' + safeTitle + '">';
                    cfHtml += '  <img class="cross-thumb" src="' + pic + '" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=window.CURSEFORGE_COVER_FALLBACK;">';
                    cfHtml += '  <div class="cross-item-info">';
                    cfHtml += '    <div class="cross-item-title">' + safeTitle + '</div>';
                    var cpExtUrl = cp.url || ('https://www.curseforge.com/minecraft/modpacks/' + (cp.slug || cp.id));
                    cfHtml += '    <div class="cross-item-sub">';
                    cfHtml += '<span style="color:#f16436; font-weight:700;">' + (cp.mc_version || '1.20.1') + '</span>';
                    cfHtml += '<span>作者: ' + $('<div>').text(cp.author || '未知').html() + '</span>';
                    cfHtml += '<span>📥 ' + dlStr + '</span>';
                    cfHtml += '    </div>';
                    cfHtml += '    <div class="cross-item-actions">';
                    cfHtml += '      <button type="button" class="cross-action-btn cross-btn-in js-jump-platform-search" data-platform="curseforge" data-query="' + safeTitle + '" title="在站内筛选查看该项目">站内 ➔</button>';
                    cfHtml += '      <a href="' + cpExtUrl + '" target="_blank" rel="noopener noreferrer" class="cross-action-btn cross-btn-ext" onclick="event.stopPropagation();" title="在新标签页直接打开 CurseForge 原始页面">原站 ↗</a>';
                    cfHtml += '    </div>';
                    cfHtml += '  </div>';
                    cfHtml += '</div>';
                }});
                $curseforgeBox.html(cfHtml);
            }}
        }}
    }});

    $(document).on('click', '.js-cross-mc-item', function() {{
        var t = $(this).attr('data-title');
        jumpToMcmodSearch(t);
    }});

    $(document).on('click', '.js-cross-bili-item', function() {{
        var t = $(this).attr('data-title');
        jumpToBiliSearch(t);
    }});

    $(document).on('click', '.js-cross-bbsmc-item', function() {{
        var t = $(this).attr('data-title');
        jumpToBbsmcSearch(t);
    }});

    $(document).on('click', '.js-cross-xyebbs-item', function() {{
        var t = $(this).attr('data-title');
        jumpToXyebbsSearch(t);
    }});

    window.jumpToMcmodSearch = function(title) {{ window.jumpToPlatformSearch('mcmod', title); }};
    window.jumpToBiliSearch = function(title) {{ window.jumpToPlatformSearch('bilibili', title); }};
    window.jumpToBbsmcSearch = function(title) {{ window.jumpToPlatformSearch('bbsmc', title); }};
    window.jumpToXyebbsSearch = function(title) {{ window.jumpToPlatformSearch('xyebbs', title); }};
    window.jumpToModrinthSearch = function(title) {{ window.jumpToPlatformSearch('modrinth', title); }};
    window.jumpToCurseforgeSearch = function(title) {{ window.jumpToPlatformSearch('curseforge', title); }};

    $(document).on('click', '.js-cross-modrinth-item', function() {{
        var t = $(this).attr('data-title');
        jumpToModrinthSearch(t);
    }});

    $(document).on('click', '.js-cross-curseforge-item', function() {{
        var t = $(this).attr('data-title');
        jumpToCurseforgeSearch(t);
    }});

    /* 核心包名提取与归一化算法 (彻底修复中文通配符吞噬真实包名Bug，并剔除营销前缀与副标题) */
    var BILI_GENRE_BUZZWORDS = /(?:rpg|冒险|高度定制|史诗战斗|魔法|枪械|科技|生存|剧情|硬核|沉浸式|高难|爽游|原版|魔改|养老|纯净|探索|空岛|地牢|格斗|战斗|拔刀剑|工业|建造|现代战争)/ig;

    function cleanPackKey(s) {{
        if (!s) return '';
        s = s.replace(/[\\uD835][\\uDC00-\\uDFFF]/g, '');
        s = s.replace(/(?:我的世界|minecraft|mine\\s*craft|mc)/ig, ' ');
        s = s.replace(/[【】\\[\\]（）\\(\\)\\{{\\}}「」『』《》/|·~～!！?？:：\\-—+*#]+/g, ' ');
        s = s.replace(/(?:mc|minecraft|我的世界)?\\s*1\\.\\d{{1,2}}(?:\\.\\d+)?/ig, ' ');
        s = s.replace(/(?:v|ver|version)?\\s*\\d+(?:\\.\\d+)+(?:[a-z\\d_\\-\\.]*)?/ig, ' ');
        s = s.replace(/(?:v|ver|version)\\s*\\d+/ig, ' ');
        s = s.replace(/\\b(?:forge|fabric|neoforge|quilt)\\b/ig, ' ');
        s = s.replace(/(?:整合包|模组包|魔改包|懒人包|重制版|正式版|抢先版|公测版|抢先体验|测试版)/ig, ' ');
        s = s.replace(/(?:最新|首发|公测|更新|发布|分享|下载|自制|自创|开坑|入坑|通关|介绍|演示|实况|推荐)/ig, ' ');
        s = s.replace(BILI_GENRE_BUZZWORDS, ' ');
        s = s.replace(/(?:新的征途.*|从此刻开始.*|第一期.*|第二期.*|第\\d+期.*|ep\\d+.*)/ig, ' ');
        s = s.replace(/[^\\u4e00-\\u9fa5a-zA-Z0-9]/g, ' ').trim().toLowerCase();
        s = s.replace(/\\s+/g, ' ');
        return s;
    }}

    var BILI_GENERIC_PACK_KEYS = new Set([
        '', 'mc', '我的世界', 'minecraft', '模组', '整合', '游戏', '自制', '包', '整合包',
        '全新', '纯净', '高配', '低配', '生存', '冒险', '科技', '魔法', '空岛', '大型',
        '超好玩', '免费', '客户端', '体验'
    ]);

    /* 智能同包聚合器 (同作者作用域隔离 + 精准核心名聚类，实现同包多版无缝合并) */
    function groupPacks(packs) {{
        var map = {{}};
        var groups = [];
        window.biliGroupsMap = map;

        packs.forEach(function(p) {{
            var rawKey = cleanPackKey(p.title);
            var authorKey = (p.author || 'unknown').trim().toLowerCase();
            var key = '';

            // 规则1：如果提取出的名字为空、长度小于2、或者属于泛用通用词，坚决不跨视频聚合，保持单视频独立！
            if (!rawKey || rawKey.length < 2 || BILI_GENERIC_PACK_KEYS.has(rawKey)) {{
                key = '__raw_' + p.bvid;
            }} else {{
                // 规则2：同作者公共核心名二阶段聚类（如 UP 终极劲爽全家桶 的两期 逆转未来 视频）
                var matchedExistingKey = null;
                for (var k in map) {{
                    if (k.indexOf(authorKey + '::') === 0) {{
                        var existRaw = k.substring(authorKey.length + 2);
                        if (existRaw === rawKey || 
                            (existRaw.length >= 2 && rawKey.indexOf(existRaw) !== -1) || 
                            (rawKey.length >= 2 && existRaw.indexOf(rawKey) !== -1)) {{
                            matchedExistingKey = k;
                            break;
                        }}
                    }}
                }}
                if (matchedExistingKey) {{
                    key = matchedExistingKey;
                }} else {{
                    key = authorKey + '::' + rawKey;
                }}
            }}

            if (!map[key]) {{
                map[key] = {{
                    key: key,
                    displayTitle: p.title,
                    author: p.author,
                    pic: p.pic,
                    latestTimestamp: p.pub_timestamp || 0,
                    latestPubTime: p.pub_time || '',
                    items: [],
                    allVersions: new Set(),
                    allLoaders: new Set(),
                    allCategories: new Set(),
                    allLinks: [],
                    allGroups: new Set(),
                    totalViews: 0,
                    totalLikes: 0,
                    totalCoins: 0,
                    totalFavs: 0,
                    totalShare: 0,
                    totalReply: 0,
                    totalDanmaku: 0
                }};
                groups.push(map[key]);
            }}

            var g = map[key];
            g.items.push(p);

            if ((p.pub_timestamp || 0) > g.latestTimestamp) {{
                g.latestTimestamp = p.pub_timestamp || 0;
                g.latestPubTime = p.pub_time || '';
                g.displayTitle = p.title;
                g.pic = p.pic;
            }}

            if (p.mc_version && p.mc_version !== '未知') g.allVersions.add(p.mc_version);
            if (p.all_versions && Array.isArray(p.all_versions)) {{
                p.all_versions.forEach(function(v) {{ if (v && v !== '未知') g.allVersions.add(v); }});
            }}
            if (p.loaders && Array.isArray(p.loaders)) {{
                p.loaders.forEach(function(l) {{ g.allLoaders.add(l); }});
            }}
            if (p.categories && Array.isArray(p.categories)) {{
                p.categories.forEach(function(c) {{ g.allCategories.add(c); }});
            }}
            if (p.download_links && Array.isArray(p.download_links)) {{
                p.download_links.forEach(function(l) {{ g.allLinks.push(l); }});
            }}
            if (p.qq_group) g.allGroups.add(p.qq_group);

            g.totalViews += (p.views || 0);
            g.totalLikes += (p.likes || 0);
            g.totalCoins += (p.coins || 0);
            g.totalFavs += (p.favorites || 0);
            g.totalShare += (p.share || 0);
            g.totalReply += (p.reply || 0);
            g.totalDanmaku += (p.danmaku || 0);
        }});

        groups.forEach(function(g) {{
            g.items.sort(function(a, b) {{
                return (b.pub_timestamp || 0) - (a.pub_timestamp || 0);
            }});
            var clean = cleanPackKey(g.displayTitle);
            if (clean.length >= 2) {{
                var words = clean.split(' ');
                g.cleanDisplayName = words.slice(0, 3).join(' ').toUpperCase();
            }} else {{
                g.cleanDisplayName = g.displayTitle;
            }}
        }});

        return groups;
    }}

    /* 渲染整个 B站 面板 */
    function renderBiliView() {{
        var q = ($('#biliSearchInput').val() || '').trim().toLowerCase();
        var ver = $('#biliVerSelect').val() || '';
        var loader = $('#biliLoaderSelect').val() || '';
        var sort = $('#biliSortSelect').val() || 'pubdate_desc';

        var nowSec = Math.floor(Date.now() / 1000);
        var refSec = nowSec;
        if (activeDate) {{
            var latestSec = 0;
            biliPacks.forEach(function(item) {{ if ((item.pub_timestamp || 0) > latestSec) latestSec = item.pub_timestamp; }});
            refSec = Math.max(nowSec, latestSec);
        }}

        // 过滤
        var filtered = biliPacks.filter(function(p) {{
            if (q) {{
                var searchTarget = ((p.title || '') + ' ' + (p.author || '') + ' ' + (p.desc || '') + ' ' + (p.mc_version || '') + ' ' + (p.loaders || []).join(' ') + ' ' + (p.categories || []).join(' ')).toLowerCase();
                if (searchTarget.indexOf(q) === -1) return false;
            }}
            if (ver && (p.mc_version || '').indexOf(ver) === -1 && !(p.all_versions || []).includes(ver)) return false;
            if (loader && !(p.loaders || []).includes(loader)) return false;
            if (!catHitMulti(activeCat, p.categories, __catExclude.bilibili)) return false;
            if (activePan) {{
                var links = p.download_links || [];
                var hasPan = links.some(function(l) {{
                    var n = (l && (l.name || l.type || '')) || '';
                    return n.indexOf(activePan) !== -1;
                }});
                if (!hasPan) return false;
            }}
            if (activeDate) {{
                if (activeDate === '7d') {{
                    if (!p.pub_timestamp || (refSec - p.pub_timestamp > 7 * 86400)) return false;
                }} else if (activeDate === '30d') {{
                    if (!p.pub_timestamp || (refSec - p.pub_timestamp > 30 * 86400)) return false;
                }} else if (activeDate === '90d') {{
                    if (!p.pub_timestamp || (refSec - p.pub_timestamp > 90 * 86400)) return false;
                }} else if (/^\\d\\d\\d\\d$/.test(activeDate)) {{
                    if (!p.pub_time || p.pub_time.indexOf(activeDate) !== 0) return false;
                }} else {{
                    if (!p.pub_time || p.pub_time.indexOf(activeDate) !== 0) return false;
                }}
            }}
            return true;
        }});

        // 更新活动过滤项标签条
        updateActiveFiltersBar(q, ver, loader);

        // 排序与渲染
        var $grid = $('#biliCardsGrid');
        $grid.empty();

        if (activeGroupMode === 'grouped') {{
            var groups = groupPacks(filtered);

            groups.sort(function(a, b) {{
                if (sort === 'views_desc') return (b.totalViews || 0) - (a.totalViews || 0);
                if (sort === 'likes_desc') return (b.totalLikes || 0) - (a.totalLikes || 0);
                if (sort === 'favs_desc') return (b.totalFavs || 0) - (a.totalFavs || 0);
                if (sort === 'coins_desc') return (b.totalCoins || 0) - (a.totalCoins || 0);
                if (sort === 'share_desc') return (b.totalShare || 0) - (a.totalShare || 0);
                if (sort === 'reply_desc') return (b.totalReply || 0) - (a.totalReply || 0);
                if (sort === 'danmaku_desc') return (b.totalDanmaku || 0) - (a.totalDanmaku || 0);
                return (b.latestTimestamp || 0) - (a.latestTimestamp || 0);
            }});

            $('#biliCurrentModeText').text('当前模式: ✨ 同名整合包智能聚合 (共 ' + groups.length + ' 款独立整合包)');

            if (groups.length === 0) {{
                $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted); font-size:1.1rem;">🔍 没有找到符合条件的整合包</div>');
                $('#biliPaginationWrap').hide();
                return;
            }}

            var displayGroups = groups.slice(0, currentBiliCardLimit);
            var htmlArr = [];
            displayGroups.forEach(function(g) {{
                htmlArr.push(renderGroupedCard(g));
            }});
            $grid.html(htmlArr.join(''));

            var remaining = groups.length - displayGroups.length;
            if (remaining > 0) {{
                $('#biliPaginationWrap').show();
                $('#biliRemainingCount').text(Math.min(remaining, 48));
                $('#biliTotalFilteredCount').text(groups.length);
            }} else {{
                $('#biliPaginationWrap').hide();
            }}
        }} else {{
            filtered.sort(function(a, b) {{
                if (sort === 'views_desc') return (b.views || 0) - (a.views || 0);
                if (sort === 'likes_desc') return (b.likes || 0) - (a.likes || 0);
                if (sort === 'favs_desc') return (b.favorites || 0) - (a.favorites || 0);
                if (sort === 'coins_desc') return (b.coins || 0) - (a.coins || 0);
                if (sort === 'share_desc') return (b.share || 0) - (a.share || 0);
                if (sort === 'reply_desc') return (b.reply || 0) - (a.reply || 0);
                if (sort === 'danmaku_desc') return (b.danmaku || 0) - (a.danmaku || 0);
                return (b.pub_timestamp || 0) - (a.pub_timestamp || 0);
            }});

            $('#biliCurrentModeText').text('当前模式: 📋 视频单条独立平铺 (共 ' + filtered.length + ' 条发布记录)');

            if (filtered.length === 0) {{
                $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted); font-size:1.1rem;">🔍 没有找到符合条件的视频</div>');
                $('#biliPaginationWrap').hide();
                return;
            }}

            var displayPacks = filtered.slice(0, currentBiliCardLimit);
            var htmlArr = [];
            displayPacks.forEach(function(p) {{
                htmlArr.push(renderFlatCard(p));
            }});
            $grid.html(htmlArr.join(''));

            var remaining = filtered.length - displayPacks.length;
            if (remaining > 0) {{
                $('#biliPaginationWrap').show();
                $('#biliRemainingCount').text(Math.min(remaining, 48));
                $('#biliTotalFilteredCount').text(filtered.length);
            }} else {{
                $('#biliPaginationWrap').hide();
            }}
        }}
    }}

    /* 动态更新活动筛选标签条 */
    function updateActiveFiltersBar(q, ver, loader) {{
        var $bar = $('#biliActiveFilters');
        var $list = $('#biliActiveFiltersList');
        $list.empty();
        var hasFilters = false;

        if (q) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="search">🔍 关键词: ' + q + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (ver) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="ver">🎮 MC: ' + ver + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (loader) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="loader">⚙️ 加载器: ' + loader + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (activeDate) {{
            hasFilters = true;
            var dateText = activeDate;
            if (activeDate === '7d') dateText = '近 7 天';
            else if (activeDate === '30d') dateText = '近 30 天';
            else if (activeDate === '90d') dateText = '近 90 天';
            else if (/^\\d\\d\\d\\d$/.test(activeDate)) dateText = activeDate + ' 年';
            else if (activeDate === '2026-09') dateText = '9月 (当月)';
            else if (activeDate === '2026-08') dateText = '8月 (暑期)';
            $list.append('<span class="active-pill" data-clear="date">📅 时间: ' + dateText + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (activeCat.length) {{
            hasFilters = true;
            activeCat.forEach(function(oneCat) {{
                $list.append('<span class="active-pill" data-clear="cat" data-val="' + escHtml(oneCat, true) + '">🏷️ 分类: ' + escHtml(catLabel(oneCat), true) + '<span class="active-pill-remove">✕</span></span>');
            }});
        }}
        if (activePan) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="pan">💾 网盘: ' + activePan + '<span class="active-pill-remove">✕</span></span>');
        }}

        if (hasFilters) {{
            $bar.show();
        }} else {{
            $bar.hide();
        }}
    }}

    /* 渲染同包聚合卡片 */
    function renderGroupedCard(g) {{
        var latest = g.items[0];
        var isMulti = g.items.length > 1;

        var vers = Array.from(g.allVersions);
        var loaders = Array.from(g.allLoaders);
        var cats = Array.from(g.allCategories);
        var groups = Array.from(g.allGroups);

        var tagsHtml = '';
        vers.forEach(function(v) {{ tagsHtml += '<span class="bili-tag-mc">🎮 ' + v + '</span>'; }});
        loaders.forEach(function(l) {{ tagsHtml += '<span class="bili-tag-loader">' + l + '</span>'; }});
        cats.forEach(function(c) {{ tagsHtml += '<span class="bili-tag-cat">' + c + '</span>'; }});

        var viewsStr = g.totalViews > 10000 ? (g.totalViews / 10000).toFixed(1) + '万' : g.totalViews;
        var likesStr = g.totalLikes > 10000 ? (g.totalLikes / 10000).toFixed(1) + '万' : g.totalLikes;
        var coinsStr = g.totalCoins > 10000 ? (g.totalCoins / 10000).toFixed(1) + '万' : g.totalCoins;
        var favsStr = g.totalFavs > 10000 ? (g.totalFavs / 10000).toFixed(1) + '万' : g.totalFavs;
        var danmakuStr = g.totalDanmaku > 10000 ? (g.totalDanmaku / 10000).toFixed(1) + '万' : g.totalDanmaku;
        var replyStr = g.totalReply > 10000 ? (g.totalReply / 10000).toFixed(1) + '万' : g.totalReply;
        var shareStr = g.totalShare > 10000 ? (g.totalShare / 10000).toFixed(1) + '万' : (g.totalShare || 0);

        var coverImg = g.pic ? (g.pic.replace('http://', 'https://') + '@480w_300h_1c.webp') : '';

        var dlZoneHtml = '<div class="bili-dl-zone">';
        var dlMap = {{}};
        g.allLinks.forEach(function(l) {{
            if (l && l.url && !dlMap[l.url]) {{
                dlMap[l.url] = true;
                var panName = (l.name || l.type || '网盘下载').trim();
                var panClass = 'pan-btn-' + (panName.indexOf('百度') !== -1 ? 'baidu' : (panName.indexOf('夸克') !== -1 ? 'quark' : (panName.indexOf('蓝奏') !== -1 ? 'lanzou' : (panName.indexOf('123') !== -1 ? 'pan123' : 'other'))));
                dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + panClass + '">💾 ' + panName + ' ↗</a>';
            }}
        }});

        if (latest.extract_code) {{
            dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-code js-copy-btn" data-text="' + latest.extract_code + '" title="点击复制提取码">🔑 码: ' + latest.extract_code + '</button>';
        }}

        groups.forEach(function(grp) {{
            dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-group js-copy-btn" data-text="' + grp + '" title="点击复制群号">👥 群: ' + grp + '</button>';
        }});

        var fullDesc = latest.desc || '';
        var pinned = latest.pinned_comment || '';
        if (fullDesc || pinned) {{
            var combined = (fullDesc ? '【简介】\\n' + fullDesc : '') + (pinned ? '\\n\\n【置顶评论】\\n' + pinned : '');
            var safeCombined = $('<div>').text(combined).html();
            dlZoneHtml += '<details class="bili-desc-collapse"><summary class="bili-desc-summary">📄 最新版本介绍与置顶评论</summary><div class="bili-desc-full">' + safeCombined + '</div></details>';
        }}

        if (latest.subtitle_text || latest.subtitle_summary) {{
            var subText = latest.subtitle_text || latest.subtitle_summary;
            var safeSub = $('<div>').text(subText).html();
            dlZoneHtml += '<details class="bili-desc-collapse" style="margin-top:6px;"><summary class="bili-desc-summary" style="color:var(--primary); font-weight:700;">📝 视频字幕与口播速读 (AI/官方)</summary><div class="bili-desc-full" style="max-height:160px; overflow-y:auto; line-height:1.6; font-size:12px;">' + safeSub + '</div></details>';
        }}

        dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other js-open-bili-group-versions" data-group-key="' + g.key + '" style="font-size:0.75rem; background:rgba(251,114,153,0.12); color:#fb7299; border-color:rgba(251,114,153,0.3); margin-top:4px;" title="打开版本详情模态窗">📜 历史发布记录 (' + g.items.length + ') ▾</button>';
        dlZoneHtml += '</div>';

        // 历史版本时间线列表
        var versionsHtml = '';
        if (isMulti) {{
            versionsHtml += '<details class="bili-versions-collapse"><summary class="bili-versions-summary">📜 查看该整合包历史 ' + g.items.length + ' 个迭代版本与关联视频</summary><div class="bili-versions-list">';
            g.items.forEach(function(item, idx) {{
                var itemViews = item.views > 10000 ? (item.views / 10000).toFixed(1) + '万' : item.views;
                var itemDanmaku = (item.danmaku || 0) > 10000 ? ((item.danmaku || 0) / 10000).toFixed(1) + '万' : (item.danmaku || 0);
                var itemCoins = item.coins || 0;
                var isLatestBadge = idx === 0 ? '<span class="bili-ver-latest-badge">最新发布</span>' : '';
                versionsHtml += '<div class="bili-version-item">' +
                    isLatestBadge +
                    '<a href="' + item.url + '" target="_blank" rel="noreferrer" class="bili-ver-title" title="' + item.title + '">' + item.title + '</a>' +
                    '<div class="bili-ver-meta">' +
                        '<span>UP: ' + item.author + '</span> · ' +
                        '<span>' + item.pub_time + '</span> · ' +
                        '<span>👁️ ' + itemViews + '</span> · ' +
                        '<span>📺 ' + itemDanmaku + '</span> · ' +
                        '<span>🪙 ' + itemCoins + '</span>' +
                    '</div>' +
                '</div>';
            }});
            versionsHtml += '</div></details>';
        }}

        return '<div class="bili-pack-card" data-key="' + g.key + '">' +
            '<a href="' + latest.url + '" target="_blank" rel="noreferrer" class="bili-card-cover">' +
                '<img class="bili-card-img" src="' + coverImg + '" alt="' + latest.title + '" loading="lazy" referrerpolicy="no-referrer">' +
                (isMulti ? '<span class="bili-multi-badge">📦 ' + g.items.length + ' 个关联版本</span>' : '') +
                (latest.duration ? '<span class="bili-card-dur">' + latest.duration + '</span>' : '') +
                '<div class="bili-card-stats">' +
                    '<span>👁️ ' + viewsStr + '</span>' +
                    '<span>📺 ' + danmakuStr + '</span>' +
                '</div>' +
            '</a>' +
            '<div class="bili-card-body">' +
                '<a href="' + latest.url + '" target="_blank" rel="noreferrer" class="bili-card-title js-open-unified-preview" data-platform="bilibili" data-full-title="' + $('<div>').text(latest.title).html() + '" data-desc="' + $('<div>').text(fullDesc || pinned || latest.title).html() + '" data-cover="' + coverImg + '" data-author="' + latest.author + '" data-ver="' + vers.join(', ') + '" data-date="' + g.latestPubTime + '" title="' + latest.title + '">' + latest.title + '</a>' +
                '<div class="bili-card-meta">' +
                    '<span>UP: <b class="bili-author-tag">' + latest.author + '</b></span>' +
                    '<span>·</span>' +
                    '<span>最新: ' + g.latestPubTime + '</span>' +
                '</div>' +
                '<div class="bili-metrics-bar">' +
                    '<span class="bmb-item" title="总播放量">👁️ <strong>' + viewsStr + '</strong></span>' +
                    '<span class="bmb-item" title="总弹幕数">📺 <strong>' + danmakuStr + '</strong></span>' +
                    '<span class="bmb-item" title="总点赞数">👍 <strong>' + likesStr + '</strong></span>' +
                    '<span class="bmb-item" title="总投币数">🪙 <strong>' + coinsStr + '</strong></span>' +
                    '<span class="bmb-item" title="总收藏数">⭐ <strong>' + favsStr + '</strong></span>' +
                    '<span class="bmb-item" title="总评论数">💬 <strong>' + replyStr + '</strong></span>' +
                    '<span class="bmb-item" title="总分享数">🔁 <strong>' + shareStr + '</strong></span>' +
                '</div>' +
                (tagsHtml ? '<div class="bili-card-tags">' + tagsHtml + '</div>' : '') +
                dlZoneHtml +
                versionsHtml +
            '</div>' +
        '</div>';
    }}

    /* 渲染单条平铺卡片 */
    function renderFlatCard(p) {{
        var tagsHtml = '';
        if (p.mc_version && p.mc_version !== '未知') tagsHtml += '<span class="bili-tag-mc">🎮 ' + p.mc_version + '</span>';
        if (p.loaders && Array.isArray(p.loaders)) {{
            p.loaders.forEach(function(l) {{ tagsHtml += '<span class="bili-tag-loader">' + l + '</span>'; }});
        }}
        if (p.categories && Array.isArray(p.categories)) {{
            p.categories.forEach(function(c) {{ tagsHtml += '<span class="bili-tag-cat">' + c + '</span>'; }});
        }}

        var viewsStr = p.views > 10000 ? (p.views / 10000).toFixed(1) + '万' : p.views;
        var danmakuStr = (p.danmaku || 0) > 10000 ? ((p.danmaku || 0) / 10000).toFixed(1) + '万' : (p.danmaku || 0);
        var likesStr = p.likes > 10000 ? (p.likes / 10000).toFixed(1) + '万' : p.likes;
        var coinsStr = p.coins > 10000 ? (p.coins / 10000).toFixed(1) + '万' : (p.coins || 0);
        var favsStr = (p.favorites || 0) > 10000 ? ((p.favorites || 0) / 10000).toFixed(1) + '万' : (p.favorites || 0);
        var replyStr = p.reply > 10000 ? (p.reply / 10000).toFixed(1) + '万' : (p.reply || 0);
        var shareStr = (p.share || 0) > 10000 ? ((p.share || 0) / 10000).toFixed(1) + '万' : (p.share || 0);

        var coverImg = p.pic ? (p.pic.replace('http://', 'https://') + '@480w_300h_1c.webp') : '';

        var dlZoneHtml = '<div class="bili-dl-zone">';
        if (p.download_links && p.download_links.length > 0) {{
            p.download_links.forEach(function(l) {{
                if (l && l.url) {{
                    var panName = (l.name || l.type || '网盘下载').trim();
                    var panClass = 'pan-btn-' + (panName.indexOf('百度') !== -1 ? 'baidu' : (panName.indexOf('夸克') !== -1 ? 'quark' : (panName.indexOf('蓝奏') !== -1 ? 'lanzou' : (panName.indexOf('123') !== -1 ? 'pan123' : 'other'))));
                    dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + panClass + '">💾 ' + panName + ' ↗</a>';
                }}
            }});
        }}
        if (p.extract_code) {{
            dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-code js-copy-btn" data-text="' + p.extract_code + '" title="点击复制提取码">🔑 码: ' + p.extract_code + '</button>';
        }}
        if (p.qq_group) {{
            dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-group js-copy-btn" data-text="' + p.qq_group + '" title="点击复制群号">👥 群: ' + p.qq_group + '</button>';
        }}

        var fullDesc = p.desc || '';
        var pinned = p.pinned_comment || '';
        if (fullDesc || pinned) {{
            var combined = (fullDesc ? '【简介】\\n' + fullDesc : '') + (pinned ? '\\n\\n【置顶评论】\\n' + pinned : '');
            var safeCombined = $('<div>').text(combined).html();
            dlZoneHtml += '<details class="bili-desc-collapse"><summary class="bili-desc-summary">📄 详细介绍与置顶评论</summary><div class="bili-desc-full">' + safeCombined + '</div></details>';
        }}

        if (p.subtitle_text || p.subtitle_summary) {{
            var subText = p.subtitle_text || p.subtitle_summary;
            var safeSub = $('<div>').text(subText).html();
            dlZoneHtml += '<details class="bili-desc-collapse" style="margin-top:6px;"><summary class="bili-desc-summary" style="color:var(--primary); font-weight:700;">📝 视频字幕与口播速读 (AI/官方)</summary><div class="bili-desc-full" style="max-height:160px; overflow-y:auto; line-height:1.6; font-size:12px;">' + safeSub + '</div></details>';
        }}

        dlZoneHtml += '</div>';

        return '<div class="bili-pack-card">' +
            '<a href="' + p.url + '" target="_blank" rel="noreferrer" class="bili-card-cover">' +
                '<img class="bili-card-img" src="' + coverImg + '" alt="' + p.title + '" loading="lazy" referrerpolicy="no-referrer">' +
                (p.duration ? '<span class="bili-card-dur">' + p.duration + '</span>' : '') +
                '<div class="bili-card-stats">' +
                    '<span>👁️ ' + viewsStr + '</span>' +
                    '<span>📺 ' + danmakuStr + '</span>' +
                '</div>' +
            '</a>' +
            '<div class="bili-card-body">' +
                '<a href="' + p.url + '" target="_blank" rel="noreferrer" class="bili-card-title" title="' + p.title + '">' + p.title + '</a>' +
                '<div class="bili-card-meta">' +
                    '<span>UP: <b class="bili-author-tag">' + p.author + '</b></span>' +
                    '<span>·</span>' +
                    '<span>' + p.pub_time + '</span>' +
                '</div>' +
                '<div class="bili-metrics-bar">' +
                    '<span class="bmb-item" title="播放量">👁️ <strong>' + viewsStr + '</strong></span>' +
                    '<span class="bmb-item" title="弹幕数">📺 <strong>' + danmakuStr + '</strong></span>' +
                    '<span class="bmb-item" title="点赞数">👍 <strong>' + likesStr + '</strong></span>' +
                    '<span class="bmb-item" title="投币数">🪙 <strong>' + coinsStr + '</strong></span>' +
                    '<span class="bmb-item" title="收藏数">⭐ <strong>' + favsStr + '</strong></span>' +
                    '<span class="bmb-item" title="评论数">💬 <strong>' + replyStr + '</strong></span>' +
                    '<span class="bmb-item" title="分享数">🔁 <strong>' + shareStr + '</strong></span>' +
                '</div>' +
                (tagsHtml ? '<div class="bili-card-tags">' + tagsHtml + '</div>' : '') +
                dlZoneHtml +
            '</div>' +
        '</div>';
    }}

    /* ═══════════ BBSMC 平台视图渲染与筛选逻辑 ═══════════ */
    function renderBbsmcView() {{
        var q = ($('#bbsmcSearchInput').val() || '').trim().toLowerCase();
        var ver = $('#bbsmcVerSelect').val() || '';
        var loader = $('#bbsmcLoaderSelect').val() || '';
        var sort = $('#bbsmcSortSelect').val() || 'downloads_desc';

        var filtered = bbsmcPacks.filter(function(p) {{
            if (q) {{
                var sTarget = ((p.title || '') + ' ' + (p.author || '') + ' ' + (p.description || '') + ' ' + (p.mc_version || '') + ' ' + (p.loaders || []).join(' ') + ' ' + (p.categories || []).join(' ')).toLowerCase();
                if (sTarget.indexOf(q) === -1) return false;
            }}
            if (ver && (p.mc_version || '').indexOf(ver) === -1 && !(p.all_versions || []).includes(ver)) return false;
            if (loader && !(p.loaders || []).includes(loader)) return false;
            if (!catHitMulti(bbsmcActiveCat, p.categories, __catExclude.bbsmc)) return false;
            if (bbsmcActivePan) {{
                var links = p.download_links || [];
                var panKey = bbsmcActivePan.toLowerCase();
                var hasPan = links.some(function(l) {{
                    var n = ((l && l.name) || '').toLowerCase();
                    var u = ((l && l.url) || '').toLowerCase();
                    var fn = ((l && l.filename) || '').toLowerCase();
                    if (panKey === 'modrinth') return n.indexOf('modrinth') !== -1 || fn.indexOf('.mrpack') !== -1 || u.indexOf('cdn.bbsmc.net') !== -1;
                    if (panKey === 'curseforge') return u.indexOf('curseforge.com') !== -1 || n.indexOf('curseforge') !== -1;
                    if (panKey === '夸克') return n.indexOf('夸克') !== -1 || u.indexOf('pan.quark.cn') !== -1;
                    if (panKey === '百度') return n.indexOf('百度') !== -1 || u.indexOf('pan.baidu.com') !== -1;
                    if (panKey === '123') return n.indexOf('123') !== -1 || u.indexOf('123pan') !== -1;
                    if (panKey === '迅雷') return n.indexOf('迅雷') !== -1 || u.indexOf('pan.xunlei.com') !== -1;
                    return n.indexOf(panKey) !== -1 || u.indexOf(panKey) !== -1;
                }});
                if (!hasPan) return false;
            }}
            return true;
        }});

        updateBbsmcActiveFiltersBar(q, ver, loader);

        filtered.sort(function(a, b) {{
            if (sort === 'downloads_desc') return (b.downloads || 0) - (a.downloads || 0);
            if (sort === 'followers_desc') return (b.followers || 0) - (a.followers || 0);
            if (sort === 'modified_desc') return (b.modified_timestamp || 0) - (a.modified_timestamp || 0);
            if (sort === 'created_desc') return (b.created_timestamp || 0) - (a.created_timestamp || 0);
            if (sort === 'title_asc') return (a.title || '').localeCompare(b.title || '');
            return (b.downloads || 0) - (a.downloads || 0);
        }});

        $('#bbsmcMatchInfo').text('共找到 ' + filtered.length.toLocaleString() + ' 款整合包');

        var $grid = $('#bbsmcCardsGrid');
        $grid.empty();

        if (filtered.length === 0) {{
            $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted); font-size:1.1rem;">🔍 没有找到符合条件的 BBSMC 整合包</div>');
            $('#bbsmcPaginationWrap').hide();
            return;
        }}

        var displayPacks = filtered.slice(0, currentBbsmcCardLimit);
        var htmlArr = [];
        displayPacks.forEach(function(p) {{
            htmlArr.push(renderBbsmcCard(p));
        }});
        $grid.html(htmlArr.join(''));

        var remaining = filtered.length - displayPacks.length;
        if (remaining > 0) {{
            $('#bbsmcPaginationWrap').show();
            $('#bbsmcRemainingCount').text(Math.min(remaining, 48));
            $('#bbsmcTotalFilteredCount').text(filtered.length.toLocaleString());
        }} else {{
            $('#bbsmcPaginationWrap').hide();
        }}
    }}

    function updateBbsmcActiveFiltersBar(q, ver, loader) {{
        var $bar = $('#bbsmcActiveFilters');
        var $list = $('#bbsmcActiveFiltersList');
        $list.empty();
        var hasFilters = false;

        if (q) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="search">🔍 关键词: ' + q + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (ver) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="ver">🎮 MC: ' + ver + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (loader) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="loader">⚙️ 加载器: ' + loader + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (bbsmcActiveCat.length) {{
            hasFilters = true;
            bbsmcActiveCat.forEach(function(oneCat) {{
                $list.append('<span class="active-pill" data-clear="cat" data-val="' + escHtml(oneCat, true) + '">🏷️ 分类: ' + escHtml(catLabel(oneCat), true) + '<span class="active-pill-remove">✕</span></span>');
            }});
        }}
        if (bbsmcActivePan) {{
            hasFilters = true;
            var panLabel = bbsmcActivePan;
            if (bbsmcActivePan === 'modrinth') panLabel = '官方直链';
            else if (bbsmcActivePan === 'curseforge') panLabel = 'CurseForge';
            $list.append('<span class="active-pill" data-clear="pan">💾 渠道: ' + panLabel + '<span class="active-pill-remove">✕</span></span>');
        }}

        if (hasFilters) {{
            $bar.show();
        }} else {{
            $bar.hide();
        }}
    }}

    function renderBbsmcCard(p) {{
        registerPackForModal(p);
        var safeTitle = $('<div>').text(p.title || '').html();
        var safeAuthor = $('<div>').text(p.author || '未知').html();
        var safeDesc = $('<div>').text(p.description || '').html();
        var coverImg = p.featured_gallery || (p.gallery && p.gallery[0]) || p.icon_url || window.BBSMC_COVER_FALLBACK;
        var dlStr = p.downloads > 10000 ? (p.downloads / 10000).toFixed(1) + '万' : (p.downloads || 0);
        var flStr = p.followers > 10000 ? (p.followers / 10000).toFixed(1) + '万' : (p.followers || 0);

        var tagsHtml = '';
        if (p.mc_version && p.mc_version !== '未知') {{
            tagsHtml += '<span class="bbsmc-badge-ver">🎮 ' + p.mc_version + '</span>';
        }}
        if (p.loaders && Array.isArray(p.loaders)) {{
            p.loaders.forEach(function(l) {{ tagsHtml += '<span class="bbsmc-badge-loader">' + loaderLabel(l) + '</span>'; }});
        }}
        if (p.categories && Array.isArray(p.categories)) {{
            p.categories.forEach(function(c) {{ tagsHtml += '<span class="bbsmc-badge-cat">' + c + '</span>'; }});
        }}

        var galleryHtml = '';
        if (p.gallery && p.gallery.length > 0) {{
            galleryHtml += '<div class="bbsmc-gallery-strip">';
            var limitG = Math.min(p.gallery.length, 6);
            for (var gi = 0; gi < limitG; gi++) {{
                var gUrl = p.gallery[gi];
                galleryHtml += '<img src="' + gUrl + '" class="bbsmc-gallery-thumb js-bbsmc-lightbox-thumb" data-full="' + gUrl + '" data-title="' + $('<div>').text(p.title || '').html() + ' 实机截图" alt="截图" loading="lazy" referrerpolicy="no-referrer">';
            }}
            galleryHtml += '</div>';
        }}

        var dlZoneHtml = '<div class="bbsmc-download-zone">';
        var links = p.download_links || [];
        var visibleLinks = links.slice(0, 4);
        var hiddenLinks = links.slice(4);

        visibleLinks.forEach(function(l) {{
            if (l && l.url) {{
                var lName = (l.name || '直接下载').trim();
                var u = l.url.toLowerCase();
                var lClass = 'pan-btn-other';
                if (lName.indexOf('modrinth') !== -1 || u.indexOf('.mrpack') !== -1 || u.indexOf('cdn.bbsmc.net') !== -1) {{
                    lClass = 'pan-btn-modrinth';
                }} else if (u.indexOf('curseforge.com') !== -1) {{
                    lClass = 'pan-btn-curseforge';
                }} else if (lName.indexOf('夸克') !== -1 || u.indexOf('pan.quark.cn') !== -1) {{
                    lClass = 'pan-btn-quark';
                }} else if (lName.indexOf('百度') !== -1 || u.indexOf('pan.baidu.com') !== -1) {{
                    lClass = 'pan-btn-baidu';
                }} else if (lName.indexOf('123') !== -1 || u.indexOf('123pan') !== -1) {{
                    lClass = 'pan-btn-pan123';
                }} else if (lName.indexOf('迅雷') !== -1 || u.indexOf('pan.xunlei.com') !== -1) {{
                    lClass = 'pan-btn-xunlei';
                }}
                var vTag = l.version ? ' (' + l.version + ')' : '';
                dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" title="' + lName + vTag + '">💾 ' + lName + ' ↗</a>';
            }}
        }});

        if (hiddenLinks.length > 0) {{
            dlZoneHtml += '<details class="bbsmc-more-links"><summary class="bbsmc-more-summary">展开更多历史下载 (' + hiddenLinks.length + ') ▾</summary><div class="bbsmc-more-body">';
            hiddenLinks.forEach(function(l) {{
                if (l && l.url) {{
                    var lName = (l.name || '直接下载').trim();
                    var vTag = l.version ? ' (' + l.version + ')' : '';
                    dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="font-size:0.75rem;" title="' + lName + vTag + '">💾 ' + lName + ' ↗</a>';
                }}
            }});
            dlZoneHtml += '</div></details>';
        }}

        dlZoneHtml += '<div style="margin-top:6px; display:flex; gap:6px; flex-wrap:wrap;">' +
            '<button type="button" class="bili-pan-btn pan-btn-other js-open-plat-version-modal" data-platform="bbsmc" data-vkey="' + p.url + '" data-title="' + safeTitle + '" data-ver="' + (p.mc_version || '') + '" data-date="' + (p.date_modified || '') + '" data-url="' + p.url + '" data-author="' + safeAuthor + '" data-downloads="' + dlStr + '" style="font-size:0.75rem; background:rgba(0,175,92,0.12); color:#00af5c; border-color:rgba(0,175,92,0.3);">📜 版本详情 ↗</button>' +
            '<a href="' + p.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="background:transparent; border-color:var(--line); color:var(--text-secondary); font-size:0.75rem;">🔗 打开 BBSMC 原页面 ↗</a></div>';
        dlZoneHtml += '</div>';


        return '<div class="bbsmc-pack-card">' +
            '<a href="' + p.url + '" target="_blank" rel="noreferrer" class="bbsmc-card-cover">' +
                '<img class="bbsmc-card-img" src="' + coverImg + '" alt="' + safeTitle + '" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=window.BBSMC_COVER_FALLBACK;">' +
                '<div class="bbsmc-card-stats">' +
                    '<span>📥 ' + dlStr + '</span>' +
                    '<span>⭐ ' + flStr + '</span>' +
                '</div>' +
                (p.mc_version ? '<span class="bbsmc-card-ver-badge">' + p.mc_version + '</span>' : '') +
            '</a>' +
            '<div class="bbsmc-card-body">' +
                '<a href="' + p.url + '" target="_blank" rel="noreferrer" class="bbsmc-card-title js-open-unified-preview" data-platform="bbsmc" data-full-title="' + safeTitle + '" data-desc="' + safeDesc + '" data-cover="' + coverImg + '" data-author="' + safeAuthor + '" data-ver="' + (p.mc_version || '') + '" data-date="' + (p.date_modified || '') + '" title="' + safeTitle + '">' + safeTitle + '</a>' +
                '<div class="bbsmc-card-meta">' +
                    '<span>作者: <b class="bbsmc-author-tag">' + safeAuthor + '</b></span>' +
                    (p.date_modified ? '<span>· 更新: ' + p.date_modified.substring(0, 10) + '</span>' : '') +
                '</div>' +
                (safeDesc ? '<div class="bbsmc-card-desc" title="' + safeDesc + '">' + safeDesc + '</div>' : '') +
                (tagsHtml ? '<div class="bbsmc-card-tags">' + tagsHtml + '</div>' : '') +
                galleryHtml +
                dlZoneHtml +
            '</div>' +
        '</div>';
    }}

    /* ═══════════ XYEBBS 平台视图渲染与筛选逻辑 ═══════════ */
    function renderXyebbsView() {{
        var q = ($('#xyebbsSearchInput').val() || '').trim().toLowerCase();
        var ver = $('#xyebbsVerSelect').val() || '';
        var loader = $('#xyebbsLoaderSelect').val() || '';
        var sort = $('#xyebbsSortSelect').val() || 'hot_desc';

        var filtered = xyebbsPacks.filter(function(p) {{
            if (q) {{
                var sTarget = ((p.title || '') + ' ' + (p.english_name || '') + ' ' + (p.author || '') + ' ' + (p.description || '') + ' ' + (p.mc_version || '') + ' ' + (p.loaders || []).join(' ') + ' ' + (p.categories || []).join(' ')).toLowerCase();
                if (sTarget.indexOf(q) === -1) return false;
            }}
            if (ver && (p.mc_version || '').indexOf(ver) === -1 && !(p.all_versions || []).includes(ver)) return false;
            if (loader && !(p.loaders || []).includes(loader)) return false;
            if (!catHitMulti(xyebbsActiveCat, p.categories, __catExclude.xyebbs)) return false;
            if (xyebbsActivePan) {{
                var links = p.download_links || [];
                var panKey = xyebbsActivePan.toLowerCase();
                if (panKey === 'official') {{
                    if (!p.url) return false;
                }} else {{
                    var hasPan = links.some(function(l) {{
                        var n = ((l && l.name) || '').toLowerCase();
                        var u = ((l && l.url) || '').toLowerCase();
                        var t = ((l && l.type) || '').toLowerCase();
                        if (panKey === '夸克') return n.indexOf('夸克') !== -1 || u.indexOf('pan.quark.cn') !== -1 || t === 'quark';
                        if (panKey === '百度') return n.indexOf('百度') !== -1 || u.indexOf('pan.baidu.com') !== -1 || t === 'baidu';
                        if (panKey === '123') return n.indexOf('123') !== -1 || u.indexOf('123pan') !== -1 || t.indexOf('123') !== -1;
                        if (panKey === '迅雷') return n.indexOf('迅雷') !== -1 || u.indexOf('pan.xunlei.com') !== -1 || t === 'xunlei';
                        if (panKey === '蓝奏') return n.indexOf('蓝奏') !== -1 || u.indexOf('lanzou') !== -1 || t.indexOf('lanzou') !== -1;
                        return n.indexOf(panKey) !== -1 || u.indexOf(panKey) !== -1;
                    }});
                    if (!hasPan) return false;
                }}
            }}
            return true;
        }});

        updateXyebbsActiveFiltersBar(q, ver, loader);

        filtered.sort(function(a, b) {{
            if (sort === 'hot_desc') {{
                var hotA = (a.downloads || 0) + (a.views || 0) * 0.05 + (a.likes || 0) * 10 + (a.comments || 0) * 5;
                var hotB = (b.downloads || 0) + (b.views || 0) * 0.05 + (b.likes || 0) * 10 + (b.comments || 0) * 5;
                return hotB - hotA;
            }}
            if (sort === 'downloads_desc') return (b.downloads || 0) - (a.downloads || 0);
            if (sort === 'views_desc') return (b.views || 0) - (a.views || 0);
            if (sort === 'modified_desc') return (b.modified_timestamp || 0) - (a.modified_timestamp || 0);
            if (sort === 'created_desc') return (b.created_timestamp || 0) - (a.created_timestamp || 0);
            if (sort === 'comments_desc') return (b.comments || 0) - (a.comments || 0);
            if (sort === 'title_asc') return (a.title || '').localeCompare(b.title || '');
            return (b.downloads || 0) - (a.downloads || 0);
        }});

        $('#xyebbsMatchInfo').text('共找到 ' + filtered.length.toLocaleString() + ' 款整合包');

        var $grid = $('#xyebbsCardsGrid');
        $grid.empty();

        if (filtered.length === 0) {{
            $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-secondary);"><div style="font-size:2.5rem; margin-bottom:0.75rem;">🍃</div>没有匹配的 XYEBBS 整合包，请尝试调整搜索词或重置筛选条件</div>');
            $('#xyebbsPaginationWrap').hide();
            return;
        }}

        var displayPacks = filtered.slice(0, currentXyebbsCardLimit);
        var htmlArr = [];
        displayPacks.forEach(function(p) {{
            htmlArr.push(renderXyebbsCard(p));
        }});
        $grid.html(htmlArr.join(''));

        var remaining = filtered.length - displayPacks.length;
        if (remaining > 0) {{
            $('#xyebbsPaginationWrap').show();
            $('#xyebbsRemainingCount').text(Math.min(remaining, 48));
            $('#xyebbsTotalFilteredCount').text(filtered.length.toLocaleString());
        }} else {{
            $('#xyebbsPaginationWrap').hide();
        }}
    }}

    function updateXyebbsActiveFiltersBar(q, ver, loader) {{
        var $bar = $('#xyebbsActiveFilters');
        var $list = $('#xyebbsActiveFiltersList');
        $list.empty();
        var hasFilters = false;

        if (q) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="search">🔍 关键词: ' + q + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (ver) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="ver">🎮 MC: ' + ver + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (loader) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="loader">⚙️ 加载器: ' + loader + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (xyebbsActiveCat.length) {{
            hasFilters = true;
            xyebbsActiveCat.forEach(function(oneCat) {{
                $list.append('<span class="active-pill" data-clear="cat" data-val="' + escHtml(oneCat, true) + '">🏷️ 分类: ' + escHtml(catLabel(oneCat), true) + '<span class="active-pill-remove">✕</span></span>');
            }});
        }}
        if (xyebbsActivePan) {{
            hasFilters = true;
            var panLabel = xyebbsActivePan === 'official' ? '官方发布页' : xyebbsActivePan;
            $list.append('<span class="active-pill" data-clear="pan">💾 渠道: ' + panLabel + '<span class="active-pill-remove">✕</span></span>');
        }}

        if (hasFilters) {{
            $bar.show();
        }} else {{
            $bar.hide();
        }}
    }}

    function renderXyebbsCard(p) {{
        registerPackForModal(p);
        var safeTitle = $('<div>').text(p.title || '').html();
        var safeAuthor = $('<div>').text(p.author || '未知').html();
        var safeDesc = $('<div>').text(p.description || '').html();
        var coverImg = p.head_url || p.icon_url || window.XYEBBS_COVER_FALLBACK || window.BBSMC_COVER_FALLBACK;
        var dlStr = p.downloads > 10000 ? (p.downloads / 10000).toFixed(1) + '万' : (p.downloads || 0);
        var viewStr = p.views > 10000 ? (p.views / 10000).toFixed(1) + '万' : (p.views || 0);

        var tagsHtml = '';
        if (p.mc_version && p.mc_version !== '未知') {{
            tagsHtml += '<span class="xyebbs-badge-ver">🎮 ' + p.mc_version + '</span>';
        }}
        if (p.loaders && Array.isArray(p.loaders)) {{
            p.loaders.forEach(function(l) {{ tagsHtml += '<span class="xyebbs-badge-loader">' + loaderLabel(l) + '</span>'; }});
        }}
        if (p.categories && Array.isArray(p.categories)) {{
            p.categories.forEach(function(c) {{ tagsHtml += '<span class="xyebbs-badge-cat">' + c + '</span>'; }});
        }}

        var dlZoneHtml = '<div class="xyebbs-download-zone">';
        var links = p.download_links || [];
        var visibleLinks = links.slice(0, 4);
        var hiddenLinks = links.slice(4);

        visibleLinks.forEach(function(l) {{
            if (l && l.url) {{
                var lName = (l.name || '直接下载').trim();
                var u = (l.url || '').toLowerCase();
                var t = ((l && l.type) || '').toLowerCase();
                var lClass = 'pan-btn-other';
                if (lName.indexOf('夸克') !== -1 || u.indexOf('pan.quark.cn') !== -1 || t === 'quark') {{
                    lClass = 'pan-btn-quark';
                }} else if (lName.indexOf('百度') !== -1 || u.indexOf('pan.baidu.com') !== -1 || t === 'baidu') {{
                    lClass = 'pan-btn-baidu';
                }} else if (lName.indexOf('123') !== -1 || u.indexOf('123pan') !== -1 || t.indexOf('123') !== -1) {{
                    lClass = 'pan-btn-pan123';
                }} else if (lName.indexOf('迅雷') !== -1 || u.indexOf('pan.xunlei.com') !== -1 || t === 'xunlei') {{
                    lClass = 'pan-btn-xunlei';
                }} else if (lName.indexOf('蓝奏') !== -1 || u.indexOf('lanzou') !== -1 || t.indexOf('lanzou') !== -1) {{
                    lClass = 'pan-btn-lanzou';
                }}
                var vTag = l.label ? ' (' + l.label + ')' : (l.version ? ' (' + l.version + ')' : '');
                dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" title="' + lName + vTag + '">💾 ' + lName + ' ↗</a>';
            }}
        }});

        if (hiddenLinks.length > 0) {{
            dlZoneHtml += '<details class="xyebbs-more-links"><summary class="xyebbs-more-summary">展开更多历史下载 (' + hiddenLinks.length + ') ▾</summary><div class="xyebbs-more-body">';
            hiddenLinks.forEach(function(l) {{
                if (l && l.url) {{
                    var lName = (l.name || '直接下载').trim();
                    var vTag = l.label ? ' (' + l.label + ')' : (l.version ? ' (' + l.version + ')' : '');
                    dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="font-size:0.75rem;" title="' + lName + vTag + '">💾 ' + lName + ' ↗</a>';
                }}
            }});
            dlZoneHtml += '</div></details>';
        }}

        dlZoneHtml += '<div style="margin-top:6px; display:flex; gap:6px; flex-wrap:wrap;">' +
            '<button type="button" class="bili-pan-btn pan-btn-other js-open-plat-version-modal" data-platform="xyebbs" data-vkey="' + p.url + '" data-title="' + safeTitle + '" data-ver="' + (p.mc_version || '') + '" data-date="' + (p.date_modified || '') + '" data-url="' + (p.url || '#') + '" data-author="' + safeAuthor + '" data-downloads="' + dlStr + '" style="font-size:0.75rem; background:rgba(22,163,74,0.12); color:#16a34a; border-color:rgba(22,163,74,0.3);">📜 版本详情 ↗</button>' +
            '<a href="' + (p.url || '#') + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="background:transparent; border-color:var(--line); color:var(--text-secondary); font-size:0.75rem;">🔗 打开 XYEBBS 原页面 ↗</a></div>';
        dlZoneHtml += '</div>';


        return '<div class="xyebbs-pack-card">' +
            '<a href="' + (p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-cover">' +
                '<img class="xyebbs-card-img" src="' + coverImg + '" alt="' + safeTitle + '" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=(window.XYEBBS_COVER_FALLBACK||window.BBSMC_COVER_FALLBACK);">' +
                '<div class="xyebbs-card-stats">' +
                    '<span>📥 ' + dlStr + '</span>' +
                    '<span>👁️ ' + viewStr + '</span>' +
                '</div>' +
                (p.mc_version ? '<span class="xyebbs-card-ver-badge">' + p.mc_version + '</span>' : '') +
            '</a>' +
            '<div class="xyebbs-card-body">' +
                '<a href="' + (p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-title js-open-unified-preview" data-platform="xyebbs" data-full-title="' + safeTitle + '" data-desc="' + safeDesc + '" data-cover="' + coverImg + '" data-author="' + safeAuthor + '" data-ver="' + (p.mc_version || '') + '" data-date="' + (p.date_modified || '') + '" title="' + safeTitle + '">' + safeTitle + '</a>' +
                '<div class="xyebbs-card-meta">' +
                    '<span>作者: <b class="xyebbs-author-tag">' + safeAuthor + '</b></span>' +
                    (p.date_modified ? '<span>· 更新: ' + p.date_modified.substring(0, 10) + '</span>' : '') +
                '</div>' +
                (safeDesc ? '<div class="xyebbs-card-desc" title="' + safeDesc + '">' + safeDesc + '</div>' : '') +
                (tagsHtml ? '<div class="xyebbs-card-tags">' + tagsHtml + '</div>' : '') +
                dlZoneHtml +
            '</div>' +
        '</div>';
    }}

    /* ═══════════ Modrinth 平台视图渲染与筛选 ═══════════ */
    function renderModrinthView() {{
        var q = ($('#modrinthSearchInput').val() || '').trim().toLowerCase();
        var ver = $('#modrinthVerSelect').val() || '';
        var loader = $('#modrinthLoaderSelect').val() || '';
        var sort = $('#modrinthSortSelect').val() || 'downloads_desc';

        var filtered = modrinthPacks.filter(function(p) {{
            if (q) {{
                var sTarget = ((p.title || '') + ' ' + (p.slug || '') + ' ' + (p.author || '') + ' ' + (p.description || '') + ' ' + (p.categories || []).join(' ')).toLowerCase();
                if (sTarget.indexOf(q) === -1) return false;
            }}
            if (ver && (p.mc_version || '').indexOf(ver) === -1 && !(p.all_versions || []).includes(ver)) return false;
            if (loader && !(p.loaders || []).includes(loader)) return false;
            if (!catHitMulti(modrinthActiveCat, p.categories, __catExclude.modrinth)) return false;
            return true;
        }});

        updateModrinthActiveFiltersBar(q, ver, loader);

        filtered.sort(function(a, b) {{
            if (sort === 'downloads_desc') return (b.downloads || 0) - (a.downloads || 0);
            if (sort === 'follows_desc') return (b.followers || 0) - (a.followers || 0);
            if (sort === 'modified_desc') return (b.date_modified || '').localeCompare(a.date_modified || '');
            if (sort === 'title_asc') return (a.title || '').localeCompare(b.title || '');
            return (b.downloads || 0) - (a.downloads || 0);
        }});

        $('#modrinthMatchInfo').text('共找到 ' + filtered.length.toLocaleString() + ' 款整合包');

        var $grid = $('#modrinthCardsGrid');
        $grid.empty();

        if (filtered.length === 0) {{
            $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-secondary);"><div style="font-size:2.5rem; margin-bottom:0.75rem;">🌐</div>没有匹配的 Modrinth 整合包</div>');
            $('#modrinthPaginationWrap').hide();
            return;
        }}

        var displayPacks = filtered.slice(0, currentModrinthCardLimit);
        var htmlArr = [];
        displayPacks.forEach(function(p) {{
            htmlArr.push(renderModrinthCard(p));
        }});
        $grid.html(htmlArr.join(''));

        var remaining = filtered.length - displayPacks.length;
        if (remaining > 0) {{
            $('#modrinthPaginationWrap').show();
            $('#modrinthRemainingCount').text(Math.min(remaining, 48));
            $('#modrinthTotalFilteredCount').text(filtered.length.toLocaleString());
        }} else {{
            $('#modrinthPaginationWrap').hide();
        }}
    }}

    function updateModrinthActiveFiltersBar(q, ver, loader) {{
        var $bar = $('#modrinthActiveFilters');
        var $list = $('#modrinthActiveFiltersList');
        $list.empty();
        var hasFilters = false;

        if (q) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="search">🔍 关键词: ' + q + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (ver) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="ver">🎮 MC: ' + ver + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (loader) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="loader">⚙️ 加载器: ' + loader + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (modrinthActiveCat.length) {{
            hasFilters = true;
            modrinthActiveCat.forEach(function(oneCat) {{
                $list.append('<span class="active-pill" data-clear="cat" data-val="' + escHtml(oneCat, true) + '">🏷️ 分类: ' + escHtml(catLabel(oneCat), true) + '<span class="active-pill-remove">✕</span></span>');
            }});
        }}

        if (hasFilters) {{
            $bar.show();
        }} else {{
            $bar.hide();
        }}
    }}

    function renderModrinthCard(p) {{
        registerPackForModal(p);
        var safeTitle = $('<div>').text(p.title || '').html();
        var safeAuthor = $('<div>').text(p.author || '未知').html();
        var safeDesc = $('<div>').text(p.description || '').html();
        var coverImg = p.icon_url || window.MODRINTH_COVER_FALLBACK;
        var dlStr = p.downloads > 10000 ? (p.downloads / 10000).toFixed(1) + '万' : (p.downloads || 0);
        var flStr = p.followers > 10000 ? (p.followers / 10000).toFixed(1) + '万' : (p.followers || 0);

        var tagsHtml = '';
        if (p.mc_version && p.mc_version !== '未知') {{
            tagsHtml += '<span class="modrinth-badge-ver">🎮 ' + p.mc_version + '</span>';
        }}
        if (p.loaders && Array.isArray(p.loaders)) {{
            p.loaders.forEach(function(l) {{ tagsHtml += '<span class="modrinth-badge-loader">' + loaderLabel(l) + '</span>'; }});
        }}
        if (p.categories && Array.isArray(p.categories)) {{
            p.categories.slice(0, 4).forEach(function(c) {{ tagsHtml += '<span class="modrinth-badge-cat" title="' + c + '">' + catLabel(c) + '</span>'; }});
        }}

        var dlZoneHtml = '<div class="xyebbs-download-zone">';
        var links = p.download_links || [];
        links.forEach(function(l) {{
            if (l && l.url) {{
                var lClass = l.type === 'APP_IMPORT' ? 'pan-btn-modrinth' : 'pan-btn-other';
                var icon = l.type === 'APP_IMPORT' ? '🚀' : '🌐';
                dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" style="font-size:0.8rem;" title="' + l.name + '">' + icon + ' ' + l.label + ' ↗</a>';
            }}
        }});
        dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other js-open-plat-version-modal" data-platform="modrinth" data-vkey="' + p.url + '" data-title="' + safeTitle + '" data-ver="' + (p.mc_version || '') + '" data-date="' + (p.date_modified || '') + '" data-url="' + (p.url || '#') + '" data-author="' + safeAuthor + '" data-downloads="' + dlStr + '" style="font-size:0.8rem; background:rgba(27,217,106,0.12); color:#1bd96a; border-color:rgba(27,217,106,0.3); margin-top:4px;">📜 版本详情 ↗</button>';
        dlZoneHtml += '</div>';


        return '<div class="modrinth-pack-card">' +
            '<a href="' + (p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-cover">' +
                '<img class="xyebbs-card-img" src="' + coverImg + '" alt="' + safeTitle + '" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=window.MODRINTH_COVER_FALLBACK;">' +
                '<div class="xyebbs-card-stats">' +
                    '<span>📥 ' + dlStr + '</span>' +
                    '<span>⭐ ' + flStr + '</span>' +
                '</div>' +
                (p.mc_version ? '<span class="xyebbs-card-ver-badge" style="background:rgba(27,217,106,0.9);">' + p.mc_version + '</span>' : '') +
            '</a>' +
            '<div class="xyebbs-card-body">' +
                '<a href="' + (p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-title js-open-unified-preview" data-platform="modrinth" data-full-title="' + safeTitle + '" data-desc="' + safeDesc + '" data-cover="' + coverImg + '" data-author="' + safeAuthor + '" data-ver="' + (p.mc_version || '') + '" data-date="' + (p.date_modified || '') + '" title="' + safeTitle + '">' + safeTitle + '</a>' +
                '<div class="xyebbs-card-meta">' +
                    '<span>作者: <b style="color:#1bd96a;">' + safeAuthor + '</b></span>' +
                    (p.date_modified ? '<span>· 更新: ' + p.date_modified.substring(0, 10) + '</span>' : '') +
                '</div>' +
                (safeDesc ? '<div class="xyebbs-card-desc" title="' + safeDesc + '">' + safeDesc + '</div>' : '') +
                (tagsHtml ? '<div class="xyebbs-card-tags">' + tagsHtml + '</div>' : '') +
                dlZoneHtml +
            '</div>' +
        '</div>';
    }}

    /* ═══════════ CurseForge 平台视图渲染与筛选 ═══════════ */
    function renderCurseforgeView() {{
        var q = ($('#curseforgeSearchInput').val() || '').trim().toLowerCase();
        var ver = $('#curseforgeVerSelect').val() || '';
        var loader = $('#curseforgeLoaderSelect').val() || '';
        var sort = $('#curseforgeSortSelect').val() || 'downloads_desc';

        var filtered = curseforgePacks.filter(function(p) {{
            if (q) {{
                var sTarget = ((p.title || '') + ' ' + (p.slug || '') + ' ' + (p.author || '') + ' ' + (p.description || '') + ' ' + (p.categories || []).join(' ')).toLowerCase();
                if (sTarget.indexOf(q) === -1) return false;
            }}
            if (ver && (p.mc_version || '').indexOf(ver) === -1 && !(p.all_versions || []).includes(ver)) return false;
            if (loader && !(p.loaders || []).includes(loader)) return false;
            if (!catHitMulti(curseforgeActiveCat, p.categories, __catExclude.curseforge)) return false;
            return true;
        }});

        updateCurseforgeActiveFiltersBar(q, ver, loader);

        filtered.sort(function(a, b) {{
            if (sort === 'downloads_desc') return (b.downloads || 0) - (a.downloads || 0);
            if (sort === 'followers_desc') return (b.followers || 0) - (a.followers || 0);
            if (sort === 'modified_desc') return (b.date_modified || '').localeCompare(a.date_modified || '');
            if (sort === 'title_asc') return (a.title || '').localeCompare(b.title || '');
            return (b.downloads || 0) - (a.downloads || 0);
        }});

        $('#curseforgeMatchInfo').text('共找到 ' + filtered.length.toLocaleString() + ' 款整合包');

        var $grid = $('#curseforgeCardsGrid');
        $grid.empty();

        if (filtered.length === 0) {{
            $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-secondary);"><div style="font-size:2.5rem; margin-bottom:0.75rem;">🔥</div>没有匹配的 CurseForge 整合包</div>');
            $('#curseforgePaginationWrap').hide();
            return;
        }}

        var displayPacks = filtered.slice(0, currentCurseforgeCardLimit);
        var htmlArr = [];
        displayPacks.forEach(function(p) {{
            htmlArr.push(renderCurseforgeCard(p));
        }});
        $grid.html(htmlArr.join(''));

        var remaining = filtered.length - displayPacks.length;
        if (remaining > 0) {{
            $('#curseforgePaginationWrap').show();
            $('#curseforgeRemainingCount').text(Math.min(remaining, 48));
            $('#curseforgeTotalFilteredCount').text(filtered.length.toLocaleString());
        }} else {{
            $('#curseforgePaginationWrap').hide();
        }}
    }}

    function updateCurseforgeActiveFiltersBar(q, ver, loader) {{
        var $bar = $('#curseforgeActiveFilters');
        var $list = $('#curseforgeActiveFiltersList');
        $list.empty();
        var hasFilters = false;

        if (q) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="search">🔍 关键词: ' + q + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (ver) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="ver">🎮 MC: ' + ver + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (loader) {{
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="loader">⚙️ 加载器: ' + loader + '<span class="active-pill-remove">✕</span></span>');
        }}
        if (curseforgeActiveCat.length) {{
            hasFilters = true;
            curseforgeActiveCat.forEach(function(oneCat) {{
                $list.append('<span class="active-pill" data-clear="cat" data-val="' + escHtml(oneCat, true) + '">🏷️ 分类: ' + escHtml(catLabel(oneCat), true) + '<span class="active-pill-remove">✕</span></span>');
            }});
        }}

        if (hasFilters) {{
            $bar.show();
        }} else {{
            $bar.hide();
        }}
    }}

    function renderCurseforgeCard(p) {{
        registerPackForModal(p);
        var safeTitle = $('<div>').text(p.title || '').html();
        var safeAuthor = $('<div>').text(p.author || '未知').html();
        var safeDesc = $('<div>').text(p.description || '').html();
        var coverImg = p.icon_url || window.CURSEFORGE_COVER_FALLBACK;
        var dlStr = p.downloads > 10000 ? (p.downloads / 10000).toFixed(1) + '万' : (p.downloads || 0);
        var flStr = p.followers > 10000 ? (p.followers / 10000).toFixed(1) + '万' : (p.followers || 0);

        var tagsHtml = '';
        if (p.mc_version && p.mc_version !== '未知') {{
            tagsHtml += '<span class="curseforge-badge-ver">🎮 ' + p.mc_version + '</span>';
        }}
        if (p.loaders && Array.isArray(p.loaders)) {{
            p.loaders.forEach(function(l) {{ tagsHtml += '<span class="curseforge-badge-loader">' + loaderLabel(l) + '</span>'; }});
        }}
        if (p.categories && Array.isArray(p.categories)) {{
            p.categories.slice(0, 4).forEach(function(c) {{ tagsHtml += '<span class="curseforge-badge-cat" title="' + c + '">' + catLabel(c) + '</span>'; }});
        }}

        var dlZoneHtml = '<div class="xyebbs-download-zone">';
        var links = p.download_links || [];
        links.forEach(function(l) {{
            if (l && l.url) {{
                var lClass = l.type === 'APP_IMPORT' ? 'pan-btn-curseforge' : 'pan-btn-other';
                var icon = l.type === 'APP_IMPORT' ? '🔥' : '🔗';
                dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" style="font-size:0.8rem;" title="' + l.name + '">' + icon + ' ' + l.label + ' ↗</a>';
            }}
        }});
        dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other js-open-plat-version-modal" data-platform="curseforge" data-vkey="' + p.url + '" data-title="' + safeTitle + '" data-ver="' + (p.mc_version || '') + '" data-date="' + (p.date_modified || '') + '" data-url="' + (p.url || '#') + '" data-author="' + safeAuthor + '" data-downloads="' + dlStr + '" style="font-size:0.8rem; background:rgba(241,100,54,0.12); color:#f16436; border-color:rgba(241,100,54,0.3); margin-top:4px;">📜 版本详情 ↗</button>';
        dlZoneHtml += '</div>';


        return '<div class="curseforge-pack-card">' +
            '<a href="' + (p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-cover">' +
                '<img class="xyebbs-card-img" src="' + coverImg + '" alt="' + safeTitle + '" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=window.CURSEFORGE_COVER_FALLBACK;">' +
                '<div class="xyebbs-card-stats">' +
                    '<span>📥 ' + dlStr + '</span>' +
                    '<span>👍 ' + flStr + '</span>' +
                '</div>' +
                (p.mc_version ? '<span class="xyebbs-card-ver-badge" style="background:rgba(241,100,54,0.9);">' + p.mc_version + '</span>' : '') +
            '</a>' +
            '<div class="xyebbs-card-body">' +
                '<a href="' + (p.url || '#') + '" target="_blank" rel="noreferrer" class="xyebbs-card-title js-open-unified-preview" data-platform="curseforge" data-full-title="' + safeTitle + '" data-desc="' + safeDesc + '" data-cover="' + coverImg + '" data-author="' + safeAuthor + '" data-ver="' + (p.mc_version || '') + '" data-date="' + (p.date_modified || '') + '" title="' + safeTitle + '">' + safeTitle + '</a>' +
                '<div class="xyebbs-card-meta">' +
                    '<span>作者: <b style="color:#f16436;">' + safeAuthor + '</b></span>' +
                    (p.date_modified ? '<span>· 更新: ' + p.date_modified.substring(0, 10) + '</span>' : '') +
                '</div>' +
                (safeDesc ? '<div class="xyebbs-card-desc" title="' + safeDesc + '">' + safeDesc + '</div>' : '') +
                (tagsHtml ? '<div class="xyebbs-card-tags">' + tagsHtml + '</div>' : '') +
                dlZoneHtml +
            '</div>' +
        '</div>';
    }}


    // 展开/收起 核心标签
    $('#expandTags').on('click', function() {{
        tagListExpanded = !tagListExpanded;
        $(this).text(tagListExpanded ? '收起 ↑' : '展开全部 ↓');
        $(this).attr('aria-expanded', String(tagListExpanded));
        renderTagChips();
    }});

    // 展开/收起 热门模组
    $('#expandMods').on('click', function() {{
        modListExpanded = !modListExpanded;
        $(this).text(modListExpanded ? '收起常用 ▴' : '常用模组(前60) ▾');
        $(this).attr('aria-expanded', String(modListExpanded));
        renderHotModChips();
    }});

    // 全部标签 / 多选弹窗
    $('#allTags').on('click', function() {{
        openPicker('tag', allTagsList, tagCountsMap, '全部玩法标签', 'TAG DISCOVERY', '同时满足所选标签 · 按收录整合包数量排序');
    }});

    // 全部模组 / 搜索多选弹窗
    $('#allMods').on('click', function() {{
        openPicker('mod', allModsList, modCountsMap, '全部收录模组（11,702 款）', 'MOD DISCOVERY', '筛选包含指定模组的整合包 · 按收录整合包数量排序');
    }});

    // 关闭弹窗
    $('#closePickerModal').on('click', function() {{
        var modalEl = $('#mcmodPickerModal')[0];
        if (modalEl && modalEl.close) modalEl.close();
        else $('#mcmodPickerModal').hide();
        syncAllFilterUI();
    }});

    $('#mcmodPickerModal').on('click', function(e) {{
        if (e.target === this) {{
            var r = this.getBoundingClientRect();
            if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) {{
                if (this.close) this.close();
                else $(this).hide();
                syncAllFilterUI();
            }}
        }}
    }});

    // 已激活筛选胶囊点击移除
    $('#activeFilters').on('click', '.active-filter-badge', function() {{
        var field = $(this).data('field');
        var val = $(this).data('val');
        if (field === 'cat') toggleMultiSelect('#categoryFilter', val);
        else if (field === 'tag') toggleMultiSelect('#packTagFilter', val);
        else if (field === 'modcat') toggleMultiSelect('#modCategoryFilter', val);
        else if (field === 'mod') toggleMultiSelect('#modFilter', val);
        else if (field === 'type') {{ $('#typeFilter').val('').trigger('change'); }}
        else if (field === 'trend') {{ $('#trendFilter').val('').trigger('change'); }}
        syncAllFilterUI();
    }});

    $('#activeFilters').on('click', '#clearAllActiveFilters', function() {{
        $('#sidebarResetFilters').click();
    }});

    // 1. 官方专区 Chips 点击
    $('#mcmodCategoryChips').on('click', '.s-chip', function() {{
        var cat = $(this).data('cat');
        if (!cat) {{
            $('#categoryFilter').val(null).trigger('change');
        }} else {{
            toggleMultiSelect('#categoryFilter', cat);
        }}
        syncAllFilterUI();
    }});

    // 2. 核心标签 Chips 点击
    $('#mcmodTagChips').on('click', '.s-chip', function() {{
        var tag = $(this).data('tag');
        if (!tag) {{
            $('#packTagFilter').val(null).trigger('change');
        }} else {{
            toggleMultiSelect('#packTagFilter', tag);
        }}
        syncAllFilterUI();
    }});

    // 3. 模组分类 Chips 点击
    $('#mcmodModCatChips').on('click', '.s-chip', function() {{
        var mcat = $(this).data('mod-cat');
        if (!mcat) {{
            $('#modCategoryFilter').val(null).trigger('change');
        }} else {{
            toggleMultiSelect('#modCategoryFilter', mcat);
        }}
        syncAllFilterUI();
    }});

    // 4. 包含模组 Chips 点击
    $('#mcmodHotModChips').on('click', '.s-chip', function() {{
        var mod = $(this).data('mod');
        if (!mod) {{
            $('#modFilter').val(null).trigger('change');
        }} else {{
            toggleMultiSelect('#modFilter', mod);
        }}
        syncAllFilterUI();
    }});

    // B站 玩法分类 Chips 点击单选与联动
    // 多选（向 MCMod 看齐）：点「全部」清空；点分类在选中集合里切换；已选中的再点取消
    $('#biliCategoryChips').on('click', '.s-chip', function() {{
        var cat = $(this).data('cat') || '';
        if (!cat) {{
            activeCat = [];
        }} else {{
            var at = activeCat.indexOf(cat);
            if (at === -1) {{ activeCat.push(cat); }} else {{ activeCat.splice(at, 1); }}
        }}
        $('#biliCategoryChips .s-chip').each(function() {{
            var cv = $(this).data('cat') || '';
            $(this).toggleClass('active', cv ? activeCat.indexOf(cv) !== -1 : activeCat.length === 0);
        }});
        renderBiliView();
    }});

    // 侧边栏 B站 网盘类型 Chips 点击联动
    $('#biliPanChips').on('click', '.s-chip', function() {{
        $('#biliPanChips .s-chip').removeClass('active');
        $(this).addClass('active');
        activePan = $(this).data('pan') || '';
        renderBiliView();
    }});

    // 侧边栏 全平台分类 Chips 点击联合搜索
    $('#allCategoryChips').on('click', '.s-chip', function() {{
        var cat = $(this).data('cat');
        $('#crossSearchInput').val(cat).trigger('input');
        if ($('.cross-search-section').length) {{
            $('html, body').animate({{ scrollTop: $('.cross-search-section').offset().top - 80 }}, 300);
        }}
    }});

    // 侧边栏 MC百科 一键重置全部筛选
    $('#sidebarResetFilters').on('click', function() {{
        $('#categoryFilter').val(null).trigger('change');
        $('#packTagFilter').val(null).trigger('change');
        $('#modCategoryFilter').val(null).trigger('change');
        $('#modFilter').val(null).trigger('change');
        $('#typeFilter').val('').trigger('change');
        $('#trendFilter').val('').trigger('change');
        $('#categoryExclude').prop('checked', false);
        $('#mcmodUnifiedSearch').val('');
        $('#mcmodSearchClear').hide();
        currentMcmodCardLimit = 48;
        if (window.table) {{
            window.table.search('').draw();
        }}
        syncAllFilterUI();
        renderMcmodCards();
    }});

    // 侧边栏 B站 一键重置全部筛选
    $('#sidebarBiliReset').on('click', function() {{
        activeCat = [];
        activePan = '';
        activeDate = '';
        $('#biliSortSelect').val('pubdate_desc').trigger('change');
        $('#biliVerSelect').val('').trigger('change');
        $('#biliLoaderSelect').val('').trigger('change');
        $('#biliSearchInput').val('');
        $('#biliSearchClear').hide();
        $('#biliCategoryChips .s-chip').removeClass('active');
        $('#biliPanChips .s-chip').removeClass('active');
        $('#biliPanChips .s-chip[data-pan=""]').addClass('active');
        $('#biliDateChips .s-chip').removeClass('active');
        $('#biliDateChips .s-chip[data-date=""]').addClass('active');
        renderBiliView();
    }});

    // 顶栏与侧边栏平台导航双向联动
    $(document).on('click', '.nav-item, .top-plat-btn', function() {{
        var tab = $(this).data('tab');
        if (tab) switchPlatformTab(tab);
    }});
    // MC百科卡片画廊分页加载更多与全部展开
    $(document).on('click', '.js-load-more-cards', function() {{
        currentMcmodCardLimit += 48;
        renderMcmodCards();
    }});
    $(document).on('click', '.js-load-all-cards', function() {{
        currentMcmodCardLimit = 99999;
        renderMcmodCards();
    }});

    // MC百科专属一体化搜索栏 (实时联动画廊卡片与专业数据表)
    var mcmodSearchTimer = null;
    $('#mcmodUnifiedSearch').on('input', function() {{
        var val = $(this).val();
        if (val) {{
            $('#mcmodSearchClear').show();
        }} else {{
            $('#mcmodSearchClear').hide();
        }}
        clearTimeout(mcmodSearchTimer);
        mcmodSearchTimer = setTimeout(function() {{
            currentMcmodCardLimit = 48;
            if (window.table) {{
                window.table.search(val).draw();
            }}
            renderMcmodCards();
        }}, 150);
    }});

    $('#mcmodSearchClear').on('click', function() {{
        $('#mcmodUnifiedSearch').val('').trigger('input');
    }});

    // MCMod 视图切换 (卡片 vs 表格)
    $('#mcmodViewToggle').on('click', '.vmode-btn', function() {{
        $('#mcmodViewToggle .vmode-btn').removeClass('active');
        $(this).addClass('active');
        activeMcmodVMode = $(this).data('vmode');
        $('#crumbCurrentView').text(activeMcmodVMode === 'cards' ? '画廊卡片' : '专业多维表格');

        if (activeMcmodVMode === 'cards') {{
            $('.table-card').hide();
            $('#mcmodCardsContainer').show();
            renderMcmodCards();
        }} else {{
            $('#mcmodCardsContainer').hide();
            $('.table-card').show();
            if (window.table) {{
                window.table.columns.adjust();
            }}
        }}
    }});

    // B站 聚合模式切换 (同包聚合 vs 视频平铺)
    $('#biliViewToggle, .bili-mode-toggle').on('click', '.vmode-btn, .bili-mode-btn', function() {{
        var mode = $(this).data('bmode') || $(this).data('mode');
        if (!mode) return;
        $('#biliViewToggle .vmode-btn').removeClass('active');
        $('#biliViewToggle .vmode-btn[data-bmode="' + mode + '"]').addClass('active');
        $('.bili-mode-btn').removeClass('active');
        $('.bili-mode-btn[data-mode="' + mode + '"]').addClass('active');

        activeGroupMode = mode;
        $('#crumbCurrentView').text(activeGroupMode === 'grouped' ? '同包聚合' : '单条平铺');
        renderBiliView();
    }});

    // B站 搜索与过滤事件 (含清除按钮与防抖)
    var biliSearchTimer = null;
    $('#biliSearchInput').on('input', function() {{
        var val = $(this).val();
        if (val) {{
            $('#biliSearchClear').show();
        }} else {{
            $('#biliSearchClear').hide();
        }}
        clearTimeout(biliSearchTimer);
        biliSearchTimer = setTimeout(function() {{
            renderBiliView();
        }}, 150);
    }});

    $('#biliSearchClear').on('click', function() {{
        $('#biliSearchInput').val('').trigger('input');
    }});

    $('#biliVerSelect, #biliLoaderSelect, #biliSortSelect').on('change', function() {{
        currentBiliCardLimit = 48;
        renderBiliView();
    }});

    // B站 加载更多与展开全部
    $(document).on('click', '.js-bili-load-more', function() {{
        currentBiliCardLimit += 48;
        renderBiliView();
    }});

    $(document).on('click', '.js-bili-load-all', function() {{
        currentBiliCardLimit = 99999;
        renderBiliView();
    }});

    // 快捷键 Ctrl+K 聚焦搜索
    $(document).on('keydown', function(e) {{
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {{
            e.preventDefault();
            if (currentTab === 'bilibili') {{
                $('#biliSearchInput').focus();
            }} else {{
                $('#mcmodUnifiedSearch').focus();
            }}
        }}
    }});

    // B站 日期 Chips 点击联动
    $('#biliDateChips').on('click', '.s-chip, .bili-chip', function() {{
        $('#biliDateChips .s-chip, #biliDateChips .bili-chip').removeClass('active');
        $(this).addClass('active');
        activeDate = $(this).data('date') || '';
        renderBiliView();
    }});

    // 活动标签清除事件
    $('#biliActiveFilters').on('click', '.active-pill', function() {{
        var clearType = $(this).data('clear');
        if (clearType === 'search') {{
            $('#biliSearchInput').val('').trigger('input');
        }} else if (clearType === 'date') {{
            $('#biliDateChips .s-chip[data-date=""]').click();
        }} else if (clearType === 'cat') {{
            var val = $(this).data('val');
            if (val) {{
                var at = activeCat.indexOf(val);
                if (at !== -1) activeCat.splice(at, 1);
            }} else {{
                activeCat = [];
            }}
            $('#biliCategoryChips .s-chip').each(function() {{
                var cv = $(this).data('cat') || '';
                $(this).toggleClass('active', cv ? activeCat.indexOf(cv) !== -1 : activeCat.length === 0);
            }});
            renderBiliView();
        }} else if (clearType === 'pan') {{
            $('#biliPanChips .s-chip[data-pan=""]').click();
        }} else if (clearType === 'ver') {{
            $('#biliVerSelect').val('').trigger('change');
        }} else if (clearType === 'loader') {{
            $('#biliLoaderSelect').val('').trigger('change');
        }}
    }});

    $('#biliClearFiltersBtn').on('click', function() {{
        $('#sidebarBiliReset').click();
    }});

    // 复制事件绑定
    $(document).on('click', '.js-copy-btn', function(e) {{
        e.preventDefault();
        var text = $(this).data('text');
        if (navigator.clipboard) {{
            navigator.clipboard.writeText(text).then(function() {{
                showToast('✅ 已复制: ' + text);
            }});
        }} else {{
            var input = document.createElement('input');
            input.value = text;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
            showToast('✅ 已复制: ' + text);
        }}
    }});

    // 移动端菜单开关
    $('#mobileMenuBtn').on('click', function() {{
        $('#mainSidebar').toggleClass('open');
    }});

    // 主题切换 (侧边栏 + 顶栏双向同步)
    $(document).on('click', '.theme-dot, .top-tdot', function() {{
        var theme = $(this).data('theme');
        $('.theme-dot, .top-tdot').removeClass('active');
        $('.theme-dot[data-theme="' + theme + '"], .top-tdot[data-theme="' + theme + '"]').addClass('active');
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('mcmod-theme-v2', theme);
    }});

    // 恢复保存的主题
    var savedTheme = localStorage.getItem('mcmod-theme-v2') || 'eye';
    $('.theme-dot[data-theme="' + savedTheme + '"], .top-tdot[data-theme="' + savedTheme + '"]').addClass('active');
    document.documentElement.setAttribute('data-theme', savedTheme);

    function showToast(msg) {{
        var $t = $('#copyToast');
        $t.text(msg).addClass('show');
        setTimeout(function() {{ $t.removeClass('show'); }}, 1800);
    }}

    function initBiliStats() {{
        if (!biliPacks.length) return;
        var mcCount = (window.tableRowsData ? window.tableRowsData.length : 1484);
        var groupedAll = groupPacks(biliPacks);
        $('#topNavBiliBadge').text(groupedAll.length.toLocaleString());
        $('#sidebarAllBadge').text((mcCount + groupedAll.length).toLocaleString() + ' 款');
        $('#sidebarMcmodBadge').text(mcCount.toLocaleString() + ' 款');
        $('#sidebarBiliBadge').text(groupedAll.length + ' 款 (' + biliPacks.length + '视频)');
        $('#heroBiliPacks').text(groupedAll.length);
        $('#heroBiliTotal').text(biliPacks.length);
        $('#biliStatTotal').text(groupedAll.length + ' 款 (' + biliPacks.length + '视频)');
        
        var totalViews = 0;
        var totalLinks = 0;
        var totalGroups = 0;
        var verSet = {{}};

        biliPacks.forEach(function(p) {{
            totalViews += (p.views || 0);
            totalLinks += (p.download_links ? p.download_links.length : 0);
            if (p.qq_group) totalGroups++;
            if (p.mc_version && p.mc_version !== '未知') {{
                verSet[p.mc_version] = (verSet[p.mc_version] || 0) + 1;
            }}
            if (p.all_versions && Array.isArray(p.all_versions)) {{
                p.all_versions.forEach(function(v) {{
                    if (v && v !== '未知') verSet[v] = (verSet[v] || 0) + 1;
                }});
            }}
        }});

        var viewsText = totalViews > 100000000 ? (totalViews / 100000000).toFixed(2) + '亿' :
                       (totalViews > 10000 ? (totalViews / 10000).toFixed(1) + '万' : totalViews);
        $('#biliStatViews').text(viewsText);
        $('#heroBiliViews').text(viewsText);
        $('#biliStatLinks').text(totalLinks + ' 个');
        $('#heroBiliLinks').text(totalLinks);
        $('#biliStatGroups').text(totalGroups + ' 个');
        $('#heroBiliGroups').text(totalGroups);

        // 填充版本下拉选项
        var sortedVers = Object.keys(verSet).sort(function(a, b) {{
            return verSet[b] - verSet[a];
        }});
        var $verSel = $('#biliVerSelect');
        sortedVers.forEach(function(v) {{
            $verSel.append('<option value="' + v + '">' + v + ' (' + verSet[v] + ')</option>');
        }});
        $verSel.trigger('change.select2');

        // 动态自适应填充发布时间 Chips（支持全量历史年限与近7/30/90天）
        initBiliDateChips();
    }}

    function initBiliDateChips() {{
        var $row = $('#biliDateChips');
        if (!$row.length) return;
        $row.empty();
        $row.append('<span class="s-chip active" data-date="">全部时间</span>');
        $row.append('<span class="s-chip" data-date="7d">近 7 天</span>');
        $row.append('<span class="s-chip" data-date="30d">近 30 天</span>');
        $row.append('<span class="s-chip" data-date="90d">近 90 天</span>');

        // 动态搜集并降序排列所有出现的年份
        var years = new Set();
        biliPacks.forEach(function(p) {{
            if (p.pub_time && p.pub_time.length >= 4) {{
                var y = p.pub_time.substring(0, 4);
                if (/^\\d\\d\\d\\d$/.test(y)) {{
                    years.add(y);
                }}
            }}
        }});
        var sortedYears = Array.from(years).sort().reverse();
        sortedYears.forEach(function(yr) {{
            $row.append('<span class="s-chip" data-date="' + yr + '">' + yr + ' 年</span>');
        }});
    }}

    initBiliStats();

    /* ════════ BBSMC 平台统计与交互事件 ════════ */
    function initBbsmcStats() {{
        if (!bbsmcPacks.length) return;
        var totalDl = 0;
        var totalFl = 0;
        var totalLinks = 0;
        var verSet = {{}};
        var catSet = {{}};

        bbsmcPacks.forEach(function(p) {{
            totalDl += (p.downloads || 0);
            totalFl += (p.followers || 0);
            totalLinks += (p.download_links ? p.download_links.length : 0);
            if (p.mc_version && p.mc_version !== '未知') {{
                verSet[p.mc_version] = (verSet[p.mc_version] || 0) + 1;
            }}
            (p.categories || []).forEach(function(c) {{
                if (c) catSet[c] = (catSet[c] || 0) + 1;
            }});
        }});

        var dlText = totalDl > 100000000 ? (totalDl / 100000000).toFixed(2) + '亿' :
                     (totalDl > 10000 ? (totalDl / 10000).toFixed(1) + '万' : totalDl);
        var flText = totalFl > 10000 ? (totalFl / 10000).toFixed(1) + '万' : totalFl;

        $('#bbsmcStatDownloads').text(dlText);
        $('#bbsmcStatFollowers').text(flText);
        $('#bbsmcStatLinks').text(totalLinks.toLocaleString() + ' 个');
        $('#bbsmcStatTotal').text((bbsmcPacks.length || 1802).toLocaleString() + ' 款');

        $('#topNavBbsmcBadge').text(bbsmcPacks.length.toLocaleString());

        // 填充 BBSMC 版本下拉选项
        var sortedVers = Object.keys(verSet).sort(function(a, b) {{ return verSet[b] - verSet[a]; }});
        var $verSel = $('#bbsmcVerSelect');
        sortedVers.forEach(function(v) {{
            $verSel.append('<option value="' + v + '">' + v + ' (' + verSet[v] + ')</option>');
        }});
        $verSel.trigger('change.select2');

        // 填充 BBSMC 玩法专区 Chips
        var sortedCats = Object.keys(catSet).sort(function(a, b) {{ return catSet[b] - catSet[a]; }});
        window.__bbsmcAllCats = sortedCats;
        window.__bbsmcCatCounts = catSet;
        window.__bbsmcCatsExpanded = false;
        renderBbsmcCatChips();
    }}

    function renderBbsmcCatChips() {{
        var $catChips = $('#bbsmcCategoryChips');
        $catChips.empty();
        $catChips.append('<span class="s-chip' + (bbsmcActiveCat.length === 0 ? ' active' : '') + '" data-cat="">全部玩法</span>');
        var maxVisible = window.__bbsmcCatsExpanded ? window.__bbsmcAllCats.length : 12;
        window.__bbsmcAllCats.forEach(function(c, idx) {{
            var isSelected = bbsmcActiveCat.indexOf(c) !== -1;
            var isVisible = idx < maxVisible || isSelected;
            var count = window.__bbsmcCatCounts[c] || 0;
            $catChips.append('<span class="s-chip' + (isSelected ? ' active' : '') + '" data-cat="' + c + '" title="' + c + '" style="' + (isVisible ? '' : 'display:none;') + '">' + catLabel(c) + ' <span class="s-chip-count">' + count + '</span></span>');
        }});
        if (window.__bbsmcAllCats.length > 12) {{
            $('#bbsmcExpandCats').show().text(window.__bbsmcCatsExpanded ? '收起 ▴' : ('展开全部(' + window.__bbsmcAllCats.length + '项) ▾'));
        }} else {{
            $('#bbsmcExpandCats').hide();
        }}
    }}

    $('#bbsmcExpandCats').on('click', function() {{
        window.__bbsmcCatsExpanded = !window.__bbsmcCatsExpanded;
        renderBbsmcCatChips();
    }});

    initBbsmcStats();

    // BBSMC 搜索防抖
    var bbsmcSearchTimer = null;
    $('#bbsmcSearchInput').on('input', function() {{
        var val = $(this).val();
        if (val) {{
            $('#bbsmcSearchClear').show();
        }} else {{
            $('#bbsmcSearchClear').hide();
        }}
        clearTimeout(bbsmcSearchTimer);
        bbsmcSearchTimer = setTimeout(function() {{
            currentBbsmcCardLimit = 48;
            renderBbsmcView();
        }}, 150);
    }});

    $('#bbsmcSearchClear').on('click', function() {{
        $('#bbsmcSearchInput').val('').trigger('input');
    }});

    $('#bbsmcSortSelect, #bbsmcVerSelect, #bbsmcLoaderSelect').on('change', function() {{
        currentBbsmcCardLimit = 48;
        renderBbsmcView();
    }});

    // BBSMC 分类 Chips 点击单选与联动
    // 多选（向 MCMod 看齐）：点「全部」清空；点分类在选中集合里切换；已选中的再点取消
    $('#bbsmcCategoryChips').on('click', '.s-chip', function() {{
        var cat = $(this).data('cat') || '';
        if (!cat) {{
            bbsmcActiveCat = [];
        }} else {{
            var at = bbsmcActiveCat.indexOf(cat);
            if (at === -1) {{ bbsmcActiveCat.push(cat); }} else {{ bbsmcActiveCat.splice(at, 1); }}
        }}
        renderBbsmcCatChips();
        currentBbsmcCardLimit = 48;
        renderBbsmcView();
    }});

    // BBSMC 渠道 Chips 点击
    $('#bbsmcPanChips').on('click', '.s-chip', function() {{
        $('#bbsmcPanChips .s-chip').removeClass('active');
        $(this).addClass('active');
        bbsmcActivePan = $(this).data('pan') || '';
        currentBbsmcCardLimit = 48;
        renderBbsmcView();
    }});

    // BBSMC 活动过滤项清除
    $('#bbsmcActiveFilters').on('click', '.active-pill', function() {{
        var clearType = $(this).data('clear');
        if (clearType === 'search') {{
            $('#bbsmcSearchInput').val('').trigger('input');
        }} else if (clearType === 'cat') {{
            var val = $(this).data('val');
            if (val) {{
                var at = bbsmcActiveCat.indexOf(val);
                if (at !== -1) bbsmcActiveCat.splice(at, 1);
            }} else {{
                bbsmcActiveCat = [];
            }}
            renderBbsmcCatChips();
            currentBbsmcCardLimit = 48;
            renderBbsmcView();
        }} else if (clearType === 'pan') {{
            $('#bbsmcPanChips .s-chip[data-pan=""]').click();
        }} else if (clearType === 'ver') {{
            $('#bbsmcVerSelect').val('').trigger('change');
        }} else if (clearType === 'loader') {{
            $('#bbsmcLoaderSelect').val('').trigger('change');
        }}
    }});

    $('#bbsmcClearFiltersBtn, #bbsmcResetBtn').on('click', function() {{
        bbsmcActiveCat = [];
        bbsmcActivePan = '';
        currentBbsmcCardLimit = 48;
        $('#bbsmcSortSelect').val('downloads_desc').trigger('change');
        $('#bbsmcVerSelect').val('').trigger('change');
        $('#bbsmcLoaderSelect').val('').trigger('change');
        $('#bbsmcSearchInput').val('');
        $('#bbsmcSearchClear').hide();
        renderBbsmcCatChips();
        $('#bbsmcPanChips .s-chip').removeClass('active');
        $('#bbsmcPanChips .s-chip[data-pan=""]').addClass('active');
        renderBbsmcView();
    }});

    // BBSMC 加载更多与展开全部
    $(document).on('click', '.js-bbsmc-load-more', function() {{
        currentBbsmcCardLimit += 48;
        renderBbsmcView();
    }});

    $(document).on('click', '.js-bbsmc-load-all', function() {{
        currentBbsmcCardLimit = 99999;
        renderBbsmcView();
    }});

    // BBSMC 画廊缩略图点击打开灯箱
    $(document).on('click', '.js-bbsmc-lightbox-thumb', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        var full = $(this).data('full') || $(this).attr('src');
        var title = $(this).data('title') || '游戏截图';
        openImageLightbox(full, title);
    }});

    /* ════════ XYEBBS 平台统计与交互事件 ════════ */
    function initXyebbsStats() {{
        if (!xyebbsPacks.length) return;
        var totalDl = 0;
        var totalViews = 0;
        var totalLinks = 0;
        var verSet = {{}};
        var catSet = {{}};

        xyebbsPacks.forEach(function(p) {{
            totalDl += (p.downloads || 0);
            totalViews += (p.views || 0);
            totalLinks += (p.download_links ? p.download_links.length : 0);
            if (p.mc_version && p.mc_version !== '未知') {{
                verSet[p.mc_version] = (verSet[p.mc_version] || 0) + 1;
            }}
            (p.categories || []).forEach(function(c) {{
                if (c) catSet[c] = (catSet[c] || 0) + 1;
            }});
        }});

        var dlText = totalDl > 100000000 ? (totalDl / 100000000).toFixed(2) + '亿' :
                     (totalDl > 10000 ? (totalDl / 10000).toFixed(1) + '万' : totalDl);
        var viewText = totalViews > 100000000 ? (totalViews / 100000000).toFixed(2) + '亿' :
                       (totalViews > 10000 ? (totalViews / 10000).toFixed(1) + '万' : totalViews);

        $('#xyebbsStatDownloads').text(dlText);
        $('#xyebbsStatViews').text(viewText);
        $('#xyebbsStatLinks').text(totalLinks.toLocaleString() + ' 个');
        $('#xyebbsStatTotal').text((xyebbsPacks.length || 5175).toLocaleString() + ' 款');

        $('#topNavXyebbsBadge').text(xyebbsPacks.length.toLocaleString());

        // 填充 XYEBBS 版本下拉选项
        var sortedVers = Object.keys(verSet).sort(function(a, b) {{ return verSet[b] - verSet[a]; }});
        var $verSel = $('#xyebbsVerSelect');
        sortedVers.forEach(function(v) {{
            $verSel.append('<option value="' + v + '">' + v + ' (' + verSet[v] + ')</option>');
        }});
        $verSel.trigger('change.select2');

        // 填充 XYEBBS 玩法专区 Chips
        var sortedCats = Object.keys(catSet).sort(function(a, b) {{ return catSet[b] - catSet[a]; }});
        window.__xyebbsAllCats = sortedCats;
        window.__xyebbsCatCounts = catSet;
        window.__xyebbsCatsExpanded = false;
        renderXyebbsCatChips();
    }}

    function renderXyebbsCatChips() {{
        var $catChips = $('#xyebbsCategoryChips');
        $catChips.empty();
        $catChips.append('<span class="s-chip' + (xyebbsActiveCat.length === 0 ? ' active' : '') + '" data-cat="">全部玩法</span>');
        var maxVisible = window.__xyebbsCatsExpanded ? window.__xyebbsAllCats.length : 12;
        window.__xyebbsAllCats.forEach(function(c, idx) {{
            var isSelected = xyebbsActiveCat.indexOf(c) !== -1;
            var isVisible = idx < maxVisible || isSelected;
            var count = window.__xyebbsCatCounts[c] || 0;
            $catChips.append('<span class="s-chip' + (isSelected ? ' active' : '') + '" data-cat="' + c + '" title="' + c + '" style="' + (isVisible ? '' : 'display:none;') + '">' + catLabel(c) + ' <span class="s-chip-count">' + count + '</span></span>');
        }});
        if (window.__xyebbsAllCats.length > 12) {{
            $('#xyebbsExpandCats').show().text(window.__xyebbsCatsExpanded ? '收起 ▴' : ('展开全部(' + window.__xyebbsAllCats.length + '项) ▾'));
        }} else {{
            $('#xyebbsExpandCats').hide();
        }}
    }}

    $('#xyebbsExpandCats').on('click', function() {{
        window.__xyebbsCatsExpanded = !window.__xyebbsCatsExpanded;
        renderXyebbsCatChips();
    }});

    initXyebbsStats();

    // XYEBBS 搜索防抖
    var xyebbsSearchTimer = null;
    $('#xyebbsSearchInput').on('input', function() {{
        var val = $(this).val().trim();
        if (val) {{
            $('#xyebbsSearchClear').show();
        }} else {{
            $('#xyebbsSearchClear').hide();
        }}
        clearTimeout(xyebbsSearchTimer);
        xyebbsSearchTimer = setTimeout(function() {{
            currentXyebbsCardLimit = 48;
            renderXyebbsView();
        }}, 250);
    }});

    $('#xyebbsSearchClear').on('click', function() {{
        $('#xyebbsSearchInput').val('').trigger('input');
    }});

    $('#xyebbsSortSelect, #xyebbsVerSelect, #xyebbsLoaderSelect').on('change', function() {{
        currentXyebbsCardLimit = 48;
        renderXyebbsView();
    }});

    // XYEBBS 分类 Chips 点击单选与联动
    // 多选（向 MCMod 看齐）：点「全部」清空；点分类在选中集合里切换；已选中的再点取消
    $('#xyebbsCategoryChips').on('click', '.s-chip', function() {{
        var cat = $(this).data('cat') || '';
        if (!cat) {{
            xyebbsActiveCat = [];
        }} else {{
            var at = xyebbsActiveCat.indexOf(cat);
            if (at === -1) {{ xyebbsActiveCat.push(cat); }} else {{ xyebbsActiveCat.splice(at, 1); }}
        }}
        renderXyebbsCatChips();
        currentXyebbsCardLimit = 48;
        renderXyebbsView();
    }});

    // XYEBBS 渠道 Chips 点击
    $('#xyebbsPanChips').on('click', '.s-chip', function() {{
        $('#xyebbsPanChips .s-chip').removeClass('active');
        $(this).addClass('active');
        xyebbsActivePan = $(this).data('pan') || '';
        currentXyebbsCardLimit = 48;
        renderXyebbsView();
    }});

    // XYEBBS 活动过滤项清除
    $('#xyebbsActiveFilters').on('click', '.active-pill', function() {{
        var clearType = $(this).data('clear');
        if (clearType === 'search') {{
            $('#xyebbsSearchInput').val('').trigger('input');
        }} else if (clearType === 'cat') {{
            var val = $(this).data('val');
            if (val) {{
                var at = xyebbsActiveCat.indexOf(val);
                if (at !== -1) xyebbsActiveCat.splice(at, 1);
            }} else {{
                xyebbsActiveCat = [];
            }}
            renderXyebbsCatChips();
            currentXyebbsCardLimit = 48;
            renderXyebbsView();
        }} else if (clearType === 'pan') {{
            $('#xyebbsPanChips .s-chip[data-pan=""]').click();
        }} else if (clearType === 'ver') {{
            $('#xyebbsVerSelect').val('').trigger('change');
        }} else if (clearType === 'loader') {{
            $('#xyebbsLoaderSelect').val('').trigger('change');
        }}
    }});

    $('#xyebbsClearFiltersBtn, #xyebbsResetBtn').on('click', function() {{
        xyebbsActiveCat = [];
        xyebbsActivePan = '';
        currentXyebbsCardLimit = 48;
        $('#xyebbsSortSelect').val('hot_desc').trigger('change');
        $('#xyebbsVerSelect').val('').trigger('change');
        $('#xyebbsLoaderSelect').val('').trigger('change');
        $('#xyebbsSearchInput').val('');
        $('#xyebbsSearchClear').hide();
        renderXyebbsCatChips();
        $('#xyebbsPanChips .s-chip').removeClass('active');
        $('#xyebbsPanChips .s-chip[data-pan=""]').addClass('active');
        renderXyebbsView();
    }});

    // XYEBBS 加载更多与展开全部
    $(document).on('click', '.js-xyebbs-load-more', function() {{
        currentXyebbsCardLimit += 48;
        renderXyebbsView();
    }});

    $(document).on('click', '.js-xyebbs-load-all', function() {{
        currentXyebbsCardLimit = 99999;
        renderXyebbsView();
    }});

    /* ════════ Modrinth 平台统计与交互事件 ════════ */
    function initModrinthStats() {{
        if (!modrinthPacks.length) return;
        var totalDl = 0;
        var totalFollows = 0;
        var verSet = {{}};
        var catSet = {{}};

        modrinthPacks.forEach(function(p) {{
            totalDl += (p.downloads || 0);
            totalFollows += (p.followers || 0);
            if (p.mc_version && p.mc_version !== '未知') {{
                verSet[p.mc_version] = (verSet[p.mc_version] || 0) + 1;
            }}
            (p.categories || []).forEach(function(c) {{
                if (c) catSet[c] = (catSet[c] || 0) + 1;
            }});
        }});

        var dlText = totalDl > 100000000 ? (totalDl / 100000000).toFixed(2) + '亿' :
                     (totalDl > 10000 ? (totalDl / 10000).toFixed(1) + '万' : totalDl);
        var flText = totalFollows > 10000 ? (totalFollows / 10000).toFixed(1) + '万' : totalFollows;

        $('#modrinthStatDownloads').text(dlText);
        $('#modrinthStatFollows').text(flText);
        $('#modrinthStatTotal').text((modrinthPacks.length || 18328).toLocaleString() + ' 款');

        // 主流加载器占比：纯统计真实 loaders 字段，不做任何推断
        var ldSet = {{}}, ldTotal = 0;
        modrinthPacks.forEach(function(p) {{
            (p.loaders || []).forEach(function(l) {{ ldSet[l] = (ldSet[l] || 0) + 1; ldTotal++; }});
        }});
        var ldTop = Object.keys(ldSet).sort(function(a, b) {{ return ldSet[b] - ldSet[a]; }})[0];
        if (ldTop) {{
            var ldPct = (ldSet[ldTop] * 100.0 / ldTotal).toFixed(1);
            $('#modrinthStatTopLoader').text(loaderLabel(ldTop));
            $('#modrinthStatTopLoaderItem').attr('title', loaderLabel(ldTop) + ' 覆盖 ' + ldPct + '% 的整合包');
        }}

        var sortedVers = Object.keys(verSet).sort(function(a, b) {{ return verSet[b] - verSet[a]; }});
        var $verSel = $('#modrinthVerSelect');
        sortedVers.forEach(function(v) {{
            $verSel.append('<option value="' + v + '">' + v + ' (' + verSet[v] + ')</option>');
        }});
        $verSel.trigger('change.select2');

        var sortedCats = Object.keys(catSet).sort(function(a, b) {{ return catSet[b] - catSet[a]; }});
        window.__modrinthAllCats = sortedCats;
        window.__modrinthCatCounts = catSet;
        window.__modrinthCatsExpanded = false;
        renderModrinthCatChips();
    }}

    function renderModrinthCatChips() {{
        var $catChips = $('#modrinthCategoryChips');
        $catChips.empty();
        $catChips.append('<span class="s-chip' + (modrinthActiveCat.length === 0 ? ' active' : '') + '" data-cat="">全部玩法</span>');
        var maxVisible = window.__modrinthCatsExpanded ? window.__modrinthAllCats.length : 12;
        window.__modrinthAllCats.forEach(function(c, idx) {{
            var isSelected = modrinthActiveCat.indexOf(c) !== -1;
            var isVisible = idx < maxVisible || isSelected;
            var count = window.__modrinthCatCounts[c] || 0;
            $catChips.append('<span class="s-chip' + (isSelected ? ' active' : '') + '" data-cat="' + c + '" title="' + c + '" style="' + (isVisible ? '' : 'display:none;') + '">' + catLabel(c) + ' <span class="s-chip-count">' + count + '</span></span>');
        }});
        if (window.__modrinthAllCats.length > 12) {{
            $('#modrinthExpandCats').show().text(window.__modrinthCatsExpanded ? '收起 ▴' : ('展开全部(' + window.__modrinthAllCats.length + '项) ▾'));
        }} else {{
            $('#modrinthExpandCats').hide();
        }}
    }}

    $('#modrinthExpandCats').on('click', function() {{
        window.__modrinthCatsExpanded = !window.__modrinthCatsExpanded;
        renderModrinthCatChips();
    }});

    initModrinthStats();

    var modrinthSearchTimer = null;
    $('#modrinthSearchInput').on('input', function() {{
        var val = $(this).val().trim();
        if (val) $('#modrinthSearchClear').show();
        else $('#modrinthSearchClear').hide();
        clearTimeout(modrinthSearchTimer);
        modrinthSearchTimer = setTimeout(function() {{
            currentModrinthCardLimit = 48;
            renderModrinthView();
        }}, 250);
    }});

    $('#modrinthSearchClear').on('click', function() {{
        $('#modrinthSearchInput').val('').trigger('input');
    }});

    $('#modrinthSortSelect, #modrinthVerSelect, #modrinthLoaderSelect').on('change', function() {{
        currentModrinthCardLimit = 48;
        renderModrinthView();
    }});

    // 多选（向 MCMod 看齐）：点「全部」清空；点分类在选中集合里切换；已选中的再点取消
    $('#modrinthCategoryChips').on('click', '.s-chip', function() {{
        var cat = $(this).data('cat') || '';
        if (!cat) {{
            modrinthActiveCat = [];
        }} else {{
            var at = modrinthActiveCat.indexOf(cat);
            if (at === -1) {{ modrinthActiveCat.push(cat); }} else {{ modrinthActiveCat.splice(at, 1); }}
        }}
        renderModrinthCatChips();
        currentModrinthCardLimit = 48;
        renderModrinthView();
    }});

    $('#modrinthActiveFilters').on('click', '.active-pill', function() {{
        var clearType = $(this).data('clear');
        if (clearType === 'search') $('#modrinthSearchInput').val('').trigger('input');
        else if (clearType === 'cat') {{
            var val = $(this).data('val');
            if (val) {{
                var at = modrinthActiveCat.indexOf(val);
                if (at !== -1) modrinthActiveCat.splice(at, 1);
            }} else {{
                modrinthActiveCat = [];
            }}
            renderModrinthCatChips();
            currentModrinthCardLimit = 48;
            renderModrinthView();
        }}
        else if (clearType === 'ver') $('#modrinthVerSelect').val('').trigger('change');
        else if (clearType === 'loader') $('#modrinthLoaderSelect').val('').trigger('change');
    }});

    $('#modrinthClearFiltersBtn, #modrinthResetBtn').on('click', function() {{
        modrinthActiveCat = [];
        currentModrinthCardLimit = 48;
        $('#modrinthSortSelect').val('downloads_desc').trigger('change');
        $('#modrinthVerSelect').val('').trigger('change');
        $('#modrinthLoaderSelect').val('').trigger('change');
        $('#modrinthSearchInput').val('');
        $('#modrinthSearchClear').hide();
        renderModrinthCatChips();
        renderModrinthView();
    }});

    $(document).on('click', '.js-modrinth-load-more', function() {{
        currentModrinthCardLimit += 48;
        renderModrinthView();
    }});

    $(document).on('click', '.js-modrinth-load-all', function() {{
        currentModrinthCardLimit = 99999;
        renderModrinthView();
    }});

    /* ════════ CurseForge 平台统计与交互事件 ════════ */
    function initCurseforgeStats() {{
        if (!curseforgePacks.length) return;
        var totalDl = 0;
        var totalLikes = 0;
        var verSet = {{}};
        var catSet = {{}};

        curseforgePacks.forEach(function(p) {{
            totalDl += (p.downloads || 0);
            totalLikes += (p.followers || 0);
            if (p.mc_version && p.mc_version !== '未知') {{
                verSet[p.mc_version] = (verSet[p.mc_version] || 0) + 1;
            }}
            (p.categories || []).forEach(function(c) {{
                if (c) catSet[c] = (catSet[c] || 0) + 1;
            }});
        }});

        var dlText = totalDl > 100000000 ? (totalDl / 100000000).toFixed(2) + '亿' :
                     (totalDl > 10000 ? (totalDl / 10000).toFixed(1) + '万' : totalDl);
        var lkText = totalLikes > 10000 ? (totalLikes / 10000).toFixed(1) + '万' : totalLikes;

        $('#curseforgeStatDownloads').text(dlText);
        $('#curseforgeStatLikes').text(lkText);
        $('#curseforgeStatTotal').text((curseforgePacks.length || 45797).toLocaleString() + ' 款');

        // 主流加载器占比：纯统计真实 loaders 字段，不做任何推断
        var ldSetC = {{}}, ldTotalC = 0;
        curseforgePacks.forEach(function(p) {{
            (p.loaders || []).forEach(function(l) {{ ldSetC[l] = (ldSetC[l] || 0) + 1; ldTotalC++; }});
        }});
        var ldTopC = Object.keys(ldSetC).sort(function(a, b) {{ return ldSetC[b] - ldSetC[a]; }})[0];
        if (ldTopC) {{
            var ldPctC = (ldSetC[ldTopC] * 100.0 / ldTotalC).toFixed(1);
            $('#curseforgeStatTopLoader').text(loaderLabel(ldTopC));
            $('#curseforgeStatTopLoaderItem').attr('title', loaderLabel(ldTopC) + ' 覆盖 ' + ldPctC + '% 的整合包');
        }}

        var sortedVers = Object.keys(verSet).sort(function(a, b) {{ return verSet[b] - verSet[a]; }});
        var $verSel = $('#curseforgeVerSelect');
        sortedVers.forEach(function(v) {{
            $verSel.append('<option value="' + v + '">' + v + ' (' + verSet[v] + ')</option>');
        }});
        $verSel.trigger('change.select2');

        var sortedCats = Object.keys(catSet).sort(function(a, b) {{ return catSet[b] - catSet[a]; }});
        window.__curseforgeAllCats = sortedCats;
        window.__curseforgeCatCounts = catSet;
        window.__curseforgeCatsExpanded = false;
        renderCurseforgeCatChips();
    }}

    function renderCurseforgeCatChips() {{
        var $catChips = $('#curseforgeCategoryChips');
        $catChips.empty();
        $catChips.append('<span class="s-chip' + (curseforgeActiveCat.length === 0 ? ' active' : '') + '" data-cat="">全部玩法</span>');
        var maxVisible = window.__curseforgeCatsExpanded ? window.__curseforgeAllCats.length : 12;
        window.__curseforgeAllCats.forEach(function(c, idx) {{
            var isSelected = curseforgeActiveCat.indexOf(c) !== -1;
            var isVisible = idx < maxVisible || isSelected;
            var count = window.__curseforgeCatCounts[c] || 0;
            $catChips.append('<span class="s-chip' + (isSelected ? ' active' : '') + '" data-cat="' + c + '" title="' + c + '" style="' + (isVisible ? '' : 'display:none;') + '">' + catLabel(c) + ' <span class="s-chip-count">' + count + '</span></span>');
        }});
        if (window.__curseforgeAllCats.length > 12) {{
            $('#curseforgeExpandCats').show().text(window.__curseforgeCatsExpanded ? '收起 ▴' : ('展开全部(' + window.__curseforgeAllCats.length + '项) ▾'));
        }} else {{
            $('#curseforgeExpandCats').hide();
        }}
    }}

    $('#curseforgeExpandCats').on('click', function() {{
        window.__curseforgeCatsExpanded = !window.__curseforgeCatsExpanded;
        renderCurseforgeCatChips();
    }});

    initCurseforgeStats();

    var curseforgeSearchTimer = null;
    $('#curseforgeSearchInput').on('input', function() {{
        var val = $(this).val().trim();
        if (val) $('#curseforgeSearchClear').show();
        else $('#curseforgeSearchClear').hide();
        clearTimeout(curseforgeSearchTimer);
        curseforgeSearchTimer = setTimeout(function() {{
            currentCurseforgeCardLimit = 48;
            renderCurseforgeView();
        }}, 250);
    }});

    $('#curseforgeSearchClear').on('click', function() {{
        $('#curseforgeSearchInput').val('').trigger('input');
    }});

    $('#curseforgeSortSelect, #curseforgeVerSelect, #curseforgeLoaderSelect').on('change', function() {{
        currentCurseforgeCardLimit = 48;
        renderCurseforgeView();
    }});

    // 多选（向 MCMod 看齐）：点「全部」清空；点分类在选中集合里切换；已选中的再点取消
    $('#curseforgeCategoryChips').on('click', '.s-chip', function() {{
        var cat = $(this).data('cat') || '';
        if (!cat) {{
            curseforgeActiveCat = [];
        }} else {{
            var at = curseforgeActiveCat.indexOf(cat);
            if (at === -1) {{ curseforgeActiveCat.push(cat); }} else {{ curseforgeActiveCat.splice(at, 1); }}
        }}
        renderCurseforgeCatChips();
        currentCurseforgeCardLimit = 48;
        renderCurseforgeView();
    }});

    $('#curseforgeActiveFilters').on('click', '.active-pill', function() {{
        var clearType = $(this).data('clear');
        if (clearType === 'search') $('#curseforgeSearchInput').val('').trigger('input');
        else if (clearType === 'cat') {{
            var val = $(this).data('val');
            if (val) {{
                var at = curseforgeActiveCat.indexOf(val);
                if (at !== -1) curseforgeActiveCat.splice(at, 1);
            }} else {{
                curseforgeActiveCat = [];
            }}
            renderCurseforgeCatChips();
            currentCurseforgeCardLimit = 48;
            renderCurseforgeView();
        }}
        else if (clearType === 'ver') $('#curseforgeVerSelect').val('').trigger('change');
        else if (clearType === 'loader') $('#curseforgeLoaderSelect').val('').trigger('change');
    }});

    $('#curseforgeClearFiltersBtn, #curseforgeResetBtn').on('click', function() {{
        curseforgeActiveCat = [];
        currentCurseforgeCardLimit = 48;
        $('#curseforgeSortSelect').val('downloads_desc').trigger('change');
        $('#curseforgeVerSelect').val('').trigger('change');
        $('#curseforgeLoaderSelect').val('').trigger('change');
        $('#curseforgeSearchInput').val('');
        $('#curseforgeSearchClear').hide();
        renderCurseforgeCatChips();
        renderCurseforgeView();
    }});

    $(document).on('click', '.js-curseforge-load-more', function() {{
        currentCurseforgeCardLimit += 48;
        renderCurseforgeView();
    }});

    $(document).on('click', '.js-curseforge-load-all', function() {{
        currentCurseforgeCardLimit = 99999;
        renderCurseforgeView();
    }});

    // 全局六大平台总徽标动态刷新
    function updateAllPlatformsTotalBadge() {{
        var mcCount = (window.tableRowsData ? window.tableRowsData.length : 1484);
        var biliCount = (window.biliModpacksData ? window.biliModpacksData.length : 935);
        var bbsmcCount = (window.bbsmcModpacksData ? window.bbsmcModpacksData.length : 1802);
        var xyebbsCount = (window.xyebbsModpacksData ? window.xyebbsModpacksData.length : 5175);
        var modrinthCount = (window.modrinthModpacksData ? window.modrinthModpacksData.length : 18328);
        var curseforgeCount = (window.curseforgeModpacksData ? window.curseforgeModpacksData.length : 45797);

        var totalAll = mcCount + biliCount + bbsmcCount + xyebbsCount + modrinthCount + curseforgeCount;
        $('#topNavAllBadge').text(totalAll.toLocaleString());
        $('#topNavMcmodBadge').text(mcCount.toLocaleString());
        $('#topNavBiliBadge').text(biliCount.toLocaleString());
        $('#topNavBbsmcBadge').text(bbsmcCount.toLocaleString());
        $('#topNavXyebbsBadge').text(xyebbsCount.toLocaleString());
        $('#topNavModrinthBadge').text(modrinthCount.toLocaleString());
        $('#topNavCurseforgeBadge').text(curseforgeCount.toLocaleString());
    }}
    updateAllPlatformsTotalBadge();
    startIdlePrefetch();


    /* ════════ 主题切换 ════════ */
    var savedTheme = localStorage.getItem('mcmod-theme-v2') || 'light';
    function setTheme(theme) {{
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('mcmod-theme-v2', theme);
        $('.theme-btn').removeClass('active');
        $('.theme-btn[data-theme="' + theme + '"]').addClass('active');
    }}
    setTheme(savedTheme);
    $('.theme-btn').on('click', function() {{
        setTheme($(this).data('theme'));
    }});
    // 普通基础多选下拉（选项较少：分类、包标签、模组分类）
    $('#categoryFilter, #packTagFilter, #modCategoryFilter').select2({{
        theme: 'bootstrap-5',
        width: '100%',
        closeOnSelect: false,
        placeholder: function() {{ return $(this).data('placeholder') || '全部'; }}
    }});

    // 针对 1.1 万个模组的海量多选：采用毫秒级流式 query 匹配，彻底消除 3 秒 UI 假死与鼠标卡顿
    $('#modFilter').select2({{
        theme: 'bootstrap-5',
        width: '100%',
        closeOnSelect: false,
        placeholder: '输入模组名称检索（1.1万模组）',
        minimumInputLength: 1,
        dropdownCssClass: 'hub-select2-dropdown',
        query: function(options) {{
            var term = (options.term || '').toLowerCase().trim();
            var matches = [];
            var list = window.allModsList || [];
            if ((!list || !list.length) && window.compareData) {{
                var modCountMap = {{}};
                Object.values(window.compareData).forEach(function(p) {{
                    (p.mods || []).forEach(function(m) {{
                        var mn = typeof m === 'string' ? m : (m.name || '');
                        if (mn) modCountMap[mn] = (modCountMap[mn] || 0) + 1;
                    }});
                }});
                window.allModsList = Object.keys(modCountMap).map(function(k) {{
                    return {{ id: k, text: k + ' (' + modCountMap[k] + ')' }};
                }}).sort(function(a, b) {{ return b.text.localeCompare(a.text); }});
                list = window.allModsList;
            }}
            for (var i = 0; i < list.length; i++) {{
                var item = list[i];
                if (item.text.toLowerCase().indexOf(term) !== -1) {{
                    matches.push(item);
                    if (matches.length >= 60) break;
                }}
            }}
            options.callback({{ results: matches }});
        }}
    }});

    function renderActiveModBadges() {{
        var vals = $('#modFilter').val() || [];
        if (!Array.isArray(vals)) vals = vals ? [vals] : [];
        var $badges = $('#activeModBadges');
        if (!$badges.length) return;
        $badges.empty();
        if (!vals.length) return;
        $badges.append('<span style="font-size:0.75rem; font-weight:750; color:var(--text-muted); margin-right:2px;">已包含：</span>');
        vals.forEach(function(val) {{
            var $pill = $('<span class="active-mod-pill" title="点击 ✕ 移除该模组筛选"><span class="pill-name"></span><button type="button" class="pill-remove-btn">✕</button></span>');
            $pill.find('.pill-name').text(val);
            $pill.find('.pill-remove-btn').attr('data-val', val);
            $badges.append($pill);
        }});
    }}

    $('#modFilter').on('select2:select', function(e) {{
        var data = (e && e.params && e.params.data) || {{}};
        if (data && data.id) {{
            if (!$('#modFilter').find('option[value="' + data.id + '"]').length) {{
                $('#modFilter').append(new Option(data.text || data.id, data.id, true, true));
            }}
        }}
        renderActiveModBadges();
    }});

    $('#modFilter').on('select2:unselect', function(e) {{
        var data = (e && e.params && e.params.data) || {{}};
        if (data && data.id) {{
            $('#modFilter').find('option[value="' + data.id + '"]').remove();
        }}
        renderActiveModBadges();
    }});

    $('#modFilter').on('change', function() {{
        renderActiveModBadges();
    }});

    $('#activeModBadges').on('click', '.pill-remove-btn', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        var val = $(this).attr('data-val');
        var current = $('#modFilter').val() || [];
        if (!Array.isArray(current)) current = current ? [current] : [];
        var idx = current.indexOf(val);
        if (idx >= 0) {{
            current.splice(idx, 1);
            $('#modFilter').find('option[value="' + val + '"]').remove();
            $('#modFilter').val(current).trigger('change');
        }}
    }});
    $('.select2-glass-single').select2({{
        theme: 'bootstrap-5',
        width: '100%',
        minimumResultsForSearch: 8,
        selectionCssClass: 'select2-glass-selection',
        dropdownCssClass: 'select2-glass-dropdown',
        placeholder: function() {{ return $(this).data('placeholder') || '全部'; }}
    }});
    // 🌟 全局中央单选下拉框升级 Select2 晶透毛玻璃组件（彻底消除 Windows 原生系统黑框蓝条）
    $('.select2-hub').select2({{
        theme: 'bootstrap-5',
        width: 'auto',
        dropdownAutoWidth: true,
        minimumResultsForSearch: 8,
        selectionCssClass: 'hub-select2-selection',
        dropdownCssClass: 'hub-select2-dropdown'
    }});
    /* ════════ DataTables 初始化（scrollY 固定表头 + 分页优化） ════════ */
    // 🌟 性能优化：将重量级的表格初始化推入下一个事件循环，让 Select2 优先完成重绘，彻底解除页面开启瞬间的 UI 卡死
    setTimeout(function() {{
        /* ════════ 全文穿透搜索引擎：支持范围自定义的全局检索 ════════ */
        function normalizeSearchKeyword() {{
            var $filterInput = $('#modpackTable_filter input');
            return $filterInput.length > 0 ? $filterInput.val().trim() : '';
        }}
        function textHasKeyword(text, keyword) {{
            return !!(text && keyword && String(text).toLowerCase().indexOf(keyword.toLowerCase()) !== -1);
        }}
        function findCommentMatch(cmt, keyword) {{
            if (!cmt || !cmt.comments || !keyword) return -1;
            for (var j = 0; j < cmt.comments.length; j++) {{
                var c = cmt.comments[j];
                if (textHasKeyword(c.text, keyword) || textHasKeyword(c.author, keyword)) return j;
                if (c.replies) {{
                    for (var k = 0; k < c.replies.length; k++) {{
                        var r = c.replies[k];
                        if (textHasKeyword(r.text, keyword) || textHasKeyword(r.author, keyword)) return j;
                    }}
                }}
            }}
            return -1;
        }}
        function matchRowSearch(data, tr, keyword, scope) {{
            var result = {{ basic: false, title: false, cat: false, desc: false, comment: false, commentIndex: -1 }};
            if (!keyword) return result;
            var kw = keyword.toLowerCase();
            for (var i = 0; i < data.length; i++) {{
                if (String(data[i] || '').toLowerCase().indexOf(kw) !== -1) {{
                    result.basic = true; break;
                }}
            }}
            result.title = String(data[0] || '').toLowerCase().indexOf(kw) !== -1;
            result.cat = String(data[6] || '').toLowerCase().indexOf(kw) !== -1 ||
                         String(data[7] || '').toLowerCase().indexOf(kw) !== -1;
            var mid = $(tr).find('a.modpack-link').data('mid');
            if (mid) {{
                result.desc = textHasKeyword(getDescText(descData[mid]), keyword);
                result.commentIndex = findCommentMatch(commentData[mid], keyword);
                result.comment = result.commentIndex >= 0;
            }}
            return result;
        }}
        function rowMatchesScope(match, scope) {{
            if (scope === 'title') return match.title;
            if (scope === 'cat') return match.cat;
            if (scope === 'desc') return match.desc;
            if (scope === 'comment') return match.comment;
            if (scope === 'basic') return match.basic;
            return match.basic || match.desc || match.comment;
        }}
        function matchRowSearchFast(data, rowData, keyword, scope) {{
            var result = {{ basic: false, title: false, cat: false, desc: false, comment: false, commentIndex: -1 }};
            if (!keyword) return result;
            var kw = keyword.toLowerCase();
            result.title = (rowData.title || '').toLowerCase().indexOf(kw) !== -1;
            result.cat = (rowData.cat_search || '').toLowerCase().indexOf(kw) !== -1 ||
                         (rowData.pack_search || '').toLowerCase().indexOf(kw) !== -1;
            var mid = rowData.mid;
            if (mid) {{
                result.desc = textHasKeyword(getDescText(descData[mid]), keyword);
                result.commentIndex = findCommentMatch(commentData[mid], keyword);
                result.comment = result.commentIndex >= 0;
            }}
            result.basic = result.title || result.cat || (rowData.mods_search || '').toLowerCase().indexOf(kw) !== -1;
            return result;
        }}

        $.fn.dataTable.ext.search.push(
            function(settings, data, dataIndex) {{
                var keyword = normalizeSearchKeyword();
                if (!keyword) return true;
                var scope = $('#searchScope').val() || 'all';
                var rowData = (window.tableRowsData && window.tableRowsData[dataIndex]);
                if (!rowData) return true;
                return rowMatchesScope(matchRowSearchFast(data, rowData, keyword, scope), scope);
            }}
        );
        var _scrollH = Math.max(400, $(window).height() - 320);
    var table = null;

    /* ════════ DataTables 初始化（数据驱动 + 真正 deferRender 延迟渲染） ════════ */
    window.initMcmodTable = function() {{
        if ($.fn.DataTable && $.fn.DataTable.isDataTable('#modpackTable')) {{
            if (window.table) window.table.columns.adjust();
            return;
        }}
        if (!window.tableRowsData || !window.tableRowsData.length) return;
        // 初始化每个 row 对象的排序字段缓存
        window.tableRowsData.forEach(function(r) {{
            r.sort_col0 = r.name_order || '';
            r.sort_col1 = (typeof r.score_n === 'number' ? r.score_n : (parseFloat(r.score_n) || 0));
            r.sort_col2 = (typeof r.t7_n === 'number' ? r.t7_n : (parseFloat(r.t7_n) || 0));
            r.sort_col3 = (typeof r.rv_n === 'number' ? r.rv_n : (parseFloat(r.rv_n) || 0));
            r.sort_col4 = (typeof r.com_n === 'number' ? r.com_n : (parseFloat(r.com_n) || 0));
            r.sort_col5 = (typeof r.tag_count === 'number' ? r.tag_count : (parseInt(r.tag_count) || 0));
            r.sort_col6 = (typeof r.mod_count === 'number' ? r.mod_count : (parseInt(r.mod_count) || 0));
        }});

        table = window.table = $('#modpackTable').DataTable({{
        "data": window.tableRowsData || [],
        "deferRender": true,
        "columns": [
            {{
                "data": "c0",
                "orderSequence": ["asc", "desc"],
                "render": function(data, type, row) {{
                    if (type === 'sort' || type === 'order') return row.sort_col0;
                    if (type === 'filter' || type === 'search') return (row.title || '') + ' ' + (row.type_name || '');
                    return data;
                }}
            }},
            {{
                "data": "c1",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {{
                    if (type === 'sort' || type === 'order') return row.sort_col1;
                    return data;
                }}
            }},
            {{
                "data": "c2",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {{
                    if (type === 'sort' || type === 'order') return row.sort_col2;
                    return data;
                }}
            }},
            {{
                "data": "c3",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {{
                    if (type === 'sort' || type === 'order') return row.sort_col3;
                    return data;
                }}
            }},
            {{
                "data": "c4",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {{
                    if (type === 'sort' || type === 'order') return row.sort_col4;
                    return data;
                }}
            }},
            {{
                "data": "c5",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {{
                    if (type === 'sort' || type === 'order') return row.sort_col5;
                    if (type === 'filter' || type === 'search') return row.tags_search || '';
                    return data;
                }}
            }},
            {{
                "data": "c6",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {{
                    if (type === 'sort' || type === 'order') return row.sort_col6;
                    if (type === 'filter' || type === 'search') return row.mods_search || '';
                    return data;
                }}
            }}
        ],
        "createdRow": function(row, rowData, dataIndex) {{
            $(row).attr('data-row', dataIndex).attr('data-mid', rowData.mid);
            var $tds = $(row).children('td');
            $tds.eq(0).addClass('td-title' + (rowData.has_cover ? ' has-cover' : ''))
                      .attr('data-type-search', rowData.type_name)
                      .attr('data-name', rowData.name_order)
                      .attr('data-order', rowData.sort_col0)
                      .attr('data-views', rowData.views_n);
            $tds.eq(1).addClass('td-trend')
                      .attr('data-score', rowData.score_n)
                      .attr('data-lat', rowData.lat_n)
                      .attr('data-max', rowData.max_n)
                      .attr('data-avg', rowData.avg_n)
                      .attr('data-days', rowData.days_n)
                      .attr('data-order', rowData.sort_col1)
                      .attr('data-trend', rowData.trend_vals)
                      .attr('data-dates', rowData.trend_dates)
                      .attr('data-title', rowData.title);
            $tds.eq(2).addClass('td-trend')
                      .attr('data-t7', rowData.t7_n)
                      .attr('data-t30', rowData.t30_n)
                      .attr('data-t60', rowData.t60_n)
                      .attr('data-tall', rowData.tall_n)
                      .attr('data-order', rowData.sort_col2);
            $tds.eq(3).addClass('td-votes')
                      .attr('data-rv', rowData.rv_n)
                      .attr('data-rp', rowData.rp_n)
                      .attr('data-bv', rowData.bv_n)
                      .attr('data-bp', rowData.bp_n)
                      .attr('data-order', rowData.sort_col3);
            $tds.eq(4).addClass('td-engage td-comment')
                      .attr('data-rec', rowData.rec_n)
                      .attr('data-fav', rowData.fav_n)
                      .attr('data-com', rowData.com_n)
                      .attr('data-order', rowData.sort_col4)
                      .attr('data-mid', rowData.mid);
            $tds.eq(5).addClass('td-tags')
                      .attr('data-search', rowData.tags_search)
                      .attr('data-cat-search', rowData.cat_search)
                      .attr('data-pack-search', rowData.pack_search)
                      .attr('data-count', rowData.tag_count)
                      .attr('data-order', rowData.sort_col5);
            $tds.eq(6).addClass('td-mods')
                      .attr('data-search', rowData.mods_search)
                      .attr('data-count', rowData.mod_count)
                      .attr('data-order', rowData.sort_col6);
        }},

        "scrollX": true,
        "autoWidth": false,
        "search": {{
            "smart": false
        }},
        "order": [[1, "desc"]],       // 默认按「官方流行指数」降序（已并入趋势列）
        "pageLength": 25,             // ★ 默认每页 25 条
        "paging": true,
        "deferRender": true,
        "lengthChange": true,
        "lengthMenu": [[25, 50, 100, 200, -1], [25, 50, 100, 200, "全部"]],
        "scrollY": _scrollH,
        "scrollCollapse": true,
        "language": {{
            "search": "🔍 全局关键字检索：",
            "info": "当前第 _START_ - _END_ 条 / 共 _TOTAL_ 条 · 筛选自 _MAX_ 条",
            "infoEmpty": "暂无匹配记录",
            "infoFiltered": "(从 _MAX_ 条总记录中筛选)",
            "zeroRecords": "没有找到符合条件的整合包",
            "lengthMenu": "每页显示 _MENU_ 条",
            "paginate": {{
                "first": "«",
                "last": "»",
                "next": "›",
                "previous": "‹"
            }}
        }},
        "columnDefs": [
            {{ "width": "220px", "targets": 0 }},
            {{ "width": "150px", "targets": 1 }},
            {{ "width": "118px", "targets": 2 }},
            {{ "width": "112px", "targets": 3 }},
            {{ "width": "104px", "targets": 4 }},
            {{ "width": "220px", "targets": 5 }},
            {{ "width": "calc(100vw - 900px)", "targets": 6 }},
            {{ "orderable": true,  "targets": [0,1,2,3,4,5,6] }}
        ],
        "initComplete": function() {{
            var api = this.api();
            /* 将每页条数选择器整合进顶部极简工具栏，消除自带表格上方空缺与重复搜索框 */
            var $wrapper = $(this.api().table().container());
            var $length = $wrapper.find('.dataTables_length');
            var $filter = $wrapper.find('.dataTables_filter');
            var $info = $wrapper.find('.dataTables_info');
            var $paginate = $wrapper.find('.dataTables_paginate');
            if ($length.length) {{
                $length.hide();
            }}
            if ($('#hubPageSize').length) {{
                $('#hubPageSize').val(api.page.len());
                $('#hubPageSize').on('change', function() {{
                    var len = parseInt($(this).val(), 10);
                    api.page.len(len).draw();
                }});
                $('#hubPageSize').select2({{
                    theme: 'bootstrap-5',
                    width: 'auto',
                    dropdownAutoWidth: true,
                    minimumResultsForSearch: Infinity,
                    selectionCssClass: 'hub-select2-selection',
                    dropdownCssClass: 'hub-select2-dropdown'
                }});
            }}
            /* 隐藏自带的空行与重复搜索行，让表格紧凑无缝贴合工具栏 */
            $filter.closest('.row').hide();
            $info.css({{ 'padding-top': '0.6rem', 'clear': 'both' }});
            $paginate.css({{ 'padding-top': '0.3rem', 'text-align': 'center' }});

            /* ★ 动态注入：全局搜索靶向选择器（仅精准注入到直接的搜索输入框 label，绝不重复污染 length 的 label） */
            var $searchLabel = $filter.children('label');
            if ($('#searchScope').length === 0) {{
                var scopeSelect = '<select id="searchScope" class="form-select form-select-sm d-inline-block w-auto me-2 select2-glass-single" data-placeholder="穿透搜索">' +
                                  '<option value="all">🔍 穿透搜索 (全部内容)</option>' +
                                  '<option value="title">📘 仅搜整合包名称</option>' +
                                  '<option value="cat">🏷️ 仅搜分类与标签</option>' +
                                  '<option value="desc">📖 仅搜百科长篇介绍</option>' +
                                  '<option value="comment">💬 仅搜评论与讨论区</option>' +
                                  '</select>';
                $searchLabel.prepend(scopeSelect);
                $('#searchScope').select2({{
                    theme: 'bootstrap-5',
                    width: '210px',
                    minimumResultsForSearch: Infinity,
                    selectionCssClass: 'select2-glass-selection',
                    dropdownCssClass: 'select2-glass-dropdown search-scope-dropdown'
                }});
            }}
            if ($('#searchNav').length === 0) {{
                var $searchNav = $('<span class="search-nav" id="searchNav" style="display:none;"><span class="search-nav-info" id="searchNavInfo">0 / 0</span><button type="button" class="search-nav-btn" id="searchPrev" title="上一个搜索结果">‹</button><button type="button" class="search-nav-btn" id="searchNext" title="下一个搜索结果">›</button><button type="button" class="search-nav-btn" id="searchOpen" title="打开命中的介绍或评论">⌖</button></span>');
                $searchLabel.append($searchNav);
            }}
            var searchHits = [];
            var searchHitIndex = -1;
            var rawCellHtml = new WeakMap();
            function restoreSearchHighlights() {{
                $wrapper.find('tbody td').each(function() {{
                    var raw = rawCellHtml.get(this);
                    if (raw !== undefined) {{
                        this.innerHTML = raw;
                    }}
                }});
                $wrapper.find('tbody tr').removeClass('search-hit-row search-current-row');
            }}
            function highlightCell($td, keyword) {{
                if (!$td.length || !keyword) return;
                var node = $td[0];
                if (!rawCellHtml.has(node)) rawCellHtml.set(node, node.innerHTML);
                var rawText = $td.text();
                if (!textHasKeyword(rawText, keyword)) return;
                node.innerHTML = highlightText(rawText, keyword);
            }}
            function updateSearchNav() {{
                var keyword = normalizeSearchKeyword();
                var scope = $('#searchScope').val() || 'all';
                restoreSearchHighlights();
                searchHits = [];
                searchHitIndex = -1;
                if (!keyword) {{
                    $('#searchNav').hide();
                    return;
                }}
                table.rows({{ search: 'applied' }}).every(function() {{
                    var rowIdx = this.index();
                    var rowData = window.tableRowsData ? window.tableRowsData[rowIdx] : null;
                    if (!rowData) return;
                    var match = matchRowSearchFast(this.data(), rowData, keyword, scope);
                    if (!rowMatchesScope(match, scope)) return;
                    searchHits.push({{ index: rowIdx, match: match }});
                    var tr = this.node();
                    if (!tr) return; // 延迟渲染下，未绘制到可视区域的行无需也不可操作 DOM
                    if (!rowMatchesScope(match, scope)) return;
                    var $tr = $(tr);
                    var hitType = match.title ? 'title' : match.cat ? 'cat' : match.desc ? 'desc' : match.comment ? 'comment' : 'basic';
                    if (scope === 'desc') hitType = 'desc';
                    if (scope === 'comment') hitType = 'comment';
                    if (scope === 'cat') hitType = 'cat';
                    if (scope === 'title') hitType = 'title';
                    $tr.addClass('search-hit-row');
                    if (hitType === 'title' || hitType === 'basic') highlightCell($tr.children('td').eq(0), keyword);
                    if (hitType === 'cat' || hitType === 'basic') {{
                        highlightCell($tr.children('td').eq(5), keyword);
                        highlightCell($tr.children('td').eq(6), keyword);
                        if ($tr.children('td').eq(6).text().toLowerCase().indexOf(keyword.toLowerCase()) !== -1) {{
                            $tr.find('.mod-details').prop('open', true);
                        }}
                    }}
                    searchHits.push({{ tr: tr, type: hitType, commentIndex: match.commentIndex }});
                }});
                if (searchHits.length > 0) searchHitIndex = 0;
                $('#searchNav').show();
                refreshSearchNavState(false);
            }}
            function refreshSearchNavState(scrollToRow) {{
                var total = searchHits.length;
                $('#searchNavInfo').text(total ? ((searchHitIndex + 1) + ' / ' + total) : '0 / 0');
                $('#searchPrev, #searchNext, #searchOpen').prop('disabled', total === 0);
                $wrapper.find('tbody tr').removeClass('search-current-row');
                if (!total) return;
                var hit = searchHits[searchHitIndex];
                var $tr = $(hit.tr).addClass('search-current-row');
                if (scrollToRow && $tr.length) {{
                    var body = $wrapper.find('.dataTables_scrollBody')[0];
                    if (body) {{
                        body.scrollTop = Math.max(0, hit.tr.offsetTop - 72);
                    }} else {{
                        hit.tr.scrollIntoView({{ block: 'center', behavior: 'smooth' }});
                    }}
                }}
            }}
            function jumpSearch(delta) {{
                if (!searchHits.length) return;
                searchHitIndex = (searchHitIndex + delta + searchHits.length) % searchHits.length;
                refreshSearchNavState(true);
            }}
            function openSearchHit() {{
                if (!searchHits.length) return;
                refreshSearchNavState(true);
                var hit = searchHits[searchHitIndex];
                var $tr = $(hit.tr);
                if (hit.type === 'comment') {{
                    showCommentPopup($tr.children('td.td-comment'));
                }} else {{
                    showDescPopup($tr.find('a.modpack-link'));
                }}
            }}
            $('#searchScope').on('change', function() {{ table.draw(); }});
            $('#searchPrev').on('click', function() {{ jumpSearch(-1); }});
            $('#searchNext').on('click', function() {{ jumpSearch(1); }});
            $('#searchOpen').on('click', function() {{ openSearchHit(); }});
            /* ★ 强力拦截：解除 DataTables 原生绑定的搜索框事件，防止原生过滤机制对无单元格内容的评论进行误杀 */
            var $filterInput = $filter.find('input');
            $filterInput.off('keyup.DT search.DT input.DT paste.DT cut.DT');
            var searchTimer = null;
            $filterInput.on('keyup input', function() {{
                clearTimeout(searchTimer);
                searchTimer = setTimeout(function() {{
                    table.draw();
                }}, 100);
            }});
            /* ★ [v10.0] 顶部数据栏跟随横向滚动 */
            var $scrollBody = $wrapper.find('.dataTables_scrollBody');
            var $scrollHead = $wrapper.find('.dataTables_scrollHead');
            var $sortStrip = $('<div class="sort-strip"><div class="sort-strip-inner"></div></div>');
            $scrollHead.append($sortStrip);
            var $sortStripInner = $sortStrip.find('.sort-strip-inner');
            $scrollBody.on('scroll', function() {{
                $scrollHead.scrollLeft($(this).scrollLeft());
                $sortStrip.scrollLeft($(this).scrollLeft());
            }});
            $scrollHead.find('th').off('.DT');
            function rebuildSortStrip() {{
                var html = '';
                var maxRight = 0;
                var $headTable = $wrapper.find('.dataTables_scrollHead table').first();
                $wrapper.find('.dataTables_scrollHead thead tr:first th').each(function(idx) {{
                    var left = Math.round(this.offsetLeft || 0);
                    var w = Math.ceil(this.getBoundingClientRect().width || $(this).outerWidth());
                    if (w < 1) return;
                    html += '<button type="button" class="sort-strip-seg" data-col="' + idx + '" title="' + $(this).text().trim() + '" style="left:' + left + 'px;width:' + w + 'px"></button>';
                    maxRight = Math.max(maxRight, left + w);
                }});
                var tableW = Math.ceil($headTable.outerWidth() || maxRight);
                $sortStripInner.css('width', Math.max(maxRight, tableW) + 'px').html(html);
            }}
            function refreshActiveSortColumn() {{
                var order = api.order();
                var colIdx = order && order.length ? order[0][0] : 2;
                var dir = order && order.length ? order[0][1] : 'desc';
                $wrapper.find('th, td').removeClass('dt-active-sort');
                $wrapper.find('.dataTables_scrollHead th').eq(colIdx).addClass('dt-active-sort').attr('data-order-dir', dir);
                $sortStrip.find('.sort-strip-seg').removeClass('active').attr('data-order-dir', '');
                $sortStrip.find('.sort-strip-seg[data-col="' + colIdx + '"]').addClass('active').attr('data-order-dir', dir);
                $wrapper.find('.dataTables_scrollBody tbody tr').each(function() {{
                    $(this).children('td').eq(colIdx).addClass('dt-active-sort');
                }});
            }}
            function sortByColumn(colIdx) {{
                if (colIdx < 0 || colIdx > 6) return;
                var current = api.order();
                var currentIdx = current && current.length ? current[0][0] : -1;
                var currentDir = current && current.length ? current[0][1] : 'desc';
                var nextDir = (currentIdx === colIdx && currentDir === 'asc') ? 'desc' : 'asc';
                api.order([colIdx, nextDir]).draw();
                refreshActiveSortColumn();
            }}
            $wrapper.on('click', '.sort-option', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                var $opt = $(this);
                var $switcher = $opt.closest('.header-sort-switcher');
                var colIdx = parseInt($switcher.attr('data-col'));
                if ($opt.hasClass('active')) {{
                    sortByColumn(colIdx);
                    return;
                }}
                $switcher.find('.sort-option').removeClass('active');
                $opt.addClass('active');
                var subKey = $opt.attr('data-subkey');
                var sortProp = 'sort_col' + colIdx;
                (window.tableRowsData || []).forEach(function(r) {{
                    var raw = r[subKey + '_n'] !== undefined ? r[subKey + '_n'] : (r[subKey] !== undefined ? r[subKey] : 0);
                    r[sortProp] = (subKey === 'name' || typeof raw === 'string') ? (raw || '') : (parseFloat(raw) || 0);
                }});
                api.rows().invalidate('data');
                var order = api.order();
                var currentIdx = order && order.length ? order[0][0] : -1;
                var currentDir = order && order.length ? order[0][1] : 'desc';
                if (currentIdx === colIdx) {{
                    api.order([colIdx, currentDir]).draw();
                }} else {{
                    api.order([colIdx, 'desc']).draw();
                }}
            }});
            $wrapper.on('click', '.dataTables_scrollHead th', function(e) {{
                var colIdx = $(this).index();
                e.preventDefault();
                e.stopImmediatePropagation();
                sortByColumn(colIdx);
            }});
            $sortStrip.on('click', '.sort-strip-seg', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                sortByColumn(Number($(this).data('col')));
            }});
            rebuildSortStrip();
            refreshActiveSortColumn();
            updateSearchNav();
            api.on('order.dt draw.dt column-sizing.dt', function() {{
                rebuildSortStrip();
                refreshActiveSortColumn();
                updateSearchNav();
            }});
            function renderModSections(groups) {{
                var html = '';
                groups.forEach(function(group) {{
                    var name = group.n || '未分类';
                    var head = group.u ? '<a class="mod-category-link" href="' + escHtml(group.u, true) + '" target="_blank">' + escHtml(name, true) + '</a>' : '<span>' + escHtml(name, true) + '</span>';
                    html += '<section class="mod-category-section" data-mod-cat-key="' + escHtml(group.k || '', true) + '"><div class="mod-category-head">' + head + '<span>' + (group.m || []).length + '</span></div><div class="mod-grid">';
                    (group.m || []).forEach(function(mod) {{
                        var modName = mod[0] || '';
                        if (!modName) return;
                        var version = mod[1] || '';
                        var url = mod[2] || '#';
                        var title = mod[3] || modName;
                        var hint = title + (version ? ' · 版本: ' + version : '') + ' · 分类: ' + name;
                        html += '<span class="tag-mod" role="button" tabindex="0" title="' + escHtml(hint, true) + '" data-mod="' + escHtml(modName, true) + '" data-mod-cat="' + escHtml(name, true) + '" data-mod-url="' + escHtml(url, true) + '"><span class="tag-mod-name">' + escHtml(modName, true) + '</span>' + (version ? '<span class="tag-mod-version">' + escHtml(version, true) + '</span>' : '') + '<a class="tag-mod-open" href="' + escHtml(url, true) + '" target="_blank" title="打开 MC百科模组页">↗</a></span>';
                    }});
                    html += '</div></section>';
                }});
                return html;
            }}
            function loadFullModList($details) {{
                var $full = $details.find('.mod-full-list');
                if (!$full.length || $full.attr('data-loaded') === '1' || $full.attr('data-loading') === '1') return;
                var mid = $details.closest('tr').attr('data-mid') || '';
                var groups = (window.modDetailData && window.modDetailData[mid]) || [];
                function doRender(gList) {{
                    $full.removeAttr('data-loading').attr('data-loaded', '1');
                    $details.find('.mod-details-body > .mod-category-section, .mod-details-body > .tag-empty').remove();
                    if (!gList || !gList.length) {{
                        var fallbackData = (window.compareData && window.compareData[mid]) || {{}};
                        var fallbackMods = fallbackData.mods || [];
                        if (fallbackMods.length) {{
                            gList = [{{
                                n: '全部收录模组',
                                k: 'cat0',
                                u: '',
                                m: fallbackMods.map(function(m) {{
                                    var mn = typeof m === 'string' ? m : (m.name || m.title || '');
                                    return [mn, '', 'https://www.mcmod.cn/s?key=' + encodeURIComponent(mn), mn];
                                }})
                            }}];
                        }}
                    }}
                    if (gList && gList.length) {{
                        $full.html(renderModSections(gList));
                    }} else {{
                        $full.html('<div class="tag-empty">暂无更多模组明细数据</div>');
                    }}
                }}
                if (groups.length) {{
                    doRender(groups);
                    return;
                }}
                $full.attr('data-loading', '1').html('<div class="tag-empty">正在读取完整模组列表…</div>');
                loadModDetailData(mid).then(function(loadedGroups) {{
                    var finalGroups = (loadedGroups && loadedGroups.length) ? loadedGroups : ((window.modDetailData && window.modDetailData[mid]) || []);
                    doRender(finalGroups);
                }}).catch(function() {{
                    doRender([]);
                }});
            }}
            $wrapper.on('click', '.mod-summary-chip', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                var $chip = $(this);
            var key = $chip.data('mod-cat-key');
            var $details = $chip.closest('.mod-details');
            if (!$details.prop('open')) {{
                $details.prop('open', true);
            }}
            loadFullModList($details);
            setTimeout(function() {{
                var $target = $details.find('.mod-category-section[data-mod-cat-key="' + key + '"]');
                if (!$target.length) return;
                var $scrollBox = $details.find('.mod-details-body');
                var currentTop = $scrollBox.scrollTop();
                var targetTop = $target.position().top + currentTop - 6;
                $scrollBox.stop(true).animate({{ scrollTop: Math.max(0, targetTop) }}, 220);
                    $target.removeClass('jump-focus');
                    void $target[0].offsetWidth;
                    $target.addClass('jump-focus');
                    api.columns.adjust();
                    rebuildSortStrip();
                    refreshActiveSortColumn();
                }}, 40);
            }});
            $wrapper.on('click', '.mod-details-body, .mod-category-section, .mod-grid', function(e) {{
                if ($(e.target).closest('.tag-mod, .tag-mod-open, .mod-category-head, .mod-category-link, a, button').length) return;
                var $details = $(this).closest('.mod-details');
                if ($details.length && $details.prop('open')) {{
                    $details.prop('open', false);
                    api.columns.adjust();
                    rebuildSortStrip();
                    refreshActiveSortColumn();
                }}
            }});
            $wrapper.on('click', '.mod-details > summary', function() {{
                var current = $(this).closest('.mod-details')[0];
                setTimeout(function() {{
                    if (current && current.open) {{
                        $wrapper.find('.mod-details[open]').each(function() {{
                            if (this !== current) this.open = false;
                        }});
                        // 某些浏览器不让 <details> 的 toggle 事件冒泡；这里直接补载完整名单。
                        loadFullModList($(current));
                        api.columns.adjust();
                        rebuildSortStrip();
                        refreshActiveSortColumn();
                    }}
                }}, 0);
            }});
            $wrapper.on('toggle', '.mod-details', function() {{
                if (this.open) {{
                    var current = this;
                    $wrapper.find('.mod-details[open]').each(function() {{
                        if (this !== current) this.open = false;
                    }});
                    loadFullModList($(this));
                }}
                setTimeout(function() {{
                    api.columns.adjust();
                    rebuildSortStrip();
                    refreshActiveSortColumn();
                }}, 30);
            }});
            $wrapper.on('wheel', '.mod-container, .mod-details-body', function(e) {{
                var el = this;
                if (!el || el.scrollHeight <= el.clientHeight) return;
                var oe = e.originalEvent;
                var delta = oe.deltaY || 0;
                var atTop = el.scrollTop <= 0;
                var atBottom = Math.ceil(el.scrollTop + el.clientHeight) >= el.scrollHeight;
                if ((delta < 0 && atTop) || (delta > 0 && atBottom)) return;
                e.stopPropagation();
            }});
            function toggleMultiSelect(selector, val) {{
                var $sel = $(selector);
                var current = $sel.val() || [];
                if (!Array.isArray(current)) current = current ? [current] : [];
                var idx = current.indexOf(val);
                if (idx >= 0) {{
                    current.splice(idx, 1);
                    $sel.find('option').filter(function() {{ return $(this).val() === val; }}).remove();
                }} else {{
                    if ($sel.find('option').filter(function() {{ return $(this).val() === val; }}).length === 0) {{
                        $sel.append($('<option>', {{ value: val, text: val, selected: true }}));
                    }}
                    current.push(val);
                }}
                $sel.val(current).trigger('change');
            }}
            /* ★ [v10.0] 点击单元格内标签筛选/取消 */
            $wrapper.on('click', '.tag-cat', function(e) {{
                if ($(e.target).closest('.tag-filter-open').length) return;
                e.preventDefault();
                e.stopPropagation();
                var val = ($(this).attr('data-tag') || $(this).find('.tag-filter-name').text() || $(this).text()).trim();
                toggleMultiSelect('#categoryFilter', val);
            }});
            $wrapper.on('click', '.tag-pack', function(e) {{
                if ($(e.target).closest('.tag-filter-open').length) return;
                e.preventDefault();
                e.stopPropagation();
                var val = ($(this).attr('data-tag') || $(this).find('.tag-filter-name').text() || $(this).text()).trim();
                toggleMultiSelect('#packTagFilter', val);
            }});
            $wrapper.on('click', '.tag-filter-open', function(e) {{
                e.stopPropagation();
            }});
            $wrapper.on('click keydown', '.tag-mod', function(e) {{
                if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') return;
                if ($(e.target).closest('.tag-mod-open').length) return;
                e.preventDefault();
                e.stopPropagation();
                var val = ($(this).attr('data-mod') || $(this).find('.tag-mod-name').text() || $(this).text()).trim();
                if (val) toggleMultiSelect('#modFilter', val);
            }});
            $wrapper.on('click', '.tag-mod-open', function(e) {{
                e.stopPropagation();
            }});
            // 初始化完成后，延迟微调一下列宽，保证表头对齐
            setTimeout(function() {{
                api.columns.adjust();
                rebuildSortStrip();
                refreshActiveSortColumn();
            }}, 100);
        }}
    }});
    }};
/* ══════════════ 1. DataTables 自定义多条件过滤器 ══════════════ */
    $.fn.dataTable.ext.search.push(
        function(settings, data, dataIndex) {{
            var selectedCat   = $('#categoryFilter').val();
            var selectedPack  = $('#packTagFilter').val();
            var selectedModCat = $('#modCategoryFilter').val();
            var selectedMod = $('#modFilter').val();
            var selectedTrend = $('#trendFilter').val();
            var selectedType = $('#typeFilter').val();
            var excludeCat = $('#categoryExclude').is(':checked');
            var excludePack = $('#packTagExclude').is(':checked');
            var excludeModCat = $('#modCategoryExclude').is(':checked');
            var excludeMod = $('#modExclude').is(':checked');
            function asArray(v) {{
                if (!v) return [];
                return Array.isArray(v) ? v : [v];
            }}
            function hasAll(rowText, selected) {{
                selected = asArray(selected);
                if (!selected.length) return true;
                rowText = String(rowText || '').toLowerCase();
                for (var i = 0; i < selected.length; i++) {{
                    if (rowText.indexOf(String(selected[i]).toLowerCase()) === -1) return false;
                }}
                return true;
            }}
            function passFilter(rowText, selected, exclude) {{
                selected = asArray(selected);
                if (!selected.length) return true;
                var matched = hasAll(rowText, selected);
                return exclude ? !matched : matched;
            }}
            // 分类和标签筛选（内存化高速检索，无需查询 DOM）
            var rowData = (window.tableRowsData && window.tableRowsData[dataIndex]);
            if (!rowData) return true;
            var rowType = rowData.type_name || '';
            var rowCat  = rowData.cat_search || '';
            var rowPack = rowData.pack_search || '';
            var rowMid = rowData.mid || '';
            var rowModData = (window.compareData && window.compareData[rowMid]) || {{}};
            var rowModCategories = (rowModData.mod_categories || []).join(' ');
            var rowModNames = (rowModData.mods || []).map(function(m) {{ return typeof m === 'string' ? m : (m.name || ''); }}).join(' ');
            if (selectedType && rowType !== selectedType) return false;
            if (!passFilter(rowCat, selectedCat, excludeCat)) return false;
            if (!passFilter(rowPack, selectedPack, excludePack)) return false;
            if (!passFilter(rowModCategories, selectedModCat, excludeModCat)) return false;
            if (!passFilter(rowModNames, selectedMod, excludeMod)) return false;
            var trendDays = rowData.days_n || 0;
            if (isNaN(trendDays)) trendDays = 0; // 安全防御
            if (selectedTrend) {{
                if (selectedTrend === "7_in") {{
                    if (trendDays > 7) return false;      // 7天内：0~7天显示，大于7的隐藏
                }} else if (selectedTrend === "7-14") {{
                    if (trendDays < 8 || trendDays > 14) return false;  // 7-14天：实际抓取 8~14天
                }} else if (selectedTrend === "14-30") {{
                    if (trendDays < 15 || trendDays > 30) return false; // 14-30天：实际抓取 15~30天
                }} else if (selectedTrend === "30_in") {{
                    if (trendDays > 30) return false;     // 30天内：大集合！0~30天都显示，大于30的隐藏
                }} else if (selectedTrend === "30-59") {{
                    if (trendDays < 31 || trendDays > 59) return false; // 30-59天：实际抓取 31~59天
                }} else if (selectedTrend === "60") {{
                    if (trendDays < 60) return false;   // 至少60天：本地长期历史超过60天也保留
                }}
            }}
            return true;
        }}
    );
    $('#typeFilter, #categoryFilter, #packTagFilter, #modCategoryFilter, #modFilter, #trendFilter, #categoryExclude, #packTagExclude, #modCategoryExclude, #modExclude').on('change', function() {{
        if (table) table.draw();
    }});
    // 表格重绘时，同步更新顶部的总条数统计及画廊卡片
    $('#modpackTable').on('draw.dt', function() {{
        var tbl = window.table;
        if (!tbl && $.fn.DataTable && $.fn.DataTable.isDataTable('#modpackTable')) {{
            tbl = $('#modpackTable').DataTable();
        }}
        var info = tbl ? tbl.page.info() : {{ recordsDisplay: (window.tableRowsData ? window.tableRowsData.length : 1484) }};
        $('#statTotal').text(info.recordsDisplay);
        $('#mcmodMatchedCount').text(info.recordsDisplay);
        $('#mcmodCardCountBadge').text(info.recordsDisplay + ' 款');
        if (activeMcmodVMode === 'cards') {{
            renderMcmodCards();
        }}
        /* ★ [v10.0] 高亮当前被激活筛选的标签 */
        var $wrap = $('#modpackTable_wrapper');
        $wrap.find('.tag-cat, .tag-pack, .tag-mod').removeClass('active-tag exclude-active-tag');
        var activeCat = $('#categoryFilter').val() || [];
        if (!Array.isArray(activeCat)) activeCat = activeCat ? [activeCat] : [];
        if (activeCat.length) {{
            $wrap.find('.tag-cat').filter(function() {{ return activeCat.indexOf(($(this).attr('data-tag') || '').trim()) >= 0; }}).addClass($('#categoryExclude').is(':checked') ? 'exclude-active-tag' : 'active-tag');
        }}
        var activePack = $('#packTagFilter').val() || [];
        if (!Array.isArray(activePack)) activePack = activePack ? [activePack] : [];
        if (activePack.length) {{
            $wrap.find('.tag-pack').filter(function() {{ return activePack.indexOf(($(this).attr('data-tag') || '').trim()) >= 0; }}).addClass($('#packTagExclude').is(':checked') ? 'exclude-active-tag' : 'active-tag');
        }}
        var activeMod = $('#modFilter').val() || [];
        if (!Array.isArray(activeMod)) activeMod = activeMod ? [activeMod] : [];
        if (activeMod.length) {{
            $wrap.find('.tag-mod').filter(function() {{ return activeMod.indexOf(($(this).attr('data-mod') || '').trim()) >= 0; }}).addClass($('#modExclude').is(':checked') ? 'exclude-active-tag' : 'active-tag');
        }}
    }});
    // 一键重置所有筛选条件
    $('#resetFilters').on('click', function() {{
        $('#categoryFilter').val(null).trigger('change');
        $('#typeFilter').val('').trigger('change');
        $('#packTagFilter').val(null).trigger('change');
        $('#modCategoryFilter').val(null).trigger('change');
        $('#modFilter').val(null).trigger('change');
        $('#categoryExclude, #packTagExclude, #modCategoryExclude, #modExclude').prop('checked', false);
        $('#trendFilter').val('').trigger('change');
        $('#mcmodUnifiedSearch').val('');
        $('#mcmodSearchClear').hide();
        currentMcmodCardLimit = 48;
        if (table) table.search('').draw();
        renderMcmodCards();
        renderSidebarTags('mcmod');
    }});

    // ★ 首屏极速初始化：定义完成后立即检查，如果数据就绪且为表格模式，立即构建表格！
    if (window.tableRowsData && window.tableRowsData.length) {{
        if (!$.fn.DataTable.isDataTable('#modpackTable') && activeMcmodVMode === 'table') {{
            window.initMcmodTable();
        }}
    }}
    /* ═══════ 整合包介绍预览 ═══════ */
    var descData = window.descData || {{}};
    var feedbackUrl = "https://feedback.suifracti.cn/";
    // 评论详情拆为同目录按需脚本，避免 Windows 首次打开时解析全部评论。
    var commentData = {{}};
    var commentLoadJobs = {{}};
    var commentApiBase = "__COMMENT_API_BASE__";
    var compareData = window.compareData || {{}};
    var modDetailData = {{}};
    var modDetailLoadJobs = {{}};
    window.compareData = compareData;
    window.modDetailData = modDetailData;
    window.__registerModDetailData = function(mid, payload) {{ modDetailData[String(mid)] = payload || []; }};
    function loadModDetailData(mid) {{
        if (modDetailData[mid]) return Promise.resolve(modDetailData[mid]);
        if (modDetailLoadJobs[mid]) return modDetailLoadJobs[mid];
        modDetailLoadJobs[mid] = new Promise(function(resolve) {{
            var script = document.createElement('script');
            script.src = 'data/mods/' + encodeURIComponent(mid) + '.js';
            script.onload = function() {{ resolve(modDetailData[mid] || []); script.remove(); }};
            script.onerror = function() {{ resolve([]); script.remove(); }};
            document.head.appendChild(script);
        }}).finally(function() {{ delete modDetailLoadJobs[mid]; }});
        return modDetailLoadJobs[mid];
    }}
    var $popup = $('#pvPopup');
    var $pvTitle = $('#pvTitle');
    var $pvBody = $('#pvBody');
    var $pvOpen = $('#pvOpen');
    var $cpopup = $('#commentPopup');
    var $cBody = $('#commentBody');
    var $cCount = $('#commentCount');
    var $commentOpen = $('#commentOpen');
    var hoverTimer = null;
    var commentHoverTimer = null;
    var HOVER_DELAY = 600;
    var HOVER_COOLDOWN_MS = 5000;
    var hoverCooldowns = {{}};
    var descHoverPopupEnabled = localStorage.getItem('desc-hover-popup-enabled') !== '0';
    var commentHoverPopupEnabled = localStorage.getItem('comment-hover-popup-enabled') === '1';
    var activeDescKey = '';
    var activeCommentKey = '';
    var activeTrendKey = '';
    $('#compareTray, #compareOverlay').appendTo(document.body);
    var favoriteKey = 'mcmod-compare-favorites-v1';
    var favoriteIds = [];
    try {{
        favoriteIds = JSON.parse(localStorage.getItem(favoriteKey) || '[]').filter(function(mid) {{ return compareData[mid]; }});
    }} catch(e) {{
        favoriteIds = [];
    }}
    function saveFavorites() {{
        favoriteIds = favoriteIds.filter(function(mid, idx, arr) {{ return compareData[mid] && arr.indexOf(mid) === idx; }});
        localStorage.setItem(favoriteKey, JSON.stringify(favoriteIds));
    }}
    function compactTitle(item) {{
        return (item && (item.title_cn || item.title || item.mid)) || '';
    }}
    function updateFavoriteStars() {{
        $('.fav-star').each(function() {{
            var mid = String($(this).data('mid') || '');
            $(this).toggleClass('active', favoriteIds.indexOf(mid) >= 0)
                   .attr('title', favoriteIds.indexOf(mid) >= 0 ? '已收藏，点击取消' : '收藏用于对比');
        }});
    }}
    function updateCompareTray() {{
        saveFavorites();
        updateFavoriteStars();
        var selected = favoriteIds.map(function(mid) {{ return compareData[mid]; }}).filter(Boolean);
        $('#compareTrayCount').text(selected.length + ' 个整合包');
        $('#compareTrayNames').html(selected.slice(0, 8).map(function(item) {{
            return '<span class="compare-mini-chip">' + escHtml(compactTitle(item), true) + '</span>';
        }}).join('') + (selected.length > 8 ? '<span class="compare-mini-chip">+' + (selected.length - 8) + '</span>' : ''));
        $('#compareTray').toggleClass('show', selected.length > 0);
        $('#compareOpen').prop('disabled', selected.length < 2).attr('title', selected.length < 2 ? '至少收藏 2 个整合包才能对比' : '打开全面对比');
    }}
    function numFmt(n) {{
        n = Number(n || 0);
        if (n >= 100000000) return (n / 100000000).toFixed(1).replace(/\\.0$/, '') + '亿';
        if (n >= 10000) return (n / 10000).toFixed(1).replace(/\\.0$/, '') + '万';
        return String(n);
    }}
    function listNames(arr, limit) {{
        arr = arr || [];
        if (!arr.length) return '<span class="compare-chip">无</span>';
        return arr.slice(0, limit || 80).map(function(x) {{
            var name = typeof x === 'string' ? x : x.name;
            return '<span class="compare-chip">' + escHtml(name || '', true) + '</span>';
        }}).join('') + (arr.length > (limit || 80) ? '<span class="compare-chip">+' + (arr.length - (limit || 80)) + '</span>' : '');
    }}
    function setIntersection(listOfSets) {{
        if (!listOfSets.length) return [];
        var base = Array.from(listOfSets[0]);
        return base.filter(function(x) {{ return listOfSets.every(function(s) {{ return s.has(x); }}); }}).sort();
    }}
    function setUnion(listOfSets) {{
        var out = new Set();
        listOfSets.forEach(function(s) {{ s.forEach(function(x) {{ out.add(x); }}); }});
        return Array.from(out).sort();
    }}
    function renderCompare() {{
        var selected = favoriteIds.map(function(mid) {{ return compareData[mid]; }}).filter(Boolean);
        if (selected.length < 2) return;
        var modSets = selected.map(function(item) {{ return new Set((item.mods || []).map(function(m) {{ return (typeof m === 'string' ? m : (m.name || '')).toLowerCase(); }})); }});
        var modNameMap = {{}};
        selected.forEach(function(item) {{
            (item.mods || []).forEach(function(m) {{ var name = typeof m === 'string' ? m : (m.name || ''); modNameMap[name.toLowerCase()] = name; }});
        }});
        var commonMods = setIntersection(modSets).map(function(k) {{ return modNameMap[k] || k; }});
        var allMods = setUnion(modSets);
        var tagSets = selected.map(function(item) {{ return new Set([].concat(item.categories || [], item.tags || [])); }});
        var commonTags = setIntersection(tagSets);
        var typeLine = selected.map(function(item) {{ return item.type || '未标明'; }});
        var html = '';
        html += '<div class="compare-grid">';
        selected.forEach(function(item) {{
            html += '<div class="compare-card">';
            html += '<h3>' + escHtml(compactTitle(item), true) + '</h3>';
            html += '<div class="compare-metric"><span>类型</span><b>' + escHtml(item.type || '未标明', true) + '</b></div>';
            html += '<div class="compare-metric"><span>官方流行</span><b>' + numFmt(item.score) + '</b></div>';
            html += '<div class="compare-metric"><span>浏览</span><b>' + numFmt(item.views) + '</b></div>';
            html += '<div class="compare-metric"><span>模组</span><b>' + numFmt((item.mods || []).length) + '</b></div>';
            html += '<div class="compare-metric"><span>评论</span><b>' + numFmt(item.comments) + '</b></div>';
            html += '<div class="compare-metric"><span>推荐/收藏</span><b>' + numFmt(item.recommend) + ' / ' + numFmt(item.favorite) + '</b></div>';
            html += '<div class="compare-metric"><span>7/30/60日</span><b>' + escHtml([item.growth7, item.growth30, item.growth60].join(' / '), true) + '</b></div>';
            html += '</div>';
        }});
        html += '</div>';
        html += '<div class="compare-section"><h3>共有模组 · ' + commonMods.length + '</h3><div class="compare-chip-cloud">' + listNames(commonMods, 120) + '</div></div>';
        html += '<div class="compare-section"><h3>共有分类/标签 · ' + commonTags.length + '</h3><div class="compare-chip-cloud">' + listNames(commonTags, 120) + '</div></div>';
        html += '<div class="compare-section"><h3>各包独有模组</h3><div class="compare-columns">';
        selected.forEach(function(item, idx) {{
            var unique = (item.mods || []).filter(function(m) {{
                var key = (typeof m === 'string' ? m : (m.name || '')).toLowerCase();
                return modSets.filter(function(s) {{ return s.has(key); }}).length === 1;
            }}).map(function(m) {{ return typeof m === 'string' ? m : m.name; }});
            html += '<div class="compare-card"><h3>' + escHtml(compactTitle(item), true) + ' · ' + unique.length + '</h3><div class="compare-chip-cloud">' + listNames(unique, 120) + '</div></div>';
        }});
        html += '</div></div>';
        html += '<div class="compare-section"><h3>模组差异矩阵 · ' + allMods.length + '</h3><div class="compare-table-wrap"><table class="compare-table"><thead><tr><th>模组</th>';
        selected.forEach(function(item) {{ html += '<th>' + escHtml(compactTitle(item), true) + '</th>'; }});
        html += '</tr></thead><tbody>';
        allMods.forEach(function(key) {{
            html += '<tr><td>' + escHtml(modNameMap[key] || key, true) + '</td>';
            modSets.forEach(function(s) {{ html += s.has(key) ? '<td class="compare-hit">●</td>' : '<td class="compare-miss">○</td>'; }});
            html += '</tr>';
        }});
        html += '</tbody></table></div></div>';
        html += '<div class="compare-section"><h3>分类/标签差异矩阵</h3><div class="compare-table-wrap"><table class="compare-table"><thead><tr><th>分类/标签</th>';
        selected.forEach(function(item) {{ html += '<th>' + escHtml(compactTitle(item), true) + '</th>'; }});
        html += '</tr></thead><tbody>';
        setUnion(tagSets).forEach(function(tag) {{
            html += '<tr><td>' + escHtml(tag, true) + '</td>';
            tagSets.forEach(function(s) {{ html += s.has(tag) ? '<td class="compare-hit">●</td>' : '<td class="compare-miss">○</td>'; }});
            html += '</tr>';
        }});
        html += '</tbody></table></div></div>';
        $('#compareBody').html(html);
        $('#compareOverlay').addClass('show').attr('aria-hidden', 'false');
    }}
    $(document).off('click.compareFav').on('click.compareFav', '.fav-star', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        var mid = String($(this).data('mid') || '');
        if (!compareData[mid]) return;
        var idx = favoriteIds.indexOf(mid);
        if (idx >= 0) favoriteIds.splice(idx, 1);
        else favoriteIds.push(mid);
        updateCompareTray();
    }});
    $('#modpackTable').on('draw.dt', updateFavoriteStars);
    $('#compareClear').on('click', function() {{ favoriteIds = []; updateCompareTray(); }});
    $('#compareOpen').on('click', renderCompare);
    $('#compareClose, #compareOverlay').on('click', function(e) {{
        if (e.target === this) $('#compareOverlay').removeClass('show').attr('aria-hidden', 'true');
    }});
    $('#compareCopy').on('click', function() {{
        var selected = favoriteIds.map(function(mid) {{ return compareData[mid]; }}).filter(Boolean);
        var text = selected.map(function(item) {{
            return compactTitle(item) + ' | 模组 ' + (item.mods || []).length + ' | 流行 ' + item.score + ' | 浏览 ' + item.views;
        }}).join('\\n');
        if (navigator.clipboard) navigator.clipboard.writeText(text);
    }});
    updateCompareTray();
    function isHoverCooling(key) {{
        return key && hoverCooldowns[key] && hoverCooldowns[key] > Date.now();
    }}
    function setHoverCooldown(key) {{
        if (key) hoverCooldowns[key] = Date.now() + HOVER_COOLDOWN_MS;
    }}
    function getCommentUrl(url) {{
        var clean = (url || 'https://www.mcmod.cn/').split('#')[0];
        return clean;
    }}
    function escAttrJs(str) {{
        return escHtml(str || '', true).replace(/<br>/g, '&#10;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }}
    function getSingleCommentUrl(c) {{
        if (c && (c.comment_url || c.url || c.href || c.link)) {{
            return c.comment_url || c.url || c.href || c.link;
        }}
        return '';
    }}
    function commentOriginMeta(c, localIndex) {{
        return '';
    }}
    function getDescText(desc) {{
        if (!desc) return '';
        if (typeof desc === 'string') return desc;
        return desc.text || desc.desc || '';
    }}
    function getDescImages(desc) {{
        if (!desc || typeof desc === 'string') return [];
        if (Array.isArray(desc.images) && desc.images.length) return desc.images;
        if (Array.isArray(desc.intro_images) && desc.intro_images.length) return desc.intro_images;
        return [];
    }}
    function normalizeImageUrlJs(url) {{
        if (!url) return '';
        try {{ return new URL(url, window.location.href).href; }} catch(e) {{
            if (String(url).indexOf('//') === 0) return 'https:' + url;
            return String(url);
        }}
    }}
    function isAvatarImage(img) {{
        if (img && String(img.kind || '').toLowerCase() === 'avatar') return true;
        var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
        var url = normalizeImageUrlJs(raw).toLowerCase();
        return url.indexOf('/user/avatar/') >= 0 || url.indexOf('/identicons/') >= 0 || url.indexOf('@60x60') >= 0;
    }}
    function isEmotionImage(img) {{
        if (img && String(img.kind || '').toLowerCase() === 'emotion') return true;
        var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
        var url = normalizeImageUrlJs(raw).toLowerCase();
        return url.indexOf('/emotion/images/') >= 0 || url.indexOf('/dialogs/emotion/') >= 0;
    }}
    function filterGalleryImages(images) {{
        if (!Array.isArray(images)) return [];
        return images.filter(function(img) {{ return !isAvatarImage(img) && !isEmotionImage(img); }});
    }}
    function filterEmotionImages(images) {{
        if (!Array.isArray(images)) return [];
        return images.filter(function(img) {{ return isEmotionImage(img); }});
    }}
    function renderInlineEmotions(images) {{
        var emos = filterEmotionImages(images);
        if (!emos.length) return '';
        var html = '<span class="inline-emotions">';
        emos.forEach(function(img, idx) {{
            var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
            var url = normalizeImageUrlJs(raw);
            if (!url) return;
            html += '<img class="inline-emotion" src="' + escAttrJs(url) + '" alt="表情" loading="lazy">';
        }});
        html += '</span>';
        return html;
    }}
    function renderImageGallery(images, extraClass) {{
        images = filterGalleryImages(images);
        if (!Array.isArray(images) || !images.length) return '';
        var html = '<div class="image-gallery ' + (extraClass || '') + '">';
        images.forEach(function(img, idx) {{
            var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
            var url = normalizeImageUrlJs(raw);
            if (!url || /loading|loadfail/i.test(url)) return;
            var alt = (typeof img === 'string') ? '' : (img.alt || img.title || '');
            var caption = alt || ('图片 ' + (idx + 1));
            html += '<a class="image-thumb" href="' + escAttrJs(url) + '" target="_blank" rel="noreferrer" title="' + escAttrJs(caption) + '">';
            html += '<img src="' + escAttrJs(url) + '" alt="' + escAttrJs(caption) + '" loading="lazy">';
            html += '<span class="image-caption">' + escHtml(caption, true) + '</span></a>';
        }});
        html += '</div>';
        return html;
    }}
    function splitIntroImages(images) {{
        var cover = [];
        var rest = [];
        (images || []).forEach(function(img) {{
            var source = (img && img.source ? String(img.source).toLowerCase() : '');
            if (source === 'cover') cover.push(img);
            else rest.push(img);
        }});
        return {{ cover: cover, rest: rest }};
    }}
    function sectionKeyFromText(text) {{
        var s = String(text || '').replace(/\\s+/g, '');
        if (!s) return '';
        if (s.indexOf('任务截图') >= 0 || s.indexOf('游戏截图') >= 0 || s.indexOf('截图') >= 0 || s.indexOf('图片') >= 0) return 'screenshots';
        if (s.indexOf('使用') >= 0) return 'usage';
        if (s.indexOf('介绍') >= 0 || s.indexOf('简介') >= 0) return 'intro';
        return '';
    }}
    function imageSectionKey(img) {{
        var s = ((img && (img.section || img.heading || img.alt || img.title)) || '').replace(/\\s+/g, '');
        return sectionKeyFromText(s);
    }}
    function renderDescHtml(desc, images, keyword) {{
        var splitImages = splitIntroImages(images || []);
        var textHtml = '';
        if (desc) {{
            if (keyword && desc.toLowerCase().indexOf(keyword.toLowerCase()) !== -1) {{
                textHtml = '<div class="pv-para">' + highlightText(desc, keyword) + '</div>';
            }} else {{
                // 介绍正文需要段落排版，这里要的是排版器而非纯转义
                textHtml = formatDescHtml(desc);
            }}
        }}
        var coverHtml = splitImages.cover.length ? '<div class="pv-cover-wrap">' + renderImageGallery(splitImages.cover, 'pv-cover-gallery') + '</div>' : '';
        var rest = splitImages.rest;
        if (!rest.length) return coverHtml + textHtml;

        var used = new Set();
        var $box = $('<div>' + textHtml + '</div>');
        $box.children().each(function() {{
            var key = sectionKeyFromText($(this).text());
            if (!key) return;
            var group = rest.filter(function(img, idx) {{
                return !used.has(idx) && (imageSectionKey(img) === key || (!imageSectionKey(img) && key === 'screenshots'));
            }});
            if (group.length) {{
                group.forEach(function(img) {{ used.add(rest.indexOf(img)); }});
                $(this).after(renderImageGallery(group, 'pv-image-gallery section-bound'));
            }}
        }});
        var leftovers = rest.filter(function(img, idx) {{ return !used.has(idx); }});
        return coverHtml + $box.html() + renderImageGallery(leftovers, 'pv-image-gallery');
    }}
    $(document).on('click', '.mcmod-consent-ok', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        $(this).closest('.pv-popup, .comment-popup').removeClass('needs-consent');
    }});
    function openImageLightbox(url, title) {{
        url = normalizeImageUrlJs(url);
        if (!url) return;
        $('#imageLightboxImg').attr('src', url).attr('alt', title || '');
        $('#imageLightboxTitle').text(title || '图片预览');
        $('#imageLightboxOpen').attr('href', url);
        $('#imageLightbox').addClass('show').attr('aria-hidden', 'false');
    }}
    function closeImageLightbox() {{
        $('#imageLightbox').removeClass('show').attr('aria-hidden', 'true');
        $('#imageLightboxImg').attr('src', '');
    }}
    var coverHoverPreviewTimer = null;
    $(document).on('mouseenter', '.modpack-cover-thumb', function() {{
        var $thumb = $(this);
        clearTimeout(coverHoverPreviewTimer);
        coverHoverPreviewTimer = setTimeout(function() {{
            openImageLightbox($thumb.data('image-url') || $thumb.attr('href'), $thumb.attr('title') || '封面预览');
        }}, 1000);
    }});
    $(document).on('mouseleave', '.modpack-cover-thumb', function() {{
        clearTimeout(coverHoverPreviewTimer);
        coverHoverPreviewTimer = null;
    }});
    $(document).on('click', '.image-thumb', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        clearTimeout(coverHoverPreviewTimer);
        openImageLightbox($(this).attr('href') || $(this).data('image-url'), $(this).attr('title') || $(this).find('.image-caption').text());
    }});
    $('#imageLightboxClose, #imageLightbox').on('click', function(e) {{
        if (e.target === this) closeImageLightbox();
    }});
    function showDescPopup($link) {{
        var url = $link.attr('href') || '#';
        var title = $link.data('full-title') || $link.text();
        var mid = $link.data('mid') || '';
        var plat = $link.data('platform') || (mid ? 'mcmod' : '');
        var customDesc = $link.data('desc') || '';
        var customCover = $link.data('cover') || '';
        activeDescKey = 'desc:' + (mid || url || title);
        if (isHoverCooling(activeDescKey)) return;
        
        var platBadge = plat ? ('[' + (plat === 'bilibili' ? '📺 B站自制' : (plat === 'bbsmc' ? '💎 BBSMC' : (plat === 'xyebbs' ? '🍃 XYEBBS' : (plat === 'modrinth' ? '🌐 Modrinth' : (plat === 'curseforge' ? '🔥 CurseForge' : '📦 MC百科'))))) + '] ') : '';
        $pvTitle.text(platBadge + title);
        $pvOpen.attr('href', url);

        var descObj = descData[mid];
        var desc = customDesc || getDescText(descObj);
        var descImages = customCover ? [customCover] : getDescImages(descObj);

        if (desc || descImages.length) {{
            var keyword = (typeof getActiveSearchQuery === 'function') ? getActiveSearchQuery() : '';
            $pvBody.html(renderDescHtml(desc, descImages, keyword));
        }} else {{
            $pvBody.html('<div class="pv-body-empty">暂无更多图文介绍<div><a href="' + url + '" target="_blank" rel="noreferrer">在新标签页中安全访问原页面 ↗</a></div></div>');
        }}
        $popup.addClass('show').attr('aria-hidden', 'false');
        var rect = $link[0].getBoundingClientRect();
        var linkH = $link.outerHeight();
        var pw = $popup.outerWidth();
        var ph = $popup.outerHeight();
        var vw = window.innerWidth;
        var vh = window.innerHeight;
        // 默认显示在链接上方
        var top = rect.top - ph - 14;
        var left = rect.left;
        // 上方空间不够 → 显示在下方
        if (top < 12) top = rect.bottom + 14;
        // 如果下方也不够，则从顶部开始
        if (top + ph > vh - 12) top = Math.max(12, Math.min(vh - ph - 12, 12));
        // 水平方向 clamp
        if (left + pw > vw - 12) left = vw - pw - 12;
        if (left < 12) left = 12;
        $popup.css({{ top: top, left: left }});
    }}
    function hideDescPopup() {{
        $popup.removeClass('show').attr('aria-hidden', 'true');
    }}
    function escapeRegExp(str) {{
        if (!str) return "";
        // 1. 先把反斜杠转义（必须最先执行）
        str = str.split('\\\\').join('\\\\\\\\');
        // 2. 逐个将其他正则敏感元字符转义
        var specials = ['/', '^', '$', '*', '+', '?', '.', '(', ')', '|', '[', ']', '{{', '}}', '-'];
        for (var i = 0; i < specials.length; i++) {{
            var c = specials[i];
            str = str.split(c).join('\\\\' + c);
        }}
        return str;
    }}
    function highlightText(str, keyword) {{
        var escaped = escHtml(str, true);
        if (!keyword) return escaped;
        var cleanKeyword = keyword.trim();
        if (!cleanKeyword) return escaped;
        var escapedKeyword = escHtml(cleanKeyword, true);
        if (!escapedKeyword) return escaped;
        try {{
            var regex = new RegExp('(' + escapeRegExp(escapedKeyword) + ')', 'gi');
            return escaped.replace(regex, '<mark class="comment-highlight">$1</mark>');
        }} catch(e) {{
            return escaped;
        }}
    }}
    /* 这个函数实际是「介绍正文排版器」：把纯文本按行重组，并套上
       <div class="pv-para"> / <blockquote> / pv-section-title 等块级标签，供介绍抽屉使用。
       它原先也叫 escHtml，与前面那个纯转义函数同名 —— JS 里同名函数后声明者覆盖前者，
       于是全页所有"以为在转义"的调用实际都在插 HTML：用在 title="..." 这类属性位置时
       引号会被内层标签冲断，整行 HTML 被当文本吐到页面上。
       现改为独立命名，只有真正需要段落排版的介绍渲染才调用它。 */
    function formatDescHtml(str, noFormat) {{
    if (str === null || str === undefined) return "";
    var d = document.createElement('div');
        d.textContent = str;
        var raw = d.innerHTML;
        var LF = String.fromCharCode(10);
        var CR = String.fromCharCode(13);
        var text = raw.split(CR + LF).join(LF).split(CR).join(LF);
        if (noFormat) {{
            return text.split(LF).join('<br>');
        }}
        var lines = text.split(LF);
        var html = '';
        var currentPara = [];
        var currentQuote = [];
        function flushPara() {{
            if (currentPara.length > 0) {{
                html += '<div class="pv-para">' + currentPara.join('<br>') + '</div>';
                currentPara = [];
            }}
        }}
        function flushQuote() {{
            if (currentQuote.length > 0) {{
                html += '<blockquote class="intro-blockquote">' + currentQuote.join('<br>') + '</blockquote>';
                currentQuote = [];
            }}
        }}
        for (var i = 0; i < lines.length; i++) {{
            var line = lines[i].trim();
            if (!line) {{
                flushPara();
                flushQuote();
                continue;
            }}
            var firstChar = line.charAt(0);
            var isQuote = firstChar === '|' || firstChar === '>';
            if (isQuote) {{
                flushPara();
                var quoteContent = line.substring(1).trim();
                currentQuote.push(quoteContent);
                continue;
            }} else {{
                flushQuote();
            }}
            var isList = false;
            var listContent = line;
            if (firstChar === '-' || firstChar === '*' || firstChar === '•' || /^\\d+\\.\\s/.test(line)) {{
                isList = true;
                listContent = line.replace(/^[-*•\\s]+|^\\d+\\.\\s+/, '');
            }} else {{
                var colonMatch = line.match(/^([^，。！、；：:]{{2,15}})[：:]/);
                if (colonMatch) {{
                    isList = true;
                    listContent = '<strong>' + colonMatch[1] + ': </strong>' + line.substring(colonMatch[0].length).trim();
                }}
            }}
            var isTitle = false;
            if (!isList) {{
                var isShort = line.length <= 25;
                var hasPunctuation = /[，。！、；]/.test(line);
                var lastChar = line.slice(-1);
                if ((isShort && !hasPunctuation && !lastChar.match(/[。！；]/)) || lastChar === ':' || lastChar === '：' || line.indexOf('——') >= 0) {{
                    isTitle = true;
                }}
            }}
            if (isList) {{
                flushPara();
                html += '<div class="pv-list-item">' + listContent + '</div>';
            }} else if (isTitle) {{
                flushPara();
                html += '<div class="pv-section-title">' + line + '</div>';
            }} else {{
                currentPara.push(line);
            }}
        }}
        flushPara();
        flushQuote();
        return html || text.split(LF).join('<br>');
    }}
    var cmtPerPage = 8;
    var cmtCurrentPage = 1;
    var cmtTotalPages = 1;
    var cmtCurrentData = null;
    var cmtTargetIndex = -1;
    var activeCommentCell = null;
    var cmtSearchMatches = [];
    var cmtSearchMatchPointer = -1;
    function renderCommentPage(page) {{
        if (!cmtCurrentData || !cmtCurrentData.comments) return;
        var comments = cmtCurrentData.comments;
        cmtTotalPages = Math.max(1, Math.ceil(comments.length / cmtPerPage));
        if (page < 1) page = 1;
        if (page > cmtTotalPages) page = cmtTotalPages;
        cmtCurrentPage = page;
        var keyword = $('#commentSearchInput').val().trim();
        var start = (page - 1) * cmtPerPage;
        var end = Math.min(start + cmtPerPage, comments.length);
        var html = '';
        for (var i = start; i < end; i++) {{
            var c = comments[i];
            var isActiveMatch = (cmtSearchMatchPointer >= 0 && i === cmtSearchMatches[cmtSearchMatchPointer]);
            html += '<div class="comment-floor' + (isActiveMatch ? ' matched-active' : '') + '" data-comment-index="' + i + '">';
            html += '<div class="comment-floor-head">';
            html += '<div class="comment-floor-main">';
            if (c.floor) {{
                html += '<span class="floor-num">第 ' + c.floor + ' 楼</span> ';
            }}
            var originMeta = commentOriginMeta(c, i);
            html += highlightText(c.author || '', keyword) + (originMeta ? '<span class="comment-origin-meta">' + originMeta + '</span>' : '') + '</div>';
            html += '</div>';
            html += '<div class="comment-floor-text">' + highlightText(c.text || '', keyword) + renderInlineEmotions(c.images || []) + '</div>';
            html += renderImageGallery(c.images || [], 'comment-image-gallery');
            if (c.replies && c.replies.length > 0) {{
                c.replies.forEach(function(r) {{
                    html += '<div class="comment-reply">';
                    html += '<div class="comment-reply-head"><span>' + highlightText(r.author || '', keyword) + '</span>';
                    html += '</div>';
                    html += '<div class="comment-reply-text">' + highlightText(r.text || '', keyword) + renderInlineEmotions(r.images || []) + '</div>';
                    html += renderImageGallery(r.images || [], 'comment-image-gallery');
                    html += '</div>';
                }});
            }}
            html += '</div>';
        }}
        $cBody.html(html);
        $cBody.scrollTop(0); // 确保翻页后滚动条滑回最上方，极大地改善了翻页可读性
        if (cmtTargetIndex >= start && cmtTargetIndex < end) {{
            setTimeout(function() {{
                var target = $cBody.find('[data-comment-index="' + cmtTargetIndex + '"]')[0];
                if (target) $cBody.scrollTop(Math.max(0, target.offsetTop - 14));
                cmtTargetIndex = -1;
            }}, 30);
        }}
        // 更新分页栏
        var $bar = $('#commentPageBar');
        var $info = $('#cmtPageInfo');
        var $first = $('#cmtFirst');
        var $prev = $('#cmtPrev');
        var $next = $('#cmtNext');
        var $last = $('#cmtLast');
        if (cmtTotalPages > 1) {{
            $bar.show();
            $info.text('第 ' + page + ' / ' + cmtTotalPages + ' 页');
            $first.removeClass('disabled').addClass(page <= 1 ? 'disabled' : '');
            $prev.removeClass('disabled').addClass(page <= 1 ? 'disabled' : '');
            $next.removeClass('disabled').addClass(page >= cmtTotalPages ? 'disabled' : '');
            $last.removeClass('disabled').addClass(page >= cmtTotalPages ? 'disabled' : '');
        }} else {{
            $bar.hide();
        }}
        repositionCommentPopup();
    }}
    /* ─── 智能高度监测系统工具方法 ─── */
    // 【1. 统一变量绑定的高度测算方法】
    function checkCommentOverflow() {{
        // 使用 setTimeout 延迟 25 毫秒，确保 DOM 节点完全重绘重排完毕，拿取绝对真实高度
        setTimeout(function() {{
            if ($cBody[0]) {{
                // 🌟 引入 8 像素溢出容差缓冲区，彻底规避小数像素四舍五入和滚动边距带来的误差
                var hasScroll = $cBody[0].scrollHeight > ($cBody.innerHeight() + 8);
                if (hasScroll) {{
                    $cpopup.addClass('has-overflow'); // 激活“滚动查看更多”胶囊
                }} else {{
                    $cpopup.removeClass('has-overflow');
                }}
            }}
        }}, 25);
    }}
    // 【2. 修正：直接绑定到局部容器，并支持滑回顶部时恢复提示】
    $('#commentBody').on('scroll', function() {{
        var scrollTop = $(this).scrollTop();
        if (scrollTop > 15) {{
            // 向下滑动超过 15px，说明用户已经发现并开始阅读，优雅隐藏提示
            $cpopup.removeClass('has-overflow');
        }} else if (scrollTop <= 5) {{
            // 如果用户又滑回了最顶部，且内容依然是超长的，把提示重新亮起来引导
            if (this.scrollHeight > $(this).innerHeight()) {{
                $cpopup.addClass('has-overflow');
            }}
        }}
    }});
    // 【3. 翻页控制】：点击各翻页按钮后安全触发重新判定
    $('#cmtFirst').on('click', function(e) {{
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage > 1) {{
            renderCommentPage(1);
            checkCommentOverflow();
        }}
    }});
    $('#cmtPrev').on('click', function(e) {{
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage > 1) {{
            renderCommentPage(cmtCurrentPage - 1);
            checkCommentOverflow();
        }}
    }});
    $('#cmtNext').on('click', function(e) {{
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage < cmtTotalPages) {{
            renderCommentPage(cmtCurrentPage + 1);
            checkCommentOverflow();
        }}
    }});
    $('#cmtLast').on('click', function(e) {{
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage < cmtTotalPages) {{
            renderCommentPage(cmtTotalPages);
            checkCommentOverflow();
        }}
    }});
    // 搜索匹配项跳转控制
    $(document).on('click', '#searchNavNext', function(e) {{
        e.stopPropagation();
        if (!cmtSearchMatches || cmtSearchMatches.length === 0) return;
        cmtSearchMatchPointer = (cmtSearchMatchPointer + 1) % cmtSearchMatches.length;
        var targetIndex = cmtSearchMatches[cmtSearchMatchPointer];
        var targetPage = Math.floor(targetIndex / cmtPerPage) + 1;
        cmtTargetIndex = targetIndex;
        $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 ' + (cmtSearchMatchPointer + 1) + ' 条)');
        renderCommentPage(targetPage);
        checkCommentOverflow();
    }});
    $(document).on('click', '#searchNavPrev', function(e) {{
        e.stopPropagation();
        if (!cmtSearchMatches || cmtSearchMatches.length === 0) return;
        cmtSearchMatchPointer = (cmtSearchMatchPointer - 1 + cmtSearchMatches.length) % cmtSearchMatches.length;
        var targetIndex = cmtSearchMatches[cmtSearchMatchPointer];
        var targetPage = Math.floor(targetIndex / cmtPerPage) + 1;
        cmtTargetIndex = targetIndex;
        $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 ' + (cmtSearchMatchPointer + 1) + ' 条)');
        renderCommentPage(targetPage);
        checkCommentOverflow();
    }});
    function repositionCommentPopup() {{
        if (!$cpopup.hasClass('show') || !activeCommentCell) return;
        var rect = activeCommentCell[0].getBoundingClientRect();
        var cellW = activeCommentCell.outerWidth();
        var vw = window.innerWidth;
        var vh = window.innerHeight;
        var safeTop = 24;
        var safeBottom = 24;
        var fixedHeight = Math.min(720, Math.max(420, vh - safeTop - safeBottom));
        $cpopup.css({{
            height: fixedHeight + 'px',
            'max-height': fixedHeight + 'px'
        }});
        $cBody.css('max-height', 'none');
        var ph = fixedHeight;
        var top = rect.top - ph - 10;
        // 如果上方放不下，则尝试放在下方
        if (top < safeTop) {{
            top = rect.bottom + 10;
        }}
        // 如果下方穿出了浏览器底部，则向上推起，将底部固定在 vh - safeBottom 位置，顶部向上延伸
        if (top + ph > vh - safeBottom) {{
            top = Math.max(safeTop, vh - safeBottom - ph);
        }}
        var pw = $cpopup.outerWidth();
        var left = rect.left + cellW / 2 - pw / 2;
        // 水平 clamp 锁定
        if (left + pw > vw - 12) left = vw - pw - 12;
        if (left < 12) left = 12;
        $cpopup.css({{
            top: top + 'px',
            bottom: 'auto',
            left: left
        }});
    }}
    function lockCommentPopupSize() {{
        var vh = window.innerHeight;
        var fixedHeight = Math.min(720, Math.max(420, vh - 48));
        $cpopup.css({{ height: fixedHeight + 'px', 'max-height': fixedHeight + 'px' }});
        $cBody.css('max-height', 'none');
    }}
    function isCommentHoverAlive() {{
        var overPopup = $cpopup.is(':hover');
        var overCell = activeCommentCell && activeCommentCell.length && activeCommentCell.is(':hover');
        return !!(overPopup || overCell);
    }}
    function scheduleCommentHide(delay) {{
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            if (isCommentHoverAlive()) return;
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, delay || 120);
    }}
    // 【4. 弹窗主渲染逻辑】：渲染完数据并全部定位成功后，激活检测
    function commentSearchMatches(comments, keyword) {{
        var matches = [];
        keyword = String(keyword || '').trim().toLowerCase();
        if (!keyword || !comments) return matches;
        for (var i = 0; i < comments.length; i++) {{
            var c = comments[i] || {{}};
            var match = String(c.author || '').toLowerCase().indexOf(keyword) !== -1 ||
                        String(c.text || '').toLowerCase().indexOf(keyword) !== -1;
            (c.replies || []).forEach(function(r) {{
                if (String(r.author || '').toLowerCase().indexOf(keyword) !== -1 ||
                    String(r.text || '').toLowerCase().indexOf(keyword) !== -1) match = true;
            }});
            if (match) matches.push(i);
        }}
        return matches;
    }}
    function applyCommentSearch() {{
        if (!cmtCurrentData || !cmtCurrentData.comments) return;
        cmtSearchMatches = commentSearchMatches(cmtCurrentData.comments, $('#commentSearchInput').val());
        cmtSearchMatchPointer = cmtSearchMatches.length ? 0 : -1;
        cmtTargetIndex = cmtSearchMatches.length ? cmtSearchMatches[0] : -1;
        if (cmtSearchMatches.length) {{
            $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 1 条)');
            $('#commentSearchNav').show();
            renderCommentPage(Math.floor(cmtTargetIndex / cmtPerPage) + 1);
        }} else {{
            $('#commentSearchNav').hide();
            renderCommentPage(1);
        }}
        checkCommentOverflow();
    }}
    $('#commentSearchInput').on('input', function() {{ applyCommentSearch(); }});
    window.__registerCommentData = function(mid, payload) {{ commentData[String(mid)] = payload || {{ comments: [] }}; }};
    function loadCommentData(mid) {{
        if (commentData[mid]) return Promise.resolve(commentData[mid]);
        if (commentLoadJobs[mid]) return commentLoadJobs[mid];
        commentLoadJobs[mid] = new Promise(function(resolve) {{
            var script = document.createElement('script');
            script.src = 'data/comments/' + encodeURIComponent(mid) + '.js';
            script.onload = function() {{ resolve(commentData[mid] || null); script.remove(); }};
            script.onerror = function() {{ console.warn('评论数据加载失败:', mid); resolve(null); script.remove(); }};
            document.head.appendChild(script);
        }}).finally(function() {{ delete commentLoadJobs[mid]; }});
        return commentLoadJobs[mid];
    }}
    function showCommentPopup($cell) {{
        var mid = String($cell.data('mid') || '');
        activeCommentCell = $cell;
        activeCommentKey = 'comment:' + mid;
        if (isHoverCooling(activeCommentKey)) return;
        if (commentData[mid]) {{
            renderCommentPopup($cell, commentData[mid]);
            return;
        }}
        var trLink = $cell.closest('tr').find('a.modpack-link').attr('href');
        var url = trLink || (mid ? ('https://www.mcmod.cn/modpack/' + mid + '.html') : 'https://www.mcmod.cn/');
        var commentUrl = getCommentUrl(url);
        $('#commentModpackLink').attr('href', commentUrl);
        $commentOpen.attr('href', commentUrl);
        $('#commentSearchInput').val('').prop('disabled', true);
        $('#commentSearchNav, #commentPageBar').hide();
        $cCount.text('正在加载评论…');
        $cBody.html('<div class="comment-empty-hint">正在按需读取这一个整合包的评论…</div>');
        $cpopup.addClass('show');
        lockCommentPopupSize();
        repositionCommentPopup();
        loadCommentData(mid).then(function(cdata) {{
            if (!activeCommentCell || !activeCommentCell.is($cell)) return;
            renderCommentPopup($cell, cdata);
        }});
    }}
    function renderCommentPopup($cell, cdata) {{
        activeCommentCell = $cell;
        var mid = $cell.data('mid') || '';
        activeCommentKey = 'comment:' + mid;
        if (isHoverCooling(activeCommentKey)) return;
        var floorCount = $cell.data('order') || 0;
        var pageCount = (cdata && cdata.page_count) ? cdata.page_count : floorCount;
        // 重置样式，以进行正确的初始测量
        $cpopup.css({{
            height: '',
            'min-height': '',
            'max-height': '',
            top: '',
            bottom: '',
            left: ''
        }});
        lockCommentPopupSize();
        if (cdata && cdata.comments && cdata.comments.length > 0) {{
            var scrapedFloors = cdata.comments.length;
            // 诱饵数据清洗与非逆向计算：直接正向统计回复数
            var scrapedReplies = 0;
            cdata.comments.forEach(function(c) {{
                if (c.replies) scrapedReplies += c.replies.length;
            }});
            pageCount = Math.max(pageCount, scrapedFloors + scrapedReplies);
            var totalLabel = '共 ' + pageCount + ' 条 · 主楼 ' + scrapedFloors + ' · 楼中楼 ' + scrapedReplies;
            $cCount.text(totalLabel);
            cmtCurrentData = cdata;
            $('#commentSearchInput').prop('disabled', false);
            /* 评论搜索只针对当前打开的评论，不再借用整合包总搜索框。 */
            var startPage = 1;
            var keyword = $('#commentSearchInput').val().trim().toLowerCase();
            var trLink = $cell.closest('tr').find('a.modpack-link').attr('href');
            var url = trLink || (mid ? ('https://www.mcmod.cn/modpack/' + mid + '.html') : 'https://www.mcmod.cn/');
            var commentUrl = getCommentUrl(url);
            $('#commentModpackLink').attr('href', commentUrl);
            $commentOpen.attr('href', commentUrl);
            
            cmtSearchMatches = commentSearchMatches(cdata.comments, keyword);
            cmtSearchMatchPointer = -1;
            if (cmtSearchMatches.length > 0) {{
                cmtSearchMatchPointer = 0;
                var targetIndex = cmtSearchMatches[0];
                startPage = Math.floor(targetIndex / cmtPerPage) + 1;
                cmtTargetIndex = targetIndex;
            }}
            
            if (cmtSearchMatches.length > 1) {{
                $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 1 条)');
                $('#commentSearchNav').show();
            }} else {{
                $('#commentSearchNav').hide();
            }}
            
            renderCommentPage(startPage);
        }} else {{
            var trLink = $cell.closest('tr').find('a.modpack-link').attr('href');
            var url = trLink || (mid ? ('https://www.mcmod.cn/modpack/' + mid + '.html') : 'https://www.mcmod.cn/');
            var commentUrl = getCommentUrl(url);
            $('#commentModpackLink').attr('href', commentUrl);
            $commentOpen.attr('href', commentUrl);
            $('#commentSearchNav').hide();
            $('#commentSearchInput').prop('disabled', true);
            $cCount.text('共 ' + (pageCount || 0) + ' 条社区讨论');
            var portalHtml = '<div class="comment-portal-card">' +
                '<div class="comment-portal-icon">💬</div>' +
                '<div class="comment-portal-title">MC百科 玩家讨论区</div>' +
                '<div class="comment-portal-meta">' +
                    '<span>累计评论: <b>' + (pageCount || 0) + '</b> 条</span> · ' +
                    '<span>来源: <b>mcmod.cn</b></span>' +
                '</div>' +
                '<p class="comment-portal-desc">本整合包在 MC百科 拥有 <b>' + (pageCount || 0) + '</b> 条社区玩家评价、提问与交流讨论。为保障获取完整楼中楼层级与最新互动，推荐直接前往原帖查阅：</p>' +
                '<div class="comment-portal-actions">' +
                    '<a href="' + commentUrl + '" target="_blank" rel="noreferrer" class="btn-comment-portal-primary">🚀 一键直达 MC百科 原帖评论区 ↗</a>' +
                    '<button type="button" class="btn-comment-portal-sec js-embed-comment-preview" data-url="' + commentUrl + '">📜 在看板内嵌入浏览评论区</button>' +
                '</div>' +
                '<div id="commentEmbedContainer" style="display:none; margin-top:14px; width:100%; height:440px; border-radius:10px; overflow:hidden; border:1px solid var(--glass-border);">' +
                    '<iframe id="commentEmbedIframe" src="about:blank" style="width:100%; height:100%; border:0;"></iframe>' +
                '</div>' +
            '</div>';
            $cBody.html(portalHtml);
            $('#commentPageBar').hide();
        }}
        $cpopup.addClass('show');
        repositionCommentPopup();
        // ✨ 完美的咬合节点：弹窗加载和精准坐标偏置完成后，立刻调取判定
        checkCommentOverflow();
    }}
    function hideCommentPopup() {{
        function clearCommentPopupLayout() {{
            $cpopup.css({{
                height: '',
                'min-height': '',
                'max-height': '',
                top: '',
                bottom: '',
                left: ''
            }});
            $cBody.css('max-height', '');
        }}
        if ($cpopup.hasClass('show')) {{
            $cpopup.addClass('hiding').removeClass('show');
            setTimeout(function() {{
                $cpopup.removeClass('hiding');
                clearCommentPopupLayout();
            }}, 180);
        }} else {{
            $cpopup.removeClass('show hiding');
            clearCommentPopupLayout();
        }}
        activeCommentCell = null;
        cmtSearchMatches = [];
        cmtSearchMatchPointer = -1;
    }}

    // ───── MCMod 版本更新日志模态窗交互 ─────
    var $vModal = $('#versionModalOverlay');
    var $vTitle = $('#versionModalTitle');
    var $vVer = $('#versionModalVer');
    var $vDate = $('#versionModalDate');
    var $vCount = $('#versionModalCount');
    var $vExtLink = $('#versionModalExtLink');
    var $vBodyInner = $('#versionModalBodyInner');

    /* 大数字可读化：各平台的下载量/播放量动辄百万级，直接打印 2297419 很难扫读。
       沿用看板其它位置的 万 / 亿 口径，小数值仍走千分位。 */
    function fmtBigNum(n) {{
        if (n === null || n === undefined || n === '') return '';
        var v = Number(n);
        if (!isFinite(v)) return String(n);
        if (v >= 100000000) return (v / 100000000).toFixed(2).replace(/\\.?0+$/, '') + '亿';
        if (v >= 10000) return (v / 10000).toFixed(1).replace(/\\.0$/, '') + '万';
        return v.toLocaleString('zh-CN');
    }}

    /* MC 版本支持分布条：把 all_versions 按「大版本族」(1.21 / 1.20 / …) 聚合，
       用条长表达该族下收录了多少个具体版本。
       纯数据呈现 —— 版本全部来自抓取结果，不补全、不推断。
       少于 2 个版本时返回空串（单个版本用条形表达没有信息量）。 */
    function buildMcVersionStrip(versions) {{
        if (!versions || !versions.length) return '';
        var uniq = [];
        versions.forEach(function(v) {{
            v = String(v == null ? '' : v).trim();
            if (v && uniq.indexOf(v) === -1) uniq.push(v);
        }});
        if (uniq.length < 2) return '';
        var fam = {{}}, order = [];
        uniq.forEach(function(v) {{
            var m = v.match(/^(\\d+\\.\\d+)/);
            var key = m ? m[1] : '其它';
            if (!fam[key]) {{ fam[key] = []; order.push(key); }}
            fam[key].push(v);
        }});
        order.sort(function(a, b) {{
            var pa = a.split('.'), pb = b.split('.');
            return (parseInt(pb[0], 10) || 0) - (parseInt(pa[0], 10) || 0)
                || (parseInt(pb[1], 10) || 0) - (parseInt(pa[1], 10) || 0);
        }});
        var maxN = 1;
        order.forEach(function(k) {{ maxN = Math.max(maxN, fam[k].length); }});
        var rows = order.map(function(k) {{
            var n = fam[k].length;
            var pct = Math.max(6, Math.round(n / maxN * 100));
            return '<div class="mcver-row" title="' + escHtml(fam[k].join(', '), true) + '">' +
                '<span class="mcver-fam">' + escHtml(k) + '</span>' +
                '<span class="mcver-track"><span class="mcver-fill" style="width:' + pct + '%;"></span></span>' +
                '<span class="mcver-n">' + n + ' 个</span>' +
            '</div>';
        }}).join('');
        return '<div class="mcver-strip">' +
            '<div class="mcver-head">🎮 Minecraft 版本支持分布' +
                '<span class="mcver-sub">共 ' + uniq.length + ' 个具体版本 · 按大版本族聚合 · 悬停可看明细</span>' +
            '</div>' + rows + '</div>';
    }}

    function openVersionModal(mid, title, ver, date, count, row, extra) {{
        extra = extra || {{}};
        var plat = extra.platform || (mid ? 'mcmod' : 'bilibili');
        if (!mid && !title && !extra.title) return;

        if (!row && mid && window.tableRowsData) {{
            for (var i = 0; i < window.tableRowsData.length; i++) {{
                if (String(window.tableRowsData[i].mid) === String(mid)) {{
                    row = window.tableRowsData[i];
                    break;
                }}
            }}
        }}

        title = title || extra.title || (row && row.title) || ('整合包 #' + mid);
        ver = ver || extra.ver || (row && row.latest_version) || '通用 / 最新';
        date = date || extra.date || (row && row.last_update_date) || '暂无记录';
        var relDate = extra.date_created || (row && row.release_date) || date || '暂无记录';
        count = count || extra.count || (row && row.version_count) || (extra.items ? extra.items.length : 1);
        // 各平台可用字段不同：没有的字段一律不编造，改用下面这组可选覆盖项改写卡片标签，
        // 让非 MCMod 平台也能复用同一个弹窗（例如把「最新发布版本」改成「最新支持版本」）。
        var mcVers = extra.mcVers || extra.ver || ((row && row.mc_versions && row.mc_versions.length) ? row.mc_versions.join(', ') : ((row && row.mc_version) || '通用 / 未指定'));
        // 版本列表（数组形态）：用于下方的「版本支持分布」可视化。
        // 只取数据里真实存在的版本，不做任何推断补全。
        var mcVersList = extra.mcVersList || (row && row.mc_versions) || [];
        if ((!mcVersList || !mcVersList.length) && extra.mcVersListRaw) mcVersList = extra.mcVersListRaw;
        var mcStrip = buildMcVersionStrip(mcVersList);
        // modCount 只在数据里真的有「模组数量」时才显示；没有就留空，绝不编造。
        var modCount = extra.modCount || ((row && row.mod_count) ? (row.mod_count + ' 款') : '');
        var typeName = extra.typeName || (row && row.type_name) || '优质模组包';
        var targetUrl = extra.url || ('https://www.mcmod.cn/modpack/version/' + mid + '.html');
        var lblVer    = extra.verLabel   || '🏷️ 最新发布版本';
        var lblCount  = extra.countLabel || '📦 累计历史版本数';
        var lblType   = extra.typeLabel  || '🧩 整合包类型与模组量';
        var countUnit = extra.countUnit  || ' 个版本';

        var platName = plat === 'bilibili' ? '哔哩哔哩自制' :
                       (plat === 'bbsmc' ? 'BBSMC开放资源' :
                       (plat === 'xyebbs' ? 'XYEBBS社区' :
                       (plat === 'modrinth' ? 'Modrinth国际服' :
                       (plat === 'curseforge' ? 'CurseForge全球服' : 'MC百科权威'))));
        // 提示语里的站点名与按钮文案同样按平台参数化，不再写死 MC百科。
        var siteShort = plat === 'bilibili' ? '哔哩哔哩' :
                        (plat === 'bbsmc' ? 'BBSMC' :
                        (plat === 'xyebbs' ? 'XYEBBS' :
                        (plat === 'modrinth' ? 'Modrinth' :
                        (plat === 'curseforge' ? 'CurseForge' : 'MC百科'))));
        var noticeText = extra.notice || ('为保障您的本地数据浏览安全，防止 ' + siteShort + ' 原站防爬拦截误封您的 IP（以及规避原网页防内嵌劫持脚本导致整个看板跳转），本弹窗已直接利用本地聚合数据库为您秒级呈现版本元信息。如需查阅官方历史每一个微小版本的详细改动日志，可点击下方按钮在新独立标签页中安全访问。');
        var btnLabel   = extra.btnLabel || ('在新标签页打开 ' + siteShort + ' 官方页面 ↗');

        $vTitle.text(title + ' · ' + platName);
        $vVer.text((extra.verTagLabel || '最新版本') + ': ' + ver);
        $vDate.text('更新时间: ' + date);
        $vCount.text((extra.countTagLabel || '累计发布') + ': ' + (count ? fmtBigNum(count) : 1) + (extra.countTagUnit || ' 个版本'));
        $vExtLink.attr('href', targetUrl);

        var modalHtml = '<div class="version-details-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:16px; margin-bottom:20px;">' +
            '<div class="vcard-metric" style="background:var(--glass-bg, rgba(255,255,255,0.05)); border:1px solid var(--glass-border, #e2e8f0); border-radius:12px; padding:16px;">' +
                '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">' + lblVer + '</div>' +
                '<div style="font-size:1.25rem; font-weight:700; color:var(--primary);">' + escHtml(ver) + '</div>' +
            '</div>' +
            '<div class="vcard-metric" style="background:var(--glass-bg, rgba(255,255,255,0.05)); border:1px solid var(--glass-border, #e2e8f0); border-radius:12px; padding:16px;">' +
                '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">📅 最近更新时间</div>' +
                '<div style="font-size:1.1rem; font-weight:700; color:var(--text);">' + escHtml(date) + '</div>' +
            '</div>' +
            '<div class="vcard-metric" style="background:var(--glass-bg, rgba(255,255,255,0.05)); border:1px solid var(--glass-border, #e2e8f0); border-radius:12px; padding:16px;">' +
                '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">🚀 首次发布日期</div>' +
                '<div style="font-size:1.1rem; font-weight:700; color:var(--text);">' + escHtml(relDate) + '</div>' +
            '</div>' +
            '<div class="vcard-metric" style="background:var(--glass-bg, rgba(255,255,255,0.05)); border:1px solid var(--glass-border, #e2e8f0); border-radius:12px; padding:16px;">' +
                '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">' + lblCount + '</div>' +
                '<div style="font-size:1.25rem; font-weight:700; color:var(--accent, #8b5cf6);">' + (count ? (fmtBigNum(count) + countUnit) : '未知') + '</div>' +
            '</div>' +
            (extra.skipMcVersCard ? '' : ('<div class="vcard-metric" style="background:var(--glass-bg, rgba(255,255,255,0.05)); border:1px solid var(--glass-border, #e2e8f0); border-radius:12px; padding:16px;">' +
                '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">🎮 Minecraft 支持版本</div>' +
                '<div style="font-size:1.05rem; font-weight:700; color:var(--emerald, #059669);">' + (mcStrip ? (mcVersList.length + ' 个具体版本') : escHtml(mcVers)) + '</div>' +
            '</div>')) +
            '<div class="vcard-metric" style="background:var(--glass-bg, rgba(255,255,255,0.05)); border:1px solid var(--glass-border, #e2e8f0); border-radius:12px; padding:16px;">' +
                '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">' + lblType + '</div>' +
                '<div style="font-size:1.05rem; font-weight:700; color:var(--text);">' + escHtml(typeName) + (modCount ? ' · ' + escHtml(modCount) : '') + '</div>' +
            '</div>' +
        '</div>' +
        mcStrip +
        '<div class="vcard-notice" style="background:rgba(37,99,235,0.08); border-left:4px solid var(--primary); padding:14px 18px; border-radius:0 10px 10px 0; margin-bottom:20px; font-size:0.88rem; line-height:1.6; color:var(--text);">' +
            '<b>🛡️ 本地离线安全保护说明：</b><br>' +
            noticeText +
        '</div>' +
        '<div style="text-align:center; padding:15px 0;">' +
            '<a href="' + targetUrl + '" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="display:inline-flex; align-items:center; gap:8px; padding:10px 24px; font-size:0.95rem; font-weight:700; border-radius:10px; text-decoration:none; box-shadow:0 4px 14px rgba(37,99,235,0.3);">' +
                '<span>' + escHtml(btnLabel) + '</span>' +
            '</a>' +
        '</div>';

        if (extra.items && extra.items.length > 0) {{
            modalHtml += '<div style="margin-top:20px; border-top:1px solid var(--border-color, rgba(255,255,255,0.1)); padding-top:16px;">' +
                '<h4 style="font-size:1rem; font-weight:700; margin:0 0 12px; color:var(--text);">📜 该整合包关联的全部发布与迭代历史视频 (' + extra.items.length + ' 期)</h4>' +
                '<div style="display:flex; flex-direction:column; gap:10px; max-height:260px; overflow-y:auto; padding-right:6px;">';
            extra.items.forEach(function(it, idx) {{
                var isLatest = idx === 0 ? '<span style="background:rgba(251,114,153,0.2); color:#fb7299; border:1px solid rgba(251,114,153,0.3); border-radius:4px; font-size:11px; padding:1px 6px; font-weight:700;">最新发布</span>' : '';
                modalHtml += '<div style="display:flex; align-items:center; justify-content:space-between; background:var(--surface, rgba(255,255,255,0.04)); border:1px solid var(--border, rgba(255,255,255,0.08)); border-radius:8px; padding:10px 12px; gap:10px;">' +
                    '<div style="flex:1; min-width:0;">' +
                        '<div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">' + isLatest + '<span style="font-size:12px; color:var(--text-muted);">' + (it.pub_time || '') + '</span></div>' +
                        '<a href="' + it.url + '" target="_blank" rel="noreferrer" style="font-size:13px; font-weight:700; color:var(--text); text-decoration:none;" title="' + escHtml(it.title) + '">' + escHtml(it.title) + '</a>' +
                    '</div>' +
                    '<a href="' + it.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="font-size:11px; padding:4px 10px; text-decoration:none;">在新窗口观看 ↗</a>' +
                '</div>';
            }});
            modalHtml += '</div></div>';
        }}

        if (extra.links && extra.links.length > 0) {{
            var hasVersionedLinks = false;
            for (var lki = 0; lki < extra.links.length; lki++) {{
                if (extra.links[lki] && (extra.links[lki].version || extra.links[lki].label)) {{
                    hasVersionedLinks = true;
                    break;
                }}
            }}

            if (hasVersionedLinks) {{
                modalHtml += '<div style="margin-top:20px; border-top:1px solid var(--border-color, rgba(255,255,255,0.1)); padding-top:16px;">' +
                    '<h4 style="font-size:1rem; font-weight:700; margin:0 0 12px; color:var(--text); display:flex; align-items:center; justify-content:space-between;">' +
                        '<span>📦 历史版本发布与下载通道 (' + extra.links.length + ' 个)</span>' +
                        '<span style="font-size:11px; font-weight:500; color:var(--text-muted);">按发布通道与版本号整理 · 点击直达下载</span>' +
                    '</h4>' +
                    '<div style="display:flex; flex-direction:column; gap:8px; max-height:260px; overflow-y:auto; padding-right:4px;">';
                extra.links.forEach(function(l) {{
                    if (l && l.url) {{
                        var lName = (l.name || '官方通道').trim();
                        var verTag = (l.version || l.label || '通用版本').trim();
                        var sizeInfo = l.size ? (' · <span style="font-size:11px; color:var(--text-muted);">' + escHtml(l.size, true) + '</span>') : '';
                        modalHtml += '<div style="display:flex; align-items:center; justify-content:space-between; background:var(--surface, rgba(255,255,255,0.04)); border:1px solid var(--border, rgba(255,255,255,0.08)); border-radius:8px; padding:8px 12px; gap:10px;">' +
                            '<div style="display:flex; align-items:center; gap:8px; min-width:0; flex:1;">' +
                                '<span class="version-meta-tag" style="background:rgba(var(--primary-rgb, 59, 130, 246), 0.15); color:var(--primary); font-weight:700; font-size:11px; padding:2px 8px; border-radius:6px; flex-shrink:0;">🏷️ ' + escHtml(verTag, true) + '</span>' +
                                '<span style="font-size:12px; font-weight:600; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">' + escHtml(lName, true) + '</span>' +
                                sizeInfo +
                            '</div>' +
                            '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="font-size:11px; padding:4px 10px; text-decoration:none; flex-shrink:0;">💾 极速下载 ↗</a>' +
                        '</div>';
                    }}
                }});
                modalHtml += '</div></div>';
            }} else {{
                modalHtml += '<div style="margin-top:20px; border-top:1px solid var(--border-color, rgba(255,255,255,0.1)); padding-top:16px;">' +
                    '<h4 style="font-size:1rem; font-weight:700; margin:0 0 12px; color:var(--text);">💾 关联下载与历史资源通道 (' + extra.links.length + ' 个)</h4>' +
                    '<div style="display:flex; flex-wrap:wrap; gap:8px;">';
                extra.links.forEach(function(l) {{
                    if (l && l.url) {{
                        var lName = (l.name || '直接下载').trim();
                        var vTag = l.version ? ' (' + l.version + ')' : '';
                        modalHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="font-size:12px; padding:6px 12px; text-decoration:none;">💾 ' + escHtml(lName + vTag) + ' ↗</a>';
                    }}
                }});
                modalHtml += '</div></div>';
            }}
        }}

        $vBodyInner.html(modalHtml);
        $vModal.css('display', 'flex');
        setTimeout(function() {{ $vModal.addClass('show'); }}, 10);
    }}

    function closeVersionModal() {{
        $vModal.removeClass('show');
        setTimeout(function() {{
            $vModal.hide();
        }}, 220);
    }}

    /* 全平台通用悬浮预览与版本模态窗事件绑定 */
    $(document).on('mouseenter', '.js-open-unified-preview', function() {{
        showDescPopup($(this));
    }}).on('mouseleave', '.js-open-unified-preview', function() {{
        hideDescPopup();
    }});

    $(document).on('click', '.js-open-plat-version-modal', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        var $btn = $(this);
        var plat = $btn.attr('data-platform') || 'bbsmc';
        var key = $btn.attr('data-vkey') || '';
        var p = key ? ((window.__packByUrl || {{}})[key]) : null;
        if (p) {{
            var extra = buildCardModalExtra(plat, p);
            openVersionModal(p.id || p.project_id || p.url, p.title, extra.ver, extra.date, extra.count, null, extra);
            return;
        }}
        // 回退：没有索引时（例如数据被外部脚本替换过）仍按 data-* 展示，保证不白屏
        var fallback = {{
            platform: plat,
            title: $btn.data('title') || '',
            ver: $btn.data('ver') || '通用 / 最新',
            date: $btn.data('date') || '暂无记录',
            url: $btn.data('url') || '#',
            count: null,
            verLabel: ($btn.data('ver-label')) || undefined,
            typeName: ($btn.data('type')) || undefined
        }};
        if (!fallback.typeName) delete fallback.typeName;
        openVersionModal(null, fallback.title, fallback.ver, fallback.date, fallback.count, null, fallback);
    }});

    $(document).on('click', '.js-open-bili-group-versions', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        var key = $(this).data('group-key');
        var g = window.biliGroupsMap ? window.biliGroupsMap[key] : null;
        if (g) {{
            var lab = __CARD_PLAT_LABELS.bilibili || {{}};
            // 只汇总组内视频真实存在的字段：MC 版本取并集、分类取并集、最早发布时间作首发
            var verSet = [], catSet = [], loaderSet = [], views = 0, earliest = '', modCount = null;
            g.items.forEach(function(it) {{
                (it.all_versions || []).forEach(function(v) {{ if (verSet.indexOf(v) === -1) verSet.push(v); }});
                if (it.mc_version && verSet.indexOf(it.mc_version) === -1) verSet.push(it.mc_version);
                (it.categories || []).forEach(function(c) {{ if (catSet.indexOf(c) === -1) catSet.push(c); }});
                (it.loaders || []).forEach(function(l) {{ if (loaderSet.indexOf(l) === -1) loaderSet.push(l); }});
                views += (typeof it.views === 'number' ? it.views : 0);
                if (typeof it.mod_count === 'number' && it.mod_count > 0) {{
                    modCount = (modCount === null) ? it.mod_count : Math.max(modCount, it.mod_count);
                }}
                if (it.pub_time && (!earliest || it.pub_time < earliest)) earliest = it.pub_time;
            }});
            var typeParts = [];
            if (catSet.length) typeParts.push(catSet.map(catLabel).join(' · '));
            if (loaderSet.length) typeParts.push('加载器: ' + loaderSet.map(loaderLabel).join(' · '));
            // mod_count 只有 B站 数据里真的有，有才显示
            if (modCount !== null) typeParts.push('整合包模组数: ' + modCount + ' 款');
            var verText = verSet.length ? verSet.join(' · ') : '未标注版本';
            openVersionModal(null, g.displayTitle, verText, g.latestPubTime, g.items.length, null, {{
                platform: 'bilibili',
                title: g.displayTitle,
                ver: verText,
                date: g.latestPubTime,
                date_created: earliest,
                url: g.items[0] ? g.items[0].url : '#',
                items: g.items,
                count: g.items.length,
                // 主版本槽已经承载「支持版本」，再放一张 Minecraft 支持版本卡就是重复信息
                skipMcVersCard: true,
                mcVers: verText,
                mcVersList: verSet,
                typeName: typeParts.join(' · ') || '未标注分类',
                verLabel: lab.verLabel, countLabel: lab.countLabel, countUnit: lab.countUnit,
                typeLabel: lab.typeLabel, countTagLabel: lab.countTagLabel, countTagUnit: lab.countTagUnit
            }});
        }}
    }});


    $(document).on('click', '.js-open-version-modal, .modpack-version-badge', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        var $btn = $(this);
        var mid = $btn.data('mid');
        if (!mid) {{
            var href = $btn.attr('href') || '';
            var m = href.match(/version\\/([0-9]+)/);
            if (m) mid = m[1];
        }}
        var row = null;
        if (mid && window.tableRowsData) {{
            for (var i = 0; i < window.tableRowsData.length; i++) {{
                if (String(window.tableRowsData[i].mid) === String(mid)) {{
                    row = window.tableRowsData[i];
                    break;
                }}
            }}
        }}
        openVersionModal(
            mid,
            (row && row.title) || $btn.data('title'),
            (row && row.latest_version) || $btn.data('ver'),
            (row && row.last_update_date) || $btn.data('date'),
            (row && row.version_count) || $btn.data('count'),
            row
        );
    }});

    $('#versionModalClose').on('click', function(e) {{
        e.preventDefault();
        closeVersionModal();
    }});

    $vModal.on('click', function(e) {{
        if (e.target === this) {{
            closeVersionModal();
        }}
    }});

    $(document).on('keydown', function(e) {{
        if (e.key === 'Escape' || e.keyCode === 27) {{
            if ($vModal.hasClass('show')) {{
                closeVersionModal();
            }}
        }}
    }});

    // ───── 评论嵌入预览交互 ─────
    $(document).on('click', '.js-embed-comment-preview', function(e) {{
        e.preventDefault();
        var u = $(this).data('url');
        var $box = $('#commentEmbedContainer');
        var $ifm = $('#commentEmbedIframe');
        if ($box.is(':visible')) {{
            $box.slideUp(180);
            $ifm.attr('src', 'about:blank');
            $(this).text('📜 在看板内嵌入浏览评论区');
        }} else {{
            $ifm.attr('src', u);
            $box.slideDown(220);
            $(this).text('收起嵌入预览 ▴');
        }}
    }});
    // =====================================================================
    // ───── 迷你走势悬浮窗渲染系统 ─────
    var $trendTooltip = $('<div class="trend-tooltip" id="trendTooltip">' +
        '<button type="button" class="hover-close" id="trendClose" title="关闭趋势图">✕</button>' +
        '<div class="trend-tooltip-title" id="trendTooltipTitle"></div>' +
        '<div class="trend-tooltip-subtitle" id="trendTooltipSubtitle">近 60 天指数走势历史</div>' +
        '<div class="trend-tooltip-chart-container" id="trendTooltipChartContainer"></div>' +
        '<div class="trend-point-label" id="trendPointLabel"></div>' +
        '<div class="trend-tooltip-footer" id="trendTooltipFooter"></div>' +
        '<div class="hover-cooldown-tip">再次点击同一趋势格、按 Esc 或点右上角可关闭</div>' +
        '</div>').appendTo('body');
    var $trendBridge = $('<div class="trend-hover-bridge" id="trendHoverBridge"></div>').appendTo('body');
    var trendHoverTimer = null;
    var activeTrendCell = null;
    var activeTrendRowKey = '';
    var trendSuppressOpenUntil = 0;
    var trendPopupPinned = false;
    var trendHoverPopupEnabled = localStorage.getItem('trend-hover-popup-enabled') === '1';
    function getTrendRowKey(cell) {{
        var $cell = $(cell);
        var $row = $cell.closest('tr');
        return String($row.attr('data-mid') || $row.data('mid') || $cell.data('title') || '');
    }}
    function syncHoverToggles() {{
        $('.js-desc-hover-toggle').prop('checked', descHoverPopupEnabled).closest('.mode-toggle-header').toggleClass('is-on', descHoverPopupEnabled).attr('aria-pressed', descHoverPopupEnabled ? 'true' : 'false');
        $('.js-trend-hover-toggle').prop('checked', trendHoverPopupEnabled).closest('.mode-toggle-header').toggleClass('is-on', trendHoverPopupEnabled).attr('aria-pressed', trendHoverPopupEnabled ? 'true' : 'false');
        $('.js-comment-hover-toggle').prop('checked', commentHoverPopupEnabled).closest('.mode-toggle-header').toggleClass('is-on', commentHoverPopupEnabled).attr('aria-pressed', commentHoverPopupEnabled ? 'true' : 'false');
    }}
    function setDescHoverMode(enabled) {{
        descHoverPopupEnabled = !!enabled;
        localStorage.setItem('desc-hover-popup-enabled', descHoverPopupEnabled ? '1' : '0');
        syncHoverToggles();
    }}
    function setTrendHoverMode(enabled) {{
        trendHoverPopupEnabled = !!enabled;
        localStorage.setItem('trend-hover-popup-enabled', trendHoverPopupEnabled ? '1' : '0');
        syncHoverToggles();
        if (!trendHoverPopupEnabled && !trendPopupPinned) {{
            $('#trendPointLabel').hide();
            $('#trendGuideLine').css('visibility', 'hidden');
            hideTrendBridge();
            $trendTooltip.removeClass('show').hide();
        }}
    }}
    function setCommentHoverMode(enabled) {{
        commentHoverPopupEnabled = !!enabled;
        localStorage.setItem('comment-hover-popup-enabled', commentHoverPopupEnabled ? '1' : '0');
        syncHoverToggles();
    }}
    function toggleHeaderMode(toggle) {{
        if (!toggle) return;
        if (toggle.querySelector('.js-desc-hover-toggle')) {{
            setDescHoverMode(!descHoverPopupEnabled);
        }} else if (toggle.querySelector('.js-trend-hover-toggle')) {{
            setTrendHoverMode(!trendHoverPopupEnabled);
        }} else if (toggle.querySelector('.js-comment-hover-toggle')) {{
            setCommentHoverMode(!commentHoverPopupEnabled);
        }}
    }}
    document.addEventListener('click', function(e) {{
        var toggle = e.target && e.target.closest ? e.target.closest('.mode-toggle-header') : null;
        if (!toggle) return;
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        toggleHeaderMode(toggle);
    }}, true);
    ['pointerdown', 'mousedown', 'mouseup', 'dblclick'].forEach(function(evtName) {{
        document.addEventListener(evtName, function(e) {{
            var toggle = e.target && e.target.closest ? e.target.closest('.mode-toggle-header') : null;
            if (!toggle) return;
            e.stopPropagation();
            if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        }}, true);
    }});
    document.addEventListener('keydown', function(e) {{
        var toggle = e.target && e.target.closest ? e.target.closest('.mode-toggle-header') : null;
        if (!toggle || (e.key !== 'Enter' && e.key !== ' ')) return;
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        toggleHeaderMode(toggle);
    }}, true);
    $(document).on('mousedown click dblclick', '.mode-toggle, .mode-toggle input', function(e) {{
        e.stopPropagation();
    }});
    syncHoverToggles();
    $(document).on('change', '.js-desc-hover-toggle', function(e) {{
        e.stopPropagation();
        setDescHoverMode($(this).is(':checked'));
    }});
    $(document).on('change', '.js-trend-hover-toggle', function(e) {{
        e.stopPropagation();
        setTrendHoverMode($(this).is(':checked'));
    }});
    $(document).on('change', '.js-comment-hover-toggle', function(e) {{
        e.stopPropagation();
        setCommentHoverMode($(this).is(':checked'));
    }});
    function isTrendHoverAlive() {{
        var overTooltip = $trendTooltip.is(':hover');
        var overBridge = $trendBridge.is(':hover');
        var overCell = activeTrendCell && activeTrendCell.length && activeTrendCell.is(':hover');
        return !!(overTooltip || overBridge || overCell);
    }}
    function hideTrendBridge() {{
        $trendBridge.hide();
    }}
    function hideTrendTooltipSoon(delay) {{
        if (trendPopupPinned) return;
        clearTimeout(trendHoverTimer);
        trendHoverTimer = setTimeout(function() {{
            if (isTrendHoverAlive()) return;
            $('#trendPointLabel').hide();
            $('#trendGuideLine').css('visibility', 'hidden');
            $trendTooltip.addClass('hiding').removeClass('show');
            hideTrendBridge();
            setTimeout(function() {{
                if (!$trendTooltip.hasClass('show')) $trendTooltip.hide().removeClass('hiding');
                activeTrendCell = null;
            }}, 180);
        }}, delay || 720);
    }}
    function hideTrendTooltipNow() {{
        clearTimeout(trendHoverTimer);
        trendPopupPinned = false;
        $('#trendPointLabel').hide();
        $('#trendGuideLine').css('visibility', 'hidden');
        hideTrendBridge();
        $trendTooltip.removeClass('show hiding').hide();
        activeTrendCell = null;
        activeTrendRowKey = '';
    }}
    function updateTrendBridge($cell) {{
        if (!$cell || !$cell.length || !$trendTooltip.is(':visible')) return;
        var c = $cell[0].getBoundingClientRect();
        var t = $trendTooltip[0].getBoundingClientRect();
        var left = Math.min(c.left, t.left) - 8;
        var right = Math.max(c.right, t.right) + 8;
        var top = Math.min(c.top, t.top) - 8;
        var bottom = Math.max(c.bottom, t.bottom) + 8;
        $trendBridge.css({{
            left: Math.max(0, left) + 'px',
            top: Math.max(0, top) + 'px',
            width: Math.max(1, right - left) + 'px',
            height: Math.max(1, bottom - top) + 'px'
        }}).show();
    }}
    function positionTrendTooltip(anchorEvent, $cell) {{
        var tw = $trendTooltip.outerWidth();
        var th = $trendTooltip.outerHeight();
        var vw = window.innerWidth;
        var vh = window.innerHeight;
        var gap = 2;
        var rect = $cell && $cell.length ? $cell[0].getBoundingClientRect() : null;
        var left = rect ? (rect.left + rect.width / 2 - tw / 2) : 10;
        var top = rect ? (rect.top - th - gap) : 10;
        if (rect && top < 10) {{
            top = Math.min(rect.bottom + gap, vh - th - 10);
        }}
        if (top + th > vh - 10) top = vh - th - 10;
        if (top < 10) top = 10;
        if (left + tw > vw - 10) left = vw - tw - 10;
        if (left < 10) left = 10;
        $trendTooltip.css({{ left: left + 'px', top: top + 'px' }});
        updateTrendBridge($cell);
    }}
    $(document).on('trend:open', '.td-trend', function(e, pinned, sourceEvent) {{
        clearTimeout(trendHoverTimer);
        if (Date.now() < trendSuppressOpenUntil) return;
        if (!pinned && (!trendHoverPopupEnabled || trendPopupPinned)) return;
        if (pinned) trendPopupPinned = true;
        var anchorEvent = sourceEvent || e;
        var $cell = $(this);
        activeTrendCell = $cell;
        activeTrendRowKey = getTrendRowKey($cell);
        var title = $cell.data('title') || '';
        var trendKey = 'trend:' + title + ':' + ($cell.data('trend') || '');
        activeTrendKey = trendKey;
        if (isHoverCooling(trendKey)) return;
        if ($trendTooltip.hasClass('show') && $trendTooltip.data('active-row-key') === activeTrendRowKey && activeTrendCell && activeTrendCell.length && $cell.is(activeTrendCell)) {{
            return;
        }}
        var metric = $cell.data('metric') || '走势';
        var trendStr = $cell.data('trend') || '';
        var datesStr = $cell.data('dates') || '';
        if (!trendStr) {{
            $trendTooltip.hide();
            return;
        }}
        var trendVals = trendStr.split(',').map(Number).filter(function(v) {{ return !isNaN(v); }});
        var dates = datesStr.split(',');
        if (trendVals.length < 2) {{
            $trendTooltip.hide();
            return;
        }}
        // 渲染标题
        $('#trendTooltipTitle').text(title);
        $('#trendTooltipSubtitle').text(metric + ' · 近 ' + trendVals.length + ' 天指数走势');
        // 测算数值范围
        var minVal = Math.min.apply(null, trendVals);
        var maxVal = Math.max.apply(null, trendVals);
        var latestVal = trendVals[trendVals.length - 1];
        var startVal = trendVals[0];
        var avgVal = Math.round(trendVals.reduce(function(a, b){{ return a + b; }}, 0) / trendVals.length);
        var firstDate = dates[0] || '';
        var lastDate = dates[trendVals.length - 1] || '';
        var delta = latestVal - startVal;
        var deltaPct = startVal ? (delta / startVal * 100) : 0;
        var deltaAbs = Math.abs(Math.round(delta));
        var deltaPctAbs = Math.abs(deltaPct).toFixed(1);
        var deltaDir = delta === 0 ? '基本不变' : (delta > 0 ? '增加 ' : '减少 ') + deltaAbs + ' 点';
        var deltaPctText = delta === 0 ? '0%' : (delta > 0 ? '上涨 ' : '下降 ') + deltaPctAbs + '%';
        var rangeText = firstDate && lastDate ? (firstDate + ' 至 ' + lastDate) : ('共 ' + trendVals.length + ' 天');
        // 填充页脚统计
        $('#trendTooltipFooter').html(
            '<span>最新指数<br><b>' + latestVal + '</b></span>' +
            '<span>总涨幅<br><b>' + deltaDir + '</b><em>' + deltaPctText + '</em></span>' +
            '<span>平均 / 最高<br><b>' + avgVal + ' / ' + maxVal + '</b></span>'
        );
        $('#trendTooltipSubtitle').text(metric + ' · 本地/官网历史 ' + trendVals.length + ' 天 · ' + rangeText);
        // 生成 SVG 走势图
        var width = 352;
        var height = 150;
        var paddingT = 18;
        var paddingB = 22;
        var paddingL = 28;
        var paddingR = 12;
        var chartW = width - paddingL - paddingR;
        var chartH = height - paddingT - paddingB;
        var valDiff = maxVal - minVal;
        if (valDiff === 0) valDiff = 1;
        var points = [];
        var len = trendVals.length;
        for (var i = 0; i < len; i++) {{
            var x = paddingL + (i / (len - 1)) * chartW;
            var y = height - paddingB - ((trendVals[i] - minVal) / valDiff) * chartH;
            points.push({{ x: x, y: y, value: trendVals[i], date: dates[i] || '' }});
        }}
        // 生成连线 path 和渐变填充 path
        var pathD = 'M ' + points[0].x + ' ' + points[0].y;
        for (var i = 1; i < len; i++) {{
            pathD += ' L ' + points[i].x + ' ' + points[i].y;
        }}
        var areaD = pathD +
            ' L ' + points[len-1].x + ' ' + (height - paddingB) +
            ' L ' + points[0].x + ' ' + (height - paddingB) + ' Z';
        var trendColor = 'var(--primary)';
        var markerHtml = '';
        var hitHtml = '<line class="trend-guide-line" id="trendGuideLine" x1="' + paddingL + '" y1="' + paddingT + '" x2="' + paddingL + '" y2="' + (height - paddingB) + '" />' +
            '<rect class="trend-chart-capture" x="' + paddingL + '" y="' + paddingT + '" width="' + chartW + '" height="' + chartH + '" fill="rgba(0,0,0,0.001)" pointer-events="all" />';
        for (var i = 0; i < len; i++) {{
            var p = points[i];
            var isMax = p.value === maxVal;
            var isMin = p.value === minVal;
            var isLatest = i === len - 1;
            if (isMax || isMin || isLatest || i === 0) {{
                markerHtml += '<circle class="trend-point-visible" cx="' + p.x + '" cy="' + p.y + '" r="' + (isMax ? 5.5 : isLatest ? 5 : 3.5) + '" fill="var(--glass-bg-solid)" stroke="' + trendColor + '" stroke-width="' + (isMax ? 2.4 : 1.8) + '" />';
            }}
            hitHtml += '<circle class="trend-point-hit" cx="' + p.x + '" cy="' + p.y + '" r="8" fill="rgba(0,0,0,0.001)" data-x="' + p.x + '" data-y="' + p.y + '" data-date="' + p.date + '" data-value="' + p.value + '" data-kind="' + (isMax ? '峰值' : isMin ? '低点' : isLatest ? '最新' : '') + '" />';
        }}
        // 绘制 SVG (使用主题颜色)
        var svgHtml = '<svg width="' + width + '" height="' + height + '">' +
            '<defs>' +
            '  <linearGradient id="trendGrad" x1="0%" y1="0%" x2="0%" y2="100%">' +
            '    <stop offset="0%" stop-color="' + trendColor + '" stop-opacity="0.36"/>' +
            '    <stop offset="100%" stop-color="' + trendColor + '" stop-opacity="0.0"/>' +
            '  </linearGradient>' +
            '</defs>' +
            '<line x1="' + paddingL + '" y1="' + paddingT + '" x2="' + (width - paddingR) + '" y2="' + paddingT + '" stroke="var(--glass-border)" stroke-dasharray="4,4" />' +
            '<line x1="' + paddingL + '" y1="' + (height - paddingB) + '" x2="' + (width - paddingR) + '" y2="' + (height - paddingB) + '" stroke="var(--glass-border)" stroke-dasharray="4,4" />' +
            '<text x="2" y="' + (paddingT + 4) + '" font-size="10" fill="var(--text-secondary)" text-anchor="start">' + maxVal + '</text>' +
            '<text x="2" y="' + (height - paddingB + 4) + '" font-size="10" fill="var(--text-secondary)" text-anchor="start">' + minVal + '</text>' +
            '<path d="' + areaD + '" fill="url(#trendGrad)" />' +
            '<path d="' + pathD + '" fill="none" stroke="' + trendColor + '" stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round" />' +
            markerHtml +
            hitHtml +
            '<text x="' + paddingL + '" y="' + (height - 5) + '" font-size="10" fill="var(--text-secondary)" text-anchor="start">' + firstDate + '</text>' +
            '<text x="' + (width - paddingR) + '" y="' + (height - 5) + '" font-size="10" fill="var(--text-secondary)" text-anchor="end">' + lastDate + '</text>' +
            '</svg>';
        $('#trendTooltipChartContainer').html(svgHtml + '<div class="trend-point-label" id="trendPointLabel" style="display:none; position:absolute; z-index:10; pointer-events:none;"></div>');
        function showTrendPoint(point) {{
            if (!point) return;
            var x = Number(point.x) || 0;
            var y = Number(point.y) || 0;
            var kind = point.kind || '';
            var date = point.date || '未知日期';
            var value = point.value;
            $('#trendPointLabel')
                .html((kind ? '<b>' + kind + '</b><br>' : '') + date + '<br>指数 ' + value)
                .css({{ left: Math.min(Math.max(x + 10, 8), width - 118) + 'px', top: Math.max(y - 34, 6) + 'px' }})
                .show();
            $('#trendGuideLine')
                .attr('x1', x).attr('x2', x)
                .css('visibility', 'visible');
        }}
        function pointFromNode(node) {{
            return {{
                x: Number(node.getAttribute('data-x')) || 0,
                y: Number(node.getAttribute('data-y')) || 0,
                date: node.getAttribute('data-date') || '',
                value: node.getAttribute('data-value') || '',
                kind: node.getAttribute('data-kind') || ''
            }};
        }}
        function nearestPointFromEvent(e) {{
            var svg = e.currentTarget.ownerSVGElement || e.currentTarget;
            var rect = svg.getBoundingClientRect();
            var clickX = e.clientX - rect.left;
            var chartX = clickX - paddingL;
            var ratio = chartX / chartW;
            var idx = Math.round(ratio * (len - 1));
            if (idx < 0) idx = 0;
            if (idx >= len) idx = len - 1;
            var point = points[idx];
            var isMax = point.value === maxVal;
            var isMin = point.value === minVal;
            var isLatest = idx === len - 1;
            return {{ x: point.x, y: point.y, date: point.date, value: point.value, kind: isMax ? '峰值' : isMin ? '低点' : isLatest ? '最新' : '' }};
        }}
        showTrendPoint({{
            x: points[len - 1].x,
            y: points[len - 1].y,
            date: points[len - 1].date,
            value: points[len - 1].value,
            kind: '最新'
        }});
        $('#trendTooltipChartContainer .trend-chart-capture').on('mouseenter mousemove click', function(e) {{
            showTrendPoint(nearestPointFromEvent(e));
        }});
        $('#trendTooltipChartContainer .trend-point-hit').on('mouseenter mousemove click', function() {{
            showTrendPoint(pointFromNode(this));
        }});
        $trendTooltip.removeClass('hiding').addClass('show').data('active-title', title).data('active-row-key', activeTrendRowKey).show();
        positionTrendTooltip(anchorEvent, $cell);
    }});
    $(document).on('mouseenter', '.td-trend', function(e) {{
        $(this).trigger('trend:open', [false, e]);
    }});
    $(document).on('click', '.td-trend', function(e) {{
        if ($(e.target).closest('a, button').length) return;
        if (Date.now() < trendSuppressOpenUntil) {{
            e.preventDefault();
            e.stopPropagation();
            return;
        }}
        e.preventDefault();
        e.stopPropagation();
        var clickedRowKey = getTrendRowKey(this);
        if ($trendTooltip.hasClass('show') && $trendTooltip.data('active-row-key') === clickedRowKey) {{
            hideTrendTooltipNow();
            trendSuppressOpenUntil = Date.now() + 220;
            return;
        }}
        $(this).trigger('trend:open', [true, e]);
    }});
    document.addEventListener('click', function(e) {{
        var cell = e.target && e.target.closest ? e.target.closest('td.td-trend') : null;
        if (!cell || e.target.closest('a, button')) return;
        var clickedRowKey = getTrendRowKey(cell);
        if ($trendTooltip.hasClass('show') && $trendTooltip.data('active-row-key') === clickedRowKey) {{
            e.preventDefault();
            e.stopPropagation();
            if (e.stopImmediatePropagation) e.stopImmediatePropagation();
            hideTrendTooltipNow();
            trendSuppressOpenUntil = Date.now() + 220;
        }}
    }}, true);
    $(document).on('mouseleave', '.td-trend', function() {{
        hideTrendTooltipSoon(720);
    }});
    $trendTooltip.on('mouseenter', function() {{
        clearTimeout(trendHoverTimer);
    }}).on('mouseleave', function() {{
        hideTrendTooltipSoon(360);
    }});
    $trendTooltip.on('mousedown', function(e) {{
        if ($(e.target).is('#trendTooltip')) {{
            hideTrendTooltipNow();
        }}
    }});
    $trendBridge.on('mouseenter', function() {{
        clearTimeout(trendHoverTimer);
    }}).on('mouseleave', function() {{
        hideTrendTooltipSoon(360);
    }});
    function showInlineTrendProbe(e, $svg) {{
        var $cell = $svg.closest('.td-trend');
        var trendStr = $cell.data('trend') || '';
        var datesStr = $cell.data('dates') || '';
        if (!trendStr) return;
        var vals = trendStr.split(',').map(Number).filter(function(v) {{ return !isNaN(v); }});
        var dates = datesStr ? datesStr.split(',') : [];
        if (vals.length < 2) return;
        var rect = $svg[0].getBoundingClientRect();
        var ratio = (e.clientX - rect.left) / rect.width;
        if (ratio < 0) ratio = 0;
        if (ratio > 1) ratio = 1;
        var idx = Math.round(ratio * (vals.length - 1));
        var value = vals[idx];
        var date = dates[idx] || '';
        var $probe = $cell.children('.trend-inline-probe');
        if (!$probe.length) {{
            $probe = $('<div class="trend-inline-probe"></div>').appendTo($cell);
        }}
        var cellRect = $cell[0].getBoundingClientRect();
        var left = e.clientX - cellRect.left + 10;
        var top = e.clientY - cellRect.top - 42;
        if (left > cellRect.width - 104) left = Math.max(6, cellRect.width - 104);
        if (top < 6) top = e.clientY - cellRect.top + 12;
        $probe.html('<b>' + value + '</b>' + (date ? date : '')).
            css({{ left: left + 'px', top: top + 'px' }}).show();
    }}
    $(document).on('mousemove', '.sparkline-svg', function(e) {{
        showInlineTrendProbe(e, $(this));
    }});
    $(document).on('mouseleave', '.sparkline-svg', function() {{
        $(this).closest('.td-trend').children('.trend-inline-probe').hide();
    }});
    // ────── 悬浮窗智能自适应延迟关闭与滚轮管理系统 ──────
    // =====================================================================
    /* ── 1. 悬停整合包名称 → 显示介绍（带 300ms 延迟及淡入淡出锁死） ── */
    $(document).on('mouseenter', '.modpack-link', function() {{
        if (!descHoverPopupEnabled) return;
        var $self = $(this);
        var descKey = 'desc:' + (($self.data('mid') || '') || ($self.attr('href') || '') || $self.text());
        if (isHoverCooling(descKey)) return;
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {{
            showDescPopup($self);
            $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
        }}, HOVER_DELAY);
    }});
    $(document).on('mouseleave', '.modpack-link', function() {{
        if (!descHoverPopupEnabled) return;
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {{
            hideDescPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 300);
    }});
    $(document).on('click', '.modpack-link', function(e) {{
        if (descHoverPopupEnabled) return;
        e.preventDefault();
        e.stopPropagation();
        var $self = $(this);
        var descKey = 'desc:' + (($self.data('mid') || '') || ($self.attr('href') || '') || $self.text());
        if ($popup.hasClass('show') && activeDescKey === descKey) {{
            hideDescPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
            return;
        }}
        clearTimeout(hoverTimer);
        showDescPopup($self);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }});
    $popup.on('mouseenter', function() {{
        clearTimeout(hoverTimer);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }}).on('mouseleave', function() {{
        if (!descHoverPopupEnabled) return;
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {{
            hideDescPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 300);
    }});
    /* ── 2. 点击评论列 / 卡片评论按钮 → 稳定打开评论详情；不再扫过表格就弹大窗 ── */
    $(document).on('click', '.td-comment', function(e) {{
        if ($(e.target).closest('a, button').length) return;
        var $self = $(this);
        clearTimeout(commentHoverTimer);
        if ($cpopup.hasClass('show') && activeCommentCell && activeCommentCell.length && $self.is(activeCommentCell)) {{
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
            return;
        }}
        showCommentPopup($self);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }});
    $(document).on('click', '.show-comment-btn', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        var $self = $(this);
        clearTimeout(commentHoverTimer);
        if ($cpopup.hasClass('show') && activeCommentCell && activeCommentCell.length && $self.is(activeCommentCell)) {{
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
            return;
        }}
        showCommentPopup($self);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }});
    $(document).on('keydown', '.engage-comment-trigger', function(e) {{
        if (e.key !== 'Enter' && e.key !== ' ') return;
        e.preventDefault();
        $(this).closest('.td-comment').trigger('click');
    }});
    $(document).on('mouseenter', '.td-comment', function() {{
        if (!commentHoverPopupEnabled) return;
        var $self = $(this);
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            if (!$self.is(':hover')) return;
            showCommentPopup($self);
            $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
        }}, HOVER_DELAY);
    }});
    $(document).on('mouseleave', '.td-comment', function() {{
        if (!commentHoverPopupEnabled) return;
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            if ($cpopup.is(':hover')) return;
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 260);
    }});
    $(document).on('mousedown', function(e) {{
        if (!$cpopup.hasClass('show')) return;
        if ($(e.target).closest('#commentPopup, .td-comment, .show-comment-btn, .comment-search-nav, .comment-page-bar').length) return;
        hideCommentPopup();
        $('body').css({{ 'overflow': '', 'height': '' }});
    }});
    $cpopup.on('mousedown', function(e) {{
        if ($(e.target).is('#commentPopup')) {{
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}
    }});
    $cpopup.on('mouseenter', function() {{
        clearTimeout(commentHoverTimer);
        $('body').css({{ 'overflow': 'hidden', 'height': '100vh' }});
    }}).on('mouseleave', function() {{
        if (!commentHoverPopupEnabled) return;
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {{
            hideCommentPopup();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }}, 280);
    }});
    /* ── 3. 关闭/Escape 恢复现场 ── */
    $('#pvClose').on('click', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        setHoverCooldown(activeDescKey);
        hideDescPopup();
        $('body').css({{ 'overflow': '', 'height': '' }});
    }});
    function closeFeedback() {{ $('#feedbackModal').removeClass('show'); }}
    var feedbackDraftKey = 'mcmod-feedback-draft-v1';
    try {{
        var draft = JSON.parse(localStorage.getItem(feedbackDraftKey) || '{{}}');
        $('#feedbackType').val(draft.type || '功能建议'); $('#feedbackContent').val(draft.content || ''); $('#feedbackContact').val(draft.contact || '');
    }} catch(e) {{}}
    $('#feedbackType, #feedbackContent, #feedbackContact').on('input change', function() {{
        localStorage.setItem(feedbackDraftKey, JSON.stringify({{ type: $('#feedbackType').val(), content: $('#feedbackContent').val(), contact: $('#feedbackContact').val() }}));
    }});
    $('#feedbackOpen').on('click', function() {{
        $('#feedbackStatus').text('⚠️ 反馈接收接口正在升级维护中，暂时不可用，敬请谅解。');
        $('#feedbackModal').addClass('show');
    }});
    $('#feedbackCancel, #feedbackModal').on('click', function(e) {{ if (e.target === this) closeFeedback(); }});
    $('#feedbackSubmit').on('click', function() {{
        var content = $('#feedbackContent').val().trim();
        if (!content) {{ $('#feedbackStatus').text('请先填写反馈内容。'); return; }}
        if (!feedbackUrl) {{ $('#feedbackStatus').text('作者尚未配置反馈接收地址。'); return; }}
        var $btn = $(this).prop('disabled', true).text('提交中…');
        $('#feedbackStatus').text('');
        fetch(feedbackUrl, {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{
            tool: '多平台聚合看板', version: 'v10.6.6', type: $('#feedbackType').val(), content: content, contact: $('#feedbackContact').val().trim()
        }}) }}).then(function(r) {{ return r.ok ? r.json().catch(function() {{ return {{ ok:true }}; }}) : Promise.reject(new Error('HTTP ' + r.status)); }}).then(function() {{
            $('#feedbackStatus').text('已提交，感谢你的反馈！'); $('#feedbackContent, #feedbackContact').val(''); localStorage.removeItem(feedbackDraftKey);
        }}).catch(function() {{ $('#feedbackStatus').text('提交失败，请稍后重试。'); }}).finally(function() {{ $btn.prop('disabled', false).text('提交'); }});
    }});
    $('#commentClose').on('click', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        hideCommentPopup();
        $('body').css({{ 'overflow': '', 'height': '' }});
    }});
    $('#trendClose').on('click', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        hideTrendTooltipNow();
    }});
    $(document).on('keydown', function(e) {{
        if (e.key === 'Escape') {{
            hideDescPopup();
            hideCommentPopup();
            hideTrendTooltipNow();
            closeImageLightbox();
            $('body').css({{ 'overflow': '', 'height': '' }});
        }} else if ($cpopup.hasClass('show')) {{
            if (e.key === 'ArrowLeft') {{
                e.preventDefault();
                $('#cmtPrev').trigger('click');
            }} else if (e.key === 'ArrowRight') {{
                e.preventDefault();
                $('#cmtNext').trigger('click');
            }}
        }}
    }});
    /* 窗口缩放 → 更新 scrollY */
    var resizeTimer = null;
    $(window).on('resize', function() {{
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {{
            var newH = Math.max(400, $(window).height() - 320);
            $('.dataTables_scrollBody').height(newH);
            if (table) {{
                table.columns.adjust();
            }}
            if ($cpopup.hasClass('show')) {{
                lockCommentPopupSize();
                repositionCommentPopup();
                checkCommentOverflow();
            }}
        }}, 300);
    }});
    
    /* ════════ 全局标签数量显隐独立控制 ════════ */
    var tagCountsVisible = localStorage.getItem('mc_show_tag_counts') !== 'false';
    function applyTagCountsVisibility() {{
        $('body').toggleClass('hide-tag-counts', !tagCountsVisible);
        $('#toggleTagCountsLabel').text(tagCountsVisible ? '标签数量' : '隐藏标签数');
        $('#toggleTagCountsBtn').attr('title', tagCountsVisible ? '当前已显示标签数量，点击可隐藏' : '当前已隐藏标签数量，点击可显示');
        $('#toggleTagCountsBtn').toggleClass('active', tagCountsVisible);
    }}
    applyTagCountsVisibility();
    $('#toggleTagCountsBtn').on('click', function() {{
        tagCountsVisible = !tagCountsVisible;
        localStorage.setItem('mc_show_tag_counts', tagCountsVisible);
        applyTagCountsVisibility();
    }});

    /* ════════ 数据抓取变动审计与生态监控交互逻辑 ════════ */
    var auditActiveType = 'all';
    var auditActivePlat = 'all';

    /* 独立命名的纯文本转义。历史上 escHtml 曾与"介绍正文排版器"同名，后者覆盖前者，
       于是这里拿到的不是转义而是段落 HTML（内容外面会套 <div class="pv-para">），
       用在 title="..." 这类属性位置时引号被内层标签冲断、整行 HTML 被当文本吐到页面上。
       排版器现已更名 formatDescHtml，这里仍保留独立命名，避免再次被同名覆盖踩到。 */
    function auditEsc(s) {{
        if (s === null || s === undefined) return '';
        return String(s)
            .split('&').join('&amp;')
            .split('<').join('&lt;')
            .split('>').join('&gt;')
            .split('"').join('&quot;')
            .split("'").join('&#39;');
    }}

    function initAuditDiffModule() {{
        var diff = window.auditDiffData;
        if (!diff) return;

        var stats = diff.stats || {{}};
        var addedCount = stats.added_count || 0;
        var updatedCount = stats.updated_count || 0;
        var removedCount = stats.removed_count || 0;
        var gainedCount = stats.version_gained_count || 0;
        var totalScope = stats.total_current || 0;
        var totalChanges = addedCount + updatedCount + removedCount + gainedCount;

        $('#auditBadgeCount').text(totalChanges);
        if (totalChanges > 0) $('#auditBadgeCount').show();

        $('#kpiAuditAdded').text(addedCount);
        $('#kpiAuditUpdated').text(updatedCount);
        $('#kpiAuditGained').text(gainedCount);
        $('#kpiAuditRemoved').text(removedCount);
        $('#kpiAuditTotal').text(totalScope.toLocaleString());
        $('#cntAllDiff').text(totalChanges);
        $('#cntAddedDiff').text(addedCount);
        $('#cntUpdatedDiff').text(updatedCount);
        $('#cntGainedDiff').text(gainedCount);
        $('#cntRemovedDiff').text(removedCount);

        if (diff.generated_at) {{
            $('#auditGenTime').text('📅 对比时间: ' + diff.generated_at);
        }}
        var scopeText = '📦 全网监测规模: ' + totalScope.toLocaleString() + ' 款';
        if ((diff.new_platforms || []).length) {{
            scopeText += '　|　本次新纳入: ' + diff.new_platforms.join('、');
        }}
        $('#auditTotalScope').text(scopeText);

        renderAuditItems();
    }}

    function renderAuditItems() {{
        var diff = window.auditDiffData;
        if (!diff) {{
            $('#auditItemsContainer').html('<div style="text-align:center; padding:30px; color:var(--text-muted);">暂无变动审计数据</div>');
            return;
        }}

        var q = ($('#auditSearchInput').val() || '').trim().toLowerCase();
        var pool = [];

        if (auditActiveType === 'all' || auditActiveType === 'added') {{
            (diff.added || []).forEach(function(x) {{
                var c = Object.assign({{}}, x, {{ _type: 'added' }});
                pool.push(c);
            }});
        }}
        if (auditActiveType === 'all' || auditActiveType === 'updated') {{
            (diff.updated || []).forEach(function(x) {{
                var c = Object.assign({{}}, x, {{ _type: 'updated' }});
                pool.push(c);
            }});
        }}
        if (auditActiveType === 'all' || auditActiveType === 'version_gained') {{
            (diff.version_gained || []).forEach(function(x) {{
                var c = Object.assign({{}}, x, {{ _type: 'version_gained' }});
                pool.push(c);
            }});
        }}
        if (auditActiveType === 'all' || auditActiveType === 'removed') {{
            (diff.removed || []).forEach(function(x) {{
                var c = Object.assign({{}}, x, {{ _type: 'removed' }});
                pool.push(c);
            }});
        }}

        // 过滤平台
        if (auditActivePlat !== 'all') {{
            pool = pool.filter(function(x) {{ return x.platform === auditActivePlat; }});
        }}

        // 过滤关键词
        if (q) {{
            pool = pool.filter(function(x) {{
                var txt = ((x.title || '') + ' ' + (x.author || '') + ' ' + (x.version || '')).toLowerCase();
                return txt.indexOf(q) !== -1;
            }});
        }}

        if (!pool.length) {{
            var hasAnyChange = (diff.added || []).length + (diff.updated || []).length + (diff.version_gained || []).length + (diff.removed || []).length;
            var emptyMsg = hasAnyChange
                ? '没有匹配到符合条件的变动条目'
                : '本次抓取未检测到变动，与上次快照完全一致';
            $('#auditItemsContainer').html('<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:0.9rem;">' + emptyMsg + '</div>');
            return;
        }}

        var platNames = {{
            mcmod: {{ name: 'MC百科', color: '#2563eb', icon: '📦' }},
            bilibili: {{ name: '哔哩哔哩', color: '#fb7299', icon: '📺' }},
            bbsmc: {{ name: 'BBSMC', color: '#00af5c', icon: '💎' }},
            xyebbs: {{ name: 'XYEBBS', color: '#16a34a', icon: '🍃' }},
            modrinth: {{ name: 'Modrinth', color: '#1bd96a', icon: '🌐' }},
            curseforge: {{ name: 'CurseForge', color: '#f16436', icon: '🔥' }}
        }};

        var html = '';
        pool.forEach(function(item) {{
            var pInfo = platNames[item.platform] || {{ name: item.platform, color: '#64748b', icon: '🧩' }};
            var typeBadge = '';
            if (item._type === 'added') {{
                typeBadge = '<span style="background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:700;">🟢 新增收录</span>';
            }} else if (item._type === 'updated') {{
                typeBadge = '<span style="background:rgba(59,130,246,0.15); color:#3b82f6; border:1px solid rgba(59,130,246,0.3); padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:700;">🔵 版本更新</span>';
            }} else if (item._type === 'version_gained') {{
                typeBadge = '<span style="background:rgba(245,158,11,0.15); color:#f59e0b; border:1px solid rgba(245,158,11,0.3); padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:700;">🆕 补全版本信息</span>';
            }} else {{
                typeBadge = '<span style="background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:700;">🔴 移除下架</span>';
            }}

            var diffDetailHtml = '';
            if (item.diff_details && item.diff_details.length) {{
                diffDetailHtml = '<div style="font-size:0.75rem; color:#f59e0b; margin-top:2px;">' + auditEsc(item.diff_details.join(' · ')) + '</div>';
            }}

            var safeTitle = auditEsc(item.title || '');
            var safeAuthor = auditEsc(item.author || '未知');
            var safeVer = auditEsc(item.version || '未知版本');

            html += '<div class="audit-item-row">';
            html += '  <div style="flex:1; min-width:0;">';
            html += '    <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">';
            html += '      ' + typeBadge;
            html += '      <span style="font-size:0.75rem; color:' + pInfo.color + '; font-weight:700;">' + pInfo.icon + ' ' + pInfo.name + '</span>';
            html += '      <span style="font-size:0.75rem; color:var(--text-muted);">' + (item.date || '') + '</span>';
            html += '    </div>';
            html += '    <div style="font-weight:700; font-size:0.92rem; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="' + safeTitle + '">' + safeTitle + '</div>';
            html += '    <div style="font-size:0.78rem; color:var(--text-muted); display:flex; gap:12px; margin-top:2px;">';
            html += '      <span>作者: <b style="color:var(--text);">' + safeAuthor + '</b></span>';
            html += '      <span>版本: <b style="color:var(--primary);">' + safeVer + '</b></span>';
            html += '    </div>';
            html += '    ' + diffDetailHtml;
            html += '  </div>';
            html += '  <div style="display:flex; align-items:center; gap:8px;">';
            html += '    <button type="button" class="cross-action-btn cross-btn-in js-jump-platform-search" data-platform="' + item.platform + '" data-query="' + safeTitle + '" title="在站内筛选">站内 ➔</button>';
            if (item.url) {{
                html += '    <a href="' + auditEsc(item.url) + '" target="_blank" rel="noopener noreferrer" class="cross-action-btn cross-btn-ext" title="在新标签页打开原页面">原站 ↗</a>';
            }}
            html += '  </div>';
            html += '</div>';
        }});

        $('#auditItemsContainer').html(html);
    }}

    $('#openAuditModalBtn').on('click', function() {{
        initAuditDiffModule();
        $('#auditModalOverlay').addClass('show').fadeIn(150);
    }});

    $('#auditModalClose, #auditModalOverlay').on('click', function(e) {{
        if (e.target === this || $(this).attr('id') === 'auditModalClose') {{
            $('#auditModalOverlay').removeClass('show').fadeOut(150);
        }}
    }});

    $('.audit-filter-chip').on('click', function() {{
        $('.audit-filter-chip').removeClass('active');
        $(this).addClass('active');
        auditActiveType = $(this).data('type');
        renderAuditItems();
    }});

    $('#auditPlatformSelect').on('change', function() {{
        auditActivePlat = $(this).val();
        renderAuditItems();
    }});

    $('#auditSearchInput').on('input', function() {{
        renderAuditItems();
    }});

    setTimeout(initAuditDiffModule, 200);

        }}, 10); // 延迟初始化，避免打开文件时阻塞浏览器
}});
</script>
<!-- 📊 数据抓取变动审计与生态监控模态窗 -->
<!-- ─── 全平台通用的「版本发布与更新日志」模态窗 ───
     注意：必须留在 body 级。原先它嵌在 #view-mcmod 内部，
     切到 B站/BBSMC/XYEBBS/Modrinth/CurseForge 页签时 #view-mcmod 会 display:none，
     导致弹窗虽然被 JS 打开却完全不可见（实测 rect 0x0）。
     同理 #mcmodPickerModal 也一并提升到 body 级。 -->
<div id="versionModalOverlay" class="version-modal-overlay" style="display:none;">
    <div class="version-modal-card">
        <div class="version-modal-header">
            <div class="version-modal-header-left">
                <span class="version-modal-badge">📜 版本发布与更新日志</span>
                <h3 class="version-modal-title" id="versionModalTitle">整合包更新日志</h3>
                <div class="version-modal-meta" id="versionModalMeta">
                    <span id="versionModalVer" class="version-meta-tag">最新版本: --</span>
                    <span id="versionModalDate" class="version-meta-tag">更新时间: --</span>
                    <span id="versionModalCount" class="version-meta-tag">累计发布: -- 个版本</span>
                </div>
            </div>
            <div class="version-modal-header-right">
                <a id="versionModalExtLink" href="#" target="_blank" rel="noreferrer" class="version-modal-ext-btn" title="在新标签页打开官方原网页">在新窗口打开 ↗</a>
                <button type="button" class="hover-close version-modal-close-btn" id="versionModalClose" title="关闭 (Esc)">✕</button>
            </div>
        </div>
        <div class="version-modal-body" style="padding: 24px; overflow-y: auto; flex: 1;">
            <div id="versionModalLoading" class="version-modal-loading" style="display:none;">
                <div class="version-modal-spinner"></div>
                <span>正在加载...</span>
            </div>
            <div id="versionModalBodyInner"></div>
        </div>
    </div>
</div>
<dialog id="mcmodPickerModal" class="picker-modal" aria-labelledby="pickerModalTitle">
    <div class="picker-modal-top">
        <span class="picker-modal-eyebrow" id="pickerModalEyebrow">MCMOD DISCOVERY</span>
        <button type="button" class="picker-close-btn" id="closePickerModal" aria-label="关闭弹窗">✕</button>
    </div>
    <div id="pickerModalBody"></div>
</dialog>
<div id="auditModalOverlay" class="audit-modal-overlay" style="display:none;">
    <div class="version-modal-card" style="max-width:980px; width:95%; max-height:88vh; display:flex; flex-direction:column; background:var(--glass-bg-solid, #1e293b); border:1px solid var(--glass-border, #334155); border-radius:18px; padding:22px; box-shadow:0 24px 70px rgba(0,0,0,0.5);">
        <div class="version-modal-header" style="display:flex; align-items:center; justify-content:space-between; padding-bottom:14px; border-bottom:1px solid var(--border-color, rgba(255,255,255,0.1));">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="font-size:1.6rem; background:rgba(59,130,246,0.15); width:42px; height:42px; border-radius:10px; display:flex; align-items:center; justify-content:center;">📊</div>
                <div>
                    <h3 style="margin:0 0 4px; font-size:1.2rem; font-weight:700;">数据抓取变动审计与生态监控</h3>
                    <div style="font-size:0.8rem; color:var(--text-muted, #94a3b8); display:flex; gap:14px;">
                        <span id="auditGenTime">📅 对比时间: 刚刚</span>
                        <span id="auditTotalScope">📦 全网监测规模: 73,521 款</span>
                    </div>
                </div>
            </div>
            <button type="button" class="hover-close version-modal-close-btn" id="auditModalClose" title="关闭 (Esc)" style="border:0; background:transparent; font-size:1.4rem; cursor:pointer; color:var(--text-muted);">✕</button>
        </div>
        
        <!-- 统计 KPI 胶囊栏 -->
        <div class="audit-kpi-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(160px, 1fr)); gap:12px; margin:16px 0;">
            <div style="background:rgba(16,185,129,0.08); border:1px solid rgba(16,185,129,0.25); border-radius:10px; padding:12px 14px;">
                <div style="font-size:0.75rem; color:#10b981; font-weight:600; margin-bottom:4px;">🟢 新增整合包</div>
                <div style="font-size:1.4rem; font-weight:800; color:#10b981;" id="kpiAuditAdded">0</div>
            </div>
            <div style="background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.25); border-radius:10px; padding:12px 14px;">
                <div style="font-size:0.75rem; color:#3b82f6; font-weight:600; margin-bottom:4px;">🔵 版本/时间更新</div>
                <div style="font-size:1.4rem; font-weight:800; color:#3b82f6;" id="kpiAuditUpdated">0</div>
            </div>
            <div style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.25); border-radius:10px; padding:12px 14px;">
                <div style="font-size:0.75rem; color:#f59e0b; font-weight:600; margin-bottom:4px;">🆕 补全版本信息</div>
                <div style="font-size:1.4rem; font-weight:800; color:#f59e0b;" id="kpiAuditGained">0</div>
            </div>
            <div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25); border-radius:10px; padding:12px 14px;">
                <div style="font-size:0.75rem; color:#ef4444; font-weight:600; margin-bottom:4px;">🔴 移除/下架</div>
                <div style="font-size:1.4rem; font-weight:800; color:#ef4444;" id="kpiAuditRemoved">0</div>
            </div>
            <div style="background:rgba(139,92,246,0.08); border:1px solid rgba(139,92,246,0.25); border-radius:10px; padding:12px 14px;">
                <div style="font-size:0.75rem; color:#8b5cf6; font-weight:600; margin-bottom:4px;">⚡ 监测总条目</div>
                <div style="font-size:1.4rem; font-weight:800; color:#8b5cf6;" id="kpiAuditTotal">73,521</div>
            </div>
        </div>

        <!-- 审计筛选工具栏 -->
        <div class="audit-filter-bar" style="display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:14px; padding-bottom:12px; border-bottom:1px solid var(--border-color, rgba(255,255,255,0.1));">
            <div class="audit-type-tabs" style="display:inline-flex; gap:6px;">
                <button type="button" class="audit-filter-chip active" data-type="all">全部变动 (<span id="cntAllDiff">0</span>)</button>
                <button type="button" class="audit-filter-chip" data-type="added">🟢 仅看新增 (<span id="cntAddedDiff">0</span>)</button>
                <button type="button" class="audit-filter-chip" data-type="updated">🔵 仅看更新 (<span id="cntUpdatedDiff">0</span>)</button>
                <button type="button" class="audit-filter-chip" data-type="version_gained">🆕 仅看补全 (<span id="cntGainedDiff">0</span>)</button>
                <button type="button" class="audit-filter-chip" data-type="removed">🔴 仅看下架 (<span id="cntRemovedDiff">0</span>)</button>
            </div>
            <select id="auditPlatformSelect" class="hub-select" style="padding:5px 10px; font-size:0.8rem; border-radius:8px; border:1px solid var(--border-color, rgba(255,255,255,0.15)); background:var(--bg-card, #1e293b); color:var(--text, #fff);">
                <option value="all">🌐 全部平台</option>
                <option value="mcmod">📦 MC百科</option>
                <option value="bilibili">📺 哔哩哔哩</option>
                <option value="bbsmc">💎 BBSMC</option>
                <option value="xyebbs">🍃 XYEBBS</option>
                <option value="modrinth">🌐 Modrinth</option>
                <option value="curseforge">🔥 CurseForge</option>
            </select>
            <input type="text" id="auditSearchInput" placeholder="搜索变动整合包名称或作者..." style="flex:1; min-width:180px; padding:6px 12px; font-size:0.82rem; border-radius:8px; border:1px solid var(--border-color, rgba(255,255,255,0.15)); background:var(--bg-input, rgba(0,0,0,0.2)); color:var(--text,#fff);">
        </div>

        <!-- 变动条目列表容器 -->
        <div id="auditItemsContainer" style="flex:1; overflow-y:auto; max-height:480px; display:flex; flex-direction:column; gap:8px; padding-right:6px;">
        </div>
    </div>
</div>

<button id="feedbackOpen" class="feedback-fab" type="button" title="意见反馈（维护升级中）">💬</button>
<div id="feedbackModal" class="feedback-modal" role="dialog" aria-modal="true" aria-label="意见反馈">
  <div class="feedback-panel">
    <h3>意见反馈</h3>
    <label for="feedbackType">反馈类型</label><select id="feedbackType"><option>功能建议</option><option>问题反馈</option><option>数据纠错</option><option>其他</option></select>
    <label for="feedbackContent">反馈内容</label><textarea id="feedbackContent" placeholder="请尽量说明使用场景或复现步骤"></textarea>
    <label for="feedbackContact">联系方式（可选）</label><input id="feedbackContact" placeholder="邮箱、QQ 或其他联系方式">
    <div id="feedbackStatus"></div><div class="feedback-actions"><button id="feedbackCancel" type="button">取消</button><button id="feedbackSubmit" type="button">提交</button></div>
  </div>
</div>
</body>
</html>'''

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
    return PRETTY_TEMPLATE.format(
        title=title, cat_opts=cat_opts, pack_opts=pack_opts, type_opts=type_opts,
        trend_opts=trend_opts,
        mod_cat_opts=mod_cat_opts, mod_opts=mod_opts, rows=rows_html,
        total=total, total_views=total_views_str, total_comments=total_comments_str,
        desc_json=desc_json_str,
        comment_json=comment_json_str,
        feedback_url_json=json.dumps(FEEDBACK_URL, ensure_ascii=False),
        app_version=APP_VERSION,
        comment_api_base_json=json.dumps(comment_api_base, ensure_ascii=False),
        dashboard_api_base_json=json.dumps(comment_api_base, ensure_ascii=False),
        compare_json=compare_json_str,
        mod_detail_json=mod_detail_json_str,
        theme_warm=THEMES["warm"]["root"],
        theme_dark=THEMES["dark"]["root"],
        theme_light=THEMES["light"]["root"],
        theme_eye=THEMES["eye"]["root"],
        theme_pink=THEMES["pink"]["root"],
        theme_anime=THEMES["anime"]["root"],
        default_theme=theme_name,
    ), comment_data, rows_html, mod_detail_data


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
