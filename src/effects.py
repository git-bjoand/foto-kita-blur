import cv2

class EffectManager:
    """
    Mengatur efek blur dengan transisi halus.
    Tidak ada HUD atau skeleton nodes - tampilan bersih.
    """
    MODE_FULL = 1
    MODE_BOKEH = 2
    MODE_CENSOR = 3

    def __init__(self, max_blur_kernel=75, transition_speed=0.25):
        self.max_blur_kernel = max_blur_kernel
        self.transition_speed = transition_speed
        self.blur_strength = 0.0
        self.current_mode = self.MODE_BOKEH

    def update_blur_strength(self, is_triggered):
        """Interpolasi halus blur naik/turun."""
        if is_triggered:
            self.blur_strength = min(1.0, self.blur_strength + self.transition_speed)
        else:
            self.blur_strength = max(0.0, self.blur_strength - self.transition_speed)

    def apply_effect(self, frame, detector_results):
        """Menerapkan full-screen Gaussian blur dengan performa tinggi (downscaling)."""
        is_triggered = detector_results['is_triggered']
        self.update_blur_strength(is_triggered)

        if self.blur_strength <= 0.01:
            return frame.copy()

        # Hitung kernel size untuk resolusi asli
        kernel_size = int(self.max_blur_kernel * self.blur_strength)
        if kernel_size < 3:
            return frame.copy()

        # Downscale frame untuk mempercepat blur (faktor 4x)
        h, w = frame.shape[:2]
        small_w = max(16, w // 4)
        small_h = max(16, h // 4)
        small_frame = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_LINEAR)

        # Skala ukuran kernel untuk gambar kecil
        small_kernel = max(3, kernel_size // 4)
        if small_kernel % 2 == 0:
            small_kernel += 1

        # Jalankan Gaussian Blur pada gambar kecil
        small_blurred = cv2.GaussianBlur(small_frame, (small_kernel, small_kernel), 0)

        # Upscale kembali ke resolusi asli
        blurred = cv2.resize(small_blurred, (w, h), interpolation=cv2.INTER_LINEAR)

        # Blend dari asli ke blur secara bertahap (transisi halus)
        return cv2.addWeighted(blurred, self.blur_strength, frame, 1.0 - self.blur_strength, 0)

