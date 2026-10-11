const { randomUUID } = require('node:crypto');
const { hasSession } = require('./_lib/auth');
const { fail, getBody, sendJson } = require('./_lib/http');
const { getGoogleClients, SPREADSHEET_ID, DRIVE_FOLDER_ID } = require('./_lib/google');

const METHODS = new Set(['Tunai', 'Transfer Bank', 'QRIS', 'Lainnya']);
const TYPES = new Set(['Pemasukan', 'Pengeluaran']);

module.exports.config = { api: { bodyParser: { sizeLimit: '1.5mb' } } };

function cleanRow(row, index) {
  return {
    id: row[0] || '',
    date: row[1] || '',
    type: row[2] || '',
    category: row[3] || '',
    amount: Number(row[4]) || 0,
    note: row[5] || '',
    method: row[6] || '',
    receiptId: row[7] || '',
    receiptUrl: row[8] || '',
    status: row[9] || '',
    createdAt: row[10] || '',
    rowNumber: index + 2,
  };
}

async function readRows(sheets) {
  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Transaksi!A2:K',
  });
  return (response.data.values || []).map(cleanRow);
}

async function getCategories(sheets) {
  const response = await sheets.spreadsheets.values.get({
    spreadsheetId: SPREADSHEET_ID,
    range: 'Kategori!A2:C',
  });
  return (response.data.values || [])
    .filter((row) => row[0] && row[1] && ['true', '1', 'ya'].includes(String(row[2] || '').toLowerCase()))
    .map((row) => ({ type: row[0], name: row[1] }));
}

function validate(body, categories) {
  const { transactionId, date, type, category, amount, note, method, receipt } = body;
  if (!/^[0-9a-f-]{36}$/i.test(String(transactionId || ''))) throw Object.assign(new Error('ID transaksi tidak valid.'), { statusCode: 400 });
  if (!TYPES.has(type)) throw Object.assign(new Error('Pilih jenis transaksi.'), { statusCode: 400 });
  const dateValue = /^\d{4}-\d{2}-\d{2}$/.test(String(date || '')) ? Date.parse(`${date}T00:00:00.000Z`) : NaN;
  if (!Number.isFinite(dateValue) || new Date(dateValue).toISOString().slice(0, 10) !== date) {
    throw Object.assign(new Error('Tanggal transaksi tidak valid.'), { statusCode: 400 });
  }
  if (!categories.some((item) => item.type === type && item.name === category)) {
    throw Object.assign(new Error('Kategori tidak tersedia untuk jenis transaksi ini.'), { statusCode: 400 });
  }
  if (!Number.isSafeInteger(amount) || amount <= 0 || amount > 1000000000000) {
    throw Object.assign(new Error('Nominal harus berupa angka rupiah yang valid.'), { statusCode: 400 });
  }
  if (!METHODS.has(method)) throw Object.assign(new Error('Pilih metode pembayaran.'), { statusCode: 400 });
  if (String(note || '').length > 300) throw Object.assign(new Error('Catatan maksimal 300 karakter.'), { statusCode: 400 });
  if (receipt) {
    if (receipt.mimeType !== 'image/jpeg' || typeof receipt.base64 !== 'string') {
      throw Object.assign(new Error('Nota harus dikirim sebagai gambar JPEG.'), { statusCode: 400 });
    }
    if (receipt.base64.length > 1050000 || !/^[A-Za-z0-9+/]+={0,2}$/.test(receipt.base64)) {
      throw Object.assign(new Error('Ukuran gambar nota terlalu besar atau formatnya tidak valid.'), { statusCode: 400 });
    }
  }
}

async function uploadReceipt(drive, body) {
  const fileBytes = Buffer.from(body.receipt.base64, 'base64');
  if (!fileBytes.length || fileBytes.length > 780000) {
    throw Object.assign(new Error('Ukuran nota setelah kompresi terlalu besar.'), { statusCode: 400 });
  }
  if (fileBytes[0] !== 0xff || fileBytes[1] !== 0xd8 || fileBytes[2] !== 0xff) {
    throw Object.assign(new Error('Berkas nota tidak terbaca sebagai gambar JPEG.'), { statusCode: 400 });
  }
  const safeDate = body.date.replaceAll('-', '');
  const query = `'${DRIVE_FOLDER_ID}' in parents and appProperties has { key='transactionId' and value='${body.transactionId}' } and trashed = false`;
  const existing = await drive.files.list({
    q: query,
    pageSize: 5,
    fields: 'files(id,webViewLink)',
    supportsAllDrives: true,
    includeItemsFromAllDrives: true,
  });
  if (existing.data.files && existing.data.files.length) {
    const file = existing.data.files[0];
    return { id: file.id, url: file.webViewLink || `https://drive.google.com/open?id=${encodeURIComponent(file.id)}` };
  }
  const result = await drive.files.create({
    requestBody: {
      name: `Nota_${safeDate}_${body.transactionId.slice(0, 8)}.jpg`,
      mimeType: 'image/jpeg',
      parents: [DRIVE_FOLDER_ID],
      appProperties: { transactionId: body.transactionId },
    },
    media: { mimeType: 'image/jpeg', body: fileBytes },
    fields: 'id,webViewLink',
    supportsAllDrives: true,
  });
  const id = result.data.id;
  return { id, url: result.data.webViewLink || `https://drive.google.com/open?id=${encodeURIComponent(id)}` };
}

async function listTransactions(res, sheets) {
  const rows = await readRows(sheets);
  const transactions = rows
    .filter((row) => row.id)
    .sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)))
    .slice(0, 8)
    .map(({ id, date, type, category, amount, note, method, receiptUrl, status }) => ({ id, date, type, category, amount, note, method, receiptUrl, status }));
  return sendJson(res, 200, { transactions });
}

async function createTransaction(res, sheets, drive, body) {
  const categories = await getCategories(sheets);
  validate(body, categories);
  const rows = await readRows(sheets);
  let existing = rows.find((row) => row.id === body.transactionId);

  if (existing) {
    const sameRequest = existing.date === body.date && existing.type === body.type && existing.category === body.category
      && existing.amount === body.amount && existing.note === String(body.note || '').trim() && existing.method === body.method;
    if (!sameRequest) throw Object.assign(new Error('ID transaksi sudah digunakan untuk data yang berbeda.'), { statusCode: 409 });
    if (existing.status === 'TERSIMPAN') return sendJson(res, 200, { ok: true, transactionId: existing.id, status: existing.status, duplicate: true });
    if (!body.receipt) throw Object.assign(new Error('Transaksi menunggu nota. Pilih kembali foto yang sama lalu coba lagi.'), { statusCode: 409 });
  } else {
    const createdAt = new Date().toISOString();
    const initialStatus = body.receipt ? 'MENUNGGU_NOTA' : 'TERSIMPAN';
    const row = [body.transactionId, body.date, body.type, body.category, body.amount, String(body.note || '').trim(), body.method, '', '', initialStatus, createdAt];
    await sheets.spreadsheets.values.append({
      spreadsheetId: SPREADSHEET_ID,
      range: 'Transaksi!A:K',
      valueInputOption: 'RAW',
      insertDataOption: 'INSERT_ROWS',
      requestBody: { majorDimension: 'ROWS', values: [row] },
    });
    existing = (await readRows(sheets)).find((item) => item.id === body.transactionId);
  }

  if (!body.receipt) return sendJson(res, 200, { ok: true, transactionId: body.transactionId, status: 'TERSIMPAN' });

  try {
    const file = await uploadReceipt(drive, body);
    await sheets.spreadsheets.values.update({
      spreadsheetId: SPREADSHEET_ID,
      range: `Transaksi!H${existing.rowNumber}:J${existing.rowNumber}`,
      valueInputOption: 'RAW',
      requestBody: { majorDimension: 'ROWS', values: [[file.id, file.url, 'TERSIMPAN']] },
    });
    return sendJson(res, 200, { ok: true, transactionId: body.transactionId, status: 'TERSIMPAN', receiptUrl: file.url });
  } catch (error) {
    if (error.statusCode) throw error;
    return sendJson(res, 202, { ok: false, transactionId: body.transactionId, status: 'MENUNGGU_NOTA', error: 'Transaksi tercatat, tetapi nota belum berhasil ditautkan. Tekan coba lagi.' });
  }
}

module.exports = async function handler(req, res) {
  if (!hasSession(req)) return sendJson(res, 401, { error: 'Sesi berakhir. Masuk kembali.' });
  try {
    const { sheets, drive } = getGoogleClients();
    if (req.method === 'GET') return await listTransactions(res, sheets);
    if (req.method === 'POST') return await createTransaction(res, sheets, drive, req.body || {});
    return sendJson(res, 405, { error: 'Metode tidak didukung.' });
  } catch (error) {
    return fail(res, error);
  }
};
