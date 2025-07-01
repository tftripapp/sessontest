from flask import Flask, request, render_template_string, send_file
import tempfile
import os
from faster_whisper import WhisperModel

app = Flask(__name__)

# Modeli baştan yükle (CPU için tiny veya base önerilir)
model = WhisperModel("base", device="cpu", compute_type="int8")

HTML = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Türkçe Ses/Video'dan Metne Çeviri</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            background: linear-gradient(135deg, #f8fafc 0%, #e0e7ef 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            background: #2563eb;
            color: #fff;
            padding: 32px 0 18px 0;
            text-align: center;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: 1px;
            box-shadow: 0 2px 8px #0001;
        }
        .container {
            background: #fff;
            padding: 32px 24px 24px 24px;
            border-radius: 14px;
            max-width: 420px;
            margin: 40px auto 24px auto;
            box-shadow: 0 4px 24px #0002;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        input[type=file] {
            padding: 8px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background: #f3f4f6;
        }
        button {
            background: #2563eb;
            color: #fff;
            border: none;
            border-radius: 6px;
            padding: 12px 0;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            margin-top: 4px;
        }
        button:hover {
            background: #1d4ed8;
        }
        textarea {
            width: 100%;
            height: 180px;
            margin-top: 8px;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #d1d5db;
            background: #f9fafb;
            font-size: 1rem;
            resize: vertical;
        }
        .download {
            margin-top: 10px;
            text-align: right;
        }
        .error {
            color: #dc2626;
            background: #fee2e2;
            border: 1px solid #fecaca;
            padding: 10px;
            border-radius: 6px;
            margin-top: 8px;
        }
        @media (max-width: 600px) {
            .container {
                max-width: 98vw;
                margin: 16px 1vw 16px 1vw;
                padding: 18px 6vw 18px 6vw;
            }
            header {
                font-size: 1.3rem;
                padding: 18px 0 10px 0;
            }
        }
        footer {
            margin-top: auto;
            background: #f1f5f9;
            color: #64748b;
            text-align: center;
            padding: 18px 0 12px 0;
            font-size: 1rem;
            letter-spacing: 0.2px;
        }
        .footer-link {
            color: #2563eb;
            text-decoration: none;
            font-weight: 500;
        }
        .footer-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <header>
        Türkçe Ses/Video'dan Metne Çeviri
    </header>
    <div class="container">
        <form method="post" enctype="multipart/form-data">
            <label for="file"><b>Ses veya video dosyası yükle:</b></label>
            <input type="file" name="file" id="file" accept="audio/*,video/*" required>
            <button type="submit">Yükle ve Çevir</button>
        </form>
        {% if text %}
            <label for="transcript"><b>Çıktı (Türkçe Transkript):</b></label>
            <textarea id="transcript" readonly>{{ text }}</textarea>
            <div class="download">
                <form method="post" action="/download">
                    <input type="hidden" name="text" value="{{ text|tojson|safe }}">
                    <button type="submit">Metni İndir</button>
                </form>
            </div>
        {% elif error %}
            <div class="error">{{ error }}</div>
        {% endif %}
    </div>
    <footer>
        &copy; 2024 Türkçe Transkript &middot; <a class="footer-link" href="https://railway.app/" target="_blank">Railway ile Barındırıldı</a>
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

@app.route('/download', methods=['POST'])
def download():
    text = request.form.get('text', '')
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tmp:
        tmp.write(text)
        tmp.flush()
        return send_file(tmp.name, as_attachment=True, download_name='transkript.txt', mimetype='text/plain')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 
