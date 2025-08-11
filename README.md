# BPS News Scraper 📰

Aplikasi web scraping untuk mengumpulkan berita dari Google berdasarkan klasifikasi topik Badan Pusat Statistik (BPS) dengan fokus pada daerah **Bangkalan, Madura, dan Jawa Timur**.

## 🎯 Fitur Utama

- **Scraping Berita Otomatis**: Mengambil link berita dari Google berdasarkan topik BPS
- **Filter Regional**: Fokus pada berita dari Bangkalan, Madura, dan Jawa Timur  
- **Klasifikasi BPS Lengkap**: Menggunakan kategori resmi BPS dari A sampai U
- **Penyimpanan JSON**: Data tersimpan dalam format JSON yang mudah diakses
- **Interface Web**: Dashboard yang user-friendly dengan warna tema BPS
- **Filter Data**: Dapat memfilter hasil berdasarkan topik, daerah, dan tanggal
- **Export ke CSV**: Download data hasil scraping dalam format CSV untuk analisis lebih lanjut

## 📊 Klasifikasi Topik BPS

Aplikasi ini menggunakan klasifikasi lengkap BPS meliputi:

- **A** - Pertanian, Kehutanan, dan Perikanan
- **B** - Pertambangan dan Penggalian  
- **C** - Industri Pengolahan
- **D** - Pengadaan Listrik dan Gas
- **E** - Pengadaan Air, Pengelolaan Sampah, Limbah dan Daur Ulang
- **F** - Konstruksi
- **G** - Perdagangan Besar dan Eceran
- **H** - Transportasi dan Pergudangan
- **I** - Penyediaan Akomodasi dan Makan Minum
- **J** - Informasi dan Komunikasi
- **K** - Jasa Keuangan dan Asuransi
- **L** - Real Estate
- **M,N** - Jasa Perusahaan
- **O** - Administrasi Pemerintahan, Pertahanan dan Jaminan Sosial
- **P** - Jasa Pendidikan
- **Q** - Jasa Kesehatan dan Kegiatan Sosial
- **R,S,T,U** - Jasa lainnya

## 🚀 Instalasi dan Menjalankan

### Persyaratan Sistem
- Python 3.7+
- pip (Python package manager)
- Koneksi internet untuk scraping

### Langkah Instalasi

1. **Clone atau download project ini**
2. **Masuk ke direktori project**:
   ```bash
   cd scraping
   ```

3. **Jalankan aplikasi**:
   ```bash
   ./run.sh
   ```
   
   Atau secara manual:
   ```bash
   source venv/bin/activate
   python app.py
   ```

4. **Buka browser** dan akses:
   ```
   http://localhost:5000
   ```

## 🎨 Interface

Aplikasi menggunakan skema warna resmi BPS dengan:
- **Warna Primer**: Biru BPS (#1e3a8a, #3b82f6)
- **Layout Responsif**: Mendukung desktop dan mobile
- **Dashboard Intuitif**: Panel kontrol dan hasil yang terpisah jelas

## 📁 Struktur File

```
scraping/
├── app.py              # Aplikasi Flask utama
├── requirements.txt    # Dependencies Python
├── run.sh             # Script untuk menjalankan aplikasi
├── README.md          # Dokumentasi ini
├── venv/              # Virtual environment Python
├── templates/
│   └── index.html     # Template HTML utama
└── data/
    └── *.json         # File hasil scraping (auto-generated)
```

## 💾 Format Data JSON

Setiap berita yang di-scraping akan disimpan dengan format:

```json
{
  "title": "Judul berita",
  "link": "https://example.com/berita",
  "source": "Nama media",
  "date": "Tanggal publikasi berita (dari sumber asli, contoh: '2 hari yang lalu')",
  "query": "Query pencarian yang digunakan",
  "topic_code": "A",
  "topic_name": "Pertanian, Kehutanan, dan Perikanan", 
  "subcategory": "Tanaman Pangan",
  "region": "Jawa Timur",
  "scraped_at": "2024-01-01T10:30:00 (tanggal kapan scraping dilakukan)"
}
```

## 🔧 Penggunaan

### 1. Scraping Berita Baru
1. Pilih **Kategori BPS** dari dropdown
2. Pilih **Sub-kategori** (jika tersedia)
3. Pilih **Daerah** target atau biarkan kosong untuk semua daerah
4. Atur **Filter Tanggal** (opsional)
5. Klik **"🚀 Mulai Scraping"**

### 2. Melihat Data Tersimpan
1. Gunakan **Filter Data Tersimpan** di panel hasil
2. Filter berdasarkan:
   - Kategori topik
   - Daerah
   - Tanggal
3. Klik **"🔍 Terapkan Filter"**

### 3. Export Data ke CSV
1. Gunakan **Filter Data Tersimpan** untuk menentukan data yang ingin diekspor (opsional)
2. Klik **"📊 Export ke CSV"** 
3. File CSV akan otomatis terdownload dengan format:
   - `bps_news_data_[filter]_YYYYMMDD_HHMMSS.csv`
   - Berisi semua kolom: No, Judul, Link, Sumber, Tanggal, Kode Topik, Nama Topik, Sub Kategori, Daerah, Query, Waktu Scraping

### 4. Mengakses Data JSON
Data tersimpan di folder `data/` dengan format:
- `news_data_YYYYMMDD.json` - Data harian
- File dapat diakses langsung untuk analisis lebih lanjut

## 🌐 Daerah Target

Aplikasi fokus pada berita dari wilayah:
- **Bangkalan**
- **Madura** (secara umum)  
- **Jawa Timur** dan kota-kota besar:
  - Surabaya, Malang, Kediri, Blitar
  - Madiun, Mojokerto, Pasuruan
  - Probolinggo, Jember, Banyuwangi
  - Bondowoso, Situbondo, Lumajang
  - Bojonegoro, Tuban, Lamongan
  - Gresik, Sidoarjo

## 📝 Catatan Teknis

- **Rate Limiting**: Ada delay 1 detik antar request untuk menghindari blocking
- **User Agent**: Menggunakan user agent browser untuk compatibility
- **Error Handling**: Sistem error handling untuk koneksi dan parsing
- **Data Deduplication**: Mencegah duplikasi link yang sama
- **Responsive Design**: Interface yang responsif untuk berbagai ukuran layar

## 🛠️ Pengembangan Lanjutan

Untuk pengembangan lebih lanjut, Anda dapat:
1. Menambah sumber berita selain Google
2. Implementasi machine learning untuk klasifikasi otomatis
3. Scheduling otomatis dengan cron job
4. Export ke format Excel/CSV
5. Integrasi dengan database (PostgreSQL, MongoDB)
6. API endpoint untuk integrasi sistem lain

## 📞 Support

Jika mengalami masalah:
1. Pastikan koneksi internet stabil
2. Check apakah semua dependencies terinstall
3. Periksa log error di terminal
4. Restart aplikasi jika diperlukan

---

**Dikembangkan untuk mendukung monitoring berita ekonomi regional sesuai klasifikasi BPS** 🇮🇩
