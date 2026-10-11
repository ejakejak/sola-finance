const { checkAccessCode, issueSession } = require('./_lib/auth');
const { fail, getBody, sendJson } = require('./_lib/http');

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Metode tidak didukung.' });
  try {
    const { code } = getBody(req);
    if (!checkAccessCode(code)) return sendJson(res, 401, { error: 'Kode akses belum sesuai.' });
    issueSession(res);
    return sendJson(res, 200, { ok: true });
  } catch (error) {
    return fail(res, error);
  }
};
