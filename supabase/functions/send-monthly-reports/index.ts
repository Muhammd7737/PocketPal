import { createClient } from "jsr:@supabase/supabase-js@2";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// ── Date helpers ──────────────────────────────────────────────────────────────
function getLastMonth() {
  const now = new Date();
  const month = now.getMonth() === 0 ? 12 : now.getMonth();      // getMonth() is 0-indexed
  const year  = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear();
  return { month, year };
}

const MONTH_NAMES = [
  "", "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

// ── HTML builder ──────────────────────────────────────────────────────────────
function buildEmail(user: any, expenses: any[], year: number, month: number): string {
  const monthLabel = `${MONTH_NAMES[month]} ${year}`;
  const total = expenses.reduce((s: number, e: any) => s + e.amount, 0);

  // Category breakdown
  const catTotals: Record<string, number> = {};
  for (const e of expenses) {
    catTotals[e.category] = (catTotals[e.category] || 0) + e.amount;
  }
  const catSorted = Object.entries(catTotals).sort((a, b) => b[1] - a[1]);

  // Top 5 expenses
  const top5 = [...expenses].sort((a, b) => b.amount - a.amount).slice(0, 5);

  const catRows = catSorted.map(([cat, amt]) => {
    const pct = total > 0 ? (amt / total) * 100 : 0;
    return `
      <tr>
        <td style="padding:10px 16px;border-bottom:1px solid #f0f0f0;">${cat}</td>
        <td style="padding:10px 16px;border-bottom:1px solid #f0f0f0;min-width:120px;">
          <div style="background:#f0f0f0;border-radius:4px;height:8px;">
            <div style="background:#6c63ff;border-radius:4px;height:8px;width:${pct.toFixed(1)}%;"></div>
          </div>
        </td>
        <td style="padding:10px 16px;border-bottom:1px solid #f0f0f0;text-align:right;font-weight:600;">$${amt.toFixed(2)}</td>
        <td style="padding:10px 16px;border-bottom:1px solid #f0f0f0;text-align:right;color:#888;">${pct.toFixed(1)}%</td>
      </tr>`;
  }).join("");

  const top5Rows = top5.map((e: any) => {
    const d = new Date(e.date);
    const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    return `
      <tr>
        <td style="padding:10px 16px;border-bottom:1px solid #f0f0f0;color:#555;">${dateStr}</td>
        <td style="padding:10px 16px;border-bottom:1px solid #f0f0f0;">${e.description}</td>
        <td style="padding:10px 16px;border-bottom:1px solid #f0f0f0;color:#888;">${e.category}</td>
        <td style="padding:10px 16px;border-bottom:1px solid #f0f0f0;text-align:right;font-weight:600;color:#e53e3e;">$${e.amount.toFixed(2)}</td>
      </tr>`;
  }).join("");

  // Budget bar (only if limit set)
  let budgetSection = "";
  if (user.budget_limit && user.budget_limit > 0) {
    const pct = Math.min((total / user.budget_limit) * 100, 100);
    const color = pct >= 90 ? "#e53e3e" : pct >= 70 ? "#f6ad55" : "#48bb78";
    const status = pct >= 90 ? "⚠️ Over or near your budget!" : "✅ Within budget";
    budgetSection = `
      <div style="background:#f9f9ff;border-radius:12px;padding:24px;margin:24px 32px;border:1px solid #e8e8ff;">
        <h3 style="margin:0 0 16px;color:#333;font-size:16px;">💰 Budget Tracker</h3>
        <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
          <span style="color:#555;">Spent: <strong>$${total.toFixed(2)}</strong></span>
          <span style="color:#555;">Limit: <strong>$${user.budget_limit.toFixed(2)}</strong></span>
        </div>
        <div style="background:#e8e8e8;border-radius:6px;height:12px;margin-bottom:8px;">
          <div style="background:${color};border-radius:6px;height:12px;width:${pct.toFixed(1)}%;"></div>
        </div>
        <p style="margin:0;color:${color};font-weight:600;">${status} (${pct.toFixed(1)}% used)</p>
      </div>`;
  }

  return `<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:600px;margin:40px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

    <div style="background:linear-gradient(135deg,#6c63ff 0%,#48bb78 100%);padding:40px 32px;text-align:center;">
      <h1 style="margin:0;color:#fff;font-size:28px;font-weight:700;">💸 PocketPal</h1>
      <p style="margin:8px 0 0;color:rgba(255,255,255,0.85);font-size:16px;">Your ${monthLabel} Spending Report</p>
    </div>

    <div style="padding:32px 32px 0;">
      <p style="margin:0;font-size:16px;color:#333;">Hi <strong>${user.username}</strong>,</p>
      <p style="color:#555;line-height:1.6;">Here's your spending summary for <strong>${monthLabel}</strong>.
      You made <strong>${expenses.length} transaction${expenses.length !== 1 ? "s" : ""}</strong> totalling:</p>
      <div style="text-align:center;padding:24px;background:#f9f9ff;border-radius:12px;margin:16px 0;">
        <span style="font-size:48px;font-weight:700;color:#6c63ff;">$${total.toFixed(2)}</span>
        <p style="margin:4px 0 0;color:#888;font-size:14px;">Total spent in ${monthLabel}</p>
      </div>
    </div>

    ${budgetSection}

    <div style="padding:0 32px;">
      <h3 style="color:#333;font-size:16px;margin:24px 0 12px;">📊 Spending by Category</h3>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="background:#f9f9f9;">
            <th style="padding:10px 16px;text-align:left;color:#888;font-weight:600;border-bottom:2px solid #eee;">Category</th>
            <th style="padding:10px 16px;text-align:left;color:#888;font-weight:600;border-bottom:2px solid #eee;">Breakdown</th>
            <th style="padding:10px 16px;text-align:right;color:#888;font-weight:600;border-bottom:2px solid #eee;">Amount</th>
            <th style="padding:10px 16px;text-align:right;color:#888;font-weight:600;border-bottom:2px solid #eee;">%</th>
          </tr>
        </thead>
        <tbody>${catRows}</tbody>
      </table>
    </div>

    <div style="padding:0 32px;">
      <h3 style="color:#333;font-size:16px;margin:32px 0 12px;">🔝 Top 5 Expenses</h3>
      <table style="width:100%;border-collapse:collapse;font-size:14px;">
        <thead>
          <tr style="background:#f9f9f9;">
            <th style="padding:10px 16px;text-align:left;color:#888;font-weight:600;border-bottom:2px solid #eee;">Date</th>
            <th style="padding:10px 16px;text-align:left;color:#888;font-weight:600;border-bottom:2px solid #eee;">Description</th>
            <th style="padding:10px 16px;text-align:left;color:#888;font-weight:600;border-bottom:2px solid #eee;">Category</th>
            <th style="padding:10px 16px;text-align:right;color:#888;font-weight:600;border-bottom:2px solid #eee;">Amount</th>
          </tr>
        </thead>
        <tbody>${top5Rows}</tbody>
      </table>
    </div>

    <div style="padding:32px;margin-top:32px;border-top:1px solid #f0f0f0;text-align:center;">
      <p style="margin:0;color:#aaa;font-size:12px;">You're receiving this because you have a PocketPal account.</p>
      <p style="margin:4px 0 0;color:#aaa;font-size:12px;">© ${year} PocketPal. Keep tracking, keep saving! 💚</p>
    </div>
  </div>
</body>
</html>`;
}

// ── Main handler ──────────────────────────────────────────────────────────────
Deno.serve(async (req) => {
  // Supabase automatically secures Edge Functions with the anon/service key
  // but you can add an extra secret check here if you want
  const { month, year } = getLastMonth();
  const startDate = `${year}-${String(month).padStart(2, "0")}-01`;
  const endDate   = new Date(year, month, 0).toISOString().split("T")[0]; // last day of month

  // 1. Fetch all users with emails
  const { data: users, error: userErr } = await supabase
    .from("user")
    .select("id, username, email, budget_limit")
    .not("email", "is", null);

  if (userErr) return new Response(JSON.stringify({ error: userErr.message }), { status: 500 });

  let sent = 0, skipped = 0;

  for (const user of users ?? []) {
    // 2. Fetch that user's expenses for last month
    const { data: expenses } = await supabase
      .from("expense")
      .select("description, amount, category, date, notes")
      .eq("user_id", user.id)
      .gte("date", startDate)
      .lte("date", endDate)
      .order("date");

    if (!expenses || expenses.length === 0) { skipped++; continue; }

    // 3. Send via Resend
    const html = buildEmail(user, expenses, year, month);
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from:    "PocketPal <reports@yourdomain.com>",  // ← swap your verified domain
        to:      user.email,
        subject: `💸 PocketPal — Your ${MONTH_NAMES[month]} ${year} Report`,
        html,
      }),
    });

    if (res.ok) sent++; else skipped++;
  }

  return new Response(JSON.stringify({ sent, skipped, month: `${year}-${month}` }), {
    headers: { "Content-Type": "application/json" },
  });
});