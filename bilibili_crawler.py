#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
====================================================================
  Bilibili (B站) Minecraft 整合包专版采集引擎 v2.0
====================================================================
特性：
1. 轻量高并发 WBI API 接口（支持免登或一键扫码登录，毫秒级响应）
2. 多关键词矩阵检索（整合包发布 / 整合包更新 / MC整合包发布 / 整合包公测）
3. 深入提取视频简介与 UP 主置顶评论（防吞防折叠）
4. 深度中文实体抽取（MC版本、Loader、各类网盘链接、提取码、QQ群号、模组数）
5. 官方与 AI 语音识别字幕自动抓取与口播全文解析
6. 自动剔除纯实况解说噪音视频
7. 同时产出 JSON 数据与前端直接加载的 JS 数据源（bili_data.js）
8. 支持一键回车全量抓取、断点识别与多版本聚合
"""

import os
import sys
import re
import time
import json
import random
import argparse
import urllib.request
import urllib.parse
from hashlib import md5
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from desktop_collection_contract import write_collection_result

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/',
}

def get_mixin_key(orig: str) -> str:
    return ''.join([orig[i] for i in MIXIN_KEY_ENC_TAB if i < len(orig)])[:32]

def enc_wbi(params: dict, img_key: str, sub_key: str) -> dict:
    mixin_key = get_mixin_key(img_key + sub_key)
    params['wts'] = round(time.time())
    params = dict(sorted(params.items()))
    params = {
        k: ''.join(filter(lambda chr: chr not in "!'()*", str(v)))
        for k, v in params.items()
    }
    query = urllib.parse.urlencode(params)
    params['w_rid'] = md5((query + mixin_key).encode()).hexdigest()
    return params


class BiliAuth:
    """B站扫码登录与凭据持久化管理"""
    REPO_ROOT = os.path.abspath(
        os.environ.get("MC_DESKTOP_WORKSPACE")
        or os.path.dirname(os.path.abspath(__file__))
    )
    COOKIE_FILE = os.path.join(REPO_ROOT, "crawler_output", "bilibili_cookies.json")

    @classmethod
    def load_cookie_str(cls) -> str:
        if os.path.exists(cls.COOKIE_FILE):
            try:
                with open(cls.COOKIE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data.get("raw_cookie_str", "")
                    elif isinstance(data, str):
                        return data
            except Exception:
                pass
        return ""

    @classmethod
    def check_login_status(cls, cookie_str: str = "") -> Dict[str, Any]:
        if not cookie_str:
            cookie_str = cls.load_cookie_str()
        headers = dict(HEADERS)
        if cookie_str:
            headers['Cookie'] = cookie_str
        try:
            req = urllib.request.Request('https://api.bilibili.com/x/web-interface/nav', headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                if res.get('code') == 0 and res.get('data', {}).get('isLogin', False):
                    data = res['data']
                    return {
                        "is_login": True,
                        "uname": data.get("uname", ""),
                        "mid": data.get("mid", 0),
                        "level": data.get("level_info", {}).get("current_level", 0)
                    }
        except Exception:
            pass
        return {"is_login": False}

    @classmethod
    def login_qr_interactive(cls) -> bool:
        print("\n" + "=" * 65)
        print("  📱 哔哩哔哩 Web 扫码授权登录")
        print("=" * 65)
        status = cls.check_login_status()
        if status.get("is_login"):
            print(f"  [√] 当前已处于登录状态: 【{status['uname']}】 (UID: {status['mid']} | Lv.{status['level']})")
            try:
                re_login = input("  是否需要重新扫码更换账号? [y/N]: ").strip().lower()
                if re_login not in ('y', 'yes'):
                    return True
            except (EOFError, KeyboardInterrupt):
                return True

        print("  -> 正在向 B站 请求扫码凭据...")
        try:
            req = urllib.request.Request('https://passport.bilibili.com/x/passport-login/web/qrcode/generate', headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                if res.get('code') != 0:
                    print(f"  [!] 获取二维码失败: {res.get('message', '未知错误')}")
                    return False
                qr_url = res['data']['url']
                qr_key = res['data']['qrcode_key']
        except Exception as e:
            print(f"  [!] 网络请求异常: {e}")
            return False

        # 生成图片和控制台二维码
        try:
            import qrcode
            qr = qrcode.QRCode()
            qr.add_data(qr_url)
            qr.make(fit=True)

            out_dir = os.path.dirname(cls.COOKIE_FILE)
            os.makedirs(out_dir, exist_ok=True)
            qr_img_path = os.path.join(out_dir, "bilibili_login_qr.png")
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(qr_img_path)

            print(f"  [√] 二维码已保存至: {qr_img_path}")
            if sys.platform == "win32":
                try:
                    os.startfile(qr_img_path)
                    print("  [√] 已调用系统图片查看器打开二维码窗口！")
                except Exception:
                    pass

            print("\n  👉 终端字符二维码 (如无法显示请扫描弹出的图片)：")
            try:
                qr.print_ascii(invert=True)
            except Exception:
                pass
        except Exception:
            pass

        print(f"\n  🔗 移动端扫码 / 浏览器打开授权链接:")
        print(f"     {qr_url}")
        print("\n  ⏳ 等待扫码中（请使用 哔哩哔哩手机客户端 扫码，有效时间 180 秒）...")

        poll_url = f'https://passport.bilibili.com/x/passport-login/web/qrcode/poll?qrcode_key={qr_key}'
        start_time = time.time()
        while time.time() - start_time < 180:
            try:
                req = urllib.request.Request(poll_url, headers=HEADERS)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    pdata = json.loads(resp.read().decode('utf-8'))
                    code = pdata.get('data', {}).get('code')
                    if code == 0:
                        cookie_headers = resp.headers.get_all('Set-Cookie', [])
                        cookie_dict = {}
                        for sc in cookie_headers:
                            part = sc.split(';')[0]
                            if '=' in part:
                                k, v = part.split('=', 1)
                                cookie_dict[k.strip()] = v.strip()

                        raw_str = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
                        save_data = {
                            "updated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                            "raw_cookie_str": raw_str,
                            "cookies": cookie_dict
                        }
                        out_dir = os.path.dirname(cls.COOKIE_FILE)
                        os.makedirs(out_dir, exist_ok=True)
                        with open(cls.COOKIE_FILE, "w", encoding="utf-8") as f:
                            json.dump(save_data, f, ensure_ascii=False, indent=2)

                        st = cls.check_login_status(raw_str)
                        name = st.get('uname', 'B站用户')
                        print("\n" + "=" * 65)
                        print(f"  🎉 登录成功！欢迎，【{name}】 (UID: {st.get('mid')} | Lv.{st.get('level')})")
                        print(f"  Cookies 已自动存盘至: {cls.COOKIE_FILE}")
                        print("=" * 65 + "\n")
                        return True
                    elif code == 86090:
                        sys.stdout.write("\r  📱 已扫码，请在手机上点击确认登录...")
                        sys.stdout.flush()
                    elif code == 86101:
                        sys.stdout.write("\r  ⏳ 等待扫描二维码...")
                        sys.stdout.flush()
                    elif code == 86038:
                        print("\n  ❌ 二维码已失效/超时，请重新尝试。")
                        return False
            except Exception:
                pass
            time.sleep(1.6)
        print("\n  ❌ 扫码超时已退出。")
        return False


class BiliModpackCrawler:
    def __init__(self):
        self.stats = {"requests": 0, "successful": 0, "failed": 0, "errors": [], "pages_completed": 0}
        self.img_key = ""
        self.sub_key = ""
        self.cookie_str = BiliAuth.load_cookie_str()
        self.headers = dict(HEADERS)
        if self.cookie_str:
            self.headers['Cookie'] = self.cookie_str
        self._init_wbi_keys()

    def _init_wbi_keys(self):
        req = urllib.request.Request('https://api.bilibili.com/x/web-interface/nav', headers=self.headers)
        self.stats["requests"] += 1
        with urllib.request.urlopen(req, timeout=8) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            img_url = res.get('data', {}).get('wbi_img', {}).get('img_url', '')
            sub_url = res.get('data', {}).get('wbi_img', {}).get('sub_url', '')
            self.img_key = img_url.rsplit('/', 1)[1].split('.')[0]
            self.sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
            self.stats["successful"] += 1

    def search_videos(self, keyword: str, page: int = 1, page_size: int = 20, order: str = "pubdate") -> List[Dict[str, Any]]:
        params = {
            'search_type': 'video',
            'keyword': keyword,
            'page': page,
            'page_size': page_size,
            'order': order,
        }
        signed = enc_wbi(params, self.img_key, self.sub_key)
        url = 'https://api.bilibili.com/x/web-interface/wbi/search/type?' + urllib.parse.urlencode(signed)
        req = urllib.request.Request(url, headers=self.headers)
        try:
            self.stats["requests"] += 1
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('code') == 0:
                    self.stats["successful"] += 1
                    self.stats["pages_completed"] += 1
                    return data.get('data', {}).get('result', [])
                self.stats["failed"] += 1
                self.stats["errors"].append(f"search code={data.get('code')} keyword={keyword} page={page}")
        except Exception as e:
            self.stats["failed"] += 1
            self.stats["errors"].append(f"search {keyword} page={page}: {e}")
            print(f"  [!] 搜索接口请求异常: {e}")
        return []

    def get_video_detail(self, bvid: str) -> Optional[Dict[str, Any]]:
        url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
        req = urllib.request.Request(url, headers=self.headers)
        try:
            self.stats["requests"] += 1
            with urllib.request.urlopen(req, timeout=8) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                if res.get('code') == 0:
                    self.stats["successful"] += 1
                    return res.get('data')
                self.stats["failed"] += 1
                self.stats["errors"].append(f"detail code={res.get('code')} bvid={bvid}")
        except Exception as e:
            self.stats["failed"] += 1
            self.stats["errors"].append(f"detail {bvid}: {e}")
            print(f"  [!] 获取详情异常 [{bvid}]: {e}")
        return None

    def get_pinned_comment(self, aid: int) -> Dict[str, Any]:
        url = f'https://api.bilibili.com/x/v2/reply/main?type=1&oid={aid}&mode=3'
        req = urllib.request.Request(url, headers=self.headers)
        try:
            self.stats["requests"] += 1
            with urllib.request.urlopen(req, timeout=8) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                if res.get('code') == 0:
                    self.stats["successful"] += 1
                    data = res.get('data')
                    if not isinstance(data, dict) or 'top' not in data:
                        return {'message': '', 'time': '', 'ctime': 0, 'observed': False}
                    top = data.get('top') or {}
                    if not isinstance(top, dict):
                        return {'message': '', 'time': '', 'ctime': 0, 'observed': False}
                    upper_top = top.get('upper')
                    if upper_top is not None:
                        if not isinstance(upper_top, dict):
                            return {'message': '', 'time': '', 'ctime': 0, 'observed': False}
                        comment_content = upper_top.get('content')
                        if not isinstance(comment_content, dict) or not isinstance(comment_content.get('message'), str):
                            return {'message': '', 'time': '', 'ctime': 0, 'observed': False}
                        content = comment_content['message'] or ''
                        ctime = upper_top.get('ctime', 0)
                        t_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(ctime)) if ctime else ""
                        return {
                            'message': content,
                            'time': t_str,
                            'ctime': ctime,
                            'observed': True,
                        }
                    return {'message': '', 'time': '', 'ctime': 0, 'observed': True}
                else:
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"pinned code={res.get('code')} aid={aid}")
        except Exception as error:
            self.stats["failed"] += 1
            self.stats["errors"].append(f"pinned aid={aid}: {error}")
        return {'message': '', 'time': '', 'ctime': 0, 'observed': False}

    def get_video_subtitle(self, aid: int, cid: int, bvid: str = "") -> Dict[str, Any]:
        """抓取官方 CC 字幕或平台 AI 语音识别转写字幕"""
        no_subtitle = {'has_subtitle': False, 'lan_doc': '', 'subtitle_text': '', 'subtitle_summary': '', 'observed': False}
        if not aid or not cid:
            return no_subtitle
        
        params = {'aid': aid, 'cid': cid}
        if bvid:
            params['bvid'] = bvid
        signed = enc_wbi(params, self.img_key, self.sub_key)
        url = 'https://api.bilibili.com/x/player/wbi/v2?' + urllib.parse.urlencode(signed)
        req = urllib.request.Request(url, headers=self.headers)
        confirmed_no_subtitles = False
        
        try:
            self.stats["requests"] += 1
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('code') != 0:
                    self.stats["failed"] += 1
                    self.stats["errors"].append(f"subtitle code={data.get('code')} bvid={bvid}")
                    return no_subtitle
                self.stats["successful"] += 1
                subtitle_info = data.get('data', {}).get('subtitle')
                if not isinstance(subtitle_info, dict) or not isinstance(subtitle_info.get('subtitles'), list):
                    return no_subtitle
                subs = subtitle_info['subtitles']
                if not subs:
                    # 备用轻量接口
                    v2_url = f'https://api.bilibili.com/x/player/v2?aid={aid}&cid={cid}'
                    req2 = urllib.request.Request(v2_url, headers=self.headers)
                    self.stats["requests"] += 1
                    with urllib.request.urlopen(req2, timeout=5) as r2:
                        d2 = json.loads(r2.read().decode('utf-8'))
                        if d2.get('code') != 0:
                            self.stats["failed"] += 1
                            self.stats["errors"].append(f"subtitle fallback code={d2.get('code')} bvid={bvid}")
                            return no_subtitle
                        self.stats["successful"] += 1
                        fallback_info = d2.get('data', {}).get('subtitle')
                        if not isinstance(fallback_info, dict) or not isinstance(fallback_info.get('subtitles'), list):
                            return no_subtitle
                        subs = fallback_info['subtitles']
                        confirmed_no_subtitles = not subs

                if subs:
                    chosen = None
                    for s in subs:
                        lan = s.get('lan', '')
                        if 'zh' in lan or 'ai' in lan or 'cn' in lan:
                            chosen = s
                            break
                    if not chosen:
                        chosen = subs[0]
                    
                    sub_url = chosen.get('subtitle_url', '')
                    if sub_url:
                        if sub_url.startswith('//'):
                            sub_url = 'https:' + sub_url
                        sub_req = urllib.request.Request(sub_url, headers=self.headers)
                        self.stats["requests"] += 1
                        with urllib.request.urlopen(sub_req, timeout=6) as sub_resp:
                            sub_json = json.loads(sub_resp.read().decode('utf-8'))
                            if not isinstance(sub_json, dict) or not isinstance(sub_json.get('body'), list):
                                return no_subtitle
                            self.stats["successful"] += 1
                            body = sub_json['body']
                            lines = [item.get('content', '').strip() for item in body if item.get('content')]
                            full_sub_text = ' '.join(lines)
                            summary = full_sub_text[:280] + ('...' if len(full_sub_text) > 280 else '')
                            return {
                                'has_subtitle': True,
                                'lan_doc': chosen.get('lan_doc', '中文'),
                                'subtitle_text': full_sub_text,
                                'subtitle_summary': summary,
                                'observed': True,
                            }
                    return no_subtitle
        except Exception as error:
            self.stats["failed"] += 1
            self.stats["errors"].append(f"subtitle {bvid}: {error}")
        return {**no_subtitle, 'observed': confirmed_no_subtitles}

    @staticmethod
    def extract_modpack_info(title: str, desc: str, pinned_comment: str, subtitle_text: str = "", author: str = "", duration: str = "") -> Dict[str, Any]:
        full_text = f"{title}\n{desc}\n{pinned_comment}\n{subtitle_text}"
        
        dur_sec = 0
        if duration:
            parts = duration.split(':')
            try:
                if len(parts) == 2:
                    dur_sec = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    dur_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            except Exception:
                pass

        # 0. 核心黄金准入准则：名字包含整合包/模组包/懒人包/整合客户端，并包含行动词或版本号
        has_pack_title = bool(re.search(r'(?:整合包|模组包|懒人包|整合客户端)', title))
        has_action_title = bool(re.search(r'(?:更新|发布|首发|公测|上线|推出|自制|原创|开源|汉化版?|重[制置]版?|正式版|测试版|抢先版|先行版|体验版|出炉|完工|制作完成|分享|下载|v?\d+\.\d+(?:\.\d+)?)', title, re.I))

        # 1. 过滤纯实况录播、分集(P/EP/第X期)、解说、一口气看完
        # 避免误伤：排除分辨率如 1080P60、720P60，排除“第一次制作整合包”，排除“更新至1.2.0版本”等正常版本表述
        is_series = bool(re.search(r'(?:第\s*[0-9一二三四五六七八九十百]+\s*[集期话季篇回]|(?<![0-9a-zA-Z])(?:[Pp]|Part|EP)\.?\s*[0-9]{1,3}(?![0-9a-zA-Z]|fps|帧)|更新至\s*[Pp]\s*\d+|[（\(]更新至\s*[Pp]?\s*\d+\s*[集期])', title, re.I))
        is_let_play_commentary = bool(re.search(
            r'(?:'
            r'【[^】]*(?:实况|解说|录播)[^】]*】|'
            r'实况|'
            r'生存实况|生存记|生存日记|'
            r'一口气(?:看完|通关|肝完|爽玩)?|'
            r'(?:实况|通关|剧情|全流程|流程|深度|速通|纯享)?解说|'
            r'通关全程|'
            r'全程实况|'
            r'通关实况|'
            r'通关记录|'
            r'全流程通关|'
            r'实况全程|'
            r'纯享版|'
            r'完结撒花|'
            r'[【\[\(](?:实况|纯享|解说|录播|切片|游戏实况|通关实况|全程实况|开箱|整活)[】\]\)]|'
            r'录播|切片|'
            r'直播回放|录像回放|直播录像|录播回放|主播被迫断更|'
            r'开局(?:就)?[坐牢受难暴毙无敌神装起飞破防痛苦折磨]|'
            r'二周目|一周目|生存档|游玩记录|'
            r'纯游玩|游戏实况|游戏解说|'
            r'学玩|'
            r'试玩(?!\s*版).*?(?:模组|整合包|生存)|'
            r'整合包#\d+'
            r')', title, re.IGNORECASE
        ))
        is_let_play = is_series or is_let_play_commentary
        
        # 特别针对长篇录像/试玩实况作者
        if author == '马福' and dur_sec > 3600:
            is_let_play = True
        elif author == '籽岷' and '试玩' in title and not re.search(r'试玩版', title):
            is_let_play = True
        elif author == 'GreatCoffee' and dur_sec > 3600:
            is_let_play = True
            
        # 盘点合集与推荐榜单（若为明确的单包自制/发布/更新，不因正文中包含“推荐”而误杀）
        is_single_pack_release = bool(re.search(r'(?:自制|原创)?\s*(?:整合包|模组包)\s*(?:发布|更新|公测|首发|上线|推出|正式版|v\d+)', title, re.I))
        is_recommendation_roundup = False
        if not is_single_pack_release or re.search(r'(?:\d+|几|[一二三四五六七八九十])款', title):
            is_recommendation_roundup = bool(re.search(
                r'(?:'
                r'最全.*?(?:整合包|模组包)?推荐|'
                r'必玩[^\n，。！？!?,]{0,15}?(?:整合包|模组包)?推荐|'
                r'游玩推荐|'
                r'(?:整合包|模组包)推荐榜|'
                r'(?:整合包|模组包)盘点|'
                r'(?:整合包|模组包)合集|'
                r'(?:整合包|模组包)合辑|'
                r'(?:整合包|模组包)排行|'
                r'(?:盘点|推荐|精选)(?:\d+|几|[一二三四五六七八九十])款|'
                r'有哪些.*?(?:整合包|模组包)|'
                r'(?:整合包|模组包)漫谈|'
                r'(?:神仙|宝藏|好玩(?:的)?)(?:MC|我的世界)?整合包推荐|'
                r'^[【\[\(]?\s*(?:(?:MC|我的世界)?整合包|模组包)推荐\s*[】\]\)]?|'
                r'^[【\[\(]?\s*(?:\d+月|[一二三四五六七八九十]+月|暑[假期]|年度|最新)?\s*推荐[！!：:\s]'
                r')', title, re.IGNORECASE
            ))
            
        # 纯材质/光影/资源包识别（排除自带/内置/专属材质光影的正品整合包）
        is_texture_or_resource = False
        if re.search(r'(?:光影整合包|材质整合包|皮肤整合包|数据包整合|超强光追材质|全物品3D模型与材质|Action&Stuff|Actions&stuff|Actions?&(?:amp;)?stuff)', title, re.I):
            is_texture_or_resource = True
        elif re.search(r'^[【\[\(]?(?:材质包|光影包|资源包|皮肤包|数据包)(?:发布|分享|推荐|展示|下载)', title, re.I):
            is_texture_or_resource = True
        elif re.search(r'(?:纯数据包|数据包发布|数据包分享|材质分享|光影分享|纯材质|手感材质|PVP材质|光影推荐|材质推荐|纹理包|皮肤包)', title, re.I):
            if re.search(r'(?:整合包|模组包)', title) and re.search(r'(?:自带|内置|附带|包含|搭载|专属|搭配|配有|配带|含).*?(?:材质|光影|资源)', title):
                is_texture_or_resource = False
            else:
                is_texture_or_resource = True
        elif re.search(r'(?:材质包|光影包|资源包)$', title) and not re.search(r'(?:整合包|模组包)', title):
            is_texture_or_resource = True
        
        # 2. 识别 MC 版本
        versions = re.findall(r'(?<![0-9.])1\.(?:21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|2)(?:\.\d+)?(?![0-9.])', full_text)
        seen = set()
        clean_versions = [v for v in versions if not (v in seen or seen.add(v))]
        
        # 3. 识别 Loader
        loaders = re.findall(r'(?i)(?<![a-zA-Z0-9])(neoforge|fabric|forge|quilt)(?![a-zA-Z0-9])', full_text)
        loaders_clean = list(set([l.capitalize() for l in loaders]))

        # 4. 识别网盘与下载链接（增强对短域名与历史链接的识别）
        download_links = []
        pan_patterns = [
            ("百度网盘", r'https?://pan\.baidu\.com/(?:s/[a-zA-Z0-9_\-]+|share/init\?surl=[a-zA-Z0-9_\-]+)'),
            ("夸克网盘", r'https?://pan\.quark\.cn/s/[a-zA-Z0-9_\-]+'),
            ("123云盘", r'https?://(?:www\.)?(?:123pan|123684|123865|123912)\.com/s/[a-zA-Z0-9_\-]+'),
            ("蓝奏云", r'https?://[a-zA-Z0-9_\-]+\.(?:lanzou[a-z]?|lanzn|lanzo)\.com/[a-zA-Z0-9_\-]+'),
            ("阿里云盘", r'https?://www\.(?:aliyundrive|alipan)\.com/s/[a-zA-Z0-9_\-]+'),
            ("迅雷云盘", r'https?://pan\.xunlei\.com/s/[a-zA-Z0-9_\-]+'),
            ("腾讯微云", r'https?://share\.weiyun\.com/[a-zA-Z0-9_\-]+'),
            ("GitHub", r'https?://github\.com/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+/(?:releases|archive)[^\s，,。\n]*'),
            ("CurseForge", r'https?://(?:www\.)?curseforge\.com/minecraft/modpacks/[a-zA-Z0-9_\-]+'),
            ("Modrinth", r'https?://modrinth\.com/modpack/[a-zA-Z0-9_\-]+'),
            ("MC百科", r'https?://www\.mcmod\.cn/modpack/\d+\.html'),
            ("星原社区", r'https?://www\.xyebbs\.com/resources/\d+'),
            ("QQ频道", r'https?://pd\.qq\.com/g/[a-zA-Z0-9_\-]+'),
            ("B站直达短链", r'https?://b23\.tv/[a-zA-Z0-9%\-_?=&]+'),
            ("磁力链接", r'magnet:\?xt=urn:btih:[a-zA-Z0-9]+'),
            ("外链下载", r'https?://[a-zA-Z0-9_\-\.]+\.(?:top|cn|com|net|org|xyz)/[a-zA-Z0-9_\-/\.]+'),
        ]
        for pan_name, pat in pan_patterns:
            matches = re.findall(pat, full_text)
            for m in matches:
                if not any(x in m for x in ['bilibili.com', 'hdslb.com', 'rainyun.com']):
                    if m not in [x['url'] for x in download_links]:
                        download_links.append({"type": pan_name, "url": m})

        # 5. 提取码/密码
        pwd_match = re.search(r'(?:提取码|密码|访问码|解压码|提取|pwd|code)[:：\s]*([a-zA-Z0-9]{4,8})', full_text, re.IGNORECASE)
        extract_code = pwd_match.group(1) if pwd_match else ""

        # 6. QQ 群号
        qq_match = re.search(r'(?<!\d)(?:QQ群|交流群|内测群|粉丝群|玩家群|群号?|官方群)[:：\s]*([0-9]{6,12})(?!\d)', full_text)
        qq_group = qq_match.group(1) if qq_match else ""

        # 7. 模组数量
        mod_count_match = re.search(r'(?:模组数量|mod数量|模组数|包含)[:：\s]*(\d+)', full_text, re.IGNORECASE)
        mod_count = mod_count_match.group(1) if mod_count_match else ""

        # 8. 分类与标签打标
        categories = []
        cat_keywords = [
            ("科技", ["科技", "工业", "无中生有", "机械", "格雷", "ae2", "应用能源", "热力"]),
            ("魔法", ["魔法", "植物魔法", "神秘", "血魔法", "铁魔法", "巫术"]),
            ("冒险", ["冒险", "地牢", "遗迹", "rpg", "探索", "交错次元", "暮色"]),
            ("宝可梦", ["宝可梦", "神奇宝贝", "方可梦", "pixelmon", "cobblemon"]),
            ("空岛", ["空岛", "海岛", "石头世界", "单方块", "贫瘠"]),
            ("末日/生存", ["末日", "丧尸", "行尸走肉", "生化", "灾变", "寄生虫", "极限生存", "硬核"]),
            ("战斗/枪械", ["枪械", "射击", "塔科夫", "拔刀剑", "大太刀", "动作", "战斗爽"]),
            ("魔改", ["魔改", "专家", "魔改科技", "合成魔改", "任务线", "魔改线"]),
            ("休闲/建筑", ["休闲", "养老", "装饰", "建筑", "农业", "烹饪", "美食", "农夫乐事"]),
        ]
        text_lower = full_text.lower()
        for cat_name, kw_list in cat_keywords:
            if any(kw in text_lower for kw in kw_list):
                categories.append(cat_name)

        # 简介中表明作者另有其人，且当前UP未提供任何网盘与QQ群（纯解说/测评/借包试玩）
        if not download_links and not qq_group:
            cred = re.search(r'(?:整合包)?(?:原?作者|制作人|制作者)\s*[:：]\s*@([^\s，,。\n]+)', desc)
            if cred:
                c_name = cred.group(1).strip()
                if author and c_name.lower() not in author.lower() and author.lower() not in c_name.lower():
                    is_let_play = True
            # 简介中若出现“整合包宣传/发布/原视频: BV...”，且没有提供网盘/群号，说明当前视频是借包试玩
            if re.search(r'整合包(?:宣传|发布|原|原版)?视频\s*[:：]\s*(?:https?://[^\s]+|BV[a-zA-Z0-9]+)', desc, re.I):
                is_let_play = True

        # 9. 过滤虚假推销营销、私信引流骗流、机器批量账号、空壳假包、枪包/武器包、服务器发布/宣传、模型包、非MC软件
        is_spam_bait = False
        spam_reason = ""
        # 9.00 过滤求整合包/向观众求推荐
        if re.search(r'(?:有没有.*?推荐我玩|求整合包推荐|求个整合包|有什么.*?整合包推荐我玩|推荐我玩啊|谁有.*?整合包|大家有没有.*?整合包|有没有什么整合包推荐)', title):
            is_spam_bait = True
            spam_reason = "求整合包推荐"
        # 9.01 过滤单模组/插件/数据包/管理器
        elif re.search(r'(?:模组码|已加入整合包|迁移管理器|女仆档案|单模组|单个模组)', title):
            is_spam_bait = True
            spam_reason = "单模组/工具"
        # 9.02 过滤延期道歉说明/补偿公告
        elif re.search(r'(?:道歉！说明！补偿|关于整合包发布.*?道歉|整合包发布.*?延期|整合包延期发布)', title):
            is_spam_bait = True
            spam_reason = "延期道歉说明"
        # 9.03 过滤伪整合包/地图码
        elif re.search(r'伪整合包', title):
            is_spam_bait = True
            spam_reason = "伪整合包"
        # 9.04 过滤纯画饼/未发布/仅情报/进度汇报/开发日志/更新前瞻（且无有效下载与群号）
        elif not download_links and not qq_group and re.search(r'(?:画饼|更新进度|可公开情报|开发日志|即将发布|发布前瞻|更新前瞻)', title):
            is_spam_bait = True
            spam_reason = "纯画饼/未发布/无包"
        # 9.05 过滤私信骗粉引流（若已公开发布有效网盘直链，则不误伤正常交流留言）
        elif not download_links and re.search(r'(?:私信(?:自动)?回复|自动私信|主动私信|私信发给你|打开和我的对话框|评论区(?:截图)?留言[，,、\s]*(?:私信|私发|获取|领取|发你|发链接|自动回复)|回复["\'“”][^"\'“”]{1,10}["\'“”].*?私信|点个免费三连关注\+一定要看完视频|请勿拖[拽动]进度条|三连\+点个关注\+私信|快点关注到\d+可以自动发|关注卡卡er|链接不发.*?私信才会发|关注后私聊获取|真的有东西的|必须要三连|关注后看后台私信|私信才会发文件|首次发布整合包.*?不要白嫖|关注并回复.*?私聊|关注后回复["\'“”]?整合["\'“”]?)', full_text, re.I):
            is_spam_bait = True
            spam_reason = "私信引流"
        elif re.search(r'(?:(?:三端|双端|安卓\+)?(?:PC\+)?iOS(?:\+手机|\+安卓|\+PC)?(?:三端)?直装|iOS直装|三端PC\+iOS|全CG(?:动态)?|3000\+娘化|3000多只娘化|动漫娘化|娘化内容|娘化宝可梦|全清凉mod|爆衣皮肤|无限内购|手机\+PC双端(?:直装|分享)|手机/电脑都可玩\s*全互通|保姆级安卓\+联机教程~~附地址|天花板\d+\.\d+版本|最强最好玩顶级\d+\.\d+版本|无偿速存|火速存起来|免费白嫖啦|手慢真会错过|入坑血赚|玩嗨了！！！)', full_text, re.I):
            is_spam_bait = True
            spam_reason = "虚假双端/低俗吸睛"
        elif (re.match(r'^bili_\d{7,}$', author) or
              re.match(r'^[a-z]{10,}$', author) or
              re.match(r'^[a-zA-Z0-9][\u4e00-\u9fa5]{2,6}[a-zA-Z0-9]{4,}$', author) or
              re.match(r'^[\u4e00-\u9fa5]{2}\d[A-Z]-[\u4e00-\u9fa5]{2}$', author) or
              author in ['梦灵神奇宝贝', '我的世界神奇宝贝屁王', '我的世界旺仔', '我的世界神奇宝贝花火', '我的世界神奇宝贝阿宇', '我的世界神奇宝贝樱木',
                         '山白嗄', '是山白呀', '世傲吖', '我的世界神奇宝贝君', '我的世界宝可梦呆呆',
                         '姐姐比我小两岁', '口袋觉醒后台板', '我的世界方块宝可梦one']):
            is_spam_bait = True
            spam_reason = "机器账号/推销号"
        elif not download_links and not qq_group and not desc.strip().replace('-', '').replace('无', ''):
            if re.search(r'(?:附地址|附带安装|双端直装|免费分享|全网最新|懒人整合包|解压即玩|火速存|无偿速存|自取)', title):
                if re.search(r'(?:【.*?】.*?分享[！!~]|双端|保姆级|最新分享|懒人版)', title):
                    is_spam_bait = True
                    spam_reason = "空壳骗流"
        # 9.0 过滤未发布/仅演示/画饼视频与极短空壳预告（排除“无下载限制/门槛”等正规高速网盘特性）
        elif re.search(r'(?:仅(?:演示|预览|展示)|未发布|暂未发布|未放出|暂不发布|不分享|暂无链接|纯演示|无下载(?!(?:限制|门槛|限速|速度限制)))', title):
            is_spam_bait = True
            spam_reason = "未发布/仅演示预览"
        elif 0 < dur_sec <= 15 and not download_links and not qq_group and re.search(r'(?:前瞻|预告|更新计划|战争地带发布)', title):
            is_spam_bait = True
            spam_reason = "超短空壳预告"
        # 9.1 非 MC 游戏/软件/AI整合包与其他独立单机大作/硬件固件
        # 9.1.0 绝对非MC独立软件/游戏/掌机固件（完全不属于MC生态）
        elif re.search(r'(?:明末|渊虚之羽|守望先锋|斗阵特攻|overwatch|lspdfr|侏罗纪世界进化|动物园之星|(?:switch|ns版).*?(?:大气层|特斯拉|超频|金手指|破解)|天马(?:\d+|前端|模拟器)|【致命解药】|致命解药.*?整合包)', title, re.I):
            is_spam_bait = True
            spam_reason = "非MC游戏/独立软件/硬件固件"
        elif re.search(r'(?:ai绘画|stable\s*diffusion|sd\s*webui|comfyui|msst.*?webui).*?(?:整合包|一键包)|(?:整合包|一键包).*?(?:ai绘画|stable\s*diffusion|comfyui)', title, re.I):
            is_spam_bait = True
            spam_reason = "AI工具整合包"
        # 9.1.1 其他单机大作（如艾尔登法环、泰拉瑞亚、辐射、赛博朋克等常作为MC整合包魔改主题）
        # 仅在全文完全无MC标识且无网盘/群号下载时才作为外游拦截，避免误杀MC二创整合包
        elif re.search(r'(?:七日杀|艾尔登法环|老头环|荒野大镖客|赛博朋克|辐射4|上古卷轴|天际线|都市天际线|模拟人生|博德之门|生化危机|暗黑破坏神|文明6|群星|十字军之王|骑马与砍杀|黑神话|幻兽帕鲁|palworld|泰拉瑞亚|terraria|星露谷|stardew|饥荒|巫师3|只狼|gta5|gta6|侠盗猎车)', full_text, re.I):
            has_mc_context = bool(re.search(r'(?i)(?:我的世界|minecraft|方块|网易mc|forge|fabric|neoforge|quilt|rlcraft|gtnh|gregtech|pcl|hmcl|curseforge|modrinth|(?:^|[^a-zA-Z0-9])mc(?:[^a-zA-Z0-9]|$)|mc整合|mc模组|mc发布|mc版本|1\.(?:21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|2))', full_text))
            if not has_mc_context and not download_links and not qq_group:
                is_spam_bait = True
                spam_reason = "非MC单机游戏"
        # 9.1.1 必须符合 Minecraft 正向特征 (标题或全文包含MC核心标识，或包含经典MC版本号)
        elif not download_links and not qq_group and not bool(re.search(r'(?i)(?:我的世界|minecraft|方块|网易mc|forge|fabric|neoforge|quilt|rlcraft|gtnh|gregtech|pcl|hmcl|curseforge|modrinth|(?:^|[^a-zA-Z0-9])mc(?:[^a-zA-Z0-9]|$)|mc整合|mc模组|mc发布|mc版本)', full_text)) and not bool(re.search(r'(?<![0-9.])1\.(?:21|20|19|18|17|16|15|14|13|12|11|10|9|8|7|6|5|4|2)(?:\.\d+)?(?![0-9.])', full_text)):
            is_spam_bait = True
            spam_reason = "无MC标识且无版本号"
        # 9.1.2 过滤教程 / 存档迁移
        elif re.search(r'(?:如何迁移存档|迁移存档|宁然一隅整合包更新教程|使用的详细教程)', title):
            is_spam_bait = True
            spam_reason = "纯教程"
        # 9.1.3 过滤服务器广告群发 (如桃子味哒狐狸精)
        elif '桃子味哒狐狸精' in author or re.search(r'(?:千人同服|永不删档|整合包服务器|永久开服拒绝删档)', title):
            is_spam_bait = True
            spam_reason = "服务器广告群发"
        # 9.2 单模组枪包/武器扩展包 (若标题为完整整合包附带枪包则不拦截)
        elif not re.search(r'(?:整合包|模组包)', title) and re.search(r'(?:枪包|枪械包|武器包|弹药包|配件包|附属枪包|TacZ\s*(?:附属|扩展|枪包)|TAC\s*(?:附属|扩展|枪包)|TAC-Z\s*(?:附属|扩展)|Point\s*Blank\s*(?:附属|扩展)|自制枪包|原创枪包|重置枪包|多枪包整合|guns\s*and\s*targets枪包|三角洲枪包|冲锋陷阵枪包|源石武器包|冲锋陷阵扩展包)', title, re.I):
            is_spam_bait = True
            spam_reason = "单模组枪包/武器包"
        elif re.search(r'(?:枪包|枪械包|武器包)', title) and not re.search(r'(?:整合包|模组包)', title):
            is_spam_bait = True
            spam_reason = "单模组枪包/武器包"
        # 9.3 单模组模型包/动作包 (若标题为完整整合包附带模型动作则不拦截)
        elif not re.search(r'(?:整合包|模组包)', title) and re.search(r'(?:YSM\s*模型|YSM\s*动作|YSM\s*整合|YSM.*?安装教程|车万女仆.*?模型|女仆模型包|CPM模型|自定义NPC模型|模型整合包|动作整合包|姿势包|骨骼动画包)', title, re.I):
            is_spam_bait = True
            spam_reason = "模型包/动作包"
        # 9.4 服务器发布/宣传/纯开服教程/云服推广
        elif re.search(r'(?:[【\[\(]?(?:服务器发布|服务器宣传|服务器招募|服务器招新|新服开荒|新服发布|开服宣传|开荒公测)[】\]\)]?)', title):
            is_spam_bait = True
            spam_reason = "服务器发布/宣传"
        elif re.search(r'(?:(?:全新|自制|大型|原创|公益|商业|高版本|生化|RPG|战争|空岛|生存|养老|纯净|模组|互通|进服)服务器|.*?服务器.*?(?:你确定不来看看吗|即将更新内容|进群|公测|招人|招募|招新|开服啦))', title, re.I) and not re.search(r'(?:整合包|模组包)\s*(?:发布|更新|下载|分享)', title):
            is_spam_bait = True
            spam_reason = "服务器宣传"
        elif re.search(r'(?:(?:安装和)?开服(?:联机)?教程|服务器搭建教程|FRP开服联机|自己的电脑也能开服)', title) and (not re.search(r'(?:整合包|模组包)\s*(?:发布|更新|首发|公测)', title) or re.search(r'开服教程！|开服联机教程！|开服教程$|联机教程！', title)):
            is_spam_bait = True
            spam_reason = "开服联机教程"
        elif re.search(r'服务器', title) and re.search(r'(?:进服|服务器ip|服务器群|服务器介绍|欢迎加入.*?服)', full_text) and not re.search(r'(?:整合包|模组包)\s*(?:发布|更新|首发)', title):
            is_spam_bait = True
            spam_reason = "服务器宣传"
        # 9.5 单模组发布/单模组更新/制作教程/启动器教程/UP主视频调侃
        elif re.search(r'^[【\[\(]?(?:MC)?(?:模组|mod|Mod|MOD)发布[】\]\)]?', title):
            is_spam_bait = True
            spam_reason = "单模组发布"
        elif re.search(r'(?:模组|mod|Mod)更新', title) and not re.search(r'(?:整合包|模组包)(?:.*?)(?:更新|发布)', title) and not re.search(r'(?:更新|发布)(?:.*?)(?:整合包|模组包)', title):
            is_spam_bait = True
            spam_reason = "单模组更新"
        elif re.search(r'(?:整合包制作$|整合包制作[，,、\s]|制作自己的(?:宝可梦)?整合包|教你.*?制作.*?整合包|整合包制作教学|手把手教你做整合包|如何制作整合包)', title) and (not re.search(r'(?:正式)?发布|公测|首发|全新更新|v\d+\.\d+更新', title) or re.search(r'(?:2分钟做自己的|傻瓜式教学|制作自己的.*?整合包)', desc) or re.search(r'2分钟下载[，,]\s*整合包制作', title)):
            is_spam_bait = True
            spam_reason = "整合包制作教学"
        elif re.search(r'(?:整合包启动教程|启动器教程|启动教程|启动教学)', title, re.I):
            is_spam_bait = True
            spam_reason = "启动教程"
        # 教学指南（不拦截带有整合包正式发布/更新的附带安装教程）
        elif not re.search(r'(?:整合包|模组包|魔改包|懒人包)\s*(?:发布|更新|公测|首发|v\d+)', title, re.I) and re.search(r'(?:[一二三四五]分钟教你|手把手教你|教你(?:如何|怎样|怎么|安装|下载|汉化|制作|开服|配置)|如何安装|怎么安装|如何下载|怎么下载|如何开服|怎么开服|还不会(?:安装|下载)|详细步骤|看了必会)', title, re.I):
            is_spam_bait = True
            spam_reason = "教学指南"
        elif re.search(r'(?:汉化补丁(?:发布|安装|分享)?|单独汉化|汉化教程|模组汉化教程|保姆级汉化教程)', title, re.I):
            is_spam_bait = True
            spam_reason = "汉化补丁"
        elif re.search(r'(?:启动器发布|pcl2?发布|hmcl发布|fcl发布|bakaxl发布|启动器更新|\[软件发布\]|【软件发布】|整合包生成器|模组包打包器|整合包一键移植器)', title, re.I):
            is_spam_bait = True
            spam_reason = "软件/工具发布"
        elif re.search(r'(?:材质包发布|光影包发布|皮肤包发布)', title, re.I):
            is_spam_bait = True
            spam_reason = "材质光影"
        elif re.search(r'^[【\[\(]?(?:FCL|PCL|HMCL|BakaXL|折叠启动器|启动器)教程', title, re.I) or re.search(r'(?:启动器教程|教会你用手机玩Java版.*?整合包下载安装及更新教程)', title):
            is_spam_bait = True
            spam_reason = "启动器教程"
        elif re.search(r'【汉化发布】', title) and not re.search(r'(?:整合包|模组包)', title):
            is_spam_bait = True
            spam_reason = "汉化补丁"
        elif author in ['丶畜生'] or re.search(r'(?:畜生|傻逼|脑瘫)', author):
            is_spam_bait = True
            spam_reason = "低俗违规UP主"
        elif re.search(r'(?:汉化资源包|汉化材质包|汉化光影包)', title):
            is_spam_bait = True
            spam_reason = "汉化资源包"
        elif re.search(r'(?:介绍\[发布\]|介绍\[更新\])', title) and not download_links and not qq_group:
            is_spam_bait = True
            spam_reason = "纯介绍无下载"
        elif re.search(r'1[3-9]\d{9}整合包', title) or (re.search(r'1[3-9]\d{9}', title) and not desc.strip()):
            is_spam_bait = True
            spam_reason = "手机号营销号"

        # 核心判定：标题必须指明整合包，并且要么标题包含行动词/版本，要么简介/评论区提供了有效网盘/群号；同时排除实况、合集、纯材质与垃圾推销
        has_action_or_resource = has_action_title or bool(download_links) or bool(qq_group)
        if not has_pack_title or not has_action_or_resource or is_texture_or_resource or is_let_play or is_recommendation_roundup or is_spam_bait:
            is_genuine = False
        else:
            is_genuine = True

        # 8.1 服务端支持识别
        has_server = bool(re.search(r'(?:服务端|服务器端|开服包|开服|双端|服务器整合包|服务器端下载)', full_text))
        for dl in download_links:
            if re.search(r'(?:server|服务端|开服)', dl.get('type', '') + ' ' + dl.get('url', ''), re.I):
                has_server = True

        # 8.2 整合包自身版本号识别
        pack_version = ""
        pv_m = re.search(r'(?:处于|版本|version|ver|v)?\s*([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:[a-zA-Z0-9_\-\.]+)?)\s*(?:初步测试|测试版|正式版|版本|阶段)', full_text, re.I)
        if pv_m:
            pack_version = pv_m.group(1).strip()
        else:
            pv_m2 = re.search(r'(?i)\bv?([0-9]+\.[0-9]+(?:\.[0-9]+)?)\b', title)
            if pv_m2 and pv_m2.group(1) not in ['1.20', '1.12', '1.16', '1.18', '1.19', '1.21', '1.7', '1.8']:
                pack_version = pv_m2.group(1).strip()

        # 8.3 群内流转版本/进群体验感知
        has_group_version = False
        group_version_note = ""
        gv_pattern = r'(?:进群体验|群文件|群里还有|群内首发|群内测试|群里更新|Q群下载|加群体验|群里下载|群内流转|群里版本|群里最新|群里另一个版本|全面换新)'
        if re.search(gv_pattern, pinned_comment):
            has_group_version = True
            group_version_note = pinned_comment.strip()
        elif re.search(gv_pattern, desc):
            has_group_version = True
            for line in desc.splitlines():
                if re.search(gv_pattern, line):
                    group_version_note = line.strip()
                    break

        return {
            "is_genuine": is_genuine,
            "is_let_play": is_let_play,
            "is_spam_bait": is_spam_bait,
            "spam_reason": spam_reason,
            "mc_version": clean_versions[0] if clean_versions else "未知",
            "all_versions": clean_versions,
            "loaders": loaders_clean,
            "download_links": download_links,
            "extract_code": extract_code,
            "qq_group": qq_group,
            "mod_count": mod_count,
            "categories": categories,
            "has_server": has_server,
            "pack_version": pack_version,
            "has_group_version": has_group_version,
            "group_version_note": group_version_note,
        }


def get_historical_search_tasks() -> List[Tuple[str, str, int]]:
    """
    生成覆盖 2012 ~ 2026 年 Minecraft 远古至今历史全周期的四维穿透搜索任务矩阵。
    返回: List[(keyword, order_mode, max_pages)]
    """
    tasks = []
    
    # 1. 核心通用词 (现代与深度排序)
    core_kws = [
        ("MC整合包", ["pubdate", "stow", "click", "totalrank"], 50),
        ("我的世界整合包", ["pubdate", "stow", "click", "totalrank"], 50),
        ("MC 整合包", ["pubdate", "stow", "click"], 50),
        ("我的世界 整合包", ["pubdate", "stow", "click"], 50),
        ("MC自制整合包", ["pubdate", "stow"], 50),
        ("我的世界自制整合包", ["pubdate", "stow"], 50),
        ("MC模组包", ["pubdate", "stow"], 50),
        ("我的世界模组包", ["pubdate", "stow"], 50),
        ("我的世界 整合包发布", ["pubdate", "stow", "click", "totalrank"], 50),
        ("我的世界 整合包更新", ["pubdate", "stow", "click"], 50),
        ("我的世界 自制整合包", ["pubdate", "stow", "click"], 50),
        ("MC 整合包发布", ["pubdate", "stow"], 50),
        ("MC 整合包更新", ["pubdate", "stow"], 50),
        ("MC 整合包公测", ["pubdate"], 30),
        ("我的世界 整合包首发", ["pubdate"], 30),
        ("我的世界 整合包正式发布", ["pubdate", "stow"], 30),
    ]
    for kw, orders, max_p in core_kws:
        for od in orders:
            tasks.append((kw, od, max_p))

    # 2. MC 历史经典版本切片 (1.2.5 ~ 1.21)
    key_versions = ['1.7.10', '1.12.2', '1.16.5', '1.20.1']
    for v in key_versions:
        tasks.append((f"我的世界 {v} 整合包", "pubdate", 30))
        tasks.append((f"我的世界 {v} 整合包", "stow", 30))
        tasks.append((f"我的世界 {v} 整合包", "click", 30))
        tasks.append((f"{v} 整合包发布", "pubdate", 30))
        tasks.append((f"{v} 整合包发布", "stow", 30))
        tasks.append((f"{v} 整合包更新", "pubdate", 30))

    other_versions = ['1.2.5', '1.4.7', '1.5.2', '1.6.4', '1.7.2', '1.8.9', '1.10.2', '1.14.4', '1.15.2', '1.18.2', '1.19.2', '1.21', '1.21.1']
    for v in other_versions:
        tasks.append((f"我的世界 {v} 整合包", "stow", 20))
        tasks.append((f"{v} 整合包发布", "pubdate", 20))

    # 3. 历史远古词法 (懒人包 / 客户端)
    old_terms = [
        ("我的世界 懒人包发布", "pubdate", 30),
        ("我的世界 懒人包发布", "stow", 30),
        ("我的世界 自制懒人包", "stow", 30),
        ("1.7.10 懒人包", "stow", 30),
        ("1.6.4 懒人包", "stow", 20),
        ("我的世界 整合客户端发布", "pubdate", 30),
        ("我的世界 整合客户端发布", "stow", 30),
    ]
    for t in old_terms:
        tasks.append(t)

    # 4. 传世神作与热门主题矩阵
    themes = [
        ("我的世界 虚无世界 整合包", "stow", 30),
        ("我的世界 虚无世界 整合包", "click", 30),
        ("虚无世界3 整合包发布", "pubdate", 20),
        ("我的世界 工业2 整合包", "stow", 30),
        ("GTNH 整合包", "stow", 30),
        ("格雷科技 整合包发布", "pubdate", 20),
        ("我的世界 神秘时代 整合包", "stow", 30),
        ("神秘时代4 整合包发布", "pubdate", 20),
        ("我的世界 拔刀剑 整合包", "stow", 30),
        ("拔刀剑 整合包发布", "pubdate", 20),
        ("我的世界 暮色森林 整合包", "stow", 30),
        ("我的世界 宝可梦 整合包发布", "pubdate", 30),
        ("我的世界 神奇宝贝 整合包发布", "stow", 30),
        ("RLCraft 整合包", "stow", 30),
        ("贝爷生存 整合包", "stow", 30),
        ("Crash Landing 整合包", "stow", 20),
        ("SevTech Ages 整合包", "stow", 20),
        ("机械动力 整合包发布", "pubdate", 30),
        ("机械动力 整合包更新", "pubdate", 30),
        ("灾变 整合包发布", "pubdate", 20),
        ("寄生虫 整合包发布", "pubdate", 20),
        ("FTB 整合包发布", "pubdate", 20),
        ("All the Mods 整合包", "stow", 20),
    ]
    for th in themes:
        tasks.append(th)

    # 5. 知名创作者回溯
    authors = [
        "爱吃土豆的界王", "明月庄主", "VM汉化组", "一个小寂哦",
        "柠娜", "墨言eclipse", "狐狸の妙妙屋", "星遥工坊",
        "Deemo旋律", "Phoebe_Real", "非酋不想变非酋", "在职玩家JoStar"
    ]
    for a in authors:
        tasks.append((f"{a} 整合包", "pubdate", 30))

    return tasks


def crawl_bilibili_modpacks(until_date: Optional[str] = None, max_pages_per_kw: int = 50, max_total: int = 10000) -> List[Dict[str, Any]]:
    # 截止日期解析：默认回车全量抓取 (None / "" / "all")
    if not until_date or str(until_date).strip().lower() in ("all", "全部", "none", ""):
        cutoff_ts = 0
        cutoff_str = "全量抓取（不设截止日期，搜尽所有历史发布）"
    else:
        import datetime
        cutoff_dt = datetime.datetime.strptime(str(until_date).strip(), "%Y-%m-%d")
        cutoff_ts = int(cutoff_dt.timestamp())
        cutoff_str = f"截止至 {until_date} 00:00:00 (时间戳: {cutoff_ts})"

    print("=" * 65)
    print(f"  Bilibili (B站) Minecraft 整合包专版采集引擎 v2.0")
    print(f"  目标采集范围: {cutoff_str}")
    
    # 检查登录状态
    login_info = BiliAuth.check_login_status()
    if login_info.get("is_login"):
        print(f"  当前登录账号: 【{login_info['uname']}】 (UID: {login_info['mid']} | Lv.{login_info['level']}) [√ 已解锁高清/完整字幕]")
    else:
        print(f"  当前运行模式: 免登录匿名模式（可在主菜单选择 [5] 扫码登录）")
    print("=" * 65)

    crawler = BiliModpackCrawler()
    repo_root = os.path.abspath(
        os.environ.get("MC_DESKTOP_WORKSPACE")
        or os.path.dirname(os.path.abspath(__file__))
    )
    out_dir = os.path.join(repo_root, "crawler_output")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "bilibili_modpacks.json")
    dashboard_data_dir = os.path.join(repo_root, "converted_output", "data")
    os.makedirs(dashboard_data_dir, exist_ok=True)
    js_path = os.path.join(dashboard_data_dir, "bili_data.js")

    # 预加载已有数据
    processed_map = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                old_list = json.load(f)
            for p in old_list:
                if p.get("bvid"):
                    processed_map[p["bvid"]] = p
            print(f"  [初始缓存] 成功载入已抓取的 {len(processed_map):,} 款 B站整合包！")
        except Exception as e:
            pass

    # 历史全周期四维穿透矩阵 (110组无重叠检索任务)
    search_tasks = get_historical_search_tasks()
    
    candidates = {}
    print(f"\n[1/3] 正在多维度扫描 B 站整合包视频流 (共 {len(search_tasks)} 组历史穿透矩阵通道)...")
    
    for task_idx, task_item in enumerate(search_tasks, 1):
        if len(task_item) == 3:
            kw, order_mode, task_max_p = task_item
        else:
            kw, order_mode = task_item
            task_max_p = max_pages_per_kw
        task_max_p = min(task_max_p, max_pages_per_kw)
        
        print(f"  [{task_idx:3d}/{len(search_tasks)}] 检索: 【{kw}】 (排序: {order_mode}, 上限: {task_max_p}页)...")
        kw_added = 0
        reached_cutoff = False
        consecutive_empty = 0
        
        for p in range(1, task_max_p + 1):
            items = crawler.search_videos(kw, page=p, page_size=20, order=order_mode)
            if not items:
                break
            
            page_new = 0
            for item in items:
                pubdate = item.get('pubdate', 0)
                if cutoff_ts > 0 and pubdate < cutoff_ts:
                    reached_cutoff = True
                    continue
                bvid = item.get('bvid')
                if bvid and bvid not in candidates:
                    candidates[bvid] = item
                    kw_added += 1
                    page_new += 1

            if len(items) < 20 or reached_cutoff:
                break
            if page_new == 0:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    break
            else:
                consecutive_empty = 0

            time.sleep(random.uniform(0.12, 0.22))
            
        print(f"      -> 【{kw}】({order_mode}) 纳录 +{kw_added} 条新候选 (当前总候选: {len(candidates)} 条)")
        time.sleep(random.uniform(0.2, 0.4))

    print(f"\n  [√] 检索完成！全矩阵去重后共获得候选视频 {len(candidates)} 条。")
    
    # 过滤掉已抓取的
    unprocessed = [(bvid, item) for bvid, item in candidates.items() if bvid not in processed_map]
    print(f"  [规划] 其中 {len(candidates) - len(unprocessed)} 条已在缓存中，待深挖新视频: {len(unprocessed)} 条 (限制上限: {max_total})\n")

    print(f"[2/3] 正在提取新视频详情、置顶评论、官方/AI字幕并执行实体抽取 (8线程并发)...")
    skipped = [0]
    subtitles_count = [sum(1 for p in processed_map.values() if p.get("has_subtitle"))]
    new_added = [0]
    processed_count = [0]
    lock = Lock()

    def save_state():
        sorted_list = list(processed_map.values())
        sorted_list.sort(key=lambda x: x.get("pub_timestamp", 0), reverse=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(sorted_list, f, ensure_ascii=False, indent=2)
        with open(js_path, "w", encoding="utf-8") as f:
            f.write("window.biliModpacksData = " + json.dumps(sorted_list, ensure_ascii=False) + ";\n")

    candidate_list = unprocessed[:max_total]

    def worker_process(task_tuple):
        bvid, item = task_tuple
        title = item.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
        author = item.get('author', '')
        pic = item.get('pic', '')
        if pic and pic.startswith('//'):
            pic = 'https:' + pic
        pubdate = item.get('pubdate', 0)
        pub_time_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(pubdate)) if pubdate else "未知"
        
        detail = crawler.get_video_detail(bvid)
        if not detail:
            return None
        
        aid = detail.get('aid', 0)
        cid = detail.get('cid', 0)
        desc = detail.get('desc', '')
        stat = detail.get('stat', {})
        views = stat.get('view', 0)
        likes = stat.get('like', 0)
        coins = stat.get('coin', 0)
        favs = stat.get('favorite', 0)
        share = stat.get('share', 0)
        reply = stat.get('reply', 0)
        danmaku = stat.get('danmaku', 0) or item.get('danmaku', 0)
        duration = detail.get('duration', 0)
        dur_str = f"{duration // 60}:{duration % 60:02d}" if duration else ""

        # 抓取置顶评论
        pinned_res = crawler.get_pinned_comment(aid)
        pinned_comment = pinned_res.get('message', '') if isinstance(pinned_res, dict) else str(pinned_res or '')
        pinned_time = pinned_res.get('time', '') if isinstance(pinned_res, dict) else ''
        
        # 抓取官方/AI字幕
        sub_info = crawler.get_video_subtitle(aid, cid, bvid)
        
        # 实体抽取
        ext = crawler.extract_modpack_info(title, desc, pinned_comment, sub_info.get('subtitle_text', ''), author=author, duration=dur_str)
        
        with lock:
            processed_count[0] += 1
            idx = processed_count[0]
            pct = (idx / len(candidate_list)) * 100 if candidate_list else 100
            
            if not ext["is_genuine"]:
                skipped[0] += 1
                return None

            if sub_info.get('has_subtitle'):
                subtitles_count[0] += 1

            pack = {
                "platform": "bilibili",
                "bvid": bvid,
                "aid": aid,
                "cid": cid,
                "url": f"https://www.bilibili.com/video/{bvid}",
                "title": title,
                "author": author,
                "pic": pic,
                "pub_time": pub_time_str,
                "pub_timestamp": pubdate,
                "duration": dur_str,
                "views": views,
                "likes": likes,
                "coins": coins,
                "favorites": favs,
                "share": share,
                "reply": reply,
                "danmaku": danmaku,
                "has_subtitle": sub_info.get('has_subtitle', False),
                "subtitle_text": sub_info.get('subtitle_text', ''),
                "subtitle_summary": sub_info.get('subtitle_summary', ''),
                "mc_version": ext["mc_version"],
                "all_versions": ext["all_versions"],
                "loaders": ext["loaders"],
                "categories": ext["categories"],
                "download_links": ext["download_links"],
                "desc_observed": isinstance(detail.get('desc'), str),
                "pinned_comment_observed": isinstance(pinned_res, dict) and pinned_res.get('observed') is True,
                "subtitle_observed": sub_info.get('observed') is True,
                "download_links_observed": bool(
                    isinstance(detail.get('desc'), str)
                    and isinstance(pinned_res, dict) and pinned_res.get('observed') is True
                    and sub_info.get('observed') is True
                ),
                "extract_code": ext["extract_code"],
                "qq_group": ext["qq_group"],
                "mod_count": ext["mod_count"],
                "desc": desc,
                "pinned_comment": pinned_comment,
                "has_server": ext.get("has_server", False),
                "pack_version": ext.get("pack_version", ""),
                "has_group_version": ext.get("has_group_version", False),
                "group_version_note": ext.get("group_version_note", ""),
                "desc_updated_at": pinned_time if (ext.get("has_group_version") and pinned_time) else "",
            }
            processed_map[bvid] = pack
            new_added[0] += 1
            
            dl_summary = f"{len(ext['download_links'])}个网盘" if ext['download_links'] else "私信/群聊"
            sub_tag = "[附字幕]" if pack["has_subtitle"] else "[无字幕]"
            try:
                print(f"  [{idx:4d}/{len(candidate_list)}] ({pct:5.1f}%) [Bili] [{ext['mc_version']:^7}] {title[:26]:<26} | UP: {author[:8]:<8} | 播放: {views:>6,} | 下载: {dl_summary} | 累计: {len(processed_map)} 款")
            except Exception:
                pass
                
            if new_added[0] % 25 == 0:
                save_state()
                
        return pack

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker_process, t) for t in candidate_list]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception:
                pass

    save_state()
    processed = list(processed_map.values())
    processed.sort(key=lambda x: x.get("pub_timestamp", 0), reverse=True)

    print("\n[3/3] 正在保存数据...")
    print("[OK] 采集完成！范围：" + str(cutoff_str))
    print(f"  - 候选视频总计: {len(candidates)} 条")
    print(f"  - 新增提取有效整合包: +{new_added} 条 (过滤纯实况: {skipped} 条)")
    print(f"  - B站收录总计: {len(processed)} 款！")
    print(f"  - 附带字幕视频: {subtitles_count} 条")
    print(f"  - JSON 归档: {json_path}")
    print(f"  - 前端数据源: {js_path}")
    print("=" * 65)
    request_completed = crawler.stats["failed"] == 0
    write_collection_result(
        "bilibili",
        request_completed=request_completed,
        fetched_count=len(candidates),
        pages_completed=int(crawler.stats["pages_completed"]),
        failed_requests=int(crawler.stats["failed"]),
        errors=crawler.stats["errors"],
        status="success" if candidates and request_completed else "empty" if request_completed else "partial" if candidates else "failed",
        details={"outputCount": len(processed), "newCount": int(new_added[0]), "requestedLimit": max_total or None, "requestedPages": max_pages_per_kw},
    )
    return processed


def sync_descriptions(target_bv: str = "") -> List[Dict[str, Any]]:
    """
    增量巡检与同步模式：
    并发请求 B站 官方 API，巡检已录入整合包视频的最新【简介】与【置顶评论】。
    专门解决 UP 主不发新视频、仅在简介更新网盘/版本号，或者置顶提示群内有新版本的问题。
    """
    repo_root = os.path.abspath(
        os.environ.get("MC_DESKTOP_WORKSPACE")
        or os.path.dirname(os.path.abspath(__file__))
    )
    json_path = os.path.join(repo_root, "crawler_output", "bilibili_modpacks.json")
    js_path = os.path.join(repo_root, "converted_output", "data", "bili_data.js")

    packs = []
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                packs = json.load(f)
        except Exception:
            pass

    pack_map = {p["bvid"]: p for p in packs if p.get("bvid")}

    # 若指定了单个 BV 号（如 BV1BFjS65ENy）且尚未录入，直接加入
    if target_bv and target_bv not in pack_map:
        pack_map[target_bv] = {
            "platform": "bilibili",
            "bvid": target_bv,
            "title": "待同步",
            "author": "",
            "views": 0,
            "pub_timestamp": int(time.time()),
            "download_links": [],
            "desc_observed": False,
            "pinned_comment_observed": False,
            "subtitle_observed": False,
            "download_links_observed": False,
        }

    crawler = BiliModpackCrawler()
    total = len(pack_map)
    print("=" * 65)
    print(f"  🔄 B站 整合包简介与置顶评论增量巡检引擎启动")
    print(f"  -> 待巡检总数: {total} 款视频")
    print("=" * 65)

    updated_count = 0
    checked_count = 0
    lock = Lock()

    def check_worker(bvid: str):
        nonlocal updated_count, checked_count
        orig_pack = pack_map[bvid]
        try:
            detail = crawler.get_video_detail(bvid)
            if not isinstance(detail, dict) or not detail:
                with lock:
                    checked_count += 1
                    orig_pack["desc_observed"] = False
                    orig_pack["download_links_observed"] = False
                return
            aid = detail.get("aid", 0)
            cid = detail.get("cid", 0)
            new_title = detail.get("title", orig_pack.get("title", ""))
            desc_value = detail.get("desc")
            desc_observed = isinstance(desc_value, str)
            new_desc = desc_value if desc_observed else ""
            owner = detail.get("owner", {})
            author = owner.get("name", orig_pack.get("author", ""))
            stat = detail.get("stat", {})
            views = stat.get("view", orig_pack.get("views", 0))
            likes = stat.get("like", orig_pack.get("likes", 0))
            pic = detail.get("pic", orig_pack.get("pic", ""))
            pubdate = detail.get("pubdate", orig_pack.get("pub_timestamp", 0))
            pub_time_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(pubdate)) if pubdate else orig_pack.get("pub_time", "")

            pinned_res = crawler.get_pinned_comment(aid)
            pinned_observed = isinstance(pinned_res, dict) and pinned_res.get("observed") is True
            pinned_comment = pinned_res.get("message", "") if pinned_observed else ""
            pinned_time = pinned_res.get("time", "") if isinstance(pinned_res, dict) else ""

            # Old captions may be reused only when their own source read was
            # confirmed. Legacy records without that provenance are fetched
            # again; an unknown caption is never treated as an empty one.
            reused_subtitle = orig_pack.get("subtitle_observed") is True
            if reused_subtitle:
                subtitle_observed = True
                subtitle_text = orig_pack.get("subtitle_text", "") if isinstance(orig_pack.get("subtitle_text", ""), str) else ""
                sub_info = {
                    "has_subtitle": orig_pack.get("has_subtitle", False),
                    "subtitle_text": subtitle_text,
                    "subtitle_summary": orig_pack.get("subtitle_summary", ""),
                    "observed": True,
                }
            else:
                sub_info = crawler.get_video_subtitle(aid, cid, bvid)
                subtitle_observed = isinstance(sub_info, dict) and sub_info.get("observed") is True
                subtitle_text = sub_info.get("subtitle_text", "") if subtitle_observed else ""

            # 实体解析
            ext = crawler.extract_modpack_info(
                new_title, new_desc, pinned_comment,
                subtitle_text,
                author=author
            )

            # 比对是否有简介/置顶更新，或者关键元数据变动
            desc_changed = desc_observed and (new_desc.strip() != orig_pack.get("desc", "").strip())
            pinned_changed = pinned_observed and (pinned_comment.strip() != orig_pack.get("pinned_comment", "").strip())
            is_new_entry = (orig_pack.get("title") == "待同步")

            updated_flag = False
            if desc_changed or pinned_changed or is_new_entry or not orig_pack.get("download_links"):
                updated_flag = True

            with lock:
                checked_count += 1
                orig_pack["title"] = new_title
                orig_pack["author"] = author
                orig_pack["pic"] = pic
                orig_pack["pub_time"] = pub_time_str
                orig_pack["pub_timestamp"] = pubdate
                orig_pack["views"] = views
                orig_pack["likes"] = likes
                if desc_observed:
                    orig_pack["desc"] = new_desc
                if pinned_observed:
                    orig_pack["pinned_comment"] = pinned_comment
                orig_pack["desc_observed"] = desc_observed
                orig_pack["pinned_comment_observed"] = pinned_observed
                orig_pack["subtitle_observed"] = subtitle_observed
                if subtitle_observed and not reused_subtitle:
                    orig_pack["has_subtitle"] = sub_info.get("has_subtitle", False)
                    orig_pack["subtitle_text"] = subtitle_text
                    orig_pack["subtitle_summary"] = sub_info.get("subtitle_summary", "")
                orig_pack["mc_version"] = ext["mc_version"]
                orig_pack["all_versions"] = ext["all_versions"]
                orig_pack["loaders"] = ext["loaders"]
                orig_pack["categories"] = ext["categories"]
                link_sources_observed = desc_observed and pinned_observed and subtitle_observed
                orig_pack["download_links_observed"] = link_sources_observed
                if link_sources_observed:
                    orig_pack["download_links"] = ext["download_links"]
                orig_pack["extract_code"] = ext["extract_code"]
                orig_pack["qq_group"] = ext["qq_group"]
                orig_pack["mod_count"] = ext["mod_count"]
                orig_pack["has_server"] = ext["has_server"]
                orig_pack["pack_version"] = ext["pack_version"]
                orig_pack["has_group_version"] = ext["has_group_version"]
                orig_pack["group_version_note"] = ext["group_version_note"]

                if updated_flag:
                    updated_count += 1
                    orig_pack["desc_updated_at"] = pinned_time or time.strftime('%Y-%m-%d %H:%M')
                    status_tag = "[新增]" if is_new_entry else "[更新]"
                    print(f"  {status_tag} [{ext['mc_version']:^7}] {new_title[:24]} | UP: {author[:8]} | 网盘: {len(ext['download_links'])} | 群版: {ext['has_group_version']}")
                elif checked_count % 50 == 0:
                    print(f"  ... 已巡检 {checked_count}/{total} 款视频 ...")
        except Exception:
            pass

    to_check = [target_bv] if target_bv else list(pack_map.keys())
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(check_worker, bv) for bv in to_check]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception:
                pass

    final_list = list(pack_map.values())
    final_list.sort(key=lambda x: x.get("pub_timestamp", 0), reverse=True)
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(js_path), exist_ok=True)
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.biliModpacksData = " + json.dumps(final_list, ensure_ascii=False) + ";\n")

    print(f"\n[√] 巡检完成！共检查 {checked_count} 条，捕获简介/置顶更新或新信息: {updated_count} 款。")
    print(f"    - JSON: {json_path}")
    print(f"    - JS: {js_path}")
    return final_list


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="B站 Minecraft 整合包专版采集引擎")
    parser.add_argument("--mode", default="crawl", choices=["crawl", "sync-desc"], help="运行模式: crawl(全网检索抓取), sync-desc(简介/置顶增量巡检)")
    parser.add_argument("--bv", default="", help="针对特定 BV 号执行抓取或更新 (如 BV1BFjS65ENy)")
    parser.add_argument("-u", "--until", default=None, help="采集截止日期（回车或留空默认全量抓取，如 2026-08-01）")
    parser.add_argument("-p", "--pages", type=int, default=50, help="每个关键词最大搜索页数（默认: 50）")
    parser.add_argument("-m", "--max", type=int, default=10000, help="最多处理候选条数（默认: 2000）")
    parser.add_argument("--login", action="store_true", help="启动扫码登录并退出")
    args = parser.parse_args()

    if args.login:
        BiliAuth.login_qr_interactive()
        sys.exit(0)

    if args.mode == "sync-desc" or args.bv:
        sync_descriptions(target_bv=args.bv)
    else:
        crawl_bilibili_modpacks(until_date=args.until, max_pages_per_kw=args.pages, max_total=args.max)
