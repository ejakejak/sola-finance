# SOLA Finance

Aplikasi satu halaman untuk mencatat pemasukan dan pengeluaran SOLA Konveksi. Aplikasi memakai Google Sheets untuk ledger dan Google Drive untuk foto nota yang sudah dikompresi di browser.

## Yang sudah disiapkan

- Tab `Transaksi` dengan kolom ID, tanggal, jenis, kategori, nominal, catatan, metode, tautan nota, status, dan waktu input.
- Tab `Kategori` dengan kategori awal pemasukan dan pengeluaran. Tambahkan kategori baru sebagai baris di bawahnya dan isi kolom `Aktif` dengan `TRUE`.
- Form transaksi satu halaman, daftar delapan catatan terakhir, dan kode akses bersama untuk Finance.
- Foto nota diperkecil menjadi JPEG sebelum dikirim. Foto asli tidak diunggah aplikasi.
- Kredensial service account tidak disertakan dalam source.

## Menjalankan secara lokal

1. Instal Node.js versi LTS dan Vercel CLI (`npm install -g vercel` bila belum ada), lalu jalankan `npm install`.
2. Salin `.env.example` menjadi `.env.local`.
3. Isi `GOOGLE_APPLICATION_CREDENTIALS` dengan lokasi file JSON service account yang sudah ada di komputer. Jangan salin file JSON itu ke folder project.
4. Isi `SOLA_ACCESS_CODE` dengan kode akses yang hanya dibagikan ke Finance.
5. Isi `SESSION_SECRET` dengan nilai acak minimal 32 karakter. Contoh untuk membuat nilai acak:

   ```powershell
   node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
   ```

6. Jalankan `npm run dev` dan buka alamat lokal yang ditampilkan Vercel CLI.

Spreadsheet dan folder Drive sudah ditetapkan di `.env.example`. Jika tujuan berubah, ubah `SOLA_SPREADSHEET_ID` atau `SOLA_DRIVE_FOLDER_ID`.

## Menyiapkan Vercel

Atur variabel ini di Project Settings → Environment Variables:

- `GOOGLE_SERVICE_ACCOUNT_JSON`: seluruh isi JSON service account, sebagai secret Vercel. Jangan taruh nilainya di repository.
- `SOLA_SPREADSHEET_ID`: ID spreadsheet.
- `SOLA_DRIVE_FOLDER_ID`: ID folder nota.
- `SOLA_ACCESS_CODE`: kode akses panjang yang dibagikan ke staf Finance.
- `SESSION_SECRET`: string acak minimal 32 karakter.

Pastikan Sheets API dan Drive API aktif di project Google Cloud, lalu service account diberi akses edit ke spreadsheet dan izin menambahkan file ke folder nota. Aplikasi memakai cookie sesi `HttpOnly` dan hanya melayani pencatatan setelah kode akses benar.

## Catatan alur penyimpanan

Jika transaksi memakai nota, aplikasi mencatat transaksi lebih dulu dengan status `MENUNGGU_NOTA`, mengunggah JPEG terkompresi ke folder Drive, lalu menandai transaksi `TERSIMPAN`. Bila upload terputus, tombol coba lagi memakai ID transaksi yang sama dan pencarian file berdasarkan ID itu untuk mencegah unggahan nota ganda.

Pembetulan transaksi dilakukan langsung pada spreadsheet untuk saat ini. Hindari menghapus baris yang sudah tersimpan agar riwayat tetap utuh.
