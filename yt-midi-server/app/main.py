from flask import Flask, request, jsonify, send_file
import os
import subprocess
import uuid
from zipfile import ZipFile

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    url = request.form.get('youtubeUrl')
    file = request.files.get('file')
    
    if not url and not file:
        return jsonify({"error": "Missing YouTube URL or file"}), 400

    session_id = str(uuid.uuid4())
    work_dir = f"/tmp/{session_id}"
    os.makedirs(work_dir, exist_ok=True)

    # Handle YouTube URL
    if url:
        wav_file = os.path.join(work_dir, "audio.wav")
        subprocess.run(f"yt-dlp -x --audio-format wav -o '{wav_file}' '{url}'", shell=True)
    
    # Handle uploaded file
    elif file:
        wav_file = os.path.join(work_dir, "audio.wav")
        file.save(wav_file)

    # Separate stems with spleeter
    subprocess.run(f"spleeter separate -i '{wav_file}' -p spleeter:4stems -o '{work_dir}/stems'", shell=True)

    # Convert stems to MIDI
    midi_dir = os.path.join(work_dir, "midi")
    os.makedirs(midi_dir, exist_ok=True)
    for stem in ["vocals", "drums", "bass", "other"]:
        stem_path = os.path.join(work_dir, "stems", "audio", f"{stem}.wav")
        midi_out = os.path.join(midi_dir, f"{stem}.mid")
        subprocess.run(f"basic-pitch '{stem_path}' --output-midi '{midi_out}'", shell=True)

    # Zip the MIDI files
    zip_path = os.path.join(work_dir, "output.zip")
    with ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(midi_dir):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)

    return send_file(zip_path, as_attachment=True, download_name="midi-files.zip")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
