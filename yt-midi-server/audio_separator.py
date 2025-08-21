import subprocess

def run_spleeter(input_path, output_path):
    # Call Spleeter to separate the audio into stems.
    # It assumes Spleeter is already installed via requirements.txt.
    subprocess.run(['spleeter', 'separate', '-i', input_path, '-o', output_path], check=True)
