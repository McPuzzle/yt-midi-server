from flask import Flask, request, send_file, jsonify
import os
import uuid
import subprocess
from zipfile import ZipFile

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        # Accept either a YouTube URL or an uploaded file
        url = request.form.get('youtubeUrl')
        uploaded_file = request.files.get('file')
        if not url and not uploaded_file:
            return jsonify({"error": "Missing YouTube URL or file"}), 400

        # Create a working directory for this request
        session_id = str(uuid.uuid4())
        work_dir = f"/tmp/{session_id}"
        os.makedirs(work_dir, exist_ok=True)
        wav_file = os.path.join(work_dir, "audio.wav")

        # Download the audio (if a URL was given) or save the uploaded file
        if url:
            subprocess.run(
                ['yt-dlp', '-x', '--audio-format', 'wav', '-o', wav_file, url],
                check=True
            )
        else:
            uploaded_file.save(wav_file)

        # Separate the track into stems (vocals, drums, bass, other)
        subprocess.run(
            ['spleeter', 'separate', '-i', wav_file, '-p', 'spleeter:4stems', '-o',
             os.path.join(work_dir, 'stems')],
            check=True
        )

        # Convert each stem to MIDI
        midi_dir = os.path.join(work_dir, 'midi')
        os.makedirs(midi_dir, exist_ok=True)
        for stem in ['vocals', 'drums', 'bass', 'other']:
            stem_path = os.path.join(work_dir, 'stems', 'audio', f'{stem}.wav')
            midi_out = os.path.join(midi_dir, f'{stem}.mid')
            subprocess.run(
                ['basic-pitch', stem_path, '--output-midi', midi_out],
                check=True
            )

        # Bundle all MIDI files into a zip
        zip_path = os.path.join(work_dir, "output.zip")
        with ZipFile(zip_path, 'w') as zf:
            for root, _, files in os.walk(midi_dir):
                for fname in files:
                    zf.write(os.path.join(root, fname), arcname=fname)

        # Send the zip file back to the client
        return send_file(zip_path, as_attachment=True, download_name="midi-files.zip")
    except Exception as e:
        # Return any errors as JSON with a 500 status code
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
