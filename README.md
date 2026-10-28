# IDRIS website (company site + waitlist)

Repo ini terpisah dari backend Idris AI dan dari Idris Studio.

- `index.html`: website (Product, Design partners, Investors, Careers, Waitlist).
- `server.py` + `waitlist.py`: server kecil yang menampilkan website dan menyimpan pendaftar waitlist. Hanya pakai Python standar, tanpa library tambahan.
- `tests/test_waitlist.py`: tes penyimpanan, statistik, ekspor, dan hapus data.

## Pasang di Render (sekali)
1. New → **Web Service** → pilih repo ini.
   - Name: `idris-website`, supaya alamatnya menjadi https://idris-website.onrender.com. Kalau nama itu sudah dipakai orang, kabari tim solver supaya alamat di `index.html` disesuaikan.
   - Runtime: Python.
   - Build command: `pip install -r requirements.txt`
   - Start command: `python server.py`
   - Plan: Starter. Paket gratis tidak bisa memakai disk, jadi data pendaftar akan hilang.
2. **Disks** → Add disk: mount path `/var/data`, ukuran 1 GB.
3. **Environment**:
   - `IDRIS_DATA_DIR` = `/var/data`
   - `IDRIS_ADMIN_TOKEN` = kata sandi panjang buatan sendiri (jangan dibagikan)
4. Buka `https://idris-website.onrender.com/health`. Bagian `waitlist` harus menunjukkan `storage_configured: true` dan `admin_configured: true`.

Website langsung tampil di `https://idris-website.onrender.com/`. GitHub Pages tidak wajib. Kalau tetap ingin GitHub Pages, aktifkan Pages di repo ini; form tetap mengirim ke server Render di atas.

## Melihat pendaftar
- Ringkasan: `https://idris-website.onrender.com/waitlist/stats?token=TOKEN`
- Semua data (CSV): `https://idris-website.onrender.com/waitlist/export.csv?token=TOKEN`

## Tanpa server (alternatif gratis)
Kalau tidak mau membayar server, ganti form dengan Google Forms/Tally → Google Sheets. Minta tim solver menyambungkannya.
