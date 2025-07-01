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
            padding: 36px 0 0 0;
            font-size: 2.1rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-align: center;
            text-shadow: 0 2px 12px #0033a055;
        }
        .panel {
            background: var(--white);
            border-radius: 24px;
            box-shadow: var(--panel-shadow);
            padding: 48px 32px 36px 32px;
            max-width: 480px;
            width: 100%;
            margin: 48px auto 32px auto;
            display: flex;
            flex-direction: column;
            gap: 22px;
        }
        label {
            font-weight: 600;
            color: #0033a0;
            margin-bottom: 6px;
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        input[type=file] {
            padding: 10px;
            border: 1.5px solid #e0e7ef;
            border-radius: 10px;
            background: #f7faff;
            font-size: 1rem;
            transition: border 0.2s;
        }
        input[type=file]:focus, input[type=file]:hover {
            border: 1.5px solid var(--accent-blue);
        }
        button {
            background: linear-gradient(90deg, var(--main-blue) 60%, var(--accent-blue) 100%);
            color: var(--white);
            border: none;
            border-radius: 12px;
            padding: 16px 0;
            font-size: 1.15rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 2px 8px #0033a022;
            transition: background 0.2s, transform 0.1s;
        }
        button:hover {
            background: linear-gradient(90deg, #002266 60%, #4f8cff 100%);
            transform: translateY(-2px) scale(1.03);
        }
        textarea {
            width: 100%;
            height: 180px;
            margin-top: 8px;
            padding: 14px;
            border-radius: 12px;
            border: 1.5px solid #e0e7ef;
            background: #f7faff;
            font-size: 1.08rem;
            resize: vertical;
            transition: border 0.2s;
        }
        textarea:focus, textarea:hover {
            border: 1.5px solid var(--accent-blue);
        }
        .download {
            margin-top: 10px;
            display: flex;
            gap: 12px;
            justify-content: flex-end;
        }
        .error {
            color: #dc2626;
            background: #fee2e2;
            border: 1.5px solid #fecaca;
            padding: 12px;
            border-radius: 10px;
            margin-top: 8px;
            font-size: 1.08rem;
        }
        @media (max-width: 700px) {
            .panel {
                max-width: 98vw;
                padding: 18px 2vw 18px 2vw;
                margin: 18px 0 18px 0;
            }
            header {
                font-size: 1.2rem;
                padding: 18px 0 0 0;
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
</head>
<body>
    <header>
        Ses/Video Metne Dönüştürücü
    </header>
    <div class="panel">
        <form method="post" enctype="multipart/form-data">
            <label for="file">Ses veya video dosyası yükle:</label>
            <input type="file" name="file" id="file" accept="audio/*,video/*" required>
            <button type="submit">Yükle ve Çevir</button>
        </form>
        {% if text %}
            <label for="transcript">Çıktı (Türkçe Transkript):</label>
            <textarea id="transcript" readonly>{{ text }}</textarea>
            <div class="download">
                <form method="post" action="/download-txt" style="display:inline;">
                    <input type="hidden" name="text" value="{{ text|tojson|safe }}">
                    <button type="submit">Metni TXT İndir</button>
                </form>
            </div>
        {% elif error %}
            <div class="error">{{ error }}</div>
        {% endif %}
    </div>
    <footer>
        2025 Tüm Hakları Sakldıır İnnosa Yazılım Teknoloji
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
