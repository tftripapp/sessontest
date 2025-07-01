# Türkçe Ses/Video'dan Metne Çeviri Web Uygulaması

## Kurulum

1. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
2. Uygulamayı başlatın:
   ```bash
   python app.py
   ```
3. Tarayıcıda `http://localhost:5000` adresine gidin.

## Özellikler
- Ses veya video dosyası yükleyin
- Türkçe transkript alın
- Sonucu kopyalayın veya indirin

## Ücretsiz Deploy
- PythonAnywhere (ücretsiz, küçük projeler için uygundur): https://www.pythonanywhere.com/
- Not: Model yükleme süresi ve dosya boyutu kısıtlamalarına dikkat edin.

## Notlar
- Model olarak `base` kullanıldı. Daha hızlı/az RAM için `tiny` seçebilirsiniz.
- Sadece geçici dosya saklama kullanılır, yüklenen dosyalar kaydedilmez. 