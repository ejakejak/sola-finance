const byId = (id) => document.getElementById(id);
const state = {
  type: 'Pengeluaran',
  categories: [],
  transactionId: null,
  receipt: null,
  receiptPreviewUrl: null,
  recoveryTransaction: null,
  pending: false,
  toastTimer: null,
};

const currency = new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 });
const shortDate = new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Asia/Jakarta' });

async function request(path, options = {}) {
  const response = await fetch(path, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok && response.status !== 202) {
    const error = new Error(data.error || 'Permintaan belum berhasil.');
    error.status = response.status;
    throw error;
  }
  return { response, data };
}

function todayJakarta() {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Jakarta', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
}

function setConnection(online, text) {
  const indicator = byId('connection-state');
  indicator.classList.toggle('is-online', online);
  indicator.classList.toggle('is-offline', !online);
  indicator.lastChild.textContent = text;
}

function showToast(message, error = false) {
  const toast = byId('toast');
  toast.textContent = message;
  toast.classList.toggle('is-error', error);
  toast.classList.add('is-visible');
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 3400);
}

function showLogin(message = '') {
  byId('login-view').hidden = false;
  byId('app-view').hidden = true;
  byId('logout-button').hidden = true;
  byId('login-error').hidden = !message;
  byId('login-error').textContent = message;
  setConnection(false, 'Perlu masuk');
  setTimeout(() => byId('access-code').focus(), 0);
}

function showApp() {
  byId('login-view').hidden = true;
  byId('app-view').hidden = false;
  byId('logout-button').hidden = false;
  setConnection(true, 'Terhubung');
}

function getAmount() {
  return Number((byId('amount').value || '').replace(/\D/g, ''));
}

function setAmount(value) {
  const digits = String(value || '').replace(/\D/g, '');
  byId('amount').value = digits ? new Intl.NumberFormat('id-ID').format(Number(digits)) : '';
}

function renderCategories() {
  const select = byId('category');
  const options = state.categories.filter((item) => item.type === state.type);
  select.replaceChildren(new Option(options.length ? 'Pilih kategori' : 'Belum ada kategori', ''));
  options.forEach((item) => select.add(new Option(item.name, item.name)));
}

function setType(type) {
  state.type = type;
  document.querySelectorAll('.type-option').forEach((button) => {
    const active = button.dataset.type === type;
    button.classList.toggle('is-active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  renderCategories();
}

function formatDate(value) {
  if (!value) return '';
  const date = new Date(`${value}T12:00:00+07:00`);
  return Number.isNaN(date.valueOf()) ? value : shortDate.format(date);
}

function renderTransactions(transactions) {
  const list = byId('recent-list');
  list.replaceChildren();
  if (!transactions.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.innerHTML = '<span class="empty-symbol" aria-hidden="true">◌</span><p>Belum ada transaksi.</p>';
    list.append(empty);
    return;
  }
  transactions.forEach((item) => {
    const income = item.type === 'Pemasukan';
    const row = document.createElement('article');
    row.className = 'recent-item';
    const icon = document.createElement('span');
    icon.className = `recent-symbol ${income ? 'income' : 'expense'}`;
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = income ? '+' : '−';
    const main = document.createElement('div');
    main.className = 'recent-main';
    const title = document.createElement('strong');
    title.textContent = item.category || item.type;
    const subtitle = document.createElement('small');
    subtitle.textContent = item.note || item.method || item.type;
    main.append(title, subtitle);
    if (item.receiptUrl) {
      const link = document.createElement('a');
      link.className = 'recent-note-link';
      link.href = item.receiptUrl;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = ' · Nota';
      subtitle.append(link);
    }
    const right = document.createElement('div');
    right.className = 'recent-right';
    const amount = document.createElement('span');
    amount.className = `recent-amount ${income ? 'income' : 'expense'}`;
    amount.textContent = `${income ? '+' : '−'}${currency.format(item.amount || 0)}`;
    const date = document.createElement('small');
    date.className = 'recent-date';
    date.textContent = formatDate(item.date);
    right.append(amount, date);
    if (item.status && item.status !== 'TERSIMPAN') {
      const status = document.createElement('span');
      status.className = 'recent-status';
      status.textContent = 'Nota tertunda';
      right.append(status);
      const retry = document.createElement('button');
      retry.type = 'button';
      retry.className = 'recent-upload';
      retry.textContent = 'Unggah nota';
      retry.addEventListener('click', () => {
        state.recoveryTransaction = item;
        byId('retry-receipt').click();
      });
      right.append(retry);
    }
    row.append(icon, main, right);
    list.append(row);
  });
}

async function loadTransactions() {
  const { data } = await request('/api/transactions', { method: 'GET', headers: {} });
  renderTransactions(data.transactions || []);
}

async function loadApp() {
  const [categoryResponse] = await Promise.all([
    request('/api/categories', { method: 'GET', headers: {} }),
    loadTransactions(),
  ]);
  state.categories = categoryResponse.data.categories || [];
  renderCategories();
  showApp();
}

function lockForm(locked) {
  document.querySelectorAll('#transaction-form input, #transaction-form select, #transaction-form textarea, #transaction-form .type-option')
    .forEach((element) => { element.disabled = locked; });
  byId('submit-button').disabled = locked;
}

function showFormMessage(message, tone = 'success') {
  const box = byId('form-message');
  box.textContent = message;
  box.className = `form-message is-${tone}`;
  box.hidden = false;
}

function clearFormMessage() {
  const box = byId('form-message');
  box.hidden = true;
  box.textContent = '';
}

function clearReceipt() {
  state.receipt = null;
  if (state.receiptPreviewUrl) URL.revokeObjectURL(state.receiptPreviewUrl);
  state.receiptPreviewUrl = null;
  byId('receipt').value = '';
  byId('receipt-preview').hidden = true;
  byId('receipt-preview').replaceChildren();
}

async function compressImage(file) {
  if (!file || !file.type.startsWith('image/')) throw new Error('Pilih file gambar untuk nota.');
  if (file.size > 12 * 1024 * 1024) throw new Error('Ukuran foto asli maksimal 12 MB.');
  if (!('createImageBitmap' in window)) throw new Error('Browser ini belum mendukung kompresi gambar. Coba browser terbaru.');
  const bitmap = await createImageBitmap(file);
  const maxEdge = 1600;
  const scale = Math.min(1, maxEdge / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(bitmap.width * scale));
  canvas.height = Math.max(1, Math.round(bitmap.height * scale));
  const context = canvas.getContext('2d', { alpha: false });
  context.fillStyle = '#ffffff';
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();
  let blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.78));
  if (!blob) throw new Error('Foto tidak bisa dikompresi. Coba file gambar lain.');
  if (blob.size > 760000) blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.62));
  if (!blob || blob.size > 780000) throw new Error('Foto masih terlalu besar setelah kompresi. Pilih foto dengan resolusi lebih kecil.');
  const dataUrl = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('Foto tidak bisa dibaca.'));
    reader.readAsDataURL(blob);
  });
  return { mimeType: 'image/jpeg', base64: String(dataUrl).split(',')[1], size: blob.size, preview: URL.createObjectURL(blob), originalName: file.name };
}

function showReceiptPreview(receipt) {
  const box = byId('receipt-preview');
  box.replaceChildren();
  const image = document.createElement('img');
  image.src = receipt.preview;
  image.alt = 'Pratinjau nota yang sudah dikompresi';
  const info = document.createElement('span');
  info.className = 'receipt-info';
  const name = document.createElement('strong');
  name.textContent = receipt.originalName;
  const size = document.createElement('small');
  size.textContent = `${(receipt.size / 1024).toFixed(0)} KB · tersimpan sebagai JPEG terkompresi`;
  info.append(name, size);
  const remove = document.createElement('button');
  remove.type = 'button';
  remove.className = 'remove-file';
  remove.disabled = state.pending;
  remove.setAttribute('aria-label', 'Hapus foto nota');
  remove.textContent = '×';
  remove.addEventListener('click', clearReceipt);
  box.append(image, info, remove);
  box.hidden = false;
}

function resetForm() {
  byId('transaction-form').reset();
  byId('date').value = todayJakarta();
  setAmount('');
  clearReceipt();
  clearFormMessage();
  state.transactionId = null;
  state.pending = false;
  lockForm(false);
  setType('Pengeluaran');
}

async function handleLogin(event) {
  event.preventDefault();
  const button = event.submitter;
  const code = byId('access-code').value;
  byId('login-error').hidden = true;
  if (button) button.disabled = true;
  try {
    await request('/api/login', { method: 'POST', body: JSON.stringify({ code }) });
    byId('login-form').reset();
    await loadApp();
    byId('date').value = todayJakarta();
  } catch (error) {
    byId('login-error').textContent = error.message;
    byId('login-error').hidden = false;
  } finally {
    if (button) button.disabled = false;
  }
}

async function handleSubmit(event) {
  event.preventDefault();
  clearFormMessage();
  const amount = getAmount();
  const date = byId('date').value;
  const category = byId('category').value;
  if (!date || !amount || amount < 1 || !category) {
    showFormMessage('Lengkapi tanggal, nominal, dan kategori terlebih dahulu.', 'error');
    return;
  }
  if (!state.transactionId) state.transactionId = crypto.randomUUID();
  const button = byId('submit-button');
  button.disabled = true;
  button.innerHTML = '<span class="button-spinner" aria-hidden="true"></span>Menyimpan…';
  const body = {
    transactionId: state.transactionId,
    date,
    type: state.type,
    category,
    amount,
    note: byId('note').value.trim(),
    method: byId('method').value,
    receipt: state.receipt ? { mimeType: state.receipt.mimeType, base64: state.receipt.base64 } : null,
  };
  try {
    const { response, data } = await request('/api/transactions', { method: 'POST', body: JSON.stringify(body) });
    if (response.status === 202 || data.status === 'MENUNGGU_NOTA') {
      state.pending = true;
      lockForm(true);
      showFormMessage(data.error || 'Transaksi tercatat, nota belum terunggah. Tekan coba lagi.', 'warning');
      button.disabled = false;
      button.textContent = 'Coba unggah nota lagi';
      return;
    }
    showFormMessage('Transaksi berhasil disimpan.', 'success');
    showToast('Transaksi berhasil disimpan.');
    resetForm();
    await loadTransactions();
    setConnection(true, 'Terhubung');
  } catch (error) {
    if (error.status === 401) return showLogin(error.message);
    showFormMessage(error.message, 'error');
    button.disabled = false;
    button.textContent = state.pending ? 'Coba unggah nota lagi' : 'Coba simpan lagi →';
    setConnection(false, 'Koneksi bermasalah');
  }
}

async function handleReceiptChange(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  clearFormMessage();
  const box = byId('receipt-preview');
  box.hidden = false;
  box.textContent = 'Mengompresi foto…';
  try {
    const compressed = await compressImage(file);
    if (state.receiptPreviewUrl) URL.revokeObjectURL(state.receiptPreviewUrl);
    state.receipt = compressed;
    state.receiptPreviewUrl = compressed.preview;
    showReceiptPreview(compressed);
  } catch (error) {
    clearReceipt();
    showFormMessage(error.message, 'error');
  }
}

async function handleRecoveryReceipt(event) {
  const file = event.target.files && event.target.files[0];
  const transaction = state.recoveryTransaction;
  event.target.value = '';
  if (!file || !transaction) return;
  let compressed;
  try {
    compressed = await compressImage(file);
    const { response, data } = await request('/api/transactions', {
      method: 'POST',
      body: JSON.stringify({
        transactionId: transaction.id,
        date: transaction.date,
        type: transaction.type,
        category: transaction.category,
        amount: transaction.amount,
        note: transaction.note || '',
        method: transaction.method,
        receipt: { mimeType: compressed.mimeType, base64: compressed.base64 },
      }),
    });
    if (response.status === 202) showToast(data.error || 'Nota belum berhasil diunggah. Coba lagi.', true);
    else showToast('Nota berhasil diunggah.');
    await loadTransactions();
  } catch (error) {
    showToast(error.message, true);
  } finally {
    if (compressed) URL.revokeObjectURL(compressed.preview);
    state.recoveryTransaction = null;
  }
}

async function logout() {
  await request('/api/logout', { method: 'POST', body: '{}' }).catch(() => {});
  showLogin();
}

async function init() {
  byId('date').value = todayJakarta();
  byId('today-label').textContent = new Intl.DateTimeFormat('id-ID', { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'Asia/Jakarta' }).format(new Date());
  document.querySelectorAll('.type-option').forEach((button) => button.addEventListener('click', () => {
    if (!state.pending) setType(button.dataset.type);
  }));
  byId('amount').addEventListener('input', (event) => {
    const input = event.target;
    const cursorEnd = input.selectionStart === input.value.length;
    setAmount(input.value);
    if (cursorEnd) input.setSelectionRange(input.value.length, input.value.length);
  });
  byId('transaction-form').addEventListener('submit', handleSubmit);
  byId('login-form').addEventListener('submit', handleLogin);
  byId('receipt').addEventListener('change', handleReceiptChange);
  byId('retry-receipt').addEventListener('change', handleRecoveryReceipt);
  byId('refresh-button').addEventListener('click', () => loadTransactions().catch((error) => showToast(error.message, true)));
  byId('logout-button').addEventListener('click', logout);
  try {
    await loadApp();
    byId('date').value = todayJakarta();
  } catch (error) {
    if (error.status === 401) showLogin();
    else {
      showLogin('Aplikasi belum tersambung. Periksa pengaturan akses, lalu coba masuk kembali.');
      setConnection(false, 'Koneksi bermasalah');
    }
  }
}

init();
