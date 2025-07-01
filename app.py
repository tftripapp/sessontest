from flask import Flask, request, render_template_string, send_file
import tempfile
import os
from faster_whisper import WhisperModel
from io import BytesIO
from docx import Document

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
            --white: #ffffff;
        }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            background: var(--white);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            background: var(--main-blue);
            color: var(--white);
            padding: 18px 36px 12px 36px;
            font-size: 1.3rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-align: left;
        }
        .container {
            background: var(--white);
            width: 100%;
            max-width: 100vw;
            margin: 0;
            padding: 40px 0 32px 0;
            min-height: 70vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            box-sizing: border-box;
        }
        .form-box {
            width: 100%;
            max-width: 520px;
            background: #f4f7fb;
            border-radius: 14px;
            box-shadow: 0 4px 24px #0033a01a;
            padding: 32px 24px 24px 24px;
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
            background: var(--main-blue);
            color: var(--white);
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
            background: #002266;
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
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
        .error {
            color: #dc2626;
            background: #fee2e2;
            border: 1px solid #fecaca;
            padding: 10px;
            border-radius: 6px;
            margin-top: 8px;
        }
        @media (max-width: 700px) {
            .form-box {
                max-width: 98vw;
                padding: 18px 2vw 18px 2vw;
            }
            header {
                font-size: 1.1rem;
                padding: 12px 10px 8px 10px;
            }
        }
        footer {
            margin-top: auto;
            background: var(--main-blue);
            color: var(--white);
            text-align: center;
            padding: 18px 0 12px 0;
            font-size: 1rem;
            letter-spacing: 0.2px;
        }
    </style>
</head>
<body>
    <header>
        Ses/Video Metne Dönüştürücü
    </header>
    <div class="container">
        <div class="form-box">
            <form method="post" enctype="multipart/form-data">
                <label for="file"><b>Ses veya video dosyası yükle:</b></label>
                <input type="file" name="file" id="file" accept="audio/*,video/*" required>
                <button type="submit">Yükle ve Çevir</button>
            </form>
            {% if text %}
                <label for="transcript"><b>Çıktı (Türkçe Transkript):</b></label>
                <textarea id="transcript" readonly>{{ text }}</textarea>
                <div class="download">
                    <form method="post" action="/download-txt" style="display:inline;">
                        <input type="hidden" name="text" value="{{ text|tojson|safe }}">
                        <button type="submit">Metni TXT İndir</button>
                    </form>
                    <form method="post" action="/download-docx" style="display:inline;">
                        <input type="hidden" name="text" value="{{ text|tojson|safe }}">
                        <button type="submit">Metni Word İndir</button>
                    </form>
                </div>
            {% elif error %}
                <div class="error">{{ error }}</div>
            {% endif %}
        </div>
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

@app.route('/download-docx', methods=['POST'])
def download_docx():
    text = request.form.get('text', '')
    doc = Document()
    doc.add_paragraph(text)
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='transkript.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 
