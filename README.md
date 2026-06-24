# 🌸 FOTO-KITA-BLUR — Kamera AI Sensor Gerakan (Pose-Triggered Camera Blur)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.14-purple.svg)](https://mediapipe.dev/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-orange.svg)](https://github.com/TomSchimansky/CustomTkinter)

**foto-Kita-Blur** adalah aplikasi kamera berbasis desktop yang dirancang dengan antarmuka modern (Dark Neon Theme) menggunakan CustomTkinter. Aplikasi ini menggunakan teknologi AI **MediaPipe Pose** untuk mendeteksi gestur tubuh Anda secara _real-time_ dan otomatis memicu efek **Gaussian Blur** yang halus ketika gerakan pemicu terdeteksi.

---

## ✨ Fitur Utama

- 📸 **AI Pose Triggered Blur:** Secara otomatis memburamkan seluruh layar ketika Anda melakukan gerakan pemicu:
    - 🙋‍♂️ **Mengangkat tangan** di atas kepala (satu atau kedua tangan).
    - 🌸 **Cute Cheek Pose** (tangan ditaruh di dekat pipi/telinga).
    - 🙅‍♂️ **Menyilangkan tangan** di depan dada.
- 🎵 **Sinkronisasi Musik Otomatis:** Perekaman video berdurasi tepat **28 detik** diiringi lagu dari detik ke-24 secara otomatis.
- ⏱ **Perekaman Stabil & Sinkron (1x Speed):** Menghasilkan video keluaran yang pas, mulus, dan tersinkronisasi penuh dengan musik (tidak terlalu cepat/lambat).
- 👁 **Halaman Pratinjau (Preview Page):** Putar ulang hasil rekaman secara melingkar (_looping_) lengkap dengan audio yang ikut melakukan _loop_ selaras dengan video.
- 💾 **Simpan Mudah:** Simpan video favorit Anda langsung ke folder bawaan sistem (`User/Videos/foto-Kita-Blur/`) dengan satu tombol.
- ⚡ **Super Ringan & Lancar (High Performance):** Dioptimalkan secara mendalam menggunakan model **MediaPipe Lite** dan teknik **Downscaled Blur** untuk memastikan performa tetap mulus di 30 FPS bahkan pada laptop berspesifikasi rendah.

---

## 🛠 Struktur Proyek

```text
foto-kita-blur/
├── assets/
│   └── Sal_Priadi_-_Foto_kita_blur_(mp3.pm).mp3  # File musik latar
├── output/                                      # Folder penyimpanan video sementara
├── src/
│   ├── app.py           # Controller utama & manajemen jendela (fullscreen/maximized)
│   ├── camera_page.py   # Halaman kamera utama & mekanisme perekaman
│   ├── preview_page.py  # Halaman pratinjau, simpan, retake, & loop musik
│   ├── detector.py      # Pengolah AI (MediaPipe Pose landmark & klasifikasi gestur)
│   ├── effects.py       # Efek visual Gaussian Blur (Downscaling mipmap)
│   └── main.py          # Entrypoint/titik masuk aplikasi
├── requirements.txt     # Daftar dependensi modul Python
└── README.md            # Dokumentasi panduan ini
```

---

## 🚀 Panduan Instalasi & Penggunaan

### 1. Prasyarat

Pastikan Anda sudah menginstal **Python 3.10** ke atas di sistem operasi Windows Anda.

### 2. Klon / Siapkan Folder Proyek

Masuk ke terminal/Powershell Anda dan arahkan ke direktori proyek `foto-kita-blur`:

```powershell
cd d:\project\py\foto-kita-blur
```

### 3. Buat dan Aktifkan Virtual Environment (venv)

```powershell
# Membuat virtual environment
python -m venv venv

# Mengaktifkan virtual environment di Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

### 4. Instal Dependensi

Instal semua pustaka pihak ketiga yang dibutuhkan:

```powershell
pip install -r requirements.txt
```

### 5. Jalankan Aplikasi

Jalankan perintah berikut untuk membuka aplikasi:

```powershell
python src/main.py
```

---

## ⌨️ Kontrol Keyboard & Navigasi

| Tombol / Aksi         | Deskripsi                                                                   |
| --------------------- | --------------------------------------------------------------------------- |
| **⏺ START RECORDING** | Memulai perekaman video 28 detik                                            |
| **💾 SAVE**           | Menyimpan hasil rekaman secara permanen ke folder `Videos/foto-Kita-Blur/`. |
| **↩ RETAKE**          | Membuang hasil rekaman sementara dan kembali ke halaman kamera.             |
| **`Escape` (Esc)**    | Masuk atau keluar dari mode layar penuh (OS Fullscreen) secara manual.      |

---

## ⚡ Detail Optimasi Performa (Anti Lag & Smooth)

Untuk menghindari masalah lag (patah-patah) dan kecepatan video yang tidak sinkron, aplikasi ini menerapkan teknik optimasi tingkat lanjut:

1. **Throttling AI (Inference Skip):** MediaPipe Pose detektor hanya memproses frame **tiap 3 frame sekali**. Frame di antaranya menggunakan cache deteksi terakhir. Hal ini memotong beban kerja CPU/GPU hingga **66%** tanpa mengurangi sensitivitas gestur Anda.
2. **Downscaled Blur (16x Faster):** Gambar di-resize ke 1/4 ukuran aslinya sebelum diproses dengan OpenCV Gaussian Blur, kemudian di-resize kembali ke resolusi asli. Ini mengurangi piksel yang diproses sebanyak 16x lipat sehingga efek blur berjalan instan.
3. **OpenCV C++ Resizing:** Seluruh proses penskalaan gambar sebelum ditampilkan ke layar menggunakan `cv2.resize` (berbasis C++) alih-alih pustaka PIL (Python) sehingga menghemat waktu render di Tkinter.
4. **Elapsed Frame Synchronization:** Penulisan frame ke video disinkronisasikan secara dinamis berdasarkan waktu nyata yang berjalan, memastikan kecepatan pemutaran video stabil pada kecepatan asli **1x speed**.
