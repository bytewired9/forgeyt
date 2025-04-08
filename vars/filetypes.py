# vars/filetypes.py (or wherever you define this)

filetypes = {
    "mp4": {
        "filetype": "mp4",
        "fileext": "mp4",
        "audio": False,
        "codec": "h264", # Example default codec
        "description": "Standard Video (H.264/AAC common, very compatible)"
    },
    "mp3": {
        "filetype": "mp3",
        "fileext": "mp3",
        "audio": True,
        "codec": "mp3",
        "description": "Popular Lossy Audio (Widely supported)"
    },
    "webm": {
        "filetype": "webm",
        "fileext": "webm",
        "audio": False,
        "codec": "vp9", # Example default codec
        "description": "Open Web Video (VP9/Opus common)"
    },
    "mkv": {
        "filetype": "mkv",
        "fileext": "mkv",
        "audio": False,
        "codec": "h265", # Example default codec (can contain many others)
        "description": "Matroska Video Container (Flexible, multiple streams)"
    },
    "flv": {
        "filetype": "flv",
        "fileext": "flv",
        "audio": False,
        "codec": "h263", # Older codec example
        "description": "Flash Video (Older format, less common now)"
    },
    "avi": {
        "filetype": "avi",
        "fileext": "avi",
        "audio": False,
        "codec": "h264", # Can contain various codecs
        "description": "Audio Video Interleave (Older Windows container)"
    },
    "mov": {
        "filetype": "mov",
        "fileext": "mov",
        "audio": False,
        "codec": "h264", # Common codec
        "description": "Apple QuickTime Video Container"
    },
    "ogg": {
        "filetype": "ogg",
        "fileext": "ogg",
        "audio": True,
        "codec": "vorbis", # Common codec for .ogg audio
        "description": "Ogg Vorbis Audio (Open, lossy format)"
    },
    "aac": {
        "filetype": "aac",
        "fileext": "aac",
        "audio": True,
        "codec": "aac",
        "description": "Advanced Audio Coding (Lossy, common in MP4/M4A)"
    },
    "wav": {
        "filetype": "wav",
        "fileext": "wav",
        "audio": True,
        "codec": "pcm", # Usually uncompressed PCM
        "description": "Waveform Audio (Uncompressed Windows format)"
    },
    "aiff": {
        "filetype": "aiff",
        "fileext": "aiff",
        "audio": True,
        "codec": "pcm", # Usually uncompressed PCM
        "description": "Audio Interchange File Format (Uncompressed Apple format)"
    },
    "flac": {
        "filetype": "flac",
        "fileext": "flac",
        "audio": True,
        "codec": "flac",
        "description": "Free Lossless Audio Codec (Lossless compression)"
    },
    "alac": {
        "filetype": "alac",
        "fileext": "m4a", # ALAC is usually stored in .m4a containers
        "audio": True,
        "codec": "alac",
        "description": "Apple Lossless Audio Codec (Lossless compression)"
    },
    "opus": {
        "filetype": "opus",
        "fileext": "opus",
        "audio": True,
        "codec": "opus",
        "description": "Opus Audio (Modern, efficient lossy codec)"
    },
    "m4a": {
        "filetype": "m4a",
        "fileext": "m4a",
        "audio": True,
        "codec": "aac", # Can also contain ALAC
        "description": "MPEG-4 Audio Container (Usually AAC or ALAC)"
    }
}

# Optional: If this file is vars/filetypes.py and used by vars/__init__.py
__all__ = ['filetypes']