# vars/filetypes.py (or wherever you define this)

filetypes = {
    "mp4": {
        "filetype": "mp4",
        "fileext": "mp4",
        "audio": False, # Indicates it's primarily video, might contain audio
        "codec": "h264", # Default video codec
        "audio_codec": "aac", # Default audio codec
        "description": "Standard Video (H.264/AAC common, very compatible)"
    },
    "mp3": {
        "filetype": "mp3",
        "fileext": "mp3",
        "audio": True,
        "codec": "mp3", # Audio codec is the main codec
        "audio_codec": "mp3",
        "description": "Popular Lossy Audio (Widely supported)"
    },
    "webm": {
        "filetype": "webm",
        "fileext": "webm",
        "audio": False,
        "codec": "vp9", # Default video codec
        "audio_codec": "opus", # Default audio codec
        "description": "Open Web Video (VP9/Opus common)"
    },
    "mkv": {
        "filetype": "mkv",
        "fileext": "mkv",
        "audio": False,
        "codec": "h264", # Flexible container, h264 is a safe default
        "audio_codec": "aac", # AAC is common, but MKV is flexible
        "description": "Matroska Video Container (Flexible, multiple streams)"
    },
    "flv": {
        "filetype": "flv",
        "fileext": "flv",
        "audio": False,
        "codec": "h264", # H.264 is common in modern FLV, though H.263 was original
        "audio_codec": "aac", # AAC is also common in modern FLV
        "description": "Flash Video (Older format, less common now)"
    },
    "avi": {
        "filetype": "avi",
        "fileext": "avi",
        "audio": False,
        "codec": "h264", # Can contain various codecs, h264 is a modern choice
        "audio_codec": "mp3", # MP3 was common in AVI
        "description": "Audio Video Interleave (Older Windows container)"
    },
    "mov": {
        "filetype": "mov",
        "fileext": "mov",
        "audio": False,
        "codec": "h264", # Common video codec
        "audio_codec": "aac", # Common audio codec
        "description": "Apple QuickTime Video Container"
    },
    "ogg": {
        "filetype": "ogg",
        "fileext": "ogg", # Usually audio, but can be video (Theora)
        "audio": True, # Primarily used for audio
        "codec": "vorbis", # Main audio codec
        "audio_codec": "vorbis",
        "description": "Ogg Vorbis Audio (Open, lossy format)"
    },
    "aac": {
        "filetype": "aac",
        "fileext": "aac", # Raw AAC stream
        "audio": True,
        "codec": "aac",
        "audio_codec": "aac",
        "description": "Advanced Audio Coding (Lossy, common in MP4/M4A)"
    },
    "wav": {
        "filetype": "wav",
        "fileext": "wav",
        "audio": True,
        "codec": "pcm_s16le", # Default PCM format (signed 16-bit little-endian)
        "audio_codec": "pcm_s16le",
        "description": "Waveform Audio (Uncompressed Windows format)"
    },
    "aiff": {
        "filetype": "aiff",
        "fileext": "aiff",
        "audio": True,
        "codec": "pcm_s16be", # Default PCM format (signed 16-bit big-endian)
        "audio_codec": "pcm_s16be",
        "description": "Audio Interchange File Format (Uncompressed Apple format)"
    },
    "flac": {
        "filetype": "flac",
        "fileext": "flac",
        "audio": True,
        "codec": "flac",
        "audio_codec": "flac",
        "description": "Free Lossless Audio Codec (Lossless compression)"
    },
    "alac": {
        "filetype": "alac",
        "fileext": "m4a", # ALAC is usually stored in .m4a containers
        "audio": True,
        "codec": "alac",
        "audio_codec": "alac",
        "description": "Apple Lossless Audio Codec (Lossless compression)"
    },
    "opus": {
        "filetype": "opus",
        "fileext": "opus",
        "audio": True,
        "codec": "opus",
        "audio_codec": "opus",
        "description": "Opus Audio (Modern, efficient lossy codec)"
    },
    "m4a": {
        "filetype": "m4a",
        "fileext": "m4a",
        "audio": True,
        "codec": "aac", # Can also contain ALAC, but AAC is more common default
        "audio_codec": "aac",
        "description": "MPEG-4 Audio Container (Usually AAC or ALAC)"
    }
}

video_codecs_list = [
    "Auto",  # Let yt-dlp/ffmpeg decide based on format/quality
    "copy",  # Do not re-encode video stream
    "h264",  # AVC (Advanced Video Coding) - Very common, compatible
    "h265",  # HEVC (High Efficiency Video Coding) - More efficient, newer
    "vp9",   # Google's open codec, common in WebM
    "av1",   # Newest open, royalty-free codec, very efficient
    "mpeg4" # Older but still used standard
]

audio_codecs_list = [
    "Auto",      # Let yt-dlp/ffmpeg decide
    "copy",      # Do not re-encode audio stream
    "aac",       # Advanced Audio Coding - Common default for MP4/M4A/MOV
    "mp3",       # MPEG Audio Layer III - Very widely supported lossy
    "opus",      # Modern, efficient lossy codec, common in WebM
    "vorbis",    # Open lossy codec, common in Ogg
    "flac",      # Free Lossless Audio Codec
    "alac",      # Apple Lossless Audio Codec
    "pcm_s16le", # Uncompressed PCM (WAV default) - Signed 16-bit Little Endian
    "pcm_s16be", # Uncompressed PCM (AIFF default) - Signed 16-bit Big Endian
    "ac3"        # Dolby Digital, common in surround sound
]

# Optional: If this file is vars/filetypes.py and used by vars/__init__.py
__all__ = ['filetypes', 'video_codecs_list', 'audio_codecs_list']