import sqlite3
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('build/canonical.db')

platforms = [
    ('mcmod', 'table_rows.js', 'window.tableRowsData = ', 'mid'),
    ('bilibili', 'bili_data.js', 'window.biliModpacksData = ', 'bvid'),
    ('bbsmc', 'bbsmc_data.js', 'window.bbsmcModpacksData = ', 'project_id'),
    ('xyebbs', 'xyebbs_data.js', 'window.xyebbsModpacksData = ', 'project_id'),
    ('modrinth', 'modrinth_data.js', 'window.modrinthModpacksData = ', 'project_id'),
    ('curseforge', 'curseforge_data.js', 'window.curseforgeModpacksData = ', 'project_id'),
]

print(f"{'Platform':<12} | {'Canonical Positive':<18} | {'V2 Legacy True':<14} | {'V2 Legacy False':<15} | {'V1 True':<10}")
print('-' * 80)

for p_id, fn, pfx, id_k in platforms:
    # Canonical count
    row = conn.execute('''
        SELECT COUNT(DISTINCT source_item_id)
        FROM environment_claims
        WHERE side = 'server'
          AND status IN ('supported', 'required', 'optional')
          AND certainty IN ('confirmed', 'inferred', 'strong_inferred')
          AND source_item_id LIKE ?
    ''', (f'{p_id}:%',)).fetchone()
    c_pos = row[0]
    
    # Legacy preview count
    p_path = os.path.join('build/legacy_preview/data', fn)
    raw = open(p_path, encoding='utf-8').read()
    idx = raw.find(pfx)
    dat = json.loads(raw[idx + len(pfx):].rstrip(';\n '))
    leg_true = sum(1 for item in dat if item.get('has_server') is True)
    leg_false = len(dat) - leg_true
    
    # V1 count
    v1_path = os.path.join('converted_output/data', fn)
    v1_true = 'N/A'
    if os.path.exists(v1_path):
        v1_raw = open(v1_path, encoding='utf-8').read()
        v1_idx = v1_raw.find(pfx)
        if v1_idx != -1:
            v1_dat = json.loads(v1_raw[v1_idx + len(pfx):].rstrip(';\n '))
            v1_true = str(sum(1 for item in v1_dat if item.get('has_server') is True))

    print(f"{p_id:<12} | {c_pos:<18} | {leg_true:<14} | {leg_false:<15} | {v1_true:<10}")
