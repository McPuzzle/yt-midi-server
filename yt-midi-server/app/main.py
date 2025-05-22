
from flask import Flask, request, jsonify, send_file
import os
import subprocess
import uuid
from zipfile import ZipFile

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    data = request.json
    url = data.get('youtubeUrl')
    if not url:
        return jsonify({"error": "Missing YouTube URL"}), 400

    session_id = str(uuid.uuid4())
    work_dir = f"/tmp/{session_id}"
    os.makedirs(work_dir, exist_ok=True)

    wav_file = os.path.join(work_dir, "audio.wav")
    subprocess.run(f"yt-dlp -x --audio-format wav -o '{wav_file}' '{url}'", shell=True)

    subprocess.run(f"spleeter separate -i '{wav_file}' -p spleeter:4stems -o '{work_dir}/stems'", shell=True)

    midi_dir = os.path.join(work_dir, "midi")
    os.makedirs(midi_dir, exist_ok=True)
    for stem in ["vocals", "drums", "bass", "other"]:
        stem_path = os.path.join(work_dir, "stems", "audio", f"{stem}.wav")
        midi_out = os.path.join(midi_dir, f"{stem}.mid")
        subprocess.run(f"basic-pitch '{stem_path}' '{midi_out}'", shell=True)

    zip_path = os.path.join(work_dir, "output.zip")
    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(midi_dir):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)

    return send_file(zip_path, as_attachment=True, download_name="midi-files.zip")

if __name__ == '__main__':
    app.run(debug=True)
