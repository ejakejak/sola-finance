const { hasSession } = require('./_lib/auth');
const { fail, sendJson } = require('./_lib/http');
const { getGoogleClients, SPREADSHEET_ID } = require('./_lib/google');

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') return sendJson(res, 405, { error: 'Metode tidak didukung.' });
  if (!hasSession(req)) return sendJson(res, 401, { error: 'Sesi berakhir. Masuk kembali.' });

  try {
    const { sheets } = getGoogleClients();
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SPREADSHEET_ID,
      range: 'Kategori!A2:C',
    });
    const categories = (response.data.values || [])
      .filter((row) => row[0] && row[1] && ['true', '1', 'ya'].includes(String(row[2] || '').toLowerCase()))
      .map((row) => ({ type: row[0], name: row[1] }));
    return sendJson(res, 200, { categories });
  } catch (error) {
    return fail(res, error);
  }
};
