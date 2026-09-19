import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
html = open('web/template.html', encoding='utf-8').read()

print("--- Modals & Drawers ---")
for m in re.findall(r'id=["\']([^"\']*(?:modal|drawer|popup|preview|panel|dialog)[^"\']*)["\']', html, re.I):
    print(" ", m)

print("\n--- Search & Inputs ---")
for m in re.findall(r'id=["\']([^"\']*(?:search|filter|select|input)[^"\']*)["\']', html, re.I):
    print(" ", m)
