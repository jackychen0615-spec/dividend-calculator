/**
 * 使用者回饋 → Telegram 通知站長。
 * 前端 feedback.js 以 sendBeacon POST { rating, page, message }（text/plain）。
 * TG_BOT_TOKEN 為機密，需在 Cloudflare Pages（Production）環境變數設定，
 * 且環境變數變更後需重新部署（git push 觸發建置）才會生效。
 * TG_CHAT_ID 非機密（聊天室 ID），以環境變數為主、寫死值為後備。
 */
export async function onRequestPost({ request, env }) {
  let data = {};
  try {
    data = JSON.parse(await request.text());
  } catch (e) {
    data = {};
  }

  const r = Math.max(0, Math.min(5, parseInt(data.rating, 10) || 0));
  const stars = "★".repeat(r) + "☆".repeat(5 - r);
  const page = String(data.page || "").slice(0, 200);
  const message = String(data.message || "(無留言)").slice(0, 1000);

  const token = env.TG_BOT_TOKEN;
  const chat = env.TG_CHAT_ID || "8365775688";

  if (token && chat) {
    const text =
      "💬 gulicalc 有新回饋\n\n" +
      "評分：" + stars + "（" + r + "/5）\n" +
      "頁面：" + page + "\n" +
      "留言：" + message;
    try {
      await fetch("https://api.telegram.org/bot" + token + "/sendMessage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chat, text: text, disable_web_page_preview: true }),
      });
    } catch (e) {
      // 通知失敗不影響前端
    }
  }

  return new Response(JSON.stringify({ ok: true }), {
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
  });
}
