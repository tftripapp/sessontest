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
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f7f7f7; }
        .container { background: #fff; padding: 30px; border-radius: 8px; max-width: 500px; margin: auto; box-shadow: 0 2px 8px #0001; }
        h1 { text-align: center; }
        input[type=file], button { width: 100%; margin: 10px 0; }
        textarea { width: 100%; height: 200px; margin-top: 10px; }
        .download { margin-top: 10px; text-align: right; }
    </style>
</head>
<body>
<div class="container">
    <h1>Türkçe Ses/Video'dan Metne Çeviri</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" accept="audio/*,video/*" required>
        <button type="submit">Yükle ve Çevir</button>
    </form>
    {% if text %}
        <textarea readonly>{{ text }}</textarea>
        <div class="download">
            <form method="post" action="/download">
                <input type="hidden" name="text" value="{{ text|tojson|safe }}">
                <button type="submit">Metni İndir</button>
            </form>
        </div>
    {% elif error %}
        <p style="color:red;">{{ error }}</p>
    {% endif %}
</div>
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