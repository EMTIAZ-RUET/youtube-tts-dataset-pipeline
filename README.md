# YouTube to LJSpeech Dataset (Bangla/Bengali)

Download YouTube videos with Bengali subtitles and create LJSpeech format datasets for TTS fine-tuning.

## ⚠️ IMPORTANT: Cookie Authentication Required

YouTube blocks requests from cloud servers/VPS. You **MUST** provide cookies to make this work.

### Quick Setup (3 Steps):

1. **Install Browser Extension** (on your LOCAL computer):
   - Chrome: Install "Get cookies.txt LOCALLY" extension
   - Firefox: Install "cookies.txt" addon

2. **Export Cookies**:
   - Go to https://www.youtube.com and login
   - Click the extension icon → Export → Save `cookies.txt`
   - Upload `cookies.txt` to the server in this directory

3. **Run the script**:
   ```bash
   python download_youtube_dataset.py "CHANNEL_URL" --cookies cookies.txt --max-videos 3
   ```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
sudo apt-get install ffmpeg

# Get cookie export help
bash export_cookies.sh
```

## Usage

### Method 1: Using Cookie File (RECOMMENDED for cloud servers)

```bash
# After exporting cookies.txt from your browser:
python download_youtube_dataset.py \
    "https://www.youtube.com/@DrMunmunJahan/videos" \
    --cookies cookies.txt \
    --max-videos 5
```

### Method 2: Using Browser Cookies Directly (LOCAL computer only)

```bash
# Only works if you run this on your LOCAL computer with browser
python download_youtube_dataset.py \
    "https://www.youtube.com/@DrMunmunJahan/videos" \
    --cookies-from-browser firefox \
    --max-videos 5
```

## Command Options

```
python download_youtube_dataset.py CHANNEL_URL [OPTIONS]

Required (choose one):
  --cookies FILE              Path to cookies.txt file (RECOMMENDED)
  --cookies-from-browser BR   Browser name: chrome, firefox, etc.

Optional:
  --max-videos N             Download only N videos (default: all)
  --output DIR               Output directory (default: ljspeech_dataset)
  --min-duration SEC         Minimum clip length (default: 1.0)
  --max-duration SEC         Maximum clip length (default: 10.0)
```

## How to Export Cookies

### Option 1: Browser Extension (EASIEST)

**Chrome:**
1. Install: https://chromewebstore.google.com/detail/cclelndahbckbenkjhflpdbgdldlbecc
2. Go to youtube.com and login
3. Click extension → Export
4. Upload cookies.txt to server

**Firefox:**
1. Install: https://addons.mozilla.org/firefox/addon/cookies-txt/
2. Go to youtube.com and login
3. Click extension → Export
4. Upload cookies.txt to server

### Option 2: Command Line (Advanced)

```bash
# On LOCAL computer with browser
yt-dlp --cookies-from-browser firefox --print-to-file cookies cookies.txt "https://www.youtube.com/watch?v=ZvnE04N8INo"

# Upload to server
scp cookies.txt user@server:/path/to/youtube-data-scrolling/
```

## Examples

```bash
# Test with 3 videos using cookies
python download_youtube_dataset.py \
    "https://www.youtube.com/@DrMunmunJahan/videos" \
    --cookies cookies.txt \
    --max-videos 3

# Custom clip duration (2-8 seconds)
python download_youtube_dataset.py \
    "https://www.youtube.com/@DrMunmunJahan/videos" \
    --cookies cookies.txt \
    --min-duration 2.0 \
    --max-duration 8.0 \
    --output bangla_tts

# Download single video
python download_youtube_dataset.py \
    "https://www.youtube.com/watch?v=VIDEO_ID" \
    --cookies cookies.txt

# Verify dataset after download
python verify_dataset.py ljspeech_dataset
```

## Output Structure

```
ljspeech_dataset/
├── wavs/
│   ├── video1_000001.wav  # 22050 Hz mono
│   ├── video1_000002.wav
│   └── ...
├── metadata.csv           # Format: filename|text|text
└── raw/
    ├── video_id.wav       # Original audio
    ├── video_id.bn.json3  # Bengali subtitles
    └── ...
```

## metadata.csv Format

```
video1_000001.wav|আসসালামু আলাইকুম|আসসালামু আলাইকুম
video1_000002.wav|আজকে আমরা কথা বলব|আজকে আমরা কথা বলব
```

Compatible with:
- Coqui TTS
- VITS
- Tacotron 2
- FastSpeech 2
- All LJSpeech-format TTS models

## Troubleshooting

### "Sign in to confirm you're not a bot"

**Problem**: YouTube is blocking requests from cloud servers.

**Solution**: Export cookies from your browser (see above).

### "No subtitles found"

**Problem**: Video doesn't have Bengali subtitles.

**Check**: Open video on YouTube → Click CC button → Check if Bengali/Bangla subtitles exist.

**Solutions**:
1. Choose videos with subtitles
2. The script will try: Bengali → Bengali-India → English (in that order)

### FFmpeg not found

```bash
sudo apt-get install ffmpeg  # Ubuntu/Debian
brew install ffmpeg          # macOS
```

### Cookie file not working

1. Make sure you're logged into YouTube when exporting
2. Export fresh cookies (they expire)
3. Check file path is correct
4. Try different browser

## Security Note

**Keep cookies.txt private!** It contains your YouTube authentication. Don't share it or commit to git.

Add to `.gitignore`:
```
cookies.txt
*.cookies
```

## Requirements

- Python 3.7+
- FFmpeg
- YouTube cookies (from browser)
- Videos must have Bengali subtitles (manual or auto-generated)

## Tips

1. **Always test first**: Start with `--max-videos 3`
2. **Check for subtitles**: Open video on YouTube and check CC button
3. **Optimal clip length**: 2-8 seconds works best for TTS
4. **Storage**: 1 hour of audio ≈ 500 MB - 1 GB
5. **Dataset size**: Aim for 3-10 hours (2000-5000 clips) minimum
6. **Fresh cookies**: Export new cookies if downloads fail

## Files

| File | Purpose |
|------|---------|
| `download_youtube_dataset.py` | Main script - download and create dataset |
| `verify_dataset.py` | Verify dataset quality |
| `export_cookies.sh` | Cookie export help/instructions |
| `requirements.txt` | Python dependencies |
| `COMMANDS.txt` | Quick command reference |

## License

Educational and research use. Respect YouTube's Terms of Service and copyright laws.
