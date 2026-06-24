import os
import cv2
import time
import shutil
import customtkinter as ctk
from PIL import Image

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

SAVE_DIR = os.path.join(os.path.expanduser("~"), "Videos", "Kita-Blur")

C_BG      = "#0D0D14"
C_SURFACE = "#16162A"
C_CARD    = "#1E1E35"
C_PURPLE  = "#7F5AF0"
C_PINK    = "#FF2D55"
C_GREEN   = "#2CB67D"
C_TEXT    = "#EFEFEF"
C_MUTED   = "#6C6C8A"
C_BORDER  = "#2A2A45"


class PreviewPage(ctk.CTkFrame):
    """
    Halaman pratinjau hasil rekaman. Video diputar berulang (loop) dan responsif
    terhadap ukuran jendela. Musik melanjutkan yang sudah berjalan dari proses
    rekaman — diputar ulang dari awal seksi lagu saat halaman ini dimuat.
    """

    def __init__(self, parent, app, video_path: str, music_file: str, music_start_sec: float):
        super().__init__(parent, fg_color=C_BG, corner_radius=0)
        self.app = app
        self.video_path = video_path
        self.music_file = music_file
        self.music_start_sec = music_start_sec

        self.cap = None
        self._frame_job = None
        self._is_playing = True
        self._saved = False

        self._build_ui()
        self._start_preview()
        self._play_music()

    # ─────────────────────── BANGUN UI ──────────────────────────

    def _build_ui(self):
        # ── Header Bar ──
        header = ctk.CTkFrame(self, fg_color=C_SURFACE, height=72, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", padx=22, pady=10)

        logo_row = ctk.CTkFrame(title_col, fg_color="transparent")
        logo_row.pack(anchor="w")
        ctk.CTkLabel(logo_row, text="KITA", font=ctk.CTkFont("Helvetica", 22, "bold"), text_color=C_PURPLE).pack(side="left")
        ctk.CTkLabel(logo_row, text="-BLUR", font=ctk.CTkFont("Helvetica", 22, "bold"), text_color=C_TEXT).pack(side="left")

        ctk.CTkLabel(
            title_col,
            text="✨  Your Moment",
            font=ctk.CTkFont("Helvetica", 12),
            text_color=C_MUTED
        ).pack(anchor="w", pady=(1, 0))

        # Badge "PREVIEW"
        badge = ctk.CTkFrame(header, fg_color=C_CARD, corner_radius=20)
        badge.pack(side="right", padx=22, pady=22)
        ctk.CTkLabel(
            badge,
            text="👁  PREVIEW",
            font=ctk.CTkFont("Helvetica", 12, "bold"),
            text_color=C_PURPLE
        ).pack(padx=16, pady=6)

        # ── Footer Bar ── (dipasang dulu agar expand bekerja)
        footer = ctk.CTkFrame(self, fg_color=C_SURFACE, height=100, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(expand=True)

        # Tombol RETAKE (outline style)
        ctk.CTkButton(
            btn_row,
            text="↩   RETAKE",
            font=ctk.CTkFont("Helvetica", 15, "bold"),
            fg_color="transparent",
            hover_color="#1A1A32",
            text_color=C_PURPLE,
            border_color=C_PURPLE,
            border_width=2,
            corner_radius=28,
            height=52,
            width=220,
            command=self._retake
        ).pack(side="left", padx=18, pady=20)

        # Tombol SAVE (filled hijau)
        self.save_btn = ctk.CTkButton(
            btn_row,
            text="💾   SAVE",
            font=ctk.CTkFont("Helvetica", 15, "bold"),
            fg_color=C_GREEN,
            hover_color="#228A5D",
            text_color="#FFFFFF",
            corner_radius=28,
            height=52,
            width=220,
            command=self._save
        )
        self.save_btn.pack(side="left", padx=18, pady=20)

        # ── Notifikasi Simpan ── (di atas footer)
        self.save_notify = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont("Helvetica", 12),
            text_color=C_GREEN
        )
        self.save_notify.pack(side="bottom", pady=(0, 6))

        # ── Area Video Preview (mengisi penuh sisa ruang) ──
        preview_container = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=14)
        preview_container.pack(padx=16, pady=(12, 4), fill="both", expand=True)

        inner_border = ctk.CTkFrame(preview_container, fg_color=C_BORDER, corner_radius=11)
        inner_border.pack(padx=3, pady=3, fill="both", expand=True)

        self.preview_label = ctk.CTkLabel(inner_border, text="", corner_radius=9)
        self.preview_label.pack(fill="both", expand=True)

    # ─────────────────────── PREVIEW VIDEO ──────────────────────

    def _start_preview(self):
        """Mulai memutar video hasil rekaman secara loop."""
        if os.path.exists(self.video_path):
            self.cap = cv2.VideoCapture(self.video_path)
            fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
            self._frame_delay = max(10, int(1000 / fps))
            self._play_frame()
        else:
            self.save_notify.configure(
                text="⚠  File video tidak ditemukan.",
                text_color=C_PINK
            )

    def _play_frame(self):
        """Loop frame-by-frame, responsif terhadap ukuran label."""
        if not self._is_playing or self.cap is None:
            return

        start_time = time.time()
        ret, frame = self.cap.read()
        if not ret:
            # Loop kembali ke frame pertama
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            # Restart musik agar tetap sinkron dengan video yang di-loop
            if PYGAME_AVAILABLE:
                try:
                    pygame.mixer.music.play(start=self.music_start_sec)
                except Exception as e:
                    print(f"Warning: Gagal me-restart musik pada loop: {e}")

        if ret:
            # Responsif: resize ke ukuran label aktual tanpa stretch
            lbl_w = self.preview_label.winfo_width()
            lbl_h = self.preview_label.winfo_height()

            if lbl_w > 10 and lbl_h > 10:
                frame_h, frame_w = frame.shape[:2]
                aspect = frame_w / frame_h
                
                # Fit inside label while maintaining aspect ratio
                if lbl_w / lbl_h > aspect:
                    display_h = lbl_h
                    display_w = int(lbl_h * aspect)
                else:
                    display_w = lbl_w
                    display_h = int(lbl_w / aspect)
            else:
                display_w, display_h = 960, 540  # Fallback

            # Resize di OpenCV (sangat cepat karena berbasis C++) sebelum konversi PIL
            frame_resized = cv2.resize(frame, (display_w, display_h), interpolation=cv2.INTER_LINEAR)
            rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            photo = ctk.CTkImage(img, size=(display_w, display_h))
            self.preview_label.configure(image=photo)
            self.preview_label._image = photo

        processing_time = time.time() - start_time
        delay = max(1, int(self._frame_delay - (processing_time * 1000)))
        self._frame_job = self.after(delay, self._play_frame)

    # ─────────────────────── MUSIK ───────────────────────────────

    def _play_music(self):
        """Putar musik dari detik musik_start_sec (sinkron dengan durasi rekaman)."""
        if not PYGAME_AVAILABLE:
            return
        if self.music_file and os.path.exists(self.music_file):
            try:
                # Selalu muat dan putar dari awal seksi musik_start_sec
                # agar sinkron sempurna dengan video pratinjau sejak detik pertama
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.play(start=self.music_start_sec)
            except Exception as e:
                print(f"Warning: Gagal memutar musik di preview: {e}")

    def _stop_music(self):
        """Hentikan musik."""
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    # ─────────────────────── AKSI TOMBOL ────────────────────────

    def _retake(self):
        """Hapus video sementara, hentikan musik, dan kembali ke kamera."""
        self._stop_music()
        self.cleanup()
        if os.path.exists(self.video_path):
            try:
                os.remove(self.video_path)
            except Exception:
                pass
        self.app.retake()

    def _save(self):
        """Simpan video ke folder pengguna. Musik tetap berjalan saat menyimpan."""
        if self._saved:
            return

        os.makedirs(SAVE_DIR, exist_ok=True)
        filename = os.path.basename(self.video_path)
        dest = os.path.join(SAVE_DIR, filename)
        try:
            shutil.copy2(self.video_path, dest)
            self._saved = True
            self.save_notify.configure(
                text=f"✅  Tersimpan di: {dest}",
                text_color=C_GREEN
            )
            # Update tombol setelah berhasil disimpan
            self.save_btn.configure(
                text="✅  TERSIMPAN",
                fg_color="#1A3A2A",
                hover_color="#1A3A2A",
                text_color=C_GREEN
            )
        except Exception as e:
            self.save_notify.configure(
                text=f"❌  Gagal menyimpan: {e}",
                text_color=C_PINK
            )

    # ─────────────────────── CLEANUP ────────────────────────────

    def cleanup(self):
        """Bebaskan resource video preview (musik diatur terpisah)."""
        self._is_playing = False
        if self._frame_job:
            self.after_cancel(self._frame_job)
            self._frame_job = None
        if self.cap:
            self.cap.release()
            self.cap = None
