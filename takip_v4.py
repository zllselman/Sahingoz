import cv2
from ultralytics import YOLO
import time
import os

def sahingoz_v4_test_revize():
    # Model yolu
    model_yolu = r"runs/detect/sahingoz_v6_ultra_final3/weights/best.pt"
    
    print(f"SİSTEM BAŞLATILIYOR...")
    
    if not os.path.exists(model_yolu):
        print(f"HATA: Model dosyası bulunamadı! Yol: {model_yolu}")
        return

    try:
        model = YOLO(model_yolu)
    except Exception as e:
        print(f"Model yükleme hatası: {e}")
        return

    # Kamera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Renkler
    RENK_KILIT = (0, 0, 255)   
    RENK_ARAMA = (0, 255, 255) 
    FONT = cv2.FONT_HERSHEY_SIMPLEX

    son_kutu = None
    kayip_sayaci = 0
    HAFIZA_LIMITI = 15

    print("KAMERA AKTİF. Çıkmak için 'q' basın.")

    while True:
        t_baslangic = time.time()
        ret, frame = cap.read()
        if not ret: break

        # --- GÜNCELLEME BURADA ---
        # conf=0.35 yaptık (Daha hassas olsun, kaçırmasın)
        # iou=0.5 (Üst üste binen kutuları temizlesin)
        results = model.track(frame, persist=True, conf=0.35, iou=0.5, imgsz=640, verbose=False)
        
        tespit_var = False
        
        # Sadece ID'ye bakma, önce kutu var mı ona bak
        if results[0].boxes and len(results[0].boxes) > 0:
            boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
            ids = results[0].boxes.id  # ID listesi (None olabilir)
            
            # En belirgin dronu al (İlk sıradaki - en yüksek conf puanlı)
            box = boxes[0]
            x1, y1, x2, y2 = box
            
            # Hafızayı Güncelle
            son_kutu = box
            kayip_sayaci = 0
            tespit_var = True
            
            # ID var mı kontrolü
            track_id = int(ids[0].item()) if ids is not None else "Tanimlaniyor..."

            # --- GÖRSELLEŞTİRME ---
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), RENK_KILIT, 3)
            
            # Nişangah
            cv2.line(frame, (cx - 20, cy), (cx + 20, cy), RENK_KILIT, 2)
            cv2.line(frame, (cx, cy - 20), (cx, cy + 20), RENK_KILIT, 2)
            
            # Bilgi (Conf değerini de yazdıralım ki görelim)
            conf_score = results[0].boxes.conf[0].item()
            cv2.putText(frame, f"ID:{track_id} CONF:{conf_score:.2f}", (x1, y1 - 10), FONT, 0.6, RENK_KILIT, 2)

        # HAFIZA MODU
        elif son_kutu is not None and kayip_sayaci < HAFIZA_LIMITI:
            kayip_sayaci += 1
            x1, y1, x2, y2 = son_kutu
            cv2.rectangle(frame, (x1, y1), (x2, y2), RENK_ARAMA, 2)
            cv2.putText(frame, f"KAYIP.. ARANIYOR ({HAFIZA_LIMITI - kayip_sayaci})", 
                       (x1, y1 - 10), FONT, 0.6, RENK_ARAMA, 2)
        else:
            son_kutu = None

        fps = 1.0 / (time.time() - t_baslangic)
        cv2.putText(frame, f"FPS: {int(fps)}", (20, 40), FONT, 0.8, (0, 255, 0), 2)

        cv2.imshow("SAHINGOZ V4 - REVIZE", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    sahingoz_v4_test_revize()