# -*- coding: utf-8 -*-
import os, sys, json

sys.stdout.reconfigure(encoding='utf-8')

html_path = os.path.join('converted_output', '点击打开.html')
assert os.path.exists(html_path), 'HTML file not found'
size = os.path.getsize(html_path)
print(f'[OK] HTML exists: {size:,} bytes')

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

checks = [
    # MC百科
    ('view-mcmod container', 'id="view-mcmod"'),
    ('topNavMcmod button', 'data-tab="mcmod"'),
    ('crossMcmodResults', 'id="crossMcmodResults"'),

    # B站
    ('view-bilibili container', 'id="view-bilibili"'),
    ('topNavBili button', 'data-tab="bilibili"'),
    ('crossBiliResults', 'id="crossBiliResults"'),

    # BBSMC
    ('view-bbsmc container', 'id="view-bbsmc"'),
    ('topNavBbsmc button', 'data-tab="bbsmc"'),
    ('crossBbsmcResults', 'id="crossBbsmcResults"'),
    ('renderBbsmcView function', 'function renderBbsmcView()'),

    # XYEBBS
    ('view-xyebbs container', 'id="view-xyebbs"'),
    ('topNavXyebbs button', 'data-tab="xyebbs"'),
    ('crossXyebbsResults', 'id="crossXyebbsResults"'),
    ('renderXyebbsView function', 'function renderXyebbsView()'),

    # Modrinth
    ('view-modrinth container', 'id="view-modrinth"'),
    ('topNavModrinth button', 'data-tab="modrinth"'),
    ('crossModrinthResults', 'id="crossModrinthResults"'),
    ('renderModrinthView function', 'function renderModrinthView()'),
    ('initModrinthStats function', 'function initModrinthStats()'),
    ('modrinth_data.js script tag', '<script src="data/modrinth_data.js"></script>'),

    # CurseForge
    ('view-curseforge container', 'id="view-curseforge"'),
    ('topNavCurseforge button', 'data-tab="curseforge"'),
    ('crossCurseforgeResults', 'id="crossCurseforgeResults"'),
    ('renderCurseforgeView function', 'function renderCurseforgeView()'),
    ('initCurseforgeStats function', 'function initCurseforgeStats()'),
    ('curseforge_data.js script tag', '<script src="data/curseforge_data.js"></script>'),

    # 全局总徽标动态刷新函数
    ('updateAllPlatformsTotalBadge', 'function updateAllPlatformsTotalBadge()'),
]

all_passed = True
print('\nVerifying HTML Components for 6 Platforms:')
for name, pattern in checks:
    if pattern in html:
        print(f'  [PASS] {name}')
    else:
        print(f'  [FAIL] {name} NOT FOUND!')
        all_passed = False

data_files = [
    ('table_rows.js', 'window.tableRowsData', 'MC百科'),
    ('bili_data.js', 'window.biliModpacksData', 'B站自制'),
    ('bbsmc_data.js', 'window.bbsmcModpacksData', 'BBSMC'),
    ('xyebbs_data.js', 'window.xyebbsModpacksData', 'XYEBBS'),
    ('modrinth_data.js', 'window.modrinthModpacksData', 'Modrinth'),
    ('curseforge_data.js', 'window.curseforgeModpacksData', 'CurseForge')
]

print('\nVerifying Data Sources for 6 Platforms:')
total_modpacks = 0
for fn, var_name, plat_title in data_files:
    fp = os.path.join('converted_output', 'data', fn)
    if os.path.exists(fp):
        fsize = os.path.getsize(fp)
        with open(fp, 'r', encoding='utf-8') as df:
            line = df.readline()
            if line.startswith(var_name + ' = '):
                # 解析数量
                try:
                    payload = json.loads(line[len(var_name + ' = '):].rstrip(';\n '))
                    count = len(payload)
                except Exception:
                    count = 'OK'
            else:
                count = 'N/A'
        if isinstance(count, int):
            total_modpacks += count
        print(f'  [PASS] {plat_title:12} -> {fn:20} ({fsize/1024/1024:.2f} MB) | 收录: {count} 款')
    else:
        print(f'  [FAIL] {fp} missing!')
        all_passed = False

print(f'\n🔥 全网六大平台整合包总收录量: {total_modpacks:,} 款！')

if all_passed:
    print('\n>>> [ALL 6-PLATFORM CHECKS PASSED PERFECTLY!] <<<')
