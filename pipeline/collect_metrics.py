import os
import re
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def count_lines(path):
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return len(f.readlines())

def count_inlines(path):
    if not os.path.exists(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return len(re.findall(r'on\w+=\s*[\'"][^\'"]*[\'"]', content))

def main():
    dashboard_legacy = os.path.join(REPO_ROOT, "apps", "web", "src", "legacy", "dashboard.legacy.js")
    index_html = os.path.join(REPO_ROOT, "apps", "web", "index.html")
    converted_html = os.path.join(REPO_ROOT, "converted_output", "看板.html")
    converted_dashboard = os.path.join(REPO_ROOT, "converted_output", "assets", "js", "dashboard.js")
    css_file = os.path.join(REPO_ROOT, "apps", "web", "assets", "css", "dashboard.css")
    converted_css = os.path.join(REPO_ROOT, "converted_output", "assets", "css", "dashboard.css")

    print(f"dashboard.legacy.js lines: {count_lines(dashboard_legacy)}")
    print(f"converted_output/dashboard.js lines: {count_lines(converted_dashboard)}")
    print(f"index.html inline handlers: {count_inlines(index_html)}")
    print(f"看板.html inline handlers: {count_inlines(converted_html)}")
    print(f"apps/web dashboard.css lines: {count_lines(css_file)}")
    print(f"converted_output dashboard.css lines: {count_lines(converted_css)}")

    # Check git diff of css
    res = subprocess.run(["git", "diff", "--stat", "apps/web/assets/css/dashboard.css"], capture_output=True, text=True, cwd=REPO_ROOT)
    print("CSS diff stat:", res.stdout.strip() if res.stdout.strip() else "0 lines (UNTOUCHED)")

if __name__ == "__main__":
    main()
