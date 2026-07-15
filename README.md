# Minecraft Modpack Data Board

English | [中文](README_CN.md)

A local data tool for organizing, searching, and analyzing Minecraft modpacks.

This project collects and organizes modpack information from [MCMod (mcmod.cn)](https://www.mcmod.cn/), then generates an offline HTML dashboard for searching, filtering, comparing, and tracking trends.

> Currently focused on MCMod data.  
> "Multi-platform" represents a future expansion direction, not a completed multi-source integration.

---

## ✨ Features

### 🔍 Search

Search modpacks by:

- Name
- Description
- Comments
- Tags
- Included mods

### 🏷️ Filtering

Filter by:

- Category
- Modpack tags
- Mod types
- Specific mods
- Trend period

### 📊 Data Analysis

View and compare:

- Ranking indexes
- Views
- Community activity
- Trend changes

### 📈 Trend Tracking

Store local historical data and analyze popularity changes over time.

### 🧩 Mod Reverse Search

Find modpacks that contain specific mods.

### 💻 Offline Dashboard

All data is stored locally.  
The generated HTML dashboard works without an online service.

---

## 📷 What You Can Do

Open the generated HTML file to:

- Search modpacks
- Read descriptions
- Browse comment data
- Compare modpacks
- Inspect trend changes

---

## 🚀 Usage

Requirements:

- Python 3
- Browser automation environment for data collection

Run:

```powershell
# Collect data (first run may take a long time)
python "多平台聚合爬虫_v1.0.py"

# Refresh items not updated within N days
python "多平台聚合爬虫_v1.0.py" --refresh-days 1

# Force refresh all data
python "多平台聚合爬虫_v1.0.py" --refresh-all

# Generate the HTML dashboard
python "多平台聚合转换器_v1.0.py"
```

Then open:

```text
converted_output/点击打开.html
```

Double-click to open. When sharing, pack the entire `converted_output/` folder (including the adjacent `data/` directory), not just the HTML file.

Workflow:

**Collect data → Generate dashboard → Open in browser**

---

## 📂 Project Structure

| Path | Description |
| --- | --- |
| `多平台聚合爬虫_v1.0.py` | Data collection script |
| `多平台聚合转换器_v1.0.py` | HTML dashboard generator |
| `多平台爬虫数据_v1.0.jsonl` | Current data snapshot (local, usually not committed) |
| `trend_history.jsonl` | Local long-term trend history (local, usually not committed) |
| `converted_output/` | Generated dashboard and on-demand data (local, usually not committed) |
| `feedback/` | Feedback deployment templates |
| `ignored_local_files/` | Local temp files and browser login state |
| `README_CN.md` | Chinese documentation |

See `LOCAL_FILE_MAP.md` for a more detailed local file map.

---

## ⚠️ Notes and Limitations

- This project is not an official tool of MCMod, Minecraft, Mojang, Microsoft, or any modpack author.
- The data collection scripts are not officially authorized by third-party data providers.
- Recommended usage: personal learning, local organization, and low-frequency updates.
- Do not perform high-frequency crawling, bypass access restrictions, redistribute complete datasets, or use collected data commercially.
- Users are responsible for evaluating their own usage environment and related risks.

---

## 🔒 Privacy

Some local files may contain:

- Browser sessions
- Cookies
- Tokens
- Personal configuration

Do not upload or share sensitive files.

---

## 🤖 AI-Generated Project

This repository’s **code, documentation, configuration, commit messages, and upload process were produced entirely (or substantially entirely) by AI**. The human maintainer has not manually authored or personally verified every line.

AI output may be wrong, incomplete, or unsafe. **Review and test before use.** Publication here is not a quality guarantee or endorsement of any specific approach.

---

## 📄 Data Disclaimer

All rankings, scores, trends, and comment summaries are locally processed results.

They are provided for information organization and reference only, and do not represent official evaluations of any modpack.

---

## License

**No open-source license is granted.**

This repository is published for **personal learning and technical reference only**. You may read the code for learning; commercial use, redistribution of collected datasets, or treating this project as an authorized product is not permitted by this notice.

All third-party content—including modpacks, mods, webpage content, and comments—belongs to their respective owners. Nothing in this repository grants rights to those materials.
