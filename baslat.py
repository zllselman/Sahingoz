import os
import subprocess
import time
import sys

def check_hdmi_connected():
    """
    Raspberry Pi üzerinde HDMI bağlantısını kontrol eder.
    HDMI kablosu takılıysa True, takılı değilse False döner.
    """
    try:
        # DRM klasöründe HDMI portlarını kontrol et
        drm_path = '/sys/class/drm/'
        if not os.path.exists(drm_path):
            # Windows gibi geliştirme ortamları için test amaçlı uyarı
            print("[TEST MODU] DRM klasörü bulunamadı (Windows/Geliştirici ortamı). HDMI yok kabul ediliyor.")
            return False
            
        for folder in os.listdir(drm_path):
            if 'HDMI' in folder or 'card' in folder:
                status_file = os.path.join(drm_path, folder, 'status')
                if os.path.exists(status_file):
                    with open(status_file, 'r') as f:
                        status = f.read().strip()
                        if status == 'connected':
                            return True
        return False
    except Exception as e:
        print(f"[HATA] HDMI kontrol hatası: {e}")
        return False

if __name__ == "__main__":
    print("\n================================================")
    print("      ŞAHİNGÖZÜ OTONOM KONTROL SİSTEMİ")
    print("================================================\n")
    print("[SİSTEM] Donanımlar kontrol ediliyor...")
    time.sleep(1) # Sensörlerin/Portların uyanması için
    
    if check_hdmi_connected():
        print("[BİLGİ] HDMI Ekran Algılandı.")
        print("[BİLGİ] Otonom sistem GÖRSEL modda başlatılıyor...")
    else:
        print("[BİLGİ] HDMI Bağlantısı Yok. (Headless Mod)")
        print("[BİLGİ] Otonom sistem EKRANSIZ modda başlatılıyor...")
        
    print("================================================\n")
    
    # Otonom sistemi çalıştır
    target_script = "hibrit_operasyon.py"
    if os.path.exists(target_script):
        # Raspberry Pi 5 libcamera V4L2 köprüsü (Kamera Hatası Çözümü)
        try:
            subprocess.run(["libcamerify", sys.executable, target_script])
        except FileNotFoundError:
            subprocess.run([sys.executable, target_script])
    else:
        print(f"[CRITICAL] {target_script} bulunamadı! Sistem durduruldu.")
