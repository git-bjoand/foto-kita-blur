import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk

ctk.set_appearance_mode("dark")


class KitaBlurApp:
    """
    Controller utama aplikasi. Mengelola perpindahan halaman dan state global
    seperti path musik yang digunakan di seluruh aplikasi.
    """

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Kita-Blur — Pose Camera")
        self.root.configure(fg_color="#0D0D14")

        # Ukuran jendela seperti aplikasi biasa (tidak langsung fullscreen/maximized)
        self.root.geometry("1100x700")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Tengahkan jendela di layar
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - 1100) // 2
        y = (screen_h - 700) // 2
        self.root.geometry(f"1100x700+{x}+{y}")

        # Bind tombol Escape untuk toggle fullscreen secara manual jika dibutuhkan
        self.root.bind("<Escape>", self._toggle_fullscreen)

        self.current_page = None
        self._show_camera_page()

    def _show_camera_page(self):
        """Berpindah ke halaman kamera."""
        if self.current_page:
            self.current_page.cleanup()
            self.current_page.destroy()
        from src.camera_page import CameraPage
        self.current_page = CameraPage(self.root, self)
        self.current_page.pack(fill="both", expand=True)

    def show_preview_page(self, video_path, music_file, music_start_sec):
        """Berpindah ke halaman pratinjau setelah perekaman selesai."""
        if self.current_page:
            self.current_page.cleanup()
            self.current_page.destroy()
        from src.preview_page import PreviewPage
        self.current_page = PreviewPage(self.root, self, video_path, music_file, music_start_sec)
        self.current_page.pack(fill="both", expand=True)

    def retake(self):
        """Kembali ke halaman kamera untuk merekam ulang."""
        self._show_camera_page()

    def run(self):
        self.root.mainloop()

    def _toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode."""
        is_fullscreen = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not is_fullscreen)
        if is_fullscreen:
            self.root.state('zoomed')

    def _on_close(self):
        if self.current_page:
            self.current_page.cleanup()
        self.root.destroy()
