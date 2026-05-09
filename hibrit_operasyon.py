import cv2
import numpy as np
from ultralytics import YOLO
import time
import os
import sys
import sounddevice as sd
import librosa
import joblib
import threading
import warnings

# ====================================================================
# RASPBERRY PI 5 - GPIOZERO ve LGPIO ENTEGRASYONU
# ====================================================================
try:
    from gpiozero import OutputDevice, Servo
    from gpiozero.pins.lgpio import LGPIOFactory
    from gpiozero import Device
    # Raspberry Pi 5 için varsayılan pin factory lgpio olarak ayarlanır
    Device.pin_factory = LGPIOFactory()
    GPIO_AVAILABLE = True
except ImportError:
    print("[UYARI] gpiozero veya lgpio kütüphanesi bulunamadı!")
    print("[UYARI] Sistem GPIO modülleri kapalı olarak (Simülasyon modunda) çalışacak.")
    GPIO_AVAILABLE = False

# Sklearn uyarılarını sustur
warnings.filterwarnings('ignore')

# ====================================================================
# SİSTEM YAPILANDIRMASI VE LİNUX UYUMLU DOSYA YOLLARI
# ====================================================================
# Scriptin bulunduğu dizini baz alır
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_MODEL_PATH = os.path.join(BASE_DIR, "drone_audio_model.joblib")
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "best.pt")

SAMPLE_RATE = 22050
DURATION = 1.0 # 1 saniyelik dinleme blokları

# Headless kontrolü: Ortam değişkenlerinde DISPLAY var mı?
DISPLAY_AVAILABLE = 'DISPLAY' in os.environ or 'WAYLAND_DISPLAY' in os.environ

# ====================================================================
# DONANIM (GPIO) PİN TANIMLAMALARI (Raspberry Pi 5)
# ====================================================================
if GPIO_AVAILABLE:
    # Pan Motoru: Tower Pro MG995 (360 Derece Sürekli Dönen Servo)
    pan_servo = Servo(17) 
    
    # Tilt Motoru: Tower Pro MG995 (180 Derece Standart Servo)
    tilt_servo = Servo(13)
    
    # Ateşleme / Lazer / Röle
    relay_pin = OutputDevice(22)
else:
    pan_servo, tilt_servo, relay_pin = None, None, None

# ====================================================================
# GLOBAL DEĞİŞKENLER VE HABERLEŞME
# ====================================================================
sistem_aktif = True
hedef_acisi = None    # None ise motor 360 döner, sayı ise o açıya döner
gorsel_kilit = False  # Kameranın hedefe kilitlenme durumu
takip_hatasi_x = 0    # Yatay (Pan) takip hatası (Piksel)
takip_hatasi_y = 0    # Dikey (Tilt) takip hatası (Piksel)

# Mikrofon dizilimi
MIC_DIRECTIONS = {
    0: {"isim": "KUZEY", "aci": 0},
    1: {"isim": "DOĞU",  "aci": 90},
    2: {"isim": "GÜNEY", "aci": 180},
    3: {"isim": "BATI",  "aci": 270}
}

# ====================================================================
# YARDIMCI DONANIM FONKSİYONLARI
# ====================================================================
# (Tower Pro MG995 servolar kendi kütüphaneleriyle kontrol edilir)

# ====================================================================
# 1. MOTOR KONTROL MODÜLÜ (ARKA PLAN İŞ PARÇACIĞI)
# ====================================================================
def motor_kontrol_dongusu():
    global sistem_aktif, hedef_acisi, gorsel_kilit, takip_hatasi_x, takip_hatasi_y
    
    mevcut_aci = 0
    print("[MOTOR] 360 Derece Tarama Motoru (MG995 360 Servo) Başlatıldı.")
    
    # Başlangıç pozisyonları
    if GPIO_AVAILABLE:
        pan_servo.value = 0.0  # 360 servoyu durdur
        tilt_servo.value = 0.0 # 180 servoyu ufuk çizgisine (ortaya) al
    
    while sistem_aktif:
        if gorsel_kilit:
            # GÖRSEL TAKİP (Dinamik Hedef İzleme)
            if abs(takip_hatasi_x) > 30:
                if GPIO_AVAILABLE:
                    # Hedef sağdaysa sağa yavaş dön (0.15), soldaysa sola yavaş dön (-0.15)
                    hiz = 0.15 if takip_hatasi_x > 0 else -0.15
                    pan_servo.value = hiz
            else:
                # Hedef X merkezindeyse dur
                if GPIO_AVAILABLE: pan_servo.value = 0.0
                
            if abs(takip_hatasi_y) > 30:
                if GPIO_AVAILABLE:
                    # Servo değerini -1.0 ile 1.0 arasında yumuşakça değiştir
                    mevcut_tilt = tilt_servo.value
                    düzeltme = -0.02 if takip_hatasi_y > 0 else 0.02
                    yeni_tilt = max(min(mevcut_tilt + düzeltme, 1.0), -1.0)
                    tilt_servo.value = yeni_tilt
                
            time.sleep(0.02)
            continue
            
        if hedef_acisi is None:
            # 360 Derece Sürekli Tarama (Yavaşça dön)
            if GPIO_AVAILABLE:
                pan_servo.value = 0.1 # Yavaş dönüş hızı
            mevcut_aci = (mevcut_aci + 1) % 360
            time.sleep(0.05)
        else:
            print(f"[MOTOR] Akustik Tehdit! Hedefe yöneliniyor...")
            # Ses yönüne dönüş simülasyonu (360 servolar açı bilmez, zamanla dönülür)
            if GPIO_AVAILABLE:
                pan_servo.value = 0.4 # Daha hızlı dönüş
            time.sleep(1) # Dönüş süresi (Mekaniğe göre kalibre edilecek)
            if GPIO_AVAILABLE:
                pan_servo.value = 0.0 # Dur
            hedef_acisi = None # Görsel kilit için bekle

# ====================================================================
# 2. AKUSTİK İŞLEME MODÜLÜ (4 KANALLI MİKROFON)
# ====================================================================
def extract_features(y, sr):
    try:
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        mel_spectrogram = librosa.feature.melspectrogram(y=y, sr=sr)
        mel_mean = np.mean(mel_spectrogram, axis=1)
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        contrast_mean = np.mean(spectral_contrast, axis=1)
        return np.hstack((mfcc_mean, chroma_mean, mel_mean, contrast_mean))
    except Exception as e:
        return None

def audio_listener(clf):
    global sistem_aktif, hedef_acisi, gorsel_kilit
    print("[AKUSTİK] 4x INMP441 Mikrofon Dinleme Aktif.")
    
    def audio_callback(indata, frames, time_info, status):
        if not sistem_aktif or gorsel_kilit:
            return 
            
        kanal_sayisi = indata.shape[1] if indata.shape[1] > 1 else 4
        en_yuksek_guven_skoru = 0
        hedef_kanal = -1
        
        for kanal_id in range(min(4, kanal_sayisi)):
            audio_data = indata[:, kanal_id] if indata.shape[1] > kanal_id else indata[:, 0]
            features = extract_features(audio_data, SAMPLE_RATE)
            
            if features is not None:
                features = features.reshape(1, -1)
                if hasattr(clf, "predict_proba"):
                    probs = clf.predict_proba(features)
                    drone_prob = probs[0][1]
                    if drone_prob > 0.6 and drone_prob > en_yuksek_guven_skoru:
                        en_yuksek_guven_skoru = drone_prob
                        hedef_kanal = kanal_id
                else:
                    prediction = clf.predict(features)
                    if prediction[0] == 1:
                        hedef_kanal = kanal_id
                        break 

        if hedef_kanal != -1:
            yon = MIC_DIRECTIONS.get(hedef_kanal, {"isim": "BİLİNMEYEN", "aci": 0})
            print(f"\n🔊 [ALARM] {yon['isim']} yönünden Drone sesi alındı! (Güven: {en_yuksek_guven_skoru:.2f})")
            hedef_acisi = yon["aci"]

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', 
                            blocksize=int(SAMPLE_RATE * DURATION), callback=audio_callback):
            while sistem_aktif:
                time.sleep(0.5)
    except Exception as e:
        print(f"[HATA] Mikrofon başlatılamadı: {e}")

# ====================================================================
# 3. GÖRSEL İŞLEME VE ATEŞLEME MODÜLÜ (ANA DÖNGÜ)
# ====================================================================
def atesleme_mekanizmasi(hedef_box):
    if GPIO_AVAILABLE:
        relay_pin.on()
        print("🔥 [ATEŞLEME] Röle Çekildi! Hedef vuruluyor...")
        time.sleep(0.5)
        relay_pin.off()
    else:
        print("🔥 [ATEŞLEME] HEDEF VURULUYOR!!! (Simülasyon Modu)")

def get_libcamera_pipeline():
    """Raspberry Pi 5 ve IMX477 için donanım hızlandırmalı GStreamer pipeline'ı döndürür."""
    # libcamera gstreamer eklentisini kullanarak doğrudan donanım işleme
    return (
        "libcamerasrc ! "
        "video/x-raw, width=1280, height=720, framerate=30/1 ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! "
        "appsink drop=true sync=false"
    )

def hibrit_sistem_baslat():
    global sistem_aktif, hedef_acisi, gorsel_kilit
    
    print("\n[BİLGİ] Otonom Şahingözü Sistemi Yükleniyor (Raspberry Pi 5 Optimizasyonu)...")
    
    # 1. Modelleri Yükle (Geliştirilmiş Hata Yönetimi)
    try:
        if os.path.exists(AUDIO_MODEL_PATH):
            audio_clf = joblib.load(AUDIO_MODEL_PATH)
        else:
            print(f"[UYARI] Ses modeli bulunamadı. Beklenen yol: {AUDIO_MODEL_PATH}")
            print("[UYARI] Akustik tarama devre dışı bırakıldı.")
            audio_clf = None
    except Exception as e:
        print(f"[KRİTİK HATA] Ses modeli yüklenirken hata oluştu: {e}")
        audio_clf = None

    try:
        if not os.path.exists(YOLO_MODEL_PATH):
            print(f"[UYARI] Görüntü modeli bulunamadı! Beklenen tam yol: {YOLO_MODEL_PATH}")
            yolo_model = None
        else:
            yolo_model = YOLO(YOLO_MODEL_PATH)
    except Exception as e:
        print(f"[UYARI] YOLO modeli başlatılamadı: {e}. Görsel takip devre dışı.")
        yolo_model = None

    # 2. Arka Plan Thread'lerini Başlat
    motor_thread = threading.Thread(target=motor_kontrol_dongusu, daemon=True)
    motor_thread.start()

    if audio_clf is not None:
        audio_thread = threading.Thread(target=audio_listener, args=(audio_clf,), daemon=True)
        audio_thread.start()

    # 3. Kamera Başlat (GStreamer / libcamera Pipeline)
    try:
        print("[KONTROL] libcamera pipeline'ı ile kamera başlatılıyor...")
        pipeline = get_libcamera_pipeline()
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        
        # GStreamer başarısız olursa V4L2'ye geri dön (Güvenlik Ağı)
        if not cap.isOpened():
            print("[UYARI] GStreamer pipeline başlatılamadı. Standart V4L2 (/dev/video0) deneniyor...")
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
        if not cap.isOpened():
            print("[KRİTİK HATA] Kamera bağlı değil! Sistem kamerasız çalışamaz. Kapatılıyor...")
            sistem_aktif = False
            sys.exit(1)
    except Exception as e:
        print(f"[KRİTİK HATA] Kamera başlatma hatası: {e}. Sistem kapatılıyor...")
        sys.exit(1)
        
    ses_bekleme_sayaci = 0
    SES_BEKLEME_MAX = 30

    print("[BİLGİ] 🎥 Sistem Hazır. Çevre taranıyor... (Kapatmak için CTRL+C)")

    try:
        while sistem_aktif:
            ret, frame = cap.read()
            if not ret: 
                print("[KRİTİK HATA] Kameradan görüntü alınamıyor, bağlantı kopmuş olabilir! Sistem durduruluyor...")
                sistem_aktif = False
                break
                
            # Performans için yeniden boyutlandır (imgsz optimizasyonu)
            frame_resized = cv2.resize(frame, (640, 480))
            
            # HUD (Heads Up Display) Arka Plan Bilgileri
            if DISPLAY_AVAILABLE:
                cv2.putText(frame_resized, "SAHINGOZU OTONOM MOD: AKTIF", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if yolo_model is None:
                if DISPLAY_AVAILABLE:
                    cv2.putText(frame_resized, "YAPAY ZEKA MODELI BULUNAMADI - KOR UCUS", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                # YOLO Arama
                results = yolo_model.track(frame_resized, persist=True, conf=0.35, iou=0.5, imgsz=640, verbose=False)
                
                if results[0].boxes and len(results[0].boxes) > 0:
                    gorsel_kilit = True
                    boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
                    box = boxes[0] 
                    x1, y1, x2, y2 = box
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    
                    ekran_merkez_x = 320 # 640/2
                    ekran_merkez_y = 240 # 480/2
                    
                    global takip_hatasi_x, takip_hatasi_y
                    takip_hatasi_x = cx - ekran_merkez_x
                    takip_hatasi_y = cy - ekran_merkez_y
                    
                    if abs(takip_hatasi_x) > 30 or abs(takip_hatasi_y) > 30:
                        hedef_durumu = "TAKIP EDILIYOR"
                        renk = (0, 165, 255) # Turuncu
                        print(f"[TAKİP] Dinamik Takip Aktif! Taret drone'u izliyor... (Hata X: {takip_hatasi_x}, Y: {takip_hatasi_y})")
                    else:
                        hedef_durumu = "ATESLEME HAZIR - KILITLI"
                        renk = (0, 0, 255) # Kırmızı
                        print(f"[KİLİT] Hedef Merkezde! (Koordinat: {cx}, {cy})")
                        atesleme_mekanizmasi(box)

                    ses_bekleme_sayaci = 0
                    
                    # Ekranda çizim yap
                    cv2.rectangle(frame_resized, (x1, y1), (x2, y2), renk, 3)
                    cv2.line(frame_resized, (cx - 20, cy), (cx + 20, cy), renk, 2)
                    cv2.line(frame_resized, (cx, cy - 20), (cx, cy + 20), renk, 2)
                    
                    # Dinamik HUD Yazıları
                    if DISPLAY_AVAILABLE:
                        cv2.putText(frame_resized, f"DURUM: {hedef_durumu}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, renk, 2)
                        cv2.putText(frame_resized, f"HATA PAYI -> X: {takip_hatasi_x} Y: {takip_hatasi_y}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                else:
                    gorsel_kilit = False
                    if hedef_acisi is not None:
                        ses_bekleme_sayaci += 1
                        if ses_bekleme_sayaci > SES_BEKLEME_MAX:
                            print("[BİLGİ] Ses yönünde hedef bulunamadı. 360 taramaya devam ediliyor.")
                            hedef_acisi = None
                            ses_bekleme_sayaci = 0

            # -------------------------------------------------------------
            # EKRANSIZ (HEADLESS) MOD KORUMASI VE GÖSTERİM
            # -------------------------------------------------------------
            if DISPLAY_AVAILABLE:
                try:
                    cv2.imshow("SAHINGOZ - Otonom Sistem", frame_resized)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        sistem_aktif = False
                        break
                except cv2.error:
                    # Görüntüleyici çökerse headless moddaymış gibi sessizce devam et
                    pass

    except KeyboardInterrupt:
        print("\n[BİLGİ] Kullanıcı tarafından durduruldu.")
    finally:
        sistem_aktif = False
        cap.release()
        if DISPLAY_AVAILABLE:
            try:
                cv2.destroyAllWindows()
            except:
                pass
        print("[BİLGİ] Sistem Kapatıldı.")

if __name__ == '__main__':
    hibrit_sistem_baslat()
