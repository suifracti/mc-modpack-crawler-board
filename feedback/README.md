# 意见反馈部署

1. 在 Google Apps Script 新建项目，粘贴 `google-apps-script.js`，在“脚本属性”设置 `FEEDBACK_SHARED_SECRET` 与 `FEEDBACK_TO_EMAIL`，部署为 Web App（允许任何人访问）。
2. 在 Cloudflare 创建 Worker，粘贴 `cloudflare-worker.js`；创建 KV 绑定 `FEEDBACK_RATE_LIMIT`，并设置机密变量 `GOOGLE_APPS_SCRIPT_URL`、`FEEDBACK_SHARED_SECRET`。
3. 将 Worker 的公开 URL 填入转换器顶部的 `FEEDBACK_URL`，重新运行转换器。

Worker 对同一 IP 每 24 小时限制 10 次。不要把 Gmail 密码或 Apps Script 密钥写进 HTML。
