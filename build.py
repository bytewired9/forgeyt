import os
import subprocess
import urllib.request
import shutil


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
        # PowerShell script to extract using Windows Explorer silently (attempt)
        ps_command = f"""
        $zipFile = '{os.path.abspath(archive_path)}';
        $outFolder = '{os.path.abspath(extract_to)}';
        $shell = New-Object -ComObject Shell.Application;
        $zip = $shell.NameSpace($zipFile);
        $shell.NameSpace($outFolder).CopyHere($zip.Items(), 16);
        Start-Sleep -Seconds 5;
        """
        # Run the PowerShell command
        subprocess.run(["powershell", "-Command", ps_command], check=True)
        print(f"Extracted {archive_path} to {extract_to} using Windows Explorer.")
        return True
    except subprocess.CalledProcessError:
        print("Windows Explorer method failed.")
        return False


# Step 4: If the Explorer method fails, fall back to 7-Zip
def extract_with_7zip(archive_path, extract_to):
    try:
        # Try to use the 7z command line tool to extract
        subprocess.run(["7z", "x", archive_path, f"-o{extract_to}"], check=True)
        print(f"Extracted {archive_path} to {extract_to} using 7-Zip.")
    except FileNotFoundError:
        print("7z command not found. Please install 7-Zip and make sure it's added to your PATH.")
        raise SystemExit(1)


# Step 5: Extract the FFmpeg archive, try Explorer first then fallback to 7-Zip
def extract_ffmpeg(archive_path, extract_to):
    if not extract_with_explorer(archive_path, extract_to):
        print("Falling back to 7-Zip extraction method...")
        extract_with_7zip(archive_path, extract_to)
    os.remove(archive_path)


# Step 6: Move ffmpeg.exe and ffprobe.exe to ./ffmpeg and delete the extracted folder
def move_ffmpeg_binaries(ffmpeg_dir):
    # Detect the folder inside ./ffmpeg (the prone-to-changing folder name)
    folders = [f for f in os.listdir(ffmpeg_dir) if os.path.isdir(os.path.join(ffmpeg_dir, f))]

    if len(folders) != 1:
        print("Error: Unable to detect FFmpeg folder with the binaries.")
        return

    changing_folder = folders[0]
    bin_folder = os.path.join(ffmpeg_dir, changing_folder, "bin")

    if not os.path.exists(bin_folder):
        print(f"Error: bin folder not found in {changing_folder}")
        return

    # Move ffmpeg.exe and ffprobe.exe to ./ffmpeg
    files_to_move = ['ffmpeg.exe', 'ffprobe.exe']
    for file_name in files_to_move:
        src_path = os.path.join(bin_folder, file_name)
        dest_path = os.path.join(ffmpeg_dir, file_name)
        if os.path.exists(src_path):
            shutil.move(src_path, dest_path)
            print(f"Moved {file_name} to {ffmpeg_dir}")
        else:
            print(f"Error: {file_name} not found in {bin_folder}")

    # Delete the changing folder
    shutil.rmtree(os.path.join(ffmpeg_dir, changing_folder))
    print(f"Deleted folder {changing_folder}")


# Step 7: Install pyinstaller
def install_pyinstaller():
    subprocess.run(["pip", "install", "pyinstaller"], check=True)


# Step 8: Run pyinstaller with forgeyt.spec
def run_pyinstaller(spec_file):
    if os.path.exists(spec_file):
        subprocess.run(["pyinstaller", spec_file], check=True)
    else:
        print(f"{spec_file} not found.")


def main():
    # Step 1: Install requirements
    install_requirements()

    # Step 2: Download FFmpeg binaries
    ffmpeg_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z"
    ffmpeg_archive = "ffmpeg-git-essentials.7z"
    download_ffmpeg(ffmpeg_url, ffmpeg_archive)

    # Step 3: Extract FFmpeg to ./ffmpeg
    extract_dir = "./ffmpeg"
    os.makedirs(extract_dir, exist_ok=True)
    extract_ffmpeg(ffmpeg_archive, extract_dir)

    # Step 6: Move binaries and clean up the folder
    move_ffmpeg_binaries(extract_dir)

    # Step 4: Install pyinstaller
    install_pyinstaller()

    # Step 5: Run pyinstaller with forgeyt.spec
    run_pyinstaller("forgeyt.spec")


if __name__ == "__main__":
    main()
