const crypto = require('node:crypto');

const COOKIE_NAME = 'sola_session';
const SESSION_SECONDS = 60 * 60 * 12;

function getCookie(req, name) {
  const cookies = req.headers.cookie || '';
  const entry = cookies.split(';').map((part) => part.trim()).find((part) => part.startsWith(`${name}=`));
  if (!entry) return '';
  try { return decodeURIComponent(entry.slice(name.length + 1)); } catch { return ''; }
}

function sign(value, secret) {
  return crypto.createHmac('sha256', secret).update(value).digest('base64url');
}

function makeCookie(value, maxAge) {
  const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
  return `${COOKIE_NAME}=${encodeURIComponent(value)}; HttpOnly; Path=/; SameSite=Lax; Max-Age=${maxAge}${secure}`;
}

function requireConfiguration() {
  const accessCode = process.env.SOLA_ACCESS_CODE || '';
  const secret = process.env.SESSION_SECRET || '';
  if (accessCode.length < 10 || secret.length < 32) {
    const error = new Error('SOLA_ACCESS_CODE dan SESSION_SECRET perlu dikonfigurasi.');
    error.statusCode = 503;
    throw error;
  }
  return { accessCode, secret };
}

function issueSession(res) {
  const { secret } = requireConfiguration();
  const expiresAt = Math.floor(Date.now() / 1000) + SESSION_SECONDS;
  const payload = String(expiresAt);
  res.setHeader('Set-Cookie', makeCookie(`${payload}.${sign(payload, secret)}`, SESSION_SECONDS));
}

function clearSession(res) {
  const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
  res.setHeader('Set-Cookie', `${COOKIE_NAME}=; HttpOnly; Path=/; SameSite=Lax; Max-Age=0${secure}`);
}

function checkAccessCode(candidate) {
  const { accessCode } = requireConfiguration();
  const expected = crypto.createHash('sha256').update(accessCode).digest();
  const actual = crypto.createHash('sha256').update(String(candidate || '')).digest();
  return crypto.timingSafeEqual(expected, actual);
}

function hasSession(req) {
  let config;
  try {
    config = requireConfiguration();
  } catch {
    return false;
  }
  const value = getCookie(req, COOKIE_NAME);
  const [payload, signature] = value.split('.');
  if (!payload || !signature || !/^\d+$/.test(payload)) return false;
  const expected = sign(payload, config.secret);
  const a = Buffer.from(signature);
  const b = Buffer.from(expected);
  return a.length === b.length && crypto.timingSafeEqual(a, b) && Number(payload) > Math.floor(Date.now() / 1000);
}

module.exports = { checkAccessCode, clearSession, hasSession, issueSession, requireConfiguration };
