function sendJson(res, statusCode, data) {
  res.statusCode = statusCode;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(data));
}

function getBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  if (typeof req.body === 'string') {
    try { return JSON.parse(req.body); } catch { return {}; }
  }
  return {};
}

function fail(res, error) {
  const status = Number(error.statusCode) || 500;
  const message = status >= 500 ? 'Terjadi kendala saat menyimpan data. Coba lagi.' : error.message;
  sendJson(res, status, { error: message });
}

module.exports = { fail, getBody, sendJson };
