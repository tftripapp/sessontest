from flask import Flask, request, render_template_string, send_file
import tempfile
import os
from faster_whisper import WhisperModel
# from io import BytesIO
# from docx import Document

app = Flask(__name__)

# Modeli baştan yükle (CPU için tiny veya base önerilir)
model = WhisperModel("base", device="cpu", compute_type="int8")

HTML = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Ses/Video Metne Dönüştürücü</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --main-blue: #0033a0;
            --accent-blue: #4f8cff;
            --white: #ffffff;
            --panel-shadow: 0 8px 32px #0033a033;
            --success-green: #22c55e;
            --success-bg: #e7fbe9;
            --error-red: #dc2626;
            --error-bg: #fee2e2;
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            min-height: 100vh;
            background: linear-gradient(120deg, var(--main-blue) 0%, var(--accent-blue) 100%);
            display: flex;
            flex-direction: column;
        }
        header {
            background: transparent;
            color: var(--white);
            padding: 48px 0 0 0;
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            text-align: center;
            text-shadow: 0 2px 12px #0033a055;
        }
        .subtitle {
            color: #e0e7ef;
            text-align: center;
            font-size: 1.15rem;
            margin-top: 16px;
            margin-bottom: 36px;
            font-weight: 400;
        }
        .panel {
            background: var(--white);
            border-radius: 24px;
            box-shadow: var(--panel-shadow);
            padding: 40px 32px 32px 32px;
            max-width: 480px;
            width: 100%;
            margin: 0 auto 32px auto;
            display: flex;
            flex-direction: column;
            gap: 28px;
        }
        .upload-box {
            background: #f6f8fc;
            border-radius: 16px;
            border: 2px dashed #b6c6e3;
            padding: 32px 18px 24px 18px;
            text-align: center;
            margin-bottom: 18px;
        }
        .upload-box svg {
            width: 48px;
            height: 48px;
            margin-bottom: 10px;
            fill: #7baaf7;
        }
        .upload-label {
            font-size: 1.13rem;
            font-weight: 600;
            color: #0033a0;
            margin-bottom: 8px;
        }
        .upload-desc {
            color: #6b7280;
            font-size: 0.98rem;
            margin-bottom: 18px;
        }
        .file-input-btn {
            display: inline-block;
            background: #fff;
            color: var(--main-blue);
            border: 2px solid var(--accent-blue);
            border-radius: 8px;
            padding: 10px 28px;
            font-size: 1.08rem;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.2s, color 0.2s, border 0.2s;
        }
        .file-input-btn:hover {
            background: var(--accent-blue);
            color: #fff;
        }
        input[type=file] {
            display: none;
        }
        .main-btn {
            background: linear-gradient(90deg, var(--main-blue) 60%, var(--accent-blue) 100%);
            color: var(--white);
            border: none;
            border-radius: 12px;
            padding: 18px 0;
            font-size: 1.18rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 2px 8px #0033a022;
            transition: background 0.2s, transform 0.1s;
            margin-top: 10px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .main-btn svg {
            width: 22px;
            height: 22px;
            fill: #fff;
        }
        .main-btn:hover {
            background: linear-gradient(90deg, #002266 60%, #4f8cff 100%);
            transform: translateY(-2px) scale(1.03);
        }
        .features {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            margin-top: 18px;
        }
        .feature {
            flex: 1;
            background: #f6f8fc;
            border-radius: 12px;
            padding: 18px 10px 12px 10px;
            text-align: center;
            box-shadow: 0 2px 8px #0033a012;
        }
        .feature svg {
            width: 28px;
            height: 28px;
            margin-bottom: 6px;
        }
        .feature-title {
            font-weight: 700;
            color: #0033a0;
            margin-bottom: 2px;
            font-size: 1.05rem;
        }
        .feature-desc {
            color: #6b7280;
            font-size: 0.97rem;
        }
        .success-box {
            background: var(--success-bg);
            border: 1.5px solid var(--success-green);
            color: #14532d;
            border-radius: 14px;
            padding: 18px 18px 12px 18px;
            margin-bottom: 10px;
        }
        .success-title {
            display: flex;
            align-items: center;
            font-weight: 700;
            font-size: 1.13rem;
            margin-bottom: 8px;
            color: var(--success-green);
        }
        .success-title svg {
            width: 22px;
            height: 22px;
            margin-right: 6px;
            fill: var(--success-green);
        }
        .success-text {
            background: #fff;
            border-radius: 8px;
            padding: 14px 12px;
            font-size: 1.07rem;
            color: #222;
            border: 1px solid #d1fae5;
        }
        .error-box {
            background: var(--error-bg);
            border: 1.5px solid var(--error-red);
            color: #991b1b;
            border-radius: 14px;
            padding: 18px 18px 12px 18px;
            margin-bottom: 10px;
        }
        .error-title {
            display: flex;
            align-items: center;
            font-weight: 700;
            font-size: 1.13rem;
            margin-bottom: 8px;
            color: var(--error-red);
        }
        .error-title svg {
            width: 22px;
            height: 22px;
            margin-right: 6px;
            fill: var(--error-red);
        }
        .error-text {
            background: #fff;
            border-radius: 8px;
            padding: 14px 12px;
            font-size: 1.07rem;
            color: #222;
            border: 1px solid #fecaca;
        }
        @media (max-width: 700px) {
            .panel {
                max-width: 98vw;
                padding: 18px 2vw 18px 2vw;
                margin: 18px 0 18px 0;
            }
            header {
                font-size: 1.3rem;
                padding: 18px 0 0 0;
            }
            .features {
                flex-direction: column;
                gap: 10px;
            }
        }
        footer {
            margin-top: auto;
            background: transparent;
            color: var(--white);
            text-align: center;
            padding: 24px 0 18px 0;
            font-size: 1.08rem;
            letter-spacing: 0.2px;
            text-shadow: 0 2px 12px #0033a055;
        }
    </style>
    <script>
    function triggerFileInput() {
        document.getElementById('file').click();
    }
    function showFileName() {
        var input = document.getElementById('file');
        var label = document.getElementById('file-label');
        if (input.files.length > 0) {
            label.innerText = input.files[0].name;
            label.style.color = '#0033a0';
        } else {
            label.innerText = 'Dosyayı buraya sürükleyin veya seçin';
            label.style.color = '#6b7280';
        }
    }
    </script>
</head>
<body>
    <header>
        Ses/Video Metne Dönüştürücü
    </header>
    <div class="subtitle">Ses ve video dosyalarınızı kolayca metne dönüştürün</div>
    <div class="panel">
        <form method="post" enctype="multipart/form-data">
            <div class="upload-label">Ses veya video dosyası yükle:</div>
            <div class="upload-box" onclick="triggerFileInput()" style="cursor:pointer;">
                <svg viewBox="0 0 48 48"><path d="M24 6a1.5 1.5 0 0 1 1.5 1.5V30.1l7.2-7.2a1.5 1.5 0 1 1 2.1 2.1l-9.75 9.75a1.5 1.5 0 0 1-2.1 0l-9.75-9.75a1.5 1.5 0 1 1 2.1-2.1l7.2 7.2V7.5A1.5 1.5 0 0 1 24 6z"/><path d="M6 36a1.5 1.5 0 0 1 1.5-1.5h33a1.5 1.5 0 0 1 0 3h-33A1.5 1.5 0 0 1 6 36z"/></svg>
                <div id="file-label">Dosyayı buraya sürükleyin veya seçin</div>
                <div class="upload-desc">MP3, MP4, WAV, M4A formatları desteklenir (Maks: 100MB)</div>
                <label class="file-input-btn">
                    <input type="file" name="file" id="file" accept="audio/*,video/*" required onchange="showFileName()">
                    Dosya Seç
                </label>
            </div>
            <button type="submit" class="main-btn">
                <svg viewBox="0 0 24 24"><path d="M16.707 10.293a1 1 0 0 0-1.414 0L13 12.586V4a1 1 0 1 0-2 0v8.586l-2.293-2.293a1 1 0 0 0-1.414 1.414l4 4a1 1 0 0 0 1.414 0l4-4a1 1 0 0 0 0-1.414z"/></svg>
                Yükle ve Çevir
            </button>
        </form>
        {% if text %}
            <div class="success-box">
                <div class="success-title">
                    <svg viewBox="0 0 24 24"><path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm-1.293-6.707a1 1 0 0 0 1.414 0l5-5a1 1 0 1 0-1.414-1.414L11 13.586l-1.293-1.293a1 1 0 0 0-1.414 1.414l2 2z"/></svg>
                    Dönüştürme Tamamlandı!
                </div>
                <div class="success-text">{{ text }}</div>
            </div>
            <div class="download">
                <form method="post" action="/download-txt" style="display:inline;">
                    <input type="hidden" name="text" value="{{ text|tojson|safe }}">
                    <button type="submit">Metni TXT İndir</button>
                </form>
            </div>
        {% elif error %}
            <div class="error-box">
                <div class="error-title">
                    <svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                    Hata!
                </div>
                <div class="error-text">{{ error }}</div>
            </div>
        {% endif %}
        <div class="features">
            <div class="feature">
                <svg viewBox="0 0 24 24"><path d="M13 2.05V4.07A8.001 8.001 0 0 1 20 12h2.02C21.93 6.48 17.52 2.07 13 2.05zM4.07 11H2.05C2.07 6.48 6.48 2.07 12 2.05v2.02A8.001 8.001 0 0 0 4.07 11zm15.93 2h-2.02A8.001 8.001 0 0 1 12 20v2.02c5.52-.02 9.93-4.43 9.95-9.95zM11 19.93V17.91A8.001 8.001 0 0 1 4 12H1.98c.02 5.52 4.43 9.93 9.95 9.95z"/></svg>
                <div class="feature-title">Hızlı İşleme</div>
                <div class="feature-desc">Dosyalarınızı saniyeler içinde işliyoruz</div>
            </div>
            <div class="feature">
                <svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 0-10 10c0 5.25 4.25 9.5 9.5 9.5S21.5 17.25 21.5 12A10 10 0 0 0 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>
                <div class="feature-title">Güvenli</div>
                <div class="feature-desc">Dosyalarınız güvenle işlenir ve saklanmaz</div>
            </div>
            <div class="feature">
                <svg viewBox="0 0 24 24"><path d="M12 2a10 10 0 0 0-10 10c0 5.25 4.25 9.5 9.5 9.5S21.5 17.25 21.5 12A10 10 0 0 0 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>
                <div class="feature-title">Türkçe Desteği</div>
                <div class="feature-desc">Türkçe ses tanıma teknolojisi</div>
            </div>
        </div>
    </div>
    <footer>
        © 2025 Tüm Hakları Sakldıır İnnosa Yazılım Teknoloji
    </footer>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    text = None
    error = None
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            error = 'Dosya seçilmedi.'
        else:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
                    file.save(tmp.name)
                    segments, info = model.transcribe(tmp.name, language='tr')
                    text = "".join([seg.text for seg in segments])
                os.unlink(tmp.name)
            except Exception as e:
                error = f'Hata: {str(e)}'
    return render_template_string(HTML, text=text, error=error)

@app.route('/download-txt', methods=['POST'])
def download_txt():
    text = request.form.get('text', '')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tmp:
        tmp.write(text)
        tmp.flush()
        return send_file(tmp.name, as_attachment=True, download_name='transkript.txt', mimetype='text/plain')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 
