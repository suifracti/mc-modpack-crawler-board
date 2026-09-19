"""
Inspect anomaly report details.
"""
import json

with open('build/anomaly_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('--- Environment Claims Distribution ---')
for row in data['env_distribution']:
    print(f"  {row['platform']:11} | {row['side']:6} | {row['status']:11} | {row['certainty']:15} | {row['evidence_type']:15} : {row['cnt']}")

print('\n--- Time Semantics: published_at > modified_at samples ---')
for row in data['time_published_after_modified'][:10]:
    print(f"  [{row['platform']}] ID={row['id']} pub='{row['published_at']}' mod='{row['modified_at']}' title='{row['title'][:40]}'")

print('\n--- Time Semantics: Future release date samples ---')
for row in data['time_future_release_date'][:10]:
    print(f"  [{row['platform']}] ID={row['id']} ver='{row['version_name']}' date='{row['release_date']}'")

print('\n--- Loader Missed in Title samples ---')
for row in data['loader_missed_in_title'][:15]:
    print(f"  [{row['platform']}] ID={row['id']} loaders='{row['loaders']}' title='{row['title'][:50]}'")

print('\n--- Non-Standard MC Version Patterns ---')
for row in data['mc_version_nonstandard_patterns']:
    print(f"  pattern='{row['mc_version']}' cnt={row['cnt']}")

print('\n--- Download Links with Empty/Invalid URLs ---')
for row in data['download_invalid_urls'][:15]:
    print(f"  [{row['platform']}] type='{row['link_type']}' label='{row['label']}' url='{row['url']}'")

print('\n--- Download Link Types Breakdown ---')
for row in data['download_link_types']:
    print(f"  {row['platform']:11} | {row['link_type']:15} : {row['cnt']}")
