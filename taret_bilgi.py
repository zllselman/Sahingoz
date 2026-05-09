# taret_bilgi.py Bu kod, bir sanal taretin gerçek zamanlı olarak bir hedefi takip etmesini ve ekranda görsel olarak temsil etmesini sağlar.
import cv2
import numpy as np
from ultralytics import YOLO
import time

class SanalTaretKontrolcusu:
    def __init__(self, genislik, yukseklik):
        self.frame_center_x = genislik // 2
        self.frame_center_y = yukseklik // 2
        
        # PID Ayarları (Hassasiyet)
        self.kp = 0.1  # Hata katsayısı
        
        # Sanal Taret Açısı (Başlangıç: Ortada)
        self.pan_acisi = 90  # Yatay (0-180)
        self.tilt_acisi = 90 # Dikey (0-180)

    def hedefi_takip_et(self, hedef_x, hedef_y):
        # Hata Hesapla (Merkezden ne kadar uzakta?)
        error_x = hedef_x - self.frame_center_x
        error_y = hedef_y - self.frame_center_y
        
        # Taret Hareketi (Sanal)
        # Hata ne kadar büyükse, o kadar hızlı dön
        pan_degisim = error_x * self.kp * -1 # Ters yön (Kamera mantığı)
        tilt_degisim = error_y * self.kp
        
        # Yeni açıları sınırla (Servo motor limitleri: 0-180)
        self.pan_acisi = np.clip(self.pan_acisi + (pan_degisim * 0.1), 0, 180)
        self.tilt_acisi = np.clip(self.tilt_acisi + (tilt_degisim * 0.1), 0, 180)
        
        return int(self.pan_acisi), int(self.tilt_acisi), int(error_x), int(error_y)

# --- ANA PROGRAM ---
def taret_simulasyonu():
    # Şimdilik mevcut modeli kullanalım (Nike seven model :D)
    model_yolu = r"runs/detect/sahingoz_v6_ultra_final3/weights/best.pt"
    model = YOLO(model_yolu)

    cap = cv2.VideoCapture(0)
    width, height = 1280, 720
    cap.set(3, width)
    cap.set(4, height)

    taret = SanalTaretKontrolcusu(width, height)

    print("SANAL TARET AKTİF...")

    while True:
        ret, frame = cap.read()
        if not ret: break

        results = model.track(frame, persist=True, conf=0.60,imgsz=1280, verbose=False)
        
        # Ekran Merkezi (Nişangah)
        cx_ekran, cy_ekran = width // 2, height // 2
        cv2.circle(frame, (cx_ekran, cy_ekran), 20, (200, 200, 200), 2)
        cv2.line(frame, (cx_ekran-30, cy_ekran), (cx_ekran+30, cy_ekran), (200, 200, 200), 1)
        cv2.line(frame, (cx_ekran, cy_ekran-30), (cx_ekran, cy_ekran+30), (200, 200, 200), 1)

        if results[0].boxes.id is not None:
            box = results[0].boxes.xyxy.cpu().numpy().astype(int)[0]
            x1, y1, x2, y2 = box
            
            # Hedef Merkezi
            target_x = int((x1 + x2) / 2)
            target_y = int((y1 + y2) / 2)

            # Taret Hesaplaması
            pan, tilt, err_x, err_y = taret.hedefi_takip_et(target_x, target_y)

            # --- GÖRSELLEŞTİRME ---
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.line(frame, (cx_ekran, cy_ekran), (target_x, target_y), (0, 255, 255), 2) # Hedefe giden çizgi
            
            # Taret Durum Paneli
            cv2.rectangle(frame, (10, 10), (300, 120), (0, 0, 0), -1)
            cv2.putText(frame, f"TARET DURUMU", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"PAN (Yatay): {pan} deg", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f"TILT (Dikey): {tilt} deg", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Kilitlenme Durumu
            if abs(err_x) < 30 and abs(err_y) < 30:
                cv2.putText(frame, "KILITLENDI - ATES!", (target_x-50, y1-20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.circle(frame, (target_x, target_y), 10, (0, 0, 255), -1)

        cv2.imshow("SAHINGOZ - Taret Testi", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    taret_simulasyonu()