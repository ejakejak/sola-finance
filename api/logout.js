const { clearSession } = require('./_lib/auth');
const { sendJson } = require('./_lib/http');

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Metode tidak didukung.' });
  clearSession(res);
  return sendJson(res, 200, { ok: true });
};
