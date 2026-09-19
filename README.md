# Minecraft Modpack Board

[中文](README_CN.md) · [Current status](docs/PROJECT_STATUS.md) · [Development](docs/DEVELOPMENT.md) · [Desktop task](docs/DESKTOP_TASK.md)

A local Minecraft modpack discovery tool with collectors for **MCMod, Bilibili, BBSMC, XYEBBS, Modrinth and CurseForge**. Search and filter local records, inspect versions/mods/source information and follow links to the original platforms.

The application currently consists of a **Python data pipeline and TypeScript/Vite web frontend**. A Windows desktop application with in-app collection and updates is the next task; no desktop executable has been released yet.

## Open an existing dashboard

When a complete `converted_output/index.html`, `assets/` and `data/` already exist, run from the repository root:

```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory converted_output
```

Open <http://127.0.0.1:8765/>. Keep the output directory together. The modern frontend uses JavaScript modules and should be served over local HTTP.

A fresh clone contains source code, not collected datasets or a prebuilt dashboard. See [development instructions](docs/DEVELOPMENT.md) for collection and staging.

## Repository map

| Path | Purpose |
| --- | --- |
| `多平台聚合爬虫_v1.0.py` and platform crawlers | Collection entry point and six collectors |
| `pipeline/` | Canonical SQLite model, adapters, exporters and staging/release tools |
| `apps/web/` | Modern frontend and unit tests |
| `web/`, `多平台聚合转换器_v1.0.py` | Shared styles and still-used legacy conversion compatibility |
| `tests/`, `pipeline/tests/` | Python checks; some require local datasets |
| `docs/` | Current status, contracts, development and historical evidence |
| `feedback/` | Optional feedback service templates |

Datasets, generated dashboards, build outputs, browser sessions and credentials stay local.

## Known boundaries

Platform coverage does not mean every field or inferred identity is verified. Unknown source facts remain unknown. Bilibili grouping is heuristic. The latest A candidate is unintegrated and its independent safety evidence is incomplete. See [current status](docs/PROJECT_STATUS.md); historical matrices are not current release certificates.

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
