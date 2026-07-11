function doPost(e) {
  const data = JSON.parse(e.postData.contents || "{}");
  const secret = PropertiesService.getScriptProperties().getProperty("FEEDBACK_SHARED_SECRET");
  if (!secret || data.secret !== secret) return ContentService.createTextOutput(JSON.stringify({ ok: false }));
  const to = PropertiesService.getScriptProperties().getProperty("FEEDBACK_TO_EMAIL");
  const subject = `[整合包工具反馈] ${data.type || "其他"}`;
  const body = `版本: ${data.version}\n类型: ${data.type}\n联系方式: ${data.contact || "未提供"}\nIP: ${data.ip || "未知"}\n\n${data.content}`;
  GmailApp.sendEmail(to, subject, body);
  return ContentService.createTextOutput(JSON.stringify({ ok: true })).setMimeType(ContentService.MimeType.JSON);
}
