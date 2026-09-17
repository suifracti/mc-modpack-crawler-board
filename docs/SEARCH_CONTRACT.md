# Architecture V2 — MCMod Search Contract Specification
## Unified Search Semantics, Description Contract, and Single Source of Truth

> **Document Version**: 1.0 (Phase 3G-C.2 Baseline)  
> **Status**: APPROVED & VERIFIED  
> **Scope**: MCMod Unified Table Search (`#mcmodUnifiedSearch`), TypeScript `SearchEngine`, and DataTables Integration.

---

## 1. 架构目标与核心原则 (Core Architecture Principles)

在 Phase 3G-C 与 Phase 3G-C.1 审计中，我们识别了两个关键的搜索契约缺口：
1. **Description Promise 矛盾**：历史文档与个别文案曾宣称可搜索“简介/长篇描述”，但实际上客户端为了性能与体积考虑（避免引入数兆未压缩的长文本），主数据包 `mcmod_data.js` 中未包含长篇正文简介。
2. **多词分词与双重过滤分脑 (Double-Filter Split-Brain)**：现代 TypeScript `SearchEngine` 使用规范的空格分词与逻辑（`terms AND`，如 `"Fabric API"` 匹配 664 款整合包），而 DataTables 原生配置了 `smart: false`，执行连续字串完全匹配（将 `"Fabric API"` 作为整段短语匹配，仅命中 111 款），且两者串联叠加过滤，导致用户最终看到的记录与底层搜索引擎不一致。

针对上述问题，Phase 3G-C.2 确立并执行了以下核心契约：
- **原则一：单一真实源 (Single Source of Truth)**。`SearchEngine` 是全站搜索匹配判断的唯一仲裁者。DataTables 退化为纯渲染器与分页器，绝不在底层匹配集合之上施加二次文本过滤。
- **原则二：空格分词与逻辑 (Whitespace Tokens AND)**。统一以空白字符分割搜索关键词，要求所有词元（tokens）必须在被搜索整合包的检索字段中同时出现。
- **原则三：诚实的搜索范围声明 (Option B Description Contract)**。主表格搜索范围明确不包含长篇描述，UI 占位符与帮助文档诚实表达检索能力，长篇描述仅用于弹窗与抽屉展示。

---

## 2. 字段检索范围矩阵 (Searchable Fields Matrix)

下表定义了生产环境客户端运行时与后端数据库的字段检索范围：

| 字段名称 | 生产运行时检索 (`mcmod_data.js`) | 原始数据库字段 (`canonical.db`) | 说明 |
| :--- | :---: | :---: | :--- |
| **标题 / 中文名** | ✅ 是 (`title`) | `source_items.title` | 包含整合包主标题与中文名称 |
| **英文名** | ✅ 是 (`englishName`) | `source_items.title` / `extra_json` | 包含整合包官方英文名称 |
| **曾用名 / 别名** | ✅ 是 (`formerTitles`) | `source_items.extra_json` | 历史曾用名别名数组 |
| **整合包类型** | ✅ 是 (`typeName`) | `source_items.extra_json.type_name` | 如“魔改整合”、“原生整合”等 |
| **作者** | ✅ 是 (`author`) | `source_items.author` | 整合包发布作者 |
| **分类与标签** | ✅ 是 (`categories`) | `source_items.categories` | 包含分类与玩法标签 |
| **包含模组文本** | ✅ 是 (`modSearchText`) | `included_mods` 表全量聚合 | 包含所有已提取模组的中文名、英文名、分类标识 |
| **长篇正文简介** | ❌ 否 (Option B) | `source_items.description` | **不参与主表格索引**，避免客户端体积膨胀 10MB+；由详情弹窗按需加载 |
| **评论讨论区** | ❌ 否 | `comments` 表 | 不参与主表格索引 |

---

## 3. 简介搜索契约 (Option B Description Contract)

### 3.1 历史事实确证
经 Headless Edge CDP 对历史版本 `build/frontend_legacy_current_data/` 的实机验证：
- Legacy 前端表格数据源 `table_rows.js` 仅包含 `c0` 至 `c6` 列，主表格检索从来没有索引长篇简介正文。
- 仅包含在简介中的关键词（如 MID `255`, `413`, `1231` 正文中含有 `"RLCraft"` 但标题与模组均无）在 Legacy 前端搜索均为 `false`（不命中）。
- `desc_data.js` 仅作为按需弹窗展示的静态旁路，从未进入主表格过滤。

### 3.2 契约决策 (Option B)
因此，系统正式采用 **Option B** 规范：
1. **主表格搜索不包含长篇简介**：保持客户端 payload 轻量（`mcmod_data.js` 紧凑传输）。
2. **UI 占位符诚实对齐**：统一占位符文案为：
   ```html
   placeholder="输入名称、模组名、作者或玩法标签实时穿透速搜..."
   ```
   严禁宣称可以搜索“简介/长篇描述”，消除虚假承诺。
3. **功能真值矩阵登记**：在 `docs/FEATURE_TRUTH_MATRIX.md` 登记 `SEARCH-MCMOD-DESC-01` 为 **`VERIFIED`**。

---

## 4. 多词查询规范与单真实源驱动 (Multi-word Query & Single Source of Truth)

### 4.1 规范分词语义 (Canonical Tokenization Semantics)
在 `legacy_compat` 模式下，查询解析器 `queryParser.ts` 遵循以下规则：
```typescript
const terms = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
```
对于文档 `doc`，匹配判定规则为：
```typescript
const isMatched = terms.every(term => 
  doc.title.includes(term) ||
  doc.formerTitles.some(ft => ft.includes(term)) ||
  doc.typeName.includes(term) ||
  doc.author.includes(term) ||
  doc.categories.some(c => c.includes(term)) ||
  doc.modSearchText.includes(term)
);
```

### 4.2 终结 DataTables 双重过滤 (Dismantling DT Double Filter)
为了彻底根除 DataTables 的连续短语过滤问题：
1. **统一路由挂钩**：对 `window.table.search` 进行安全拦截：
   - 读状态时，返回 `searchCoordinator.getQuery('mcmod')`。
   - 写状态时，将输入值无损同步至 `searchCoordinator.setQuery(input, 'mcmod')`，并向 DataTables 原生搜索器传递空字符串 `""`。
2. **单一来源谓词驱动**：DataTables 自定义过滤器 `$.fn.dataTable.ext.search` 仅调用：
   ```javascript
   window.searchCoordinator.isMatched(rowData.mid, 'mcmod');
   ```
   内部维护以 MID 为键的哈希 Set 缓存（$O(1)$ 查找），DataTables 的行过滤完全听从 `SearchEngine` 的决策。
3. **一致性保证**：
   $$\text{TS SearchEngine Matched IDs} \equiv \text{DataTables Visible Rows} \equiv \text{Cards Rendered Rows}$$
   差异数为恒为 **0**。

---

## 5. 核心查询金集对比基准 (Golden Parity Benchmark)

下表记录了在 1,484 条真实 MCMod 整合包上，执行 Phase 3G-C.2 桥接前后及 TS 引擎与 DataTables 的匹配数比对：

| 查询词 (Query) | 类别 | 历史 DataTables (连续短语) | 规范 TS SearchEngine (分词 AND) | 当前修复后 DataTables | 最终可见数是否一致 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `RLCraft` | Pack Identity | 93 | 93 | 93 | ✅ 100% 一致 |
| `GreedyCraft` | Pack Identity | 2 | 2 | 2 | ✅ 100% 一致 |
| `Age of Fate` | Pack Identity | 1 | 2 | 2 | ✅ 100% 一致 |
| `Enigmatica` | Pack Identity | 31 | 31 | 31 | ✅ 100% 一致 |
| `DawnCraft` | Pack Identity | 2 | 2 | 2 | ✅ 100% 一致 |
| `Create` | Core-theme Mod | 477 | 477 | 477 | ✅ 100% 一致 |
| `Cobblemon` | Core-theme Mod | 8 | 8 | 8 | ✅ 100% 一致 |
| `GregTech` | Core-theme Mod | 70 | 70 | 70 | ✅ 100% 一致 |
| `Mekanism` | Core-theme Mod | 300 | 300 | 300 | ✅ 100% 一致 |
| `Botania` | Core-theme Mod | 286 | 286 | 286 | ✅ 100% 一致 |
| `JEI` | Utility / Library | 740 | 740 | 740 | ✅ 100% 一致 |
| `Architectury` | Utility / Library | 634 | 634 | 634 | ✅ 100% 一致 |
| `Cloth Config` | Utility / Library | 591 | 595 | 595 | ✅ 100% 一致 |
| `Fabric API` | Utility / Library | 111 (短语被截断) | 664 (分词 AND) | 664 | ✅ 100% 一致 |
| `Mouse Tweaks` | Utility / Library | 733 | 736 | 736 | ✅ 100% 一致 |
| `Twilight Forest` | Ambiguous Mod | 279 | 279 | 279 | ✅ 100% 一致 |
| `Applied Energistics` | Ambiguous Mod | 353 | 354 | 354 | ✅ 100% 一致 |
| `Ice and Fire` | Ambiguous Mod | 125 | 260 (分词 AND) | 260 | ✅ 100% 一致 |
| `Thermal` | Ambiguous Mod | 295 | 295 | 295 | ✅ 100% 一致 |
| `Avaritia` | Ambiguous Mod | 149 | 149 | 149 | ✅ 100% 一致 |

> **关键证明**：
> - `"Fabric API"`：历史 DataTables 仅展示 111 款，现已完全恢复为规范的 664 款。
> - `"Ice and Fire"`：历史 DataTables 仅展示 125 款，现已完全恢复为规范的 260 款。
> - 20 项金集查询在真实浏览器环境中达成 **20/20 完全一致**（`Equal?: true`）。
