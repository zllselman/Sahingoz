import cv2
import numpy as np
from ultralytics import YOLO
import time
import os

def termal_nisan_sistemi():
    # 1. MODELİ YÜKLE (V4 Final)
    model_yolu = r"runs/detect/sahingoz_v6_ultra_final3/weights/best.pt"
    
    if not os.path.exists(model_yolu):
        print("HATA: Model bulunamadı!")
        return

    model = YOLO(model_yolu)

    # 2. KAMERA
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)

    print("TERMAL MOD AKTİF. Çıkış için 'q'.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # 3. GÖRÜNTÜYÜ İŞLE (Siyah Beyaz Yap)
        # Önce tüm görüntüyü griye çeviriyoruz
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Takip işlemi (YOLO renkli sever ama gri de yiyebilir, biz yine de orijinali verelim)
        results = model.track(frame, persist=True, conf=0.25, verbose=False)
        
        # Ekrana basılacak son görüntü (Varsayılan: Gri Tonlamalı)
        # 3 kanallı yapalım ki üzerine renkli yazı yazabilelim
        final_goruntu = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2BGR)

        hedef_bulundu = False
        
        if results[0].boxes.id is not None:
            # En belirgin hedefi al
            box = results[0].boxes.xyxy.cpu().numpy().astype(int)[0]
            x1, y1, x2, y2 = box
            
            hedef_bulundu = True
            
            # --- EFEKT: SİYAH ARKA PLAN, BEYAZ HEDEF ---
            
            # 1. Simsiyah bir tuval oluştur
            black_canvas = np.zeros_like(gray_frame)
            
            # 2. Hedefin olduğu parçayı (ROI) al
            roi = gray_frame[y1:y2, x1:x2]
            
            # 3. Hedefi "Patlat" (Parlaklığı artır / Threshold uygula)
            # 100'ün üzerindeki her pikseli 255 (Bembeyaz) yap
            _, binary_roi = cv2.threshold(roi, 80, 255, cv2.THRESH_BINARY)
            
            # 4. Bu beyaz parçayı siyah tuvalin içine yapıştır
            black_canvas[y1:y2, x1:x2] = binary_roi
            
            # 5. Son görüntüyü bu yap (Bunu tekrar renkli formata çevir ki kırmızı yazı yazalım)
            final_goruntu = cv2.cvtColor(black_canvas, cv2.COLOR_GRAY2BGR)
            
            # --- NİŞANGAH ---
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            # Kırmızı Nişangah (Karanlıkta parlasın diye)
            cv2.line(final_goruntu, (cx - 40, cy), (cx + 40, cy), (0, 0, 255), 2)
            cv2.line(final_goruntu, (cx, cy - 40), (cx, cy + 40), (0, 0, 255), 2)
            cv2.circle(final_goruntu, (cx, cy), 20, (0, 0, 255), 2)
            
            # Bilgiler
            cv2.putText(final_goruntu, "HEDEF KILITLENDI", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(final_goruntu, f"KONUM: {cx}, {cy}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        else:
            # Hedef yoksa: Normal Siyah Beyaz (Arama Modu)
            # Ekrana yeşil "TARANIYOR..." yazısı ekle
            cv2.putText(final_goruntu, "SISTEM TARAMA MODUNDA...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Ortaya basit bir artı koy
            h, w = final_goruntu.shape[:2]
            cv2.line(final_goruntu, (w//2 - 20, h//2), (w//2 + 20, h//2), (0, 200, 0), 1)
            cv2.line(final_goruntu, (w//2, h//2 - 20), (w//2, h//2 + 20), (0, 200, 0), 1)

        cv2.imshow("SAHINGOZ - Termal Nisan Modu", final_goruntu)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    termal_nisan_sistemi()