import os
from flask import Flask, render_template, request, send_from_directory, jsonify
from gtts import gTTS
import fitz  # PyMuPDF
from langdetect import detect

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "static/audio"

# Ensure folders exist
for folder in [UPLOAD_FOLDER, AUDIO_FOLDER]:
    if os.path.isfile(folder):
        os.remove(folder)
    os.makedirs(folder, exist_ok=True)


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF (fitz)"""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    pdf_file = request.files["pdf"]
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
    pdf_file.save(pdf_path)

    # Extract text
    text = extract_text_from_pdf(pdf_path)

    if not text.strip():
        return jsonify({"error": "No readable text found in PDF"}), 400

    # Detect language (English or Hindi)
    try:
        lang = detect(text[:500])
    except:
        lang = "en"

    if lang.startswith("hi"):
        tts_lang = "hi"
        audio_filename = "audiobook_hi.mp3"
    else:
        tts_lang = "en"
        audio_filename = "audiobook_en.mp3"

    audio_path = os.path.join(AUDIO_FOLDER, audio_filename)

    # Generate audio
    tts = gTTS(text=text, lang=tts_lang, slow=False)
    tts.save(audio_path)

    return jsonify({
        "audio_url": f"/static/audio/{audio_filename}",
        "download_url": f"/download/{audio_filename}",
        "language": tts_lang
    })


@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(AUDIO_FOLDER, filename, as_attachment=True)


@app.route("/static/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True)
