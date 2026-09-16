$(document).ready(function() {

    /* 全局通用安全 HTML 转义与多选辅助函数（提前声明，保证所有组件和生命周期全局可用） */
    function escHtml(str, noFormat) {
        if (str === null || str === undefined) return "";
        var d = document.createElement('div');
        d.textContent = str;
        var raw = d.innerHTML;
        var LF = String.fromCharCode(10);
        var CR = String.fromCharCode(13);
        var text = raw.split(CR + LF).join(LF).split(CR).join(LF);
        if (noFormat) {
            return text.split(LF).join('<br>');
        }
        return text;
    }
    window.escHtml = escHtml;

    function escAttrJs(str) {
        return escHtml(str || '', true).replace(/<br>/g, '&#10;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
    window.escAttrJs = escAttrJs;

    function toggleMultiSelect(selector, val) {
        var $sel = $(selector);
        var current = $sel.val() || [];
        if (!Array.isArray(current)) current = current ? [current] : [];
        var idx = current.indexOf(val);
        if (idx >= 0) {
            current.splice(idx, 1);
            $sel.find('option').filter(function() { return $(this).val() === val; }).remove();
        } else {
            if ($sel.find('option').filter(function() { return $(this).val() === val; }).length === 0) {
                $sel.append($('<option>', { value: val, text: val, selected: true }));
            }
            current.push(val);
        }
        $sel.val(current).trigger('change');
    }
    window.toggleMultiSelect = toggleMultiSelect;

    


    /* ═════════════════ 非阻塞流式平台数据加载引擎 V3.0 ═════════════════ */
    var PLATFORMS = {
        'mcmod': { id: 'mcmod', name: 'MC百科', src: 'data/table_rows.js', globalVar: 'tableRowsData', count: 1484, loaded: false, loading: false, callbacks: [] },
        'bilibili': { id: 'bilibili', name: 'B站自制', src: 'data/bili_data.js', globalVar: 'biliModpacksData', count: 606, loaded: false, loading: false, callbacks: [] },
        'bbsmc': { id: 'bbsmc', name: 'BBSMC', src: 'data/bbsmc_data.js', globalVar: 'bbsmcModpacksData', count: 1802, loaded: false, loading: false, callbacks: [] },
        'xyebbs': { id: 'xyebbs', name: 'XYEBBS', src: 'data/xyebbs_data.js', globalVar: 'xyebbsModpacksData', count: 5175, loaded: false, loading: false, callbacks: [] },
        'modrinth': { id: 'modrinth', name: 'Modrinth', src: 'data/modrinth_data.js', globalVar: 'modrinthModpacksData', count: 18328, loaded: false, loading: false, callbacks: [] },
        'curseforge': { id: 'curseforge', name: 'CurseForge', src: 'data/curseforge_data.js', globalVar: 'curseforgeModpacksData', count: 45797, loaded: false, loading: false, callbacks: [] }
    };
    window.PlatformLoader = PLATFORMS;

    function onPlatformLoaded(platId) {
        if (platId === 'mcmod') {
            enhanceMcmodRows();
            if (activeMcmodVMode === 'cards') {
                renderMcmodCards();
            } else if (window.initMcmodTable) {
                window.initMcmodTable();
            }
        } else if (platId === 'bilibili') {
            biliPacks = window.biliModpacksData || [];
            initBiliDateChips();
            initBiliStats();
            if (currentTab === 'bilibili') renderBiliView();
        } else if (platId === 'bbsmc') {
            bbsmcPacks = window.bbsmcModpacksData || [];
            initBbsmcStats();
            if (currentTab === 'bbsmc') renderBbsmcView();
        } else if (platId === 'xyebbs') {
            xyebbsPacks = window.xyebbsModpacksData || [];
            initXyebbsStats();
            if (currentTab === 'xyebbs') renderXyebbsView();
        } else if (platId === 'modrinth') {
            modrinthPacks = window.modrinthModpacksData || [];
            initModrinthStats();
            if (currentTab === 'modrinth') renderModrinthView();
        } else if (platId === 'curseforge') {
            curseforgePacks = window.curseforgeModpacksData || [];
            initCurseforgeStats();
            if (currentTab === 'curseforge') renderCurseforgeView();
        }
        updateAllPlatformsTotalBadge();
        var q = ($('#crossSearchInput').val() || '').trim();
        if (q) $('#crossSearchInput').trigger('input');
    }

    function loadPlatformScript(platId, callback) {
        var p = PLATFORMS[platId];
        if (!p) { if (callback) callback(); return; }
        if (window[p.globalVar] && window[p.globalVar].length) {
            p.loaded = true;
            if (callback) callback();
            return;
        }
        if (callback) p.callbacks.push(callback);
        if (p.loading) return;
        p.loading = true;

        var script = document.createElement('script');
        script.src = p.src;
        script.async = true;
        script.onload = function() {
            p.loaded = true;
            p.loading = false;
            onPlatformLoaded(platId);
            var cbs = p.callbacks.slice();
            p.callbacks = [];
            cbs.forEach(function(fn) {
                try { fn(); } catch(e) { console.error(e); }
            });
        };
        script.onerror = function() {
            console.error('加载 ' + p.name + ' 数据源失败: ' + p.src);
            p.loading = false;
        };
        document.body.appendChild(script);
    }

    function startIdlePrefetch() {
        var queue = ['bilibili', 'bbsmc', 'xyebbs', 'mcmod', 'modrinth', 'curseforge'];
        function step() {
            if (!queue.length) return;
            var nextId = queue.shift();
            if (PLATFORMS[nextId].loaded || PLATFORMS[nextId].loading) {
                step();
                return;
            }
            loadPlatformScript(nextId, function() {
                setTimeout(step, 150);
            });
        }
        setTimeout(step, 300);
    }

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
    var __catExclude = { bilibili: false, bbsmc: false, xyebbs: false, modrinth: false, curseforge: false };

    /* 分类命中判定：
       - 未选任何分类 => 全部命中；
       - exclude 为假 => 条目分类命中任一所选即通过（并集语义）；
       - exclude 为真 => 命中任一所选即排除（MCMod 的「反向排除模式」）。 */
    function catHitMulti(sel, cats, exclude) {
        if (!sel || !sel.length) return true;
        cats = cats || [];
        var hit = false;
        for (var i = 0; i < cats.length; i++) {
            if (sel.indexOf(cats[i]) !== -1) { hit = true; break; }
        }
        return exclude ? !hit : hit;
    }

    /* ════════════ 分类 / 加载器 的中文展示层 ════════════
       Modrinth 与 CurseForge 的分类是英文原文（multiplayer / Exploration …），
       直接铺在看板上对中文用户不友好。这里只做「展示名」映射：
       筛选、统计、data-cat 一律仍用原始英文值，保证逻辑与数据零改动。
       没收录的值原样返回 —— 不猜、不硬凑。 */
    var __CAT_LABEL = {
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
    };
    // 加载器统一大小写（B站 数据里是 Neoforge，其余平台是 NeoForge）
    var __LOADER_LABEL = { 'Neoforge': 'NeoForge', 'neoforge': 'NeoForge', 'neoForge': 'NeoForge' };
    function catLabel(v) { return (v === null || v === undefined || v === '') ? '' : (__CAT_LABEL[v] || v); }
    function loaderLabel(v) { return (v === null || v === undefined || v === '') ? '' : (__LOADER_LABEL[v] || v); }
    function catLabelList(arr) { return (arr || []).map(catLabel).join(' · '); }
    function loaderLabelList(arr) { return (arr || []).map(loaderLabel).join(' · '); }

    /* 「反向排除」开关的委托绑定：各平台高阶过滤里的 .js-cat-exclude 复选框共用一套逻辑 */
    $(document).on('change', '.js-cat-exclude', function() {
        var plat = $(this).data('plat');
        if (!plat || !(plat in __catExclude)) return;
        __catExclude[plat] = $(this).is(':checked');
        if (plat === 'bilibili') renderBiliView();
        else if (plat === 'bbsmc') { currentBbsmcCardLimit = 48; renderBbsmcView(); }
        else if (plat === 'xyebbs') { currentXyebbsCardLimit = 48; renderXyebbsView(); }
        else if (plat === 'modrinth') { currentModrinthCardLimit = 48; renderModrinthView(); }
        else if (plat === 'curseforge') { currentCurseforgeCardLimit = 48; renderCurseforgeView(); }
    });

    /* ════════════ 卡片平台的「版本与详情」弹窗桥接（向 MCMod 看齐） ════════════
       5 个卡片平台的字段各不相同：B站 有 pub_time / views / mod_count，
       BBSMC/XYEBBS/Modrinth/CurseForge 有 date_created / date_modified / downloads，
       但都没有 MCMod 那种逐版本的改动日志。
       所以这里只做「有就做」：把真实存在的字段组织进同一个弹窗，
       没有的字段一律留空，绝不编造。
       实现上不往 DOM 里塞一长串 data-*（标题含引号会直接破坏属性），
       改为按 url 建索引，点击时回查原始对象。 */
    window.__packByUrl = window.__packByUrl || {};
    function registerPackForModal(p) {
        if (p && p.url) window.__packByUrl[p.url] = p;
        return p;
    }

    /* 各平台弹窗标签覆盖表：字段语义不同，标签也必须跟着不同，
       否则会出现「累计历史版本数: 2297419」这种明显错位。 */
    var __CARD_PLAT_LABELS = {
        bilibili:   { verLabel: '🎮 支持版本', countLabel: '📺 关联发布记录', countUnit: ' 期', typeLabel: '🏷️ 分区与标签', countTagLabel: '累计发布', countTagUnit: ' 期' },
        bbsmc:      { verLabel: '🏷️ 最新支持版本', countLabel: '📥 累计下载量', countUnit: '次', typeLabel: '🏷️ 玩法分类', countTagLabel: '累计下载', countTagUnit: '次' },
        xyebbs:     { verLabel: '🏷️ 最新支持版本', countLabel: '📥 累计下载量', countUnit: '次', typeLabel: '🏷️ 玩法分类', countTagLabel: '累计下载', countTagUnit: '次' },
        modrinth:   { verLabel: '🏷️ 最新支持版本', countLabel: '📥 累计下载量', countUnit: '次', typeLabel: '🏷️ 分类标签', countTagLabel: '累计下载', countTagUnit: '次' },
        curseforge: { verLabel: '🏷️ 最新支持版本', countLabel: '📥 累计下载量', countUnit: '次', typeLabel: '🏷️ 分类标签', countTagLabel: '累计下载', countTagUnit: '次' }
    };

    /* 把原始 pack 对象整理成弹窗所需的 extra，字段缺失就留空 */
    function buildCardModalExtra(plat, p) {
        var lab = __CARD_PLAT_LABELS[plat] || {};
        var ten = function(s) { return s ? String(s).substring(0, 10) : ''; };
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
        for (var li = 0; li < links.length; li++) {
            var lk = links[li];
            if (lk && (lk.version || lk.label)) {
                packVer = (lk.version || lk.label || '').trim();
                break;
            }
        }
        var displayVer = packVer ? (packVer + (p.mc_version ? ' (MC ' + p.mc_version + ')' : '')) : (p.mc_version || (vers[0] || '通用 / 最新'));

        return {
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
        };
    }


    /* 版本号与 Minecraft 运行版本识别算法 */
    function extractVersion(r) {
        if (!r) return '';
        // 1. 优先读取已解析的官方 MC 运行版本 (支持多版本展示，如 ATM10: 1.21.1 / 1.21)
        if (r.mc_versions && Array.isArray(r.mc_versions) && r.mc_versions.length > 0) {
            if (r.mc_versions.length > 2) {
                return 'MC ' + r.mc_versions[0] + ' (+' + (r.mc_versions.length - 1) + ')';
            }
            return 'MC ' + r.mc_versions.join(' / ');
        }
        if (r.mc_version) {
            return 'MC ' + r.mc_version;
        }
        // 2. ATM 家族智能识别 (确保 ATM 无论如何都能准确点亮运行版本徽章)
        var title = r.title || '';
        var mAtm = title.match(/\[ATM([0-9A-Za-z]+)\]/i) || title.match(/All [Tt]he Mods\s*(\d+)/i);
        if (mAtm) {
            var atmKey = mAtm[1].toLowerCase();
            var atmMap = {
                '10': 'MC 1.21.1 / 1.21', '10s': 'MC 1.21.1 / 1.21', '11': 'MC 1.21.1',
                '9': 'MC 1.20.1', '9s': 'MC 1.20.1', '9nf': 'MC 1.20.1', 'g2': 'MC 1.20.1',
                '8': 'MC 1.19.2', '7': 'MC 1.18.2', '7s': 'MC 1.18.2',
                '6': 'MC 1.16.5', '6s': 'MC 1.16.5', '5': 'MC 1.15.2', '4': 'MC 1.14.4',
                '3': 'MC 1.12.2', '3e': 'MC 1.12.2', '3l': 'MC 1.12.2', '3r': 'MC 1.12.2',
                '2': 'MC 1.11.2', '1': 'MC 1.10.2', '0': 'MC 1.7.10', 'ar': 'MC 1.18.2'
            };
            if (atmMap[atmKey]) return atmMap[atmKey];
        }
        // 3. 标题中的明确 Minecraft 版本 (如 [1.20.1] 或 1.12.2)
        var mTitleMC = title.match(/\b(1\.(?:[7-9]|1\d|2\d)(?:\.\d+)?)\b/);
        if (mTitleMC) return 'MC ' + mTitleMC[1];
        // 4. 标题中的整合包大版本号 (如 v1.2.0)
        var mVer = title.match(/\bv(\d+(?:\.\d+)*)\b/i);
        if (mVer) return mVer[0];
        // 5. 标签中的版本
        var mTagsMC = (r.tags_search || '').match(/\b(1\.(?:[7-9]|1\d|2\d)(?:\.\d+)?)\b/);
        if (mTagsMC) return 'MC ' + mTagsMC[1];
        return '';
    }

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

    function enhanceMcmodRows() {
        if (!window.tableRowsData) return;
        window.tableRowsData.forEach(function(r) {
            // 提取封面 URL，确保各模块随时可用且自带防盗链与 fallback
            if (!r.cover_url && r.c0) {
                var mCover = r.c0.match(/data-image-url="([^"]+)"/);
                if (mCover && mCover[1]) {
                    r.cover_url = mCover[1];
                }
            }
            if (r.c0) {
                var verStr = extractVersion(r);
                if (verStr && r.c0.indexOf('modpack-ver-badge') === -1) {
                    var verBadge = '<span class="modpack-ver-badge">' + verStr + '</span>';
                    r.c0 = r.c0.replace('<div class="modpack-meta-row">', '<div class="modpack-meta-row">' + verBadge + ' ');
                }
            }
        });
    }
    enhanceMcmodRows();

    var currentMcmodCardLimit = 48;
    var currentBiliCardLimit = 48;
    var renderedTabs = {};

    /* 渲染 MCMod 画廊卡片 */
    function renderMcmodCards() {
        var $grid = $('#mcmodCardsGrid');
        $grid.empty();
        
        var rows = [];
        if (window.table) {
            rows = window.table.rows({ search: 'applied' }).data().toArray();
        } else if ($.fn.DataTable && $.fn.DataTable.isDataTable('#modpackTable')) {
            var table = $('#modpackTable').DataTable();
            rows = table.rows({ search: 'applied' }).data().toArray();
        } else {
            rows = window.tableRowsData || [];
        }

        $('#mcmodCardCountBadge').text(rows.length + ' 款');
        $('#mcmodMatchedCount').text(rows.length);

        if (rows.length === 0) {
            $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted); font-size:1.1rem;">🔍 未匹配到任何 MC百科整合包</div>');
            return;
        }

        var limit = Math.min(rows.length, currentMcmodCardLimit);
        var htmlArr = [];
        for (var i = 0; i < limit; i++) {
            var r = rows[i];
            var mid = r.mid;
            var title = r.title || '';
            var coverImg = r.cover_url || '';
            if (!coverImg) {
                var mCover = (r.c0 || '').match(/data-image-url="([^"]+)"/);
                if (mCover && mCover[1]) coverImg = mCover[1];
            }
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
        }

        if (rows.length > limit) {
            var remain = rows.length - limit;
            var loadNext = Math.min(remain, 48);
            var loadMoreHtml = '<div class="mcmod-load-more-bar">' +
                '<button type="button" class="btn-card-load-more js-load-more-cards">📥 加载更多 ' + loadNext + ' 款 (剩余 ' + remain + ' 款) ▾</button>' +
                '<button type="button" class="btn-card-load-all js-load-all-cards">⚡ 全部展开 (' + rows.length + ' 款)</button>' +
                '</div>';
            htmlArr.push(loadMoreHtml);
        }
        $grid.html(htmlArr.join(''));
    }

    /* 官方真实分类数据集 (绝不胡乱自创，100% 取自官方数据) */
    var MC_REAL_CATEGORIES = [
        {cat: '科技', count: 936 },
        {cat: '冒险', count: 929 },
        {cat: '任务', count: 897 },
        {cat: '魔法', count: 700 },
        {cat: '国创', count: 630 },
        {cat: '大型', count: 514 },
        {cat: '硬核', count: 448 },
        {cat: '轻量', count: 405 },
        {cat: '休闲', count: 365 },
        {cat: '空岛', count: 249 },
        {cat: '建筑', count: 188 },
        {cat: '剧情', count: 155 },
        {cat: '地图', count: 107 },
        {cat: 'PvP', count: 41 }
    ];

    var BILI_REAL_CATEGORIES = [
        {cat: '冒险', count: 87 },
        {cat: '科技', count: 47 },
        {cat: '休闲/建筑', count: 40 },
        {cat: '宝可梦', count: 37 },
        {cat: '魔改', count: 30 },
        {cat: '战斗/枪械', count: 22 },
        {cat: '魔法', count: 16 },
        {cat: '末日/生存', count: 16 },
        {cat: '空岛', count: 10 }
    ];

    var ALL_REAL_CATEGORIES = [
        {cat: '科技', count: 983 },
        {cat: '冒险', count: 1016 },
        {cat: '魔法', count: 716 },
        {cat: '任务', count: 897 },
        {cat: '国创', count: 630 },
        {cat: '硬核', count: 448 },
        {cat: '宝可梦', count: 122 },
        {cat: '空岛', count: 259 },
        {cat: '休闲', count: 405 }
    ];

    /* 初始化侧边栏分类 Chips */
    var MC_HOT_TAGS = [
        {tag: '机械动力', count: 69},
        {tag: 'FTB', count: 49},
        {tag: '优化', count: 45},
        {tag: '生存', count: 37},
        {tag: 'RPG', count: 31},
        {tag: '格雷科技', count: 26},
        {tag: '养老', count: 25},
        {tag: '战斗', count: 25},
        {tag: '魔改', count: 24},
        {tag: '枪械', count: 23},
        {tag: '末日', count: 19},
        {tag: '僵尸', count: 18},
        {tag: '探索', count: 18},
        {tag: '恐怖', count: 16},
        {tag: '自动化', count: 16},
        {tag: '拔刀剑', count: 15},
        {tag: '暮色森林', count: 15},
        {tag: '应用能源2', count: 14},
        {tag: '植物魔法', count: 14},
        {tag: '等价交换', count: 12},
        {tag: '龙之研究', count: 12},
        {tag: '无尽贪婪', count: 11},
        {tag: '冰与火之歌', count: 11},
        {tag: '宝可梦', count: 10}
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

    function analyzeCompareData() {
        tagCountsMap.clear();
        modCatCountsMap.clear();
        modCountsMap.clear();
        if (!window.compareData) return;
        for (var mid in window.compareData) {
            var item = window.compareData[mid];
            if (!item) continue;
            // 1. 玩法标签
            var tags = item.tags || [];
            for (var i = 0; i < tags.length; i++) {
                var t = String(tags[i] || '').trim();
                if (t) tagCountsMap.set(t, (tagCountsMap.get(t) || 0) + 1);
            }
            // 2. 模组分类
            var mcs = item.mod_categories || [];
            for (var j = 0; j < mcs.length; j++) {
                var mc = String(mcs[j] || '').trim();
                if (mc) modCatCountsMap.set(mc, (modCatCountsMap.get(mc) || 0) + 1);
            }
            // 3. 收录模组
            var mods = item.mods || [];
            for (var k = 0; k < mods.length; k++) {
                var m = mods[k];
                var mName = typeof m === 'string' ? m : (m && m.name ? m.name : '');
                mName = String(mName || '').trim();
                if (mName) modCountsMap.set(mName, (modCountsMap.get(mName) || 0) + 1);
            }
        }

        allTagsList = Array.from(tagCountsMap.keys()).sort(function(a, b) {
            return (tagCountsMap.get(b) - tagCountsMap.get(a)) || a.localeCompare(b, 'zh-CN');
        });

        var standardOrder = ['辅助', 'LIB', '实用', '装饰', '魔改', '冒险', '农业', '科技', '魔法', '未分类'];
        allModCatsList = Array.from(modCatCountsMap.keys()).sort(function(a, b) {
            var ia = standardOrder.indexOf(a), ib = standardOrder.indexOf(b);
            if (ia !== -1 && ib !== -1) return ia - ib;
            if (ia !== -1) return -1;
            if (ib !== -1) return 1;
            return (modCatCountsMap.get(b) - modCatCountsMap.get(a));
        });

        allModsList = Array.from(modCountsMap.keys()).sort(function(a, b) {
            return (modCountsMap.get(b) - modCountsMap.get(a)) || a.localeCompare(b, 'zh-CN');
        });
    }

    function renderCategoryChips() {
        var $mcBox = $('#mcmodCategoryChips');
        $mcBox.empty();
        $mcBox.append('<span class="s-chip active" data-cat="">全部</span>');
        MC_REAL_CATEGORIES.forEach(function(item) {
            $mcBox.append('<span class="s-chip" data-cat="' + escHtml(item.cat, true) + '">' + escHtml(item.cat, true) + ' <span class="s-chip-count">' + item.count + '</span></span>');
        });
    }

    function renderTagChips() {
        var $tagBox = $('#mcmodTagChips');
        if (!$tagBox.length) return;
        $tagBox.empty();
        $tagBox.toggleClass('expanded-chips', tagListExpanded);
        $tagBox.closest('.hub-filter-row').toggleClass('row-expanded', tagListExpanded);
        $tagBox.append('<span class="s-chip active" data-tag="">全部</span>');
        var items = tagListExpanded ? allTagsList : (allTagsList.length ? allTagsList.slice(0, 40) : MC_HOT_TAGS.map(function(x) { return x.tag; }));
        for (var i = 0; i < items.length; i++) {
            var t = items[i];
            var cnt = tagCountsMap.get(t) || 0;
            $tagBox.append('<span class="s-chip" data-tag="' + escHtml(t, true) + '">' + escHtml(t, true) + ' <span class="s-chip-count">' + cnt + '</span></span>');
        }
        syncAllFilterUI();
    }

    function renderModCatChips() {
        var $modCatBox = $('#mcmodModCatChips');
        if (!$modCatBox.length) return;
        $modCatBox.empty();
        $modCatBox.append('<span class="s-chip active" data-mod-cat="">全部</span>');
        for (var i = 0; i < allModCatsList.length; i++) {
            var mc = allModCatsList[i];
            var cnt = modCatCountsMap.get(mc) || 0;
            $modCatBox.append('<span class="s-chip" data-mod-cat="' + escHtml(mc, true) + '">' + escHtml(mc, true) + ' <span class="s-chip-count">' + cnt + '</span></span>');
        }
        syncAllFilterUI();
    }

    function renderHotModChips() {
        var $modBox = $('#mcmodHotModChips');
        if (!$modBox.length) return;
        $modBox.empty();
        $modBox.toggleClass('expanded-chips', modListExpanded);
        $modBox.closest('.hub-filter-row').toggleClass('row-expanded', modListExpanded);
        $modBox.append('<span class="s-chip active" data-mod="">全部</span>');
        var items = modListExpanded ? allModsList.slice(0, 100) : allModsList.slice(0, 40);
        for (var i = 0; i < items.length; i++) {
            var m = items[i];
            var cnt = modCountsMap.get(m) || 0;
            $modBox.append('<span class="s-chip" data-mod="' + escHtml(m, true) + '">' + escHtml(m, true) + ' <span class="s-chip-count">' + cnt + '</span></span>');
        }
        syncAllFilterUI();
    }

    function syncAllFilterUI() {
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
        $('#mcmodCategoryChips .s-chip').each(function() {
            var c = $(this).data('cat');
            if (!c) {
                $(this).toggleClass('active', selCats.length === 0);
            } else {
                $(this).toggleClass('active', selCats.indexOf(c) !== -1);
            }
        });

        // 2. 同步核心标签 Chips
        $('#mcmodTagChips .s-chip').each(function() {
            var t = $(this).data('tag');
            if (!t) {
                $(this).toggleClass('active', selTags.length === 0);
            } else {
                $(this).toggleClass('active', selTags.indexOf(t) !== -1);
            }
        });

        // 3. 同步模组分类 Chips
        $('#mcmodModCatChips .s-chip').each(function() {
            var mc = $(this).data('mod-cat');
            if (!mc) {
                $(this).toggleClass('active', selModCats.length === 0);
            } else {
                $(this).toggleClass('active', selModCats.indexOf(mc) !== -1);
            }
        });

        // 4. 同步包含模组 Chips
        $('#mcmodHotModChips .s-chip').each(function() {
            var m = $(this).data('mod');
            if (!m) {
                $(this).toggleClass('active', selMods.length === 0);
            } else {
                $(this).toggleClass('active', selMods.indexOf(m) !== -1);
            }
        });

        // 5. 渲染 activeFilters 胶囊指示栏 (参考黄游 active-filters)
        var $activeBox = $('#activeFilters');
        var badges = [];
        selCats.forEach(function(c) { badges.push({ field: 'cat', label: '🏷️ 专区: ' + c, val: c }); });
        selTags.forEach(function(t) { badges.push({ field: 'tag', label: '🔥 标签: ' + t, val: t }); });
        selModCats.forEach(function(mc) { badges.push({ field: 'modcat', label: '📦 模组分类: ' + mc, val: mc }); });
        selMods.forEach(function(m) { badges.push({ field: 'mod', label: '🧩 模组: ' + m, val: m }); });
        if (selType) {
            badges.push({ field: 'type', label: '类型: ' + selType, val: selType });
        }
        if (selTrend) {
            var trendText = $('#trendFilter option:selected').text() || selTrend;
            badges.push({ field: 'trend', label: '走势: ' + trendText, val: selTrend });
        }

        if (badges.length === 0) {
            $activeBox.empty().hide();
        } else {
            var badgeHtml = '<span style="font-size:12px; font-weight:750; color:var(--text-secondary); margin-right:4px;">已筛选：</span>';
            badgeHtml += badges.map(function(b) {
                return '<span class="active-filter-badge" data-field="' + b.field + '" data-val="' + escHtml(b.val, true) + '" title="点击移除该条件">' +
                    escHtml(b.label, true) +
                    '<span class="badge-del">×</span>' +
                '</span>';
            }).join('');
            if (badges.length >= 2) {
                badgeHtml += '<button type="button" class="active-filters-clear-all" id="clearAllActiveFilters">清空全部筛选 ↺</button>';
            }
            $activeBox.html(badgeHtml).show();
        }
    }

    function openPicker(field, list, countMap, title, eyebrow, ruleHint) {
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

        function buildItemHtml(item, curSelected) {
            var name = typeof item === 'string' ? item : (item.name || '');
            var count = countMap ? (countMap.get(name) || (typeof item === 'object' ? item.count : 0) || 0) : 0;
            var isActive = curSelected.indexOf(name) !== -1;
            return '<button type="button" class="picker-option' + (isActive ? ' active' : '') + '" data-picker-val="' + escHtml(name, true) + '">' +
                '<span>' + escHtml(name, true) + '</span>' +
                (count ? '<b class="tag-count">(' + count + ')</b>' : '') +
            '</button>';
        }

        function updateStatus() {
            var curSelected = $(selector).val() || [];
            if (!Array.isArray(curSelected)) curSelected = curSelected ? [curSelected] : [];
            var shown = Math.min(filtered.length, currentCap);
            var statusText = '已选 ' + curSelected.length + ' 项 · 找到 ' + filtered.length + ' 项';
            if (filtered.length > shown) {
                statusText += '（已呈现前 ' + shown + ' 项 · 下滑或点击底部自动加载更多）';
            } else {
                statusText += '（已全部呈现）';
            }
            $('#pickerModalStatus').text(statusText);
        }

        function renderGrid() {
            var query = ($('#pickerModalSearch').val() || '').trim().toLowerCase();
            var curSelected = $(selector).val() || [];
            if (!Array.isArray(curSelected)) curSelected = curSelected ? [curSelected] : [];

            filtered = list;
            if (query) {
                filtered = list.filter(function(item) {
                    var name = typeof item === 'string' ? item : (item.name || '');
                    return name.toLowerCase().indexOf(query) !== -1;
                });
            }

            currentCap = query ? 500 : 300;
            var displayItems = filtered.slice(0, currentCap);

            var gridHtml = '';
            if (displayItems.length === 0) {
                gridHtml = '<div style="grid-column:1/-1; padding:2.5rem; text-align:center; color:var(--text-muted);">🔍 没有找到匹配项，试试其他关键词</div>';
            } else {
                for (var i = 0; i < displayItems.length; i++) {
                    gridHtml += buildItemHtml(displayItems[i], curSelected);
                }
                if (filtered.length > currentCap) {
                    gridHtml += '<div id="pickerMoreBar" style="grid-column:1/-1; text-align:center; padding:12px 0;">' +
                        '<button type="button" id="btnPickerLoadMore" style="background:var(--primary); color:#fff; border:none; border-radius:8px; padding:8px 20px; font-weight:700; cursor:pointer; font-size:0.88rem; box-shadow:0 3px 10px rgba(0,0,0,0.15);">' +
                            '📥 加载更多 200 项 (剩余 ' + (filtered.length - currentCap) + ' 项) ▾' +
                        '</button>' +
                    '</div>';
                }
            }
            $('#pickerModalGrid').html(gridHtml);
            updateStatus();
        }

        function loadMoreBatch() {
            if (currentCap >= filtered.length) return;
            var curSelected = $(selector).val() || [];
            if (!Array.isArray(curSelected)) curSelected = curSelected ? [curSelected] : [];
            var start = currentCap;
            var end = Math.min(filtered.length, currentCap + 200);
            currentCap = end;

            $('#pickerMoreBar').remove();
            var appendHtml = '';
            for (var i = start; i < end; i++) {
                appendHtml += buildItemHtml(filtered[i], curSelected);
            }
            if (filtered.length > currentCap) {
                appendHtml += '<div id="pickerMoreBar" style="grid-column:1/-1; text-align:center; padding:12px 0;">' +
                    '<button type="button" id="btnPickerLoadMore" style="background:var(--primary); color:#fff; border:none; border-radius:8px; padding:8px 20px; font-weight:700; cursor:pointer; font-size:0.88rem; box-shadow:0 3px 10px rgba(0,0,0,0.15);">' +
                        '📥 加载更多 200 项 (剩余 ' + (filtered.length - currentCap) + ' 项) ▾' +
                    '</button>' +
                '</div>';
            }
            $('#pickerModalGrid').append(appendHtml);
            updateStatus();
        }

        renderGrid();

        // 触底自动滚动加载 + 按钮手动点击加载，平滑展现所有万级模组
        $('#pickerModalGrid').off('scroll').on('scroll', function() {
            var el = this;
            if (el.scrollHeight - el.scrollTop - el.clientHeight < 260) {
                loadMoreBatch();
            }
        });

        $('#pickerModalGrid').off('click', '#btnPickerLoadMore').on('click', '#btnPickerLoadMore', function(e) {
            e.preventDefault();
            loadMoreBatch();
        });

        $('#pickerModalSearch').on('input', function() {
            renderGrid();
        });

        $('#pickerModalGrid').off('click', '.picker-option').on('click', '.picker-option', function() {
            var val = $(this).attr('data-picker-val');
            toggleMultiSelect(selector, val);
            var curSelected = $(selector).val() || [];
            if (!Array.isArray(curSelected)) curSelected = curSelected ? [curSelected] : [];
            $(this).toggleClass('active', curSelected.indexOf(val) !== -1);
            updateStatus();
            syncAllFilterUI();
        });

        $('#pickerModalClear').off('click').on('click', function() {
            $(selector).val(null).trigger('change');
            $('#pickerModalGrid .picker-option').removeClass('active');
            updateStatus();
            syncAllFilterUI();
        });

        $('#pickerModalDone').off('click').on('click', function() {
            if (modalEl.close) modalEl.close();
            else $modal.hide();
            syncAllFilterUI();
        });

        if (modalEl.showModal) modalEl.showModal();
        else $modal.show();
        setTimeout(function() { $('#pickerModalSearch').focus(); }, 100);
    }

    function initSidebarChips() {
        analyzeCompareData();
        renderCategoryChips();
        renderTagChips();
        renderModCatChips();
        renderHotModChips();

        // 5. B站自制玩法分类 Chips
        var $biliBox = $('#biliCategoryChips');
        $biliBox.empty();
        $biliBox.append('<span class="s-chip active" data-cat="">全部</span>');
        BILI_REAL_CATEGORIES.forEach(function(item) {
            $biliBox.append('<span class="s-chip" data-cat="' + escHtml(item.cat, true) + '">' + escHtml(item.cat, true) + ' <span class="s-chip-count">' + item.count + '</span></span>');
        });

        // 6. 全平台热门分类 Chips
        var $allBox = $('#allCategoryChips');
        if ($allBox.length) {
            $allBox.empty();
            ALL_REAL_CATEGORIES.forEach(function(item) {
                $allBox.append('<span class="s-chip" data-cat="' + escHtml(item.cat, true) + '">' + escHtml(item.cat, true) + ' <span class="s-chip-count">' + item.count + '</span></span>');
            });
        }
    }
    initSidebarChips();

    window.renderSidebarTags = function(tab) {
        if (tab === 'mcmod') {
            $('#sidebarMcmodFilters').show();
            $('#sidebarBiliFilters').hide();
            $('#sidebarAllFilters').hide();
            // 同步 MCMod 激活分类
            var curVals = $('#categoryFilter').val() || [];
            if (!Array.isArray(curVals)) curVals = [curVals];
            $('#mcmodCategoryChips .s-chip').each(function() {
                var c = $(this).data('cat');
                if (curVals.indexOf(c) !== -1) {
                    $(this).addClass('active');
                } else {
                    $(this).removeClass('active');
                }
            });
        } else if (tab === 'bilibili') {
            $('#sidebarBiliFilters').show();
            $('#sidebarMcmodFilters').hide();
            $('#sidebarAllFilters').hide();
            $('#biliCategoryChips .s-chip').each(function() {
                var c = $(this).data('cat');
                if (activeCat.indexOf(c) !== -1) {
                    $(this).addClass('active');
                } else {
                    $(this).removeClass('active');
                }
            });
            $('#biliDateChips .s-chip').each(function() {
                var d = $(this).data('date') || '';
                if (activeDate === d) {
                    $(this).addClass('active');
                } else {
                    $(this).removeClass('active');
                }
            });
            $('#biliPanChips .s-chip').each(function() {
                var p = $(this).data('pan') || '';
                if (activePan === p) {
                    $(this).addClass('active');
                } else {
                    $(this).removeClass('active');
                }
            });
        } else {
            $('#sidebarAllFilters').show();
            $('#sidebarMcmodFilters').hide();
            $('#sidebarBiliFilters').hide();
        }
    };

        /* 全局跨标签页搜索同步与穿透跳转引擎 */
    function getActiveSearchQuery() {
        if (currentTab === 'all') return ($('#crossSearchInput').val() || '').trim();
        if (currentTab === 'bilibili') return ($('#biliSearchInput').val() || '').trim();
        if (currentTab === 'bbsmc') return ($('#bbsmcSearchInput').val() || '').trim();
        if (currentTab === 'xyebbs') return ($('#xyebbsSearchInput').val() || '').trim();
        if (currentTab === 'modrinth') return ($('#modrinthSearchInput').val() || '').trim();
        if (currentTab === 'curseforge') return ($('#curseforgeSearchInput').val() || '').trim();
        if (currentTab === 'mcmod') {
            return ($('#mcmodUnifiedSearch').val() || (window.table ? window.table.search() : '') || '').trim();
        }
        return '';
    }

    window.jumpToPlatformSearch = function(plat, query) {
        var qStr = (query !== undefined && query !== null) ? String(query).trim() : '';
        if (plat === 'mcmod') {
            $('#mcmodUnifiedSearch').val(qStr);
        } else if (plat === 'bilibili') {
            $('#biliSearchInput').val(qStr);
            if (qStr) $('#biliSearchClear').show(); else $('#biliSearchClear').hide();
        } else if (plat === 'bbsmc') {
            $('#bbsmcSearchInput').val(qStr);
            if (qStr) $('#bbsmcSearchClear').show(); else $('#bbsmcSearchClear').hide();
        } else if (plat === 'xyebbs') {
            $('#xyebbsSearchInput').val(qStr);
            if (qStr) $('#xyebbsSearchClear').show(); else $('#xyebbsSearchClear').hide();
        } else if (plat === 'modrinth') {
            $('#modrinthSearchInput').val(qStr);
            if (qStr) $('#modrinthSearchClear').show(); else $('#modrinthSearchClear').hide();
        } else if (plat === 'curseforge') {
            $('#curseforgeSearchInput').val(qStr);
            if (qStr) $('#curseforgeSearchClear').show(); else $('#curseforgeSearchClear').hide();
        }

        switchPlatformTab(plat);

        loadPlatformScript(plat, function() {
            if (plat === 'mcmod') {
                if (window.table && qStr) {
                    window.table.search(qStr).draw();
                }
                if (typeof renderMcmodCards === 'function' && activeMcmodVMode === 'cards') {
                    renderMcmodCards();
                }
            } else if (plat === 'bilibili') {
                if (typeof renderBiliView === 'function') renderBiliView();
            } else if (plat === 'bbsmc') {
                if (typeof renderBbsmcView === 'function') renderBbsmcView();
            } else if (plat === 'xyebbs') {
                if (typeof renderXyebbsView === 'function') renderXyebbsView();
            } else if (plat === 'modrinth') {
                if (typeof renderModrinthView === 'function') renderModrinthView();
            } else if (plat === 'curseforge') {
                if (typeof renderCurseforgeView === 'function') renderCurseforgeView();
            }
        });
    };

    function syncSearchQueryToTab(targetTab, query) {
        if (!query) return;
        window.jumpToPlatformSearch(targetTab, query);
    }

    window.jumpToPlatformWithCurrentSearch = function(plat) {
        var q = ($('#crossSearchInput').val() || '').trim();
        window.jumpToPlatformSearch(plat, q);
    };

    $(document).on('click', '.js-jump-platform-search', function(e) {
        e.stopPropagation();
        var plat = $(this).data('platform');
        var query = $(this).data('query');
        window.jumpToPlatformSearch(plat, query);
    });

    window.switchPlatformTab = function(tab) {
        $('.nav-item').removeClass('active');
        $('.nav-item[data-tab="' + tab + '"]').addClass('active');
        $('.top-plat-btn').removeClass('active');
        $('.top-plat-btn[data-tab="' + tab + '"]').addClass('active');
        currentTab = tab;
        window.scrollTo(0, 0);

        renderSidebarTags(tab);

        if (tab === 'all') {
            $('#view-all').show().addClass('active');
            $('#view-mcmod, #view-bilibili, #view-bbsmc, #view-xyebbs, #view-modrinth, #view-curseforge').hide().removeClass('active');
            $('#mcmodViewToggle, #biliViewToggle').hide();
            $('#crumbCurrentTab').text('全平台总览');
            $('#crumbCurrentView').text('综合大盘');
            window.location.hash = '#all';
        } else if (tab === 'bilibili') {
            $('#view-all, #view-mcmod, #view-bbsmc, #view-xyebbs, #view-modrinth, #view-curseforge').hide().removeClass('active');
            $('#view-bilibili').show().addClass('active');
            $('#mcmodViewToggle').hide();
            $('#biliViewToggle').show();
            $('#crumbCurrentTab').text('B站自制整合包');
            $('#crumbCurrentView').text(activeGroupMode === 'grouped' ? '同包聚合' : '单条平铺');
            window.location.hash = '#bilibili';
            if (!renderedTabs['bilibili']) {
                if (!PLATFORMS['bilibili'].loaded && (!window.biliModpacksData || !window.biliModpacksData.length)) {
                    $('#biliCardsGrid').html('<div class="platform-loading-box" style="grid-column:1/-1; text-align:center; padding:3.5rem; color:var(--text-secondary);"><div style="font-size:2rem; margin-bottom:0.5rem; animation:pulse 1s infinite;">📺</div>正在极速接入 B站 935 款自制整合包发布流...</div>');
                }
                loadPlatformScript('bilibili', function() {
                    renderBiliView();
                    renderedTabs['bilibili'] = true;
                });
            }
        } else if (tab === 'bbsmc') {
            $('#view-all, #view-mcmod, #view-bilibili, #view-xyebbs, #view-modrinth, #view-curseforge').hide().removeClass('active');
            $('#view-bbsmc').show().addClass('active');
            $('#mcmodViewToggle, #biliViewToggle').hide();
            $('#crumbCurrentTab').text('BBSMC开放资源');
            $('#crumbCurrentView').text('开源模组包库');
            window.location.hash = '#bbsmc';
            if (!renderedTabs['bbsmc']) {
                if (!PLATFORMS['bbsmc'].loaded && (!window.bbsmcModpacksData || !window.bbsmcModpacksData.length)) {
                    $('#bbsmcCardsGrid').html('<div class="platform-loading-box" style="grid-column:1/-1; text-align:center; padding:3.5rem; color:var(--text-secondary);"><div style="font-size:2rem; margin-bottom:0.5rem; animation:pulse 1s infinite;">💎</div>正在极速接入 BBSMC 1,802 款开源模组包...</div>');
                }
                loadPlatformScript('bbsmc', function() {
                    renderBbsmcView();
                    renderedTabs['bbsmc'] = true;
                });
            }
        } else if (tab === 'xyebbs') {
            $('#view-all, #view-mcmod, #view-bilibili, #view-bbsmc, #view-modrinth, #view-curseforge').hide().removeClass('active');
            $('#view-xyebbs').show().addClass('active');
            $('#mcmodViewToggle, #biliViewToggle').hide();
            $('#crumbCurrentTab').text('XYEBBS像素世界');
            $('#crumbCurrentView').text('社区资源专区');
            window.location.hash = '#xyebbs';
            if (!renderedTabs['xyebbs']) {
                if (!PLATFORMS['xyebbs'].loaded && (!window.xyebbsModpacksData || !window.xyebbsModpacksData.length)) {
                    $('#xyebbsCardsGrid').html('<div class="platform-loading-box" style="grid-column:1/-1; text-align:center; padding:3.5rem; color:var(--text-secondary);"><div style="font-size:2rem; margin-bottom:0.5rem; animation:pulse 1s infinite;">🍃</div>正在极速接入 XYEBBS 5,175 款社区整合包...</div>');
                }
                loadPlatformScript('xyebbs', function() {
                    renderXyebbsView();
                    renderedTabs['xyebbs'] = true;
                });
            }
        } else if (tab === 'modrinth') {
            $('#view-all, #view-mcmod, #view-bilibili, #view-bbsmc, #view-xyebbs, #view-curseforge').hide().removeClass('active');
            $('#view-modrinth').show().addClass('active');
            $('#mcmodViewToggle, #biliViewToggle').hide();
            $('#crumbCurrentTab').text('Modrinth国际服');
            $('#crumbCurrentView').text('开源模组包库');
            window.location.hash = '#modrinth';
            if (!renderedTabs['modrinth']) {
                if (!PLATFORMS['modrinth'].loaded && (!window.modrinthModpacksData || !window.modrinthModpacksData.length)) {
                    $('#modrinthCardsGrid').html('<div class="platform-loading-box" style="grid-column:1/-1; text-align:center; padding:3.5rem; color:var(--text-secondary);"><div style="font-size:2rem; margin-bottom:0.5rem; animation:pulse 1s infinite;">🌐</div>正在极速接入 Modrinth 18,328 款开源模组包...</div>');
                }
                loadPlatformScript('modrinth', function() {
                    renderModrinthView();
                    renderedTabs['modrinth'] = true;
                });
            }
        } else if (tab === 'curseforge') {
            $('#view-all, #view-mcmod, #view-bilibili, #view-bbsmc, #view-xyebbs, #view-modrinth').hide().removeClass('active');
            $('#view-curseforge').show().addClass('active');
            $('#mcmodViewToggle, #biliViewToggle').hide();
            $('#crumbCurrentTab').text('CurseForge国际服');
            $('#crumbCurrentView').text('全球殿堂包专区');
            window.location.hash = '#curseforge';
            if (!renderedTabs['curseforge']) {
                if (!PLATFORMS['curseforge'].loaded && (!window.curseforgeModpacksData || !window.curseforgeModpacksData.length)) {
                    $('#curseforgeCardsGrid').html('<div class="platform-loading-box" style="grid-column:1/-1; text-align:center; padding:3.5rem; color:var(--text-secondary);"><div style="font-size:2rem; margin-bottom:0.5rem; animation:pulse 1s infinite;">🔥</div>正在极速接入 CurseForge 45,797 款全球殿堂巨作...</div>');
                }
                loadPlatformScript('curseforge', function() {
                    renderCurseforgeView();
                    renderedTabs['curseforge'] = true;
                });
            }
        } else {
            $('#view-all, #view-bilibili, #view-bbsmc, #view-xyebbs, #view-modrinth, #view-curseforge').hide().removeClass('active');
            $('#view-mcmod').show().addClass('active');
            $('#mcmodViewToggle').show();
            $('#biliViewToggle').hide();
            $('#crumbCurrentTab').text('MC百科整合包');
            $('#crumbCurrentView').text(activeMcmodVMode === 'cards' ? '画廊卡片' : '专业多维表格');
            window.location.hash = '#mcmod';
            if (!renderedTabs['mcmod']) {
                loadPlatformScript('mcmod', function() {
                    if (activeMcmodVMode === 'cards') {
                        renderMcmodCards();
                    } else if (window.initMcmodTable) {
                        window.initMcmodTable();
                    }
                    renderedTabs['mcmod'] = true;
                });
            } else {
                if (activeMcmodVMode === 'cards') {
                    renderMcmodCards();
                } else if (!$.fn.DataTable.isDataTable('#modpackTable') && window.initMcmodTable) {
                    window.initMcmodTable();
                } else if (window.table) {
                    window.table.columns.adjust();
                }
            }
        }
    };

    $(document).on('click', '.nav-item', function() {
        var tab = $(this).data('tab');
        if (tab) switchPlatformTab(tab);
    });

    if (window.location.hash === '#mcmod') {
        switchPlatformTab('mcmod');
    } else if (window.location.hash === '#modrinth') {
        switchPlatformTab('modrinth');
    } else if (window.location.hash === '#curseforge') {
        switchPlatformTab('curseforge');
    } else if (window.location.hash === '#bilibili') {
        switchPlatformTab('bilibili');
    } else if (window.location.hash === '#bbsmc') {
        switchPlatformTab('bbsmc');
    } else if (window.location.hash === '#xyebbs') {
        switchPlatformTab('xyebbs');
    } else {
        switchPlatformTab('all');
    }

    /* 跨平台联合穿透搜索交互 */
        // 热门快搜标签点击即搜
    $(document).on('click', '.hot-chip', function() {
        var q = $(this).data('query');
        $('#crossSearchInput').val(q).trigger('input').focus();
    });

    // 清空搜索按钮点击
    $('#crossSearchClear').on('click', function() {
        $('#crossSearchInput').val('').trigger('input').focus();
    });

    // 全局快捷键 Ctrl+K / '/' 聚焦跨平台搜索框
    $(document).on('keydown', function(e) {
        if ((e.ctrlKey && (e.key === 'k' || e.key === 'K')) || (e.key === '/' && !$(e.target).is('input, textarea, select'))) {
            e.preventDefault();
            if ($('#view-all').is(':visible')) {
                $('#crossSearchInput').focus().select();
            } else {
                switchPlatformTab('all');
                setTimeout(function() {
                    $('#crossSearchInput').focus().select();
                }, 150);
            }
        } else if (e.key === 'Escape' && $('#crossSearchInput').is(':focus')) {
            $('#crossSearchInput').val('').trigger('input').blur();
        }
    });

    /* 跨平台联合穿透搜索交互 */
    $('#crossSearchInput').on('input', function() {
        var query = $(this).val().trim().toLowerCase();
        var $clearBtn = $('#crossSearchClear');
        var $grid = $('#crossResultsGrid');
        var $mcBox = $('#crossMcmodResults');
        var $biliBox = $('#crossBiliResults');
        var $bbsmcBox = $('#crossBbsmcResults');
        var $xyebbsBox = $('#crossXyebbsResults');
        var $modrinthBox = $('#crossModrinthResults');
        var $curseforgeBox = $('#crossCurseforgeResults');

        if (!query) {
            $clearBtn.hide();
            $grid.removeClass('active').hide().css('display', 'none');
            $mcBox.empty();
            $biliBox.empty();
            $bbsmcBox.empty();
            $xyebbsBox.empty();
            $modrinthBox.empty();
            $curseforgeBox.empty();
            return;
        }

        $clearBtn.show();
        $grid.addClass('active').show().css('display', 'grid');

        // 1. 搜索 MC百科
        var mcMatches = [];
        var mcRows = window.tableRowsData || [];
        for (var i = 0; i < mcRows.length; i++) {
            var r = mcRows[i];
            var searchTxt = ((r.title || '') + ' ' + (r.title_en || '') + ' ' + (r.category || '') + ' ' + (r.tags_search || '') + ' ' + (r.c6 || '')).toLowerCase();
            if (searchTxt.indexOf(query) !== -1) {
                mcMatches.push(r);
                if (mcMatches.length >= 4) break;
            }
        }

        if (mcMatches.length === 0) {
            $mcBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 MC百科 词条</div>');
        } else {
            var mcHtml = '';
            mcMatches.forEach(function(item) {
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
            });
            $mcBox.html(mcHtml);
        }

        // 2. 搜索 B站
        var biliMatches = [];
        var bPacks = window.biliModpacksData || [];
        if ((!window.biliModpacksData || !window.biliModpacksData.length) && typeof loadPlatformScript === 'function') {
            loadPlatformScript('bilibili');
        }
        if (PLATFORMS['bilibili'] && !PLATFORMS['bilibili'].loaded && (!bPacks || !bPacks.length)) {
            $biliBox.html('<div style="font-size:12px; color:var(--primary); padding:10px 0;">⏳ B站自制数据加载中...</div>');
        } else {
            for (var j = 0; j < bPacks.length; j++) {
                var bp = bPacks[j];
                var bTxt = ((bp.title || '') + ' ' + (bp.author || '') + ' ' + (bp.desc || '') + ' ' + (bp.mc_version || '') + ' ' + (bp.subtitle_text || '')).toLowerCase();
                if (bTxt.indexOf(query) !== -1) {
                    biliMatches.push(bp);
                    if (biliMatches.length >= 4) break;
                }
            }

            if (biliMatches.length === 0) {
                $biliBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 B站 视频</div>');
            } else {
                var bHtml = '';
                biliMatches.forEach(function(bp) {
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
                    if (bp.download_links && bp.download_links.length > 0) {
                        bHtml += '<span style="color:#10b981; font-weight:700;">📦 网盘可用</span>';
                    }
                    bHtml += '    </div>';
                    bHtml += '    <div class="cross-item-actions">';
                    bHtml += '      <button type="button" class="cross-action-btn cross-btn-in js-jump-platform-search" data-platform="bilibili" data-query="' + safeTitle + '" title="在站内筛选查看该项目">站内 ➔</button>';
                    bHtml += '      <a href="' + bExtUrl + '" target="_blank" rel="noopener noreferrer" class="cross-action-btn cross-btn-ext" onclick="event.stopPropagation();" title="在新标签页直接打开 B站 视频">原站 ↗</a>';
                    bHtml += '    </div>';
                    bHtml += '  </div>';
                    bHtml += '</div>';
                });
                $biliBox.html(bHtml);
            }
        }

        // 3. 搜索 BBSMC
        var bbsmcMatches = [];
        var bPacksBbs = window.bbsmcModpacksData || [];
        if ((!window.bbsmcModpacksData || !window.bbsmcModpacksData.length) && typeof loadPlatformScript === 'function') {
            loadPlatformScript('bbsmc');
        }
        if (PLATFORMS['bbsmc'] && !PLATFORMS['bbsmc'].loaded && (!bPacksBbs || !bPacksBbs.length)) {
            $bbsmcBox.html('<div style="font-size:12px; color:var(--primary); padding:10px 0;">⏳ BBSMC数据加载中...</div>');
        } else {
            for (var k = 0; k < bPacksBbs.length; k++) {
                var bb = bPacksBbs[k];
                var bbTxt = ((bb.title || '') + ' ' + (bb.author || '') + ' ' + (bb.description || '') + ' ' + (bb.mc_version || '') + ' ' + (bb.loaders || []).join(' ') + ' ' + (bb.categories || []).join(' ')).toLowerCase();
                if (bbTxt.indexOf(query) !== -1) {
                    bbsmcMatches.push(bb);
                    if (bbsmcMatches.length >= 4) break;
                }
            }

            if (bbsmcMatches.length === 0) {
                $bbsmcBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 BBSMC 资源</div>');
            } else {
                var bbHtml = '';
                bbsmcMatches.forEach(function(bb) {
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
                });
                $bbsmcBox.html(bbHtml);
            }
        }

        // 4. 搜索 XYEBBS
        var xyebbsMatches = [];
        var bPacksXye = window.xyebbsModpacksData || [];
        if ((!window.xyebbsModpacksData || !window.xyebbsModpacksData.length) && typeof loadPlatformScript === 'function') {
            loadPlatformScript('xyebbs');
        }
        if (PLATFORMS['xyebbs'] && !PLATFORMS['xyebbs'].loaded && (!bPacksXye || !bPacksXye.length)) {
            $xyebbsBox.html('<div style="font-size:12px; color:var(--primary); padding:10px 0;">⏳ XYEBBS数据加载中...</div>');
        } else {
            for (var m = 0; m < bPacksXye.length; m++) {
                var xp = bPacksXye[m];
                var xpTxt = ((xp.title || '') + ' ' + (xp.author || '') + ' ' + (xp.description || '') + ' ' + (xp.mc_version || '') + ' ' + (xp.loaders || []).join(' ') + ' ' + (xp.categories || []).join(' ')).toLowerCase();
                if (xpTxt.indexOf(query) !== -1) {
                    xyebbsMatches.push(xp);
                    if (xyebbsMatches.length >= 4) break;
                }
            }

            if (xyebbsMatches.length === 0) {
                $xyebbsBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 XYEBBS 资源</div>');
            } else {
                var xpHtml = '';
                xyebbsMatches.forEach(function(xp) {
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
                });
                $xyebbsBox.html(xpHtml);
            }
        }

        // 5. 搜索 Modrinth
        var modrinthMatches = [];
        var mPacks = window.modrinthModpacksData || [];
        if ((!window.modrinthModpacksData || !window.modrinthModpacksData.length) && typeof loadPlatformScript === 'function') {
            loadPlatformScript('modrinth');
        }
        if (PLATFORMS['modrinth'] && !PLATFORMS['modrinth'].loaded && (!mPacks || !mPacks.length)) {
            $modrinthBox.html('<div style="font-size:12px; color:var(--primary); padding:10px 0;">⏳ Modrinth数据加载中...</div>');
        } else {
            for (var mi = 0; mi < mPacks.length; mi++) {
                var mp = mPacks[mi];
                var mTarget = ((mp.title || '') + ' ' + (mp.slug || '') + ' ' + (mp.author || '') + ' ' + (mp.description || '') + ' ' + (mp.categories || []).join(' ')).toLowerCase();
                if (mTarget.indexOf(query) !== -1) {
                    modrinthMatches.push(mp);
                    if (modrinthMatches.length >= 4) break;
                }
            }

            if (modrinthMatches.length === 0) {
                $modrinthBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 Modrinth 项目</div>');
            } else {
                var mHtml = '';
                modrinthMatches.forEach(function(mp) {
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
                });
                $modrinthBox.html(mHtml);
            }
        }

        // 6. 搜索 CurseForge
        var curseforgeMatches = [];
        var cfPacks = window.curseforgeModpacksData || [];
        if ((!window.curseforgeModpacksData || !window.curseforgeModpacksData.length) && typeof loadPlatformScript === 'function') {
            loadPlatformScript('curseforge');
        }
        if (PLATFORMS['curseforge'] && !PLATFORMS['curseforge'].loaded && (!cfPacks || !cfPacks.length)) {
            $curseforgeBox.html('<div style="font-size:12px; color:var(--primary); padding:10px 0;">⏳ CurseForge数据加载中...</div>');
        } else {
            for (var cfi = 0; cfi < cfPacks.length; cfi++) {
                var cp = cfPacks[cfi];
                var cpTarget = ((cp.title || '') + ' ' + (cp.slug || '') + ' ' + (cp.author || '') + ' ' + (cp.description || '') + ' ' + (cp.categories || []).join(' ')).toLowerCase();
                if (cpTarget.indexOf(query) !== -1) {
                    curseforgeMatches.push(cp);
                    if (curseforgeMatches.length >= 4) break;
                }
            }

            if (curseforgeMatches.length === 0) {
                $curseforgeBox.html('<div style="font-size:12px; color:var(--text-muted); padding:10px 0;">未找到与“' + $('<div>').text(query).html() + '”相关的 CurseForge 项目</div>');
            } else {
                var cfHtml = '';
                curseforgeMatches.forEach(function(cp) {
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
                });
                $curseforgeBox.html(cfHtml);
            }
        }
    });

    $(document).on('click', '.js-cross-mc-item', function() {
        var t = $(this).attr('data-title');
        jumpToMcmodSearch(t);
    });

    $(document).on('click', '.js-cross-bili-item', function() {
        var t = $(this).attr('data-title');
        jumpToBiliSearch(t);
    });

    $(document).on('click', '.js-cross-bbsmc-item', function() {
        var t = $(this).attr('data-title');
        jumpToBbsmcSearch(t);
    });

    $(document).on('click', '.js-cross-xyebbs-item', function() {
        var t = $(this).attr('data-title');
        jumpToXyebbsSearch(t);
    });

    window.jumpToMcmodSearch = function(title) { window.jumpToPlatformSearch('mcmod', title); };
    window.jumpToBiliSearch = function(title) { window.jumpToPlatformSearch('bilibili', title); };
    window.jumpToBbsmcSearch = function(title) { window.jumpToPlatformSearch('bbsmc', title); };
    window.jumpToXyebbsSearch = function(title) { window.jumpToPlatformSearch('xyebbs', title); };
    window.jumpToModrinthSearch = function(title) { window.jumpToPlatformSearch('modrinth', title); };
    window.jumpToCurseforgeSearch = function(title) { window.jumpToPlatformSearch('curseforge', title); };

    $(document).on('click', '.js-cross-modrinth-item', function() {
        var t = $(this).attr('data-title');
        jumpToModrinthSearch(t);
    });

    $(document).on('click', '.js-cross-curseforge-item', function() {
        var t = $(this).attr('data-title');
        jumpToCurseforgeSearch(t);
    });

    /* 核心包名提取与归一化算法 (彻底修复中文通配符吞噬真实包名Bug，并剔除营销前缀与副标题) */
    var BILI_GENRE_BUZZWORDS = /(?:rpg|冒险|高度定制|史诗战斗|魔法|枪械|科技|生存|剧情|硬核|沉浸式|高难|爽游|原版|魔改|养老|纯净|探索|空岛|地牢|格斗|战斗|拔刀剑|工业|建造|现代战争)/ig;

    function cleanPackKey(s) {
        if (!s) return '';
        s = s.replace(/[\uD835][\uDC00-\uDFFF]/g, '');
        s = s.replace(/(?:我的世界|minecraft|mine\s*craft|mc)/ig, ' ');
        s = s.replace(/[【】\[\]（）\(\)\{\}「」『』《》/|·~～!！?？:：\-—+*#]+/g, ' ');
        s = s.replace(/(?:mc|minecraft|我的世界)?\s*1\.\d{1,2}(?:\.\d+)?/ig, ' ');
        s = s.replace(/(?:v|ver|version)?\s*\d+(?:\.\d+)+(?:[a-z\d_\-\.]*)?/ig, ' ');
        s = s.replace(/(?:v|ver|version)\s*\d+/ig, ' ');
        s = s.replace(/\b(?:forge|fabric|neoforge|quilt)\b/ig, ' ');
        s = s.replace(/(?:整合包|模组包|魔改包|懒人包|重制版|正式版|抢先版|公测版|抢先体验|测试版)/ig, ' ');
        s = s.replace(/(?:最新|首发|公测|更新|发布|分享|下载|自制|自创|开坑|入坑|通关|介绍|演示|实况|推荐)/ig, ' ');
        s = s.replace(BILI_GENRE_BUZZWORDS, ' ');
        s = s.replace(/(?:新的征途.*|从此刻开始.*|第一期.*|第二期.*|第\d+期.*|ep\d+.*)/ig, ' ');
        s = s.replace(/[^\u4e00-\u9fa5a-zA-Z0-9]/g, ' ').trim().toLowerCase();
        s = s.replace(/\s+/g, ' ');
        return s;
    }

    var BILI_GENERIC_PACK_KEYS = new Set([
        '', 'mc', '我的世界', 'minecraft', '模组', '整合', '游戏', '自制', '包', '整合包',
        '全新', '纯净', '高配', '低配', '生存', '冒险', '科技', '魔法', '空岛', '大型',
        '超好玩', '免费', '客户端', '体验'
    ]);

    /* 智能同包聚合器 (同作者作用域隔离 + 精准核心名聚类，实现同包多版无缝合并) */
    function groupPacks(packs) {
        var map = {};
        var groups = [];
        window.biliGroupsMap = map;

        packs.forEach(function(p) {
            var rawKey = cleanPackKey(p.title);
            var authorKey = (p.author || 'unknown').trim().toLowerCase();
            var key = '';

            // 规则1：如果提取出的名字为空、长度小于2、或者属于泛用通用词，坚决不跨视频聚合，保持单视频独立！
            if (!rawKey || rawKey.length < 2 || BILI_GENERIC_PACK_KEYS.has(rawKey)) {
                key = '__raw_' + p.bvid;
            } else {
                // 规则2：同作者公共核心名二阶段聚类（如 UP 终极劲爽全家桶 的两期 逆转未来 视频）
                var matchedExistingKey = null;
                for (var k in map) {
                    if (k.indexOf(authorKey + '::') === 0) {
                        var existRaw = k.substring(authorKey.length + 2);
                        if (existRaw === rawKey || 
                            (existRaw.length >= 2 && rawKey.indexOf(existRaw) !== -1) || 
                            (rawKey.length >= 2 && existRaw.indexOf(rawKey) !== -1)) {
                            matchedExistingKey = k;
                            break;
                        }
                    }
                }
                if (matchedExistingKey) {
                    key = matchedExistingKey;
                } else {
                    key = authorKey + '::' + rawKey;
                }
            }

            if (!map[key]) {
                map[key] = {
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
                };
                groups.push(map[key]);
            }

            var g = map[key];
            g.items.push(p);

            if ((p.pub_timestamp || 0) > g.latestTimestamp) {
                g.latestTimestamp = p.pub_timestamp || 0;
                g.latestPubTime = p.pub_time || '';
                g.displayTitle = p.title;
                g.pic = p.pic;
            }

            if (p.mc_version && p.mc_version !== '未知') g.allVersions.add(p.mc_version);
            if (p.all_versions && Array.isArray(p.all_versions)) {
                p.all_versions.forEach(function(v) { if (v && v !== '未知') g.allVersions.add(v); });
            }
            if (p.loaders && Array.isArray(p.loaders)) {
                p.loaders.forEach(function(l) { g.allLoaders.add(l); });
            }
            if (p.categories && Array.isArray(p.categories)) {
                p.categories.forEach(function(c) { g.allCategories.add(c); });
            }
            if (p.download_links && Array.isArray(p.download_links)) {
                p.download_links.forEach(function(l) { g.allLinks.push(l); });
            }
            if (p.qq_group) g.allGroups.add(p.qq_group);

            g.totalViews += (p.views || 0);
            g.totalLikes += (p.likes || 0);
            g.totalCoins += (p.coins || 0);
            g.totalFavs += (p.favorites || 0);
            g.totalShare += (p.share || 0);
            g.totalReply += (p.reply || 0);
            g.totalDanmaku += (p.danmaku || 0);
        });

        groups.forEach(function(g) {
            g.items.sort(function(a, b) {
                return (b.pub_timestamp || 0) - (a.pub_timestamp || 0);
            });
            var clean = cleanPackKey(g.displayTitle);
            if (clean.length >= 2) {
                var words = clean.split(' ');
                g.cleanDisplayName = words.slice(0, 3).join(' ').toUpperCase();
            } else {
                g.cleanDisplayName = g.displayTitle;
            }
        });

        return groups;
    }

    /* 渲染整个 B站 面板 */
    function renderBiliView() {
        var q = ($('#biliSearchInput').val() || '').trim().toLowerCase();
        var ver = $('#biliVerSelect').val() || '';
        var loader = $('#biliLoaderSelect').val() || '';
        var sort = $('#biliSortSelect').val() || 'pubdate_desc';

        var nowSec = Math.floor(Date.now() / 1000);
        var refSec = nowSec;
        if (activeDate) {
            var latestSec = 0;
            biliPacks.forEach(function(item) { if ((item.pub_timestamp || 0) > latestSec) latestSec = item.pub_timestamp; });
            refSec = Math.max(nowSec, latestSec);
        }

        // 过滤
        var filtered = biliPacks.filter(function(p) {
            if (q) {
                var searchTarget = ((p.title || '') + ' ' + (p.author || '') + ' ' + (p.desc || '') + ' ' + (p.mc_version || '') + ' ' + (p.loaders || []).join(' ') + ' ' + (p.categories || []).join(' ')).toLowerCase();
                if (searchTarget.indexOf(q) === -1) return false;
            }
            if (ver && (p.mc_version || '').indexOf(ver) === -1 && !(p.all_versions || []).includes(ver)) return false;
            if (loader && !(p.loaders || []).includes(loader)) return false;
            if (!catHitMulti(activeCat, p.categories, __catExclude.bilibili)) return false;
            if (activePan) {
                var links = p.download_links || [];
                var hasPan = links.some(function(l) {
                    var n = (l && (l.name || l.type || '')) || '';
                    return n.indexOf(activePan) !== -1;
                });
                if (!hasPan) return false;
            }
            if (activeDate) {
                if (activeDate === '7d') {
                    if (!p.pub_timestamp || (refSec - p.pub_timestamp > 7 * 86400)) return false;
                } else if (activeDate === '30d') {
                    if (!p.pub_timestamp || (refSec - p.pub_timestamp > 30 * 86400)) return false;
                } else if (activeDate === '90d') {
                    if (!p.pub_timestamp || (refSec - p.pub_timestamp > 90 * 86400)) return false;
                } else if (/^\d\d\d\d$/.test(activeDate)) {
                    if (!p.pub_time || p.pub_time.indexOf(activeDate) !== 0) return false;
                } else {
                    if (!p.pub_time || p.pub_time.indexOf(activeDate) !== 0) return false;
                }
            }
            return true;
        });

        // 更新活动过滤项标签条
        updateActiveFiltersBar(q, ver, loader);

        // 排序与渲染
        var $grid = $('#biliCardsGrid');
        $grid.empty();

        if (activeGroupMode === 'grouped') {
            var groups = groupPacks(filtered);

            groups.sort(function(a, b) {
                if (sort === 'views_desc') return (b.totalViews || 0) - (a.totalViews || 0);
                if (sort === 'likes_desc') return (b.totalLikes || 0) - (a.totalLikes || 0);
                if (sort === 'favs_desc') return (b.totalFavs || 0) - (a.totalFavs || 0);
                if (sort === 'coins_desc') return (b.totalCoins || 0) - (a.totalCoins || 0);
                if (sort === 'share_desc') return (b.totalShare || 0) - (a.totalShare || 0);
                if (sort === 'reply_desc') return (b.totalReply || 0) - (a.totalReply || 0);
                if (sort === 'danmaku_desc') return (b.totalDanmaku || 0) - (a.totalDanmaku || 0);
                return (b.latestTimestamp || 0) - (a.latestTimestamp || 0);
            });

            $('#biliCurrentModeText').text('当前模式: ✨ 同名整合包智能聚合 (共 ' + groups.length + ' 款独立整合包)');

            if (groups.length === 0) {
                $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted); font-size:1.1rem;">🔍 没有找到符合条件的整合包</div>');
                $('#biliPaginationWrap').hide();
                return;
            }

            var displayGroups = groups.slice(0, currentBiliCardLimit);
            var htmlArr = [];
            displayGroups.forEach(function(g) {
                htmlArr.push(renderGroupedCard(g));
            });
            $grid.html(htmlArr.join(''));

            var remaining = groups.length - displayGroups.length;
            if (remaining > 0) {
                $('#biliPaginationWrap').show();
                $('#biliRemainingCount').text(Math.min(remaining, 48));
                $('#biliTotalFilteredCount').text(groups.length);
            } else {
                $('#biliPaginationWrap').hide();
            }
        } else {
            filtered.sort(function(a, b) {
                if (sort === 'views_desc') return (b.views || 0) - (a.views || 0);
                if (sort === 'likes_desc') return (b.likes || 0) - (a.likes || 0);
                if (sort === 'favs_desc') return (b.favorites || 0) - (a.favorites || 0);
                if (sort === 'coins_desc') return (b.coins || 0) - (a.coins || 0);
                if (sort === 'share_desc') return (b.share || 0) - (a.share || 0);
                if (sort === 'reply_desc') return (b.reply || 0) - (a.reply || 0);
                if (sort === 'danmaku_desc') return (b.danmaku || 0) - (a.danmaku || 0);
                return (b.pub_timestamp || 0) - (a.pub_timestamp || 0);
            });

            $('#biliCurrentModeText').text('当前模式: 📋 视频单条独立平铺 (共 ' + filtered.length + ' 条发布记录)');

            if (filtered.length === 0) {
                $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted); font-size:1.1rem;">🔍 没有找到符合条件的视频</div>');
                $('#biliPaginationWrap').hide();
                return;
            }

            var displayPacks = filtered.slice(0, currentBiliCardLimit);
            var htmlArr = [];
            displayPacks.forEach(function(p) {
                htmlArr.push(renderFlatCard(p));
            });
            $grid.html(htmlArr.join(''));

            var remaining = filtered.length - displayPacks.length;
            if (remaining > 0) {
                $('#biliPaginationWrap').show();
                $('#biliRemainingCount').text(Math.min(remaining, 48));
                $('#biliTotalFilteredCount').text(filtered.length);
            } else {
                $('#biliPaginationWrap').hide();
            }
        }
    }

    /* 动态更新活动筛选标签条 */
    function updateActiveFiltersBar(q, ver, loader) {
        var $bar = $('#biliActiveFilters');
        var $list = $('#biliActiveFiltersList');
        $list.empty();
        var hasFilters = false;

        if (q) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="search">🔍 关键词: ' + q + '<span class="active-pill-remove">✕</span></span>');
        }
        if (ver) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="ver">🎮 MC: ' + ver + '<span class="active-pill-remove">✕</span></span>');
        }
        if (loader) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="loader">⚙️ 加载器: ' + loader + '<span class="active-pill-remove">✕</span></span>');
        }
        if (activeDate) {
            hasFilters = true;
            var dateText = activeDate;
            if (activeDate === '7d') dateText = '近 7 天';
            else if (activeDate === '30d') dateText = '近 30 天';
            else if (activeDate === '90d') dateText = '近 90 天';
            else if (/^\d\d\d\d$/.test(activeDate)) dateText = activeDate + ' 年';
            else if (activeDate === '2026-09') dateText = '9月 (当月)';
            else if (activeDate === '2026-08') dateText = '8月 (暑期)';
            $list.append('<span class="active-pill" data-clear="date">📅 时间: ' + dateText + '<span class="active-pill-remove">✕</span></span>');
        }
        if (activeCat.length) {
            hasFilters = true;
            activeCat.forEach(function(oneCat) {
                $list.append('<span class="active-pill" data-clear="cat" data-val="' + escHtml(oneCat, true) + '">🏷️ 分类: ' + escHtml(catLabel(oneCat), true) + '<span class="active-pill-remove">✕</span></span>');
            });
        }
        if (activePan) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="pan">💾 网盘: ' + activePan + '<span class="active-pill-remove">✕</span></span>');
        }

        if (hasFilters) {
            $bar.show();
        } else {
            $bar.hide();
        }
    }

    /* 渲染同包聚合卡片 */
    function renderGroupedCard(g) {
        var latest = g.items[0];
        var isMulti = g.items.length > 1;

        var vers = Array.from(g.allVersions);
        var loaders = Array.from(g.allLoaders);
        var cats = Array.from(g.allCategories);
        var groups = Array.from(g.allGroups);

        var tagsHtml = '';
        vers.forEach(function(v) { tagsHtml += '<span class="bili-tag-mc">🎮 ' + v + '</span>'; });
        loaders.forEach(function(l) { tagsHtml += '<span class="bili-tag-loader">' + l + '</span>'; });
        cats.forEach(function(c) { tagsHtml += '<span class="bili-tag-cat">' + c + '</span>'; });

        var viewsStr = g.totalViews > 10000 ? (g.totalViews / 10000).toFixed(1) + '万' : g.totalViews;
        var likesStr = g.totalLikes > 10000 ? (g.totalLikes / 10000).toFixed(1) + '万' : g.totalLikes;
        var coinsStr = g.totalCoins > 10000 ? (g.totalCoins / 10000).toFixed(1) + '万' : g.totalCoins;
        var favsStr = g.totalFavs > 10000 ? (g.totalFavs / 10000).toFixed(1) + '万' : g.totalFavs;
        var danmakuStr = g.totalDanmaku > 10000 ? (g.totalDanmaku / 10000).toFixed(1) + '万' : g.totalDanmaku;
        var replyStr = g.totalReply > 10000 ? (g.totalReply / 10000).toFixed(1) + '万' : g.totalReply;
        var shareStr = g.totalShare > 10000 ? (g.totalShare / 10000).toFixed(1) + '万' : (g.totalShare || 0);

        var coverImg = g.pic ? (g.pic.replace('http://', 'https://') + '@480w_300h_1c.webp') : '';

        var dlZoneHtml = '<div class="bili-dl-zone">';
        var dlMap = {};
        g.allLinks.forEach(function(l) {
            if (l && l.url && !dlMap[l.url]) {
                dlMap[l.url] = true;
                var panName = (l.name || l.type || '网盘下载').trim();
                var panClass = 'pan-btn-' + (panName.indexOf('百度') !== -1 ? 'baidu' : (panName.indexOf('夸克') !== -1 ? 'quark' : (panName.indexOf('蓝奏') !== -1 ? 'lanzou' : (panName.indexOf('123') !== -1 ? 'pan123' : 'other'))));
                dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + panClass + '">💾 ' + panName + ' ↗</a>';
            }
        });

        if (latest.extract_code) {
            dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-code js-copy-btn" data-text="' + latest.extract_code + '" title="点击复制提取码">🔑 码: ' + latest.extract_code + '</button>';
        }

        groups.forEach(function(grp) {
            dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-group js-copy-btn" data-text="' + grp + '" title="点击复制群号">👥 群: ' + grp + '</button>';
        });

        var fullDesc = latest.desc || '';
        var pinned = latest.pinned_comment || '';
        if (fullDesc || pinned) {
            var combined = (fullDesc ? '【简介】\n' + fullDesc : '') + (pinned ? '\n\n【置顶评论】\n' + pinned : '');
            var safeCombined = $('<div>').text(combined).html();
            dlZoneHtml += '<details class="bili-desc-collapse"><summary class="bili-desc-summary">📄 最新版本介绍与置顶评论</summary><div class="bili-desc-full">' + safeCombined + '</div></details>';
        }

        if (latest.subtitle_text || latest.subtitle_summary) {
            var subText = latest.subtitle_text || latest.subtitle_summary;
            var safeSub = $('<div>').text(subText).html();
            dlZoneHtml += '<details class="bili-desc-collapse" style="margin-top:6px;"><summary class="bili-desc-summary" style="color:var(--primary); font-weight:700;">📝 视频字幕与口播速读 (AI/官方)</summary><div class="bili-desc-full" style="max-height:160px; overflow-y:auto; line-height:1.6; font-size:12px;">' + safeSub + '</div></details>';
        }

        dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-other js-open-bili-group-versions" data-group-key="' + g.key + '" style="font-size:0.75rem; background:rgba(251,114,153,0.12); color:#fb7299; border-color:rgba(251,114,153,0.3); margin-top:4px;" title="打开版本详情模态窗">📜 历史发布记录 (' + g.items.length + ') ▾</button>';
        dlZoneHtml += '</div>';

        // 历史版本时间线列表
        var versionsHtml = '';
        if (isMulti) {
            versionsHtml += '<details class="bili-versions-collapse"><summary class="bili-versions-summary">📜 查看该整合包历史 ' + g.items.length + ' 个迭代版本与关联视频</summary><div class="bili-versions-list">';
            g.items.forEach(function(item, idx) {
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
            });
            versionsHtml += '</div></details>';
        }

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
    }

    /* 渲染单条平铺卡片 */
    function renderFlatCard(p) {
        var tagsHtml = '';
        if (p.mc_version && p.mc_version !== '未知') tagsHtml += '<span class="bili-tag-mc">🎮 ' + p.mc_version + '</span>';
        if (p.loaders && Array.isArray(p.loaders)) {
            p.loaders.forEach(function(l) { tagsHtml += '<span class="bili-tag-loader">' + l + '</span>'; });
        }
        if (p.categories && Array.isArray(p.categories)) {
            p.categories.forEach(function(c) { tagsHtml += '<span class="bili-tag-cat">' + c + '</span>'; });
        }

        var viewsStr = p.views > 10000 ? (p.views / 10000).toFixed(1) + '万' : p.views;
        var danmakuStr = (p.danmaku || 0) > 10000 ? ((p.danmaku || 0) / 10000).toFixed(1) + '万' : (p.danmaku || 0);
        var likesStr = p.likes > 10000 ? (p.likes / 10000).toFixed(1) + '万' : p.likes;
        var coinsStr = p.coins > 10000 ? (p.coins / 10000).toFixed(1) + '万' : (p.coins || 0);
        var favsStr = (p.favorites || 0) > 10000 ? ((p.favorites || 0) / 10000).toFixed(1) + '万' : (p.favorites || 0);
        var replyStr = p.reply > 10000 ? (p.reply / 10000).toFixed(1) + '万' : (p.reply || 0);
        var shareStr = (p.share || 0) > 10000 ? ((p.share || 0) / 10000).toFixed(1) + '万' : (p.share || 0);

        var coverImg = p.pic ? (p.pic.replace('http://', 'https://') + '@480w_300h_1c.webp') : '';

        var dlZoneHtml = '<div class="bili-dl-zone">';
        if (p.download_links && p.download_links.length > 0) {
            p.download_links.forEach(function(l) {
                if (l && l.url) {
                    var panName = (l.name || l.type || '网盘下载').trim();
                    var panClass = 'pan-btn-' + (panName.indexOf('百度') !== -1 ? 'baidu' : (panName.indexOf('夸克') !== -1 ? 'quark' : (panName.indexOf('蓝奏') !== -1 ? 'lanzou' : (panName.indexOf('123') !== -1 ? 'pan123' : 'other'))));
                    dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + panClass + '">💾 ' + panName + ' ↗</a>';
                }
            });
        }
        if (p.extract_code) {
            dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-code js-copy-btn" data-text="' + p.extract_code + '" title="点击复制提取码">🔑 码: ' + p.extract_code + '</button>';
        }
        if (p.qq_group) {
            dlZoneHtml += '<button type="button" class="bili-pan-btn pan-btn-group js-copy-btn" data-text="' + p.qq_group + '" title="点击复制群号">👥 群: ' + p.qq_group + '</button>';
        }

        var fullDesc = p.desc || '';
        var pinned = p.pinned_comment || '';
        if (fullDesc || pinned) {
            var combined = (fullDesc ? '【简介】\n' + fullDesc : '') + (pinned ? '\n\n【置顶评论】\n' + pinned : '');
            var safeCombined = $('<div>').text(combined).html();
            dlZoneHtml += '<details class="bili-desc-collapse"><summary class="bili-desc-summary">📄 详细介绍与置顶评论</summary><div class="bili-desc-full">' + safeCombined + '</div></details>';
        }

        if (p.subtitle_text || p.subtitle_summary) {
            var subText = p.subtitle_text || p.subtitle_summary;
            var safeSub = $('<div>').text(subText).html();
            dlZoneHtml += '<details class="bili-desc-collapse" style="margin-top:6px;"><summary class="bili-desc-summary" style="color:var(--primary); font-weight:700;">📝 视频字幕与口播速读 (AI/官方)</summary><div class="bili-desc-full" style="max-height:160px; overflow-y:auto; line-height:1.6; font-size:12px;">' + safeSub + '</div></details>';
        }

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
    }

    /* ═══════════ BBSMC 平台视图渲染与筛选逻辑 ═══════════ */
    function renderBbsmcView() {
        var q = ($('#bbsmcSearchInput').val() || '').trim().toLowerCase();
        var ver = $('#bbsmcVerSelect').val() || '';
        var loader = $('#bbsmcLoaderSelect').val() || '';
        var sort = $('#bbsmcSortSelect').val() || 'downloads_desc';

        var filtered = bbsmcPacks.filter(function(p) {
            if (q) {
                var sTarget = ((p.title || '') + ' ' + (p.author || '') + ' ' + (p.description || '') + ' ' + (p.mc_version || '') + ' ' + (p.loaders || []).join(' ') + ' ' + (p.categories || []).join(' ')).toLowerCase();
                if (sTarget.indexOf(q) === -1) return false;
            }
            if (ver && (p.mc_version || '').indexOf(ver) === -1 && !(p.all_versions || []).includes(ver)) return false;
            if (loader && !(p.loaders || []).includes(loader)) return false;
            if (!catHitMulti(bbsmcActiveCat, p.categories, __catExclude.bbsmc)) return false;
            if (bbsmcActivePan) {
                var links = p.download_links || [];
                var panKey = bbsmcActivePan.toLowerCase();
                var hasPan = links.some(function(l) {
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
                });
                if (!hasPan) return false;
            }
            return true;
        });

        updateBbsmcActiveFiltersBar(q, ver, loader);

        filtered.sort(function(a, b) {
            if (sort === 'downloads_desc') return (b.downloads || 0) - (a.downloads || 0);
            if (sort === 'followers_desc') return (b.followers || 0) - (a.followers || 0);
            if (sort === 'modified_desc') return (b.modified_timestamp || 0) - (a.modified_timestamp || 0);
            if (sort === 'created_desc') return (b.created_timestamp || 0) - (a.created_timestamp || 0);
            if (sort === 'title_asc') return (a.title || '').localeCompare(b.title || '');
            return (b.downloads || 0) - (a.downloads || 0);
        });

        $('#bbsmcMatchInfo').text('共找到 ' + filtered.length.toLocaleString() + ' 款整合包');

        var $grid = $('#bbsmcCardsGrid');
        $grid.empty();

        if (filtered.length === 0) {
            $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted); font-size:1.1rem;">🔍 没有找到符合条件的 BBSMC 整合包</div>');
            $('#bbsmcPaginationWrap').hide();
            return;
        }

        var displayPacks = filtered.slice(0, currentBbsmcCardLimit);
        var htmlArr = [];
        displayPacks.forEach(function(p) {
            htmlArr.push(renderBbsmcCard(p));
        });
        $grid.html(htmlArr.join(''));

        var remaining = filtered.length - displayPacks.length;
        if (remaining > 0) {
            $('#bbsmcPaginationWrap').show();
            $('#bbsmcRemainingCount').text(Math.min(remaining, 48));
            $('#bbsmcTotalFilteredCount').text(filtered.length.toLocaleString());
        } else {
            $('#bbsmcPaginationWrap').hide();
        }
    }

    function updateBbsmcActiveFiltersBar(q, ver, loader) {
        var $bar = $('#bbsmcActiveFilters');
        var $list = $('#bbsmcActiveFiltersList');
        $list.empty();
        var hasFilters = false;

        if (q) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="search">🔍 关键词: ' + q + '<span class="active-pill-remove">✕</span></span>');
        }
        if (ver) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="ver">🎮 MC: ' + ver + '<span class="active-pill-remove">✕</span></span>');
        }
        if (loader) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="loader">⚙️ 加载器: ' + loader + '<span class="active-pill-remove">✕</span></span>');
        }
        if (bbsmcActiveCat.length) {
            hasFilters = true;
            bbsmcActiveCat.forEach(function(oneCat) {
                $list.append('<span class="active-pill" data-clear="cat" data-val="' + escHtml(oneCat, true) + '">🏷️ 分类: ' + escHtml(catLabel(oneCat), true) + '<span class="active-pill-remove">✕</span></span>');
            });
        }
        if (bbsmcActivePan) {
            hasFilters = true;
            var panLabel = bbsmcActivePan;
            if (bbsmcActivePan === 'modrinth') panLabel = '官方直链';
            else if (bbsmcActivePan === 'curseforge') panLabel = 'CurseForge';
            $list.append('<span class="active-pill" data-clear="pan">💾 渠道: ' + panLabel + '<span class="active-pill-remove">✕</span></span>');
        }

        if (hasFilters) {
            $bar.show();
        } else {
            $bar.hide();
        }
    }

    function renderBbsmcCard(p) {
        registerPackForModal(p);
        var safeTitle = $('<div>').text(p.title || '').html();
        var safeAuthor = $('<div>').text(p.author || '未知').html();
        var safeDesc = $('<div>').text(p.description || '').html();
        var coverImg = p.featured_gallery || (p.gallery && p.gallery[0]) || p.icon_url || window.BBSMC_COVER_FALLBACK;
        var dlStr = p.downloads > 10000 ? (p.downloads / 10000).toFixed(1) + '万' : (p.downloads || 0);
        var flStr = p.followers > 10000 ? (p.followers / 10000).toFixed(1) + '万' : (p.followers || 0);

        var tagsHtml = '';
        if (p.mc_version && p.mc_version !== '未知') {
            tagsHtml += '<span class="bbsmc-badge-ver">🎮 ' + p.mc_version + '</span>';
        }
        if (p.loaders && Array.isArray(p.loaders)) {
            p.loaders.forEach(function(l) { tagsHtml += '<span class="bbsmc-badge-loader">' + loaderLabel(l) + '</span>'; });
        }
        if (p.categories && Array.isArray(p.categories)) {
            p.categories.forEach(function(c) { tagsHtml += '<span class="bbsmc-badge-cat">' + c + '</span>'; });
        }

        var galleryHtml = '';
        if (p.gallery && p.gallery.length > 0) {
            galleryHtml += '<div class="bbsmc-gallery-strip">';
            var limitG = Math.min(p.gallery.length, 6);
            for (var gi = 0; gi < limitG; gi++) {
                var gUrl = p.gallery[gi];
                galleryHtml += '<img src="' + gUrl + '" class="bbsmc-gallery-thumb js-bbsmc-lightbox-thumb" data-full="' + gUrl + '" data-title="' + $('<div>').text(p.title || '').html() + ' 实机截图" alt="截图" loading="lazy" referrerpolicy="no-referrer">';
            }
            galleryHtml += '</div>';
        }

        var dlZoneHtml = '<div class="bbsmc-download-zone">';
        var links = p.download_links || [];
        var visibleLinks = links.slice(0, 4);
        var hiddenLinks = links.slice(4);

        visibleLinks.forEach(function(l) {
            if (l && l.url) {
                var lName = (l.name || '直接下载').trim();
                var u = l.url.toLowerCase();
                var lClass = 'pan-btn-other';
                if (lName.indexOf('modrinth') !== -1 || u.indexOf('.mrpack') !== -1 || u.indexOf('cdn.bbsmc.net') !== -1) {
                    lClass = 'pan-btn-modrinth';
                } else if (u.indexOf('curseforge.com') !== -1) {
                    lClass = 'pan-btn-curseforge';
                } else if (lName.indexOf('夸克') !== -1 || u.indexOf('pan.quark.cn') !== -1) {
                    lClass = 'pan-btn-quark';
                } else if (lName.indexOf('百度') !== -1 || u.indexOf('pan.baidu.com') !== -1) {
                    lClass = 'pan-btn-baidu';
                } else if (lName.indexOf('123') !== -1 || u.indexOf('123pan') !== -1) {
                    lClass = 'pan-btn-pan123';
                } else if (lName.indexOf('迅雷') !== -1 || u.indexOf('pan.xunlei.com') !== -1) {
                    lClass = 'pan-btn-xunlei';
                }
                var vTag = l.version ? ' (' + l.version + ')' : '';
                dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" title="' + lName + vTag + '">💾 ' + lName + ' ↗</a>';
            }
        });

        if (hiddenLinks.length > 0) {
            dlZoneHtml += '<details class="bbsmc-more-links"><summary class="bbsmc-more-summary">展开更多历史下载 (' + hiddenLinks.length + ') ▾</summary><div class="bbsmc-more-body">';
            hiddenLinks.forEach(function(l) {
                if (l && l.url) {
                    var lName = (l.name || '直接下载').trim();
                    var vTag = l.version ? ' (' + l.version + ')' : '';
                    dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="font-size:0.75rem;" title="' + lName + vTag + '">💾 ' + lName + ' ↗</a>';
                }
            });
            dlZoneHtml += '</div></details>';
        }

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
    }

    /* ═══════════ XYEBBS 平台视图渲染与筛选逻辑 ═══════════ */
    function renderXyebbsView() {
        var q = ($('#xyebbsSearchInput').val() || '').trim().toLowerCase();
        var ver = $('#xyebbsVerSelect').val() || '';
        var loader = $('#xyebbsLoaderSelect').val() || '';
        var sort = $('#xyebbsSortSelect').val() || 'hot_desc';

        var filtered = xyebbsPacks.filter(function(p) {
            if (q) {
                var sTarget = ((p.title || '') + ' ' + (p.english_name || '') + ' ' + (p.author || '') + ' ' + (p.description || '') + ' ' + (p.mc_version || '') + ' ' + (p.loaders || []).join(' ') + ' ' + (p.categories || []).join(' ')).toLowerCase();
                if (sTarget.indexOf(q) === -1) return false;
            }
            if (ver && (p.mc_version || '').indexOf(ver) === -1 && !(p.all_versions || []).includes(ver)) return false;
            if (loader && !(p.loaders || []).includes(loader)) return false;
            if (!catHitMulti(xyebbsActiveCat, p.categories, __catExclude.xyebbs)) return false;
            if (xyebbsActivePan) {
                var links = p.download_links || [];
                var panKey = xyebbsActivePan.toLowerCase();
                if (panKey === 'official') {
                    if (!p.url) return false;
                } else {
                    var hasPan = links.some(function(l) {
                        var n = ((l && l.name) || '').toLowerCase();
                        var u = ((l && l.url) || '').toLowerCase();
                        var t = ((l && l.type) || '').toLowerCase();
                        if (panKey === '夸克') return n.indexOf('夸克') !== -1 || u.indexOf('pan.quark.cn') !== -1 || t === 'quark';
                        if (panKey === '百度') return n.indexOf('百度') !== -1 || u.indexOf('pan.baidu.com') !== -1 || t === 'baidu';
                        if (panKey === '123') return n.indexOf('123') !== -1 || u.indexOf('123pan') !== -1 || t.indexOf('123') !== -1;
                        if (panKey === '迅雷') return n.indexOf('迅雷') !== -1 || u.indexOf('pan.xunlei.com') !== -1 || t === 'xunlei';
                        if (panKey === '蓝奏') return n.indexOf('蓝奏') !== -1 || u.indexOf('lanzou') !== -1 || t.indexOf('lanzou') !== -1;
                        return n.indexOf(panKey) !== -1 || u.indexOf(panKey) !== -1;
                    });
                    if (!hasPan) return false;
                }
            }
            return true;
        });

        updateXyebbsActiveFiltersBar(q, ver, loader);

        filtered.sort(function(a, b) {
            if (sort === 'hot_desc') {
                var hotA = (a.downloads || 0) + (a.views || 0) * 0.05 + (a.likes || 0) * 10 + (a.comments || 0) * 5;
                var hotB = (b.downloads || 0) + (b.views || 0) * 0.05 + (b.likes || 0) * 10 + (b.comments || 0) * 5;
                return hotB - hotA;
            }
            if (sort === 'downloads_desc') return (b.downloads || 0) - (a.downloads || 0);
            if (sort === 'views_desc') return (b.views || 0) - (a.views || 0);
            if (sort === 'modified_desc') return (b.modified_timestamp || 0) - (a.modified_timestamp || 0);
            if (sort === 'created_desc') return (b.created_timestamp || 0) - (a.created_timestamp || 0);
            if (sort === 'comments_desc') return (b.comments || 0) - (a.comments || 0);
            if (sort === 'title_asc') return (a.title || '').localeCompare(b.title || '');
            return (b.downloads || 0) - (a.downloads || 0);
        });

        $('#xyebbsMatchInfo').text('共找到 ' + filtered.length.toLocaleString() + ' 款整合包');

        var $grid = $('#xyebbsCardsGrid');
        $grid.empty();

        if (filtered.length === 0) {
            $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-secondary);"><div style="font-size:2.5rem; margin-bottom:0.75rem;">🍃</div>没有匹配的 XYEBBS 整合包，请尝试调整搜索词或重置筛选条件</div>');
            $('#xyebbsPaginationWrap').hide();
            return;
        }

        var displayPacks = filtered.slice(0, currentXyebbsCardLimit);
        var htmlArr = [];
        displayPacks.forEach(function(p) {
            htmlArr.push(renderXyebbsCard(p));
        });
        $grid.html(htmlArr.join(''));

        var remaining = filtered.length - displayPacks.length;
        if (remaining > 0) {
            $('#xyebbsPaginationWrap').show();
            $('#xyebbsRemainingCount').text(Math.min(remaining, 48));
            $('#xyebbsTotalFilteredCount').text(filtered.length.toLocaleString());
        } else {
            $('#xyebbsPaginationWrap').hide();
        }
    }

    function updateXyebbsActiveFiltersBar(q, ver, loader) {
        var $bar = $('#xyebbsActiveFilters');
        var $list = $('#xyebbsActiveFiltersList');
        $list.empty();
        var hasFilters = false;

        if (q) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="search">🔍 关键词: ' + q + '<span class="active-pill-remove">✕</span></span>');
        }
        if (ver) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="ver">🎮 MC: ' + ver + '<span class="active-pill-remove">✕</span></span>');
        }
        if (loader) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="loader">⚙️ 加载器: ' + loader + '<span class="active-pill-remove">✕</span></span>');
        }
        if (xyebbsActiveCat.length) {
            hasFilters = true;
            xyebbsActiveCat.forEach(function(oneCat) {
                $list.append('<span class="active-pill" data-clear="cat" data-val="' + escHtml(oneCat, true) + '">🏷️ 分类: ' + escHtml(catLabel(oneCat), true) + '<span class="active-pill-remove">✕</span></span>');
            });
        }
        if (xyebbsActivePan) {
            hasFilters = true;
            var panLabel = xyebbsActivePan === 'official' ? '官方发布页' : xyebbsActivePan;
            $list.append('<span class="active-pill" data-clear="pan">💾 渠道: ' + panLabel + '<span class="active-pill-remove">✕</span></span>');
        }

        if (hasFilters) {
            $bar.show();
        } else {
            $bar.hide();
        }
    }

    function renderXyebbsCard(p) {
        registerPackForModal(p);
        var safeTitle = $('<div>').text(p.title || '').html();
        var safeAuthor = $('<div>').text(p.author || '未知').html();
        var safeDesc = $('<div>').text(p.description || '').html();
        var coverImg = p.head_url || p.icon_url || window.XYEBBS_COVER_FALLBACK || window.BBSMC_COVER_FALLBACK;
        var dlStr = p.downloads > 10000 ? (p.downloads / 10000).toFixed(1) + '万' : (p.downloads || 0);
        var viewStr = p.views > 10000 ? (p.views / 10000).toFixed(1) + '万' : (p.views || 0);

        var tagsHtml = '';
        if (p.mc_version && p.mc_version !== '未知') {
            tagsHtml += '<span class="xyebbs-badge-ver">🎮 ' + p.mc_version + '</span>';
        }
        if (p.loaders && Array.isArray(p.loaders)) {
            p.loaders.forEach(function(l) { tagsHtml += '<span class="xyebbs-badge-loader">' + loaderLabel(l) + '</span>'; });
        }
        if (p.categories && Array.isArray(p.categories)) {
            p.categories.forEach(function(c) { tagsHtml += '<span class="xyebbs-badge-cat">' + c + '</span>'; });
        }

        var dlZoneHtml = '<div class="xyebbs-download-zone">';
        var links = p.download_links || [];
        var visibleLinks = links.slice(0, 4);
        var hiddenLinks = links.slice(4);

        visibleLinks.forEach(function(l) {
            if (l && l.url) {
                var lName = (l.name || '直接下载').trim();
                var u = (l.url || '').toLowerCase();
                var t = ((l && l.type) || '').toLowerCase();
                var lClass = 'pan-btn-other';
                if (lName.indexOf('夸克') !== -1 || u.indexOf('pan.quark.cn') !== -1 || t === 'quark') {
                    lClass = 'pan-btn-quark';
                } else if (lName.indexOf('百度') !== -1 || u.indexOf('pan.baidu.com') !== -1 || t === 'baidu') {
                    lClass = 'pan-btn-baidu';
                } else if (lName.indexOf('123') !== -1 || u.indexOf('123pan') !== -1 || t.indexOf('123') !== -1) {
                    lClass = 'pan-btn-pan123';
                } else if (lName.indexOf('迅雷') !== -1 || u.indexOf('pan.xunlei.com') !== -1 || t === 'xunlei') {
                    lClass = 'pan-btn-xunlei';
                } else if (lName.indexOf('蓝奏') !== -1 || u.indexOf('lanzou') !== -1 || t.indexOf('lanzou') !== -1) {
                    lClass = 'pan-btn-lanzou';
                }
                var vTag = l.label ? ' (' + l.label + ')' : (l.version ? ' (' + l.version + ')' : '');
                dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" title="' + lName + vTag + '">💾 ' + lName + ' ↗</a>';
            }
        });

        if (hiddenLinks.length > 0) {
            dlZoneHtml += '<details class="xyebbs-more-links"><summary class="xyebbs-more-summary">展开更多历史下载 (' + hiddenLinks.length + ') ▾</summary><div class="xyebbs-more-body">';
            hiddenLinks.forEach(function(l) {
                if (l && l.url) {
                    var lName = (l.name || '直接下载').trim();
                    var vTag = l.label ? ' (' + l.label + ')' : (l.version ? ' (' + l.version + ')' : '');
                    dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="font-size:0.75rem;" title="' + lName + vTag + '">💾 ' + lName + ' ↗</a>';
                }
            });
            dlZoneHtml += '</div></details>';
        }

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
    }

    /* ═══════════ Modrinth 平台视图渲染与筛选 ═══════════ */
    function renderModrinthView() {
        var q = ($('#modrinthSearchInput').val() || '').trim().toLowerCase();
        var ver = $('#modrinthVerSelect').val() || '';
        var loader = $('#modrinthLoaderSelect').val() || '';
        var sort = $('#modrinthSortSelect').val() || 'downloads_desc';

        var filtered = modrinthPacks.filter(function(p) {
            if (q) {
                var sTarget = ((p.title || '') + ' ' + (p.slug || '') + ' ' + (p.author || '') + ' ' + (p.description || '') + ' ' + (p.categories || []).join(' ')).toLowerCase();
                if (sTarget.indexOf(q) === -1) return false;
            }
            if (ver && (p.mc_version || '').indexOf(ver) === -1 && !(p.all_versions || []).includes(ver)) return false;
            if (loader && !(p.loaders || []).includes(loader)) return false;
            if (!catHitMulti(modrinthActiveCat, p.categories, __catExclude.modrinth)) return false;
            return true;
        });

        updateModrinthActiveFiltersBar(q, ver, loader);

        filtered.sort(function(a, b) {
            if (sort === 'downloads_desc') return (b.downloads || 0) - (a.downloads || 0);
            if (sort === 'follows_desc') return (b.followers || 0) - (a.followers || 0);
            if (sort === 'modified_desc') return (b.date_modified || '').localeCompare(a.date_modified || '');
            if (sort === 'title_asc') return (a.title || '').localeCompare(b.title || '');
            return (b.downloads || 0) - (a.downloads || 0);
        });

        $('#modrinthMatchInfo').text('共找到 ' + filtered.length.toLocaleString() + ' 款整合包');

        var $grid = $('#modrinthCardsGrid');
        $grid.empty();

        if (filtered.length === 0) {
            $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-secondary);"><div style="font-size:2.5rem; margin-bottom:0.75rem;">🌐</div>没有匹配的 Modrinth 整合包</div>');
            $('#modrinthPaginationWrap').hide();
            return;
        }

        var displayPacks = filtered.slice(0, currentModrinthCardLimit);
        var htmlArr = [];
        displayPacks.forEach(function(p) {
            htmlArr.push(renderModrinthCard(p));
        });
        $grid.html(htmlArr.join(''));

        var remaining = filtered.length - displayPacks.length;
        if (remaining > 0) {
            $('#modrinthPaginationWrap').show();
            $('#modrinthRemainingCount').text(Math.min(remaining, 48));
            $('#modrinthTotalFilteredCount').text(filtered.length.toLocaleString());
        } else {
            $('#modrinthPaginationWrap').hide();
        }
    }

    function updateModrinthActiveFiltersBar(q, ver, loader) {
        var $bar = $('#modrinthActiveFilters');
        var $list = $('#modrinthActiveFiltersList');
        $list.empty();
        var hasFilters = false;

        if (q) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="search">🔍 关键词: ' + q + '<span class="active-pill-remove">✕</span></span>');
        }
        if (ver) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="ver">🎮 MC: ' + ver + '<span class="active-pill-remove">✕</span></span>');
        }
        if (loader) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="loader">⚙️ 加载器: ' + loader + '<span class="active-pill-remove">✕</span></span>');
        }
        if (modrinthActiveCat.length) {
            hasFilters = true;
            modrinthActiveCat.forEach(function(oneCat) {
                $list.append('<span class="active-pill" data-clear="cat" data-val="' + escHtml(oneCat, true) + '">🏷️ 分类: ' + escHtml(catLabel(oneCat), true) + '<span class="active-pill-remove">✕</span></span>');
            });
        }

        if (hasFilters) {
            $bar.show();
        } else {
            $bar.hide();
        }
    }

    function renderModrinthCard(p) {
        registerPackForModal(p);
        var safeTitle = $('<div>').text(p.title || '').html();
        var safeAuthor = $('<div>').text(p.author || '未知').html();
        var safeDesc = $('<div>').text(p.description || '').html();
        var coverImg = p.icon_url || window.MODRINTH_COVER_FALLBACK;
        var dlStr = p.downloads > 10000 ? (p.downloads / 10000).toFixed(1) + '万' : (p.downloads || 0);
        var flStr = p.followers > 10000 ? (p.followers / 10000).toFixed(1) + '万' : (p.followers || 0);

        var tagsHtml = '';
        if (p.mc_version && p.mc_version !== '未知') {
            tagsHtml += '<span class="modrinth-badge-ver">🎮 ' + p.mc_version + '</span>';
        }
        if (p.loaders && Array.isArray(p.loaders)) {
            p.loaders.forEach(function(l) { tagsHtml += '<span class="modrinth-badge-loader">' + loaderLabel(l) + '</span>'; });
        }
        if (p.categories && Array.isArray(p.categories)) {
            p.categories.slice(0, 4).forEach(function(c) { tagsHtml += '<span class="modrinth-badge-cat" title="' + c + '">' + catLabel(c) + '</span>'; });
        }

        var dlZoneHtml = '<div class="xyebbs-download-zone">';
        var links = p.download_links || [];
        links.forEach(function(l) {
            if (l && l.url) {
                var lClass = l.type === 'APP_IMPORT' ? 'pan-btn-modrinth' : 'pan-btn-other';
                var icon = l.type === 'APP_IMPORT' ? '🚀' : '🌐';
                dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" style="font-size:0.8rem;" title="' + l.name + '">' + icon + ' ' + l.label + ' ↗</a>';
            }
        });
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
    }

    /* ═══════════ CurseForge 平台视图渲染与筛选 ═══════════ */
    function renderCurseforgeView() {
        var q = ($('#curseforgeSearchInput').val() || '').trim().toLowerCase();
        var ver = $('#curseforgeVerSelect').val() || '';
        var loader = $('#curseforgeLoaderSelect').val() || '';
        var sort = $('#curseforgeSortSelect').val() || 'downloads_desc';

        var filtered = curseforgePacks.filter(function(p) {
            if (q) {
                var sTarget = ((p.title || '') + ' ' + (p.slug || '') + ' ' + (p.author || '') + ' ' + (p.description || '') + ' ' + (p.categories || []).join(' ')).toLowerCase();
                if (sTarget.indexOf(q) === -1) return false;
            }
            if (ver && (p.mc_version || '').indexOf(ver) === -1 && !(p.all_versions || []).includes(ver)) return false;
            if (loader && !(p.loaders || []).includes(loader)) return false;
            if (!catHitMulti(curseforgeActiveCat, p.categories, __catExclude.curseforge)) return false;
            return true;
        });

        updateCurseforgeActiveFiltersBar(q, ver, loader);

        filtered.sort(function(a, b) {
            if (sort === 'downloads_desc') return (b.downloads || 0) - (a.downloads || 0);
            if (sort === 'followers_desc') return (b.followers || 0) - (a.followers || 0);
            if (sort === 'modified_desc') return (b.date_modified || '').localeCompare(a.date_modified || '');
            if (sort === 'title_asc') return (a.title || '').localeCompare(b.title || '');
            return (b.downloads || 0) - (a.downloads || 0);
        });

        $('#curseforgeMatchInfo').text('共找到 ' + filtered.length.toLocaleString() + ' 款整合包');

        var $grid = $('#curseforgeCardsGrid');
        $grid.empty();

        if (filtered.length === 0) {
            $grid.html('<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-secondary);"><div style="font-size:2.5rem; margin-bottom:0.75rem;">🔥</div>没有匹配的 CurseForge 整合包</div>');
            $('#curseforgePaginationWrap').hide();
            return;
        }

        var displayPacks = filtered.slice(0, currentCurseforgeCardLimit);
        var htmlArr = [];
        displayPacks.forEach(function(p) {
            htmlArr.push(renderCurseforgeCard(p));
        });
        $grid.html(htmlArr.join(''));

        var remaining = filtered.length - displayPacks.length;
        if (remaining > 0) {
            $('#curseforgePaginationWrap').show();
            $('#curseforgeRemainingCount').text(Math.min(remaining, 48));
            $('#curseforgeTotalFilteredCount').text(filtered.length.toLocaleString());
        } else {
            $('#curseforgePaginationWrap').hide();
        }
    }

    function updateCurseforgeActiveFiltersBar(q, ver, loader) {
        var $bar = $('#curseforgeActiveFilters');
        var $list = $('#curseforgeActiveFiltersList');
        $list.empty();
        var hasFilters = false;

        if (q) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="search">🔍 关键词: ' + q + '<span class="active-pill-remove">✕</span></span>');
        }
        if (ver) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="ver">🎮 MC: ' + ver + '<span class="active-pill-remove">✕</span></span>');
        }
        if (loader) {
            hasFilters = true;
            $list.append('<span class="active-pill" data-clear="loader">⚙️ 加载器: ' + loader + '<span class="active-pill-remove">✕</span></span>');
        }
        if (curseforgeActiveCat.length) {
            hasFilters = true;
            curseforgeActiveCat.forEach(function(oneCat) {
                $list.append('<span class="active-pill" data-clear="cat" data-val="' + escHtml(oneCat, true) + '">🏷️ 分类: ' + escHtml(catLabel(oneCat), true) + '<span class="active-pill-remove">✕</span></span>');
            });
        }

        if (hasFilters) {
            $bar.show();
        } else {
            $bar.hide();
        }
    }

    function renderCurseforgeCard(p) {
        registerPackForModal(p);
        var safeTitle = $('<div>').text(p.title || '').html();
        var safeAuthor = $('<div>').text(p.author || '未知').html();
        var safeDesc = $('<div>').text(p.description || '').html();
        var coverImg = p.icon_url || window.CURSEFORGE_COVER_FALLBACK;
        var dlStr = p.downloads > 10000 ? (p.downloads / 10000).toFixed(1) + '万' : (p.downloads || 0);
        var flStr = p.followers > 10000 ? (p.followers / 10000).toFixed(1) + '万' : (p.followers || 0);

        var tagsHtml = '';
        if (p.mc_version && p.mc_version !== '未知') {
            tagsHtml += '<span class="curseforge-badge-ver">🎮 ' + p.mc_version + '</span>';
        }
        if (p.loaders && Array.isArray(p.loaders)) {
            p.loaders.forEach(function(l) { tagsHtml += '<span class="curseforge-badge-loader">' + loaderLabel(l) + '</span>'; });
        }
        if (p.categories && Array.isArray(p.categories)) {
            p.categories.slice(0, 4).forEach(function(c) { tagsHtml += '<span class="curseforge-badge-cat" title="' + c + '">' + catLabel(c) + '</span>'; });
        }

        var dlZoneHtml = '<div class="xyebbs-download-zone">';
        var links = p.download_links || [];
        links.forEach(function(l) {
            if (l && l.url) {
                var lClass = l.type === 'APP_IMPORT' ? 'pan-btn-curseforge' : 'pan-btn-other';
                var icon = l.type === 'APP_IMPORT' ? '🔥' : '🔗';
                dlZoneHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn ' + lClass + '" style="font-size:0.8rem;" title="' + l.name + '">' + icon + ' ' + l.label + ' ↗</a>';
            }
        });
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
    }


    // 展开/收起 核心标签
    $('#expandTags').on('click', function() {
        tagListExpanded = !tagListExpanded;
        $(this).text(tagListExpanded ? '收起 ↑' : '展开全部 ↓');
        $(this).attr('aria-expanded', String(tagListExpanded));
        renderTagChips();
    });

    // 展开/收起 热门模组
    $('#expandMods').on('click', function() {
        modListExpanded = !modListExpanded;
        $(this).text(modListExpanded ? '收起常用 ▴' : '常用模组(前60) ▾');
        $(this).attr('aria-expanded', String(modListExpanded));
        renderHotModChips();
    });

    // 全部标签 / 多选弹窗
    $('#allTags').on('click', function() {
        openPicker('tag', allTagsList, tagCountsMap, '全部玩法标签', 'TAG DISCOVERY', '同时满足所选标签 · 按收录整合包数量排序');
    });

    // 全部模组 / 搜索多选弹窗
    $('#allMods').on('click', function() {
        openPicker('mod', allModsList, modCountsMap, '全部收录模组（11,702 款）', 'MOD DISCOVERY', '筛选包含指定模组的整合包 · 按收录整合包数量排序');
    });

    // 关闭弹窗
    $('#closePickerModal').on('click', function() {
        var modalEl = $('#mcmodPickerModal')[0];
        if (modalEl && modalEl.close) modalEl.close();
        else $('#mcmodPickerModal').hide();
        syncAllFilterUI();
    });

    $('#mcmodPickerModal').on('click', function(e) {
        if (e.target === this) {
            var r = this.getBoundingClientRect();
            if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) {
                if (this.close) this.close();
                else $(this).hide();
                syncAllFilterUI();
            }
        }
    });

    // 已激活筛选胶囊点击移除
    $('#activeFilters').on('click', '.active-filter-badge', function() {
        var field = $(this).data('field');
        var val = $(this).data('val');
        if (field === 'cat') toggleMultiSelect('#categoryFilter', val);
        else if (field === 'tag') toggleMultiSelect('#packTagFilter', val);
        else if (field === 'modcat') toggleMultiSelect('#modCategoryFilter', val);
        else if (field === 'mod') toggleMultiSelect('#modFilter', val);
        else if (field === 'type') { $('#typeFilter').val('').trigger('change'); }
        else if (field === 'trend') { $('#trendFilter').val('').trigger('change'); }
        syncAllFilterUI();
    });

    $('#activeFilters').on('click', '#clearAllActiveFilters', function() {
        $('#sidebarResetFilters').click();
    });

    // 1. 官方专区 Chips 点击
    $('#mcmodCategoryChips').on('click', '.s-chip', function() {
        var cat = $(this).data('cat');
        if (!cat) {
            $('#categoryFilter').val(null).trigger('change');
        } else {
            toggleMultiSelect('#categoryFilter', cat);
        }
        syncAllFilterUI();
    });

    // 2. 核心标签 Chips 点击
    $('#mcmodTagChips').on('click', '.s-chip', function() {
        var tag = $(this).data('tag');
        if (!tag) {
            $('#packTagFilter').val(null).trigger('change');
        } else {
            toggleMultiSelect('#packTagFilter', tag);
        }
        syncAllFilterUI();
    });

    // 3. 模组分类 Chips 点击
    $('#mcmodModCatChips').on('click', '.s-chip', function() {
        var mcat = $(this).data('mod-cat');
        if (!mcat) {
            $('#modCategoryFilter').val(null).trigger('change');
        } else {
            toggleMultiSelect('#modCategoryFilter', mcat);
        }
        syncAllFilterUI();
    });

    // 4. 包含模组 Chips 点击
    $('#mcmodHotModChips').on('click', '.s-chip', function() {
        var mod = $(this).data('mod');
        if (!mod) {
            $('#modFilter').val(null).trigger('change');
        } else {
            toggleMultiSelect('#modFilter', mod);
        }
        syncAllFilterUI();
    });

    // B站 玩法分类 Chips 点击单选与联动
    // 多选（向 MCMod 看齐）：点「全部」清空；点分类在选中集合里切换；已选中的再点取消
    $('#biliCategoryChips').on('click', '.s-chip', function() {
        var cat = $(this).data('cat') || '';
        if (!cat) {
            activeCat = [];
        } else {
            var at = activeCat.indexOf(cat);
            if (at === -1) { activeCat.push(cat); } else { activeCat.splice(at, 1); }
        }
        $('#biliCategoryChips .s-chip').each(function() {
            var cv = $(this).data('cat') || '';
            $(this).toggleClass('active', cv ? activeCat.indexOf(cv) !== -1 : activeCat.length === 0);
        });
        renderBiliView();
    });

    // 侧边栏 B站 网盘类型 Chips 点击联动
    $('#biliPanChips').on('click', '.s-chip', function() {
        $('#biliPanChips .s-chip').removeClass('active');
        $(this).addClass('active');
        activePan = $(this).data('pan') || '';
        renderBiliView();
    });

    // 侧边栏 全平台分类 Chips 点击联合搜索
    $('#allCategoryChips').on('click', '.s-chip', function() {
        var cat = $(this).data('cat');
        $('#crossSearchInput').val(cat).trigger('input');
        if ($('.cross-search-section').length) {
            $('html, body').animate({ scrollTop: $('.cross-search-section').offset().top - 80 }, 300);
        }
    });

    // 侧边栏 MC百科 一键重置全部筛选
    $('#sidebarResetFilters').on('click', function() {
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
        if (window.table) {
            window.table.search('').draw();
        }
        syncAllFilterUI();
        renderMcmodCards();
    });

    // 侧边栏 B站 一键重置全部筛选
    $('#sidebarBiliReset').on('click', function() {
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
    });

    // 顶栏与侧边栏平台导航双向联动
    $(document).on('click', '.nav-item, .top-plat-btn', function() {
        var tab = $(this).data('tab');
        if (tab) switchPlatformTab(tab);
    });
    // MC百科卡片画廊分页加载更多与全部展开
    $(document).on('click', '.js-load-more-cards', function() {
        currentMcmodCardLimit += 48;
        renderMcmodCards();
    });
    $(document).on('click', '.js-load-all-cards', function() {
        currentMcmodCardLimit = 99999;
        renderMcmodCards();
    });

    // MC百科专属一体化搜索栏 (实时联动画廊卡片与专业数据表)
    var mcmodSearchTimer = null;
    $('#mcmodUnifiedSearch').on('input', function() {
        var val = $(this).val();
        if (val) {
            $('#mcmodSearchClear').show();
        } else {
            $('#mcmodSearchClear').hide();
        }
        clearTimeout(mcmodSearchTimer);
        mcmodSearchTimer = setTimeout(function() {
            currentMcmodCardLimit = 48;
            if (window.table) {
                window.table.search(val).draw();
            }
            renderMcmodCards();
        }, 150);
    });

    $('#mcmodSearchClear').on('click', function() {
        $('#mcmodUnifiedSearch').val('').trigger('input');
    });

    // MCMod 视图切换 (卡片 vs 表格)
    $('#mcmodViewToggle').on('click', '.vmode-btn', function() {
        $('#mcmodViewToggle .vmode-btn').removeClass('active');
        $(this).addClass('active');
        activeMcmodVMode = $(this).data('vmode');
        $('#crumbCurrentView').text(activeMcmodVMode === 'cards' ? '画廊卡片' : '专业多维表格');

        if (activeMcmodVMode === 'cards') {
            $('.table-card').hide();
            $('#mcmodCardsContainer').show();
            renderMcmodCards();
        } else {
            $('#mcmodCardsContainer').hide();
            $('.table-card').show();
            if (window.table) {
                window.table.columns.adjust();
            }
        }
    });

    // B站 聚合模式切换 (同包聚合 vs 视频平铺)
    $('#biliViewToggle, .bili-mode-toggle').on('click', '.vmode-btn, .bili-mode-btn', function() {
        var mode = $(this).data('bmode') || $(this).data('mode');
        if (!mode) return;
        $('#biliViewToggle .vmode-btn').removeClass('active');
        $('#biliViewToggle .vmode-btn[data-bmode="' + mode + '"]').addClass('active');
        $('.bili-mode-btn').removeClass('active');
        $('.bili-mode-btn[data-mode="' + mode + '"]').addClass('active');

        activeGroupMode = mode;
        $('#crumbCurrentView').text(activeGroupMode === 'grouped' ? '同包聚合' : '单条平铺');
        renderBiliView();
    });

    // B站 搜索与过滤事件 (含清除按钮与防抖)
    var biliSearchTimer = null;
    $('#biliSearchInput').on('input', function() {
        var val = $(this).val();
        if (val) {
            $('#biliSearchClear').show();
        } else {
            $('#biliSearchClear').hide();
        }
        clearTimeout(biliSearchTimer);
        biliSearchTimer = setTimeout(function() {
            renderBiliView();
        }, 150);
    });

    $('#biliSearchClear').on('click', function() {
        $('#biliSearchInput').val('').trigger('input');
    });

    $('#biliVerSelect, #biliLoaderSelect, #biliSortSelect').on('change', function() {
        currentBiliCardLimit = 48;
        renderBiliView();
    });

    // B站 加载更多与展开全部
    $(document).on('click', '.js-bili-load-more', function() {
        currentBiliCardLimit += 48;
        renderBiliView();
    });

    $(document).on('click', '.js-bili-load-all', function() {
        currentBiliCardLimit = 99999;
        renderBiliView();
    });

    // 快捷键 Ctrl+K 聚焦搜索
    $(document).on('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            if (currentTab === 'bilibili') {
                $('#biliSearchInput').focus();
            } else {
                $('#mcmodUnifiedSearch').focus();
            }
        }
    });

    // B站 日期 Chips 点击联动
    $('#biliDateChips').on('click', '.s-chip, .bili-chip', function() {
        $('#biliDateChips .s-chip, #biliDateChips .bili-chip').removeClass('active');
        $(this).addClass('active');
        activeDate = $(this).data('date') || '';
        renderBiliView();
    });

    // 活动标签清除事件
    $('#biliActiveFilters').on('click', '.active-pill', function() {
        var clearType = $(this).data('clear');
        if (clearType === 'search') {
            $('#biliSearchInput').val('').trigger('input');
        } else if (clearType === 'date') {
            $('#biliDateChips .s-chip[data-date=""]').click();
        } else if (clearType === 'cat') {
            var val = $(this).data('val');
            if (val) {
                var at = activeCat.indexOf(val);
                if (at !== -1) activeCat.splice(at, 1);
            } else {
                activeCat = [];
            }
            $('#biliCategoryChips .s-chip').each(function() {
                var cv = $(this).data('cat') || '';
                $(this).toggleClass('active', cv ? activeCat.indexOf(cv) !== -1 : activeCat.length === 0);
            });
            renderBiliView();
        } else if (clearType === 'pan') {
            $('#biliPanChips .s-chip[data-pan=""]').click();
        } else if (clearType === 'ver') {
            $('#biliVerSelect').val('').trigger('change');
        } else if (clearType === 'loader') {
            $('#biliLoaderSelect').val('').trigger('change');
        }
    });

    $('#biliClearFiltersBtn').on('click', function() {
        $('#sidebarBiliReset').click();
    });

    // 复制事件绑定
    $(document).on('click', '.js-copy-btn', function(e) {
        e.preventDefault();
        var text = $(this).data('text');
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                showToast('✅ 已复制: ' + text);
            });
        } else {
            var input = document.createElement('input');
            input.value = text;
            document.body.appendChild(input);
            input.select();
            document.execCommand('copy');
            document.body.removeChild(input);
            showToast('✅ 已复制: ' + text);
        }
    });

    // 移动端菜单开关
    $('#mobileMenuBtn').on('click', function() {
        $('#mainSidebar').toggleClass('open');
    });

    // 主题切换 (侧边栏 + 顶栏双向同步)
    $(document).on('click', '.theme-dot, .top-tdot', function() {
        var theme = $(this).data('theme');
        $('.theme-dot, .top-tdot').removeClass('active');
        $('.theme-dot[data-theme="' + theme + '"], .top-tdot[data-theme="' + theme + '"]').addClass('active');
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('mcmod-theme-v2', theme);
    });

    // 恢复保存的主题
    var savedTheme = localStorage.getItem('mcmod-theme-v2') || 'eye';
    $('.theme-dot[data-theme="' + savedTheme + '"], .top-tdot[data-theme="' + savedTheme + '"]').addClass('active');
    document.documentElement.setAttribute('data-theme', savedTheme);

    function showToast(msg) {
        var $t = $('#copyToast');
        $t.text(msg).addClass('show');
        setTimeout(function() { $t.removeClass('show'); }, 1800);
    }

    function initBiliStats() {
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
        var verSet = {};

        biliPacks.forEach(function(p) {
            totalViews += (p.views || 0);
            totalLinks += (p.download_links ? p.download_links.length : 0);
            if (p.qq_group) totalGroups++;
            if (p.mc_version && p.mc_version !== '未知') {
                verSet[p.mc_version] = (verSet[p.mc_version] || 0) + 1;
            }
            if (p.all_versions && Array.isArray(p.all_versions)) {
                p.all_versions.forEach(function(v) {
                    if (v && v !== '未知') verSet[v] = (verSet[v] || 0) + 1;
                });
            }
        });

        var viewsText = totalViews > 100000000 ? (totalViews / 100000000).toFixed(2) + '亿' :
                       (totalViews > 10000 ? (totalViews / 10000).toFixed(1) + '万' : totalViews);
        $('#biliStatViews').text(viewsText);
        $('#heroBiliViews').text(viewsText);
        $('#biliStatLinks').text(totalLinks + ' 个');
        $('#heroBiliLinks').text(totalLinks);
        $('#biliStatGroups').text(totalGroups + ' 个');
        $('#heroBiliGroups').text(totalGroups);

        // 填充版本下拉选项
        var sortedVers = Object.keys(verSet).sort(function(a, b) {
            return verSet[b] - verSet[a];
        });
        var $verSel = $('#biliVerSelect');
        sortedVers.forEach(function(v) {
            $verSel.append('<option value="' + v + '">' + v + ' (' + verSet[v] + ')</option>');
        });
        $verSel.trigger('change.select2');

        // 动态自适应填充发布时间 Chips（支持全量历史年限与近7/30/90天）
        initBiliDateChips();
    }

    function initBiliDateChips() {
        var $row = $('#biliDateChips');
        if (!$row.length) return;
        $row.empty();
        $row.append('<span class="s-chip active" data-date="">全部时间</span>');
        $row.append('<span class="s-chip" data-date="7d">近 7 天</span>');
        $row.append('<span class="s-chip" data-date="30d">近 30 天</span>');
        $row.append('<span class="s-chip" data-date="90d">近 90 天</span>');

        // 动态搜集并降序排列所有出现的年份
        var years = new Set();
        biliPacks.forEach(function(p) {
            if (p.pub_time && p.pub_time.length >= 4) {
                var y = p.pub_time.substring(0, 4);
                if (/^\d\d\d\d$/.test(y)) {
                    years.add(y);
                }
            }
        });
        var sortedYears = Array.from(years).sort().reverse();
        sortedYears.forEach(function(yr) {
            $row.append('<span class="s-chip" data-date="' + yr + '">' + yr + ' 年</span>');
        });
    }

    initBiliStats();

    /* ════════ BBSMC 平台统计与交互事件 ════════ */
    function initBbsmcStats() {
        if (!bbsmcPacks.length) return;
        var totalDl = 0;
        var totalFl = 0;
        var totalLinks = 0;
        var verSet = {};
        var catSet = {};

        bbsmcPacks.forEach(function(p) {
            totalDl += (p.downloads || 0);
            totalFl += (p.followers || 0);
            totalLinks += (p.download_links ? p.download_links.length : 0);
            if (p.mc_version && p.mc_version !== '未知') {
                verSet[p.mc_version] = (verSet[p.mc_version] || 0) + 1;
            }
            (p.categories || []).forEach(function(c) {
                if (c) catSet[c] = (catSet[c] || 0) + 1;
            });
        });

        var dlText = totalDl > 100000000 ? (totalDl / 100000000).toFixed(2) + '亿' :
                     (totalDl > 10000 ? (totalDl / 10000).toFixed(1) + '万' : totalDl);
        var flText = totalFl > 10000 ? (totalFl / 10000).toFixed(1) + '万' : totalFl;

        $('#bbsmcStatDownloads').text(dlText);
        $('#bbsmcStatFollowers').text(flText);
        $('#bbsmcStatLinks').text(totalLinks.toLocaleString() + ' 个');
        $('#bbsmcStatTotal').text((bbsmcPacks.length || 1802).toLocaleString() + ' 款');

        $('#topNavBbsmcBadge').text(bbsmcPacks.length.toLocaleString());

        // 填充 BBSMC 版本下拉选项
        var sortedVers = Object.keys(verSet).sort(function(a, b) { return verSet[b] - verSet[a]; });
        var $verSel = $('#bbsmcVerSelect');
        sortedVers.forEach(function(v) {
            $verSel.append('<option value="' + v + '">' + v + ' (' + verSet[v] + ')</option>');
        });
        $verSel.trigger('change.select2');

        // 填充 BBSMC 玩法专区 Chips
        var sortedCats = Object.keys(catSet).sort(function(a, b) { return catSet[b] - catSet[a]; });
        window.__bbsmcAllCats = sortedCats;
        window.__bbsmcCatCounts = catSet;
        window.__bbsmcCatsExpanded = false;
        renderBbsmcCatChips();
    }

    function renderBbsmcCatChips() {
        var $catChips = $('#bbsmcCategoryChips');
        $catChips.empty();
        $catChips.append('<span class="s-chip' + (bbsmcActiveCat.length === 0 ? ' active' : '') + '" data-cat="">全部玩法</span>');
        var maxVisible = window.__bbsmcCatsExpanded ? window.__bbsmcAllCats.length : 12;
        window.__bbsmcAllCats.forEach(function(c, idx) {
            var isSelected = bbsmcActiveCat.indexOf(c) !== -1;
            var isVisible = idx < maxVisible || isSelected;
            var count = window.__bbsmcCatCounts[c] || 0;
            $catChips.append('<span class="s-chip' + (isSelected ? ' active' : '') + '" data-cat="' + c + '" title="' + c + '" style="' + (isVisible ? '' : 'display:none;') + '">' + catLabel(c) + ' <span class="s-chip-count">' + count + '</span></span>');
        });
        if (window.__bbsmcAllCats.length > 12) {
            $('#bbsmcExpandCats').show().text(window.__bbsmcCatsExpanded ? '收起 ▴' : ('展开全部(' + window.__bbsmcAllCats.length + '项) ▾'));
        } else {
            $('#bbsmcExpandCats').hide();
        }
    }

    $('#bbsmcExpandCats').on('click', function() {
        window.__bbsmcCatsExpanded = !window.__bbsmcCatsExpanded;
        renderBbsmcCatChips();
    });

    initBbsmcStats();

    // BBSMC 搜索防抖
    var bbsmcSearchTimer = null;
    $('#bbsmcSearchInput').on('input', function() {
        var val = $(this).val();
        if (val) {
            $('#bbsmcSearchClear').show();
        } else {
            $('#bbsmcSearchClear').hide();
        }
        clearTimeout(bbsmcSearchTimer);
        bbsmcSearchTimer = setTimeout(function() {
            currentBbsmcCardLimit = 48;
            renderBbsmcView();
        }, 150);
    });

    $('#bbsmcSearchClear').on('click', function() {
        $('#bbsmcSearchInput').val('').trigger('input');
    });

    $('#bbsmcSortSelect, #bbsmcVerSelect, #bbsmcLoaderSelect').on('change', function() {
        currentBbsmcCardLimit = 48;
        renderBbsmcView();
    });

    // BBSMC 分类 Chips 点击单选与联动
    // 多选（向 MCMod 看齐）：点「全部」清空；点分类在选中集合里切换；已选中的再点取消
    $('#bbsmcCategoryChips').on('click', '.s-chip', function() {
        var cat = $(this).data('cat') || '';
        if (!cat) {
            bbsmcActiveCat = [];
        } else {
            var at = bbsmcActiveCat.indexOf(cat);
            if (at === -1) { bbsmcActiveCat.push(cat); } else { bbsmcActiveCat.splice(at, 1); }
        }
        renderBbsmcCatChips();
        currentBbsmcCardLimit = 48;
        renderBbsmcView();
    });

    // BBSMC 渠道 Chips 点击
    $('#bbsmcPanChips').on('click', '.s-chip', function() {
        $('#bbsmcPanChips .s-chip').removeClass('active');
        $(this).addClass('active');
        bbsmcActivePan = $(this).data('pan') || '';
        currentBbsmcCardLimit = 48;
        renderBbsmcView();
    });

    // BBSMC 活动过滤项清除
    $('#bbsmcActiveFilters').on('click', '.active-pill', function() {
        var clearType = $(this).data('clear');
        if (clearType === 'search') {
            $('#bbsmcSearchInput').val('').trigger('input');
        } else if (clearType === 'cat') {
            var val = $(this).data('val');
            if (val) {
                var at = bbsmcActiveCat.indexOf(val);
                if (at !== -1) bbsmcActiveCat.splice(at, 1);
            } else {
                bbsmcActiveCat = [];
            }
            renderBbsmcCatChips();
            currentBbsmcCardLimit = 48;
            renderBbsmcView();
        } else if (clearType === 'pan') {
            $('#bbsmcPanChips .s-chip[data-pan=""]').click();
        } else if (clearType === 'ver') {
            $('#bbsmcVerSelect').val('').trigger('change');
        } else if (clearType === 'loader') {
            $('#bbsmcLoaderSelect').val('').trigger('change');
        }
    });

    $('#bbsmcClearFiltersBtn, #bbsmcResetBtn').on('click', function() {
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
    });

    // BBSMC 加载更多与展开全部
    $(document).on('click', '.js-bbsmc-load-more', function() {
        currentBbsmcCardLimit += 48;
        renderBbsmcView();
    });

    $(document).on('click', '.js-bbsmc-load-all', function() {
        currentBbsmcCardLimit = 99999;
        renderBbsmcView();
    });

    // BBSMC 画廊缩略图点击打开灯箱
    $(document).on('click', '.js-bbsmc-lightbox-thumb', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var full = $(this).data('full') || $(this).attr('src');
        var title = $(this).data('title') || '游戏截图';
        openImageLightbox(full, title);
    });

    /* ════════ XYEBBS 平台统计与交互事件 ════════ */
    function initXyebbsStats() {
        if (!xyebbsPacks.length) return;
        var totalDl = 0;
        var totalViews = 0;
        var totalLinks = 0;
        var verSet = {};
        var catSet = {};

        xyebbsPacks.forEach(function(p) {
            totalDl += (p.downloads || 0);
            totalViews += (p.views || 0);
            totalLinks += (p.download_links ? p.download_links.length : 0);
            if (p.mc_version && p.mc_version !== '未知') {
                verSet[p.mc_version] = (verSet[p.mc_version] || 0) + 1;
            }
            (p.categories || []).forEach(function(c) {
                if (c) catSet[c] = (catSet[c] || 0) + 1;
            });
        });

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
        var sortedVers = Object.keys(verSet).sort(function(a, b) { return verSet[b] - verSet[a]; });
        var $verSel = $('#xyebbsVerSelect');
        sortedVers.forEach(function(v) {
            $verSel.append('<option value="' + v + '">' + v + ' (' + verSet[v] + ')</option>');
        });
        $verSel.trigger('change.select2');

        // 填充 XYEBBS 玩法专区 Chips
        var sortedCats = Object.keys(catSet).sort(function(a, b) { return catSet[b] - catSet[a]; });
        window.__xyebbsAllCats = sortedCats;
        window.__xyebbsCatCounts = catSet;
        window.__xyebbsCatsExpanded = false;
        renderXyebbsCatChips();
    }

    function renderXyebbsCatChips() {
        var $catChips = $('#xyebbsCategoryChips');
        $catChips.empty();
        $catChips.append('<span class="s-chip' + (xyebbsActiveCat.length === 0 ? ' active' : '') + '" data-cat="">全部玩法</span>');
        var maxVisible = window.__xyebbsCatsExpanded ? window.__xyebbsAllCats.length : 12;
        window.__xyebbsAllCats.forEach(function(c, idx) {
            var isSelected = xyebbsActiveCat.indexOf(c) !== -1;
            var isVisible = idx < maxVisible || isSelected;
            var count = window.__xyebbsCatCounts[c] || 0;
            $catChips.append('<span class="s-chip' + (isSelected ? ' active' : '') + '" data-cat="' + c + '" title="' + c + '" style="' + (isVisible ? '' : 'display:none;') + '">' + catLabel(c) + ' <span class="s-chip-count">' + count + '</span></span>');
        });
        if (window.__xyebbsAllCats.length > 12) {
            $('#xyebbsExpandCats').show().text(window.__xyebbsCatsExpanded ? '收起 ▴' : ('展开全部(' + window.__xyebbsAllCats.length + '项) ▾'));
        } else {
            $('#xyebbsExpandCats').hide();
        }
    }

    $('#xyebbsExpandCats').on('click', function() {
        window.__xyebbsCatsExpanded = !window.__xyebbsCatsExpanded;
        renderXyebbsCatChips();
    });

    initXyebbsStats();

    // XYEBBS 搜索防抖
    var xyebbsSearchTimer = null;
    $('#xyebbsSearchInput').on('input', function() {
        var val = $(this).val().trim();
        if (val) {
            $('#xyebbsSearchClear').show();
        } else {
            $('#xyebbsSearchClear').hide();
        }
        clearTimeout(xyebbsSearchTimer);
        xyebbsSearchTimer = setTimeout(function() {
            currentXyebbsCardLimit = 48;
            renderXyebbsView();
        }, 250);
    });

    $('#xyebbsSearchClear').on('click', function() {
        $('#xyebbsSearchInput').val('').trigger('input');
    });

    $('#xyebbsSortSelect, #xyebbsVerSelect, #xyebbsLoaderSelect').on('change', function() {
        currentXyebbsCardLimit = 48;
        renderXyebbsView();
    });

    // XYEBBS 分类 Chips 点击单选与联动
    // 多选（向 MCMod 看齐）：点「全部」清空；点分类在选中集合里切换；已选中的再点取消
    $('#xyebbsCategoryChips').on('click', '.s-chip', function() {
        var cat = $(this).data('cat') || '';
        if (!cat) {
            xyebbsActiveCat = [];
        } else {
            var at = xyebbsActiveCat.indexOf(cat);
            if (at === -1) { xyebbsActiveCat.push(cat); } else { xyebbsActiveCat.splice(at, 1); }
        }
        renderXyebbsCatChips();
        currentXyebbsCardLimit = 48;
        renderXyebbsView();
    });

    // XYEBBS 渠道 Chips 点击
    $('#xyebbsPanChips').on('click', '.s-chip', function() {
        $('#xyebbsPanChips .s-chip').removeClass('active');
        $(this).addClass('active');
        xyebbsActivePan = $(this).data('pan') || '';
        currentXyebbsCardLimit = 48;
        renderXyebbsView();
    });

    // XYEBBS 活动过滤项清除
    $('#xyebbsActiveFilters').on('click', '.active-pill', function() {
        var clearType = $(this).data('clear');
        if (clearType === 'search') {
            $('#xyebbsSearchInput').val('').trigger('input');
        } else if (clearType === 'cat') {
            var val = $(this).data('val');
            if (val) {
                var at = xyebbsActiveCat.indexOf(val);
                if (at !== -1) xyebbsActiveCat.splice(at, 1);
            } else {
                xyebbsActiveCat = [];
            }
            renderXyebbsCatChips();
            currentXyebbsCardLimit = 48;
            renderXyebbsView();
        } else if (clearType === 'pan') {
            $('#xyebbsPanChips .s-chip[data-pan=""]').click();
        } else if (clearType === 'ver') {
            $('#xyebbsVerSelect').val('').trigger('change');
        } else if (clearType === 'loader') {
            $('#xyebbsLoaderSelect').val('').trigger('change');
        }
    });

    $('#xyebbsClearFiltersBtn, #xyebbsResetBtn').on('click', function() {
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
    });

    // XYEBBS 加载更多与展开全部
    $(document).on('click', '.js-xyebbs-load-more', function() {
        currentXyebbsCardLimit += 48;
        renderXyebbsView();
    });

    $(document).on('click', '.js-xyebbs-load-all', function() {
        currentXyebbsCardLimit = 99999;
        renderXyebbsView();
    });

    /* ════════ Modrinth 平台统计与交互事件 ════════ */
    function initModrinthStats() {
        if (!modrinthPacks.length) return;
        var totalDl = 0;
        var totalFollows = 0;
        var verSet = {};
        var catSet = {};

        modrinthPacks.forEach(function(p) {
            totalDl += (p.downloads || 0);
            totalFollows += (p.followers || 0);
            if (p.mc_version && p.mc_version !== '未知') {
                verSet[p.mc_version] = (verSet[p.mc_version] || 0) + 1;
            }
            (p.categories || []).forEach(function(c) {
                if (c) catSet[c] = (catSet[c] || 0) + 1;
            });
        });

        var dlText = totalDl > 100000000 ? (totalDl / 100000000).toFixed(2) + '亿' :
                     (totalDl > 10000 ? (totalDl / 10000).toFixed(1) + '万' : totalDl);
        var flText = totalFollows > 10000 ? (totalFollows / 10000).toFixed(1) + '万' : totalFollows;

        $('#modrinthStatDownloads').text(dlText);
        $('#modrinthStatFollows').text(flText);
        $('#modrinthStatTotal').text((modrinthPacks.length || 18328).toLocaleString() + ' 款');

        // 主流加载器占比：纯统计真实 loaders 字段，不做任何推断
        var ldSet = {}, ldTotal = 0;
        modrinthPacks.forEach(function(p) {
            (p.loaders || []).forEach(function(l) { ldSet[l] = (ldSet[l] || 0) + 1; ldTotal++; });
        });
        var ldTop = Object.keys(ldSet).sort(function(a, b) { return ldSet[b] - ldSet[a]; })[0];
        if (ldTop) {
            var ldPct = (ldSet[ldTop] * 100.0 / ldTotal).toFixed(1);
            $('#modrinthStatTopLoader').text(loaderLabel(ldTop));
            $('#modrinthStatTopLoaderItem').attr('title', loaderLabel(ldTop) + ' 覆盖 ' + ldPct + '% 的整合包');
        }

        var sortedVers = Object.keys(verSet).sort(function(a, b) { return verSet[b] - verSet[a]; });
        var $verSel = $('#modrinthVerSelect');
        sortedVers.forEach(function(v) {
            $verSel.append('<option value="' + v + '">' + v + ' (' + verSet[v] + ')</option>');
        });
        $verSel.trigger('change.select2');

        var sortedCats = Object.keys(catSet).sort(function(a, b) { return catSet[b] - catSet[a]; });
        window.__modrinthAllCats = sortedCats;
        window.__modrinthCatCounts = catSet;
        window.__modrinthCatsExpanded = false;
        renderModrinthCatChips();
    }

    function renderModrinthCatChips() {
        var $catChips = $('#modrinthCategoryChips');
        $catChips.empty();
        $catChips.append('<span class="s-chip' + (modrinthActiveCat.length === 0 ? ' active' : '') + '" data-cat="">全部玩法</span>');
        var maxVisible = window.__modrinthCatsExpanded ? window.__modrinthAllCats.length : 12;
        window.__modrinthAllCats.forEach(function(c, idx) {
            var isSelected = modrinthActiveCat.indexOf(c) !== -1;
            var isVisible = idx < maxVisible || isSelected;
            var count = window.__modrinthCatCounts[c] || 0;
            $catChips.append('<span class="s-chip' + (isSelected ? ' active' : '') + '" data-cat="' + c + '" title="' + c + '" style="' + (isVisible ? '' : 'display:none;') + '">' + catLabel(c) + ' <span class="s-chip-count">' + count + '</span></span>');
        });
        if (window.__modrinthAllCats.length > 12) {
            $('#modrinthExpandCats').show().text(window.__modrinthCatsExpanded ? '收起 ▴' : ('展开全部(' + window.__modrinthAllCats.length + '项) ▾'));
        } else {
            $('#modrinthExpandCats').hide();
        }
    }

    $('#modrinthExpandCats').on('click', function() {
        window.__modrinthCatsExpanded = !window.__modrinthCatsExpanded;
        renderModrinthCatChips();
    });

    initModrinthStats();

    var modrinthSearchTimer = null;
    $('#modrinthSearchInput').on('input', function() {
        var val = $(this).val().trim();
        if (val) $('#modrinthSearchClear').show();
        else $('#modrinthSearchClear').hide();
        clearTimeout(modrinthSearchTimer);
        modrinthSearchTimer = setTimeout(function() {
            currentModrinthCardLimit = 48;
            renderModrinthView();
        }, 250);
    });

    $('#modrinthSearchClear').on('click', function() {
        $('#modrinthSearchInput').val('').trigger('input');
    });

    $('#modrinthSortSelect, #modrinthVerSelect, #modrinthLoaderSelect').on('change', function() {
        currentModrinthCardLimit = 48;
        renderModrinthView();
    });

    // 多选（向 MCMod 看齐）：点「全部」清空；点分类在选中集合里切换；已选中的再点取消
    $('#modrinthCategoryChips').on('click', '.s-chip', function() {
        var cat = $(this).data('cat') || '';
        if (!cat) {
            modrinthActiveCat = [];
        } else {
            var at = modrinthActiveCat.indexOf(cat);
            if (at === -1) { modrinthActiveCat.push(cat); } else { modrinthActiveCat.splice(at, 1); }
        }
        renderModrinthCatChips();
        currentModrinthCardLimit = 48;
        renderModrinthView();
    });

    $('#modrinthActiveFilters').on('click', '.active-pill', function() {
        var clearType = $(this).data('clear');
        if (clearType === 'search') $('#modrinthSearchInput').val('').trigger('input');
        else if (clearType === 'cat') {
            var val = $(this).data('val');
            if (val) {
                var at = modrinthActiveCat.indexOf(val);
                if (at !== -1) modrinthActiveCat.splice(at, 1);
            } else {
                modrinthActiveCat = [];
            }
            renderModrinthCatChips();
            currentModrinthCardLimit = 48;
            renderModrinthView();
        }
        else if (clearType === 'ver') $('#modrinthVerSelect').val('').trigger('change');
        else if (clearType === 'loader') $('#modrinthLoaderSelect').val('').trigger('change');
    });

    $('#modrinthClearFiltersBtn, #modrinthResetBtn').on('click', function() {
        modrinthActiveCat = [];
        currentModrinthCardLimit = 48;
        $('#modrinthSortSelect').val('downloads_desc').trigger('change');
        $('#modrinthVerSelect').val('').trigger('change');
        $('#modrinthLoaderSelect').val('').trigger('change');
        $('#modrinthSearchInput').val('');
        $('#modrinthSearchClear').hide();
        renderModrinthCatChips();
        renderModrinthView();
    });

    $(document).on('click', '.js-modrinth-load-more', function() {
        currentModrinthCardLimit += 48;
        renderModrinthView();
    });

    $(document).on('click', '.js-modrinth-load-all', function() {
        currentModrinthCardLimit = 99999;
        renderModrinthView();
    });

    /* ════════ CurseForge 平台统计与交互事件 ════════ */
    function initCurseforgeStats() {
        if (!curseforgePacks.length) return;
        var totalDl = 0;
        var totalLikes = 0;
        var verSet = {};
        var catSet = {};

        curseforgePacks.forEach(function(p) {
            totalDl += (p.downloads || 0);
            totalLikes += (p.followers || 0);
            if (p.mc_version && p.mc_version !== '未知') {
                verSet[p.mc_version] = (verSet[p.mc_version] || 0) + 1;
            }
            (p.categories || []).forEach(function(c) {
                if (c) catSet[c] = (catSet[c] || 0) + 1;
            });
        });

        var dlText = totalDl > 100000000 ? (totalDl / 100000000).toFixed(2) + '亿' :
                     (totalDl > 10000 ? (totalDl / 10000).toFixed(1) + '万' : totalDl);
        var lkText = totalLikes > 10000 ? (totalLikes / 10000).toFixed(1) + '万' : totalLikes;

        $('#curseforgeStatDownloads').text(dlText);
        $('#curseforgeStatLikes').text(lkText);
        $('#curseforgeStatTotal').text((curseforgePacks.length || 45797).toLocaleString() + ' 款');

        // 主流加载器占比：纯统计真实 loaders 字段，不做任何推断
        var ldSetC = {}, ldTotalC = 0;
        curseforgePacks.forEach(function(p) {
            (p.loaders || []).forEach(function(l) { ldSetC[l] = (ldSetC[l] || 0) + 1; ldTotalC++; });
        });
        var ldTopC = Object.keys(ldSetC).sort(function(a, b) { return ldSetC[b] - ldSetC[a]; })[0];
        if (ldTopC) {
            var ldPctC = (ldSetC[ldTopC] * 100.0 / ldTotalC).toFixed(1);
            $('#curseforgeStatTopLoader').text(loaderLabel(ldTopC));
            $('#curseforgeStatTopLoaderItem').attr('title', loaderLabel(ldTopC) + ' 覆盖 ' + ldPctC + '% 的整合包');
        }

        var sortedVers = Object.keys(verSet).sort(function(a, b) { return verSet[b] - verSet[a]; });
        var $verSel = $('#curseforgeVerSelect');
        sortedVers.forEach(function(v) {
            $verSel.append('<option value="' + v + '">' + v + ' (' + verSet[v] + ')</option>');
        });
        $verSel.trigger('change.select2');

        var sortedCats = Object.keys(catSet).sort(function(a, b) { return catSet[b] - catSet[a]; });
        window.__curseforgeAllCats = sortedCats;
        window.__curseforgeCatCounts = catSet;
        window.__curseforgeCatsExpanded = false;
        renderCurseforgeCatChips();
    }

    function renderCurseforgeCatChips() {
        var $catChips = $('#curseforgeCategoryChips');
        $catChips.empty();
        $catChips.append('<span class="s-chip' + (curseforgeActiveCat.length === 0 ? ' active' : '') + '" data-cat="">全部玩法</span>');
        var maxVisible = window.__curseforgeCatsExpanded ? window.__curseforgeAllCats.length : 12;
        window.__curseforgeAllCats.forEach(function(c, idx) {
            var isSelected = curseforgeActiveCat.indexOf(c) !== -1;
            var isVisible = idx < maxVisible || isSelected;
            var count = window.__curseforgeCatCounts[c] || 0;
            $catChips.append('<span class="s-chip' + (isSelected ? ' active' : '') + '" data-cat="' + c + '" title="' + c + '" style="' + (isVisible ? '' : 'display:none;') + '">' + catLabel(c) + ' <span class="s-chip-count">' + count + '</span></span>');
        });
        if (window.__curseforgeAllCats.length > 12) {
            $('#curseforgeExpandCats').show().text(window.__curseforgeCatsExpanded ? '收起 ▴' : ('展开全部(' + window.__curseforgeAllCats.length + '项) ▾'));
        } else {
            $('#curseforgeExpandCats').hide();
        }
    }

    $('#curseforgeExpandCats').on('click', function() {
        window.__curseforgeCatsExpanded = !window.__curseforgeCatsExpanded;
        renderCurseforgeCatChips();
    });

    initCurseforgeStats();

    var curseforgeSearchTimer = null;
    $('#curseforgeSearchInput').on('input', function() {
        var val = $(this).val().trim();
        if (val) $('#curseforgeSearchClear').show();
        else $('#curseforgeSearchClear').hide();
        clearTimeout(curseforgeSearchTimer);
        curseforgeSearchTimer = setTimeout(function() {
            currentCurseforgeCardLimit = 48;
            renderCurseforgeView();
        }, 250);
    });

    $('#curseforgeSearchClear').on('click', function() {
        $('#curseforgeSearchInput').val('').trigger('input');
    });

    $('#curseforgeSortSelect, #curseforgeVerSelect, #curseforgeLoaderSelect').on('change', function() {
        currentCurseforgeCardLimit = 48;
        renderCurseforgeView();
    });

    // 多选（向 MCMod 看齐）：点「全部」清空；点分类在选中集合里切换；已选中的再点取消
    $('#curseforgeCategoryChips').on('click', '.s-chip', function() {
        var cat = $(this).data('cat') || '';
        if (!cat) {
            curseforgeActiveCat = [];
        } else {
            var at = curseforgeActiveCat.indexOf(cat);
            if (at === -1) { curseforgeActiveCat.push(cat); } else { curseforgeActiveCat.splice(at, 1); }
        }
        renderCurseforgeCatChips();
        currentCurseforgeCardLimit = 48;
        renderCurseforgeView();
    });

    $('#curseforgeActiveFilters').on('click', '.active-pill', function() {
        var clearType = $(this).data('clear');
        if (clearType === 'search') $('#curseforgeSearchInput').val('').trigger('input');
        else if (clearType === 'cat') {
            var val = $(this).data('val');
            if (val) {
                var at = curseforgeActiveCat.indexOf(val);
                if (at !== -1) curseforgeActiveCat.splice(at, 1);
            } else {
                curseforgeActiveCat = [];
            }
            renderCurseforgeCatChips();
            currentCurseforgeCardLimit = 48;
            renderCurseforgeView();
        }
        else if (clearType === 'ver') $('#curseforgeVerSelect').val('').trigger('change');
        else if (clearType === 'loader') $('#curseforgeLoaderSelect').val('').trigger('change');
    });

    $('#curseforgeClearFiltersBtn, #curseforgeResetBtn').on('click', function() {
        curseforgeActiveCat = [];
        currentCurseforgeCardLimit = 48;
        $('#curseforgeSortSelect').val('downloads_desc').trigger('change');
        $('#curseforgeVerSelect').val('').trigger('change');
        $('#curseforgeLoaderSelect').val('').trigger('change');
        $('#curseforgeSearchInput').val('');
        $('#curseforgeSearchClear').hide();
        renderCurseforgeCatChips();
        renderCurseforgeView();
    });

    $(document).on('click', '.js-curseforge-load-more', function() {
        currentCurseforgeCardLimit += 48;
        renderCurseforgeView();
    });

    $(document).on('click', '.js-curseforge-load-all', function() {
        currentCurseforgeCardLimit = 99999;
        renderCurseforgeView();
    });

    // 全局六大平台总徽标动态刷新
    function updateAllPlatformsTotalBadge() {
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
    }
    updateAllPlatformsTotalBadge();
    startIdlePrefetch();


    /* ════════ 主题切换 ════════ */
    var savedTheme = localStorage.getItem('mcmod-theme-v2') || 'light';
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('mcmod-theme-v2', theme);
        $('.theme-btn').removeClass('active');
        $('.theme-btn[data-theme="' + theme + '"]').addClass('active');
    }
    setTheme(savedTheme);
    $('.theme-btn').on('click', function() {
        setTheme($(this).data('theme'));
    });
    // 普通基础多选下拉（选项较少：分类、包标签、模组分类）
    $('#categoryFilter, #packTagFilter, #modCategoryFilter').select2({
        theme: 'bootstrap-5',
        width: '100%',
        closeOnSelect: false,
        placeholder: function() { return $(this).data('placeholder') || '全部'; }
    });

    // 针对 1.1 万个模组的海量多选：采用毫秒级流式 query 匹配，彻底消除 3 秒 UI 假死与鼠标卡顿
    $('#modFilter').select2({
        theme: 'bootstrap-5',
        width: '100%',
        closeOnSelect: false,
        placeholder: '输入模组名称检索（1.1万模组）',
        minimumInputLength: 1,
        dropdownCssClass: 'hub-select2-dropdown',
        query: function(options) {
            var term = (options.term || '').toLowerCase().trim();
            var matches = [];
            var list = window.allModsList || [];
            if ((!list || !list.length) && window.compareData) {
                var modCountMap = {};
                Object.values(window.compareData).forEach(function(p) {
                    (p.mods || []).forEach(function(m) {
                        var mn = typeof m === 'string' ? m : (m.name || '');
                        if (mn) modCountMap[mn] = (modCountMap[mn] || 0) + 1;
                    });
                });
                window.allModsList = Object.keys(modCountMap).map(function(k) {
                    return { id: k, text: k + ' (' + modCountMap[k] + ')' };
                }).sort(function(a, b) { return b.text.localeCompare(a.text); });
                list = window.allModsList;
            }
            for (var i = 0; i < list.length; i++) {
                var item = list[i];
                if (item.text.toLowerCase().indexOf(term) !== -1) {
                    matches.push(item);
                    if (matches.length >= 60) break;
                }
            }
            options.callback({ results: matches });
        }
    });

    function renderActiveModBadges() {
        var vals = $('#modFilter').val() || [];
        if (!Array.isArray(vals)) vals = vals ? [vals] : [];
        var $badges = $('#activeModBadges');
        if (!$badges.length) return;
        $badges.empty();
        if (!vals.length) return;
        $badges.append('<span style="font-size:0.75rem; font-weight:750; color:var(--text-muted); margin-right:2px;">已包含：</span>');
        vals.forEach(function(val) {
            var $pill = $('<span class="active-mod-pill" title="点击 ✕ 移除该模组筛选"><span class="pill-name"></span><button type="button" class="pill-remove-btn">✕</button></span>');
            $pill.find('.pill-name').text(val);
            $pill.find('.pill-remove-btn').attr('data-val', val);
            $badges.append($pill);
        });
    }

    $('#modFilter').on('select2:select', function(e) {
        var data = (e && e.params && e.params.data) || {};
        if (data && data.id) {
            if (!$('#modFilter').find('option[value="' + data.id + '"]').length) {
                $('#modFilter').append(new Option(data.text || data.id, data.id, true, true));
            }
        }
        renderActiveModBadges();
    });

    $('#modFilter').on('select2:unselect', function(e) {
        var data = (e && e.params && e.params.data) || {};
        if (data && data.id) {
            $('#modFilter').find('option[value="' + data.id + '"]').remove();
        }
        renderActiveModBadges();
    });

    $('#modFilter').on('change', function() {
        renderActiveModBadges();
    });

    $('#activeModBadges').on('click', '.pill-remove-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var val = $(this).attr('data-val');
        var current = $('#modFilter').val() || [];
        if (!Array.isArray(current)) current = current ? [current] : [];
        var idx = current.indexOf(val);
        if (idx >= 0) {
            current.splice(idx, 1);
            $('#modFilter').find('option[value="' + val + '"]').remove();
            $('#modFilter').val(current).trigger('change');
        }
    });
    $('.select2-glass-single').select2({
        theme: 'bootstrap-5',
        width: '100%',
        minimumResultsForSearch: 8,
        selectionCssClass: 'select2-glass-selection',
        dropdownCssClass: 'select2-glass-dropdown',
        placeholder: function() { return $(this).data('placeholder') || '全部'; }
    });
    // 🌟 全局中央单选下拉框升级 Select2 晶透毛玻璃组件（彻底消除 Windows 原生系统黑框蓝条）
    $('.select2-hub').select2({
        theme: 'bootstrap-5',
        width: 'auto',
        dropdownAutoWidth: true,
        minimumResultsForSearch: 8,
        selectionCssClass: 'hub-select2-selection',
        dropdownCssClass: 'hub-select2-dropdown'
    });
    /* ════════ DataTables 初始化（scrollY 固定表头 + 分页优化） ════════ */
    // 🌟 性能优化：将重量级的表格初始化推入下一个事件循环，让 Select2 优先完成重绘，彻底解除页面开启瞬间的 UI 卡死
    setTimeout(function() {
        /* ════════ 全文穿透搜索引擎：支持范围自定义的全局检索 ════════ */
        function normalizeSearchKeyword() {
            var $filterInput = $('#modpackTable_filter input');
            return $filterInput.length > 0 ? $filterInput.val().trim() : '';
        }
        function textHasKeyword(text, keyword) {
            return !!(text && keyword && String(text).toLowerCase().indexOf(keyword.toLowerCase()) !== -1);
        }
        function findCommentMatch(cmt, keyword) {
            if (!cmt || !cmt.comments || !keyword) return -1;
            for (var j = 0; j < cmt.comments.length; j++) {
                var c = cmt.comments[j];
                if (textHasKeyword(c.text, keyword) || textHasKeyword(c.author, keyword)) return j;
                if (c.replies) {
                    for (var k = 0; k < c.replies.length; k++) {
                        var r = c.replies[k];
                        if (textHasKeyword(r.text, keyword) || textHasKeyword(r.author, keyword)) return j;
                    }
                }
            }
            return -1;
        }
        function matchRowSearch(data, tr, keyword, scope) {
            var result = { basic: false, title: false, cat: false, desc: false, comment: false, commentIndex: -1 };
            if (!keyword) return result;
            var kw = keyword.toLowerCase();
            for (var i = 0; i < data.length; i++) {
                if (String(data[i] || '').toLowerCase().indexOf(kw) !== -1) {
                    result.basic = true; break;
                }
            }
            result.title = String(data[0] || '').toLowerCase().indexOf(kw) !== -1;
            result.cat = String(data[6] || '').toLowerCase().indexOf(kw) !== -1 ||
                         String(data[7] || '').toLowerCase().indexOf(kw) !== -1;
            var mid = $(tr).find('a.modpack-link').data('mid');
            if (mid) {
                result.desc = textHasKeyword(getDescText(descData[mid]), keyword);
                result.commentIndex = findCommentMatch(commentData[mid], keyword);
                result.comment = result.commentIndex >= 0;
            }
            return result;
        }
        function rowMatchesScope(match, scope) {
            if (scope === 'title') return match.title;
            if (scope === 'cat') return match.cat;
            if (scope === 'desc') return match.desc;
            if (scope === 'comment') return match.comment;
            if (scope === 'basic') return match.basic;
            return match.basic || match.desc || match.comment;
        }
        function matchRowSearchFast(data, rowData, keyword, scope) {
            var result = { basic: false, title: false, cat: false, desc: false, comment: false, commentIndex: -1 };
            if (!keyword) return result;
            var kw = keyword.toLowerCase();
            result.title = (rowData.title || '').toLowerCase().indexOf(kw) !== -1;
            result.cat = (rowData.cat_search || '').toLowerCase().indexOf(kw) !== -1 ||
                         (rowData.pack_search || '').toLowerCase().indexOf(kw) !== -1;
            var mid = rowData.mid;
            if (mid) {
                result.desc = textHasKeyword(getDescText(descData[mid]), keyword);
                result.commentIndex = findCommentMatch(commentData[mid], keyword);
                result.comment = result.commentIndex >= 0;
            }
            result.basic = result.title || result.cat || (rowData.mods_search || '').toLowerCase().indexOf(kw) !== -1;
            return result;
        }

        $.fn.dataTable.ext.search.push(
            function(settings, data, dataIndex) {
                var keyword = normalizeSearchKeyword();
                if (!keyword) return true;
                var scope = $('#searchScope').val() || 'all';
                var rowData = (window.tableRowsData && window.tableRowsData[dataIndex]);
                if (!rowData) return true;
                return rowMatchesScope(matchRowSearchFast(data, rowData, keyword, scope), scope);
            }
        );
        var _scrollH = Math.max(400, $(window).height() - 320);
    var table = null;

    /* ════════ DataTables 初始化（数据驱动 + 真正 deferRender 延迟渲染） ════════ */
    window.initMcmodTable = function() {
        if ($.fn.DataTable && $.fn.DataTable.isDataTable('#modpackTable')) {
            if (window.table) window.table.columns.adjust();
            return;
        }
        if (!window.tableRowsData || !window.tableRowsData.length) return;
        // 初始化每个 row 对象的排序字段缓存
        window.tableRowsData.forEach(function(r) {
            r.sort_col0 = r.name_order || '';
            r.sort_col1 = (typeof r.score_n === 'number' ? r.score_n : (parseFloat(r.score_n) || 0));
            r.sort_col2 = (typeof r.t7_n === 'number' ? r.t7_n : (parseFloat(r.t7_n) || 0));
            r.sort_col3 = (typeof r.rv_n === 'number' ? r.rv_n : (parseFloat(r.rv_n) || 0));
            r.sort_col4 = (typeof r.com_n === 'number' ? r.com_n : (parseFloat(r.com_n) || 0));
            r.sort_col5 = (typeof r.tag_count === 'number' ? r.tag_count : (parseInt(r.tag_count) || 0));
            r.sort_col6 = (typeof r.mod_count === 'number' ? r.mod_count : (parseInt(r.mod_count) || 0));
        });

        table = window.table = $('#modpackTable').DataTable({
        "data": window.tableRowsData || [],
        "deferRender": true,
        "columns": [
            {
                "data": "c0",
                "orderSequence": ["asc", "desc"],
                "render": function(data, type, row) {
                    if (type === 'sort' || type === 'order') return row.sort_col0;
                    if (type === 'filter' || type === 'search') return (row.title || '') + ' ' + (row.type_name || '');
                    return data;
                }
            },
            {
                "data": "c1",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {
                    if (type === 'sort' || type === 'order') return row.sort_col1;
                    return data;
                }
            },
            {
                "data": "c2",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {
                    if (type === 'sort' || type === 'order') return row.sort_col2;
                    return data;
                }
            },
            {
                "data": "c3",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {
                    if (type === 'sort' || type === 'order') return row.sort_col3;
                    return data;
                }
            },
            {
                "data": "c4",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {
                    if (type === 'sort' || type === 'order') return row.sort_col4;
                    return data;
                }
            },
            {
                "data": "c5",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {
                    if (type === 'sort' || type === 'order') return row.sort_col5;
                    if (type === 'filter' || type === 'search') return row.tags_search || '';
                    return data;
                }
            },
            {
                "data": "c6",
                "orderSequence": ["desc", "asc"],
                "render": function(data, type, row) {
                    if (type === 'sort' || type === 'order') return row.sort_col6;
                    if (type === 'filter' || type === 'search') return row.mods_search || '';
                    return data;
                }
            }
        ],
        "createdRow": function(row, rowData, dataIndex) {
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
        },

        "scrollX": true,
        "autoWidth": false,
        "search": {
            "smart": false
        },
        "order": [[1, "desc"]],       // 默认按「官方流行指数」降序（已并入趋势列）
        "pageLength": 25,             // ★ 默认每页 25 条
        "paging": true,
        "deferRender": true,
        "lengthChange": true,
        "lengthMenu": [[25, 50, 100, 200, -1], [25, 50, 100, 200, "全部"]],
        "scrollY": _scrollH,
        "scrollCollapse": true,
        "language": {
            "search": "🔍 全局关键字检索：",
            "info": "当前第 _START_ - _END_ 条 / 共 _TOTAL_ 条 · 筛选自 _MAX_ 条",
            "infoEmpty": "暂无匹配记录",
            "infoFiltered": "(从 _MAX_ 条总记录中筛选)",
            "zeroRecords": "没有找到符合条件的整合包",
            "lengthMenu": "每页显示 _MENU_ 条",
            "paginate": {
                "first": "«",
                "last": "»",
                "next": "›",
                "previous": "‹"
            }
        },
        "columnDefs": [
            { "width": "220px", "targets": 0 },
            { "width": "150px", "targets": 1 },
            { "width": "118px", "targets": 2 },
            { "width": "112px", "targets": 3 },
            { "width": "104px", "targets": 4 },
            { "width": "220px", "targets": 5 },
            { "width": "calc(100vw - 900px)", "targets": 6 },
            { "orderable": true,  "targets": [0,1,2,3,4,5,6] }
        ],
        "initComplete": function() {
            var api = this.api();
            /* 将每页条数选择器整合进顶部极简工具栏，消除自带表格上方空缺与重复搜索框 */
            var $wrapper = $(this.api().table().container());
            var $length = $wrapper.find('.dataTables_length');
            var $filter = $wrapper.find('.dataTables_filter');
            var $info = $wrapper.find('.dataTables_info');
            var $paginate = $wrapper.find('.dataTables_paginate');
            if ($length.length) {
                $length.hide();
            }
            if ($('#hubPageSize').length) {
                $('#hubPageSize').val(api.page.len());
                $('#hubPageSize').on('change', function() {
                    var len = parseInt($(this).val(), 10);
                    api.page.len(len).draw();
                });
                $('#hubPageSize').select2({
                    theme: 'bootstrap-5',
                    width: 'auto',
                    dropdownAutoWidth: true,
                    minimumResultsForSearch: Infinity,
                    selectionCssClass: 'hub-select2-selection',
                    dropdownCssClass: 'hub-select2-dropdown'
                });
            }
            /* 隐藏自带的空行与重复搜索行，让表格紧凑无缝贴合工具栏 */
            $filter.closest('.row').hide();
            $info.css({ 'padding-top': '0.6rem', 'clear': 'both' });
            $paginate.css({ 'padding-top': '0.3rem', 'text-align': 'center' });

            /* ★ 动态注入：全局搜索靶向选择器（仅精准注入到直接的搜索输入框 label，绝不重复污染 length 的 label） */
            var $searchLabel = $filter.children('label');
            if ($('#searchScope').length === 0) {
                var scopeSelect = '<select id="searchScope" class="form-select form-select-sm d-inline-block w-auto me-2 select2-glass-single" data-placeholder="穿透搜索">' +
                                  '<option value="all">🔍 穿透搜索 (全部内容)</option>' +
                                  '<option value="title">📘 仅搜整合包名称</option>' +
                                  '<option value="cat">🏷️ 仅搜分类与标签</option>' +
                                  '<option value="desc">📖 仅搜百科长篇介绍</option>' +
                                  '<option value="comment">💬 仅搜评论与讨论区</option>' +
                                  '</select>';
                $searchLabel.prepend(scopeSelect);
                $('#searchScope').select2({
                    theme: 'bootstrap-5',
                    width: '210px',
                    minimumResultsForSearch: Infinity,
                    selectionCssClass: 'select2-glass-selection',
                    dropdownCssClass: 'select2-glass-dropdown search-scope-dropdown'
                });
            }
            if ($('#searchNav').length === 0) {
                var $searchNav = $('<span class="search-nav" id="searchNav" style="display:none;"><span class="search-nav-info" id="searchNavInfo">0 / 0</span><button type="button" class="search-nav-btn" id="searchPrev" title="上一个搜索结果">‹</button><button type="button" class="search-nav-btn" id="searchNext" title="下一个搜索结果">›</button><button type="button" class="search-nav-btn" id="searchOpen" title="打开命中的介绍或评论">⌖</button></span>');
                $searchLabel.append($searchNav);
            }
            var searchHits = [];
            var searchHitIndex = -1;
            var rawCellHtml = new WeakMap();
            function restoreSearchHighlights() {
                $wrapper.find('tbody td').each(function() {
                    var raw = rawCellHtml.get(this);
                    if (raw !== undefined) {
                        this.innerHTML = raw;
                    }
                });
                $wrapper.find('tbody tr').removeClass('search-hit-row search-current-row');
            }
            function highlightCell($td, keyword) {
                if (!$td.length || !keyword) return;
                var node = $td[0];
                if (!rawCellHtml.has(node)) rawCellHtml.set(node, node.innerHTML);
                var rawText = $td.text();
                if (!textHasKeyword(rawText, keyword)) return;
                node.innerHTML = highlightText(rawText, keyword);
            }
            function updateSearchNav() {
                var keyword = normalizeSearchKeyword();
                var scope = $('#searchScope').val() || 'all';
                restoreSearchHighlights();
                searchHits = [];
                searchHitIndex = -1;
                if (!keyword) {
                    $('#searchNav').hide();
                    return;
                }
                table.rows({ search: 'applied' }).every(function() {
                    var rowIdx = this.index();
                    var rowData = window.tableRowsData ? window.tableRowsData[rowIdx] : null;
                    if (!rowData) return;
                    var match = matchRowSearchFast(this.data(), rowData, keyword, scope);
                    if (!rowMatchesScope(match, scope)) return;
                    searchHits.push({ index: rowIdx, match: match });
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
                    if (hitType === 'cat' || hitType === 'basic') {
                        highlightCell($tr.children('td').eq(5), keyword);
                        highlightCell($tr.children('td').eq(6), keyword);
                        if ($tr.children('td').eq(6).text().toLowerCase().indexOf(keyword.toLowerCase()) !== -1) {
                            $tr.find('.mod-details').prop('open', true);
                        }
                    }
                    searchHits.push({ tr: tr, type: hitType, commentIndex: match.commentIndex });
                });
                if (searchHits.length > 0) searchHitIndex = 0;
                $('#searchNav').show();
                refreshSearchNavState(false);
            }
            function refreshSearchNavState(scrollToRow) {
                var total = searchHits.length;
                $('#searchNavInfo').text(total ? ((searchHitIndex + 1) + ' / ' + total) : '0 / 0');
                $('#searchPrev, #searchNext, #searchOpen').prop('disabled', total === 0);
                $wrapper.find('tbody tr').removeClass('search-current-row');
                if (!total) return;
                var hit = searchHits[searchHitIndex];
                var $tr = $(hit.tr).addClass('search-current-row');
                if (scrollToRow && $tr.length) {
                    var body = $wrapper.find('.dataTables_scrollBody')[0];
                    if (body) {
                        body.scrollTop = Math.max(0, hit.tr.offsetTop - 72);
                    } else {
                        hit.tr.scrollIntoView({ block: 'center', behavior: 'smooth' });
                    }
                }
            }
            function jumpSearch(delta) {
                if (!searchHits.length) return;
                searchHitIndex = (searchHitIndex + delta + searchHits.length) % searchHits.length;
                refreshSearchNavState(true);
            }
            function openSearchHit() {
                if (!searchHits.length) return;
                refreshSearchNavState(true);
                var hit = searchHits[searchHitIndex];
                var $tr = $(hit.tr);
                if (hit.type === 'comment') {
                    showCommentPopup($tr.children('td.td-comment'));
                } else {
                    showDescPopup($tr.find('a.modpack-link'));
                }
            }
            $('#searchScope').on('change', function() { table.draw(); });
            $('#searchPrev').on('click', function() { jumpSearch(-1); });
            $('#searchNext').on('click', function() { jumpSearch(1); });
            $('#searchOpen').on('click', function() { openSearchHit(); });
            /* ★ 强力拦截：解除 DataTables 原生绑定的搜索框事件，防止原生过滤机制对无单元格内容的评论进行误杀 */
            var $filterInput = $filter.find('input');
            $filterInput.off('keyup.DT search.DT input.DT paste.DT cut.DT');
            var searchTimer = null;
            $filterInput.on('keyup input', function() {
                clearTimeout(searchTimer);
                searchTimer = setTimeout(function() {
                    table.draw();
                }, 100);
            });
            /* ★ [v10.0] 顶部数据栏跟随横向滚动 */
            var $scrollBody = $wrapper.find('.dataTables_scrollBody');
            var $scrollHead = $wrapper.find('.dataTables_scrollHead');
            var $sortStrip = $('<div class="sort-strip"><div class="sort-strip-inner"></div></div>');
            $scrollHead.append($sortStrip);
            var $sortStripInner = $sortStrip.find('.sort-strip-inner');
            $scrollBody.on('scroll', function() {
                $scrollHead.scrollLeft($(this).scrollLeft());
                $sortStrip.scrollLeft($(this).scrollLeft());
            });
            $scrollHead.find('th').off('.DT');
            function rebuildSortStrip() {
                var html = '';
                var maxRight = 0;
                var $headTable = $wrapper.find('.dataTables_scrollHead table').first();
                $wrapper.find('.dataTables_scrollHead thead tr:first th').each(function(idx) {
                    var left = Math.round(this.offsetLeft || 0);
                    var w = Math.ceil(this.getBoundingClientRect().width || $(this).outerWidth());
                    if (w < 1) return;
                    html += '<button type="button" class="sort-strip-seg" data-col="' + idx + '" title="' + $(this).text().trim() + '" style="left:' + left + 'px;width:' + w + 'px"></button>';
                    maxRight = Math.max(maxRight, left + w);
                });
                var tableW = Math.ceil($headTable.outerWidth() || maxRight);
                $sortStripInner.css('width', Math.max(maxRight, tableW) + 'px').html(html);
            }
            function refreshActiveSortColumn() {
                var order = api.order();
                var colIdx = order && order.length ? order[0][0] : 2;
                var dir = order && order.length ? order[0][1] : 'desc';
                $wrapper.find('th, td').removeClass('dt-active-sort');
                $wrapper.find('.dataTables_scrollHead th').eq(colIdx).addClass('dt-active-sort').attr('data-order-dir', dir);
                $sortStrip.find('.sort-strip-seg').removeClass('active').attr('data-order-dir', '');
                $sortStrip.find('.sort-strip-seg[data-col="' + colIdx + '"]').addClass('active').attr('data-order-dir', dir);
                $wrapper.find('.dataTables_scrollBody tbody tr').each(function() {
                    $(this).children('td').eq(colIdx).addClass('dt-active-sort');
                });
            }
            function sortByColumn(colIdx) {
                if (colIdx < 0 || colIdx > 6) return;
                var current = api.order();
                var currentIdx = current && current.length ? current[0][0] : -1;
                var currentDir = current && current.length ? current[0][1] : 'desc';
                var nextDir = (currentIdx === colIdx && currentDir === 'asc') ? 'desc' : 'asc';
                api.order([colIdx, nextDir]).draw();
                refreshActiveSortColumn();
            }
            $wrapper.on('click', '.sort-option', function(e) {
                e.preventDefault();
                e.stopPropagation();
                var $opt = $(this);
                var $switcher = $opt.closest('.header-sort-switcher');
                var colIdx = parseInt($switcher.attr('data-col'));
                if ($opt.hasClass('active')) {
                    sortByColumn(colIdx);
                    return;
                }
                $switcher.find('.sort-option').removeClass('active');
                $opt.addClass('active');
                var subKey = $opt.attr('data-subkey');
                var sortProp = 'sort_col' + colIdx;
                (window.tableRowsData || []).forEach(function(r) {
                    var raw = r[subKey + '_n'] !== undefined ? r[subKey + '_n'] : (r[subKey] !== undefined ? r[subKey] : 0);
                    r[sortProp] = (subKey === 'name' || typeof raw === 'string') ? (raw || '') : (parseFloat(raw) || 0);
                });
                api.rows().invalidate('data');
                var order = api.order();
                var currentIdx = order && order.length ? order[0][0] : -1;
                var currentDir = order && order.length ? order[0][1] : 'desc';
                if (currentIdx === colIdx) {
                    api.order([colIdx, currentDir]).draw();
                } else {
                    api.order([colIdx, 'desc']).draw();
                }
            });
            $wrapper.on('click', '.dataTables_scrollHead th', function(e) {
                var colIdx = $(this).index();
                e.preventDefault();
                e.stopImmediatePropagation();
                sortByColumn(colIdx);
            });
            $sortStrip.on('click', '.sort-strip-seg', function(e) {
                e.preventDefault();
                e.stopPropagation();
                sortByColumn(Number($(this).data('col')));
            });
            rebuildSortStrip();
            refreshActiveSortColumn();
            updateSearchNav();
            api.on('order.dt draw.dt column-sizing.dt', function() {
                rebuildSortStrip();
                refreshActiveSortColumn();
                updateSearchNav();
            });
            function renderModSections(groups) {
                var html = '';
                groups.forEach(function(group) {
                    var name = group.n || '未分类';
                    var head = group.u ? '<a class="mod-category-link" href="' + escHtml(group.u, true) + '" target="_blank">' + escHtml(name, true) + '</a>' : '<span>' + escHtml(name, true) + '</span>';
                    html += '<section class="mod-category-section" data-mod-cat-key="' + escHtml(group.k || '', true) + '"><div class="mod-category-head">' + head + '<span>' + (group.m || []).length + '</span></div><div class="mod-grid">';
                    (group.m || []).forEach(function(mod) {
                        var modName = mod[0] || '';
                        if (!modName) return;
                        var version = mod[1] || '';
                        var url = mod[2] || '#';
                        var title = mod[3] || modName;
                        var hint = title + (version ? ' · 版本: ' + version : '') + ' · 分类: ' + name;
                        html += '<span class="tag-mod" role="button" tabindex="0" title="' + escHtml(hint, true) + '" data-mod="' + escHtml(modName, true) + '" data-mod-cat="' + escHtml(name, true) + '" data-mod-url="' + escHtml(url, true) + '"><span class="tag-mod-name">' + escHtml(modName, true) + '</span>' + (version ? '<span class="tag-mod-version">' + escHtml(version, true) + '</span>' : '') + '<a class="tag-mod-open" href="' + escHtml(url, true) + '" target="_blank" title="打开 MC百科模组页">↗</a></span>';
                    });
                    html += '</div></section>';
                });
                return html;
            }
            function loadFullModList($details) {
                var $full = $details.find('.mod-full-list');
                if (!$full.length || $full.attr('data-loaded') === '1' || $full.attr('data-loading') === '1') return;
                var mid = $details.closest('tr').attr('data-mid') || '';
                var groups = (window.modDetailData && window.modDetailData[mid]) || [];
                function doRender(gList) {
                    $full.removeAttr('data-loading').attr('data-loaded', '1');
                    $details.find('.mod-details-body > .mod-category-section, .mod-details-body > .tag-empty').remove();
                    if (!gList || !gList.length) {
                        var fallbackData = (window.compareData && window.compareData[mid]) || {};
                        var fallbackMods = fallbackData.mods || [];
                        if (fallbackMods.length) {
                            gList = [{
                                n: '全部收录模组',
                                k: 'cat0',
                                u: '',
                                m: fallbackMods.map(function(m) {
                                    var mn = typeof m === 'string' ? m : (m.name || m.title || '');
                                    return [mn, '', 'https://www.mcmod.cn/s?key=' + encodeURIComponent(mn), mn];
                                })
                            }];
                        }
                    }
                    if (gList && gList.length) {
                        $full.html(renderModSections(gList));
                    } else {
                        $full.html('<div class="tag-empty">暂无更多模组明细数据</div>');
                    }
                }
                if (groups.length) {
                    doRender(groups);
                    return;
                }
                $full.attr('data-loading', '1').html('<div class="tag-empty">正在读取完整模组列表…</div>');
                loadModDetailData(mid).then(function(loadedGroups) {
                    var finalGroups = (loadedGroups && loadedGroups.length) ? loadedGroups : ((window.modDetailData && window.modDetailData[mid]) || []);
                    doRender(finalGroups);
                }).catch(function() {
                    doRender([]);
                });
            }
            $wrapper.on('click', '.mod-summary-chip', function(e) {
                e.preventDefault();
                e.stopPropagation();
                var $chip = $(this);
            var key = $chip.data('mod-cat-key');
            var $details = $chip.closest('.mod-details');
            if (!$details.prop('open')) {
                $details.prop('open', true);
            }
            loadFullModList($details);
            setTimeout(function() {
                var $target = $details.find('.mod-category-section[data-mod-cat-key="' + key + '"]');
                if (!$target.length) return;
                var $scrollBox = $details.find('.mod-details-body');
                var currentTop = $scrollBox.scrollTop();
                var targetTop = $target.position().top + currentTop - 6;
                $scrollBox.stop(true).animate({ scrollTop: Math.max(0, targetTop) }, 220);
                    $target.removeClass('jump-focus');
                    void $target[0].offsetWidth;
                    $target.addClass('jump-focus');
                    api.columns.adjust();
                    rebuildSortStrip();
                    refreshActiveSortColumn();
                }, 40);
            });
            $wrapper.on('click', '.mod-details-body, .mod-category-section, .mod-grid', function(e) {
                if ($(e.target).closest('.tag-mod, .tag-mod-open, .mod-category-head, .mod-category-link, a, button').length) return;
                var $details = $(this).closest('.mod-details');
                if ($details.length && $details.prop('open')) {
                    $details.prop('open', false);
                    api.columns.adjust();
                    rebuildSortStrip();
                    refreshActiveSortColumn();
                }
            });
            $wrapper.on('click', '.mod-details > summary', function() {
                var current = $(this).closest('.mod-details')[0];
                setTimeout(function() {
                    if (current && current.open) {
                        $wrapper.find('.mod-details[open]').each(function() {
                            if (this !== current) this.open = false;
                        });
                        // 某些浏览器不让 <details> 的 toggle 事件冒泡；这里直接补载完整名单。
                        loadFullModList($(current));
                        api.columns.adjust();
                        rebuildSortStrip();
                        refreshActiveSortColumn();
                    }
                }, 0);
            });
            $wrapper.on('toggle', '.mod-details', function() {
                if (this.open) {
                    var current = this;
                    $wrapper.find('.mod-details[open]').each(function() {
                        if (this !== current) this.open = false;
                    });
                    loadFullModList($(this));
                }
                setTimeout(function() {
                    api.columns.adjust();
                    rebuildSortStrip();
                    refreshActiveSortColumn();
                }, 30);
            });
            $wrapper.on('wheel', '.mod-container, .mod-details-body', function(e) {
                var el = this;
                if (!el || el.scrollHeight <= el.clientHeight) return;
                var oe = e.originalEvent;
                var delta = oe.deltaY || 0;
                var atTop = el.scrollTop <= 0;
                var atBottom = Math.ceil(el.scrollTop + el.clientHeight) >= el.scrollHeight;
                if ((delta < 0 && atTop) || (delta > 0 && atBottom)) return;
                e.stopPropagation();
            });
            function toggleMultiSelect(selector, val) {
                var $sel = $(selector);
                var current = $sel.val() || [];
                if (!Array.isArray(current)) current = current ? [current] : [];
                var idx = current.indexOf(val);
                if (idx >= 0) {
                    current.splice(idx, 1);
                    $sel.find('option').filter(function() { return $(this).val() === val; }).remove();
                } else {
                    if ($sel.find('option').filter(function() { return $(this).val() === val; }).length === 0) {
                        $sel.append($('<option>', { value: val, text: val, selected: true }));
                    }
                    current.push(val);
                }
                $sel.val(current).trigger('change');
            }
            /* ★ [v10.0] 点击单元格内标签筛选/取消 */
            $wrapper.on('click', '.tag-cat', function(e) {
                if ($(e.target).closest('.tag-filter-open').length) return;
                e.preventDefault();
                e.stopPropagation();
                var val = ($(this).attr('data-tag') || $(this).find('.tag-filter-name').text() || $(this).text()).trim();
                toggleMultiSelect('#categoryFilter', val);
            });
            $wrapper.on('click', '.tag-pack', function(e) {
                if ($(e.target).closest('.tag-filter-open').length) return;
                e.preventDefault();
                e.stopPropagation();
                var val = ($(this).attr('data-tag') || $(this).find('.tag-filter-name').text() || $(this).text()).trim();
                toggleMultiSelect('#packTagFilter', val);
            });
            $wrapper.on('click', '.tag-filter-open', function(e) {
                e.stopPropagation();
            });
            $wrapper.on('click keydown', '.tag-mod', function(e) {
                if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') return;
                if ($(e.target).closest('.tag-mod-open').length) return;
                e.preventDefault();
                e.stopPropagation();
                var val = ($(this).attr('data-mod') || $(this).find('.tag-mod-name').text() || $(this).text()).trim();
                if (val) toggleMultiSelect('#modFilter', val);
            });
            $wrapper.on('click', '.tag-mod-open', function(e) {
                e.stopPropagation();
            });
            // 初始化完成后，延迟微调一下列宽，保证表头对齐
            setTimeout(function() {
                api.columns.adjust();
                rebuildSortStrip();
                refreshActiveSortColumn();
            }, 100);
        }
    });
    };
/* ══════════════ 1. DataTables 自定义多条件过滤器 ══════════════ */
    $.fn.dataTable.ext.search.push(
        function(settings, data, dataIndex) {
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
            function asArray(v) {
                if (!v) return [];
                return Array.isArray(v) ? v : [v];
            }
            function hasAll(rowText, selected) {
                selected = asArray(selected);
                if (!selected.length) return true;
                rowText = String(rowText || '').toLowerCase();
                for (var i = 0; i < selected.length; i++) {
                    if (rowText.indexOf(String(selected[i]).toLowerCase()) === -1) return false;
                }
                return true;
            }
            function passFilter(rowText, selected, exclude) {
                selected = asArray(selected);
                if (!selected.length) return true;
                var matched = hasAll(rowText, selected);
                return exclude ? !matched : matched;
            }
            // 分类和标签筛选（内存化高速检索，无需查询 DOM）
            var rowData = (window.tableRowsData && window.tableRowsData[dataIndex]);
            if (!rowData) return true;
            var rowType = rowData.type_name || '';
            var rowCat  = rowData.cat_search || '';
            var rowPack = rowData.pack_search || '';
            var rowMid = rowData.mid || '';
            var rowModData = (window.compareData && window.compareData[rowMid]) || {};
            var rowModCategories = (rowModData.mod_categories || []).join(' ');
            var rowModNames = (rowModData.mods || []).map(function(m) { return typeof m === 'string' ? m : (m.name || ''); }).join(' ');
            if (selectedType && rowType !== selectedType) return false;
            if (!passFilter(rowCat, selectedCat, excludeCat)) return false;
            if (!passFilter(rowPack, selectedPack, excludePack)) return false;
            if (!passFilter(rowModCategories, selectedModCat, excludeModCat)) return false;
            if (!passFilter(rowModNames, selectedMod, excludeMod)) return false;
            var trendDays = rowData.days_n || 0;
            if (isNaN(trendDays)) trendDays = 0; // 安全防御
            if (selectedTrend) {
                if (selectedTrend === "7_in") {
                    if (trendDays > 7) return false;      // 7天内：0~7天显示，大于7的隐藏
                } else if (selectedTrend === "7-14") {
                    if (trendDays < 8 || trendDays > 14) return false;  // 7-14天：实际抓取 8~14天
                } else if (selectedTrend === "14-30") {
                    if (trendDays < 15 || trendDays > 30) return false; // 14-30天：实际抓取 15~30天
                } else if (selectedTrend === "30_in") {
                    if (trendDays > 30) return false;     // 30天内：大集合！0~30天都显示，大于30的隐藏
                } else if (selectedTrend === "30-59") {
                    if (trendDays < 31 || trendDays > 59) return false; // 30-59天：实际抓取 31~59天
                } else if (selectedTrend === "60") {
                    if (trendDays < 60) return false;   // 至少60天：本地长期历史超过60天也保留
                }
            }
            return true;
        }
    );
    $('#typeFilter, #categoryFilter, #packTagFilter, #modCategoryFilter, #modFilter, #trendFilter, #categoryExclude, #packTagExclude, #modCategoryExclude, #modExclude').on('change', function() {
        if (table) table.draw();
    });
    // 表格重绘时，同步更新顶部的总条数统计及画廊卡片
    $('#modpackTable').on('draw.dt', function() {
        var tbl = window.table;
        if (!tbl && $.fn.DataTable && $.fn.DataTable.isDataTable('#modpackTable')) {
            tbl = $('#modpackTable').DataTable();
        }
        var info = tbl ? tbl.page.info() : { recordsDisplay: (window.tableRowsData ? window.tableRowsData.length : 1484) };
        $('#statTotal').text(info.recordsDisplay);
        $('#mcmodMatchedCount').text(info.recordsDisplay);
        $('#mcmodCardCountBadge').text(info.recordsDisplay + ' 款');
        if (activeMcmodVMode === 'cards') {
            renderMcmodCards();
        }
        /* ★ [v10.0] 高亮当前被激活筛选的标签 */
        var $wrap = $('#modpackTable_wrapper');
        $wrap.find('.tag-cat, .tag-pack, .tag-mod').removeClass('active-tag exclude-active-tag');
        var activeCat = $('#categoryFilter').val() || [];
        if (!Array.isArray(activeCat)) activeCat = activeCat ? [activeCat] : [];
        if (activeCat.length) {
            $wrap.find('.tag-cat').filter(function() { return activeCat.indexOf(($(this).attr('data-tag') || '').trim()) >= 0; }).addClass($('#categoryExclude').is(':checked') ? 'exclude-active-tag' : 'active-tag');
        }
        var activePack = $('#packTagFilter').val() || [];
        if (!Array.isArray(activePack)) activePack = activePack ? [activePack] : [];
        if (activePack.length) {
            $wrap.find('.tag-pack').filter(function() { return activePack.indexOf(($(this).attr('data-tag') || '').trim()) >= 0; }).addClass($('#packTagExclude').is(':checked') ? 'exclude-active-tag' : 'active-tag');
        }
        var activeMod = $('#modFilter').val() || [];
        if (!Array.isArray(activeMod)) activeMod = activeMod ? [activeMod] : [];
        if (activeMod.length) {
            $wrap.find('.tag-mod').filter(function() { return activeMod.indexOf(($(this).attr('data-mod') || '').trim()) >= 0; }).addClass($('#modExclude').is(':checked') ? 'exclude-active-tag' : 'active-tag');
        }
    });
    // 一键重置所有筛选条件
    $('#resetFilters').on('click', function() {
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
    });

    // ★ 首屏极速初始化：定义完成后立即检查，如果数据就绪且为表格模式，立即构建表格！
    if (window.tableRowsData && window.tableRowsData.length) {
        if (!$.fn.DataTable.isDataTable('#modpackTable') && activeMcmodVMode === 'table') {
            window.initMcmodTable();
        }
    }
    /* ═══════ 整合包介绍预览 ═══════ */
    var descData = window.descData || {};
    var feedbackUrl = "https://feedback.suifracti.cn/";
    // 评论详情拆为同目录按需脚本，避免 Windows 首次打开时解析全部评论。
    var commentData = {};
    var commentLoadJobs = {};
    var commentApiBase = "__COMMENT_API_BASE__";
    var compareData = window.compareData || {};
    var modDetailData = {};
    var modDetailLoadJobs = {};
    window.compareData = compareData;
    window.modDetailData = modDetailData;
    window.__registerModDetailData = function(mid, payload) { modDetailData[String(mid)] = payload || []; };
    function loadModDetailData(mid) {
        if (modDetailData[mid]) return Promise.resolve(modDetailData[mid]);
        if (modDetailLoadJobs[mid]) return modDetailLoadJobs[mid];
        modDetailLoadJobs[mid] = new Promise(function(resolve) {
            var script = document.createElement('script');
            script.src = 'data/mods/' + encodeURIComponent(mid) + '.js';
            script.onload = function() { resolve(modDetailData[mid] || []); script.remove(); };
            script.onerror = function() { resolve([]); script.remove(); };
            document.head.appendChild(script);
        }).finally(function() { delete modDetailLoadJobs[mid]; });
        return modDetailLoadJobs[mid];
    }
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
    var hoverCooldowns = {};
    var descHoverPopupEnabled = localStorage.getItem('desc-hover-popup-enabled') !== '0';
    var commentHoverPopupEnabled = localStorage.getItem('comment-hover-popup-enabled') === '1';
    var activeDescKey = '';
    var activeCommentKey = '';
    var activeTrendKey = '';
    $('#compareTray, #compareOverlay').appendTo(document.body);
    var favoriteKey = 'mcmod-compare-favorites-v1';
    var favoriteIds = [];
    try {
        favoriteIds = JSON.parse(localStorage.getItem(favoriteKey) || '[]').filter(function(mid) { return compareData[mid]; });
    } catch(e) {
        favoriteIds = [];
    }
    function saveFavorites() {
        favoriteIds = favoriteIds.filter(function(mid, idx, arr) { return compareData[mid] && arr.indexOf(mid) === idx; });
        localStorage.setItem(favoriteKey, JSON.stringify(favoriteIds));
    }
    function compactTitle(item) {
        return (item && (item.title_cn || item.title || item.mid)) || '';
    }
    function updateFavoriteStars() {
        $('.fav-star').each(function() {
            var mid = String($(this).data('mid') || '');
            $(this).toggleClass('active', favoriteIds.indexOf(mid) >= 0)
                   .attr('title', favoriteIds.indexOf(mid) >= 0 ? '已收藏，点击取消' : '收藏用于对比');
        });
    }
    function updateCompareTray() {
        saveFavorites();
        updateFavoriteStars();
        var selected = favoriteIds.map(function(mid) { return compareData[mid]; }).filter(Boolean);
        $('#compareTrayCount').text(selected.length + ' 个整合包');
        $('#compareTrayNames').html(selected.slice(0, 8).map(function(item) {
            return '<span class="compare-mini-chip">' + escHtml(compactTitle(item), true) + '</span>';
        }).join('') + (selected.length > 8 ? '<span class="compare-mini-chip">+' + (selected.length - 8) + '</span>' : ''));
        $('#compareTray').toggleClass('show', selected.length > 0);
        $('#compareOpen').prop('disabled', selected.length < 2).attr('title', selected.length < 2 ? '至少收藏 2 个整合包才能对比' : '打开全面对比');
    }
    function numFmt(n) {
        n = Number(n || 0);
        if (n >= 100000000) return (n / 100000000).toFixed(1).replace(/\.0$/, '') + '亿';
        if (n >= 10000) return (n / 10000).toFixed(1).replace(/\.0$/, '') + '万';
        return String(n);
    }
    function listNames(arr, limit) {
        arr = arr || [];
        if (!arr.length) return '<span class="compare-chip">无</span>';
        return arr.slice(0, limit || 80).map(function(x) {
            var name = typeof x === 'string' ? x : x.name;
            return '<span class="compare-chip">' + escHtml(name || '', true) + '</span>';
        }).join('') + (arr.length > (limit || 80) ? '<span class="compare-chip">+' + (arr.length - (limit || 80)) + '</span>' : '');
    }
    function setIntersection(listOfSets) {
        if (!listOfSets.length) return [];
        var base = Array.from(listOfSets[0]);
        return base.filter(function(x) { return listOfSets.every(function(s) { return s.has(x); }); }).sort();
    }
    function setUnion(listOfSets) {
        var out = new Set();
        listOfSets.forEach(function(s) { s.forEach(function(x) { out.add(x); }); });
        return Array.from(out).sort();
    }
    function renderCompare() {
        var selected = favoriteIds.map(function(mid) { return compareData[mid]; }).filter(Boolean);
        if (selected.length < 2) return;
        var modSets = selected.map(function(item) { return new Set((item.mods || []).map(function(m) { return (typeof m === 'string' ? m : (m.name || '')).toLowerCase(); })); });
        var modNameMap = {};
        selected.forEach(function(item) {
            (item.mods || []).forEach(function(m) { var name = typeof m === 'string' ? m : (m.name || ''); modNameMap[name.toLowerCase()] = name; });
        });
        var commonMods = setIntersection(modSets).map(function(k) { return modNameMap[k] || k; });
        var allMods = setUnion(modSets);
        var tagSets = selected.map(function(item) { return new Set([].concat(item.categories || [], item.tags || [])); });
        var commonTags = setIntersection(tagSets);
        var typeLine = selected.map(function(item) { return item.type || '未标明'; });
        var html = '';
        html += '<div class="compare-grid">';
        selected.forEach(function(item) {
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
        });
        html += '</div>';
        html += '<div class="compare-section"><h3>共有模组 · ' + commonMods.length + '</h3><div class="compare-chip-cloud">' + listNames(commonMods, 120) + '</div></div>';
        html += '<div class="compare-section"><h3>共有分类/标签 · ' + commonTags.length + '</h3><div class="compare-chip-cloud">' + listNames(commonTags, 120) + '</div></div>';
        html += '<div class="compare-section"><h3>各包独有模组</h3><div class="compare-columns">';
        selected.forEach(function(item, idx) {
            var unique = (item.mods || []).filter(function(m) {
                var key = (typeof m === 'string' ? m : (m.name || '')).toLowerCase();
                return modSets.filter(function(s) { return s.has(key); }).length === 1;
            }).map(function(m) { return typeof m === 'string' ? m : m.name; });
            html += '<div class="compare-card"><h3>' + escHtml(compactTitle(item), true) + ' · ' + unique.length + '</h3><div class="compare-chip-cloud">' + listNames(unique, 120) + '</div></div>';
        });
        html += '</div></div>';
        html += '<div class="compare-section"><h3>模组差异矩阵 · ' + allMods.length + '</h3><div class="compare-table-wrap"><table class="compare-table"><thead><tr><th>模组</th>';
        selected.forEach(function(item) { html += '<th>' + escHtml(compactTitle(item), true) + '</th>'; });
        html += '</tr></thead><tbody>';
        allMods.forEach(function(key) {
            html += '<tr><td>' + escHtml(modNameMap[key] || key, true) + '</td>';
            modSets.forEach(function(s) { html += s.has(key) ? '<td class="compare-hit">●</td>' : '<td class="compare-miss">○</td>'; });
            html += '</tr>';
        });
        html += '</tbody></table></div></div>';
        html += '<div class="compare-section"><h3>分类/标签差异矩阵</h3><div class="compare-table-wrap"><table class="compare-table"><thead><tr><th>分类/标签</th>';
        selected.forEach(function(item) { html += '<th>' + escHtml(compactTitle(item), true) + '</th>'; });
        html += '</tr></thead><tbody>';
        setUnion(tagSets).forEach(function(tag) {
            html += '<tr><td>' + escHtml(tag, true) + '</td>';
            tagSets.forEach(function(s) { html += s.has(tag) ? '<td class="compare-hit">●</td>' : '<td class="compare-miss">○</td>'; });
            html += '</tr>';
        });
        html += '</tbody></table></div></div>';
        $('#compareBody').html(html);
        $('#compareOverlay').addClass('show').attr('aria-hidden', 'false');
    }
    $(document).off('click.compareFav').on('click.compareFav', '.fav-star', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var mid = String($(this).data('mid') || '');
        if (!compareData[mid]) return;
        var idx = favoriteIds.indexOf(mid);
        if (idx >= 0) favoriteIds.splice(idx, 1);
        else favoriteIds.push(mid);
        updateCompareTray();
    });
    $('#modpackTable').on('draw.dt', updateFavoriteStars);
    $('#compareClear').on('click', function() { favoriteIds = []; updateCompareTray(); });
    $('#compareOpen').on('click', renderCompare);
    $('#compareClose, #compareOverlay').on('click', function(e) {
        if (e.target === this) $('#compareOverlay').removeClass('show').attr('aria-hidden', 'true');
    });
    $('#compareCopy').on('click', function() {
        var selected = favoriteIds.map(function(mid) { return compareData[mid]; }).filter(Boolean);
        var text = selected.map(function(item) {
            return compactTitle(item) + ' | 模组 ' + (item.mods || []).length + ' | 流行 ' + item.score + ' | 浏览 ' + item.views;
        }).join('\n');
        if (navigator.clipboard) navigator.clipboard.writeText(text);
    });
    updateCompareTray();
    function isHoverCooling(key) {
        return key && hoverCooldowns[key] && hoverCooldowns[key] > Date.now();
    }
    function setHoverCooldown(key) {
        if (key) hoverCooldowns[key] = Date.now() + HOVER_COOLDOWN_MS;
    }
    function getCommentUrl(url) {
        var clean = (url || 'https://www.mcmod.cn/').split('#')[0];
        return clean;
    }
    function escAttrJs(str) {
        return escHtml(str || '', true).replace(/<br>/g, '&#10;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }
    function getSingleCommentUrl(c) {
        if (c && (c.comment_url || c.url || c.href || c.link)) {
            return c.comment_url || c.url || c.href || c.link;
        }
        return '';
    }
    function commentOriginMeta(c, localIndex) {
        return '';
    }
    function getDescText(desc) {
        if (!desc) return '';
        if (typeof desc === 'string') return desc;
        return desc.text || desc.desc || '';
    }
    function getDescImages(desc) {
        if (!desc || typeof desc === 'string') return [];
        if (Array.isArray(desc.images) && desc.images.length) return desc.images;
        if (Array.isArray(desc.intro_images) && desc.intro_images.length) return desc.intro_images;
        return [];
    }
    function normalizeImageUrlJs(url) {
        if (!url) return '';
        try { return new URL(url, window.location.href).href; } catch(e) {
            if (String(url).indexOf('//') === 0) return 'https:' + url;
            return String(url);
        }
    }
    function isAvatarImage(img) {
        if (img && String(img.kind || '').toLowerCase() === 'avatar') return true;
        var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
        var url = normalizeImageUrlJs(raw).toLowerCase();
        return url.indexOf('/user/avatar/') >= 0 || url.indexOf('/identicons/') >= 0 || url.indexOf('@60x60') >= 0;
    }
    function isEmotionImage(img) {
        if (img && String(img.kind || '').toLowerCase() === 'emotion') return true;
        var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
        var url = normalizeImageUrlJs(raw).toLowerCase();
        return url.indexOf('/emotion/images/') >= 0 || url.indexOf('/dialogs/emotion/') >= 0;
    }
    function filterGalleryImages(images) {
        if (!Array.isArray(images)) return [];
        return images.filter(function(img) { return !isAvatarImage(img) && !isEmotionImage(img); });
    }
    function filterEmotionImages(images) {
        if (!Array.isArray(images)) return [];
        return images.filter(function(img) { return isEmotionImage(img); });
    }
    function renderInlineEmotions(images) {
        var emos = filterEmotionImages(images);
        if (!emos.length) return '';
        var html = '<span class="inline-emotions">';
        emos.forEach(function(img, idx) {
            var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
            var url = normalizeImageUrlJs(raw);
            if (!url) return;
            html += '<img class="inline-emotion" src="' + escAttrJs(url) + '" alt="表情" loading="lazy">';
        });
        html += '</span>';
        return html;
    }
    function renderImageGallery(images, extraClass) {
        images = filterGalleryImages(images);
        if (!Array.isArray(images) || !images.length) return '';
        var html = '<div class="image-gallery ' + (extraClass || '') + '">';
        images.forEach(function(img, idx) {
            var raw = (typeof img === 'string') ? img : (img.url || img.src || '');
            var url = normalizeImageUrlJs(raw);
            if (!url || /loading|loadfail/i.test(url)) return;
            var alt = (typeof img === 'string') ? '' : (img.alt || img.title || '');
            var caption = alt || ('图片 ' + (idx + 1));
            html += '<a class="image-thumb" href="' + escAttrJs(url) + '" target="_blank" rel="noreferrer" title="' + escAttrJs(caption) + '">';
            html += '<img src="' + escAttrJs(url) + '" alt="' + escAttrJs(caption) + '" loading="lazy">';
            html += '<span class="image-caption">' + escHtml(caption, true) + '</span></a>';
        });
        html += '</div>';
        return html;
    }
    function splitIntroImages(images) {
        var cover = [];
        var rest = [];
        (images || []).forEach(function(img) {
            var source = (img && img.source ? String(img.source).toLowerCase() : '');
            if (source === 'cover') cover.push(img);
            else rest.push(img);
        });
        return { cover: cover, rest: rest };
    }
    function sectionKeyFromText(text) {
        var s = String(text || '').replace(/\s+/g, '');
        if (!s) return '';
        if (s.indexOf('任务截图') >= 0 || s.indexOf('游戏截图') >= 0 || s.indexOf('截图') >= 0 || s.indexOf('图片') >= 0) return 'screenshots';
        if (s.indexOf('使用') >= 0) return 'usage';
        if (s.indexOf('介绍') >= 0 || s.indexOf('简介') >= 0) return 'intro';
        return '';
    }
    function imageSectionKey(img) {
        var s = ((img && (img.section || img.heading || img.alt || img.title)) || '').replace(/\s+/g, '');
        return sectionKeyFromText(s);
    }
    function renderDescHtml(desc, images, keyword) {
        var splitImages = splitIntroImages(images || []);
        var textHtml = '';
        if (desc) {
            if (keyword && desc.toLowerCase().indexOf(keyword.toLowerCase()) !== -1) {
                textHtml = '<div class="pv-para">' + highlightText(desc, keyword) + '</div>';
            } else {
                // 介绍正文需要段落排版，这里要的是排版器而非纯转义
                textHtml = formatDescHtml(desc);
            }
        }
        var coverHtml = splitImages.cover.length ? '<div class="pv-cover-wrap">' + renderImageGallery(splitImages.cover, 'pv-cover-gallery') + '</div>' : '';
        var rest = splitImages.rest;
        if (!rest.length) return coverHtml + textHtml;

        var used = new Set();
        var $box = $('<div>' + textHtml + '</div>');
        $box.children().each(function() {
            var key = sectionKeyFromText($(this).text());
            if (!key) return;
            var group = rest.filter(function(img, idx) {
                return !used.has(idx) && (imageSectionKey(img) === key || (!imageSectionKey(img) && key === 'screenshots'));
            });
            if (group.length) {
                group.forEach(function(img) { used.add(rest.indexOf(img)); });
                $(this).after(renderImageGallery(group, 'pv-image-gallery section-bound'));
            }
        });
        var leftovers = rest.filter(function(img, idx) { return !used.has(idx); });
        return coverHtml + $box.html() + renderImageGallery(leftovers, 'pv-image-gallery');
    }
    $(document).on('click', '.mcmod-consent-ok', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).closest('.pv-popup, .comment-popup').removeClass('needs-consent');
    });
    function openImageLightbox(url, title) {
        url = normalizeImageUrlJs(url);
        if (!url) return;
        $('#imageLightboxImg').attr('src', url).attr('alt', title || '');
        $('#imageLightboxTitle').text(title || '图片预览');
        $('#imageLightboxOpen').attr('href', url);
        $('#imageLightbox').addClass('show').attr('aria-hidden', 'false');
    }
    function closeImageLightbox() {
        $('#imageLightbox').removeClass('show').attr('aria-hidden', 'true');
        $('#imageLightboxImg').attr('src', '');
    }
    var coverHoverPreviewTimer = null;
    $(document).on('mouseenter', '.modpack-cover-thumb', function() {
        var $thumb = $(this);
        clearTimeout(coverHoverPreviewTimer);
        coverHoverPreviewTimer = setTimeout(function() {
            openImageLightbox($thumb.data('image-url') || $thumb.attr('href'), $thumb.attr('title') || '封面预览');
        }, 1000);
    });
    $(document).on('mouseleave', '.modpack-cover-thumb', function() {
        clearTimeout(coverHoverPreviewTimer);
        coverHoverPreviewTimer = null;
    });
    $(document).on('click', '.image-thumb', function(e) {
        e.preventDefault();
        e.stopPropagation();
        clearTimeout(coverHoverPreviewTimer);
        openImageLightbox($(this).attr('href') || $(this).data('image-url'), $(this).attr('title') || $(this).find('.image-caption').text());
    });
    $('#imageLightboxClose, #imageLightbox').on('click', function(e) {
        if (e.target === this) closeImageLightbox();
    });
    function showDescPopup($link) {
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

        if (desc || descImages.length) {
            var keyword = (typeof getActiveSearchQuery === 'function') ? getActiveSearchQuery() : '';
            $pvBody.html(renderDescHtml(desc, descImages, keyword));
        } else {
            $pvBody.html('<div class="pv-body-empty">暂无更多图文介绍<div><a href="' + url + '" target="_blank" rel="noreferrer">在新标签页中安全访问原页面 ↗</a></div></div>');
        }
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
        $popup.css({ top: top, left: left });
    }
    function hideDescPopup() {
        $popup.removeClass('show').attr('aria-hidden', 'true');
    }
    function escapeRegExp(str) {
        if (!str) return "";
        // 1. 先把反斜杠转义（必须最先执行）
        str = str.split('\\').join('\\\\');
        // 2. 逐个将其他正则敏感元字符转义
        var specials = ['/', '^', '$', '*', '+', '?', '.', '(', ')', '|', '[', ']', '{', '}', '-'];
        for (var i = 0; i < specials.length; i++) {
            var c = specials[i];
            str = str.split(c).join('\\' + c);
        }
        return str;
    }
    function highlightText(str, keyword) {
        var escaped = escHtml(str, true);
        if (!keyword) return escaped;
        var cleanKeyword = keyword.trim();
        if (!cleanKeyword) return escaped;
        var escapedKeyword = escHtml(cleanKeyword, true);
        if (!escapedKeyword) return escaped;
        try {
            var regex = new RegExp('(' + escapeRegExp(escapedKeyword) + ')', 'gi');
            return escaped.replace(regex, '<mark class="comment-highlight">$1</mark>');
        } catch(e) {
            return escaped;
        }
    }
    /* 这个函数实际是「介绍正文排版器」：把纯文本按行重组，并套上
       <div class="pv-para"> / <blockquote> / pv-section-title 等块级标签，供介绍抽屉使用。
       它原先也叫 escHtml，与前面那个纯转义函数同名 —— JS 里同名函数后声明者覆盖前者，
       于是全页所有"以为在转义"的调用实际都在插 HTML：用在 title="..." 这类属性位置时
       引号会被内层标签冲断，整行 HTML 被当文本吐到页面上。
       现改为独立命名，只有真正需要段落排版的介绍渲染才调用它。 */
    function formatDescHtml(str, noFormat) {
    if (str === null || str === undefined) return "";
    var d = document.createElement('div');
        d.textContent = str;
        var raw = d.innerHTML;
        var LF = String.fromCharCode(10);
        var CR = String.fromCharCode(13);
        var text = raw.split(CR + LF).join(LF).split(CR).join(LF);
        if (noFormat) {
            return text.split(LF).join('<br>');
        }
        var lines = text.split(LF);
        var html = '';
        var currentPara = [];
        var currentQuote = [];
        function flushPara() {
            if (currentPara.length > 0) {
                html += '<div class="pv-para">' + currentPara.join('<br>') + '</div>';
                currentPara = [];
            }
        }
        function flushQuote() {
            if (currentQuote.length > 0) {
                html += '<blockquote class="intro-blockquote">' + currentQuote.join('<br>') + '</blockquote>';
                currentQuote = [];
            }
        }
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i].trim();
            if (!line) {
                flushPara();
                flushQuote();
                continue;
            }
            var firstChar = line.charAt(0);
            var isQuote = firstChar === '|' || firstChar === '>';
            if (isQuote) {
                flushPara();
                var quoteContent = line.substring(1).trim();
                currentQuote.push(quoteContent);
                continue;
            } else {
                flushQuote();
            }
            var isList = false;
            var listContent = line;
            if (firstChar === '-' || firstChar === '*' || firstChar === '•' || /^\d+\.\s/.test(line)) {
                isList = true;
                listContent = line.replace(/^[-*•\s]+|^\d+\.\s+/, '');
            } else {
                var colonMatch = line.match(/^([^，。！、；：:]{2,15})[：:]/);
                if (colonMatch) {
                    isList = true;
                    listContent = '<strong>' + colonMatch[1] + ': </strong>' + line.substring(colonMatch[0].length).trim();
                }
            }
            var isTitle = false;
            if (!isList) {
                var isShort = line.length <= 25;
                var hasPunctuation = /[，。！、；]/.test(line);
                var lastChar = line.slice(-1);
                if ((isShort && !hasPunctuation && !lastChar.match(/[。！；]/)) || lastChar === ':' || lastChar === '：' || line.indexOf('——') >= 0) {
                    isTitle = true;
                }
            }
            if (isList) {
                flushPara();
                html += '<div class="pv-list-item">' + listContent + '</div>';
            } else if (isTitle) {
                flushPara();
                html += '<div class="pv-section-title">' + line + '</div>';
            } else {
                currentPara.push(line);
            }
        }
        flushPara();
        flushQuote();
        return html || text.split(LF).join('<br>');
    }
    var cmtPerPage = 8;
    var cmtCurrentPage = 1;
    var cmtTotalPages = 1;
    var cmtCurrentData = null;
    var cmtTargetIndex = -1;
    var activeCommentCell = null;
    var cmtSearchMatches = [];
    var cmtSearchMatchPointer = -1;
    function renderCommentPage(page) {
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
        for (var i = start; i < end; i++) {
            var c = comments[i];
            var isActiveMatch = (cmtSearchMatchPointer >= 0 && i === cmtSearchMatches[cmtSearchMatchPointer]);
            html += '<div class="comment-floor' + (isActiveMatch ? ' matched-active' : '') + '" data-comment-index="' + i + '">';
            html += '<div class="comment-floor-head">';
            html += '<div class="comment-floor-main">';
            if (c.floor) {
                html += '<span class="floor-num">第 ' + c.floor + ' 楼</span> ';
            }
            var originMeta = commentOriginMeta(c, i);
            html += highlightText(c.author || '', keyword) + (originMeta ? '<span class="comment-origin-meta">' + originMeta + '</span>' : '') + '</div>';
            html += '</div>';
            html += '<div class="comment-floor-text">' + highlightText(c.text || '', keyword) + renderInlineEmotions(c.images || []) + '</div>';
            html += renderImageGallery(c.images || [], 'comment-image-gallery');
            if (c.replies && c.replies.length > 0) {
                c.replies.forEach(function(r) {
                    html += '<div class="comment-reply">';
                    html += '<div class="comment-reply-head"><span>' + highlightText(r.author || '', keyword) + '</span>';
                    html += '</div>';
                    html += '<div class="comment-reply-text">' + highlightText(r.text || '', keyword) + renderInlineEmotions(r.images || []) + '</div>';
                    html += renderImageGallery(r.images || [], 'comment-image-gallery');
                    html += '</div>';
                });
            }
            html += '</div>';
        }
        $cBody.html(html);
        $cBody.scrollTop(0); // 确保翻页后滚动条滑回最上方，极大地改善了翻页可读性
        if (cmtTargetIndex >= start && cmtTargetIndex < end) {
            setTimeout(function() {
                var target = $cBody.find('[data-comment-index="' + cmtTargetIndex + '"]')[0];
                if (target) $cBody.scrollTop(Math.max(0, target.offsetTop - 14));
                cmtTargetIndex = -1;
            }, 30);
        }
        // 更新分页栏
        var $bar = $('#commentPageBar');
        var $info = $('#cmtPageInfo');
        var $first = $('#cmtFirst');
        var $prev = $('#cmtPrev');
        var $next = $('#cmtNext');
        var $last = $('#cmtLast');
        if (cmtTotalPages > 1) {
            $bar.show();
            $info.text('第 ' + page + ' / ' + cmtTotalPages + ' 页');
            $first.removeClass('disabled').addClass(page <= 1 ? 'disabled' : '');
            $prev.removeClass('disabled').addClass(page <= 1 ? 'disabled' : '');
            $next.removeClass('disabled').addClass(page >= cmtTotalPages ? 'disabled' : '');
            $last.removeClass('disabled').addClass(page >= cmtTotalPages ? 'disabled' : '');
        } else {
            $bar.hide();
        }
        repositionCommentPopup();
    }
    /* ─── 智能高度监测系统工具方法 ─── */
    // 【1. 统一变量绑定的高度测算方法】
    function checkCommentOverflow() {
        // 使用 setTimeout 延迟 25 毫秒，确保 DOM 节点完全重绘重排完毕，拿取绝对真实高度
        setTimeout(function() {
            if ($cBody[0]) {
                // 🌟 引入 8 像素溢出容差缓冲区，彻底规避小数像素四舍五入和滚动边距带来的误差
                var hasScroll = $cBody[0].scrollHeight > ($cBody.innerHeight() + 8);
                if (hasScroll) {
                    $cpopup.addClass('has-overflow'); // 激活“滚动查看更多”胶囊
                } else {
                    $cpopup.removeClass('has-overflow');
                }
            }
        }, 25);
    }
    // 【2. 修正：直接绑定到局部容器，并支持滑回顶部时恢复提示】
    $('#commentBody').on('scroll', function() {
        var scrollTop = $(this).scrollTop();
        if (scrollTop > 15) {
            // 向下滑动超过 15px，说明用户已经发现并开始阅读，优雅隐藏提示
            $cpopup.removeClass('has-overflow');
        } else if (scrollTop <= 5) {
            // 如果用户又滑回了最顶部，且内容依然是超长的，把提示重新亮起来引导
            if (this.scrollHeight > $(this).innerHeight()) {
                $cpopup.addClass('has-overflow');
            }
        }
    });
    // 【3. 翻页控制】：点击各翻页按钮后安全触发重新判定
    $('#cmtFirst').on('click', function(e) {
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage > 1) {
            renderCommentPage(1);
            checkCommentOverflow();
        }
    });
    $('#cmtPrev').on('click', function(e) {
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage > 1) {
            renderCommentPage(cmtCurrentPage - 1);
            checkCommentOverflow();
        }
    });
    $('#cmtNext').on('click', function(e) {
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage < cmtTotalPages) {
            renderCommentPage(cmtCurrentPage + 1);
            checkCommentOverflow();
        }
    });
    $('#cmtLast').on('click', function(e) {
        e.stopPropagation();
        clearTimeout(commentHoverTimer); // ★ 防秒退保护
        if (cmtCurrentPage < cmtTotalPages) {
            renderCommentPage(cmtTotalPages);
            checkCommentOverflow();
        }
    });
    // 搜索匹配项跳转控制
    $(document).on('click', '#searchNavNext', function(e) {
        e.stopPropagation();
        if (!cmtSearchMatches || cmtSearchMatches.length === 0) return;
        cmtSearchMatchPointer = (cmtSearchMatchPointer + 1) % cmtSearchMatches.length;
        var targetIndex = cmtSearchMatches[cmtSearchMatchPointer];
        var targetPage = Math.floor(targetIndex / cmtPerPage) + 1;
        cmtTargetIndex = targetIndex;
        $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 ' + (cmtSearchMatchPointer + 1) + ' 条)');
        renderCommentPage(targetPage);
        checkCommentOverflow();
    });
    $(document).on('click', '#searchNavPrev', function(e) {
        e.stopPropagation();
        if (!cmtSearchMatches || cmtSearchMatches.length === 0) return;
        cmtSearchMatchPointer = (cmtSearchMatchPointer - 1 + cmtSearchMatches.length) % cmtSearchMatches.length;
        var targetIndex = cmtSearchMatches[cmtSearchMatchPointer];
        var targetPage = Math.floor(targetIndex / cmtPerPage) + 1;
        cmtTargetIndex = targetIndex;
        $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 ' + (cmtSearchMatchPointer + 1) + ' 条)');
        renderCommentPage(targetPage);
        checkCommentOverflow();
    });
    function repositionCommentPopup() {
        if (!$cpopup.hasClass('show') || !activeCommentCell) return;
        var rect = activeCommentCell[0].getBoundingClientRect();
        var cellW = activeCommentCell.outerWidth();
        var vw = window.innerWidth;
        var vh = window.innerHeight;
        var safeTop = 24;
        var safeBottom = 24;
        var fixedHeight = Math.min(720, Math.max(420, vh - safeTop - safeBottom));
        $cpopup.css({
            height: fixedHeight + 'px',
            'max-height': fixedHeight + 'px'
        });
        $cBody.css('max-height', 'none');
        var ph = fixedHeight;
        var top = rect.top - ph - 10;
        // 如果上方放不下，则尝试放在下方
        if (top < safeTop) {
            top = rect.bottom + 10;
        }
        // 如果下方穿出了浏览器底部，则向上推起，将底部固定在 vh - safeBottom 位置，顶部向上延伸
        if (top + ph > vh - safeBottom) {
            top = Math.max(safeTop, vh - safeBottom - ph);
        }
        var pw = $cpopup.outerWidth();
        var left = rect.left + cellW / 2 - pw / 2;
        // 水平 clamp 锁定
        if (left + pw > vw - 12) left = vw - pw - 12;
        if (left < 12) left = 12;
        $cpopup.css({
            top: top + 'px',
            bottom: 'auto',
            left: left
        });
    }
    function lockCommentPopupSize() {
        var vh = window.innerHeight;
        var fixedHeight = Math.min(720, Math.max(420, vh - 48));
        $cpopup.css({ height: fixedHeight + 'px', 'max-height': fixedHeight + 'px' });
        $cBody.css('max-height', 'none');
    }
    function isCommentHoverAlive() {
        var overPopup = $cpopup.is(':hover');
        var overCell = activeCommentCell && activeCommentCell.length && activeCommentCell.is(':hover');
        return !!(overPopup || overCell);
    }
    function scheduleCommentHide(delay) {
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {
            if (isCommentHoverAlive()) return;
            hideCommentPopup();
            $('body').css({ 'overflow': '', 'height': '' });
        }, delay || 120);
    }
    // 【4. 弹窗主渲染逻辑】：渲染完数据并全部定位成功后，激活检测
    function commentSearchMatches(comments, keyword) {
        var matches = [];
        keyword = String(keyword || '').trim().toLowerCase();
        if (!keyword || !comments) return matches;
        for (var i = 0; i < comments.length; i++) {
            var c = comments[i] || {};
            var match = String(c.author || '').toLowerCase().indexOf(keyword) !== -1 ||
                        String(c.text || '').toLowerCase().indexOf(keyword) !== -1;
            (c.replies || []).forEach(function(r) {
                if (String(r.author || '').toLowerCase().indexOf(keyword) !== -1 ||
                    String(r.text || '').toLowerCase().indexOf(keyword) !== -1) match = true;
            });
            if (match) matches.push(i);
        }
        return matches;
    }
    function applyCommentSearch() {
        if (!cmtCurrentData || !cmtCurrentData.comments) return;
        cmtSearchMatches = commentSearchMatches(cmtCurrentData.comments, $('#commentSearchInput').val());
        cmtSearchMatchPointer = cmtSearchMatches.length ? 0 : -1;
        cmtTargetIndex = cmtSearchMatches.length ? cmtSearchMatches[0] : -1;
        if (cmtSearchMatches.length) {
            $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 1 条)');
            $('#commentSearchNav').show();
            renderCommentPage(Math.floor(cmtTargetIndex / cmtPerPage) + 1);
        } else {
            $('#commentSearchNav').hide();
            renderCommentPage(1);
        }
        checkCommentOverflow();
    }
    $('#commentSearchInput').on('input', function() { applyCommentSearch(); });
    window.__registerCommentData = function(mid, payload) { commentData[String(mid)] = payload || { comments: [] }; };
    function loadCommentData(mid) {
        if (commentData[mid]) return Promise.resolve(commentData[mid]);
        if (commentLoadJobs[mid]) return commentLoadJobs[mid];
        commentLoadJobs[mid] = new Promise(function(resolve) {
            var script = document.createElement('script');
            script.src = 'data/comments/' + encodeURIComponent(mid) + '.js';
            script.onload = function() { resolve(commentData[mid] || null); script.remove(); };
            script.onerror = function() { console.warn('评论数据加载失败:', mid); resolve(null); script.remove(); };
            document.head.appendChild(script);
        }).finally(function() { delete commentLoadJobs[mid]; });
        return commentLoadJobs[mid];
    }
    function showCommentPopup($cell) {
        var mid = String($cell.data('mid') || '');
        activeCommentCell = $cell;
        activeCommentKey = 'comment:' + mid;
        if (isHoverCooling(activeCommentKey)) return;
        if (commentData[mid]) {
            renderCommentPopup($cell, commentData[mid]);
            return;
        }
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
        loadCommentData(mid).then(function(cdata) {
            if (!activeCommentCell || !activeCommentCell.is($cell)) return;
            renderCommentPopup($cell, cdata);
        });
    }
    function renderCommentPopup($cell, cdata) {
        activeCommentCell = $cell;
        var mid = $cell.data('mid') || '';
        activeCommentKey = 'comment:' + mid;
        if (isHoverCooling(activeCommentKey)) return;
        var floorCount = $cell.data('order') || 0;
        var pageCount = (cdata && cdata.page_count) ? cdata.page_count : floorCount;
        // 重置样式，以进行正确的初始测量
        $cpopup.css({
            height: '',
            'min-height': '',
            'max-height': '',
            top: '',
            bottom: '',
            left: ''
        });
        lockCommentPopupSize();
        if (cdata && cdata.comments && cdata.comments.length > 0) {
            var scrapedFloors = cdata.comments.length;
            // 诱饵数据清洗与非逆向计算：直接正向统计回复数
            var scrapedReplies = 0;
            cdata.comments.forEach(function(c) {
                if (c.replies) scrapedReplies += c.replies.length;
            });
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
            if (cmtSearchMatches.length > 0) {
                cmtSearchMatchPointer = 0;
                var targetIndex = cmtSearchMatches[0];
                startPage = Math.floor(targetIndex / cmtPerPage) + 1;
                cmtTargetIndex = targetIndex;
            }
            
            if (cmtSearchMatches.length > 1) {
                $('#searchNavInfo').text('找到 ' + cmtSearchMatches.length + ' 条匹配评论 (当前第 1 条)');
                $('#commentSearchNav').show();
            } else {
                $('#commentSearchNav').hide();
            }
            
            renderCommentPage(startPage);
        } else {
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
        }
        $cpopup.addClass('show');
        repositionCommentPopup();
        // ✨ 完美的咬合节点：弹窗加载和精准坐标偏置完成后，立刻调取判定
        checkCommentOverflow();
    }
    function hideCommentPopup() {
        function clearCommentPopupLayout() {
            $cpopup.css({
                height: '',
                'min-height': '',
                'max-height': '',
                top: '',
                bottom: '',
                left: ''
            });
            $cBody.css('max-height', '');
        }
        if ($cpopup.hasClass('show')) {
            $cpopup.addClass('hiding').removeClass('show');
            setTimeout(function() {
                $cpopup.removeClass('hiding');
                clearCommentPopupLayout();
            }, 180);
        } else {
            $cpopup.removeClass('show hiding');
            clearCommentPopupLayout();
        }
        activeCommentCell = null;
        cmtSearchMatches = [];
        cmtSearchMatchPointer = -1;
    }

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
    function fmtBigNum(n) {
        if (n === null || n === undefined || n === '') return '';
        var v = Number(n);
        if (!isFinite(v)) return String(n);
        if (v >= 100000000) return (v / 100000000).toFixed(2).replace(/\.?0+$/, '') + '亿';
        if (v >= 10000) return (v / 10000).toFixed(1).replace(/\.0$/, '') + '万';
        return v.toLocaleString('zh-CN');
    }

    /* MC 版本支持分布条：把 all_versions 按「大版本族」(1.21 / 1.20 / …) 聚合，
       用条长表达该族下收录了多少个具体版本。
       纯数据呈现 —— 版本全部来自抓取结果，不补全、不推断。
       少于 2 个版本时返回空串（单个版本用条形表达没有信息量）。 */
    function buildMcVersionStrip(versions) {
        if (!versions || !versions.length) return '';
        var uniq = [];
        versions.forEach(function(v) {
            v = String(v == null ? '' : v).trim();
            if (v && uniq.indexOf(v) === -1) uniq.push(v);
        });
        if (uniq.length < 2) return '';
        var fam = {}, order = [];
        uniq.forEach(function(v) {
            var m = v.match(/^(\d+\.\d+)/);
            var key = m ? m[1] : '其它';
            if (!fam[key]) { fam[key] = []; order.push(key); }
            fam[key].push(v);
        });
        order.sort(function(a, b) {
            var pa = a.split('.'), pb = b.split('.');
            return (parseInt(pb[0], 10) || 0) - (parseInt(pa[0], 10) || 0)
                || (parseInt(pb[1], 10) || 0) - (parseInt(pa[1], 10) || 0);
        });
        var maxN = 1;
        order.forEach(function(k) { maxN = Math.max(maxN, fam[k].length); });
        var rows = order.map(function(k) {
            var n = fam[k].length;
            var pct = Math.max(6, Math.round(n / maxN * 100));
            return '<div class="mcver-row" title="' + escHtml(fam[k].join(', '), true) + '">' +
                '<span class="mcver-fam">' + escHtml(k) + '</span>' +
                '<span class="mcver-track"><span class="mcver-fill" style="width:' + pct + '%;"></span></span>' +
                '<span class="mcver-n">' + n + ' 个</span>' +
            '</div>';
        }).join('');
        return '<div class="mcver-strip">' +
            '<div class="mcver-head">🎮 Minecraft 版本支持分布' +
                '<span class="mcver-sub">共 ' + uniq.length + ' 个具体版本 · 按大版本族聚合 · 悬停可看明细</span>' +
            '</div>' + rows + '</div>';
    }

    function openVersionModal(mid, title, ver, date, count, row, extra) {
        extra = extra || {};
        var plat = extra.platform || (mid ? 'mcmod' : 'bilibili');
        if (!mid && !title && !extra.title) return;

        if (!row && mid && window.tableRowsData) {
            for (var i = 0; i < window.tableRowsData.length; i++) {
                if (String(window.tableRowsData[i].mid) === String(mid)) {
                    row = window.tableRowsData[i];
                    break;
                }
            }
        }

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

        if (extra.items && extra.items.length > 0) {
            modalHtml += '<div style="margin-top:20px; border-top:1px solid var(--border-color, rgba(255,255,255,0.1)); padding-top:16px;">' +
                '<h4 style="font-size:1rem; font-weight:700; margin:0 0 12px; color:var(--text);">📜 该整合包关联的全部发布与迭代历史视频 (' + extra.items.length + ' 期)</h4>' +
                '<div style="display:flex; flex-direction:column; gap:10px; max-height:260px; overflow-y:auto; padding-right:6px;">';
            extra.items.forEach(function(it, idx) {
                var isLatest = idx === 0 ? '<span style="background:rgba(251,114,153,0.2); color:#fb7299; border:1px solid rgba(251,114,153,0.3); border-radius:4px; font-size:11px; padding:1px 6px; font-weight:700;">最新发布</span>' : '';
                modalHtml += '<div style="display:flex; align-items:center; justify-content:space-between; background:var(--surface, rgba(255,255,255,0.04)); border:1px solid var(--border, rgba(255,255,255,0.08)); border-radius:8px; padding:10px 12px; gap:10px;">' +
                    '<div style="flex:1; min-width:0;">' +
                        '<div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">' + isLatest + '<span style="font-size:12px; color:var(--text-muted);">' + (it.pub_time || '') + '</span></div>' +
                        '<a href="' + it.url + '" target="_blank" rel="noreferrer" style="font-size:13px; font-weight:700; color:var(--text); text-decoration:none;" title="' + escHtml(it.title) + '">' + escHtml(it.title) + '</a>' +
                    '</div>' +
                    '<a href="' + it.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="font-size:11px; padding:4px 10px; text-decoration:none;">在新窗口观看 ↗</a>' +
                '</div>';
            });
            modalHtml += '</div></div>';
        }

        if (extra.links && extra.links.length > 0) {
            var hasVersionedLinks = false;
            for (var lki = 0; lki < extra.links.length; lki++) {
                if (extra.links[lki] && (extra.links[lki].version || extra.links[lki].label)) {
                    hasVersionedLinks = true;
                    break;
                }
            }

            if (hasVersionedLinks) {
                modalHtml += '<div style="margin-top:20px; border-top:1px solid var(--border-color, rgba(255,255,255,0.1)); padding-top:16px;">' +
                    '<h4 style="font-size:1rem; font-weight:700; margin:0 0 12px; color:var(--text); display:flex; align-items:center; justify-content:space-between;">' +
                        '<span>📦 历史版本发布与下载通道 (' + extra.links.length + ' 个)</span>' +
                        '<span style="font-size:11px; font-weight:500; color:var(--text-muted);">按发布通道与版本号整理 · 点击直达下载</span>' +
                    '</h4>' +
                    '<div style="display:flex; flex-direction:column; gap:8px; max-height:260px; overflow-y:auto; padding-right:4px;">';
                extra.links.forEach(function(l) {
                    if (l && l.url) {
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
                    }
                });
                modalHtml += '</div></div>';
            } else {
                modalHtml += '<div style="margin-top:20px; border-top:1px solid var(--border-color, rgba(255,255,255,0.1)); padding-top:16px;">' +
                    '<h4 style="font-size:1rem; font-weight:700; margin:0 0 12px; color:var(--text);">💾 关联下载与历史资源通道 (' + extra.links.length + ' 个)</h4>' +
                    '<div style="display:flex; flex-wrap:wrap; gap:8px;">';
                extra.links.forEach(function(l) {
                    if (l && l.url) {
                        var lName = (l.name || '直接下载').trim();
                        var vTag = l.version ? ' (' + l.version + ')' : '';
                        modalHtml += '<a href="' + l.url + '" target="_blank" rel="noreferrer" class="bili-pan-btn pan-btn-other" style="font-size:12px; padding:6px 12px; text-decoration:none;">💾 ' + escHtml(lName + vTag) + ' ↗</a>';
                    }
                });
                modalHtml += '</div></div>';
            }
        }

        $vBodyInner.html(modalHtml);
        $vModal.css('display', 'flex');
        setTimeout(function() { $vModal.addClass('show'); }, 10);
    }

    function closeVersionModal() {
        $vModal.removeClass('show');
        setTimeout(function() {
            $vModal.hide();
        }, 220);
    }

    /* 全平台通用悬浮预览与版本模态窗事件绑定 */
    $(document).on('mouseenter', '.js-open-unified-preview', function() {
        showDescPopup($(this));
    }).on('mouseleave', '.js-open-unified-preview', function() {
        hideDescPopup();
    });

    $(document).on('click', '.js-open-plat-version-modal', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var $btn = $(this);
        var plat = $btn.attr('data-platform') || 'bbsmc';
        var key = $btn.attr('data-vkey') || '';
        var p = key ? ((window.__packByUrl || {})[key]) : null;
        if (p) {
            var extra = buildCardModalExtra(plat, p);
            openVersionModal(p.id || p.project_id || p.url, p.title, extra.ver, extra.date, extra.count, null, extra);
            return;
        }
        // 回退：没有索引时（例如数据被外部脚本替换过）仍按 data-* 展示，保证不白屏
        var fallback = {
            platform: plat,
            title: $btn.data('title') || '',
            ver: $btn.data('ver') || '通用 / 最新',
            date: $btn.data('date') || '暂无记录',
            url: $btn.data('url') || '#',
            count: null,
            verLabel: ($btn.data('ver-label')) || undefined,
            typeName: ($btn.data('type')) || undefined
        };
        if (!fallback.typeName) delete fallback.typeName;
        openVersionModal(null, fallback.title, fallback.ver, fallback.date, fallback.count, null, fallback);
    });

    $(document).on('click', '.js-open-bili-group-versions', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var key = $(this).data('group-key');
        var g = window.biliGroupsMap ? window.biliGroupsMap[key] : null;
        if (g) {
            var lab = __CARD_PLAT_LABELS.bilibili || {};
            // 只汇总组内视频真实存在的字段：MC 版本取并集、分类取并集、最早发布时间作首发
            var verSet = [], catSet = [], loaderSet = [], views = 0, earliest = '', modCount = null;
            g.items.forEach(function(it) {
                (it.all_versions || []).forEach(function(v) { if (verSet.indexOf(v) === -1) verSet.push(v); });
                if (it.mc_version && verSet.indexOf(it.mc_version) === -1) verSet.push(it.mc_version);
                (it.categories || []).forEach(function(c) { if (catSet.indexOf(c) === -1) catSet.push(c); });
                (it.loaders || []).forEach(function(l) { if (loaderSet.indexOf(l) === -1) loaderSet.push(l); });
                views += (typeof it.views === 'number' ? it.views : 0);
                if (typeof it.mod_count === 'number' && it.mod_count > 0) {
                    modCount = (modCount === null) ? it.mod_count : Math.max(modCount, it.mod_count);
                }
                if (it.pub_time && (!earliest || it.pub_time < earliest)) earliest = it.pub_time;
            });
            var typeParts = [];
            if (catSet.length) typeParts.push(catSet.map(catLabel).join(' · '));
            if (loaderSet.length) typeParts.push('加载器: ' + loaderSet.map(loaderLabel).join(' · '));
            // mod_count 只有 B站 数据里真的有，有才显示
            if (modCount !== null) typeParts.push('整合包模组数: ' + modCount + ' 款');
            var verText = verSet.length ? verSet.join(' · ') : '未标注版本';
            openVersionModal(null, g.displayTitle, verText, g.latestPubTime, g.items.length, null, {
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
            });
        }
    });


    $(document).on('click', '.js-open-version-modal, .modpack-version-badge', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var $btn = $(this);
        var mid = $btn.data('mid');
        if (!mid) {
            var href = $btn.attr('href') || '';
            var m = href.match(/version\/([0-9]+)/);
            if (m) mid = m[1];
        }
        var row = null;
        if (mid && window.tableRowsData) {
            for (var i = 0; i < window.tableRowsData.length; i++) {
                if (String(window.tableRowsData[i].mid) === String(mid)) {
                    row = window.tableRowsData[i];
                    break;
                }
            }
        }
        openVersionModal(
            mid,
            (row && row.title) || $btn.data('title'),
            (row && row.latest_version) || $btn.data('ver'),
            (row && row.last_update_date) || $btn.data('date'),
            (row && row.version_count) || $btn.data('count'),
            row
        );
    });

    $('#versionModalClose').on('click', function(e) {
        e.preventDefault();
        closeVersionModal();
    });

    $vModal.on('click', function(e) {
        if (e.target === this) {
            closeVersionModal();
        }
    });

    $(document).on('keydown', function(e) {
        if (e.key === 'Escape' || e.keyCode === 27) {
            if ($vModal.hasClass('show')) {
                closeVersionModal();
            }
        }
    });

    // ───── 评论嵌入预览交互 ─────
    $(document).on('click', '.js-embed-comment-preview', function(e) {
        e.preventDefault();
        var u = $(this).data('url');
        var $box = $('#commentEmbedContainer');
        var $ifm = $('#commentEmbedIframe');
        if ($box.is(':visible')) {
            $box.slideUp(180);
            $ifm.attr('src', 'about:blank');
            $(this).text('📜 在看板内嵌入浏览评论区');
        } else {
            $ifm.attr('src', u);
            $box.slideDown(220);
            $(this).text('收起嵌入预览 ▴');
        }
    });
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
    function getTrendRowKey(cell) {
        var $cell = $(cell);
        var $row = $cell.closest('tr');
        return String($row.attr('data-mid') || $row.data('mid') || $cell.data('title') || '');
    }
    function syncHoverToggles() {
        $('.js-desc-hover-toggle').prop('checked', descHoverPopupEnabled).closest('.mode-toggle-header').toggleClass('is-on', descHoverPopupEnabled).attr('aria-pressed', descHoverPopupEnabled ? 'true' : 'false');
        $('.js-trend-hover-toggle').prop('checked', trendHoverPopupEnabled).closest('.mode-toggle-header').toggleClass('is-on', trendHoverPopupEnabled).attr('aria-pressed', trendHoverPopupEnabled ? 'true' : 'false');
        $('.js-comment-hover-toggle').prop('checked', commentHoverPopupEnabled).closest('.mode-toggle-header').toggleClass('is-on', commentHoverPopupEnabled).attr('aria-pressed', commentHoverPopupEnabled ? 'true' : 'false');
    }
    function setDescHoverMode(enabled) {
        descHoverPopupEnabled = !!enabled;
        localStorage.setItem('desc-hover-popup-enabled', descHoverPopupEnabled ? '1' : '0');
        syncHoverToggles();
    }
    function setTrendHoverMode(enabled) {
        trendHoverPopupEnabled = !!enabled;
        localStorage.setItem('trend-hover-popup-enabled', trendHoverPopupEnabled ? '1' : '0');
        syncHoverToggles();
        if (!trendHoverPopupEnabled && !trendPopupPinned) {
            $('#trendPointLabel').hide();
            $('#trendGuideLine').css('visibility', 'hidden');
            hideTrendBridge();
            $trendTooltip.removeClass('show').hide();
        }
    }
    function setCommentHoverMode(enabled) {
        commentHoverPopupEnabled = !!enabled;
        localStorage.setItem('comment-hover-popup-enabled', commentHoverPopupEnabled ? '1' : '0');
        syncHoverToggles();
    }
    function toggleHeaderMode(toggle) {
        if (!toggle) return;
        if (toggle.querySelector('.js-desc-hover-toggle')) {
            setDescHoverMode(!descHoverPopupEnabled);
        } else if (toggle.querySelector('.js-trend-hover-toggle')) {
            setTrendHoverMode(!trendHoverPopupEnabled);
        } else if (toggle.querySelector('.js-comment-hover-toggle')) {
            setCommentHoverMode(!commentHoverPopupEnabled);
        }
    }
    document.addEventListener('click', function(e) {
        var toggle = e.target && e.target.closest ? e.target.closest('.mode-toggle-header') : null;
        if (!toggle) return;
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        toggleHeaderMode(toggle);
    }, true);
    ['pointerdown', 'mousedown', 'mouseup', 'dblclick'].forEach(function(evtName) {
        document.addEventListener(evtName, function(e) {
            var toggle = e.target && e.target.closest ? e.target.closest('.mode-toggle-header') : null;
            if (!toggle) return;
            e.stopPropagation();
            if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        }, true);
    });
    document.addEventListener('keydown', function(e) {
        var toggle = e.target && e.target.closest ? e.target.closest('.mode-toggle-header') : null;
        if (!toggle || (e.key !== 'Enter' && e.key !== ' ')) return;
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        toggleHeaderMode(toggle);
    }, true);
    $(document).on('mousedown click dblclick', '.mode-toggle, .mode-toggle input', function(e) {
        e.stopPropagation();
    });
    syncHoverToggles();
    $(document).on('change', '.js-desc-hover-toggle', function(e) {
        e.stopPropagation();
        setDescHoverMode($(this).is(':checked'));
    });
    $(document).on('change', '.js-trend-hover-toggle', function(e) {
        e.stopPropagation();
        setTrendHoverMode($(this).is(':checked'));
    });
    $(document).on('change', '.js-comment-hover-toggle', function(e) {
        e.stopPropagation();
        setCommentHoverMode($(this).is(':checked'));
    });
    function isTrendHoverAlive() {
        var overTooltip = $trendTooltip.is(':hover');
        var overBridge = $trendBridge.is(':hover');
        var overCell = activeTrendCell && activeTrendCell.length && activeTrendCell.is(':hover');
        return !!(overTooltip || overBridge || overCell);
    }
    function hideTrendBridge() {
        $trendBridge.hide();
    }
    function hideTrendTooltipSoon(delay) {
        if (trendPopupPinned) return;
        clearTimeout(trendHoverTimer);
        trendHoverTimer = setTimeout(function() {
            if (isTrendHoverAlive()) return;
            $('#trendPointLabel').hide();
            $('#trendGuideLine').css('visibility', 'hidden');
            $trendTooltip.addClass('hiding').removeClass('show');
            hideTrendBridge();
            setTimeout(function() {
                if (!$trendTooltip.hasClass('show')) $trendTooltip.hide().removeClass('hiding');
                activeTrendCell = null;
            }, 180);
        }, delay || 720);
    }
    function hideTrendTooltipNow() {
        clearTimeout(trendHoverTimer);
        trendPopupPinned = false;
        $('#trendPointLabel').hide();
        $('#trendGuideLine').css('visibility', 'hidden');
        hideTrendBridge();
        $trendTooltip.removeClass('show hiding').hide();
        activeTrendCell = null;
        activeTrendRowKey = '';
    }
    function updateTrendBridge($cell) {
        if (!$cell || !$cell.length || !$trendTooltip.is(':visible')) return;
        var c = $cell[0].getBoundingClientRect();
        var t = $trendTooltip[0].getBoundingClientRect();
        var left = Math.min(c.left, t.left) - 8;
        var right = Math.max(c.right, t.right) + 8;
        var top = Math.min(c.top, t.top) - 8;
        var bottom = Math.max(c.bottom, t.bottom) + 8;
        $trendBridge.css({
            left: Math.max(0, left) + 'px',
            top: Math.max(0, top) + 'px',
            width: Math.max(1, right - left) + 'px',
            height: Math.max(1, bottom - top) + 'px'
        }).show();
    }
    function positionTrendTooltip(anchorEvent, $cell) {
        var tw = $trendTooltip.outerWidth();
        var th = $trendTooltip.outerHeight();
        var vw = window.innerWidth;
        var vh = window.innerHeight;
        var gap = 2;
        var rect = $cell && $cell.length ? $cell[0].getBoundingClientRect() : null;
        var left = rect ? (rect.left + rect.width / 2 - tw / 2) : 10;
        var top = rect ? (rect.top - th - gap) : 10;
        if (rect && top < 10) {
            top = Math.min(rect.bottom + gap, vh - th - 10);
        }
        if (top + th > vh - 10) top = vh - th - 10;
        if (top < 10) top = 10;
        if (left + tw > vw - 10) left = vw - tw - 10;
        if (left < 10) left = 10;
        $trendTooltip.css({ left: left + 'px', top: top + 'px' });
        updateTrendBridge($cell);
    }
    $(document).on('trend:open', '.td-trend', function(e, pinned, sourceEvent) {
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
        if ($trendTooltip.hasClass('show') && $trendTooltip.data('active-row-key') === activeTrendRowKey && activeTrendCell && activeTrendCell.length && $cell.is(activeTrendCell)) {
            return;
        }
        var metric = $cell.data('metric') || '走势';
        var trendStr = $cell.data('trend') || '';
        var datesStr = $cell.data('dates') || '';
        if (!trendStr) {
            $trendTooltip.hide();
            return;
        }
        var trendVals = trendStr.split(',').map(Number).filter(function(v) { return !isNaN(v); });
        var dates = datesStr.split(',');
        if (trendVals.length < 2) {
            $trendTooltip.hide();
            return;
        }
        // 渲染标题
        $('#trendTooltipTitle').text(title);
        $('#trendTooltipSubtitle').text(metric + ' · 近 ' + trendVals.length + ' 天指数走势');
        // 测算数值范围
        var minVal = Math.min.apply(null, trendVals);
        var maxVal = Math.max.apply(null, trendVals);
        var latestVal = trendVals[trendVals.length - 1];
        var startVal = trendVals[0];
        var avgVal = Math.round(trendVals.reduce(function(a, b){ return a + b; }, 0) / trendVals.length);
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
        for (var i = 0; i < len; i++) {
            var x = paddingL + (i / (len - 1)) * chartW;
            var y = height - paddingB - ((trendVals[i] - minVal) / valDiff) * chartH;
            points.push({ x: x, y: y, value: trendVals[i], date: dates[i] || '' });
        }
        // 生成连线 path 和渐变填充 path
        var pathD = 'M ' + points[0].x + ' ' + points[0].y;
        for (var i = 1; i < len; i++) {
            pathD += ' L ' + points[i].x + ' ' + points[i].y;
        }
        var areaD = pathD +
            ' L ' + points[len-1].x + ' ' + (height - paddingB) +
            ' L ' + points[0].x + ' ' + (height - paddingB) + ' Z';
        var trendColor = 'var(--primary)';
        var markerHtml = '';
        var hitHtml = '<line class="trend-guide-line" id="trendGuideLine" x1="' + paddingL + '" y1="' + paddingT + '" x2="' + paddingL + '" y2="' + (height - paddingB) + '" />' +
            '<rect class="trend-chart-capture" x="' + paddingL + '" y="' + paddingT + '" width="' + chartW + '" height="' + chartH + '" fill="rgba(0,0,0,0.001)" pointer-events="all" />';
        for (var i = 0; i < len; i++) {
            var p = points[i];
            var isMax = p.value === maxVal;
            var isMin = p.value === minVal;
            var isLatest = i === len - 1;
            if (isMax || isMin || isLatest || i === 0) {
                markerHtml += '<circle class="trend-point-visible" cx="' + p.x + '" cy="' + p.y + '" r="' + (isMax ? 5.5 : isLatest ? 5 : 3.5) + '" fill="var(--glass-bg-solid)" stroke="' + trendColor + '" stroke-width="' + (isMax ? 2.4 : 1.8) + '" />';
            }
            hitHtml += '<circle class="trend-point-hit" cx="' + p.x + '" cy="' + p.y + '" r="8" fill="rgba(0,0,0,0.001)" data-x="' + p.x + '" data-y="' + p.y + '" data-date="' + p.date + '" data-value="' + p.value + '" data-kind="' + (isMax ? '峰值' : isMin ? '低点' : isLatest ? '最新' : '') + '" />';
        }
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
        function showTrendPoint(point) {
            if (!point) return;
            var x = Number(point.x) || 0;
            var y = Number(point.y) || 0;
            var kind = point.kind || '';
            var date = point.date || '未知日期';
            var value = point.value;
            $('#trendPointLabel')
                .html((kind ? '<b>' + kind + '</b><br>' : '') + date + '<br>指数 ' + value)
                .css({ left: Math.min(Math.max(x + 10, 8), width - 118) + 'px', top: Math.max(y - 34, 6) + 'px' })
                .show();
            $('#trendGuideLine')
                .attr('x1', x).attr('x2', x)
                .css('visibility', 'visible');
        }
        function pointFromNode(node) {
            return {
                x: Number(node.getAttribute('data-x')) || 0,
                y: Number(node.getAttribute('data-y')) || 0,
                date: node.getAttribute('data-date') || '',
                value: node.getAttribute('data-value') || '',
                kind: node.getAttribute('data-kind') || ''
            };
        }
        function nearestPointFromEvent(e) {
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
            return { x: point.x, y: point.y, date: point.date, value: point.value, kind: isMax ? '峰值' : isMin ? '低点' : isLatest ? '最新' : '' };
        }
        showTrendPoint({
            x: points[len - 1].x,
            y: points[len - 1].y,
            date: points[len - 1].date,
            value: points[len - 1].value,
            kind: '最新'
        });
        $('#trendTooltipChartContainer .trend-chart-capture').on('mouseenter mousemove click', function(e) {
            showTrendPoint(nearestPointFromEvent(e));
        });
        $('#trendTooltipChartContainer .trend-point-hit').on('mouseenter mousemove click', function() {
            showTrendPoint(pointFromNode(this));
        });
        $trendTooltip.removeClass('hiding').addClass('show').data('active-title', title).data('active-row-key', activeTrendRowKey).show();
        positionTrendTooltip(anchorEvent, $cell);
    });
    $(document).on('mouseenter', '.td-trend', function(e) {
        $(this).trigger('trend:open', [false, e]);
    });
    $(document).on('click', '.td-trend', function(e) {
        if ($(e.target).closest('a, button').length) return;
        if (Date.now() < trendSuppressOpenUntil) {
            e.preventDefault();
            e.stopPropagation();
            return;
        }
        e.preventDefault();
        e.stopPropagation();
        var clickedRowKey = getTrendRowKey(this);
        if ($trendTooltip.hasClass('show') && $trendTooltip.data('active-row-key') === clickedRowKey) {
            hideTrendTooltipNow();
            trendSuppressOpenUntil = Date.now() + 220;
            return;
        }
        $(this).trigger('trend:open', [true, e]);
    });
    document.addEventListener('click', function(e) {
        var cell = e.target && e.target.closest ? e.target.closest('td.td-trend') : null;
        if (!cell || e.target.closest('a, button')) return;
        var clickedRowKey = getTrendRowKey(cell);
        if ($trendTooltip.hasClass('show') && $trendTooltip.data('active-row-key') === clickedRowKey) {
            e.preventDefault();
            e.stopPropagation();
            if (e.stopImmediatePropagation) e.stopImmediatePropagation();
            hideTrendTooltipNow();
            trendSuppressOpenUntil = Date.now() + 220;
        }
    }, true);
    $(document).on('mouseleave', '.td-trend', function() {
        hideTrendTooltipSoon(720);
    });
    $trendTooltip.on('mouseenter', function() {
        clearTimeout(trendHoverTimer);
    }).on('mouseleave', function() {
        hideTrendTooltipSoon(360);
    });
    $trendTooltip.on('mousedown', function(e) {
        if ($(e.target).is('#trendTooltip')) {
            hideTrendTooltipNow();
        }
    });
    $trendBridge.on('mouseenter', function() {
        clearTimeout(trendHoverTimer);
    }).on('mouseleave', function() {
        hideTrendTooltipSoon(360);
    });
    function showInlineTrendProbe(e, $svg) {
        var $cell = $svg.closest('.td-trend');
        var trendStr = $cell.data('trend') || '';
        var datesStr = $cell.data('dates') || '';
        if (!trendStr) return;
        var vals = trendStr.split(',').map(Number).filter(function(v) { return !isNaN(v); });
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
        if (!$probe.length) {
            $probe = $('<div class="trend-inline-probe"></div>').appendTo($cell);
        }
        var cellRect = $cell[0].getBoundingClientRect();
        var left = e.clientX - cellRect.left + 10;
        var top = e.clientY - cellRect.top - 42;
        if (left > cellRect.width - 104) left = Math.max(6, cellRect.width - 104);
        if (top < 6) top = e.clientY - cellRect.top + 12;
        $probe.html('<b>' + value + '</b>' + (date ? date : '')).
            css({ left: left + 'px', top: top + 'px' }).show();
    }
    $(document).on('mousemove', '.sparkline-svg', function(e) {
        showInlineTrendProbe(e, $(this));
    });
    $(document).on('mouseleave', '.sparkline-svg', function() {
        $(this).closest('.td-trend').children('.trend-inline-probe').hide();
    });
    // ────── 悬浮窗智能自适应延迟关闭与滚轮管理系统 ──────
    // =====================================================================
    /* ── 1. 悬停整合包名称 → 显示介绍（带 300ms 延迟及淡入淡出锁死） ── */
    $(document).on('mouseenter', '.modpack-link', function() {
        if (!descHoverPopupEnabled) return;
        var $self = $(this);
        var descKey = 'desc:' + (($self.data('mid') || '') || ($self.attr('href') || '') || $self.text());
        if (isHoverCooling(descKey)) return;
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {
            showDescPopup($self);
            $('body').css({ 'overflow': 'hidden', 'height': '100vh' });
        }, HOVER_DELAY);
    });
    $(document).on('mouseleave', '.modpack-link', function() {
        if (!descHoverPopupEnabled) return;
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {
            hideDescPopup();
            $('body').css({ 'overflow': '', 'height': '' });
        }, 300);
    });
    $(document).on('click', '.modpack-link', function(e) {
        if (descHoverPopupEnabled) return;
        e.preventDefault();
        e.stopPropagation();
        var $self = $(this);
        var descKey = 'desc:' + (($self.data('mid') || '') || ($self.attr('href') || '') || $self.text());
        if ($popup.hasClass('show') && activeDescKey === descKey) {
            hideDescPopup();
            $('body').css({ 'overflow': '', 'height': '' });
            return;
        }
        clearTimeout(hoverTimer);
        showDescPopup($self);
        $('body').css({ 'overflow': 'hidden', 'height': '100vh' });
    });
    $popup.on('mouseenter', function() {
        clearTimeout(hoverTimer);
        $('body').css({ 'overflow': 'hidden', 'height': '100vh' });
    }).on('mouseleave', function() {
        if (!descHoverPopupEnabled) return;
        clearTimeout(hoverTimer);
        hoverTimer = setTimeout(function() {
            hideDescPopup();
            $('body').css({ 'overflow': '', 'height': '' });
        }, 300);
    });
    /* ── 2. 点击评论列 / 卡片评论按钮 → 稳定打开评论详情；不再扫过表格就弹大窗 ── */
    $(document).on('click', '.td-comment', function(e) {
        if ($(e.target).closest('a, button').length) return;
        var $self = $(this);
        clearTimeout(commentHoverTimer);
        if ($cpopup.hasClass('show') && activeCommentCell && activeCommentCell.length && $self.is(activeCommentCell)) {
            hideCommentPopup();
            $('body').css({ 'overflow': '', 'height': '' });
            return;
        }
        showCommentPopup($self);
        $('body').css({ 'overflow': 'hidden', 'height': '100vh' });
    });
    $(document).on('click', '.show-comment-btn', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var $self = $(this);
        clearTimeout(commentHoverTimer);
        if ($cpopup.hasClass('show') && activeCommentCell && activeCommentCell.length && $self.is(activeCommentCell)) {
            hideCommentPopup();
            $('body').css({ 'overflow': '', 'height': '' });
            return;
        }
        showCommentPopup($self);
        $('body').css({ 'overflow': 'hidden', 'height': '100vh' });
    });
    $(document).on('keydown', '.engage-comment-trigger', function(e) {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        e.preventDefault();
        $(this).closest('.td-comment').trigger('click');
    });
    $(document).on('mouseenter', '.td-comment', function() {
        if (!commentHoverPopupEnabled) return;
        var $self = $(this);
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {
            if (!$self.is(':hover')) return;
            showCommentPopup($self);
            $('body').css({ 'overflow': 'hidden', 'height': '100vh' });
        }, HOVER_DELAY);
    });
    $(document).on('mouseleave', '.td-comment', function() {
        if (!commentHoverPopupEnabled) return;
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {
            if ($cpopup.is(':hover')) return;
            hideCommentPopup();
            $('body').css({ 'overflow': '', 'height': '' });
        }, 260);
    });
    $(document).on('mousedown', function(e) {
        if (!$cpopup.hasClass('show')) return;
        if ($(e.target).closest('#commentPopup, .td-comment, .show-comment-btn, .comment-search-nav, .comment-page-bar').length) return;
        hideCommentPopup();
        $('body').css({ 'overflow': '', 'height': '' });
    });
    $cpopup.on('mousedown', function(e) {
        if ($(e.target).is('#commentPopup')) {
            hideCommentPopup();
            $('body').css({ 'overflow': '', 'height': '' });
        }
    });
    $cpopup.on('mouseenter', function() {
        clearTimeout(commentHoverTimer);
        $('body').css({ 'overflow': 'hidden', 'height': '100vh' });
    }).on('mouseleave', function() {
        if (!commentHoverPopupEnabled) return;
        clearTimeout(commentHoverTimer);
        commentHoverTimer = setTimeout(function() {
            hideCommentPopup();
            $('body').css({ 'overflow': '', 'height': '' });
        }, 280);
    });
    /* ── 3. 关闭/Escape 恢复现场 ── */
    $('#pvClose').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        setHoverCooldown(activeDescKey);
        hideDescPopup();
        $('body').css({ 'overflow': '', 'height': '' });
    });
    function closeFeedback() { $('#feedbackModal').removeClass('show'); }
    var feedbackDraftKey = 'mcmod-feedback-draft-v1';
    try {
        var draft = JSON.parse(localStorage.getItem(feedbackDraftKey) || '{}');
        $('#feedbackType').val(draft.type || '功能建议'); $('#feedbackContent').val(draft.content || ''); $('#feedbackContact').val(draft.contact || '');
    } catch(e) {}
    $('#feedbackType, #feedbackContent, #feedbackContact').on('input change', function() {
        localStorage.setItem(feedbackDraftKey, JSON.stringify({ type: $('#feedbackType').val(), content: $('#feedbackContent').val(), contact: $('#feedbackContact').val() }));
    });
    $('#feedbackOpen').on('click', function() {
        $('#feedbackStatus').text('⚠️ 反馈接收接口正在升级维护中，暂时不可用，敬请谅解。');
        $('#feedbackModal').addClass('show');
    });
    $('#feedbackCancel, #feedbackModal').on('click', function(e) { if (e.target === this) closeFeedback(); });
    $('#feedbackSubmit').on('click', function() {
        var content = $('#feedbackContent').val().trim();
        if (!content) { $('#feedbackStatus').text('请先填写反馈内容。'); return; }
        if (!feedbackUrl) { $('#feedbackStatus').text('作者尚未配置反馈接收地址。'); return; }
        var $btn = $(this).prop('disabled', true).text('提交中…');
        $('#feedbackStatus').text('');
        fetch(feedbackUrl, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
            tool: '多平台聚合看板', version: 'v10.6.6', type: $('#feedbackType').val(), content: content, contact: $('#feedbackContact').val().trim()
        }) }).then(function(r) { return r.ok ? r.json().catch(function() { return { ok:true }; }) : Promise.reject(new Error('HTTP ' + r.status)); }).then(function() {
            $('#feedbackStatus').text('已提交，感谢你的反馈！'); $('#feedbackContent, #feedbackContact').val(''); localStorage.removeItem(feedbackDraftKey);
        }).catch(function() { $('#feedbackStatus').text('提交失败，请稍后重试。'); }).finally(function() { $btn.prop('disabled', false).text('提交'); });
    });
    $('#commentClose').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        hideCommentPopup();
        $('body').css({ 'overflow': '', 'height': '' });
    });
    $('#trendClose').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        hideTrendTooltipNow();
    });
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') {
            hideDescPopup();
            hideCommentPopup();
            hideTrendTooltipNow();
            closeImageLightbox();
            $('body').css({ 'overflow': '', 'height': '' });
        } else if ($cpopup.hasClass('show')) {
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                $('#cmtPrev').trigger('click');
            } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                $('#cmtNext').trigger('click');
            }
        }
    });
    /* 窗口缩放 → 更新 scrollY */
    var resizeTimer = null;
    $(window).on('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            var newH = Math.max(400, $(window).height() - 320);
            $('.dataTables_scrollBody').height(newH);
            if (table) {
                table.columns.adjust();
            }
            if ($cpopup.hasClass('show')) {
                lockCommentPopupSize();
                repositionCommentPopup();
                checkCommentOverflow();
            }
        }, 300);
    });
    
    /* ════════ 全局标签数量显隐独立控制 ════════ */
    var tagCountsVisible = localStorage.getItem('mc_show_tag_counts') !== 'false';
    function applyTagCountsVisibility() {
        $('body').toggleClass('hide-tag-counts', !tagCountsVisible);
        $('#toggleTagCountsLabel').text(tagCountsVisible ? '标签数量' : '隐藏标签数');
        $('#toggleTagCountsBtn').attr('title', tagCountsVisible ? '当前已显示标签数量，点击可隐藏' : '当前已隐藏标签数量，点击可显示');
        $('#toggleTagCountsBtn').toggleClass('active', tagCountsVisible);
    }
    applyTagCountsVisibility();
    $('#toggleTagCountsBtn').on('click', function() {
        tagCountsVisible = !tagCountsVisible;
        localStorage.setItem('mc_show_tag_counts', tagCountsVisible);
        applyTagCountsVisibility();
    });

    /* ════════ 数据抓取变动审计与生态监控交互逻辑 ════════ */
    var auditActiveType = 'all';
    var auditActivePlat = 'all';

    /* 独立命名的纯文本转义。历史上 escHtml 曾与"介绍正文排版器"同名，后者覆盖前者，
       于是这里拿到的不是转义而是段落 HTML（内容外面会套 <div class="pv-para">），
       用在 title="..." 这类属性位置时引号被内层标签冲断、整行 HTML 被当文本吐到页面上。
       排版器现已更名 formatDescHtml，这里仍保留独立命名，避免再次被同名覆盖踩到。 */
    function auditEsc(s) {
        if (s === null || s === undefined) return '';
        return String(s)
            .split('&').join('&amp;')
            .split('<').join('&lt;')
            .split('>').join('&gt;')
            .split('"').join('&quot;')
            .split("'").join('&#39;');
    }

    function initAuditDiffModule() {
        var diff = window.auditDiffData;
        if (!diff) return;

        var stats = diff.stats || {};
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

        if (diff.generated_at) {
            $('#auditGenTime').text('📅 对比时间: ' + diff.generated_at);
        }
        var scopeText = '📦 全网监测规模: ' + totalScope.toLocaleString() + ' 款';
        if ((diff.new_platforms || []).length) {
            scopeText += '　|　本次新纳入: ' + diff.new_platforms.join('、');
        }
        $('#auditTotalScope').text(scopeText);

        renderAuditItems();
    }

    function renderAuditItems() {
        var diff = window.auditDiffData;
        if (!diff) {
            $('#auditItemsContainer').html('<div style="text-align:center; padding:30px; color:var(--text-muted);">暂无变动审计数据</div>');
            return;
        }

        var q = ($('#auditSearchInput').val() || '').trim().toLowerCase();
        var pool = [];

        if (auditActiveType === 'all' || auditActiveType === 'added') {
            (diff.added || []).forEach(function(x) {
                var c = Object.assign({}, x, { _type: 'added' });
                pool.push(c);
            });
        }
        if (auditActiveType === 'all' || auditActiveType === 'updated') {
            (diff.updated || []).forEach(function(x) {
                var c = Object.assign({}, x, { _type: 'updated' });
                pool.push(c);
            });
        }
        if (auditActiveType === 'all' || auditActiveType === 'version_gained') {
            (diff.version_gained || []).forEach(function(x) {
                var c = Object.assign({}, x, { _type: 'version_gained' });
                pool.push(c);
            });
        }
        if (auditActiveType === 'all' || auditActiveType === 'removed') {
            (diff.removed || []).forEach(function(x) {
                var c = Object.assign({}, x, { _type: 'removed' });
                pool.push(c);
            });
        }

        // 过滤平台
        if (auditActivePlat !== 'all') {
            pool = pool.filter(function(x) { return x.platform === auditActivePlat; });
        }

        // 过滤关键词
        if (q) {
            pool = pool.filter(function(x) {
                var txt = ((x.title || '') + ' ' + (x.author || '') + ' ' + (x.version || '')).toLowerCase();
                return txt.indexOf(q) !== -1;
            });
        }

        if (!pool.length) {
            var hasAnyChange = (diff.added || []).length + (diff.updated || []).length + (diff.version_gained || []).length + (diff.removed || []).length;
            var emptyMsg = hasAnyChange
                ? '没有匹配到符合条件的变动条目'
                : '本次抓取未检测到变动，与上次快照完全一致';
            $('#auditItemsContainer').html('<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:0.9rem;">' + emptyMsg + '</div>');
            return;
        }

        var platNames = {
            mcmod: { name: 'MC百科', color: '#2563eb', icon: '📦' },
            bilibili: { name: '哔哩哔哩', color: '#fb7299', icon: '📺' },
            bbsmc: { name: 'BBSMC', color: '#00af5c', icon: '💎' },
            xyebbs: { name: 'XYEBBS', color: '#16a34a', icon: '🍃' },
            modrinth: { name: 'Modrinth', color: '#1bd96a', icon: '🌐' },
            curseforge: { name: 'CurseForge', color: '#f16436', icon: '🔥' }
        };

        var html = '';
        pool.forEach(function(item) {
            var pInfo = platNames[item.platform] || { name: item.platform, color: '#64748b', icon: '🧩' };
            var typeBadge = '';
            if (item._type === 'added') {
                typeBadge = '<span style="background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:700;">🟢 新增收录</span>';
            } else if (item._type === 'updated') {
                typeBadge = '<span style="background:rgba(59,130,246,0.15); color:#3b82f6; border:1px solid rgba(59,130,246,0.3); padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:700;">🔵 版本更新</span>';
            } else if (item._type === 'version_gained') {
                typeBadge = '<span style="background:rgba(245,158,11,0.15); color:#f59e0b; border:1px solid rgba(245,158,11,0.3); padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:700;">🆕 补全版本信息</span>';
            } else {
                typeBadge = '<span style="background:rgba(239,68,68,0.15); color:#ef4444; border:1px solid rgba(239,68,68,0.3); padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:700;">🔴 移除下架</span>';
            }

            var diffDetailHtml = '';
            if (item.diff_details && item.diff_details.length) {
                diffDetailHtml = '<div style="font-size:0.75rem; color:#f59e0b; margin-top:2px;">' + auditEsc(item.diff_details.join(' · ')) + '</div>';
            }

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
            if (item.url) {
                html += '    <a href="' + auditEsc(item.url) + '" target="_blank" rel="noopener noreferrer" class="cross-action-btn cross-btn-ext" title="在新标签页打开原页面">原站 ↗</a>';
            }
            html += '  </div>';
            html += '</div>';
        });

        $('#auditItemsContainer').html(html);
    }

    $('#openAuditModalBtn').on('click', function() {
        initAuditDiffModule();
        $('#auditModalOverlay').addClass('show').fadeIn(150);
    });

    $('#auditModalClose, #auditModalOverlay').on('click', function(e) {
        if (e.target === this || $(this).attr('id') === 'auditModalClose') {
            $('#auditModalOverlay').removeClass('show').fadeOut(150);
        }
    });

    $('.audit-filter-chip').on('click', function() {
        $('.audit-filter-chip').removeClass('active');
        $(this).addClass('active');
        auditActiveType = $(this).data('type');
        renderAuditItems();
    });

    $('#auditPlatformSelect').on('change', function() {
        auditActivePlat = $(this).val();
        renderAuditItems();
    });

    $('#auditSearchInput').on('input', function() {
        renderAuditItems();
    });

    setTimeout(initAuditDiffModule, 200);

        }, 10); // 延迟初始化，避免打开文件时阻塞浏览器
});
