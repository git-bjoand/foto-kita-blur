import cv2
import numpy as np
import math

# PENTING: Fallback aman untuk memuat submodul MediaPipe di berbagai lingkungan Python
try:
    import mediapipe.solutions.pose as mp_pose
    import mediapipe.solutions.drawing_utils as mp_drawing
    import mediapipe.solutions.drawing_styles as mp_drawing_styles
except ModuleNotFoundError:
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

class PoseDetector:
    """
    PoseDetector bertugas mendeteksi koordinat tubuh (landmarks) dari frame kamera
    dan mengklasifikasikan apakah pose pemicu blur sedang aktif.
    """
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_pose = mp_pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            enable_segmentation=False, # Dinonaktifkan karena menggunakan full screen blur (lebih cepat)
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_drawing = mp_drawing
        self.mp_drawing_styles = mp_drawing_styles

    def process_frame(self, frame):
        """
        Memproses frame BGR dari kamera, mengonversi ke RGB, melacak pose,
        dan mengklasifikasikan jenis gerakan pemicu blur.
        """
        # Konversi format BGR bawaan OpenCV ke RGB bawaan MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        
        # Proses gambar dengan model Pose MediaPipe
        results = self.pose.process(rgb_frame)
        
        # Buat frame dapat ditulis kembali
        rgb_frame.flags.writeable = True
        
        active_pose = None
        is_triggered = False
        landmarks_dict = {}
        segmentation_mask = None
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            h, w, c = frame.shape
            
            # Helper untuk mengubah koordinat normalisasi (0.0 - 1.0) ke koordinat piksel layar
            def get_pixel_coords(lm):
                return int(lm.x * w), int(lm.y * h)
            
            # Mengambil landmark koordinat utama untuk pose
            # Hidung (0), Telinga (7, 8), Bahu (11, 12), Pergelangan Tangan (15, 16)
            nose = landmarks[0]
            left_ear = landmarks[7]
            right_ear = landmarks[8]
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_wrist = landmarks[15]
            right_wrist = landmarks[16]
            
            # Menyimpan koordinat piksel untuk visualisasi HUD
            landmarks_dict = {
                'nose': get_pixel_coords(nose),
                'left_ear': get_pixel_coords(left_ear),
                'right_ear': get_pixel_coords(right_ear),
                'left_shoulder': get_pixel_coords(left_shoulder),
                'right_shoulder': get_pixel_coords(right_shoulder),
                'left_wrist': get_pixel_coords(left_wrist),
                'right_wrist': get_pixel_coords(right_wrist)
            }
            
            # Visibilitas minimal agar deteksi dianggap valid (skor 0.0 - 1.0)
            min_vis = 0.5
            
            # --- LOGIKA PENENTUAN POSE ---
            
            # 1. Pose: Angkat Tangan di Atas Kepala
            # Pada koordinat layar, titik Y=0 berada di atas, sehingga posisi "lebih tinggi" memiliki nilai Y yang lebih kecil.
            hand_raised_offset = -0.10
            left_hand_raised = (left_wrist.visibility > min_vis and 
                                left_wrist.y < (nose.y - hand_raised_offset))
            right_hand_raised = (right_wrist.visibility > min_vis and 
                                 right_wrist.y < (nose.y - hand_raised_offset))
            
            # 2. Pose: Tangan di Pipi (Cute Cheek Pose)
            # Menghitung jarak Euclid antara pergelangan tangan dan telinga
            dist_left_wrist_ear = math.hypot(left_wrist.x - left_ear.x, left_wrist.y - left_ear.y)
            dist_right_wrist_ear = math.hypot(right_wrist.x - right_ear.x, right_wrist.y - right_ear.y)
            
            cute_pose_threshold = 0.08
            is_cute_left = left_wrist.visibility > min_vis and dist_left_wrist_ear < cute_pose_threshold
            is_cute_right = right_wrist.visibility > min_vis and dist_right_wrist_ear < cute_pose_threshold
            
            # 3. Pose: Menyilangkan Tangan di Dada (Arms Crossed)
            # Tangan kiri dekat dengan bahu kanan dan tangan kanan dekat dengan bahu kiri
            dist_left_wrist_r_shoulder = math.hypot(left_wrist.x - right_shoulder.x, left_wrist.y - right_shoulder.y)
            dist_right_wrist_l_shoulder = math.hypot(right_wrist.x - left_shoulder.x, right_wrist.y - left_shoulder.y)
            
            crossed_threshold = 0.12
            is_crossed = (left_wrist.visibility > min_vis and right_wrist.visibility > min_vis and 
                          dist_left_wrist_r_shoulder < crossed_threshold and dist_right_wrist_l_shoulder < crossed_threshold)
            
            # Klasifikasi prioritas pose
            if left_hand_raised and right_hand_raised:
                active_pose = "KEDUA TANGAN DIANGKAT"
                is_triggered = True
            elif left_hand_raised:
                active_pose = "TANGAN KIRI DIANGKAT"
                is_triggered = True
            elif right_hand_raised:
                active_pose = "TANGAN KANAN DIANGKAT"
                is_triggered = True
            elif is_cute_left and is_cute_right:
                active_pose = "POSE PIPI (CUTE CHEEK)"
                is_triggered = True
            elif is_cute_left:
                active_pose = "POSE PIPI KIRI"
                is_triggered = True
            elif is_cute_right:
                active_pose = "POSE PIPI KANAN"
                is_triggered = True
            elif is_crossed:
                active_pose = "TANGAN DISILANGKAN"
                is_triggered = True
            
            # Ambil masker segmentasi tubuh untuk efek blur latar belakang
            if results.segmentation_mask is not None:
                segmentation_mask = results.segmentation_mask
                
        return {
            'is_triggered': is_triggered,
            'active_pose': active_pose,
            'landmarks': landmarks_dict,
            'raw_results': results,
            'segmentation_mask': segmentation_mask
        }
        
    def close(self):
        """Mematikan resource MediaPipe secara bersih."""
        self.pose.close()
