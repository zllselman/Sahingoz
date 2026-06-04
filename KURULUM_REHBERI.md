# 🚀 Şahingözü: Yeni Başlayanlar İçin Adım Adım Kurulum Rehberi

Merhaba! Bu rehber, elinizdeki parçalarla (Raspberry Pi 5, MG995 Servolar, INMP441 Mikrofonlar, Kamera vb.) otonom bir drone takip kulesini **sıfırdan, en baştan ve en anlaşılır şekilde** nasıl kuracağınızı anlatmak için özel olarak hazırlandı.

Hiç endişelenmeyin, kablo kablo, pin pin ilerleyeceğiz!

---

## 🏗️ BÖLÜM 1: Mekanik Kurulum (Kimin Yeri Neresi?)

Kuleniz 3 kattan oluşur:
1. **Zemin Kat (Sabit Taban):** Yere basan kısımdır. İçinde devasa bataryanız (Robo R750) duracak.
2. **Orta Kat (Dönen Gövde):** Kendi etrafında 360 derece fırıl fırıl dönecek olan ana kutudur. Raspberry Pi 5 bilgisayarınız, mikrofonlar ve motor sürücüleriniz bu kutunun içinde veya üstünde yer alacak.
3. **Çatı Katı (U-Braket Kafa):** Kameranın takılı olduğu, yukarı-aşağı sallanan kafadır.

> **Slip Ring (Kayar Bilezik) Ne İşe Yarar?**
> Batarya yerde sabit dururken, orta kat sürekli döneceği için kablolar dolanıp kopar. Kayar bileziği tam zemin kat ile orta katın arasına yerleştiririz. Bataryanın kabloları alttan bileziğe girer, üstünden çıkarak dönen Raspberry Pi'ye elektriği kabloları dolandırmadan ulaştırır!

---

## 🔌 BÖLÜM 2: Güç (Elektrik) Bağlantıları

> **DİKKAT:** Raspberry Pi 5 hassastır. Bu sürümde LM2596 veya benzeri bir regülatör kullanmayacağız; motorlar ve Raspberry Pi ayrı güç kaynaklarıyla beslenecektir.

1. **Güç Kaynakları:**
   - Motorlar için yüksek akım verebilen bir 5V batarya/psu kullanın. Motorların kırmızı (VCC) kablolarını bu 5V pozitifine bağlayın.
   - Motorların kahverengi (GND) kablolarını batarya/psu negatifine bağlayın.
   - Raspberry Pi'yi kendi 5V beslemesiyle çalıştırın.
   - MUTLAKA ortak toprak (COMMON GND) oluşturun: batarya/psu negatifini Raspberry Pi'nin herhangi bir GND pinine bağlayın.
   - Kablo kesitlerinin motorların çektiği akımı taşıyabildiğinden emin olun.

---

## 📷 BÖLÜM 3: Kamera Bağlantısı

1. Raspberry Pi 5'in üzerindeki iki adet küçük uzun porttan birini (genellikle CAM/DISP 0 yazar) bulun.
2. Portun siyah tırnağını nazikçe yukarı kaldırın.
3. IMX477 kameranızın yassı şerit kablosunu alın. Kablonun **parlak (metalik) dişleri içe (işlemciye doğru), mavi kısmı dışa** bakacak şekilde yuvaya oturtun.
4. Siyah tırnağı aşağı bastırarak kilitleyin. Kamerayı çatı katındaki U-Braket'e vidalayın.

---

## 🤖 BÖLÜM 4: Motor Bağlantıları (MG995 Servolar)

Elinizde 2 çeşit MG995 var:
- **Pan Motoru (360 Derece Dönen):** Kuleyi sağa/sola sürekli çevirecek.
- **Tilt Motoru (180 Derece Dönen):** Kamerayı yukarı/aşağı ezecek.

İki motorun da 3 kablosu vardır: **Kırmızı (Güç)**, **Kahverengi (GND/Toprak)**, **Turuncu/Sarı (Sinyal)**.

> **UYARI:** Motorların Kırmızı kablolarını asla Raspberry Pi'nin 5V pinlerinden almayın. Motorlar yüksek akım çeker; onları yeterli akım sağlayan ayrı bir güç kaynağına bağlayın ve Pi ile ortak toprak sağlayın.

**Pan Motoru (Taret Dönüşü, ~120° Tarama):**
1. **Kırmızı Kablo:** Motorların kırmızı (VCC) kablolarını ayrı 5V batarya/psu pozitifine bağlayın (Pi'nin 5V pinini kullanmayın).
2. **Kahverengi Kablo:** Motorların kahverengi (GND) kablolarını batarya/psu negatifine bağlayın ve bu negatif hattı Raspberry Pi'nin herhangi bir GND pinine bağlayarak ortak toprak oluşturun.
3. **Turuncu Kablo (Sinyal):** Raspberry Pi'nin **Pin 32 (GPIO 12)** ayağına.

**Tilt Motoru (180° - Kamera Kafası):**
1. **Kırmızı Kablo:** Motorun kırmızı (VCC) kablosunu ayrı 5V batarya/psu pozitifine bağlayın.
2. **Kahverengi Kablo:** Motorun kahverengi (GND) kablosunu batarya/psu negatifine bağlayın (ortak toprak ile Raspberry Pi).
3. **Turuncu Kablo (Sinyal):** Raspberry Pi'nin **Pin 33 (GPIO 13)** ayağına.

---

## 🎤 BÖLÜM 5: Mikrofon (INMP441) Bağlantıları

Kulenin 4 tarafına (Kuzey, Güney, Doğu, Batı) 4 adet küçük INMP441 modülü yapıştırın. Bu mikrofonlar dijital (I2S) çalışır.
Tüm mikrofonların aynı isimli pinlerini birbirine paralel bağlayacağız (Yani hepsinin VDD'si aynı yere gidecek).

| INMP441 Üzerindeki Yazı | Nereye Bağlanacak? (Raspberry Pi 5) |
| :--- | :--- |
| **VDD** | **Pin 1 (3.3V)** *(Sakın 5V'a takmayın, mikrofonlar yanar)* |
| **GND** | **Pin 9 (GND)** |
| **SD** (Data) | **Pin 38 (GPIO 20)** |
| **SCK** (Saat) | **Pin 12 (GPIO 18)** |
| **WS** (Kelime Seçimi) | **Pin 35 (GPIO 19)** |
| **L/R** (Kanal) | Sağ taraf için VDD'ye (3.3V), Sol taraf için GND'ye bağlayın. |

---

## 💻 BÖLÜM 6: Yazılımı Çalıştırma

Tüm kabloları taktınız. Şimdi işin sihirli kısmına geçiyoruz!

1. Raspberry Pi'yi bir ekrana ve klavyeye bağlayarak açın.
2. İnternete bağlanın.
3. Terminali (siyah ekran) açın ve şu komutları yazıp Enter'a basın (Kütüphaneleri kuruyoruz):
   ```bash
   sudo apt update
   pip install gpiozero lgpio ultralytics opencv-python sounddevice librosa joblib
   ```
4. Hazırladığımız `baslat.py`, `hibrit_operasyon.py` ve `.pt` ile `.joblib` model dosyalarınızı Pi'nin içindeki bir klasöre (Örn: `/home/pi/SAHINGOZU-main/`) atın.

**Otomatik Başlama (Otonom) Ayarı:**
Kuleyi sahaya götürdüğünüzde ekrana takmadan fişini çeker çekmez kendi kendine çalışması için son bir ayar yapacağız:
1. Terminale şunu yazın:
   ```bash
   sudo nano /etc/systemd/system/sahingozu.service
   ```
2. Açılan siyah ekrana şunları kopyalayıp yapıştırın:
   ```ini
   [Unit]
   Description=Sahingozu Otonom Savunma Sistemi
   After=multi-user.target

   [Service]
   Type=idle
   User=pi
   Environment=DISPLAY=:0
   ExecStart=/usr/bin/python3 /home/pi/SAHINGOZU-main/baslat.py
   WorkingDirectory=/home/pi/SAHINGOZU-main
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Klavyeden sırasıyla `CTRL + O`, `Enter`, `CTRL + X` tuşlarına basarak kaydedin ve çıkın.
4. Terminale şu iki komutu yazarak sistemi aktifleştirin:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable sahingozu.service
   ```

**VE BİTTİ! 🎉**
Artık Raspberry Pi'nizi kapatın. HDMI ekran kablosunu sökün. Sistemi doğrudan batarya ile beslediğiniz an kule kendi kendine dönmeye başlayacak, ses dinleyecek ve hedefi görünce üstündeki kafayı drone'a kilitleyip namluyu üzerine çevirecektir!

---

## 🛠️ BÖLÜM 7: Gelişmiş Donanım Revizyonu (4 Mikrofon & Arduino Co-Processor)

Sisteminizi tam profesyonel bir seviyeye çıkarmak ve "titreme (jitter)" sorunlarını tamamen yok etmek için yapılan en güncel donanım kurulum yönergeleri aşağıdadır.

### A. Jitter (Titreme) Önleyici Motor Bağlantıları (PWM Revizyonu)
Raspberry Pi 5'te motorların pürüzsüz çalışması için yazılımsal değil donanımsal PWM pinlerini kullanmalısınız. Aksi halde motorlarınız dönmek yerine titrer:
- **Pan Motoru (360° Sürekli Döner):** Turuncu/Sarı Sinyal Kablosu -> **Raspberry Pi Pin 32 (GPIO 12)**
- **Tilt Motoru (180° Yukarı/Aşağı):** Turuncu/Sarı Sinyal Kablosu -> **Raspberry Pi Pin 33 (GPIO 13)**
> *(Not: Kırmızı kablolar KESİNLİKLE LM2596 Regülatör 5V çıkışına, kahverengi kablolar ise Regülatör GND çıkışına bağlanmalıdır. Regülatör GND'si ile Raspberry Pi GND'si mutlaka birleştirilmelidir!)*

### B. Arduino (ESP32) Yardımcı İşlemci (Co-Processor) Kurulumu
Raspberry Pi üzerinde yalnızca 2 mikrofon (stereo) bağlanabilen bir donanım sınırı vardır. 4 adet INMP441 mikrofonu sorunsuz kullanmak için araya bir **Arduino ESP32 Geliştirme Kartı** ekleyeceğiz. Bu kart, Raspberry Pi'nin üzerinden ses işleme yükünü tamamen alacaktır.

**1. Mikrofonların Arduino'ya (ESP32) Bağlanması (Breadboard Üzerinden):**
Tüm devre bağlantılarını geniş bir Breadboard (devre tahtası) üzerinde yapın. 4 mikrofonun da VDD, GND, SCK ve WS pinlerini breadboard üzerindeki aynı hatlara (kısa devre/paralel) bağlayabilirsiniz.
- **VDD:** ESP32'nin **3.3V** pinine (Breadboard'un kırmızı hattına)
- **GND:** ESP32'nin **GND** pinine (Breadboard'un mavi hattına)
- **SCK (Saat):** ESP32'nin I2S Clock pinine (Örn: GPIO 14)
- **WS (Kelime Seçimi):** ESP32'nin I2S WS pinine (Örn: GPIO 15)
- **SD (Veri):** ESP32'nin I2S Data pinlerine (2 mikrofonu GPIO 32'ye, kalan 2 mikrofonu GPIO 33'e bağlayın)
- **L/R Pinleri:** Yön tespiti için 2 mikrofonun L/R pinini Breadboard'da VDD'ye (Sağ kanal), diğer 2'sinin L/R pinini GND'ye (Sol kanal) bağlayın.

**2. ESP32 Yazılım Görevi:**
ESP32'ye Arduino IDE üzerinden I2S dinleme kodu yüklenir. ESP32 sesi sürekli dinler, ses seviyelerini ve zaman farkını analiz eder ve bir dron tespit ettiğinde Raspberry Pi'ye sadece o yönün açısını yazar (Örn: `ANGLE: 180`).

**3. ESP32 ile Raspberry Pi'nin Birleştirilmesi:**
ESP32 kartını standart bir Micro-USB veya Type-C veri kablosuyla doğrudan Raspberry Pi 5'in USB portlarından birine takın. Raspberry Pi yazılımımız arka planda bu USB portunu (Örn: `/dev/ttyUSB0`) otomatik olarak bulacak, dinlemeye başlayacak ve ESP32'den gelen 180 derece komutunu duyduğu an ana kamerayı o yöne çevirecektir!

---

## 🛠️ BÖLÜM 8: Güncel Donanım Revizyonu (2 Mikrofon & Motor Titremesi Çözümü)

Sisteminizi en güncel ve kararlı haliyle çalıştırmak için yapılan son donanım güncellemeleri aşağıdadır. Arduino entegrasyonu çıkarılarak doğrudan Raspberry Pi üzerinden ses işleme yapılmaktadır.

### A. Motor Titremesi (Jitter) Tam Çözümü - Donanımsal PWM Pinleri
Raspberry Pi 5'te motorların pürüzsüz çalışması için yazılımsal değil donanımsal PWM pinlerini kullanmalısınız. Aksi halde motorlarınız dönmek yerine titrer:
- **Pan Motoru (360° Sürekli Döner):** Turuncu/Sarı Sinyal Kablosu -> **Raspberry Pi Pin 32 (GPIO 12)**
- **Tilt Motoru (180° Yukarı/Aşağı):** Turuncu/Sarı Sinyal Kablosu -> **Raspberry Pi Pin 33 (GPIO 13)**
> *(Not: Kırmızı kablolar KESİNLİKLE LM2596 Regülatör 5V çıkışına, kahverengi kablolar ise Regülatör GND çıkışına bağlanmalıdır. Regülatör GND'si ile Raspberry Pi GND'si mutlaka birleştirilmelidir!)*

### B. 2 Mikrofon Stereo Bağlantısı (INMP441)
Raspberry Pi'nin donanım sınırlaması nedeniyle 2 adet INMP441 mikrofon kullanacağız. Bunlar sol ve sağ kanalları temsil edecek şekilde bağlanacaktır.

**Mikrofon Bağlantısı (Breadboard Üzerinden):**
Tüm bağlantıları geniş bir Breadboard üzerinde yapın. İki mikrofonun da VDD, GND, SCK ve WS pinlerini breadboard üzerindeki aynı hatlara (kısa devre/paralel) bağlayabilirsiniz.

| INMP441 Üzerindeki Yazı | Nereye Bağlanacak? (Raspberry Pi 5) |
| :--- | :--- |
| **VDD** | **Pin 1 (3.3V)** *(Sakın 5V'a takmayın, mikrofonlar yanar)* |
| **GND** | **Pin 9 (GND)** |
| **SD** (Data) | Sol Mikrofon: **Pin 38 (GPIO 20)**, Sağ Mikrofon: **Pin 40 (GPIO 21)** |
| **SCK** (Saat) | **Pin 12 (GPIO 18)** |
| **WS** (Kelime Seçimi) | **Pin 35 (GPIO 19)** |
| **L/R** (Kanal) | Sol Mikrofon: GND'ye (Sol kanal), Sağ Mikrofon: 3.3V'ye (Sağ kanal) bağlayın. |

**Breadboard Bağlantı Adımları:**
1. Breadboard'un kırmızı hattını (pozitif) Raspberry Pi'nin **Pin 1 (3.3V)**'e bağlayın.
2. Breadboard'un mavi hattını (GND) Raspberry Pi'nin **Pin 9 (GND)**'e bağlayın.
3. Breadboard'un sarı hattını (SCK) Raspberry Pi'nin **Pin 12 (GPIO 18)**'e bağlayın.
4. Breadboard'un yeşil hattını (WS) Raspberry Pi'nin **Pin 35 (GPIO 19)**'e bağlayın.
5. Sol mikrofonun SD pinini Raspberry Pi'nin **Pin 38 (GPIO 20)**'e bağlayın.
6. Sağ mikrofonun SD pinini Raspberry Pi'nin **Pin 40 (GPIO 21)**'e bağlayın.
7. İki mikrofonun da VDD pinlerini breadboard'un kırmızı hattına (3.3V) bağlayın.
8. İki mikrofonun da GND pinlerini breadboard'un mavi hattına bağlayın.
9. İki mikrofonun da SCK pinlerini breadboard'un sarı hattına bağlayın.
10. İki mikrofonun da WS pinlerini breadboard'un yeşil hattına bağlayın.
11. Sol mikrofonun L/R pinini breadboard'un mavi hattına (GND - Sol kanal) bağlayın.
12. Sağ mikrofonun L/R pinini breadboard'un kırmızı hattına (3.3V - Sağ kanal) bağlayın.

**Mikrofon Yerleşimi:**
- Sol mikrofonu sistemin sol tarafına (örneğin batı yönüne) yerleştirin.
- Sağ mikrofonu sistemin sağ tarafına (örneğin doğu yönüne) yerleştirin.
- Sistem ses modeliyle sol kanalda drone tespit ederse sola (270°), sağ kanalda tespit ederse sağa (90°) dönecektir.

### C. Güç ve Toprak Bağlantıları
- Tüm motorların kırmızı (VDD) kablolarını LM2596 Regülatörün **OUT+ (5V)** çıkışına bağlayın.
- Tüm motorların kahverengi (GND) kablolarını LM2596 Regülatörün **OUT- (GND)** çıkışına bağlayın.
- Regülatörün GND'sini Raspberry Pi'nin herhangi bir GND pinine (örneğin Pin 6) bağlayarak ortak toprak sağlayın.

Bu kurulumla sistem titremesiz çalışacak, stereo ses dinleme yapacak ve tehdit algılandığında otomatik olarak hedef yönüne dönecektir! 🚀
