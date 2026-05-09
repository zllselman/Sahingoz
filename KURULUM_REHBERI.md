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

> **DİKKAT:** Raspberry Pi 5 çok hassastır. Bataryayı doğrudan Pi'ye **ASLA** bağlamayın, anında yanar. Araya LM2596 Voltaj Regülatörü koyacağız.

1. **Batarya -> Regülatör (LM2596):** 
   Bataryanızın Kırmızı (+) ve Siyah (-) kablolarını alın. LM2596 kartının `IN+` ve `IN-` yazan yerlerine lehimleyin veya vidalayın.
2. **Regülatörü Ayarlama:** 
   LM2596'nın üstündeki küçük sarı vidayı bir tornavida ile çevirin. Bir multimetre (voltmetre) ile çıkış (`OUT+` ve `OUT-`) voltajını ölçün. Ekranda tam olarak **5.1V** (5.1 Volt) görene kadar vidayı çevirin.
3. **Regülatör -> Slip Ring -> Raspberry Pi:**
   - LM2596'dan çıkan `OUT+` (5.1V) kablosunu Slip Ring'in bir kablosuna (örneğin kırmızı) bağlayın.
   - LM2596'dan çıkan `OUT-` (GND) kablosunu Slip Ring'in diğer kablosuna (örneğin siyah) bağlayın.
   - Slip Ring'in dönen üst kısmından çıkan o kırmızı kabloyu Raspberry Pi'nin **Pin 2 (5V)** veya **Pin 4 (5V)** ayağına bağlayın. Siyah kabloyu ise **Pin 6 (GND)** ayağına bağlayın.
   *(Artık Pi 5, kule dönerken bile elektrik alabilecek!)*

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

> **UYARI:** Motorların Kırmızı kablolarını asla Raspberry Pi'nin üzerinden almayın. Çok akım çeker ve Pi'yi kapatır. Motorların kırmızı kablolarını doğrudan LM2596 Regülatörün 5V çıkışına bağlayın.

**Pan Motoru (360° - Taret Dönüşü):**
1. **Kırmızı Kablo:** LM2596'nın 5V (OUT+) çıkışına.
2. **Kahverengi Kablo:** LM2596'nın GND (OUT-) çıkışına **VE** Raspberry Pi'nin herhangi bir GND pinine (Örn: Pin 14). *(Buna ortak toprak denir, şarttır!)*
3. **Turuncu Kablo (Sinyal):** Raspberry Pi'nin **Pin 11 (GPIO 17)** ayağına.

**Tilt Motoru (180° - Kamera Kafası):**
1. **Kırmızı Kablo:** LM2596'nın 5V (OUT+) çıkışına.
2. **Kahverengi Kablo:** Ortağa (GND).
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
