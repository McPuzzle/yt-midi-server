import subprocess

def run_spleeter(input_path, output_path):
    subprocess.run([
        "pip", "install", "spleeter==2.4.2", "--no-cache-dir"
    ], check=True)

    subprocess.run([
        "spleeter", "separate", "-i", input_path, "-o", output_path
    ], check=True)
