import os
import sys
import cv2
import time
import customtkinter as ctk
from PIL import Image

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame tidak tersedia. Musik tidak akan diputar.")

from src.detector import PoseDetector
from src.effects import EffectManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_FILE = os.path.join(BASE_DIR, "assets", "Sal_Priadi_-_Foto_kita_blur_(mp3.pm).mp3")
MUSIC_START_SEC = 24.0
RECORDING_END_SEC = 52.0
RECORDING_DURATION = RECORDING_END_SEC - MUSIC_START_SEC  # = 28 detik
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Palet warna tema gelap neon
C_BG      = "#0D0D14"
C_SURFACE = "#16162A"
C_CARD    = "#1E1E35"
C_PURPLE  = "#7F5AF0"
C_PINK    = "#FF2D55"
C_GREEN   = "#2CB67D"
C_TEXT    = "#EFEFEF"
C_MUTED   = "#6C6C8A"
C_BORDER  = "#2A2A45"


class CameraPage(ctk.CTkFrame):
    """
    Halaman utama tampilan kamera. Feed kamera mengisi penuh area yang tersedia
    dan responsif terhadap perubahan ukuran jendela secara real-time.
    """

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C_BG, corner_radius=0)
        self.app = app

        # Komponen kamera & AI
        self.cap = None
        self.detector = None
        self.effects = None

        # Status rekaman
        self.is_recording = False
        self.recording_start_time = None
        self.video_writer = None
        self.output_path = None

        # Handle untuk tkinter after() scheduler
        self._frame_job = None
        self._pulse_job = None
        self._pulse_on = True

        # Optimasi performa: batasi frekuensi inferensi MediaPipe
        self.frame_counter = 0
        self.last_results = None

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self._init_camera()
        self._init_music()
        self._build_ui()
        self._update_frame()

    # ─────────────────────── INISIALISASI ───────────────────────

    def _init_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30.0)
        self.video_fps = 30.0
        self.detector = PoseDetector()
        self.effects = EffectManager()

    def _init_music(self):
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"Warning: Gagal init pygame: {e}")

    # ─────────────────────── BANGUN UI ──────────────────────────

    def _build_ui(self):
        # ── Header Bar ──
        header = ctk.CTkFrame(self, fg_color=C_SURFACE, height=62, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=22, pady=10)

        ctk.CTkLabel(
            logo_frame,
            text="KITA",
            font=ctk.CTkFont("Helvetica", 22, "bold"),
            text_color=C_PURPLE
        ).pack(side="left")
        ctk.CTkLabel(
            logo_frame,
            text="-BLUR",
            font=ctk.CTkFont("Helvetica", 22, "bold"),
            text_color=C_TEXT
        ).pack(side="left")

        # Status indikator (kanan header)
        status_box = ctk.CTkFrame(header, fg_color=C_CARD, corner_radius=20)
        status_box.pack(side="right", padx=22, pady=14)

        self.status_dot = ctk.CTkLabel(
            status_box,
            text="●",
            font=ctk.CTkFont("Helvetica", 13),
            text_color=C_GREEN
        )
        self.status_dot.pack(side="left", padx=(12, 4), pady=6)

        self.status_label = ctk.CTkLabel(
            status_box,
            text="SIAP",
            font=ctk.CTkFont("Helvetica", 12, "bold"),
            text_color=C_MUTED
        )
        self.status_label.pack(side="left", padx=(0, 14), pady=6)

        # ── Footer Bar ── (dipasang dulu agar expand bekerja)
        footer = ctk.CTkFrame(self, fg_color=C_SURFACE, height=100, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        # Progress bar rekaman (tersembunyi saat idle)
        self.progress_wrapper = ctk.CTkFrame(footer, fg_color="transparent")
        self.progress_wrapper.pack(fill="x", padx=28, pady=(10, 0))

        prog_row = ctk.CTkFrame(self.progress_wrapper, fg_color="transparent")
        prog_row.pack(fill="x")

        self.rec_dot_label = ctk.CTkLabel(
            prog_row,
            text="⏺  REC",
            font=ctk.CTkFont("Helvetica", 11, "bold"),
            text_color=C_PINK
        )
        self.rec_dot_label.pack(side="left", padx=(0, 10))

        self.progress_bar = ctk.CTkProgressBar(
            prog_row,
            height=8,
            fg_color=C_BORDER,
            progress_color=C_PINK,
            corner_radius=4
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True)

        self.timer_label = ctk.CTkLabel(
            prog_row,
            text="0:28",
            font=ctk.CTkFont("Helvetica", 12, "bold"),
            text_color=C_TEXT,
            width=44
        )
        self.timer_label.pack(side="right", padx=(10, 0))

        self.progress_wrapper.pack_forget()  # Sembunyikan dulu

        # Tombol START
        self.start_btn = ctk.CTkButton(
            footer,
            text="⏺   START RECORDING",
            font=ctk.CTkFont("Helvetica", 15, "bold"),
            fg_color=C_PURPLE,
            hover_color="#6445CC",
            text_color="#FFFFFF",
            corner_radius=28,
            height=52,
            width=280,
            command=self._start_recording
        )
        self.start_btn.pack(expand=True, pady=12)

        # ── Label Pose Status ── (di atas footer)
        self.pose_label = ctk.CTkLabel(
            self,
            text="⬆  Angkat tangan di atas kepala untuk memicu blur",
            font=ctk.CTkFont("Helvetica", 13),
            text_color=C_MUTED
        )
        self.pose_label.pack(side="bottom", pady=(0, 6))

        # ── Area Kamera (mengisi sisa ruang sepenuhnya) ──
        cam_container = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=14)
        cam_container.pack(padx=16, pady=(12, 4), fill="both", expand=True)

        # Border neon tipis di sekeliling kamera
        self.cam_border = ctk.CTkFrame(cam_container, fg_color=C_BORDER, corner_radius=11)
        self.cam_border.pack(padx=3, pady=3, fill="both", expand=True)

        # Label kamera (fill="both", expand=True agar responsif)
        self.cam_label = ctk.CTkLabel(self.cam_border, text="", corner_radius=9)
        self.cam_label.pack(fill="both", expand=True)

    # ─────────────────────── LOOP KAMERA ────────────────────────

    def _update_frame(self):
        """Loop utama: baca frame kamera, resize ke ukuran label aktual, tampilkan."""
        if self.cap is None or not self.cap.isOpened():
            return

        start_time = time.time()

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)

            # Deteksi pose secara periodik (setiap 3 frame) untuk menghemat CPU
            self.frame_counter += 1
            if self.frame_counter % 3 == 0 or self.last_results is None:
                results = self.detector.process_frame(frame)
                self.last_results = results
            else:
                results = self.last_results

            processed = self.effects.apply_effect(frame, results)

            # Tulis frame ke file jika sedang merekam
            if self.is_recording and self.video_writer is not None:
                elapsed = time.time() - self.recording_start_time
                target_frames = int(elapsed * 30.0)
                frames_to_write = target_frames - self.frames_written

                # Duplikat frame jika pemrosesan tertinggal untuk sinkronisasi 1x speed
                for _ in range(max(1, frames_to_write)):
                    self.video_writer.write(processed)
                    self.frames_written += 1

                remaining = max(0.0, RECORDING_DURATION - elapsed)
                progress = min(1.0, elapsed / RECORDING_DURATION)

                self.progress_bar.set(progress)
                secs = int(remaining)
                self.timer_label.configure(text=f"0:{secs:02d}")

                if elapsed >= RECORDING_DURATION:
                    self._stop_recording()
                    return

            # Update label pose
            if results['is_triggered']:
                self.pose_label.configure(
                    text=f"🌸  {results['active_pose']}",
                    text_color=C_PINK
                )
                self.cam_border.configure(fg_color=C_PINK)
            else:
                self.pose_label.configure(
                    text="⬆  Angkat tangan di atas kepala untuk memicu blur",
                    text_color=C_MUTED
                )
                self.cam_border.configure(fg_color=C_BORDER)

            # ── Responsif: resize frame ke ukuran label saat ini tanpa stretch ──
            lbl_w = self.cam_label.winfo_width()
            lbl_h = self.cam_label.winfo_height()

            if lbl_w > 10 and lbl_h > 10:
                frame_h, frame_w = processed.shape[:2]
                aspect = frame_w / frame_h
                
                # Fit inside label while maintaining aspect ratio
                if lbl_w / lbl_h > aspect:
                    display_h = lbl_h
                    display_w = int(lbl_h * aspect)
                else:
                    display_w = lbl_w
                    display_h = int(lbl_w / aspect)
            else:
                display_w, display_h = 960, 540  # Fallback awal

            # Resize di OpenCV (sangat cepat karena berbasis C++) sebelum konversi PIL
            processed_resized = cv2.resize(processed, (display_w, display_h), interpolation=cv2.INTER_LINEAR)
            rgb = cv2.cvtColor(processed_resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            photo = ctk.CTkImage(img, size=(display_w, display_h))
            self.cam_label.configure(image=photo)
            self.cam_label._image = photo  # Cegah garbage collection

        processing_time = time.time() - start_time
        frame_time_ms = 1000.0 / self.video_fps
        delay = max(1, int(frame_time_ms - (processing_time * 1000)))
        self._frame_job = self.after(delay, self._update_frame)

    # ─────────────────────── REKAMAN ────────────────────────────

    def _start_recording(self):
        if self.is_recording:
            return

        ts = time.strftime("%Y%m%d_%H%M%S")
        self.output_path = os.path.join(OUTPUT_DIR, f"kita_blur_{ts}.mp4")

        # Video writer resolusi 1280x720 dengan FPS menyesuaikan kamera asli (1:1)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(self.output_path, fourcc, self.video_fps, (1280, 720))
        self.frames_written = 0

        # Putar musik dari detik ke-24
        if PYGAME_AVAILABLE and os.path.exists(MUSIC_FILE):
            try:
                pygame.mixer.music.load(MUSIC_FILE)
                pygame.mixer.music.play(start=MUSIC_START_SEC)
            except Exception as e:
                print(f"Warning: Gagal memutar musik: {e}")
        elif not os.path.exists(MUSIC_FILE):
            print(f"Info: File musik tidak ditemukan di {MUSIC_FILE}")

        self.is_recording = True
        self.recording_start_time = time.time()

        self.start_btn.pack_forget()
        self.progress_wrapper.pack(fill="x", padx=28, pady=(10, 0))
        self.progress_bar.set(0)
        self.status_label.configure(text="MEREKAM", text_color=C_PINK)
        self._pulse_rec_dot()

    def _stop_recording(self):
        """Hentikan rekaman dan pindah ke halaman preview (musik TIDAK dihentikan)."""
        self.is_recording = False

        if self._frame_job:
            self.after_cancel(self._frame_job)
            self._frame_job = None
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None

        # PENTING: Musik TIDAK dihentikan di sini agar lanjut ke preview
        # pygame.mixer.music.stop() — sengaja tidak dipanggil

        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        output_path = self.output_path

        # Cleanup kamera & detektor saja (musik tetap jalan)
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.detector:
            self.detector.close()
            self.detector = None

        # Pindah ke preview, kirim info musik agar bisa diputar ulang di preview
        self.app.show_preview_page(output_path, MUSIC_FILE, MUSIC_START_SEC)

    def _pulse_rec_dot(self):
        """Animasi kedip pada indikator REC."""
        if not self.is_recording:
            return
        self._pulse_on = not self._pulse_on
        color = C_PINK if self._pulse_on else "#5A0020"
        self.rec_dot_label.configure(text_color=color)
        self._pulse_job = self.after(500, self._pulse_rec_dot)

    # ─────────────────────── CLEANUP ────────────────────────────

    def cleanup(self):
        """Bebaskan semua resource kamera, MediaPipe, dan musik."""
        if self._frame_job:
            self.after_cancel(self._frame_job)
            self._frame_job = None
        if self._pulse_job:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.detector:
            self.detector.close()
            self.detector = None
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
