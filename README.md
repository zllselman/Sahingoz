# 🦅 ŞAHİNGÖZÜ: Otonom Hibrit Drone Savunma ve Takip Sistemi

**Şahingözü Projesine Hoş Geldiniz!**  
Eğer bu sayfaya geldiyseniz ve *"Burada ne oluyor, bu kablolar ve kodlar ne işe yarıyor?"* diyorsanız, tam olarak doğru yerdesiniz. Bu belge, teknolojiyle veya mühendislikle hiçbir alakası olmayan birinin bile sistemi bir çırpıda anlayabilmesi için özel olarak, aşırı detaylı bir hikaye ve rehber tadında hazırlanmıştır.

---

## 📖 Projenin Amacı Nedir? Neden Böyle Bir Şeye İhtiyaç Duyduk?

Günümüzde dronlar (insansız hava araçları) her yerde. Kargo taşıyorlar, video çekiyorlar ama maalesef bazen de kötü amaçlarla (izinsiz gözetleme, askeri tehdit vb.) kullanılabiliyorlar. Bir drone'u havada tespit etmek çok zordur çünkü çok küçüklerdir ve radarlara kolay kolay yakalanmazlar. Klasik askeri radarlar ise milyonlarca dolar değerindedir.

İşte **Şahingözü** tam olarak bu sorunu çözmek için doğdu!
Biz, **Raspberry Pi 5** (kredi kartı büyüklüğünde ama çok güçlü bir bilgisayar) kullanarak, son derece düşük maliyetli ama bir o kadar da zeki bir **"Otonom Nöbetçi Kulesi"** inşa ettik. Bu kule; tıpkı bir insan gibi duyabilir, görebilir, kafasını çevirebilir ve tehdidi etkisiz hale getirebilir.

Özetle Şahingözü; bir bölgeyi (örneğin bir askeri üssü veya özel bir mülkü) izinsiz giren dronlara karşı **7 gün 24 saat uyanık kalarak, insan müdahalesi olmadan koruyan yapay zeka destekli bir robotik sistemdir.**

---

## ⚙️ Sistem Nasıl Çalışır? (Adım Adım Otonom Avcılık)

Sistemi bir dağın başına koyup fişini taktığınızı hayal edin. Herhangi bir ekran, klavye veya fare bağlı değildir (Buna **Headless - Ekransız Mod** denir). Kule tamamen kendi başına şu adımları izler:

### 1. Dinleme ve Fark Etme (Kulakların Devreye Girmesi)
Kulenin 4 tarafına (Kuzey, Güney, Doğu, Batı) yerleştirilmiş 4 adet hassas mikrofon (INMP441) vardır. Sistem sürekli olarak etrafı dinler. Rüzgar sesi, kuş sesi, araba motoru sesi... Yapay zeka tüm bunları filtreler. Ancak uzaktan bir **"vızzzzz"** (drone pervanesi) sesi duyduğunda, anında alarm durumuna geçer. Sesi analiz ederek dronun tam olarak hangi yönden (örneğin Doğu'dan) geldiğini hesaplar.

### 2. Yönelme (Boynun Dönmesi)
Sesin Doğu'dan geldiği anlaşıldığı an, kulenin altındaki dev motor (**Pan Motoru - 360 Derece Servo**) kuleyi hızla Doğu yönüne doğru çevirir. Kule artık körü körüne değil, şüpheli sese doğru bakmaktadır.

### 3. Görme ve Kilitlenme (Gözlerin Devreye Girmesi)
Kule o yöne döndükten sonra tepesindeki yüksek çözünürlüklü Kamera (IMX477 HQ) devreye girer. Görüntü işleme yapay zekası (YOLO Modeli) gökyüzünü saniyede onlarca kez tarar. Hedef ekranda göründüğü an, sistem dronun etrafına sanal bir kırmızı kutu çizer. **Buna "Görsel Kilit" (Visual Lock) denir.** Artık kulaklara ihtiyaç kalmamıştır, av gözle görülmüştür.

### 4. Dinamik Takip (Avın Peşinden Ayrılmama)
Drone havada sabit durmaz, sağa sola veya aşağı yukarı kaçmaya çalışır. Şahingözü bunu anlar!
- Drone sağa kaçarsa, alt motor kuleyi sağa çevirir.
- Drone yukarı çıkarsa, üstteki ikinci motor (**Tilt Motoru - 180 Derece Servo**) kameranın kafasını yukarı kaldırır.
Tıpkı bir kedinin lazer ışığını gözleriyle takip etmesi gibi, sistem drone'u ekranın tam merkezinde tutmak için motorlarla sürekli düzeltme yapar.

### 5. Ateşleme / Etkisiz Hale Getirme
Drone kameranın tam ortasına oturduğunda (hata payı sıfırlandığında), sistem hedefin nişangaha tam oturduğunu anlar. Ardından elektronik bir anahtarı (Röle) çeker. Bu röleye ne bağladığınız size kalmıştır; güçlü bir lazer, bir sinyal bozucu (jammer) veya bir paintball silahı! Ateşleme komutu verilir ve tehdit bertaraf edilir.

---

## 🛠️ Hangi Parça Ne İşe Yarıyor? (Donanım Sözlüğü)

Mühendis olmayanlar için parçaların gerçek hayattaki karşılıkları:

*   **Raspberry Pi 5 (Beyin):** Tüm kararları veren, sesleri ve görüntüleri saniyenin onda biri hızında hesaplayan mini bilgisayardır.
*   **INMP441 Mikrofonlar (Kulaklar):** Sesi çok net bir şekilde dijital veriye çevirip beyne ileten minik dinleme cihazlarıdır.
*   **Kamera (Göz):** Gökyüzünün fotoğrafını çekip içindeki dronu bulan yüksek kaliteli mercektir.
*   **MG995 Servo Motorlar (Boyun ve Kaslar):**
    *   **360 Derece Servo (Pan):** Belden dönen motor. Kuleyi sağa ve sola sınırsız döndürür.
    *   **180 Derece Servo (Tilt):** Boyundan dönen motor. Kafayı aşağı ve yukarı ezer.
*   **Slip Ring / Kayar Bilezik (Omurilik):** Bu çok kritik bir parçadır! Kule sağa doğru 50 kere dönerse normalde kablolar dolanır ve kopar. Kayar bilezik, içinde dönen metal halkalar sayesinde kablolar birbirine dolanmadan elektriği yukarıdaki dönen kısma kesintisiz aktarır.
*   **LM2596 Regülatör (Kalp Pili):** Devasa bataryanın gücünü (12V-24V) alıp, Raspberry Pi'nin yanmaması için tam 5.1V'a (sakin bir akıma) düşüren çeviricidir.

---

## 📂 Dosyalar Ne İşe Yarıyor?

Projenin içinde birçok kod dosyası göreceksiniz. Onların görevleri şöyledir:

- **`baslat.py`**: Sistemin şalteridir. Elektrik verildiğinde otomatik olarak çalışır, HDMI (ekran) kablosu takılı mı diye bakar. Ekran yoksa "Tamam, dağdayız, göreve başlıyorum" diyerek ana sistemi tetikler.
- **`hibrit_operasyon.py`**: Sistemin asıl ruhudur. Yapay zekanın sesi dinlediği, kameradan görüntü aldığı, motorlara "sağa dön, sola dön" dediği tüm zeka algoritması bu dosyanın içindedir.
- **`KURULUM_REHBERI.md`**: Bu devasa sistemi parçalar halindeyken evde masanın üzerinde nasıl birleştireceğinizi anlatan adımdır. Hangi renk kablo nereye girecek tek tek orada yazar.

---

## 🚀 Sistemi Nasıl Kurabilirim?

Eğer bu yazıyı okuduysanız ve *"Harika! Ben de bunu kurmak istiyorum, elimde parçalar var ama kabloları nereye takacağımı bilmiyorum"* diyorsanız;
Lütfen klasörün içindeki **`KURULUM_REHBERI.md`** dosyasına gidin. Orada hiçbir teknik bilgiye ihtiyaç duymadan, kablo renklerine kadar adım adım sistemi nasıl yapacağınızı anlattık.

*Şahingözü asla uyumaz, asla gözden kaçırmaz.* 🦅
