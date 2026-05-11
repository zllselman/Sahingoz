import cv2
import numpy as np
from ultralytics import YOLO
import time
import os
import sys
import threading
import warnings
import threading
import warnings
import subprocess
import sounddevice as sd
import librosa
import joblib

# ====================================================================
# GLOBAL DEĞİŞKENLER (THREAD İLETİŞİMİ)
# ====================================================================
yolo_sonuclar = {
    "kutu_var": False,
    "x1": 0, "y1": 0, "x2": 0, "y2": 0,
    "cx": 0, "cy": 0,
    "hedef_durumu": "",
    "renk": (0, 255, 0)
}
son_frame_yolo_icin = None
yolo_aktif = True

# Ses modeli
ses_modeli = None

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
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "best.pt")
SES_MODEL_PATH = os.path.join(BASE_DIR, "drone_audio_model.joblib")

# Headless kontrolü: Ortam değişkenlerinde DISPLAY var mı?
try:
    import socket
    socket.create_connection(('localhost', 6000), timeout=1)
    DISPLAY_AVAILABLE = True
except (OSError, socket.error, socket.timeout):
    DISPLAY_AVAILABLE = 'DISPLAY' in os.environ or 'WAYLAND_DISPLAY' in os.environ

# ====================================================================
# DONANIM (GPIO) PİN TANIMLAMALARI (Raspberry Pi 5)
# ====================================================================
if GPIO_AVAILABLE:
    # Pan Motoru: Tower Pro MG995 (360 Derece Sürekli Dönen Servo)
    pan_servo = Servo(12) 
    
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
    
    # 45 saniyede 1 tur atan Pan motor hızı (Kalibrasyon değeri: 0.05)
    SWEEP_SPEED = 0.05
    
    # Tilt motor sınırları: 45 derece (0.5) ile 90 derece (1.0) arasında
    MIN_TILT = 45 / 90.0   # 0.5
    MAX_TILT = 90 / 90.0   # 1.0
    
    print("[MOTOR] 360 Derece Tarama Motoru (Pan) ve 180 Derece Tilt Motoru Başlatıldı.")
    
    if GPIO_AVAILABLE:
        pan_servo.value = 0.0
        tilt_servo.value = MIN_TILT  # Başlangış pozisyonu: 45 derece
    
    while sistem_aktif:
        if gorsel_kilit:
            # GÖRSEL TAKİP
            if GPIO_AVAILABLE:
                # Pan Takip (Sağ/Sol)
                if abs(takip_hatasi_x) > 30:
                    hiz = 0.15 if takip_hatasi_x > 0 else -0.15
                    pan_servo.value = hiz
                else:
                    pan_servo.value = 0.0
                    
                # Tilt Takip (Yukarı/Aşağı) - 45-75 derece arasında sınırlı
                if abs(takip_hatasi_y) > 30:
                    mevcut_tilt = tilt_servo.value
                    düzeltme = -0.02 if takip_hatasi_y > 0 else 0.02
                    tilt_servo.value = max(min(mevcut_tilt + düzeltme, MAX_TILT), MIN_TILT)
                
            time.sleep(0.02)
            continue
            
        # Görsel kilit yoksa ve tehdit yoksa, Tilt motoru sabit durur (45 derece)
        if GPIO_AVAILABLE and tilt_servo.value != MIN_TILT:
            tilt_servo.value = MIN_TILT
            
        if hedef_acisi is None:
            # 360 Derece Sürekli Tarama (Sürekli dön)
            if GPIO_AVAILABLE:
                pan_servo.value = SWEEP_SPEED
            time.sleep(0.05)
        else:
            # Ses yönüne dön!
            print(f"[MOTOR] Akustik Tehdit! {hedef_acisi} derecesine yöneliniyor...")
            if GPIO_AVAILABLE:
                pan_servo.value = 0.4 # Tehdite doğru hızlı dönüş
            time.sleep(1) # Dönüş süresi kalibrasyonu
            if GPIO_AVAILABLE:
                pan_servo.value = 0.0 # Dur ve kameranın (YOLO'nun) tespit etmesini bekle
            hedef_acisi = None

# ====================================================================
# 2. AKUSTİK İŞLEME MODÜLÜ (SES MODELİ İLE STEREO DİNLEME)
# ====================================================================
def list_audio_input_devices():
    try:
        devices = sd.query_devices()
        print("[AKUSTİK] Mevcut ses giriş cihazları taranıyor...")
        for idx, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                print(f"  [{idx}] {dev['name']} | input_channels={dev['max_input_channels']} | default_sr={dev['default_samplerate']}")
        return devices
    except Exception as e:
        print(f"[AKUSTİK] Ses cihazları listelenemedi: {e}")
        return []


def select_audio_input_device():
    devices = list_audio_input_devices()
    for idx, dev in enumerate(devices):
        if dev['max_input_channels'] >= 2:
            print(f"[AKUSTİK] Stereo giriş cihazı seçildi: {dev['name']} (#{idx})")
            return idx
    try:
        default_device = sd.default.device
        if isinstance(default_device, tuple):
            return default_device[0]
        return int(default_device)
    except Exception:
        return None


def audio_listener():
    global sistem_aktif, hedef_acisi, gorsel_kilit, ses_modeli
    
    print("[AKUSTİK] Ses Modeli ile Stereo Dinleme Başlatılıyor...")
    
    if ses_modeli is None:
        print("[UYARI] Ses modeli bulunamadı! Akustik tespit devre dışı.")
        return
    
    audio_device = select_audio_input_device()
    if audio_device is None:
        print("[UYARI] Stereo ses girişi bulunamadı! Akustik tespit devre dışı.")
        return

    try:
        sd.default.device = audio_device
    except Exception as e:
        print(f"[UYARI] Ses cihazı atanamadı: {e}")
        return

    available_rates = [44100, 48000, 32000, 22050, 16000]
    print(f"[AKUSTİK] Denenecek sample rate listesi: {available_rates}")
    SAMPLE_RATE = None
    for rate in available_rates:
        try:
            sd.check_input_settings(device=audio_device, samplerate=rate, channels=2)
            SAMPLE_RATE = rate
            print(f"[AKUSTİK] Kullanılacak sample rate: {SAMPLE_RATE}")
            break
        except Exception:
            continue

    if SAMPLE_RATE is None:
        print("[UYARI] Uygun sample rate bulunamadı! Akustik tespit devre dışı.")
        return

    DURATION = 1.0  # 1 saniyelik kayıt
    BUFFER_SIZE = int(SAMPLE_RATE * DURATION)
    
    def extract_features(audio_data):
        """Ses verisinden özellik çıkarımı (160 feature)."""
        try:
            # MFCC özelliklerini çıkar (13 MFCC * 10 frame = 130)
            mfccs = librosa.feature.mfcc(y=audio_data, sr=SAMPLE_RATE, n_mfcc=13, n_fft=2048, hop_length=512)
            if mfccs.shape[1] < 10:
                mfccs = np.pad(mfccs, ((0,0), (0, 10-mfccs.shape[1])), mode='constant')
            mfccs_flat = mfccs[:, :10].flatten()  # 130 features
            
            # Spektral özellikler
            spectral_centroid = librosa.feature.spectral_centroid(y=audio_data, sr=SAMPLE_RATE)[0][:10]
            if len(spectral_centroid) < 10:
                spectral_centroid = np.pad(spectral_centroid, (0, 10-len(spectral_centroid)), mode='constant')
            
            # RMS enerji
            rms = librosa.feature.rms(y=audio_data)[0][:10]
            if len(rms) < 10:
                rms = np.pad(rms, (0, 10-len(rms)), mode='constant')
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y=audio_data)[0][:10]
            if len(zcr) < 10:
                zcr = np.pad(zcr, (0, 10-len(zcr)), mode='constant')
            
            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=SAMPLE_RATE)[0][:10]
            if len(spectral_rolloff) < 10:
                spectral_rolloff = np.pad(spectral_rolloff, (0, 10-len(spectral_rolloff)), mode='constant')
            
            # Özellikleri birleştir (130 + 10 + 10 + 10 = 160)
            features = np.concatenate([
                mfccs_flat,
                spectral_centroid,
                rms,
                zcr,
                spectral_rolloff
            ])
            
            return features[:160]  # Tam olarak 160 feature döndür
        except Exception as e:
            print(f"[UYARI] Feature çıkarımı hatası: {e}")
            return np.zeros(160)  # Hata durumunda sıfır vektörü döndür
    
    while sistem_aktif:
        if gorsel_kilit:
            time.sleep(0.5)  # Görsel kilit varsa sesi dinlemeye gerek yok
            continue
        
        try:
            # Stereo kayıt (2 kanal)
            recording = sd.rec(int(BUFFER_SIZE), samplerate=SAMPLE_RATE, channels=2, dtype='float32', device=audio_device)
            sd.wait()
            
            if recording is None or recording.size == 0:
                print(f"[UYARI] Ses kaydı boş geldi.")
                time.sleep(0.5)
                continue
            
            # Sol ve sağ kanalları ayır
            left_channel = recording[:, 0]
            right_channel = recording[:, 1]
            
            # Her kanal için özellik çıkar ve tahmin yap
            left_features = extract_features(left_channel).reshape(1, -1)
            right_features = extract_features(right_channel).reshape(1, -1)
            
            if left_features.shape[1] != 160 or right_features.shape[1] != 160:
                print(f"[UYARI] Feature sayısı hatalı: left={left_features.shape[1]}, right={right_features.shape[1]}")
                time.sleep(0.5)
                continue
            
            left_prediction = ses_modeli.predict(left_features)[0]
            right_prediction = ses_modeli.predict(right_features)[0]
            
            # Drone tespit kontrolü
            if left_prediction == 1:  # Sol tarafta drone
                hedef_acisi = 270  # Batı (sol)
                print(f"[AKUSTİK] 🎯 Sol Tarafta Drone Tespit Edildi! Yön: {hedef_acisi} Derece")
            elif right_prediction == 1:  # Sağ tarafta drone
                hedef_acisi = 90  # Doğu (sağ)
                print(f"[AKUSTİK] 🎯 Sağ Tarafta Drone Tespit Edildi! Yön: {hedef_acisi} Derece")
            
        except Exception as e:
            print(f"[HATA] Ses işleme hatası: {e}")
            time.sleep(1)
        
        time.sleep(0.1)  # Kısa bekleme

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

def yolo_worker_dongusu(yolo_model):
    """Arka planda (Ayrı bir Thread'de) YOLO'yu çalıştırarak ana ekranın kasmasını engeller."""
    global sistem_aktif, yolo_aktif, son_frame_yolo_icin, yolo_sonuclar, gorsel_kilit
    global takip_hatasi_x, takip_hatasi_y
    
    ekran_merkez_x = 320
    ekran_merkez_y = 240
    
    while sistem_aktif and yolo_aktif:
        if son_frame_yolo_icin is None:
            time.sleep(0.01)
            continue
            
        # O anki frame'in kopyasını al (çakışmayı önlemek için)
        frame_to_process = son_frame_yolo_icin.copy()
        
        # YOLO arama işlemi (Bu işlem ne kadar sürerse sürsün ana ekran kilitlenmez)
        results = yolo_model.track(frame_to_process, persist=True, conf=0.35, iou=0.5, imgsz=640, verbose=False)
        
        if results[0].boxes and len(results[0].boxes) > 0:
            gorsel_kilit = True
            boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
            box = boxes[0] 
            x1, y1, x2, y2 = box
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            takip_hatasi_x = cx - ekran_merkez_x
            takip_hatasi_y = cy - ekran_merkez_y
            
            if abs(takip_hatasi_x) > 30 or abs(takip_hatasi_y) > 30:
                yolo_sonuclar["hedef_durumu"] = "TAKIP EDILIYOR"
                yolo_sonuclar["renk"] = (0, 165, 255) # Turuncu
            else:
                yolo_sonuclar["hedef_durumu"] = "ATESLEME HAZIR - KILITLI"
                yolo_sonuclar["renk"] = (0, 0, 255) # Kırmızı
                atesleme_mekanizmasi(box)

            yolo_sonuclar["kutu_var"] = True
            yolo_sonuclar["x1"] = x1
            yolo_sonuclar["y1"] = y1
            yolo_sonuclar["x2"] = x2
            yolo_sonuclar["y2"] = y2
            yolo_sonuclar["cx"] = cx
            yolo_sonuclar["cy"] = cy
        else:
            gorsel_kilit = False
            yolo_sonuclar["kutu_var"] = False
            
        time.sleep(0.01) # Aşırı CPU kullanımını engellemek için mini mola

class RPi5Camera:
    """Raspberry Pi 5 için OpenCV uyumsuzluğuna karşı doğrudan native rpicam-vid okuyucusu."""
    def __init__(self, width=640, height=480, framerate=30):
        self.width = width
        self.height = height
        self.frame_size = int(width * height * 1.5)
        
        cmd_name = "rpicam-vid" if os.path.exists("/usr/bin/rpicam-vid") else "libcamera-vid"
        self.cmd = [
            cmd_name, "-t", "0", "--width", str(width), "--height", str(height),
            "--framerate", str(framerate), "--codec", "yuv420", "--inline", "--nopreview", "-o", "-"
        ]
        self.process = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=self.frame_size*3)
        self._is_opened = self.process.poll() is None

    def isOpened(self):
        return self._is_opened and self.process.poll() is None

    def read(self):
        if not self.isOpened(): return False, None
        raw_data = self.process.stdout.read(self.frame_size)
        if len(raw_data) != self.frame_size:
            self._is_opened = False
            return False, None
        yuv = np.frombuffer(raw_data, dtype=np.uint8).reshape((int(self.height * 1.5), self.width))
        return True, cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)

    def release(self):
        if hasattr(self, 'process') and self.process:
            self.process.terminate()
            self.process.wait()

class ThreadedCamera:
    """Arka planda sürekli en yeni kareyi okuyarak buffer gecikmesini (lag) sıfırlayan asenkron sarmalayıcı sınıf."""
    def __init__(self, camera_source):
        self.camera = camera_source
        self.ret = False
        self.frame = None
        self.running = True
        
        # İlk okumayı yap
        self.ret, self.frame = self.camera.read()
        
        # Sürekli okuma yapan arka plan iş parçacığı
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            ret, frame = self.camera.read()
            if ret:
                self.ret = ret
                self.frame = frame
            else:
                time.sleep(0.01)

    def read(self):
        # Her zaman en taze (en son) kareyi döndür
        return self.ret, self.frame
        
    def release(self):
        self.running = False
        if hasattr(self.camera, 'release'):
            self.camera.release()

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
    
    # 1. Modelleri Yükle
    try:
        if not os.path.exists(YOLO_MODEL_PATH):
            print(f"[UYARI] Görüntü modeli bulunamadı! Beklenen tam yol: {YOLO_MODEL_PATH}")
            yolo_model = None
        else:
            yolo_model = YOLO(YOLO_MODEL_PATH)
    except Exception as e:
        print(f"[UYARI] YOLO modeli başlatılamadı: {e}. Görsel takip devre dışı.")
        yolo_model = None
    
    # Ses modelini yükle
    global ses_modeli
    try:
        if not os.path.exists(SES_MODEL_PATH):
            print(f"[UYARI] Ses modeli bulunamadı! Beklenen tam yol: {SES_MODEL_PATH}")
            ses_modeli = None
        else:
            ses_modeli = joblib.load(SES_MODEL_PATH)
            print("[BİLGİ] Ses modeli başarıyla yüklendi.")
    except Exception as e:
        print(f"[UYARI] Ses modeli yüklenemedi: {e}. Akustik tespit devre dışı.")
        ses_modeli = None

    # 2. Arka Plan Thread'lerini Başlat
    motor_thread = threading.Thread(target=motor_kontrol_dongusu, daemon=True)
    motor_thread.start()

    audio_thread = threading.Thread(target=audio_listener, daemon=True)
    audio_thread.start()

    if yolo_model is not None:
        print("[BİLGİ] Yapay Zeka (YOLO) Çekirdeği Asenkron Olarak Başlatılıyor...")
        yolo_thread = threading.Thread(target=yolo_worker_dongusu, args=(yolo_model,), daemon=True)
        yolo_thread.start()

    # 3. Kamera Başlat
    try:
        print("[KONTROL] Standart OpenCV V4L2 kamerası deneniyor...")
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Test okuması yap. Pi 5 üzerinde cv2 genelde okuyamaz ve ret=False döner
        ret, test_frame = cap.read()
        if not ret or test_frame is None:
            cap.release()
            print("[UYARI] OpenCV standart kamera okuması başarısız. libcamera GStreamer pipeline deneniyor...")
            cap = cv2.VideoCapture(get_libcamera_pipeline(), cv2.CAP_GSTREAMER)
            if cap.isOpened():
                ret, test_frame = cap.read()

        if not cap.isOpened() or not ret or test_frame is None:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass
            print("[UYARI] GStreamer pipeline da başarısız. Raspberry Pi 5 Native (rpicam-vid) okuyucusuna geçiliyor...")
            cap = RPi5Camera(width=640, height=480, framerate=30)
            ret, test_frame = cap.read()

        if not cap.isOpened() or not ret or test_frame is None:
            print("[KRİTİK HATA] Kamera bağlı değil veya okuma alınamıyor! Sistem kamerasız çalışamaz. Kapatılıyor...")
            sistem_aktif = False
            sys.exit(1)
            
        print("[BİLGİ] Asenkron Kamera Okuyucu (Anti-Lag Thread) başlatılıyor...")
        cap = ThreadedCamera(cap)
        
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
            
            # YOLO thread'ine güncel kareyi besle
            global son_frame_yolo_icin
            son_frame_yolo_icin = frame_resized

            # HUD (Heads Up Display) Arka Plan Bilgileri
            if DISPLAY_AVAILABLE:
                cv2.putText(frame_resized, "SAHINGOZU OTONOM MOD: AKTIF", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            if yolo_model is None:
                if DISPLAY_AVAILABLE:
                    cv2.putText(frame_resized, "YAPAY ZEKA MODELI BULUNAMADI - KOR UCUS", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                # YAPAY ZEKA (YOLO) ÇİZİMLERİNİ EKRANA BAS (Ana döngü gecikmesiz çalışır)
                if yolo_sonuclar["kutu_var"]:
                    x1, y1, x2, y2 = yolo_sonuclar["x1"], yolo_sonuclar["y1"], yolo_sonuclar["x2"], yolo_sonuclar["y2"]
                    cx, cy = yolo_sonuclar["cx"], yolo_sonuclar["cy"]
                    renk = yolo_sonuclar["renk"]
                    hedef_durumu = yolo_sonuclar["hedef_durumu"]
                    
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
