import os
import subprocess
import urllib.request
import shutil
import zipfile
import tempfile

# Step 1: Install packages from requirements.txt
def install_requirements():
    if os.path.exists("requirements.txt"):
        subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
    else:
        print("requirements.txt not found.")

# Step 2: Download FFmpeg binaries
def download_ffmpeg(url, save_path):
    print(f"Downloading FFmpeg from {url}")
    urllib.request.urlretrieve(url, save_path)
    print(f"Downloaded FFmpeg to {save_path}")

# Step 3: Attempt to extract using Windows Explorer silently via PowerShell
def extract_with_explorer(archive_path, extract_to):
    try:
        ps_command = f"""
        $zipFile = '{os.path.abspath(archive_path)}';
        $outFolder = '{os.path.abspath(extract_to)}';
        $shell = New-Object -ComObject Shell.Application;
        $zip = $shell.NameSpace($zipFile);
        $shell.NameSpace($outFolder).CopyHere($zip.Items(), 16);
        Start-Sleep -Seconds 5;
        """
        subprocess.run(["powershell", "-Command", ps_command], check=True)
        print(f"Extracted {archive_path} to {extract_to} using Windows Explorer.")
        return True
    except subprocess.CalledProcessError:
        print("Windows Explorer method failed.")
        return False

# Step 4: If the Explorer method fails, fall back to 7-Zip
def extract_with_7zip(archive_path, extract_to):
    try:
        subprocess.run(["7z", "x", archive_path, f"-o{extract_to}"], check=True)
        print(f"Extracted {archive_path} to {extract_to} using 7-Zip.")
    except FileNotFoundError:
        print("7z command not found. Please install 7-Zip and add it to your PATH.")
        raise SystemExit(1)

# Step 5: Extract the FFmpeg archive, trying Explorer first then falling back to 7-Zip
def extract_ffmpeg(archive_path, extract_to):
    if not extract_with_explorer(archive_path, extract_to):
        print("Falling back to 7-Zip extraction method...")
        extract_with_7zip(archive_path, extract_to)
    os.remove(archive_path)
    print("Deleted " + archive_path)

# Step 6: Move ffmpeg.exe and ffprobe.exe to ./ffmpeg and delete the extracted folder
def move_ffmpeg_binaries(ffmpeg_dir):
    folders = [f for f in os.listdir(ffmpeg_dir) if os.path.isdir(os.path.join(ffmpeg_dir, f))]
    if len(folders) != 1:
        print("Error: Unable to detect FFmpeg folder with the binaries.")
        return
    changing_folder = folders[0]
    bin_folder = os.path.join(ffmpeg_dir, changing_folder, "bin")
    if not os.path.exists(bin_folder):
        print(f"Error: bin folder not found in {changing_folder}")
        return
    files_to_move = ['ffmpeg.exe', 'ffprobe.exe']
    for file_name in files_to_move:
        src_path = os.path.join(bin_folder, file_name)
        dest_path = os.path.join(ffmpeg_dir, file_name)
        if os.path.exists(src_path):
            shutil.move(src_path, dest_path)
            print(f"Moved {file_name} to {os.path.abspath(ffmpeg_dir)}")
        else:
            print(f"Error: {file_name} not found in {bin_folder}")
    shutil.rmtree(os.path.join(ffmpeg_dir, changing_folder))
    print(f"Deleted folder {changing_folder}")

# Step 7: Download and extract UPX binaries to ./upx
def download_and_extract_upx():
    upx_url = "https://github.com/upx/upx/releases/download/v5.0.0/upx-5.0.0-win64.zip"
    upx_zip = "upx-5.0.0-win64.zip"
    upx_dir = "./upx"
    if not os.path.exists(upx_dir):
        os.makedirs(upx_dir)
    print(f"Downloading UPX from {upx_url}")
    urllib.request.urlretrieve(upx_url, upx_zip)
    print(f"Downloaded UPX to {upx_zip}")

    with zipfile.ZipFile(upx_zip, 'r') as zip_ref:
        temp_dir = tempfile.mkdtemp()
        zip_ref.extractall(temp_dir)
        upx_exe_found = False
        for root, dirs, files in os.walk(temp_dir):
            if "upx.exe" in files:
                src_upx = os.path.join(root, "upx.exe")
                dest_upx = os.path.join(upx_dir, "upx.exe")
                shutil.move(src_upx, dest_upx)
                upx_exe_found = True
                print(f"Moved upx.exe to {os.path.abspath(dest_upx)}")
                break
        if not upx_exe_found:
            print("upx.exe not found in the downloaded UPX package.")
    shutil.rmtree(temp_dir)
    os.remove(upx_zip)

    # Create a symlink named "upx" pointing to "upx.exe" (Windows-specific workaround)
    symlink_path = os.path.join(upx_dir, "upx")
    exe_path = os.path.join(upx_dir, "upx.exe")
    if os.name == 'nt':
        try:
            if os.path.exists(symlink_path):
                os.remove(symlink_path)
            os.symlink(exe_path, symlink_path)
            print(f"Created symlink: {symlink_path} -> {exe_path}")
        except Exception as e:
            print(f"Could not create symlink due to: {e}. You might need to run as admin or enable Developer Mode.")

# Step 8: Install pyinstaller
def install_pyinstaller():
    subprocess.run(["pip", "install", "pyinstaller"], check=True)

# Step 9: Run pyinstaller with forgeyt.spec and specify UPX directory
def run_pyinstaller(spec_file):
    if os.path.exists(spec_file):
        subprocess.run(["pyinstaller", "--upx-dir", os.path.abspath("./upx"), spec_file], check=True)
    else:
        print(f"{spec_file} not found.")

def main():
    # Install requirements
    install_requirements()

    # Download and extract FFmpeg binaries only if ffmpeg.exe and ffprobe.exe don't exist
    ffmpeg_exe = "./ffmpeg/ffmpeg.exe"
    ffprobe_exe = "./ffmpeg/ffprobe.exe"
    if not (os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe)):
        ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z"
        ffmpeg_archive = "ffmpeg-git-essentials.7z"
        download_ffmpeg(ffmpeg_url, ffmpeg_archive)
        extract_dir = "./ffmpeg"
        os.makedirs(extract_dir, exist_ok=True)
        extract_ffmpeg(ffmpeg_archive, extract_dir)
        move_ffmpeg_binaries(extract_dir)
    else:
        print("FFmpeg binaries already present, skipping download and extraction.")

    # Download and set up UPX for compression only if upx.exe isn't present
    if not os.path.exists("./upx/upx.exe"):
        download_and_extract_upx()
    else:
        print("UPX binary already present, skipping download and extraction.")

    # Install pyinstaller and run with the updated spec file
    install_pyinstaller()
    run_pyinstaller("forgeyt.spec")

if __name__ == "__main__":
    main()
