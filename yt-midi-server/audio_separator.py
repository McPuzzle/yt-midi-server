import subprocess

def run_spleeter(input_path, output_path):
    subprocess.run(['spleeter', 'separate', '-i', input_path, '-o', output_path], check=True)
