export default {
  async fetch(request, env) {
    const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type" };
    if (request.method === "OPTIONS") return new Response(null, { headers: cors });
    if (request.method !== "POST") return new Response("Method not allowed", { status: 405, headers: cors });
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const key = `feedback:${ip}:${new Date().toISOString().slice(0, 10)}`;
    const count = Number(await env.FEEDBACK_RATE_LIMIT.get(key) || 0);
    if (count >= 10) return Response.json({ ok: false, error: "rate_limited" }, { status: 429, headers: cors });
    let data;
    try { data = await request.json(); } catch { return Response.json({ ok: false, error: "invalid_json" }, { status: 400, headers: cors }); }
    if (!data.content || String(data.content).trim().length > 4000) return Response.json({ ok: false, error: "invalid_content" }, { status: 400, headers: cors });
    await env.FEEDBACK_RATE_LIMIT.put(key, String(count + 1), { expirationTtl: 86400 });
    const upstream = await fetch(env.GOOGLE_APPS_SCRIPT_URL, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...data, secret: env.FEEDBACK_SHARED_SECRET, ip }) });
    return Response.json({ ok: upstream.ok }, { status: upstream.ok ? 200 : 502, headers: cors });
  }
};
