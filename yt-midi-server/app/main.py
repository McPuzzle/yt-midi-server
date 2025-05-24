@app.route('/convert', methods=['POST'])
def convert():
    try:
        url = request.form.get('youtubeUrl')
        file = request.files.get('file')
        print("Received:", "URL" if url else "File" if file else "Nothing")

        if not url and not file:
            return jsonify({"error": "Missing YouTube URL or file"}), 400

        session_id = str(uuid.uuid4())
        work_dir = f"/tmp/{session_id}"
        os.makedirs(work_dir, exist_ok=True)

        wav_file = os.path.join(work_dir, "audio.wav")

        if url:
            print("Downloading YouTube audio...")
            subprocess.run(f"yt-dlp -x --audio-format wav -o '{wav_file}' '{url}'", shell=True, check=True)
        elif file:
            print("Saving uploaded file...")
            file.save(wav_file)

        print("Running spleeter...")
        subprocess.run(f"spleeter separate -i '{wav_file}' -p spleeter:4stems -o '{work_dir}/stems'", shell=True, check=True)

        midi_dir = os.path.join(work_dir, "midi")
        os.makedirs(midi_dir, exist_ok=True)

        for stem in ["vocals", "drums", "bass", "other"]:
            stem_path = os.path.join(work_dir, "stems", "audio", f"{stem}.wav")
            midi_out = os.path.join(midi_dir, f"{stem}.mid")
            print(f"Converting {stem} to MIDI...")
            subprocess.run(f"basic-pitch '{stem_path}' --output-midi '{midi_out}'", shell=True, check=True)

        zip_path = os.path.join(work_dir, "output.zip")
        with ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(midi_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)

        return send_file(zip_path, as_attachment=True, download_name="midi-files.zip")

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
