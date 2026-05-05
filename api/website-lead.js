import { Resend } from 'resend';

const REQUIRED_FIELDS = ['bizName', 'yourName', 'phone', 'email', 'niche'];

function emailHtml({ bizName, yourName, phone, email, niche, city, message }) {
  const rows = [
    ['Business Name', bizName],
    ['Contact Name', yourName],
    ['Phone', `<a href="tel:${phone}" style="color:#3b82f6;text-decoration:none">${phone}</a>`],
    ['Email', `<a href="mailto:${email}" style="color:#3b82f6;text-decoration:none">${email}</a>`],
    ['Trade / Niche', niche],
    city ? ['City', city] : null,
    message ? ['Message', message] : null,
  ].filter(Boolean);

  const tableRows = rows.map(([label, value]) => `
    <tr>
      <td style="padding:10px 16px;font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#999;white-space:nowrap;border-bottom:1px solid #f0ece4">${label}</td>
      <td style="padding:10px 16px;font-size:14px;color:#1a1816;border-bottom:1px solid #f0ece4">${value}</td>
    </tr>
  `).join('');

  return `<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:40px 0;background:#f0ece4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:2px;overflow:hidden;max-width:560px">

        <!-- Header -->
        <tr>
          <td style="padding:28px 32px 20px;border-bottom:1px solid #1a1816">
            <p style="margin:0 0 8px;font-size:11px;font-weight:600;letter-spacing:0.1em;color:#999;text-transform:uppercase">RSWebWorks</p>
            <span style="display:inline-block;font-size:10px;font-weight:600;letter-spacing:0.08em;color:#fff;background:#1a1816;padding:4px 10px;border-radius:2px;text-transform:uppercase">NEW LEAD</span>
          </td>
        </tr>

        <!-- Name + email hero -->
        <tr>
          <td style="padding:24px 32px 16px">
            <h1 style="margin:0 0 4px;font-size:22px;font-weight:700;color:#1a1816;letter-spacing:-0.02em">${yourName}</h1>
            <a href="mailto:${email}" style="font-size:14px;color:#555;text-decoration:none">${email}</a>
          </td>
        </tr>

        <!-- Fields table -->
        <tr>
          <td style="padding:0 16px 8px">
            <table width="100%" cellpadding="0" cellspacing="0">
              ${tableRows}
            </table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:16px 32px;background:#f0ece4;border-top:1px solid #e8e4dc;text-align:center">
            <p style="margin:0;font-size:11px;color:#aaa">Submitted via rswebworks.com</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const body = req.body || {};

  for (const field of REQUIRED_FIELDS) {
    if (!body[field] || !String(body[field]).trim()) {
      return res.status(400).json({ error: `Missing required field: ${field}` });
    }
  }

  const payload = {
    bizName:  String(body.bizName).trim(),
    yourName: String(body.yourName).trim(),
    phone:    String(body.phone).trim(),
    email:    String(body.email).trim().toLowerCase(),
    niche:    String(body.niche).trim(),
    city:     body.city ? String(body.city).trim() : '',
    message:  body.message ? String(body.message).trim() : '',
  };

  const resend = new Resend(process.env.RESEND_API_KEY);

  try {
    await resend.emails.send({
      from:    'RSWebWorks <hello@send.revshiftmedia.com>',
      to:      'hello@rswebworks.com',
      subject: `[NEW LEAD] ${payload.bizName} — ${payload.niche}`,
      html:    emailHtml(payload),
    });
  } catch (err) {
    console.error('[website-lead] Resend error:', err);
    // Don't block user on email failure
  }

  return res.status(200).json({ success: true });
}
