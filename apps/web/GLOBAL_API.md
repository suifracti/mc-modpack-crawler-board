# Global API Inventory (Architecture V2 — Phase 3A)

## 1. 概述 (Overview)
为了将大型单体脚本 `web/assets/js/dashboard.js` (7,244 行) 逐步重构成清晰的现代 ES Module / TypeScript 模块，本清单盘点并分类了所有暴露到全局 `window` 的变量、HTML 行内属性调用的事件处理器、以及页面引导的副作用。

---

## 2. API 分类清单 (Inventory Categorization)

### A. EVENT_HANDLER（HTML 行内与模板动态生成的事件处理器）
在 HTML 标签中直接通过 `onclick="..."` 等行内属性调用的顶层函数，在 ES Module 构建中必须通过命名空间或有限全局桥接（`window.xxx`）保留兼容性：

| 函数名称 | 调用位置 | 职责说明 |
| :--- | :--- | :--- |
| `switchPlatformTab(tabId)` | 顶栏导航按钮、面包屑导航 | 切换当前展示平台（all / mcmod / bilibili / bbsmc / xyebbs / modrinth / curseforge） |
| `jumpToMcmodSearch(query)` | 跨平台搜索项、总览卡片 | 切换到 MC百科 并填充搜索词进行精确过滤 |
| `jumpToBiliSearch(query)` | 跨平台搜索项、总览卡片 | 切换到 哔哩哔哩 并填充搜索词 |
| `jumpToBbsmcSearch(query)` | 跨平台搜索项、总览卡片 | 切换到 BBSMC 并填充搜索词 |
| `jumpToXyebbsSearch(query)` | 跨平台搜索项、总览卡片 | 切换到 XYEBBS 并填充搜索词 |
| `jumpToModrinthSearch(query)` | 跨平台搜索项、总览卡片 | 切换到 Modrinth 并填充搜索词 |
| `jumpToCurseforgeSearch(query)` | 跨平台搜索项、总览卡片 | 切换到 CurseForge 并填充搜索词 |
| `jumpToPlatformWithCurrentSearch(platId)` | 总览面板各栏脚部「查看全部」链接 | 带当前统一搜索词跳转至对应平台看板 |
| `openVersionModal(...)` | 各平台卡片中的版本详情按钮 | 打开多版本下载与历史发布明细弹窗 |

---

### B. PUBLIC_GLOBAL（被外部测试、侧车数据或组件直接引用的全局对象）
测试套件（如 `pipeline/smoke_test_single.js`）及动态加载脚本所需读取的变量：

| 变量名称 | 宿主类型 | 职责说明 |
| :--- | :--- | :--- |
| `window.table` | DataTables API | MC百科主数据表格的 DataTables 实例 |
| `window.tableRowsData` | Array | MC百科所有行数据的纯 JSON 数组 (1,484 条) |
| `window.compareData` | Object | MC百科各整合包历史改动与版本对比数据 |
| `window.descData` | Object | MC百科整合包图文介绍纯文本与结构化数据 |
| `window.biliModpacksData` | Array | 哔哩哔哩平台整合包数据 (936 条) |
| `window.bbsmcModpacksData` | Array | BBSMC 平台整合包数据 (1,802 条) |
| `window.xyebbsModpacksData` | Array | XYEBBS 平台整合包数据 (5,175 条) |
| `window.modrinthModpacksData` | Array | Modrinth 平台整合包数据 (18,328 条) |
| `window.curseforgeModpacksData` | Array | CurseForge 平台整合包数据 (45,797 条) |
| `window.escHtml(str, noFormat)` | Function | 全局 HTML 转义纯函数 |
| `window.escAttrJs(str)` | Function | 全局属性值转义纯函数 |
| `window.toggleMultiSelect(selector, val)` | Function | 多选下拉框值切换与 Select2 同步更新辅助函数 |
| `window.PlatformLoader` | Object | 平台元数据与加载状态对象（Phase 3A 由 Repository 封装） |
| `window.MC_COVER_FALLBACK` 等 | String | 6 大平台的 SVG 缺省封面 Data URL |
| `window.__registerModDetailData` | Function | 模组侧车动态注入注册函数 (`data/mods/{id}.js`) |
| `window.__registerCommentData` | Function | 评论侧车动态注入注册函数 (`data/comments/{id}.js`) |

---

### C. SIDE_EFFECT_BOOTSTRAP（页面启动期副作用与依赖顺序）
| 时机 | 执行内容 | 依赖与说明 |
| :--- | :--- | :--- |
| `<head>` 防闪烁 (Anti-FOUC) | `localStorage.getItem('mcmod-theme-v2')` 读取并注入 `document.documentElement[data-theme]` | 必须尽早执行，无 DOM 依赖 |
| 初始静态资源加载 | jQuery, Bootstrap, Select2, DataTables, `table_rows.js`, `app_data.js`, `desc_data.js` | 传统同步 script 标签加载 |
| `$(document).ready` | 初始化 DataTables、Select2、绑定全局事件、启动空闲预加载 `startIdlePrefetch()` | 依赖完整 DOM 与 jQuery 插件 |

---

### D. INTERNAL_ONLY（内部纯函数与 UI 渲染函数，拟逐步模块化迁移）
- **本轮 Phase 3A 迁出**:
  - `escHtml`, `escAttrJs` -> `src/utils/html.ts`
  - `fmtBigNum`, `numFmt`, `formatVFileSize`, `asArray` -> `src/utils/format.ts`
  - `extractVersion` -> `src/domain/minecraft.ts`
  - `cleanPackKey` -> `src/domain/packName.ts`
  - 主题双向同步与切换逻辑 -> `src/state/theme.ts`
  - 侧车动态注入与状态跟踪 -> `src/data/LegacySidecarLoader.ts` & `src/data/LegacySidecarRepository.ts`
- **后续 Phase 3B/3C 规划迁出**:
  - `renderBiliView`, `renderGroupedCard`, `renderFlatCard`
  - `renderBbsmcView`, `renderXyebbsView`, `renderModrinthView`, `renderCurseforgeView`
  - `openVersionModal`, `openImageLightbox`, `showCommentPopup`
  - `initMcmodTable`, DataTables 列渲染器
