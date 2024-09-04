# forgeyt

[![GitHub all releases](https://img.shields.io/github/downloads/ForgedCore8/forgeyt/total)](https://github.com/ForgedCore8/forgeyt/releases)
[![CodeQL](https://github.com/ForgedCore8/forgeyt/actions/workflows/codeql.yml/badge.svg)](https://github.com/ForgedCore8/forgeyt/actions/workflows/codeql.yml)

## Introduction
`forgeyt` is a user-friendly graphical user interface (GUI) wrapper for `yt-dlp`, making it easier to download videos from YouTube and other video platforms. It simplifies the process of specifying download options and formats, streamlining the user experience.

## Features
- Easy-to-use GUI for `yt-dlp`
- Supports various file formats for downloads
- Streamlined process for copying URLs and starting downloads

## Prerequisites
Before installing `forgeyt`, ensure you have `ffmpeg` and `ffprobe` binaries installed on your system as they are required for the tool to function properly.

## Installation

```bash
pip3 install -r requirements.txt
```

## Usage

To use `forgeyt`, simply copy the video URL into the provided field, select your desired filetype, and click start. The intuitive interface makes it easy to download videos quickly.

## Compiling

To compile `forgeyt`, you just need to type the following command:
```
nuitka --standalone --onefile --windows-icon-from-ico=ForgeYT.ico --include-data-file=About.png=About.png --include-data-file=About_dark.png=About_dark.png --include-data-file=Console.png=Console.png --include-data-file=Console_dark.png=Console_dark.png --include-data-file=download.png=download.png --include-data-file=download_dark.png=download_dark.png --include-data-file=ForgeYT.png=ForgeYT.png --include-data-file=ForgeYT.ico=ForgeYT.ico --include-data-file=Home.png=Home.png --include-data-file=Home_dark.png=Home_dark.png --include-data-file=Settings.png=Settings.png --include-data-file=Settings_dark.png=Settings_dark.png --include-data-file=ffmpeg.exe=ffmpeg.exe --include-data-file=ffprobe.exe=ffprobe.exe --include-data-dir=utils=utils --include-data-dir=app=app --include-data-dir=vars=vars --disable-console forgeyt.py
```

## Contributing

We welcome contributions to `forgeyt`! Here's how you can contribute:

1. **Fork the Repository**: Click the 'Fork' button at the top right of the page to create your own copy of the repository.
2. **Clone the Forked Repository**:
   ```bash
   git clone https://github.com/ForgedCore8/forgeyt.git
   ```
3. **Create a New Branch**:
   ```bash
   git checkout -b [branch-name]
   ```
4. **Make Your Changes** and commit them:
   ```bash
   git commit -m "Add some feature"
   ```
5. **Push to the Branch**:
   ```bash
   git push origin [branch-name]
   ```
6. **Create a Pull Request**: Go to your fork on GitHub and click the 'New pull request' button. Please ensure your pull request describes the proposed changes.

*Note*: A review is required for all contributions. Please follow standard coding conventions and include updates to documentation as needed.

## License

`forgeyt` is distributed under the GNU GPL 3.0 license. See the [LICENSE](https://github.com/bytewired9/forgeyt/blob/main/LICENSE) file for more details.

## Contact

If you encounter any problems or have questions about `forgeyt`, feel free to reach out on Discord: @bytewired9 in [StompZone](https://discord.io/stomp), or create an issue in the [issue tracker](https://github.com/bytewired9/forgeyt/issues).

## Acknowledgments

A big thank you to all the contributors who have helped make `forgeyt` a reality:

<a href = "https://github.com/forgedcore8/forgeyt/graphs/contributors">
  <img src = "https://contrib.rocks/image?repo=forgedcore8/forgeyt"/>
</a>
