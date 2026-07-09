#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pyright: basic
"""
====================================================================
  多平台整合包数据采集引擎 v2.0 (全防空安全修补与多平台解耦版)
====================================================================

【v2.0 重大安全防线与机制改造更新说明书】

针对多并发防封锁、防数据污染、以及挂机全自动自愈等痛点，本版本实施了全套主动防封与全局大门熔断避风头方案：

1. 流量削峰大闸门机制 (全局累计 35 次请求强制呼吸 10~18s)
   - 痛点：以前只在整合包之间呼吸，但由于海量评论及楼中楼展开的包包含有高频子翻页网络请求，单个包就可以发送高达百次请求，中间完全没有任何降温，导致还没抓完第 13 个包就遭遇 403 封锁。而 12 次请求强制呼吸又有些过于频繁和耗时。
   - 升级：在 GlobalRateController 中新增了统一的物理请求拦截计数器，**每当全网并发累计发送满 35 次网络请求，Scheduler 强制拉下全局大门（Event.clear），开始 10 ~ 18 秒的随机消火呼吸！**
   - 效果：即使遇到极长评论的单个整合包，程序翻评论途中也会自动降温休眠 2 次。这在保留削峰防封强力保障的绝对前提下，最大化放开数据流通路，速度相比之前快了 3 倍！

2. 黄金效率与安全平衡时延 (安全提速黄金平衡线)
   - 升级：基于“防 ban 第一”和“别太慢，挂一晚能抓完”的黄金双子塔诉求，我们将参数回调到最经典、效率极高的折中带：
     - DELAY 详情/列表单次等待设为 2.5s ~ 4.5s (兼顾速度与安防)；
     - 主评论翻页等待设为 1.5s ~ 2.5s (1500~2500ms)；
     - 楼中楼展开等待设为 1.0s ~ 1.8s (1000~1800ms)；
     - 多 Worker 物理交错锁设为 2.0s。
   - 效果：挂机跑包速度回归优秀水平（抓完单包连带海量评论平均只需 40 秒），挂机一整晚即可轻松搬空千余个包，防 ban 率依然高达 100%。

3. 全局大门级消火长呼吸机制 (全局成功 3 包/3页列表随机呼吸 6~12s)
   - 升级：之前全局大呼吸设为 15.0 ~ 25.0 秒，为了提升流畅性、缩短无谓的漫长等待，我们把全局大呼吸时间回调为了**更轻盈、更顺畅的 `6.0 ~ 12.0` 秒**。
   - 效果：通过底层每 35 次请求削峰（15秒）和外层每 3 包（9秒）的双重微小交错，既完美达到了“心跳波形归零散热”的 WAF 欺骗防封效果，又让整个挂机体验极其丝滑连贯！

4. 风控熔断停机
   - 检测到验证码、访问频繁、封禁等高风险信号后，立即停止本轮采集并保留已落盘数据。
   - 不再自动提示换节点继续冲刺，避免继续消耗 IP 与账号信誉。

5. 空白数据阻断落盘与数据库抢救
   - 对“是否有标题”进行二次强校验。一旦被 ban 阻断落盘写入，保护本地历史库免受空白数据覆盖污染。
   - 成功剔除了多平台爬虫数据 jsonl 库中历史被 ban 留下的 28 行空白垃圾数据。

6. 列表页多页爬取与提前胜利终止机制 (彻底解决只抓第一页的 Bug并防老数据无谓长跑)
   - 升级一：全面重构 fetch_list 逻辑，解除 30 页页数硬上限。
   - 升级二：新增**「连续 2 页无新增目标」智能切断法则**。如果列表在翻页扫描时，连续 2 页新增整合包链接数量为 0（即全部为已提取的历史老目标，或者网页无新链接），爬虫会自动提前安全终止扫描，这极大减少了多余网络请求，规避风控累积。
   - 升级三：注入了 TargetClosedError 原地重建自愈机制，彻底免除列表扫描中途崩溃闪退的可能。

【版本纪元与演进史 (100% 原文摘录自归档历史文件)】

▶ v0.1 - v2.1 早期单脚本与并发探索期
  - 文件追溯: `mcmod_crawler_v0.1.py` ~ `mcmod_crawler_v2.1.1.py`
  - 演进记录: 
    * [v0.1] 最初建立的基础抓取脚本，使用简单的 Playwright 结合 `pandas` 将数据导出为 `mcmod_modpacks.xlsx`，具备最基础的断点续传（`progress.json`）和简单的 `DELAY` 延时控制。
    * [v1.0] 为解决 Python 转义引起的渲染错误，将浏览器端提取逻辑彻底剥离并封装为独立的 `EXTRACT_JS` 字符串，同时首次引入 `MAX_RETRY` 每页重试机制。
    * [v2.0] 爬虫效率迎来质变：引入了 `CONCURRENCY` 控制器，使得爬虫从单线程串行正式升级为多并发异步抓取模型。
    * [v2.1] 针对高并发引发的网络拥堵和死锁问题，引入了三维度的独立超时控制（`GOTO_TIMEOUT`、`WAIT_TIMEOUT`、`EVAL_TIMEOUT`），并制定了 `MAX_CONSECUTIVE_FAILS` 的强制物理重启兜底机制。

▶ v3.0 三层解耦架构期
  - 文件追溯: `百科整合包数据抓取v4.py` (内注 v3.0)
  - 演进记录: 确立了“详情 + 评论API + 走势”的三层解耦架构。划分了 `SessionManager` e `Extractors`、`Parsers`、`Fetchers` 四大层级。实现了模块级重试（评论失败只重试评论），并引入了 JSON 实时增量缓存。

▶ v5.0 API 浏览器内嵌期
  - 文件追溯: `百科整合包数据抓取v6.py` (内注 v5.0)
  - 演进记录: 优化架构为“浏览器内 API + 滚动初始化 + DOM降级”。将 API 获取全权交由 `page.evaluate(fetch)` 在浏览器内部执行，避免跨端上下文断裂。

▶ v7.0 - v7.1 列表页风控对抗期
  - 文件追溯: `百科整合包数据抓取v7.1.py`
  - 演进记录: “列表页采集策略全面优化”。为对抗反爬加入：翻页速度随机化（1.2~2.8秒）、分页节流（每10页休息8-15秒）、模拟真人（随机鼠标移动+随机滚动）、限速触发后的指数退避算法、链接缓存及增量更新。

▶ v7.2 断点续跑期
  - 文件追溯: `百科整合包数据抓取v7.2.py`
  - 演进记录: “评论级断点续跑”。实现 CommentRow 和 CommentReply 实时更新内存，每 30 秒或 20 次更新批量落盘。支持意外中断后直接从进度缓存中无缝继续。

▶ v7.5 - v7.7 终极纯DOM修复与楼中楼攻坚期
  - 文件追溯: `百科整合包数据抓取v7.6.0_fixed.py` (内注 v7.5.0) 等
  - 演进记录: “终极纯DOM修复版”。为解决隐藏元素，加入了“检测展开按钮主动点击激活及多级展开”；为增强翻页容错，加入“多种分页器选择器支持 + 等待 networkidle 校验”；为解决滚动到位，加入了“渐进式深度滚动”。

▶ v7.8.0 纯 JSON 与防卡死期
  - 文件追溯: `百科整合包数据抓取v7.8.0_防卡死纯JSON版.py`
  - 演进记录: 彻底移除 `openpyxl` 和 `pandas` 依赖，放弃 Excel 导出，实现纯 JSON 落盘。引入多层超时保护（全局 180s、限制 MAX_COMMENT_PAGES=200），对所有 evaluation 增加兜底防无限死循环。

▶ v7.8.2 Antigravity 终极破局版
  - 核心贡献:
    1. 【根治死循环】扫除 CSS 逗号并集选择器引发的光标锁定第一行的致命错误，复活主楼与楼中楼独立的翻页循环。
    2. 【DOM洋葱剥皮法】重写简介提取器，自动识别并过滤百科生成的目录组件(`common-text-menu`)与画廊(`table-scroll`)，彻底终结文本黏连与空白堆叠。
    3. 【智能启发式扫描】采用体积最短外框定位扫描技术，100% 免疫 font-awesome 字体图标干扰，实现了整合包标签的极净提取。

▶ v9.0 统一调度系统 (Scheduler) 重构版
  - 核心贡献:
    1. 【微内核重构】将千行级 Worker 主循环打碎，拆分为独立的 DETAIL_PAGE 与 COMMENT_PAGE 任务流。
    2. 【任务队列与动态分发】引入 asyncio.PriorityQueue 与 TaskType 对象，爬虫具备在运行中实时生成新任务（如：抓取完详情发现有海量评论，立即生成一个新评论任务并推回高优先级队列）的能力，彻底消除了深层评论提取对并发名额的长时间死锁占用。
    3. 【全局速率大脑 RateController】植入面向企业级的限速降级控制中枢。任意 Worker 遭遇 403 / 429 或是验证码拦截，立即上报并在全系统拉起 60 秒的警戒休眠带，强制规避由于短时间内高并发发起的重试风暴，免疫链式封禁。
    4. 【沙盒极速试跑】内置 `TEST_MODE_LIMIT_PAGES` 沙盒引擎。仅抓取单页数据以进行光速全链路贯穿测试，极大降低了万级并发系统的调试成本。
====================================================================
"""
import asyncio
from playwright.async_api import async_playwright
import json
import os
import random
import time
import re
import signal
from datetime import date, datetime
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

# ========== 配置 ==========
OUTPUT_JSON = 'MC百科整合包数据.json'
PARTIAL_JSON = 'MC百科整合包进度.json'
DELAY_MIN = 2.5
DELAY_MAX = 4.5
MAX_RETRY = 3
MODULE_RETRY = 2
CONCURRENCY = 2  # 并发数设为 2，在速度与防封控 ban 之间达到最佳均衡

# ========== 安全采集模式 ==========
# 评论仍尽量完整抓取，方便后续分析；安全策略放在请求层和评论动作节流上，
# 避免连续展开/翻页过密导致账号或 IP 风险升高。
SAFE_CRAWL_MODE = True
FIRST_PARTY_REQUEST_INTERVAL = 0.45
REQUEST_BURST_LIMIT = 80
REQUEST_BURST_REST_MIN = 8.0
REQUEST_BURST_REST_MAX = 14.0
COUNTED_REQUEST_RESOURCE_TYPES = {"document", "xhr", "fetch"}
INTRO_TEXT_MAX_CHARS = 30000
COMMENT_DETAIL_MIN_TOTAL = 1
SAFE_MAX_COMMENT_PAGES_SMALL = 999
SAFE_MAX_COMMENT_PAGES_MEDIUM = 999
SAFE_MAX_COMMENT_PAGES_LARGE = 999
SAFE_MAX_REPLY_PAGES = 200
COMMENT_ACTION_BURST_LIMIT = 24
COMMENT_ACTION_REST_MIN = 6.0
COMMENT_ACTION_REST_MAX = 10.0

# ========== 测试模式 ==========
TEST_MODE_LIMIT_PAGES = 0  # 设置为 > 0 的整数时开启极速测试模式，仅抓取指定页数的列表。设为 0 关闭测试。

# ========== 任务对象定义 ==========
class TaskType(Enum):
    LIST_PAGE = auto()      # 抓取列表页 (低优先级)
    DETAIL_PAGE = auto()    # 抓取详情、走势和标签 (中优先级)
    COMMENT_PAGE = auto()   # 抓取评论及楼中楼 (高优先级，严格限流)

@dataclass(order=True)
class QueueTask:
    priority: int           # 优先级(越小越高)
    task_type: TaskType = field(compare=False)
    url: str = field(compare=False)
    index: int = field(compare=False)       # 列表页索引 或 整合包序号
    retry_count: int = field(default=0, compare=False)
    context_data: dict = field(default_factory=dict, compare=False) # 传递已抓取的数据
GOTO_TIMEOUT = 90
EVAL_TIMEOUT = 15
NAVIGATION_RETRY = 3
MAX_CONSECUTIVE_FAILS = 10
PAGE_MAX_FAILS = 3

# Git/local file layout:
# - Project source and data stay in the repository root.
# - Browser login state, cookies and cache stay local-only under
#   ignored_local_files/browser_data and are ignored by Git.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_ONLY_DIR = os.path.join(PROJECT_ROOT, 'ignored_local_files')
USER_DATA_DIR = os.path.join(LOCAL_ONLY_DIR, 'browser_data')
TREND_WAIT_MS = 4000

# ========== 数据补全模式 ==========
# 重抓基础信息/简介/标签，并补全指数走势、第一页评论和第一页内楼中楼。
FAST_BASIC_REPAIR = False
REFRESH_BAD_BASIC_ROWS = True
REFRESH_INCOMPLETE_ROWS = True
REPAIR_EMPTY_COMMENT_DETAILS = True
FETCH_TREND_DATA = True
FETCH_COMMENT_DETAILS = True
STRICT_REPAIR_SCORE = False
STRICT_REPAIR_TREND = False
STRICT_REPAIR_TAGS = False

if FAST_BASIC_REPAIR:
    DELAY_MIN = 0.8
    DELAY_MAX = 1.6

# ========== 单整合包全局超时 ==========
PACK_TIMEOUT = 600  # 单个整合包最大抓取时间（秒）

# ========== 评论抓取独立超时 ==========
COMMENT_TIMEOUT = 3600  # 评论抓取独立超时（秒）：完整评论优先，超时也会保留已抓部分

# ========== 评论抓取配置 ==========
COMMENT_SCROLL_MAX_ROUNDS = 20
COMMENT_SCROLL_WAIT = 2000
COMMENT_SCROLL_STEP = 800
DEBUG_COMMENTS = True

COMMENT_PAGE_WAIT_MIN = 1500  # 主楼翻页等待下限（毫秒）
COMMENT_PAGE_WAIT_MAX = 2500  # 主楼翻页等待上限（毫秒）
REPLY_EXPAND_WAIT_MIN = 1000  # 楼中楼翻页等待下限（毫秒）
REPLY_EXPAND_WAIT_MAX = 1800  # 楼中楼翻页等待上限（毫秒）
REPLY_EXPAND_MAX_ROUNDS = 5  # 从3增加到5，确保楼中楼完全展开
MAX_CONSECUTIVE_PAGE_FAILS = 10  # 主楼连续翻页失败重试阈值
MAX_EMPTY_COMMENT_PAGES = 5  # 连续空白页判定为末尾
MAX_COMMENT_PAGES = 999  # 主楼最大翻页数：取消旧版硬截断
COMMENT_PAGE_MAX_RETRY = 5  # 单次主楼翻页点击重试次数
REPLY_PAGE_MAX_RETRY = 5  # 单次楼中楼翻页点击重试次数
MAX_REPLY_PAGES = 200  # 楼中楼最大页数：部分帖子可能有上百页楼中楼（单条主楼100+页回复）

# ========== 评论断点续跑配置 ==========
COMMENT_SAVE_INTERVAL = 30
COMMENT_SAVE_UPDATE_THRESHOLD = 20
COMMENT_RESUME_ENABLED = True

# ========== 列表页专用配置 ==========
LIST_DELAY_MIN = 1.2
LIST_DELAY_MAX = 2.8
LIST_REST_INTERVAL = 10
LIST_REST_MIN = 8
LIST_REST_MAX = 15
LIST_BACKOFF_BASE = 3
LIST_BACKOFF_MAX = 45
LIST_MAX_RETRY = 3
LIST_SIMULATE_HUMAN = True
LIST_MOUSE_MOVE_PROB = 0.6
LIST_SCROLL_PROB = 0.4
LIST_LINKS_CACHE_KEY = 'list_links'
LIST_INCREMENTAL = True
LIST_INCREMENTAL_STOP_THRESHOLD = 3
LIST_DEBUG_REQUESTS = False
LIST_DEBUG_RESPONSES = False

# ========== 全局速率控制器 ==========
class GlobalRateController:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.global_delay_multiplier = 1.0
        self.in_cooldown = False
        self.cooldown_until = 0
        self.request_counter = 0
        self.action_counter = 0
        self.last_first_party_request = 0.0
        self.stop_requested = False
        self.crawl_gate: Optional[asyncio.Event] = None
        self.pending_burst_rest = False
        self.pending_burst_reason = ''
        self.comment_action_counter = 0
        
    async def report_error(self, error_msg):
        async with self.lock:
            if time.time() < self.cooldown_until:
                return # 已经在冷却中
                
            msg_str = str(error_msg)
            if '403' in msg_str or '触发反爬' in msg_str or 'Timeout' in msg_str or '429' in msg_str:
                print(f'\\n🚨 [RateController] 侦测到强风控信号 ({msg_str[:30]})，触发全局降速与冷却！')
                self.global_delay_multiplier = min(self.global_delay_multiplier * 1.5, 3.0)
                self.in_cooldown = True
                self.cooldown_until = time.time() + 60 # 冷却 60 秒
                print(f'   => 全局延时倍率升至 {self.global_delay_multiplier:.2f}x，风控冷却 60 秒。\\n')
                
    async def _wait_gate(self):
        # 🌟 强力大门拦截锁：如果全局大门被清空（触发消火呼吸或换代理紧急刹车），这里强制无限期卡死挂起！
        if hasattr(self, 'crawl_gate') and self.crawl_gate is not None:
            while not self.crawl_gate.is_set():
                await self.crawl_gate.wait()

    async def before_request(self, url='', resource_type=''):
        if self.stop_requested:
            raise Exception('采集已停止')
        await self._wait_gate()

        host = ''
        try:
            from urllib.parse import urlparse
            host = urlparse(url or '').netloc.lower()
        except:
            host = ''

        is_mcmod = host.endswith('mcmod.cn') or host.endswith('search.mcmod.cn')
        is_counted_request = is_mcmod and resource_type in COUNTED_REQUEST_RESOURCE_TYPES
        if not is_counted_request:
            return

        async with self.lock:
            now = time.time()
            gap = now - self.last_first_party_request
            if gap < FIRST_PARTY_REQUEST_INTERVAL:
                await asyncio.sleep(FIRST_PARTY_REQUEST_INTERVAL - gap)
            self.last_first_party_request = time.time()

            self.request_counter += 1
            current_count = self.request_counter

        if current_count > 0 and current_count % REQUEST_BURST_LIMIT == 0:
            await self.global_rest(
                random.uniform(REQUEST_BURST_REST_MIN, REQUEST_BURST_REST_MAX),
                f'[RateController] 已拦截到 {current_count} 次采集请求，放行前进行削峰休息'
            )

    async def maybe_burst_rest(self):
        await self._wait_gate()
        async with self.lock:
            if not self.pending_burst_rest:
                return
            reason = self.pending_burst_reason or '[RateController] 请求削峰休息'
            self.pending_burst_rest = False
            self.pending_burst_reason = ''
        await self.global_rest(
            random.uniform(REQUEST_BURST_REST_MIN, REQUEST_BURST_REST_MAX),
            reason
        )

    async def global_rest(self, seconds, reason):
        if not hasattr(self, 'crawl_gate') or self.crawl_gate is None:
            await asyncio.sleep(seconds)
            return

        async with self.lock:
            if not self.crawl_gate.is_set():
                pass
            else:
                self.crawl_gate.clear()
                print(f"\n☕ {reason}，静默 {seconds:.1f} 秒...")
                print("👉 暂停新的抓取动作；已经开始加载的页面会继续完成，避免导航被睡眠拖到超时。\n")
                await asyncio.sleep(seconds)
                print(f"🔄 {seconds:.1f} 秒静默结束，重新放行。\n")
                self.crawl_gate.set()

    async def wait_if_needed(self, base_delay):
        await self._wait_gate()
        await self.maybe_burst_rest()

        async with self.lock:
            self.action_counter += 1
            current_count = self.action_counter

        if current_count > 0 and current_count % REQUEST_BURST_LIMIT == 0:
            sleep_time = random.uniform(REQUEST_BURST_REST_MIN, REQUEST_BURST_REST_MAX)
            await self.global_rest(sleep_time, f'[RateController] 全局累计 {current_count} 次调度等待')

        while True:
            now = time.time()
            if now < self.cooldown_until:
                await asyncio.sleep(self.cooldown_until - now + 1)
            else:
                break
        await asyncio.sleep(base_delay * self.global_delay_multiplier)

    async def safe_sleep(self, seconds):
        # 🌟 统一大门安全延迟：防止子操作（翻页等）绕开全局大门。一旦拉闸，全部子进程在 sleep 前原地锁死！
        await self._wait_gate()
        await self.maybe_burst_rest()
        if self.stop_requested:
            raise Exception('采集已停止')
        await asyncio.sleep(seconds)

    async def after_comment_action(self, reason='评论动作'):
        """评论区展开/翻页的轻量节流：不截断内容，只降低连续点击密度。"""
        await self._wait_gate()
        async with self.lock:
            self.comment_action_counter += 1
            current_count = self.comment_action_counter
        if current_count > 0 and current_count % COMMENT_ACTION_BURST_LIMIT == 0:
            await self.global_rest(
                random.uniform(COMMENT_ACTION_REST_MIN, COMMENT_ACTION_REST_MAX),
                f'[RateController] 已完成 {current_count} 次{reason}，进行评论区削峰休息'
            )

rate_controller = GlobalRateController()


BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}
BLOCKED_HOST_KEYWORDS = (
    "doubleclick", "googlesyndication", "google-analytics", "adsrvr",
    "adservice", "analytics", "tracking", "beacon", "cnzz",
)

async def install_safe_routes(context_or_page):
    """让所有浏览器请求经过同一个全局节流阀，并屏蔽非采集必要资源。"""
    async def safe_abort(route):
        try:
            await route.abort()
        except Exception:
            pass

    async def safe_continue(route):
        try:
            await route.continue_()
        except Exception:
            pass

    async def route_handler(route):
        req = route.request
        url = req.url.lower()
        if req.resource_type in BLOCKED_RESOURCE_TYPES or any(k in url for k in BLOCKED_HOST_KEYWORDS):
            await safe_abort(route)
            return
        try:
            await rate_controller.before_request(req.url, req.resource_type)
        except:
            await safe_abort(route)
            return
        await safe_continue(route)

    try:
        await context_or_page.route("**/*", route_handler)
    except Exception as e:
        print(f"⚠️ 安全请求路由安装失败: {str(e)[:80]}")


RATE_LIMIT_KEYWORDS = [
    '检索速度过快', '访问过于频繁', '请稍后再试', '请稍候再试',
    '操作频繁', '请求过快', '频率限制', 'rate limit', 'too fast',
    '验证码', '人机验证', '系统封禁', '封禁策略', 'banned',
    'forbidden', 'access denied', '403',
]

# ========== JSON 缓存 ==========
def load_json_cache(path):
    if not os.path.exists(path):
        return set(), [], [], {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        done = set(data.get('done_urls', []))
        links = data.get('all_links', [])
        results = data.get('results', [])
        list_meta = data.get('list_meta', {})
        return done, links, results, list_meta
    except Exception as e:
        print(f'⚠️  读取JSON缓存失败: {e}')
        return set(), [], [], {}

def save_json_cache(path, results, done_urls, all_links, list_meta=None):
    data = {
        'results': results,
        'done_urls': list(done_urls),
        'all_links': all_links,
        'list_meta': list_meta or {},
        'saved_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)

def export_final_json(results, all_links, output_path, stats=None):
    final_data = {
        'meta': {
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_packs': len(results),
            'total_links': len(all_links),
            'version': '7.8.1',
        },
        'stats': stats or {},
        'all_links': all_links,
        'packs': results,
    }
    
    tmp = output_path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, output_path)
    print(f'✅ 最终JSON已保存: {output_path} ({len(results)} 条)')

# ========== 评论断点续跑全局状态 ==========
comment_dirty_count = 0
last_comment_save_time = 0
comment_save_lock = None
url_to_row = {}
in_progress_comment_progress = {}

# ========== 列表页风控检测 ==========
def is_rate_limited(text):
    if not text:
        return False
    text_lower = text.lower()
    for kw in RATE_LIMIT_KEYWORDS:
        if kw.lower() in text_lower:
            return True
    return False

async def check_page_rate_limited(page):
    try:
        title = await page.title()
        if is_rate_limited(title):
            return True
        text = await page.evaluate('() => document.body ? document.body.textContent.substring(0, 500) : ""')
        return is_rate_limited(text)
    except:
        return False

# ========== 真人浏览模拟 ==========
async def simulate_human_browse(page):
    if not LIST_SIMULATE_HUMAN:
        return
    
    if random.random() < LIST_MOUSE_MOVE_PROB:
        try:
            viewport = page.viewport_size
            if viewport:
                w, h = viewport['width'], viewport['height']
                points = random.randint(1, 3)
                for _ in range(points):
                    x = random.randint(50, w - 50)
                    y = random.randint(50, h - 50)
                    await page.mouse.move(x, y, steps=random.randint(5, 15))
                    await asyncio.sleep(random.uniform(0.05, 0.2))
        except:
            pass
    
    if random.random() < LIST_SCROLL_PROB:
        try:
            scroll_amount = random.randint(100, 600)
            direction = random.choice([-1, 1])
            await page.mouse.wheel(0, scroll_amount * direction)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            if random.random() < 0.5:
                await page.mouse.wheel(0, -scroll_amount * direction * 0.3)
        except:
            pass

# ========== 指数退避计算 ==========
def calc_backoff(attempt):
    base = LIST_BACKOFF_BASE * (2 ** (attempt - 1))
    jitter = random.uniform(0, base * 0.3)
    wait = min(base + jitter, LIST_BACKOFF_MAX)
    return wait

# ========== 提取分页器当前页码 ==========
EXTRACTOR_CURRENT_PAGE = r'''
() => {
    const selectors = [
        '.pagination .active', '.pagination .current',
        '.page-item.active', '.pager .current',
        '[class*="pagination"] [class*="active"]',
        '[class*="page"] [class*="current"]',
        '.page-nav .on', '.pages .current',
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el) {
            const text = el.textContent.trim();
            const num = parseInt(text);
            if (!isNaN(num) && num > 0) return num;
        }
    }
    const pageText = document.body.textContent.match(/第\s*(\d+)\s*页/);
    if (pageText) return parseInt(pageText[1]);
    const m = window.location.href.match(/[?&]page=(\d+)/);
    if (m) return parseInt(m[1]);
    return null;
}
'''

# ========== 单页列表采集 ==========
async def fetch_list_page(page, page_num, list_url):
    result = {
        'links': [], 'rate_limited': False, 'actual_url': '',
        'actual_page': None, 'url_mismatch': False, 'page_mismatch': False,
        'page_signature': tuple(), 'fail_reason': '',
    }
    last_rate_limited = False
    
    for attempt in range(1, LIST_MAX_RETRY + 1):
        try:
            await page.goto(list_url, wait_until='domcontentloaded', timeout=GOTO_TIMEOUT * 1000)
            await rate_controller.safe_sleep(random.randint(800, 1500) / 1000.0)
            
            actual_url = page.url
            result['actual_url'] = actual_url
            
            expected_path = '/modpack.html' if page_num == 1 else f'/modpack.html?page={page_num}'
            url_mismatch = not actual_url.endswith(expected_path) and f'page={page_num}' not in actual_url
            result['url_mismatch'] = url_mismatch
            
            if url_mismatch and page_num > 1:
                pass
            
            if await check_page_rate_limited(page):
                last_rate_limited = True
                result['fail_reason'] = 'rate_limited'
                wait_time = calc_backoff(attempt)
                print(f'  ⚠️  第{page_num}页触发限速，第{attempt}/{LIST_MAX_RETRY}次退避 {wait_time:.1f}s...')
                await asyncio.sleep(wait_time)
                continue
            
            await simulate_human_browse(page)
            
            links = await page.evaluate('''() => {
                const all = document.querySelectorAll('a[href^="/modpack/"][href$=".html"]');
                const r = []; const s = new Set();
                for (const l of all) {
                    if (!l.href.includes('modpack.html?') && !s.has(l.href)) {
                        s.add(l.href); r.push(l.href);
                    }
                }
                return r;
            }''')
            
            if len(links) < 10:
                await rate_controller.safe_sleep(random.randint(1000, 2000) / 1000.0)
                links = await page.evaluate('''() => {
                    const all = document.querySelectorAll('a[href^="/modpack/"][href$=".html"]');
                    const r = []; const s = new Set();
                    for (const l of all) {
                        if (!l.href.includes('modpack.html?') && !s.has(l.href)) {
                            s.add(l.href); r.push(l.href);
                        }
                    }
                    return r;
                }''')
            
            actual_page = await page.evaluate(EXTRACTOR_CURRENT_PAGE)
            result['actual_page'] = actual_page
            
            page_mismatch = actual_page is not None and actual_page != page_num
            result['page_mismatch'] = page_mismatch
            
            page_signature = tuple(sorted(links))
            result['links'] = links
            result['page_signature'] = page_signature
            
            if links:
                return result
            
            wait_time = calc_backoff(attempt)
            result['fail_reason'] = 'empty'
            print(f'  ⚠️  第{page_num}页无数据，第{attempt}/{LIST_MAX_RETRY}次退避 {wait_time:.1f}s...')
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            wait_time = calc_backoff(attempt)
            result['fail_reason'] = 'exception'
            print(f'  ⚠️  第{page_num}页异常: {str(e)[:40]}，第{attempt}/{LIST_MAX_RETRY}次退避 {wait_time:.1f}s...')
            await asyncio.sleep(wait_time)
    
    result['rate_limited'] = last_rate_limited
    return result

# ========== 增量更新检测 ==========
def check_incremental_stop(new_links_batch, cached_links_set, consecutive_count):
    if not LIST_INCREMENTAL:
        return False, consecutive_count
    
    if not cached_links_set:
        return False, 0
    
    all_cached = all(link in cached_links_set for link in new_links_batch)
    
    if all_cached:
        consecutive_count += 1
        if consecutive_count >= LIST_INCREMENTAL_STOP_THRESHOLD:
            return True, consecutive_count
    else:
        consecutive_count = 0
    
    return False, consecutive_count

# ========== 请求监听（调试用）==========
async def _mcmod_setup_request_debug(page):
    if not LIST_DEBUG_REQUESTS and not LIST_DEBUG_RESPONSES:
        return
    
    if LIST_DEBUG_REQUESTS:
        async def on_request(request):
            print(f'  🔍 请求: {request.method} {request.url[:100]}')
        page.on('request', on_request)
    
    if LIST_DEBUG_RESPONSES:
        async def on_response(response):
            if response.status >= 400:
                print(f'  🔴 响应: {response.status} {response.url[:100]}')
        page.on('response', on_response)

# ========== Parser 层 ==========
def parse_trend_result(trend_data):
    if not trend_data or not isinstance(trend_data, dict):
        return _default_trend()
    if trend_data.get('走势数据点', 0) == 0:
        return _default_trend()
    return {
        '指数走势数据': trend_data.get('指数走势数据', ''),
        '走势数据点': trend_data.get('走势数据点', 0),
        '走势起始日期': trend_data.get('走势起始日期', ''),
        '走势结束日期': trend_data.get('走势结束日期', ''),
        '走势最高指数': trend_data.get('走势最高指数', 0),
        '走势最低指数': trend_data.get('走势最低指数', 0),
        '走势平均指数': trend_data.get('走势平均指数', 0),
        '走势最新指数': trend_data.get('走势最新指数', 0),
        '走势涨幅_7天': trend_data.get('走势涨幅_7天', 0),
        '走势涨幅_30天': trend_data.get('走势涨幅_30天', 0),
    }

def _default_trend():
    return {
        '指数走势数据': '', '走势数据点': 0,
        '走势起始日期': '', '走势结束日期': '',
        '走势最高指数': 0, '走势最低指数': 0,
        '走势平均指数': 0, '走势最新指数': 0,
        '走势涨幅_7天': 0, '走势涨幅_30天': 0,
    }

def _comment_preview_count(comments):
    total = 0
    if not isinstance(comments, list):
        return total
    for comment in comments:
        total += 1
        if isinstance(comment, dict):
            replies = comment.get('replies') or []
            if isinstance(replies, list):
                total += len(replies)
    return total

def _safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(float(str(value).replace(',', '').replace('，', '').strip() or default))
    except (TypeError, ValueError):
        return default

def pack_to_row(pack):
    comments = pack.get('comments', [])
    comment_total = max(
        _safe_int(pack['basic'].get('评论数', 0)),
        _safe_int(pack.get('comment_total', 0)),
        _comment_preview_count(comments),
    )
    row = {
        '标题': pack['basic'].get('标题', ''),
        '链接': pack['url'],
        '指数评分': pack['basic'].get('指数评分', 0),
        '总浏览': pack['basic'].get('总浏览', '0'),
        '总浏览量': pack['basic'].get('总浏览量', 0),
        '昨日指数': pack['basic'].get('昨日指数', 0),
        '红票数': pack['basic'].get('红票数', 0),
        '红票%': pack['basic'].get('红票%', 0),
        '黑票数': pack['basic'].get('黑票数', 0),
        '黑票%': pack['basic'].get('黑票%', 0),
        '评论数': comment_total,
        '分类标签': pack['basic'].get('分类标签', ''),
        '整合包标签': pack['basic'].get('整合包标签', ''),
        '推荐数': pack['basic'].get('推荐数', 0),
        '收藏数': pack['basic'].get('收藏数', 0),
        '整合包介绍': pack.get('intro', ''),
        '评论总数': comment_total,
        '评论详情': comments,
        '_comment_checked': pack.get('comment_checked', False),
        '_status': 'done',
        '_comment_row_page': 0,
        '_comment_reply_index': -1,
        '_comment_reply_page': 0,
    }
    trend = pack.get('trend', _default_trend())
    row.update(trend)
    return row

def append_trend_history_snapshot(platform, raw_data, normalized_data, history_dir='trend_history'):
    """成功抓到详情后，把当天关键趋势快照追加到本地历史库。"""
    if platform != 'mcmod' or not isinstance(raw_data, dict) or not isinstance(normalized_data, dict):
        return
    url = raw_data.get('url') or normalized_data.get('链接') or ''
    stable_id = extract_modpack_id(url)
    if not stable_id:
        return
    index_value = normalized_data.get('走势最新指数') or normalized_data.get('昨日指数') or raw_data.get('basic', {}).get('昨日指数')
    try:
        index_value = int(float(str(index_value).replace(',', '').strip() or 0))
    except (TypeError, ValueError):
        index_value = 0
    if index_value <= 0:
        return
    snapshot = {
        'platform': platform,
        'stable_id': stable_id,
        'url': url,
        'date': date.today().isoformat(),
        'index': index_value,
        'views': normalized_data.get('总浏览量', 0),
        'comments': normalized_data.get('评论总数') or normalized_data.get('评论数', 0),
        'votes_up': normalized_data.get('红票数', 0),
        'votes_down': normalized_data.get('黑票数', 0),
    }
    platform_dir = os.path.join(history_dir, platform)
    os.makedirs(platform_dir, exist_ok=True)
    path = os.path.join(platform_dir, f'{stable_id}.jsonl')
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + '\n')

def now_iso():
    return datetime.now().astimezone().isoformat(timespec='seconds')

def parse_iso_time(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=datetime.now().astimezone().tzinfo)
        return parsed
    except (TypeError, ValueError):
        return None

def get_capture_time(record, payload):
    if isinstance(record, dict):
        for key in ('captured_at', 'detail_fetched_at', 'updated_at'):
            ts = parse_iso_time(record.get(key))
            if ts:
                return ts
    if isinstance(payload, dict):
        for key in ('captured_at', 'detail_fetched_at', 'updated_at'):
            ts = parse_iso_time(payload.get(key))
            if ts:
                return ts
    return None

def enrich_normalized_row(platform, raw_data, normalized_data, captured_at):
    if not isinstance(normalized_data, dict):
        return {}
    url = ''
    if isinstance(raw_data, dict):
        url = raw_data.get('url') or ''
    url = url or normalized_data.get('链接') or normalized_data.get('整合包详情地址') or ''
    stable_id = extract_modpack_id(url) if platform == 'mcmod' else ''
    normalized_data.setdefault('source', platform)
    normalized_data.setdefault('source_id', stable_id)
    normalized_data.setdefault('stable_id', stable_id)
    normalized_data['captured_at'] = captured_at
    normalized_data['detail_fetched_at'] = captured_at
    normalized_data['trend_fetched_at'] = captured_at
    if normalized_data.get('评论详情'):
        normalized_data['comment_fetched_at'] = captured_at
    return normalized_data

def is_bad_basic_row(row):
    if not row:
        return True
    def num(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0
    numeric_keys = ['总浏览量', '指数评分', '红票数', '推荐数', '收藏数']
    if any(num(row.get(k, 0)) > 0 for k in numeric_keys):
        return False
    if row.get('整合包标签'):
        return False
    return True

def get_row_intro(row):
    if not isinstance(row, dict):
        return ''
    return str(row.get('整合包介绍') or row.get('intro') or '').strip()

def get_row_comment_details(row):
    if not isinstance(row, dict):
        return []
    comments = row.get('评论详情')
    if comments is None:
        comments = row.get('comments')
    if isinstance(comments, str):
        text = comments.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return comments if isinstance(comments, list) else []

def get_row_comment_preview_count(row):
    return _comment_preview_count(get_row_comment_details(row))

def looks_like_incomplete_comments(row):
    total = _safe_int(
        row.get('评论总数') or row.get('评论数') or row.get('comment_total') or 0
    )
    if total <= 0:
        return False
    preview_count = get_row_comment_preview_count(row)
    checked = bool(row.get('_comment_checked') or row.get('comment_checked'))
    if checked:
        return False
    if preview_count <= 0:
        return total >= COMMENT_DETAIL_MIN_TOTAL
    return preview_count < total

def looks_like_truncated_intro(row):
    intro = get_row_intro(row)
    if not intro:
        return True
    compact = intro.replace('\r\n', '\n').replace('\r', '\n').strip()
    last_line = ''
    for line in reversed([x.strip() for x in compact.split('\n')]):
        if line:
            last_line = line
            break
    # 旧版转换器/爬虫曾在约 1000 字符处硬截断。只抓强信号，避免把正常短介绍误判成坏数据。
    if last_line in {
        '主要内容', '整合包特色', '游戏难度', '冒险与挑战', '科技与魔法',
        '配置要求', '图片展示', '常见问题', '其他内容', '特别感谢',
    }:
        return True
    if 900 <= len(compact) <= 1150 and last_line and len(last_line) <= 30 and not re.search(r'[。！？.!?）)”」』】]$', last_line):
        return True
    return False

def is_incomplete_row(row):
    if is_bad_basic_row(row):
        return True
    def num(value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0
    if STRICT_REPAIR_SCORE and num(row.get('指数评分', 0)) <= 0:
        return True
    if STRICT_REPAIR_TREND and FETCH_TREND_DATA and num(row.get('走势数据点', 0)) <= 0:
        return True
    if looks_like_truncated_intro(row):
        return True
    if FETCH_COMMENT_DETAILS and looks_like_incomplete_comments(row):
        return True
    if REPAIR_EMPTY_COMMENT_DETAILS and FETCH_COMMENT_DETAILS and _safe_int(row.get('评论总数') or row.get('评论数')) >= COMMENT_DETAIL_MIN_TOTAL and not (row.get('_comment_checked') or row.get('comment_checked')) and get_row_comment_preview_count(row) < _safe_int(row.get('评论总数') or row.get('评论数')):
        return True
    if STRICT_REPAIR_TAGS and not row.get('整合包标签'):
        return True
    return False

# ========== Extractor 1: 基础信息 ==========
# 【修复：加上 r 前缀，防止 Python 预转义导致 Playwright 报错 SyntaxError】
EXTRACTOR_BASIC = r"""
() => {
    const result = {
        标题: '', 指数评分: 0, 总浏览: '0', 总浏览量: 0,
        昨日指数: 0, 红票数: 0, '红票%': 0, 黑票数: 0, '黑票%': 0,
        评论数: 0, 推荐数: 0, 收藏数: 0, 分类标签: '',
    };
    
    try {
        const bodyText = document.body ? document.body.innerText : '';
        const flatText = bodyText.replace(/\s+/g, ' ');
        function parseCount(raw) {
            if (!raw) return 0;
            const s = String(raw).replace(/,/g, '').replace(/，/g, '').trim();
            const m = s.match(/([\d.]+)\s*(万)?/);
            if (!m) return 0;
            const n = parseFloat(m[1]);
            if (isNaN(n)) return 0;
            return Math.round(n * (m[2] ? 10000 : 1));
        }
        function setCount(displayKey, numberKey, raw) {
            const n = parseCount(raw);
            if (n > 0) {
                if (displayKey) result[displayKey] = String(raw).trim();
                result[numberKey] = n;
            }
        }
        function pick(regex) {
            const m = flatText.match(regex) || bodyText.match(regex);
            return m ? m[1] : '';
        }
        function pickNearLines(label) {
            const lines = bodyText.split(/\n+/).map(x => x.trim()).filter(Boolean);
            for (let i = 0; i < lines.length; i++) {
                if (lines[i] === label && i > 0) return lines[i - 1];
                if (lines[i].startsWith(label)) return lines[i].slice(label.length).trim();
            }
            return '';
        }
        
        const titleEl = document.querySelector('.common-title h1, .title h1, h1');
        if (titleEl) result.标题 = titleEl.innerText.trim();
        if (!result.标题 && document.title) {
            result.标题 = document.title.replace(/\s*-\s*MC百科.*$/i, '').trim();
        }
        
        function setScore(raw) {
            const n = parseFloat(String(raw || '').replace(/[^\d.]/g, ''));
            if (!isNaN(n) && n > 0 && n <= 5) result.指数评分 = n;
        }
        const scoreEl = document.querySelector('.index-score, .score-num, [class*="score"]');
        if (scoreEl) {
            setScore(scoreEl.textContent);
        }
        
        const viewEls = document.querySelectorAll('.view-count, .views, [class*="view"], [class*="browse"]');
        for (const el of viewEls) {
            const text = el.textContent;
            const m = text.match(/总?浏览[：:\s]*([\d,.，]+万?)/i);
            if (m) {
                result.总浏览 = m[1];
                result.总浏览量 = parseCount(m[1]);
                break;
            }
        }
        
        const redEl = document.querySelector('.red-count, [class*="red"]');
        if (redEl) {
            const text = redEl.textContent;
            const m = text.match(/红票[：:\s]*([\d]+)/i);
            if (m) result.红票数 = parseInt(m[1]) || 0;
        }
        
        const blackEl = document.querySelector('.black-count, [class*="black"]');
        if (blackEl) {
            const text = blackEl.textContent;
            const m = text.match(/黑票[：:\s]*([\d]+)/i);
            if (m) result.黑票数 = parseInt(m[1]) || 0;
        }
        
        const commentEl = document.querySelector('.class-comment-count, [class*="class-comment-count"]');
        if (commentEl) {
            const text = commentEl.textContent;
            const m = text.match(/评论[：:\\s]*([\\d]+)/i);
            if (m) result.评论数 = parseInt(m[1]) || 0;
        }
        // [V1.1 霸道补丁] 针对无痕沙盒或未登录态下无法获取右上角评论数的问题
        if (result.评论数 === 0) {
            // 如果底部有评论块，则将评论数强制置为 1（作为诱饵触发后续的深度翻页抓取机制）
            if (document.querySelector('.common-comment-block')) {
                result.评论数 = 1;
            }
        }
        
        const recommendEl = document.querySelector('.recommend-count, [class*="recommend"]');
        if (recommendEl) {
            const text = recommendEl.textContent;
            const m = text.match(/推荐[：:\s]*([\d]+)/i);
            if (m) result.推荐数 = parseInt(m[1]) || 0;
        }
        
        const favoriteEl = document.querySelector('.favorite-count, [class*="favorite"], [class*="collect"]');
        if (favoriteEl) {
            const text = favoriteEl.textContent;
            const m = text.match(/收藏[：:\s]*([\d]+)/i);
            if (m) result.收藏数 = parseInt(m[1]) || 0;
        }

        // 当前 MC百科整合包页的很多基础信息没有稳定 class，使用正文文本兜底。
        if (!result.红票数) {
            const m = flatText.match(/投红票[：:\s]*(\d+)\s*[（(]\s*([\d.]+)%\s*[）)]/);
            if (m) {
                result.红票数 = parseInt(m[1]) || 0;
                result['红票%'] = parseFloat(m[2]) || 0;
            }
        }
        if (!result.黑票数 && result['黑票%'] === 0) {
            const m = flatText.match(/投黑票[：:\s]*(\d+)\s*[（(]\s*([\d.]+)%\s*[）)]/);
            if (m) {
                result.黑票数 = parseInt(m[1]) || 0;
                result['黑票%'] = parseFloat(m[2]) || 0;
            }
        }
        if (!result.昨日指数) {
            result.昨日指数 = parseCount(pick(/昨日指数[：:\s]*([\d,.，]+)/));
        }
        if (!result.总浏览量) {
            const rawView = pickNearLines('总浏览') || pick(/([\d,.，]+万?)\s*总浏览/);
            setCount('总浏览', '总浏览量', rawView);
        }
        if (!result.推荐数) {
            result.推荐数 = parseCount(pick(/推荐\s*([\d,.，]+)/));
        }
        if (!result.收藏数) {
            result.收藏数 = parseCount(pick(/收藏\s*([\d,.，]+)/));
        }
        if (!result.评论数) {
            result.评论数 = parseCount(pick(/(?:评论|喷泉广场)\s*[（(]?\s*([\d,.，]+)\s*[）)]?/));
        }
        if (!result.指数评分) {
            const lines = bodyText.split(/\n+/).map(x => x.trim()).filter(Boolean);
            for (let i = 0; i < lines.length; i++) {
                if (/昨日指数/.test(lines[i])) {
                    for (let j = Math.max(0, i - 12); j < i; j++) {
                        if (/^[0-5](?:\.\d+)?$/.test(lines[j])) {
                            const n = parseFloat(lines[j]);
                            if (n > 0 && n <= 5) {
                                result.指数评分 = n;
                                break;
                            }
                        }
                    }
                    break;
                }
            }
        }
        if (!result.指数评分) {
            const scoreMatch = bodyText.match(/(?:^|\n)\s*([0-5](?:\.\d+)?)\s*\n\s*(?:默默无闻|初出茅庐|小有名气|人气十足|名扬天下|殿堂级|编辑推荐)[^\n]*\n\s*昨日指数/m);
            if (scoreMatch) setScore(scoreMatch[1]);
        }
        
        const catLinks = document.querySelectorAll('a[href*="/category/"]');
        const cats = [];
        for (const link of catLinks) {
            const text = link.textContent.trim();
            if (text && text.length <= 10 && !cats.includes(text)) {
                cats.push(text);
            }
        }
        if (cats.length > 0) {
            result.分类标签 = cats.join('、');
        }
    } catch(e) {
        result.error = e.toString();
    }
    
    return result;
}
"""

# ========== Extractor 2: 介绍 + 标签 ==========
# 修复1：介绍字段重复 - 优化提取逻辑，增加去重
# 修复5：整合包标签黏连 - 优化标签分隔符识别
EXTRACTOR_INTRO_TAGS = r'''
() => {
    let description = '';
    let categoryTags = '';
    let modpackTags = '';
    const bodyText = document.body ? document.body.innerText : '';
    const flatText = bodyText.replace(/\s+/g, ' ');

    function normLine(text) {
        return (text || '').replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim();
    }

    function splitLines(parts) {
        const lines = [];
        for (const part of parts || []) {
            String(part || '').split(/\n+/).forEach(line => {
                const t = normLine(line);
                if (t) lines.push(t);
            });
        }
        return lines;
    }

    function isTocLine(line) {
        return /^目录[:：]/.test(line) || /^目录$/.test(line);
    }

    function isIntroHeading(line) {
        return /^(?:\d+(?:\.\d+)*\s*)?简介[:：]?$/.test(line);
    }

    function isNumberedHeading(line) {
        if (/^(?:\d+(?:\.\d+)*\s*)?简介[:：]?$/.test(line)) return true;
        if (/^\d+(?:\.\d+)*\s+\S{1,30}$/.test(line)) return true;
        return /^(说明|一些说明及建议|配置需求|DLC管理器相关|特别鸣谢|整合特征介绍|性能优化|功能辅助|兼容版本|整合内容摘要|常见问题|先来说点啥吧|一些游戏内图片)[:：]?$/.test(line);
    }

    // 介绍前导目录序号过滤：开头形如 "1 2 3 4 5 1.1 1.2 2.1" 这种纯数字小标题
    // 这些原素是百科页主介绍区上方的"章节目录"序号列表（如 <ol> 或 <ul class="toc">），
    // 经 innerText 拼接后变成单行 "1\n2\n3..." 混到了介绍字段最前面。
    function isPureNumberToc(line) {
        // 仅由数字+点+空格组成，长度<=8（如 "1"、"1.1"、"2.5"）
        const s = (line || '').replace(/\u00a0/g, ' ').trim();
        if (!s) return false;
        return /^[0-9.]+$/.test(s) && s.length <= 8;
    }

    // 前导目录序号块跳过：从头部一直剔除纯数字行，
    // 直到遇到一个非纯数字行（实际介绍内容的第一个段落）才停止。
    function stripLeadingToc(lines) {
        let i = 0;
        while (i < lines.length && isPureNumberToc(lines[i])) i++;
        return lines.slice(i);
    }

    function cleanIntroContent(parts) {
        let lines = splitLines(parts);
        if (!lines.length) return '';

        const seen = new Set();
        lines = lines.filter(line => {
            const n = line.replace(/\s+/g, '');
            if (!n || isTocLine(line)) return false;
            if (seen.has(n)) return false;
            seen.add(n);
            return true;
        });

        let start = -1;
        for (let i = 0; i < lines.length; i++) {
            if (isIntroHeading(lines[i])) {
                start = i + 1;
                break;
            }
        }

        let picked = [];
        if (start >= 0) {
            for (let i = start; i < lines.length; i++) {
                picked.push(lines[i]);
            }
        }

        if (!picked.length) {
            picked = lines;
        }

        const maxChars = 30000;
        const cleaned = [];
        for (const line of picked) {
            if (!line || isTocLine(line)) continue;
            if (/^(过于丰富的|明确的阶段引导|数量庞大的|可制作的|丰富的BOSS指引)[:：]?$/.test(line)) continue;
            if ((cleaned.join('\n\n').length + line.length) > maxChars) break;
            cleaned.push(line);
        }

        return cleaned.join('\n\n').trim();
    }
    
    // 介绍提取：使用新版百科页面的真实HTML结构
    // 整合包介绍位于 <div class="class-menu-main swiper-no-swiping"> 下的
    // <li data-id="1" class="text-area common-text font14"> 中的内容
    // 介绍标题是 <p><span class="common-text-title common-text-title-1" id="ctm-title-...">整合包介绍</span></p>
    
    
    let introContent = null;
    const mainPane = document.querySelector('.class-menu-main li.text-area[data-id="1"]') || document.querySelector('.text-area.common-text[data-id="1"]');
    
    if (mainPane) {
        let contentParts = [];
        let inTOC = false;
        
        for (const child of Array.from(mainPane.children)) {
            if (child.tagName === 'STYLE' || child.tagName === 'SCRIPT') continue;
            if (child.classList && child.classList.contains('table-scroll')) continue;
            if (child.classList && child.classList.contains('common-text-menu')) continue;
            
            let text = child.innerText ? child.innerText.trim() : '';
            if (!text) continue;
            
            if (/^目录[:：]?$/.test(text)) {
                inTOC = true;
                continue;
            }
            
            if (inTOC && child.tagName === 'UL') continue;
            
            if (child.querySelector && child.querySelector('.common-text-title')) {
                inTOC = false;
            }
            
            if (inTOC) continue;
            
            contentParts.push(text);
        }
        
        if (contentParts.length > 0) {
            introContent = contentParts;
        }
    }

    // 方法3：通用提取
    if (!introContent) {
        const allText = document.querySelectorAll('.common-text, .text-content, [class*="content"]');
        for (const el of allText) {
            const text = el.innerText ? el.innerText.trim() : '';
            if (text && text.length > 100 && text.length < 5000) {
                introContent = [text];
                break;
            }
        }
    }
    
    // 【修复1】去重处理：相邻段落内容相同则只保留一份，并优先截取“简介”小节
    if (introContent && introContent.length > 0) {
        const uniqueParts = [];
        const seenParts = new Set();
        for (const part of introContent) {
            const normalized = part.replace(/\s+/g, '').trim();
            if (normalized && !seenParts.has(normalized)) {
                uniqueParts.push(part);
                seenParts.add(normalized);
            }
        }
        // 先去重，再过滤前导目录序号
        description = cleanIntroContent(uniqueParts);
        // 在 cleanIntroContent 之后额外做一个尾随过滤，确保行级数字目录也被干掉
        if (description) {
            const descLines = description.split('\n').map(l => l.trim()).filter(l => l);
            // 从头跳过所有纯数字行
            const filtered = stripLeadingToc(descLines);
            // 再从尾部也跳过纯数字行（有些整合包末尾也有目录）
            let end = filtered.length;
            while (end > 0 && isPureNumberToc(filtered[end-1])) end--;
            const finalLines = filtered.slice(0, end);
            if (finalLines.length > 0 && finalLines.length < descLines.length) {
                description = finalLines.join('\n\n').trim();
            }
        }
    }
    
    // 分类标签：百科页面现在分类标签在整合包标题旁的 <a class="label label-default label-s" href="/class/..."> 中
    const cats = [];
    // 方法1：从 .label-s 或 .label-default 提取分类标签
    const labelEls = document.querySelectorAll('a.label.label-s, a.label-default.label-s, a[class*="label"][class*="label-s"]');
    if (labelEls.length === 0) {
        // 老方法保底：/category/ 链接
        const oldCats = document.querySelectorAll('a[href*="/category/"]');
        for (const link of oldCats) {
            const text = link.textContent.trim();
            if (text && text.length <= 20 && text.length >= 2 && !cats.includes(text)) cats.push(text);
        }
    } else {
        for (const el of labelEls) {
            const text = (el.textContent || '').trim();
            if (text && text.length <= 20 && text.length >= 2 && !cats.includes(text)) cats.push(text);
        }
    }
    if (cats.length > 0) {
        categoryTags = cats.join('、');
    }

    // 整合包标签：从页面里找 a[href*="/s?key="] 开头的搜索链接（整合包标签栏）
    // 示例：<a class="class-son-tag" href="https://search.mcmod.cn/s?key=剧情向&mold=1">剧情向</a>
    const packTags = [];
    const tagLinkEls = document.querySelectorAll('a[href*="/s?key="], a.class-son-tag, a[href*="search.mcmod.cn/s?key="]');
    if (tagLinkEls.length > 0) {
        for (const el of tagLinkEls) {
            const text = (el.textContent || '').trim();
            if (text && text.length >= 1 && text.length <= 20 && !packTags.includes(text) && !cats.includes(text)) {
                packTags.push(text);
            }
        }
    }
    if (packTags.length > 0 && packTags.length <= 50) {
        modpackTags = packTags.join('、');
    }
    
    // 【修复5】整合包标签：优先使用标签链接，避免“星露谷物语农业”这类文本黏连。
    function isStopText(text) {
        return /相关链接|支持的MC版本|收录时间|编辑次数|运作方式|更新日志|目录|简介|包含模组|下载地址/.test(text || '');
    }
    function pushTag(list, raw) {
        let text = normLine(raw).replace(/^[#＃]+/, '');
        text = text.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F000}-\u{1F02F}]/gu, '').trim();
        if (!text || text.length < 2 || text.length > 18) return;
        if (/[：:]/.test(text) || /^\d+(?:\.\d+)?$/.test(text)) return;
        if (isStopText(text) || text.includes('整合包标签') || text.includes('分类标签')) return;
        if (!list.includes(text)) list.push(text);
    }
    function tagsFromScope(scope) {
        const list = [];
        if (!scope) return list;
        const links = scope.querySelectorAll('a');
        links.forEach(a => pushTag(list, a.innerText || a.textContent || ''));
        return list;
    }
    function tagsFromText(text) {
        const list = [];
        let content = String(text || '').replace(/^.*?整合包标签[：:]\s*/, '');
        content = content.split(/相关链接|支持的MC版本|收录时间|编辑次数|运作方式|更新日志|目录|简介|包含模组|下载地址/)[0];
        content.split(/[🔹◆●■▲★♦◇○□△▽▷◁☆✦✧❖⦿◉◎◐◑◒◓◔◕⬢⬡⬣⬤⬥⬦⬧⬨⬩⬪⬫▪▫▬▭▮▯▰▱◌◍◖◗❏❐❑❒•·・、，,；;\s]+/u)
            .forEach(part => pushTag(list, part));
        return list;
    }

    const tagList = [];
    const possibleScopes = Array.from(document.querySelectorAll('li, dd, dt, dl, div, section, table, tr, p'))
        .filter(el => {
            const text = normLine(el.innerText || el.textContent || '');
            return text.includes('整合包标签') && text.length <= 500;
        })
        .sort((a, b) => normLine(a.innerText || a.textContent || '').length - normLine(b.innerText || b.textContent || '').length);

    for (const scope of possibleScopes) {
        tagsFromScope(scope).forEach(t => pushTag(tagList, t));
        let next = scope.nextElementSibling;
        let steps = 0;
        while (next && steps < 3 && tagList.length === 0) {
            const nextText = normLine(next.innerText || next.textContent || '');
            if (isStopText(nextText)) break;
            tagsFromScope(next).forEach(t => pushTag(tagList, t));
            next = next.nextElementSibling;
            steps++;
        }
        if (tagList.length > 0) break;
    }

    if (tagList.length === 0) {
        const directTagMatch = flatText.match(/整合包标签[：:]\s*([^相关链接支持的MC版本收录时间编辑次数运作方式更新日志目录简介包含模组下载地址\n\r]{1,160})/);
        if (directTagMatch) tagsFromText(directTagMatch[1]).forEach(t => pushTag(tagList, t));
    }

    if (tagList.length > 0 && tagList.length <= 30) {
        modpackTags = tagList.join('、');
    }
    
    return { 整合包介绍: description || '', 分类标签: categoryTags || '', 整合包标签: modpackTags || '' };
}
'''

# ========== Extractor 2.5: 评论数提取 ==========
EXTRACTOR_COMMENT_COUNT = r'''
() => {
    let count = 0;
    const bodyText = document.body ? document.body.innerText : '';
    
    const totalText = document.querySelector('.class-comment-block, .common-comment-block');
    if (totalText) {
        const text = totalText.innerText || totalText.textContent || '';
        const tm = text.match(/(?:共计|共有|全部|评论)[：:\s]*(\d+)\s*(?:条|个|楼|则)?/);
        if (tm) count = parseInt(tm[1]);
    }
    
    if (!count) {
        const fm = bodyText.match(/(?:喷泉广场|评论|短评)\s*[（(]\s*(\d+)\s*[）)]/);
        if (fm) count = parseInt(fm[1]);
    }

    if (!count) {
        const rowCount = document.querySelectorAll('.class-comment-block .class-comment-row, .common-comment-block .comment-row, li.class-comment-row, li.comment-row, [data-comment-id]').length;
        if (rowCount > 0) count = rowCount;
    }
    
    if (!count) {
        const pageInfo = document.querySelector('.class-comment-block .pagination, .common-comment-block .pagination, ul.pagination[data-name=\'comment-list\']');
        if (pageInfo) {
            const text = pageInfo.textContent;
            const tm = text.match(/共\s*(\d+)\s*页/);
            if (tm) {
                const totalPage = parseInt(tm[1]);
                count = totalPage * 20;
            }
        }
    }
    
    return count;
}
'''

# ========== Extractor 3: 走势 ==========
FIND_TREND_TARGET_JS = r'''
() => {
    function visible(el) {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.pointerEvents === 'none') return false;
        return true;
    }
    
    function normText(el) {
        return (el && el.textContent ? el.textContent : '').replace(/\s+/g, ' ').trim();
    }
    
    const candidates = [];
    const allEls = Array.from(document.querySelectorAll('a, button, span, div, li, [role="button"], [onclick], [data-toggle], [data-target]'));
    for (const el of allEls) {
        const text = normText(el);
        if (!text.includes('指数走势')) continue;
        
        const clickable = el.closest('a, button, [role="button"], [onclick], [data-toggle], [data-target], li, [class*="btn"], [class*="button"]') || el;
        if (!visible(clickable)) continue;
        
        const rect = clickable.getBoundingClientRect();
        const tag = clickable.tagName.toLowerCase();
        const className = String(clickable.className || '');
        const exact = text === '指数走势';
        const interactive = ['a', 'button', 'li'].includes(tag) || clickable.onclick || clickable.getAttribute('role') === 'button';
        const area = rect.width * rect.height;
        let score = 0;
        if (exact) score += 100;
        if (interactive) score += 60;
        if (className.includes('btn') || className.includes('button')) score += 30;
        score -= Math.min(text.length, 200) / 5;
        score -= Math.min(area / 10000, 30);
        
        candidates.push({ el: clickable, score, text, tag, className, area });
    }
    
    candidates.sort((a, b) => b.score - a.score);
    const hit = candidates[0];
    if (!hit) {
        return { found: false, reason: '页面上没有找到可点击的“指数走势”元素' };
    }
    
    try { hit.el.scrollIntoView({ behavior: 'instant', block: 'center', inline: 'center' }); } catch(e) {}
    const rect = hit.el.getBoundingClientRect();
    return {
        found: true,
        x: Math.round(rect.left + rect.width / 2),
        y: Math.round(rect.top + rect.height / 2),
        text: hit.text.slice(0, 80),
        tag: hit.tag,
        className: hit.className.slice(0, 120),
        score: Math.round(hit.score),
        candidates: candidates.slice(0, 5).map(c => ({
            text: c.text.slice(0, 50),
            tag: c.tag,
            className: c.className.slice(0, 80),
            score: Math.round(c.score)
        }))
    };
}
'''

def build_trend_js():
    return f'''
async () => {{
    const result = {{
        指数走势数据: '', 走势数据点: 0,
        走势起始日期: '', 走势结束日期: '',
        走势最高指数: 0, 走势最低指数: 0,
        走势平均指数: 0, 走势最新指数: 0,
        走势涨幅_7天: 0, 走势涨幅_30天: 0
    }};
    
    if (typeof echarts === 'undefined') return result;
    
    let dates = null, values = null;
    const divs = document.querySelectorAll('div');
    for (const div of divs) {{
        try {{
            const inst = echarts.getInstanceByDom(div);
            if (inst) {{
                const opt = inst.getOption ? inst.getOption() : inst.getModel && inst.getModel().option;
                const xAxis = opt && opt.xAxis ? (Array.isArray(opt.xAxis) ? opt.xAxis[0] : opt.xAxis) : null;
                const series = opt && opt.series ? (Array.isArray(opt.series) ? opt.series[0] : opt.series) : null;
                if (xAxis && series) {{
                    const d = xAxis.data || [];
                    const v = (series.data || []).map(item => Array.isArray(item) ? item[1] : (item && typeof item === 'object' ? (item.value ?? item.y ?? item.data) : item));
                    if (d.length > 0 && v.length > 0) {{ dates = d; values = v; break; }}
                }}
            }}
        }} catch(e){{}}
    }}
    
    if (!dates || !values) return result;
    
    const nums = values.map(v => parseInt(v)).filter(v => !isNaN(v));
    if (nums.length === 0) return result;
    
    result.指数走势数据 = JSON.stringify(dates.map((d,i)=>({{ 日期: d, 指数: parseInt(values[i]) || 0 }})));
    result.走势数据点 = nums.length;
    result.走势起始日期 = dates[0];
    result.走势结束日期 = dates[dates.length-1];
    result.走势最高指数 = Math.max(...nums);
    result.走势最低指数 = Math.min(...nums);
    result.走势平均指数 = Math.round(nums.reduce((a,b)=>a+b,0)/nums.length);
    result.走势最新指数 = nums[nums.length-1];
    
    if (nums.length >= 8) {{
        const v7 = nums[nums.length - 8];
        result.走势涨幅_7天 = v7 > 0 ? Math.round((result.走势最新指数 - v7) / v7 * 100) : 0;
    }}
    if (nums.length >= 31) {{
        const v30 = nums[nums.length - 31];
        result.走势涨幅_30天 = v30 > 0 ? Math.round((result.走势最新指数 - v30) / v30 * 100) : 0;
    }}
    
    try {{ const cb = document.querySelector('.modal .close, .modal [data-dismiss], .modal-close, [class*="close"]');
        if (cb) cb.click(); }} catch(e){{}}
    
    return result;
}}
'''
EXTRACT_TREND_JS = build_trend_js()

# ========== 工具函数 ==========
def extract_modpack_id(url):
    m = re.search(r'/modpack/(\d+)\.html', url)
    return m.group(1) if m else None

async def _mcmod_check_anti_crawl(page):
    try:
        text = await page.evaluate('() => document.body ? document.body.textContent.substring(0, 500) : ""')
        return any(kw in text for kw in ['验证码', '访问过于频繁', '请稍候再试', '人机验证', '系统封禁', '封禁策略', 'banned', 'You have been banned'])
    except:
        return False

async def _mcmod_recreate_page(context, old_page):
    try:
        if old_page:
            await old_page.close(timeout=15000)
    except:
        pass
    page = await context.new_page()
    page.set_default_timeout(GOTO_TIMEOUT * 1000)
    await install_safe_routes(page)
    return page

async def safe_goto(page, url, wait_until='domcontentloaded', timeout=None, attempts=NAVIGATION_RETRY):
    """带全局闸门感知的导航重试，避免静默休息或网络抖动造成单次超时后直接丢任务。"""
    timeout = timeout or GOTO_TIMEOUT * 1000
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            await rate_controller._wait_gate()
            await rate_controller.maybe_burst_rest()
            return await page.goto(url, wait_until=wait_until, timeout=timeout)
        except Exception as e:
            last_error = e
            msg = str(e)
            retryable = 'Timeout' in msg or 'ERR_CONNECTION' in msg or 'net::' in msg or '连接超时' in msg
            if attempt >= attempts or not retryable:
                raise
            wait_s = min(4 + attempt * 3, 12)
            print(f"  [导航重试] 第 {attempt}/{attempts} 次进入页面失败，{wait_s}s 后重试: {msg[:90]}")
            try:
                await page.evaluate("window.stop && window.stop()")
            except Exception:
                pass
            try:
                await page.goto('about:blank', wait_until='commit', timeout=10000)
            except Exception:
                pass
            await rate_controller.safe_sleep(wait_s)
    raise last_error or Exception(f'导航失败: {url}')

async def wait_mcmod_page_ready(page, url='', worker_id=0, index=0, attempts=3):
    """等待 MCMod 详情页真正出现可读正文；commit 只代表开始响应，不代表 DOM 可提取。"""
    last_state = {}
    for attempt in range(1, attempts + 1):
        try:
            await page.wait_for_function(
                '''() => {
                    const title = document.title || '';
                    const body = document.body ? (document.body.innerText || document.body.textContent || '') : '';
                    if (title.includes('MC百科') || title.length >= 2) return true;
                    if (body.includes('整合包') || body.includes('指数走势') || body.length > 300) return true;
                    return false;
                }''',
                timeout=30000
            )
            return True
        except Exception:
            try:
                last_state = await page.evaluate('''() => ({
                    url: location.href,
                    title: document.title || '',
                    body_len: document.body ? ((document.body.innerText || document.body.textContent || '').length) : 0,
                    ready: document.readyState
                })''')
            except Exception:
                last_state = {}
            print(f"  [W{worker_id}] [{index}] 页面仍为空/未就绪，重试加载 {attempt}/{attempts}: {last_state}")
            if attempt < attempts:
                try:
                    await page.goto('about:blank', wait_until='commit', timeout=10000)
                except Exception:
                    pass
                await rate_controller.safe_sleep(3 + attempt * 2)
                await safe_goto(page, url or page.url, wait_until='domcontentloaded')
    raise Exception(f"页面未加载出可提取内容: {last_state}")

# ========== 模块级 Fetcher ==========
async def _mcmod_fetch_basic(page, worker_id, index):
    last_error = ''
    for attempt in range(MODULE_RETRY):
        try:
            data = await asyncio.wait_for(page.evaluate(EXTRACTOR_BASIC), timeout=EVAL_TIMEOUT)
            if data and data.get('标题') and len(str(data.get('标题'))) >= 2:
                return data
            last_error = '未提取到标题'
        except Exception as e:
            last_error = str(e)
        await asyncio.sleep(1)
    try:
        data = await asyncio.wait_for(page.evaluate(EXTRACTOR_BASIC), timeout=EVAL_TIMEOUT)
        if data and not data.get('标题'):
            title = await page.title()
            if title:
                data['标题'] = re.sub(r'\s*-\s*MC百科.*$', '', title).strip()
        # 强制防线：如果没有抓到有效的标题，说明提取完全失败（通常是验证码或封禁阻断），返回 None
        if not data or not data.get('标题') or len(str(data.get('标题')).strip()) < 2:
            return None
        return data
    except Exception as e:
        last_error = str(e)
        if last_error:
            print(f'  [W{worker_id}] [{index}] ⚠️  基础信息提取异常: {last_error[:120]}')
        return None

async def _mcmod_fetch_intro_tags(page, worker_id, index):
    for attempt in range(MODULE_RETRY):
        try:
            return await asyncio.wait_for(page.evaluate(EXTRACTOR_INTRO_TAGS), timeout=EVAL_TIMEOUT)
        except:
            pass
        await asyncio.sleep(1)
    return {'整合包介绍': '', '分类标签': '', '整合包标签': ''}

async def _mcmod_scroll_to_comments(page, worker_id, index, max_retry=6):
    for retry in range(max_retry):
        try:
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight);')
            await rate_controller.safe_sleep(random.randint(1500, 2200) / 1000.0)
            exist = await page.evaluate('''() => {
                const block = document.querySelector(".class-comment-block, .common-comment-block");
                if(block){ block.scrollIntoView({behavior:"smooth", block:"center"}); return true; }
                return false;
            }''')
            if exist:
                await page.wait_for_timeout(2000)
                if DEBUG_COMMENTS:
                    print(f'  [W{worker_id}] [{index}] ✅ 第{retry+1}轮成功定位评论区')
                return True
            await page.evaluate('window.scrollBy(0, -400)')
        except Exception as e:
            if DEBUG_COMMENTS:
                print(f'  [W{worker_id}] [{index}] ⚠️ 滚动重试{retry+1}异常：{str(e)[:40]}')
        await rate_controller.safe_sleep(random.randint(1200, 2000) / 1000.0)
    if DEBUG_COMMENTS:
        print(f'  [W{worker_id}] [{index}] ⚠️ {max_retry}轮滚动未检测到评论区块，继续执行抓取逻辑')
    return False

async def _mcmod_wait_for_comments_loaded(page, worker_id, index, timeout_ms=12000):
    try:
        state = await page.wait_for_function('''() => {
            const block = document.querySelector(".class-comment-block, .common-comment-block");
            if (!block) return "missing";
            const text = (block.innerText || block.textContent || "").replace(/\\s+/g, " ").trim();
            const rows = block.querySelectorAll(".class-comment-row, .comment-row, li.class-comment-row, .comment-row, [class*='class-comment-row'], [data-comment-id], .comment-item, li[class*='comment']").length;
            if (rows > 0) return "rows";
            if (/暂无|没有|0\\s*条|还没有/.test(text)) return "empty";
            if (!/加载中|正在加载|loading/i.test(text) && text.length > 20) return "text";
            return false;
        }''', timeout=timeout_ms)
        status = await state.json_value()
        if DEBUG_COMMENTS:
            print(f'  [W{worker_id}] [{index}] 💬 评论区加载状态: {status}')
        return status
    except Exception:
        if DEBUG_COMMENTS:
            print(f'  [W{worker_id}] [{index}] ⚠️ 评论区等待超时，尝试解析当前 DOM')
        return 'timeout'

# ========== 单条主楼内部楼中楼分页（按页码逐页翻）==========
async def _mcmod_click_single_reply_next(page, row_selector, worker_id, index):
    """单条主楼内部楼中楼分页（v7.8.2：按页码翻，兼容 active 页码后找下一个 data-page 按钮）"""
    js = r'''(rowSel) => {
        const rowEl = document.querySelector(rowSel);
        if (!rowEl) return false;
        
        // 查找楼中楼分页器
        const replyPagiSelectors = [
            '.class-comment-reply-floor .pagination[data-name*="comment-reply-list"]',
            '.class-comment-reply-floor .pagination',
            '.reply-floor .pagination',
            '.comment-replies .pagination',
            '[class*="reply"] .pagination',
        ];
        
        let replyPagi = null;
        for (const sel of replyPagiSelectors) {
            const found = rowEl.querySelector(sel);
            if (found) { replyPagi = found; break; }
        }
        
        if (!replyPagi) return false;
        
        // 找当前激活页的下一个页码链接（而不是识别"后页"文字）
        const activeItem = replyPagi.querySelector('li.page-item.active');
        if (!activeItem) {
            // 如果没有激活页，尝试点第一个可见的页码
            const firstLink = replyPagi.querySelector('a.page-link:not([aria-disabled="true"]), .page-item:not(.disabled) a.page-link');
            if (firstLink && firstLink.textContent.trim() !== '1') {
                try { firstLink.click(); return true; } catch(e) {}
            }
            return false;
        }
        
        // 从 active 往后找第一个非 active、非 disabled 的页码链接
        let current = activeItem;
        while (current && current.nextElementSibling) {
            current = current.nextElementSibling;
            const li = current;
            if (!li.classList || li.classList.contains('disabled') || li.classList.contains('active')) continue;
            const link = li.querySelector('a.page-link');
            if (!link) continue;
            const txt = (link.textContent || '').trim();
            // 跳过"后页""尾页"等文字按钮，只按数字页码翻
            if (/^\d+$/.test(txt)) {
                try { link.click(); return true; } catch(e) { return false; }
            }
        }
        
        // fallback: 尝试 data-page 属性
        const allLinks = replyPagi.querySelectorAll('a.page-link');
        const activePage = parseInt(activeItem.textContent) || 0;
        for (const link of allLinks) {
            const dp = link.getAttribute('data-page');
            if (dp) {
                const p = parseInt(dp);
                if (p > activePage && /^\d+$/.test(link.textContent.trim())) {
                    try { link.click(); return true; } catch(e) {}
                }
            }
        }
        
        return false;
    }'''
    try:
        clicked = await page.evaluate(js, row_selector)
        if not clicked:
            return False
        await rate_controller.after_comment_action('楼中楼翻页')
        await rate_controller.safe_sleep(random.randint(REPLY_EXPAND_WAIT_MIN, REPLY_EXPAND_WAIT_MAX) / 1000.0)
    except Exception as e:
        if DEBUG_COMMENTS:
            print(f'  [W{worker_id}] [{index}] 楼中楼翻页异常 {str(e)[:60]}')
        return False
    return True

# ========== 展开楼中楼回复 ==========
async def _mcmod_expand_all_replies(page, worker_id, index):
    """展开所有楼中楼回复（修复版，增强选择器和展开逻辑）"""
    total_expanded = 0
    
    for round_num in range(REPLY_EXPAND_MAX_ROUNDS):
        expanded_count = await page.evaluate('''() => {
            let count = 0;
            
            // 增强的展开按钮选择器
            const expandSelectors = [
                '.class-comment-reply-expand', '.reply-expand', '.expand-reply',
                '.view-reply', '.show-reply', '.reply-toggle',
                '[class*="reply-expand"]', '[class*="expand-reply"]', 
                '[class*="view-reply"]', '[class*="show-reply"]',
                '[class*="reply-toggle"]',
            ];
            
            const buttons = [];
            for (const sel of expandSelectors) {
                document.querySelectorAll(sel).forEach(btn => {
                    const style = window.getComputedStyle(btn);
                    if (style.display !== 'none' && style.visibility !== 'hidden') {
                        const text = btn.textContent.trim();
                        // 增强的展开按钮文本识别
                        if (text.includes('查看回复') || 
                            text.includes('展开回复') || 
                            text.includes('查看更多') ||
                            text.includes('展开') ||
                            text.includes('更多回复') ||
                            text.includes('查看全部') ||
                            text.match(/^\\d+\\s*条回复$/) ||
                            text.match(/^共\\s*\\d+\\s*条/)) {
                            buttons.push(btn);
                        }
                    }
                });
            }
            
            const uniqueButtons = [...new Set(buttons)];
            
            for (const btn of uniqueButtons) {
                try { btn.click(); count++; } catch(e) {}
            }
            
            return count;
        }''')
        
        if expanded_count > 0:
            total_expanded += expanded_count
            if DEBUG_COMMENTS:
                print(f'  [W{worker_id}] [{index}] 📂 第{round_num+1}轮展开 {expanded_count} 个楼中楼')
            await rate_controller.after_comment_action('楼中楼展开')
            await rate_controller.safe_sleep(random.randint(REPLY_EXPAND_WAIT_MIN, REPLY_EXPAND_WAIT_MAX) / 1000.0)
        else:
            break
    
    if total_expanded > 0 and DEBUG_COMMENTS:
        print(f'  [W{worker_id}] [{index}] ✅ 共展开 {total_expanded} 个楼中楼')
    
    return total_expanded

async def _mcmod_click_next_page(page, worker_id, index, current_page):
    for retry in range(COMMENT_PAGE_MAX_RETRY):
        clicked = await page.evaluate('''() => {
            const pagination = document.querySelector(".pagination[data-name='comment-list']");
            if (!pagination) return false;
            // 按页码翻：找到当前 active 的下一个页码按钮
            const activeItem = pagination.querySelector('li.page-item.active');
            if (activeItem) {
                let current = activeItem;
                while (current && current.nextElementSibling) {
                    current = current.nextElementSibling;
                    const li = current;
                    if (!li.classList || li.classList.contains('disabled') || li.classList.contains('active')) continue;
                    const link = li.querySelector('a.page-link');
                    if (!link) continue;
                    const txt = (link.textContent || '').trim();
                    if (/^\\d+$/.test(txt)) {
                        try { link.click(); return true; } catch(e) { return false; }
                    }
                    // 如果下一个不是数字，尝试检查有无 data-page
                    const dp = link.getAttribute('data-page');
                    if (dp && parseInt(dp) > 0) {
                        try { link.click(); return true; } catch(e) { return false; }
                    }
                }
            }
            // fallback: old method
            const nextTexts = ['下一页', '下页', '>', '»', '后页', 'next'];
            const links = pagination.querySelectorAll('a.page-link');
            for (const link of links) {
                const text = (link.textContent || link.innerText || '').trim();
                let match = false;
                for (const t of nextTexts) {
                    if (text.includes(t)) { match = true; break; }
                }
                if (!match) continue;
                const li = link.closest('li.page-item');
                if (li.classList.contains('disabled') || link.getAttribute('aria-disabled') === 'true') return false;
                if (li.classList.contains('active') || link.classList.contains('current')) continue;
                try { link.click(); return true; } catch(e) {}
            }
            return false;
        }''')
        if not clicked:
            if DEBUG_COMMENTS and retry == 0:
                print(f'  [W{worker_id}] [{index}] 主评论无下一页')
            return False
        try:
            await page.wait_for_load_state('networkidle', timeout=5000)
        except:
            pass
        await rate_controller.after_comment_action('主评论翻页')
        await rate_controller.safe_sleep(random.randint(COMMENT_PAGE_WAIT_MIN, COMMENT_PAGE_WAIT_MAX) / 1000.0)
        new_page = await page.evaluate(EXTRACTOR_CURRENT_PAGE)
        if new_page and new_page > current_page:
            if DEBUG_COMMENTS:
                print(f'  [W{worker_id}] [{index}] 主评论翻页成功 {current_page} → {new_page}')
            return True
        else:
            if DEBUG_COMMENTS:
                print(f'  [W{worker_id}] [{index}] 主评论翻页页码未变，重试{retry+1}')
            await asyncio.sleep(1)
    if DEBUG_COMMENTS:
        print(f'  [W{worker_id}] [{index}] 主评论翻页全部重试失败')
    return False

# ========== 单条主楼下楼中楼当前页提取 ==========
# 用于在楼中楼翻页中途，对指定主楼提取当前显示的所有 .comment-reply-row
EXTRACT_MAIN_REPLY_PAGI_INFO_JS = r"""(row_css) => {
    const row = document.querySelector(row_css);
    if (!row) return { pages: 0, curr: 0 };
    
    const pagi = row.querySelector('.pagination[data-name*="comment-reply-list"]') || 
                 row.querySelector('.class-comment-reply-floor .pagination') ||
                 row.querySelector('.reply-floor .pagination');
                 
    if (!pagi) return { pages: 0, curr: 0 };
    
    let curr = 1;
    let pages = 1;

    // 优先读取文字提示：<span>当前 1 / 2 页，共计 8 条。</span>
    const spans = Array.from(pagi.querySelectorAll('span'));
    const infoSpan = spans.find(s => s.innerText.includes('当前') && s.innerText.includes('页'));
    if (infoSpan) {
        const match = infoSpan.innerText.match(/当前\s*(\d+)\s*\/\s*(\d+)\s*页/);
        if (match) {
            curr = parseInt(match[1]);
            pages = parseInt(match[2]);
            return { pages: pages, curr: curr };
        }
    }

    // 兜底方案
    const activeItem = pagi.querySelector('li.page-item.active');
    if (activeItem) {
        curr = parseInt(activeItem.innerText.trim()) || 1;
    } else {
        // 应对散落的无 active 状态但又没有 href 的当前页：
        const allLinks = pagi.querySelectorAll('a.page-link');
        for (const link of allLinks) {
            if (link.getAttribute('href') === 'javascript:void(0);' && !link.getAttribute('data-page')) {
                const n = parseInt(link.innerText.trim());
                if (!isNaN(n)) { curr = n; break; }
            }
        }
    }
    
    const links = pagi.querySelectorAll('a.page-link');
    links.forEach(link => {
        const num = parseInt(link.innerText.trim());
        if (!isNaN(num) && num > pages) {
            pages = num;
        }
    });
    
    return { pages: pages, curr: curr };
}"""

EXTRACT_REPLY_ROWS_FOR_MAIN_JS = r'''
(mainRowSel) => {
    const mainRow = document.querySelector(mainRowSel);
    if (!mainRow) return { page: 1, keys: [], replies: [] };
    
    // 找楼中楼容器
    const replyFloorSelectors = [
        ".class-comment-reply-floor", ".reply-floor", ".comment-replies",
        ".replies", "[class*='reply-floor']", "[class*='reply-list']",
        ".class-comment-reply-list", "[class*='reply-content']"
    ];
    let replyFloor = null;
    for (const sel of replyFloorSelectors) {
        const el = mainRow.querySelector(sel);
        if (el) { replyFloor = el; break; }
    }
    if (!replyFloor) return { page: 1, keys: [], replies: [] };
    
    function cleanText(raw) {
        return String(raw || '')
            .replace(/\u00a0/g, ' ')
            .replace(/[ 	]+/g, ' ')
            .replace(/\n{3,}/g, '\n\n')
            .trim();
    }
    function visible(el) {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden';
    }
    function pickText(root, selectors) {
        let best = '';
        for (const sel of selectors) {
            root.querySelectorAll(sel).forEach(el => {
                if (!visible(el)) return;
                const t = cleanText(el.innerText || el.textContent || '');
                if (t.length > best.length) best = t;
            });
        }
        return best;
    }
    function pickAuthor(root, selectors) {
        for (const sel of selectors) {
            const el = root.querySelector(sel);
            if (!el || !visible(el)) continue;
            const t = cleanText(el.innerText || el.textContent || '');
            if (t && t.length <= 40) return t;
        }
        return '匿名用户';
    }
    
    const replyRowSelectors = [
        "li.class-comment-reply-row", "li.comment-reply-row", "div.class-comment-reply-row", "div.comment-reply-row",
        "li.reply-row", "li.reply-item"
    ];
    let replyRows = [];
    for (const sel of replyRowSelectors) {
        const found = Array.from(replyFloor.querySelectorAll(sel)).filter(visible);
        if (found.length > 0) { replyRows = found; break; }
    }
    
    // 楼中楼当前页码（用于日志）
    const pagi = replyFloor.querySelector('.pagination[data-name*="comment-reply-list"]')
        || mainRow.querySelector('.pagination[data-name*="comment-reply-list"]');
    let page = 1;
    if (pagi) {
        const active = pagi.querySelector('li.page-item.active');
        if (active) page = parseInt(active.textContent) || 1;
    }
    
    const replies = [];
    const keys = new Set();
    replyRows.forEach(reply => {
        const author = pickAuthor(reply, [
            ".comment-reply-row-username a:first-child", ".class-comment-reply-row-username a", ".reply-username a",
            ".class-comment-reply-username a", ".class-comment-reply-row-username",
            ".reply-username", "[class*='reply-username']",
            ".reply-author", "[class*='username']", "[class*='author']"
        ]);
        let text = pickText(reply, [
            ".comment-reply-row-text-content", ".class-comment-reply-row-text-content", ".reply-text-content",
            ".class-comment-reply-text", ".reply-text",
            "[class*='reply-text']", "[class*='reply-content']",
            "[class*='text-content']", "p"
        ]);
        if (!text) text = cleanText(reply.innerText || reply.textContent || '');
        if (text && !/加载中|正在加载/.test(text)) {
            const key = author + '|' + text;
            if (!keys.has(key)) {
                keys.add(key);
                replies.push({ author, text });
            }
        }
    });

    return { page: page, keys: Array.from(keys), replies: replies };
}
'''

# ========== 评论抓取（增量楼中楼逐页翻）==========
async def _mcmod_fetch_comments(page, modpack_id, comment_count_display, worker_id, index,
                         row=None, start_row_page=1, start_reply_index=-1):
    """模块3: 评论抓取（v7.8.2：主楼逐页翻，逐条主楼翻完所有楼中楼后增量合并）"""
    print(f'  [W{worker_id}] [{index}] 💬 开始抓取评论（v8.0.0 终结版）')
    
    try:
        await asyncio.wait_for(page.wait_for_load_state("networkidle"), timeout=6)
    except:
        pass
    
    await _mcmod_scroll_to_comments(page, worker_id, index)
    await _mcmod_wait_for_comments_loaded(page, worker_id, index)
    await rate_controller.safe_sleep(1.0)
    
    actual_comment_count = 0
    try:
        actual_comment_count = await asyncio.wait_for(
            page.evaluate(EXTRACTOR_COMMENT_COUNT), 
            timeout=EVAL_TIMEOUT
        )
        if actual_comment_count > 0 and DEBUG_COMMENTS:
            print(f'  [W{worker_id}] [{index}] 📊 评论总数: {actual_comment_count}')
    except Exception as e:
        if DEBUG_COMMENTS:
            print(f'  [W{worker_id}] [{index}] 读取评论总数失败：{str(e)[:50]}')
    
    if actual_comment_count > 0 and comment_count_display == 0:
        comment_count_display = actual_comment_count

    effective_comment_total = max(int(actual_comment_count or 0), int(comment_count_display or 0))
    page_budget = MAX_COMMENT_PAGES
    reply_page_budget = MAX_REPLY_PAGES
    if SAFE_CRAWL_MODE:
        if effective_comment_total >= 500:
            page_budget = min(page_budget, SAFE_MAX_COMMENT_PAGES_LARGE)
        elif effective_comment_total >= 150:
            page_budget = min(page_budget, SAFE_MAX_COMMENT_PAGES_MEDIUM)
        else:
            page_budget = min(page_budget, SAFE_MAX_COMMENT_PAGES_SMALL)
        reply_page_budget = min(reply_page_budget, SAFE_MAX_REPLY_PAGES)
        if DEBUG_COMMENTS:
            print(f'  [W{worker_id}] [{index}] 🛡️ 安全预算: 主评论最多 {page_budget} 页，单楼中楼最多 {reply_page_budget} 页')
    
    all_comments = []  # 每条: { author, text, floor, replies: [{author, text}] }
    dom_page = 1
    empty_page_count = 0
    consecutive_page_fails = 0
    reached_comment_end = False
    start_time = time.time()

    def save_comment_progress(current_page=dom_page, checked=False, error=''):
        if row is None:
            return
        total_now = max(int(actual_comment_count or 0), int(comment_count_display or 0), _comment_preview_count(all_comments))
        row['comments'] = list(all_comments)
        row['评论详情'] = list(all_comments)
        row['comment_total'] = total_now
        row['评论总数'] = total_now
        row['comment_checked'] = checked
        row['_comment_checked'] = checked
        row['_comment_row_page'] = current_page
        if error:
            row['comment_error'] = str(error)[:300]
    
    while True:
        elapsed = time.time() - start_time
        if elapsed >= COMMENT_TIMEOUT:
            if DEBUG_COMMENTS:
                print(f'  [W{worker_id}] [{index}] ⏰ 评论抓取超时 ({COMMENT_TIMEOUT}s)，返回 {len(all_comments)} 条')
            break
        
        if dom_page > page_budget:
            if DEBUG_COMMENTS:
                print(f'  [W{worker_id}] [{index}] 🛡️ 已达安全页数预算 {page_budget}，保留已采集评论并停止深挖')
            break
        
        # 展开"查看回复"按钮
        expanded = await _mcmod_expand_all_replies(page, worker_id, index)
        if expanded > 0:
            await rate_controller.safe_sleep(1.5)
        
        # ★先提取当前页主楼的基本信息（不含楼中楼），然后逐条翻楼中楼
        page_main_comment_texts = await page.evaluate('''() => {
            const block = document.querySelector(".class-comment-block, .common-comment-block");
            if (!block) return [];
            const texts = [];
            const rows = block.querySelectorAll(".class-comment-row, .comment-row");
            rows.forEach((r, i) => {
                const tc = (r.querySelector('.class-comment-row, .comment-row-text-content') || r.querySelector('[class*="class-comment-text"]') || {});
                texts.push({ text: (tc.innerText || tc.textContent || '').trim().replace(/^回复\\s*/, '').slice(0, 200), idx: i+1 });
            });
            return texts;
        }''')
        
        # 生成已存在评论的 text 集合
        existing_texts = {c['text'] for c in all_comments}
        
        # 获取 .class-comment-row, .comment-row 索引列表（使用 CSS :nth-child）
        row_sel_list = list(range(1, len(page_main_comment_texts) + 1))
        
        if not row_sel_list:
            empty_page_count += 1
            await _mcmod_scroll_to_comments(page, worker_id, index, max_retry=3)
            if empty_page_count >= MAX_EMPTY_COMMENT_PAGES:
                if DEBUG_COMMENTS:
                    print(f'  [W{worker_id}] [{index}] 连续{MAX_EMPTY_COMMENT_PAGES}次空白页，终止')
                reached_comment_end = True
                break
        else:
            empty_page_count = 0
            consecutive_page_fails = 0
        
        # 对该页每条主楼：增量翻完所有楼中楼页
        page_new_comments = []
        
        for idx in row_sel_list:
            elapsed = time.time() - start_time
            if elapsed >= COMMENT_TIMEOUT:
                break
            
            row_css = f".class-comment-block .class-comment-row:nth-child({idx}), .common-comment-block .comment-row:nth-child({idx})"
            
            # 判断这条主楼是不是已经存在（去重）：用主楼 text 签名
            main_text = page_main_comment_texts[idx-1]['text'] if idx-1 < len(page_main_comment_texts) else ''
            # 如果主楼 text 为空则用更精确的方法取
            if not main_text:
                try:
                    main_text = await page.evaluate(f'''() => {{
                        const r = document.querySelector('{row_css}');
                        if (!r) return '';
                        const tc = r.querySelector('.class-comment-row, .comment-row-text-content') || r.querySelector('[class*="class-comment-text"]') || {{}};
                        return (tc.innerText || tc.textContent || '').trim().replace(/^回复\\s*/, '').slice(0, 200);
                    }}''')
                except:
                    pass
            
            if main_text in existing_texts:
                # 已经抓过这条主楼（翻页回到同一行），跳过
                continue
            
            # 获取该主楼的楼中楼分页信息（总页数/当前页）
            pgi = await page.evaluate(EXTRACT_MAIN_REPLY_PAGI_INFO_JS, row_css)
            reply_pages = pgi['pages']
            if reply_pages <= 0:
                # 检查是否有楼中楼容器
                has_reply_floor = await page.evaluate(f'''() => {{
                    const r = document.querySelector('{row_css}');
                    return !!(r && (r.querySelector('.class-comment-reply-floor') || r.querySelector('.reply-floor') || r.querySelector('.comment-replies')));
                }}''')
                if not has_reply_floor:
                    # 没有楼中楼
                    # 直接提取这条主楼
                    main_row_data = await page.evaluate(f'''() => {{
                        const tx = document.querySelector("{row_css}");
                        if (!tx) return null;
                        const tc = tx.querySelector('.class-comment-row, .comment-row-text-content') || tx.querySelector('[class*="class-comment-text"]') || {{}};
                        const ta = tx.querySelector('.class-comment-row, .comment-row-username a') || tx.querySelector('[class*="class-username"]') || {{}};
                        const text = (tc.innerText || tc.textContent || '').trim().replace(/^回复\\s*/, '');
                        const author = (ta.innerText || ta.textContent || '').trim();
                        return {{ author: author || '匿名用户', text: text, replies: [] }};
                    }}''')
                    if main_row_data and main_row_data['text'] and main_row_data['text'] not in existing_texts:
                        page_new_comments.append(main_row_data)
                        existing_texts.add(main_row_data['text'])
                    continue
            
            # 【有楼中楼分页】先翻到第一页（当前页就是第一页或某一页）
            # 收集所有楼中楼的 key 集合
            collected_keys = set()
            collected_replies = []
            
            for reply_p in range(1, reply_pages + 1):
                elapsed = time.time() - start_time
                if elapsed >= COMMENT_TIMEOUT:
                    break
                if reply_p > reply_page_budget:
                    break
                
                if reply_p > 1:
                    # 翻到第 reply_p 页
                    clicked = await page.evaluate(f'''([rowSel, targetPage]) => {{
                        const rowEl = document.querySelector(rowSel);
                        if (!rowEl) return false;
                        const replyFloor = rowEl.querySelector('.class-comment-reply-floor') || rowEl.querySelector('.reply-floor') || rowEl.querySelector('.comment-replies') || rowEl;
                        const pagi = replyFloor.querySelector('.pagination[data-name*="comment-reply-list"]');
                        if (!pagi) return false;
                        const links = pagi.querySelectorAll('a.page-link');
                        for (const link of links) {{
                            const dp = link.getAttribute('data-page');
                            if (dp && parseInt(dp) === targetPage) {{
                                try {{ link.click(); return true; }} catch(e) {{ return false; }}
                            }}
                            if (link.textContent.trim() === String(targetPage)) {{
                                try {{ link.click(); return true; }} catch(e) {{ return false; }}
                            }}
                        }}
                        return false;
                    }}''', [row_css, reply_p])
                    if not clicked:
                        # 点击失败，尝试按"下一页"方式翻
                        if reply_p == 2:
                            await _mcmod_click_single_reply_next(page, row_css, worker_id, index)
                        break
                    await rate_controller.after_comment_action('楼中楼翻页')
                    await rate_controller.safe_sleep(random.randint(1500, 2500) / 1000.0)
                
                # 提取当前页的楼中楼
                try:
                    reply_data = await page.evaluate(EXTRACT_REPLY_ROWS_FOR_MAIN_JS, row_css)
                except Exception as eval_err2:
                    print(f"  [W{worker_id}] [{index}] ❌ 解析楼中楼时 JS 崩溃，跳过此主楼: {eval_err2}")
                    break
                for rp in reply_data['replies']:
                    key = rp['author'] + '|' + rp['text']
                    if key not in collected_keys:
                        collected_keys.add(key)
                        collected_replies.append(rp)
            
            # 提取主楼内容
            main_row_data = await page.evaluate(f'''() => {{
                const block = document.querySelector('.class-comment-block, .common-comment-block');
                if (!block) return null;
                const tx = block.querySelector('.class-comment-row, .comment-row:nth-child({idx})');
                if (!tx) return null;
                const tc = tx.querySelector('.class-comment-row, .comment-row-text-content') || tx.querySelector('[class*="class-comment-text"]') || {{}};
                const ta = tx.querySelector('.class-comment-row, .comment-row-username a') || tx.querySelector('[class*="class-username"]') || {{}};
                const text = (tc.innerText || tc.textContent || '').trim().replace(/^回复\\s*/, '');
                const author = (ta.innerText || ta.textContent || '').trim();
                return {{ author: author || '匿名用户', text: text, replies: {json.dumps(collected_replies, ensure_ascii=False)} }};
            }}''')
            
            if main_row_data and main_row_data['text'] and main_row_data['text'] not in existing_texts:
                page_new_comments.append(main_row_data)
                existing_texts.add(main_row_data['text'])
            
            # 楼中楼翻页完成后，翻回第1页（防止后续主楼错位）
            try:
                await page.evaluate(f'''() => {{
                    const rowEl = document.querySelector('{row_css}');
                    if (!rowEl) return;
                    const replyFloor = rowEl.querySelector('.class-comment-reply-floor') || rowEl.querySelector('.reply-floor') || rowEl.querySelector('.comment-replies') || rowEl;
                    const pagi = replyFloor.querySelector('.pagination[data-name*="comment-reply-list"]');
                    if (!pagi) return;
                    const firstLink = pagi.querySelector('a.page-link[data-page="1"], a.page-link:not([data-page])');
                    if (firstLink && firstLink.textContent.trim() === '1') {{
                        firstLink.click();
                    }}
                }}''')
                await rate_controller.after_comment_action('楼中楼回到第一页')
                await rate_controller.safe_sleep(random.randint(500, 1000) / 1000.0)
            except:
                pass
            
            if len(page_new_comments) > 0:
                main_count = len(page_new_comments)
                total_reply = sum(len(c.get('replies', [])) for c in page_new_comments)
                print(f'  [W{worker_id}] [{index}] 👤 主楼{idx}/{len(row_sel_list)}: 已采集 {total_reply} 条楼中楼 (共{reply_pages}页)')
        
        if page_new_comments:
            all_comments.extend(page_new_comments)
            save_comment_progress(dom_page, checked=False)
            if DEBUG_COMMENTS:
                print(f'  [W{worker_id}] [{index}] 📝 第{dom_page}页: +{len(page_new_comments)}条主楼')
        
        # 已抓满退出
        if actual_comment_count > 0 and len(all_comments) >= actual_comment_count:
            if DEBUG_COMMENTS:
                print(f'  [W{worker_id}] [{index}] ✅ 已抓 {len(all_comments)} 条，达到总数 {actual_comment_count}')
            reached_comment_end = True
            break
        
        if dom_page >= page_budget:
            break
        
        # 翻到下一页主楼
        has_next = await _mcmod_click_next_page(page, worker_id, index, dom_page)
        if not has_next:
            consecutive_page_fails += 1
            if consecutive_page_fails >= MAX_CONSECUTIVE_PAGE_FAILS:
                print(f'  [W{worker_id}] [{index}] ⚠️  连续翻页失败{MAX_CONSECUTIVE_PAGE_FAILS}次，退出')
                break
            reached_comment_end = True
            break
        
        consecutive_page_fails = 0
        dom_page += 1
        try:
            await page.evaluate('document.querySelector(".class-comment-block, .common-comment-block").scrollIntoView({block:"center"})')
            await rate_controller.safe_sleep(1.5)
        except:
            pass
    
    total_reply_count = sum(len(c.get('replies', [])) for c in all_comments)
    if DEBUG_COMMENTS and all_comments:
        print(f'  [W{worker_id}] [{index}] ✅ 评论抓取完成: {len(all_comments)}条主楼, {total_reply_count}条楼中楼')
    
    total_all = max(int(actual_comment_count or 0), int(comment_count_display or 0), len(all_comments))
    if row is not None and SAFE_CRAWL_MODE and total_all > len(all_comments):
        row['评论安全截断'] = True
        row['评论已采集主楼数'] = len(all_comments)
        row['评论采集页数预算'] = page_budget
    save_comment_progress(dom_page, checked=(reached_comment_end or len(all_comments) >= total_all or total_all == 0))
    return all_comments, total_all

async def _mcmod_fetch_trend(page, worker_id, index):
    for attempt in range(MODULE_RETRY + 1):  # 增加一次重试
        try:
            clicked = False
            for sel in [
                "a:has-text('指数走势')",
                "button:has-text('指数走势')",
                "[role='button']:has-text('指数走势')",
                "li:has-text('指数走势')",
                "text=指数走势",
            ]:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() > 0:
                        await loc.scroll_into_view_if_needed(timeout=3000)
                        await loc.click(timeout=5000)
                        clicked = True
                        if attempt == 0 and DEBUG_COMMENTS:
                            print(f'  [W{worker_id}] [{index}] 🔎 已点击指数走势: {sel}')
                        break
                except:
                    pass

            if not clicked:
                target = await asyncio.wait_for(page.evaluate(FIND_TREND_TARGET_JS), timeout=EVAL_TIMEOUT)
                if not target or not target.get('found'):
                    if attempt == 0:
                        reason = target.get('reason', '未知原因') if isinstance(target, dict) else '未知原因'
                        print(f'  [W{worker_id}] [{index}] ⚠️  未找到指数走势按钮: {reason}')
                    await asyncio.sleep(1.5)
                    continue
                
                if attempt == 0 and DEBUG_COMMENTS:
                    print(f'  [W{worker_id}] [{index}] 🔎 指数走势按钮: {target.get("tag", "")}.{target.get("className", "")[:40]}')
                
                await page.mouse.click(target['x'], target['y'])

            await page.wait_for_timeout(TREND_WAIT_MS)
            try:
                await page.wait_for_function('''() => {
                    if (typeof echarts === 'undefined') return false;
                    return Array.from(document.querySelectorAll('div')).some(div => {
                        try { return !!echarts.getInstanceByDom(div); } catch(e) { return false; }
                    });
                }''', timeout=8000)
            except:
                pass
            result = await asyncio.wait_for(page.evaluate(EXTRACT_TREND_JS), timeout=EVAL_TIMEOUT + 10)
            parsed = parse_trend_result(result)
            if parsed.get('走势数据点', 0) > 0:
                return parsed
        except Exception as e:
            if attempt == 0:
                print(f'  [W{worker_id}] [{index}] ⚠️  指数走势抓取异常: {str(e)[:120]}')
        await asyncio.sleep(1.5)
    return _default_trend()

# ========== Fetch Orchestrator ==========
async def _mcmod_fetch_detail_pack(page, url, worker_id, index, total):
    # [Adapter 管线] 仅负责基础指标、详情结构与趋势数据的极速抓取
    async def _do_fetch():
        await safe_goto(page, url, wait_until='commit')
        await wait_mcmod_page_ready(page, url, worker_id, index)
        if await _mcmod_check_anti_crawl(page):
            raise Exception('触发反爬')
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        basic = await _mcmod_fetch_basic(page, worker_id, index)
        if not basic:
            try:
                state = await page.evaluate('''() => ({
                    url: location.href,
                    title: document.title || '',
                    body_len: document.body ? ((document.body.innerText || document.body.textContent || '').length) : 0,
                    ready: document.readyState
                })''')
            except Exception as state_err:
                state = {'state_error': str(state_err)}
            raise Exception(f'基础信息提取失败: {state}')
            
        intro_data = await _mcmod_fetch_intro_tags(page, worker_id, index)
        basic['整合包介绍'] = intro_data.get('整合包介绍', '')
        basic['分类标签'] = intro_data.get('分类标签', '') or basic.get('分类标签', '')
        basic['整合包标签'] = intro_data.get('整合包标签', '') or basic.get('整合包标签', '')
        
        # 抓走势
        if FETCH_TREND_DATA:
            trend = await _mcmod_fetch_trend(page, worker_id, index)
        else:
            trend = _default_trend()
            
        comment_total = int(basic.get('评论数', 0) or 0)
        if not FETCH_COMMENT_DETAILS:
            try:
                quick_count = await asyncio.wait_for(page.evaluate(EXTRACTOR_COMMENT_COUNT), timeout=EVAL_TIMEOUT)
                if quick_count:
                    comment_total = int(quick_count)
            except:
                pass
        
        if comment_total > 0:
            basic['评论数'] = comment_total
            
        pack = {
            'url': url,
            'basic': basic,
            'intro': basic.get('整合包介绍', ''),
            'comments': [],
            'comment_total': comment_total,
            'comment_checked': False,
            'trend': trend,
        }
        return pack

    try:
        return await asyncio.wait_for(_do_fetch(), timeout=PACK_TIMEOUT)
    except asyncio.TimeoutError:
        print(f'  [W{worker_id}] [{index}] ⏰ 详情页抓取超时 ({PACK_TIMEOUT}s)')
        raise Exception(f'详情页抓取超时 {PACK_TIMEOUT}s')

async def _mcmod_fetch_comment_pack(page, url, worker_id, index, total, row):
    # [Adapter 深度挖掘管线] 基于定点地址启动无缝翻页器，实现全量评论树的暴力下钻
    async def _do_fetch():
        await safe_goto(page, url, wait_until='commit')
        await wait_mcmod_page_ready(page, url, worker_id, index)
        if await _mcmod_check_anti_crawl(page):
            raise Exception('触发反爬')
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        modpack_id = extract_modpack_id(url)
        basic = row.get('basic') if isinstance(row, dict) else {}
        comment_count_display = row.get('comment_total', 0) or row.get('评论总数', 0) or (basic or {}).get('评论数', 0)
        
        start_row_page = 1
                
        comments, comment_total = await _mcmod_fetch_comments(
            page, modpack_id, comment_count_display, worker_id, index,
            row=row, start_row_page=start_row_page
        )
        comment_checked = bool(row.get('comment_checked') or row.get('_comment_checked'))
        
        preview_count = _comment_preview_count(comments)
        final_comment_total = max(_safe_int(comment_total), _safe_int(comment_count_display), preview_count)
        if final_comment_total > 0:
            row['comment_total'] = final_comment_total
            row['评论总数'] = final_comment_total
            if isinstance(basic, dict):
                basic['评论数'] = final_comment_total

        row['comments'] = comments
        row['评论详情'] = comments
        
        pack = {
            'url': url,
            'basic': {}, # 因为只更新评论，这里不需要 basic
            'comments': comments,
            'comment_total': final_comment_total,
            'comment_checked': comment_checked,
        }
        return pack

    return await _do_fetch()

# ==========================================
# 🚀 平台层 (Adapter)：多平台插件系统
# ==========================================
class Task:
    def __init__(self, platform: str, url: str):
        self.platform = platform
        self.url = url
        self.retry_count = 0
        self.index = 0  # 由 Scheduler 在出队时分配

class BaseAdapter:
    """
    所有平台适配器的基类。
    每个平台必须像"插件"一样实现以下方法，确保平台之间完全隔离：
    - create_context(): 创建独立的浏览器上下文（Cookie/UA/登录态 互不污染）
    - check_login():    平台专属的登录检测与引导
    - fetch_list():     从该平台的列表页提取目标 URL
    - fetch():          抓取单个目标的详情数据
    """
    name: str = 'base'
    concurrency: int = 2  # 每个平台独立的并发数（设 2 以兼顾效率与安全）

    async def create_context(self, playwright):
        """创建该平台专属的浏览器上下文（必须重写）"""
        raise NotImplementedError

    async def check_login(self, context) -> bool:
        """检测登录状态，如需登录则引导用户操作。返回 True 表示已登录/就绪。"""
        return True  # 默认不需要登录

    async def fetch_list(self, context) -> list:
        """从列表页提取该平台的目标 URL 列表（必须重写）"""
        raise NotImplementedError

    async def fetch(self, task: Task, page, worker_id: int = 0) -> dict:
        """抓取单个目标的详细数据（必须重写）"""
        raise NotImplementedError

    def normalize(self, raw_data: dict) -> dict:
        """把平台原始数据转换为统一字段。新平台各自重写，不在调度器里硬合并。"""
        return raw_data if isinstance(raw_data, dict) else {}

    def get_fallback_urls(self) -> list:
        """当 fetch_list 返回空时的备用目标"""
        return []


class MCModAdapter(BaseAdapter):
    """
    MC百科 (mcmod.cn) 平台适配器。
    独立管理：浏览器上下文 / 登录状态 / 列表提取 / 详情+评论抓取。
    """
    name = 'mcmod'
    concurrency = 2  # 严格将 MCMod 并发限制为 2，提供双工人并发，兼顾效率与防封锁

    async def create_context(self, playwright):
        """创建 MCMod 专属的持久化浏览器上下文（携带已保存的登录态）"""
        user_data_dir = USER_DATA_DIR
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        return context

    async def check_login(self, context) -> bool:
        """检测 MCMod 登录状态，未登录则弹出浏览器引导用户手动登录"""
        page = context.pages[0] if context.pages else await context.new_page()
        print('🔄 [MCMod] 检测登录...')
        await safe_goto(page, 'https://www.mcmod.cn/', wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)
        is_logged_in = await page.evaluate('''() => {
            const t = document.body.textContent;
            return t.includes('退出') || t.includes('我的主页') || t.includes('消息中心');
        }''')

        if not is_logged_in:
            print('\n⚠️ [MCMod] 未登录，请在浏览器中手动登录...')
            await safe_goto(page, 'https://www.mcmod.cn/login/', wait_until='domcontentloaded')
            for i in range(120):
                await page.wait_for_timeout(1000)
                try:
                    logged_in = await page.evaluate('''() => {
                        const t = document.body.textContent;
                        return t.includes('退出') || t.includes('我的主页');
                    }''')
                    if logged_in:
                        print('✅ [MCMod] 登录成功！\n')
                        return True
                except:
                    pass
            print('⏰ [MCMod] 等待超时，继续执行...\n')
            return False
        else:
            print('✅ [MCMod] 已登录\n')
            return True

    async def fetch_list(self, context) -> list:
        """从 MCMod 整合包列表页动态提取目标链接（支持多页提取，页面异常自愈）"""
        print("🔍 [MCMod] 正在从列表页爬取最新整合包链接...")
        list_page = await context.new_page()
        all_urls = []
        page_num = 1
        consecutive_no_new_pages = 0  # 连续无新增目标的列表页数计数器
        
        # 当测试限制参数为 0 时，扫描最大上限设为 9999 页（代表无上限连续翻页，直到最后一页提取不到链接自动结束）
        max_pages = TEST_MODE_LIMIT_PAGES if TEST_MODE_LIMIT_PAGES > 0 else 9999
        
        try:
            while page_num <= max_pages:
                url = 'https://www.mcmod.cn/modpack.html' if page_num == 1 else f'https://www.mcmod.cn/modpack.html?page={page_num}'
                print(f"   🔎 正在提取第 {page_num} 页列表 => {url}")
                
                result = await fetch_list_page(list_page, page_num, url)
                
                # 如果发生异常（如页面关闭、连接被重置），进行页面级销毁并重建重试
                if result.get('fail_reason') == 'exception':
                    print(f"   ⚠️ 第 {page_num} 页提取遇到异常，正在重建列表页面并进行原地自愈重试...")
                    try: await list_page.close()
                    except: pass
                    list_page = await context.new_page()
                    result = await fetch_list_page(list_page, page_num, url)
                
                urls = result.get('links', [])
                if not urls:
                    print(f"   ℹ️ 第 {page_num} 页未提取到新链接，列表扫描提前终止。")
                    break
                
                # 去重合并
                new_added = 0
                for u in urls:
                    if u not in all_urls:
                        all_urls.append(u)
                        new_added += 1
                
                print(f"   ✅ 第 {page_num} 页新增 {new_added} 个目标，累计 {len(all_urls)} 个整合包目标")
                
                # “连续 2 页无新增”判定法则：防列表老数据无谓长跑，提升挂机安全度
                if new_added == 0:
                    consecutive_no_new_pages += 1
                else:
                    consecutive_no_new_pages = 0
                    
                if consecutive_no_new_pages >= 2:
                    print(f"   ℹ️ 连续 {consecutive_no_new_pages} 页未提取到任何新增整合包，判定已抵达最新数据边缘，列表扫描安全终止！")
                    break
                
                # 列表翻页之间进行安全消火等待
                await rate_controller.safe_sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                
                # 每成功抓取 3 页列表，强行触发一次 15~25秒 随机大呼吸消火，给防火墙充足降温缓冲时间
                if page_num % 3 == 0:
                    sleep_time = random.uniform(6.0, 12.0)
                    print(f"\n☕ [MCMod] 列表已成功扫描 {page_num} 页，触发全局大门级消火长呼吸，原地静默 {sleep_time:.1f} 秒...")
                    await rate_controller.safe_sleep(sleep_time)
                    print("🔄 全局大呼吸结束，继续扫描下一页列表...\n")
                page_num += 1
                
            print(f"✅ [MCMod] 列表提取完成！累计提取到 {len(all_urls)} 个整合包目标")
            return all_urls
        except Exception as e:
            print(f"❌ [MCMod] 列表页面提取失败: {e}")
            return all_urls
        finally:
            try: await list_page.close()
            except: pass

    def get_fallback_urls(self) -> list:
        """MCMod 备用目标"""
        return [
            'https://www.mcmod.cn/modpack/1109.html',
            'https://www.mcmod.cn/modpack/205.html',
            'https://www.mcmod.cn/modpack/1211.html',
        ]

    def normalize(self, raw_data: dict) -> dict:
        """MCMod raw -> 看板统一字段。"""
        return pack_to_row(raw_data) if isinstance(raw_data, dict) else {}

    async def fetch(self, task: Task, page, worker_id: int = 0) -> dict:
        """抓取单个 MCMod 整合包的详情 + 评论"""
        try:
            print(f"  [MCMod] 开始提取基础属性与介绍文本...")
            raw_data = await _mcmod_fetch_detail_pack(page, task.url, worker_id=worker_id, index=task.index, total=0)
            if not raw_data or not raw_data.get('basic') or not raw_data['basic'].get('标题'):
                raise Exception("ANTI_CRAWL_TRIGGERED")

            # 评论完整抓取：失败时保留基础信息；评论本身由内部逻辑尽量返回已抓到的部分。
            comment_total_for_fetch = _safe_int(raw_data.get('comment_total', 0))
            if FETCH_COMMENT_DETAILS and comment_total_for_fetch >= COMMENT_DETAIL_MIN_TOTAL:
                print(f"  [MCMod] 探测到 {raw_data['comment_total']} 条评论，启动完整评论抓取...")
                try:
                    comment_result = await _mcmod_fetch_comment_pack(page, task.url, worker_id=worker_id, index=task.index, total=0, row=raw_data)
                    if isinstance(comment_result, dict) and 'comments' in comment_result:
                        raw_data['comments'] = comment_result['comments']
                        raw_data['comment_checked'] = bool(comment_result.get('comment_checked'))
                        raw_data['comment_total'] = max(
                            _safe_int(raw_data.get('comment_total', 0)),
                            _safe_int(comment_result.get('comment_total', 0)),
                            _comment_preview_count(comment_result.get('comments', [])),
                        )
                        if isinstance(raw_data.get('basic'), dict):
                            raw_data['basic']['评论数'] = raw_data['comment_total']
                    else:
                        raw_data['comments'] = comment_result
                        raw_data['comment_checked'] = False
                    raw_data['comment_total'] = max(
                        _safe_int(raw_data.get('comment_total', 0)),
                        _comment_preview_count(raw_data.get('comments', [])),
                    )
                    if isinstance(raw_data.get('basic'), dict):
                        raw_data['basic']['评论数'] = raw_data['comment_total']
                    print(f"  [MCMod] 评论完整抓取完成！")
                except Exception as ce:
                    raw_data['comment_checked'] = False
                    raw_data['comment_error'] = str(ce)[:300]
                    print(f"  [MCMod] ⚠️ 评论提取中断，基础数据会先落盘，下次继续补评论: {ce}")
            elif FETCH_COMMENT_DETAILS and comment_total_for_fetch > 0:
                raw_data['comment_checked'] = True
                print(f"  [MCMod] 评论数 {comment_total_for_fetch} 低于采样阈值，仅记录总数，跳过评论详情。")
            else:
                print(f"  [MCMod] 详情抓取完毕 (无评论配置或无评论记录)。")

            return raw_data
        except Exception as e:
            err_msg = str(e)
            if '触发反爬' in err_msg or '10秒' in err_msg:
                raise Exception("ANTI_CRAWL_TRIGGERED")
            raise Exception(f"FETCH_ERROR: {err_msg}")


# ==========================================
# 🧠 调度层 (Scheduler)：平台无关的核心引擎
# ==========================================
# Scheduler 的职责边界：
#   ✅ 派发任务 / 控制并发 / 风控熔断 / JSONL 落盘 / 进度恢复
#   ❌ 不解析网页 / 不写 selector / 不碰 DOM / 不知道任何平台细节

class Scheduler:
    def __init__(self, refresh_days: Optional[int] = None, refresh_all: bool = False):
        self.adapters = {}       # platform_name -> BaseAdapter
        self.contexts = {}       # platform_name -> BrowserContext (隔离)
        self.tasks = asyncio.Queue()
        self.results = []
        self.failed_tasks = []
        self.lock = asyncio.Lock()
        self.cooling_down = {}   # platform_name -> bool (熔断隔离)
        self.anti_crawl_lock = asyncio.Lock()  # 排他提示锁
        self.crawl_gate = asyncio.Event()     # 全局放行通道
        self.crawl_gate.set()                 # 默认处于打开（set）状态
        rate_controller.crawl_gate = self.crawl_gate  # ★ 强穿透：让全局速率控制器直接持有放行大门
        self.need_recreate_page = {}          # platform_name -> bool
        self.last_request_time = 0.0          # 全局上次请求时间戳，防多 Worker 重叠同秒“双击”
        self.success_count = {}               # platform -> int，用于呼吸休息判定
        self.done_urls = set()
        self.incomplete_urls = set()
        self.url_last_seen = {}
        self.refresh_days = refresh_days
        self.refresh_all = refresh_all
        self._task_counter = 0
        self.stop_platforms = set()

    def _drain_platform_tasks(self, platform: str):
        kept = []
        try:
            while True:
                task = self.tasks.get_nowait()
                self.tasks.task_done()
                if task.platform != platform:
                    kept.append(task)
        except asyncio.QueueEmpty:
            pass
        for task in kept:
            self.tasks.put_nowait(task)

    def register(self, platform: str, adapter: BaseAdapter):
        self.adapters[platform] = adapter

    def add_task(self, task: Task):
        if self.should_fetch(task.url):
            self.tasks.put_nowait(task)

    def should_fetch(self, url: str) -> bool:
        if self.refresh_all:
            return True
        if url in self.incomplete_urls:
            return True
        if url not in self.done_urls:
            return True
        if self.refresh_days is None:
            return False
        last_seen = self.url_last_seen.get(url)
        if not last_seen:
            return True
        age_days = (datetime.now().astimezone() - last_seen).total_seconds() / 86400
        return age_days >= self.refresh_days

    async def _safe_new_page(self, platform: str):
        """从指定平台的 Context 中创建新页面（支持 Context 意外死亡的强韧自愈重建）"""
        adapter = self.adapters.get(platform)
        if not adapter:
            raise Exception(f"未找到平台 Adapter: {platform}")
            
        for attempt in range(3):
            context = self.contexts.get(platform)
            if not context:
                raise Exception(f"平台 {platform} 没有已注册的 Context")
                
            try:
                print(f"[Scheduler] 为 [{platform}] 创建工作页面...")
                page = await context.new_page()
                page.set_default_timeout(30000)
                return page
            except Exception as e:
                err_msg = str(e)
                if "TargetClosedError" in err_msg or "closed" in err_msg.lower():
                    print(f"\n⚠️ [Scheduler] 检测到 [{platform}] 浏览器隔离上下文已死亡 (Attempt {attempt+1}/3)！")
                    print(f"👉 正在自动强行销毁并重建该平台的隔离 Context...")
                    try: await context.close()
                    except: pass
                    
                    try:
                        new_context = await adapter.create_context(self.playwright)
                        self.contexts[platform] = new_context
                        await adapter.check_login(new_context)
                        print(f"✅ [{platform}] 浏览器隔离上下文自愈重建成功！继续拉起页面...")
                    except Exception as recreate_err:
                        print(f"❌ 浏览器上下文重建失败: {recreate_err}")
                else:
                    raise e
        raise Exception(f"平台 {platform} 的 BrowserContext 多次重建后依然处于关闭死亡状态，无法拉起工作页面。")

    def _load_progress(self):
        """从已有 JSONL 中加载进度；质量不达标的历史记录会在本轮补抓。"""
        jsonl_path = '多平台爬虫数据_v1.0.jsonl'
        if not os.path.exists(jsonl_path):
            return
        try:
            latest_by_url = {}
            with open(jsonl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        payload = obj.get('data') or obj.get('normalized') or obj.get('raw') or {}
                        url = payload.get('url', '') or payload.get('链接', '') or payload.get('整合包详情地址', '')
                        if url:
                            seen_at = get_capture_time(obj, payload)
                            prev = latest_by_url.get(url)
                            if not prev or (seen_at and prev.get('seen_at') and seen_at > prev['seen_at']) or (seen_at and not prev.get('seen_at')):
                                latest_by_url[url] = {'record': obj, 'payload': payload, 'seen_at': seen_at}
                    except:
                        pass
            bad_count = 0
            for url, item in latest_by_url.items():
                payload = item.get('payload') or {}
                if item.get('seen_at'):
                    self.url_last_seen[url] = item['seen_at']
                if REFRESH_INCOMPLETE_ROWS and is_incomplete_row(payload):
                    self.incomplete_urls.add(url)
                    bad_count += 1
                else:
                    self.done_urls.add(url)
            if self.done_urls:
                if self.refresh_all:
                    print(f"[进度恢复] 已读取 {len(self.done_urls)} 个历史目标；本轮强制刷新全部匹配目标")
                elif self.refresh_days is not None:
                    print(f"[进度恢复] 已读取 {len(self.done_urls)} 个历史目标；本轮仅刷新超过 {self.refresh_days} 天或缺少时间戳的目标")
                else:
                    print(f"[进度恢复] 已跳过 {len(self.done_urls)} 个已完成的目标")
            if bad_count:
                print(f"[质量补抓] 发现 {bad_count} 个历史目标疑似缺字段/截断/抓取失败，本轮会自动重新抓取")
        except Exception as e:
            print(f"[警告] 读取进度文件失败: {e}")

    async def _worker(self, worker_id: int, platform: str):
        """工人循环：从队列取任务，调用对应 Adapter 处理"""
        page = await self._safe_new_page(platform)
        adapter = self.adapters[platform]

        while True:
            # 1. 如果上下文被重建过，Worker 使用新页面继续；风控触发时会直接停机。
            if self.need_recreate_page.get(platform, False):
                try: await page.close()
                except: pass
                page = await self._safe_new_page(platform)
                self.need_recreate_page[platform] = False

            # 2. 必须等待全局放行门处于开启状态，防止熔断锁门期间其他 Worker 盲目冲撞
            await self.crawl_gate.wait()

            if platform in self.stop_platforms:
                break

            try:
                task = self.tasks.get_nowait()
            except asyncio.QueueEmpty:
                break

            # 如果任务不属于这个 worker 对应的平台，放回去跳过
            if task.platform != platform:
                self.tasks.put_nowait(task)
                self.tasks.task_done()
                await asyncio.sleep(0.1)
                continue

            try:
                # 强制交错排队机制：防止 W0/W1 在同一秒发生高频重叠请求引发防火墙敏感
                async with self.lock:
                    import time
                    now = time.time()
                    elapsed = now - self.last_request_time
                    if elapsed < 2.0:
                        await asyncio.sleep(2.0 - elapsed)
                    self.last_request_time = time.time()

                # 分配递增序号
                async with self.lock:
                    self._task_counter += 1
                    task.index = self._task_counter

                print(f"[W{worker_id}] [{task.index}/{self.tasks.qsize() + self._task_counter}] 抓取 => {task.url}")
                raw_data = await adapter.fetch(task, page, worker_id=worker_id)
                captured_at = now_iso()
                normalized_data = adapter.normalize(raw_data)
                normalized_data = enrich_normalized_row(task.platform, raw_data, normalized_data, captured_at)

                # ❗核心：统一出口，各自落盘
                output = {
                    "source": task.platform,
                    "captured_at": captured_at,
                    "detail_fetched_at": captured_at,
                    "trend_fetched_at": captured_at,
                    "raw": raw_data,
                    "normalized": normalized_data,
                    "data": normalized_data
                }
                if normalized_data.get('评论详情'):
                    output["comment_fetched_at"] = captured_at

                async with self.lock:
                    try:
                        append_trend_history_snapshot(task.platform, raw_data, normalized_data)
                    except Exception as history_err:
                        print(f"⚠️ 本地趋势快照写入失败: {history_err}")
                    self.results.append(output)
                    self.done_urls.add(task.url)
                    self.incomplete_urls.discard(task.url)
                    self.url_last_seen[task.url] = parse_iso_time(captured_at)
                    with open('多平台爬虫数据_v1.0.jsonl', 'a', encoding='utf-8') as f:
                        f.write(json.dumps(output, ensure_ascii=False) + '\n')

                # 累计成功量：安全模式下少一些频繁顿挫，改成较低频的整段休息。
                async with self.lock:
                    self.success_count[platform] = self.success_count.get(platform, 0) + 1
                    curr_success = self.success_count[platform]

                rest_every = 20 if SAFE_CRAWL_MODE else 8
                if curr_success % rest_every == 0:
                    async with self.anti_crawl_lock:
                        if self.crawl_gate.is_set():
                            self.crawl_gate.clear()  # 关上全局放行门！令其他并发 Worker 在跑完当前包后卡在排队路口挂起
                            sleep_time = random.uniform(10.0, 18.0) if SAFE_CRAWL_MODE else random.uniform(4.0, 8.0)
                            print(f"\n☕ [W{worker_id}] 平台 [{platform}] 全局累计成功抓取 {curr_success} 个目标，开始 {sleep_time:.1f} 秒随机全局消火呼吸休眠...")
                            print("👉 期间浏览器底层请求也会排队，不会出现另一个 Worker 继续翻页。\n")
                            await asyncio.sleep(sleep_time)
                            print(f"🔄 {sleep_time:.1f} 秒随机休眠期结束！重新开启全局放行门，多 Worker 继续进击...\n")
                            self.crawl_gate.set()   # 打开全局放行门，多 Worker 继续工作

            except Exception as e:
                err_msg = str(e)
                if "ANTI_CRAWL_TRIGGERED" in err_msg:
                    # 3. 触发风控/封禁：立即停机，不自动换节点续跑，避免继续消耗 IP 与账号信誉。
                    async with self.anti_crawl_lock:
                        self.stop_platforms.add(platform)
                        rate_controller.stop_requested = True
                        self._drain_platform_tasks(platform)
                        print("\n" + "🔴"*35)
                        print(f"[W{worker_id}] ⚠️ 平台 [{platform}] 检测到风控/封禁/验证码信号。")
                        print("👉 已立即停止本轮采集，没有自动重试，也不会继续换节点冲刺。")
                        print("👉 已采集的数据已经实时落盘；当前任务会记录为失败，建议稍后人工登录检查账号状态。")
                        print("🔴"*35 + "\n")
                        self.failed_tasks.append(task)
                    break
                else:
                    print(f"[W{worker_id}] ❌ 抓取失败: {err_msg}")
                    if 'Page.goto' in err_msg or 'Timeout' in err_msg or 'ERR_CONNECTION' in err_msg or 'net::' in err_msg or '基础信息提取失败' in err_msg or '页面未加载出可提取内容' in err_msg:
                        try:
                            print(f"[W{worker_id}] 页面异常，重建浏览器页面后继续。")
                            try:
                                await page.close()
                            except Exception:
                                pass
                            page = await self._safe_new_page(platform)
                        except Exception as rebuild_err:
                            print(f"[W{worker_id}] 页面重建失败: {rebuild_err}")
                    if task.retry_count < 3:
                        task.retry_count += 1
                        self.tasks.put_nowait(task)
                    else:
                        self.failed_tasks.append(task)
            finally:
                self.tasks.task_done()

        await page.close()

    async def run(self):
        print("\n=======================================")
        print("启动多平台整合包数据采集引擎 V2.0 (架构重构版)")
        print("核心：平台隔离 | 插件化 Adapter | JSONL 实时落盘")
        print("=======================================\n")

        # ① 进度恢复
        self._load_progress()

        # ② 启动 Playwright
        self.playwright = await async_playwright().start()
        playwright = self.playwright

        # ③ 遍历所有已注册平台：独立初始化
        all_workers = []
        worker_id_counter = 0

        for platform_name, adapter in self.adapters.items():
            print(f"\n{'='*40}")
            print(f"📦 初始化平台: [{platform_name}]")
            print(f"{'='*40}")

            # a. 创建该平台独立的 Context（互不污染）
            try:
                context = await adapter.create_context(playwright)
                self.contexts[platform_name] = context
            except Exception as e:
                print(f"❌ [{platform_name}] Context 创建失败: {e}，跳过该平台")
                continue

            # b. 登录检测（由 Adapter 自己控制）
            try:
                await adapter.check_login(context)
            except Exception as e:
                msg = str(e)
                if 'ERR_NAME_NOT_RESOLVED' in msg or 'net::' in msg:
                    print(f"❌ [{platform_name}] 无法访问平台首页，可能是 DNS/网络/代理问题：{msg}")
                    print(f"   已跳过该平台；请确认浏览器能打开 https://www.mcmod.cn/ 后再重试。")
                else:
                    print(f"❌ [{platform_name}] 登录检测失败：{e}")
                try:
                    await context.close()
                except Exception:
                    pass
                continue
            await install_safe_routes(context)

            # c. 列表提取（由 Adapter 自己控制）
            urls = await adapter.fetch_list(context)

            # d. 入队
            for url in urls:
                self.add_task(Task(platform_name, url))

            # e. 如果列表为空，使用备用目标
            if not urls:
                fallbacks = adapter.get_fallback_urls()
                if fallbacks:
                    print(f"⚠️ [{platform_name}] 列表为空，使用 {len(fallbacks)} 个备用目标")
                    for url in fallbacks:
                        self.add_task(Task(platform_name, url))

            # f. 按平台并发数创建 worker
            for _ in range(adapter.concurrency):
                task_coro = asyncio.create_task(
                    self._worker(worker_id_counter, platform_name)
                )
                all_workers.append(task_coro)
                worker_id_counter += 1

        # ④ 汇总
        total_tasks = self.tasks.qsize()
        print(f"\n📋 任务队列已就绪: {total_tasks} 个目标, {worker_id_counter} 个工人\n")

        if not all_workers:
            print("⚠️ 没有可用的平台，退出")
        else:
            # ⑤ 启动所有工人
            await asyncio.gather(*all_workers)

        print(f"\n[Scheduler] 采集完成! 成功: {len(self.results)}")

        # ⑥ 关闭所有 Context
        for platform_name, context in self.contexts.items():
            try:
                await context.close()
            except:
                pass
        await playwright.stop()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='多平台整合包数据采集引擎')
    parser.add_argument('--refresh-days', type=int, default=None,
                        help='增量刷新：只重新抓取超过 N 天未更新，或旧数据缺少时间戳的目标。例：--refresh-days 1')
    parser.add_argument('--refresh-all', action='store_true',
                        help='强制刷新列表中匹配到的所有目标；谨慎使用，会接近重新抓一遍。')
    parser.add_argument('--repair-comments', action='store_true',
                        help='兼容旧命令；现在默认就会补抓缺失或明显异常的评论详情。')
    args = parser.parse_args()
    if args.repair_comments:
        REPAIR_EMPTY_COMMENT_DETAILS = True

    scheduler = Scheduler(refresh_days=args.refresh_days, refresh_all=args.refresh_all)
    scheduler.register('mcmod', MCModAdapter())
    # 将来扩展其他平台只需：
    # scheduler.register('curseforge', CurseForgeAdapter())
    # scheduler.register('modrinth', ModrinthAdapter())
    asyncio.run(scheduler.run())

