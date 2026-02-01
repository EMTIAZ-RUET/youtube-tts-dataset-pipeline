# Complete TTS Dataset Creation Pipeline

**From YouTube to Production-Ready Bengali TTS Dataset**

This guide covers the entire pipeline from downloading YouTube videos to creating a clean, ready-to-use TTS dataset.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Cookie Generation](#step-1-cookie-generation)
3. [Step 2: Download & Sequential Mapping](#step-2-download--sequential-mapping)
4. [Step 3: Background Music Removal (Demucs AI)](#step-3-background-music-removal-demucs-ai)
5. [Step 4: Silence Trimming & Smooth Endings](#step-4-silence-trimming--smooth-endings)
6. [Step 5: Combine Short Clips](#step-5-combine-short-clips)
7. [Step 6: Slow Down Audio (Optional)](#step-6-slow-down-audio-optional)
8. [Complete Pipeline Scripts](#complete-pipeline-script)
9. [Final Dataset](#final-dataset)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Install Required Packages

```bash
# Core dependencies
pip install yt-dlp pydub

# For noise reduction (optional)
pip install noisereduce

# For AI vocal separation (optional)
pip install demucs

# For pitch-preserving slow down (optional)
pip install librosa soundfile

# System requirements
sudo apt-get install ffmpeg  # or brew install ffmpeg on Mac
```

---

## Step 1: Cookie Generation

YouTube may block requests from cloud servers. You need to export cookies from your browser using a browser extension.

### Using Browser Extension

1. **Install Extension:**
   - Chrome: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally)
   - Firefox: [Get cookies.txt LOCALLY](https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/)

2. **Export Cookies:**
   - Go to [youtube.com](https://youtube.com) and login to your account
   - Click the extension icon in your browser toolbar
   - Click "Export" or "Copy" to get the cookies
   - Save the cookies as `youtube_cookies.txt` in your project directory

3. **Verify File:**
   - Make sure the file is named exactly `youtube_cookies.txt`
   - File should be in the same directory as your scripts
   - File should contain Netscape cookie format

**Important:** Keep your cookies file private and don't share it.

---

## Step 2: Download & Sequential Mapping

This step downloads YouTube videos and creates sequential, non-overlapping audio segments with accurate text mapping.

### Code: `download_youtube_dataset.py`

<details>
<summary>Click to see full code</summary>

```python
#!/usr/bin/env python3
"""
Download YouTube videos with Bengali subtitles and create LJSpeech format dataset.
Uses sequential segmentation: start of subtitle to start of NEXT subtitle.
"""

import os
import sys
import json
from pathlib import Path
import argparse

try:
    import yt_dlp
    from pydub import AudioSegment
except ImportError:
    print("Error: Missing required packages")
    print("Run: pip install yt-dlp pydub")
    sys.exit(1)


class YouTubeDatasetCreator:
    def __init__(self, output_dir="ljspeech_dataset", max_videos=None,
                 min_duration=1.0, max_duration=10.0, cookie_browser=None, cookie_file=None):
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "raw"
        self.wavs_dir = self.output_dir / "wavs"
        self.max_videos = max_videos
        self.min_duration = min_duration
        self.max_duration = max_duration
        self.cookie_browser = cookie_browser
        self.cookie_file = cookie_file

        # Create directories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.wavs_dir.mkdir(parents=True, exist_ok=True)

        self.metadata = []
        self.audio_counter = 0

    def get_video_id(self, url):
        """Extract video ID from YouTube URL."""
        if 'v=' in url:
            return url.split('v=')[-1].split('&')[0]
        elif 'youtu.be/' in url:
            return url.split('youtu.be/')[-1].split('?')[0]
        return None

    def download_channel_videos(self, channel_url):
        """Get list of video URLs from channel."""
        print(f"Fetching video list from: {channel_url}\n")

        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'no_warnings': True,
        }

        if self.cookie_browser:
            ydl_opts['cookiesfrombrowser'] = (self.cookie_browser,)
        elif self.cookie_file:
            ydl_opts['cookiefile'] = self.cookie_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)

                if 'entries' not in info:
                    print("Error: Could not fetch videos")
                    return []

                video_urls = []
                for entry in info['entries']:
                    if entry and 'id' in entry:
                        video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
                        if self.max_videos and len(video_urls) >= self.max_videos:
                            break

                print(f"Found {len(video_urls)} videos to process\n")
                return video_urls
        except Exception as e:
            print(f"Error fetching videos: {e}")
            return []

    def download_with_subtitles(self, video_url, video_id):
        """Download audio and subtitles using yt-dlp."""
        print(f"  Downloading audio and subtitles...")

        output_template = str(self.raw_dir / video_id)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['bn', 'bn-IN', 'en'],
            'subtitlesformat': 'json3',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
        }

        if self.cookie_browser:
            ydl_opts['cookiesfrombrowser'] = (self.cookie_browser,)
        elif self.cookie_file:
            ydl_opts['cookiefile'] = self.cookie_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            return True
        except Exception as e:
            print(f"  Error: {e}")
            return False

    def parse_subtitles(self, subtitle_file):
        """Parse JSON3 subtitle format."""
        try:
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            captions = []
            for event in data.get('events', []):
                if 'segs' not in event:
                    continue

                text = ''.join(seg.get('utf8', '') for seg in event['segs'])
                text = text.strip()

                if not text:
                    continue

                start_sec = event.get('tStartMs', 0) / 1000.0
                duration_ms = event.get('dDurationMs', 0)
                duration_sec = duration_ms / 1000.0

                captions.append({
                    'text': text,
                    'start': start_sec,
                    'duration': duration_sec
                })

            return captions
        except Exception as e:
            print(f"  Error parsing subtitles: {e}")
            return []

    def segment_audio(self, audio_path, captions, video_id):
        """
        Create sequential, non-overlapping segments.
        Uses subtitle START as segment start, and NEXT subtitle START as segment end.
        This handles YouTube's rolling/overlapping subtitle display correctly.
        """
        print(f"  Segmenting audio into clips...")

        try:
            audio = AudioSegment.from_wav(str(audio_path))
        except Exception as e:
            print(f"  Error loading audio: {e}")
            return 0

        # Sort captions by start time
        sorted_captions = sorted(captions, key=lambda x: x['start'])

        clips_created = 0

        # Save detailed timing information
        timing_file = self.output_dir / f"{video_id}_timing_info.txt"
        with open(timing_file, 'w', encoding='utf-8') as tf:
            tf.write("filename|text|start_time|end_time|duration\n")

        # Process each subtitle, using next subtitle's start as the end
        for i, caption in enumerate(sorted_captions):
            text = caption['text'].replace('\n', ' ').replace('  ', ' ').strip()
            if not text:
                continue

            start_sec = caption['start']

            # Determine end time: use next subtitle's start
            if i < len(sorted_captions) - 1:
                next_start = sorted_captions[i + 1]['start']
                # But don't let segments be too long
                max_end = start_sec + self.max_duration
                end_sec = min(next_start, max_end)
            else:
                # Last subtitle - use its duration or max duration
                end_sec = min(start_sec + caption['duration'],
                            start_sec + self.max_duration)

            duration_sec = end_sec - start_sec

            # Filter by duration
            if duration_sec < self.min_duration or duration_sec > self.max_duration:
                continue

            # Extract segment
            start_ms = int(start_sec * 1000)
            end_ms = int(end_sec * 1000)

            # Ensure we don't go beyond audio length
            if end_ms > len(audio):
                end_ms = len(audio)
                duration_sec = (end_ms - start_ms) / 1000.0

            # Safety check
            if start_ms >= end_ms or start_ms < 0:
                continue

            try:
                audio_segment = audio[start_ms:end_ms]
            except Exception as e:
                print(f"  Warning: Could not extract segment at {start_sec}s: {e}")
                continue

            # Generate filename
            filename = f"{video_id}_{self.audio_counter:06d}.wav"
            output_path = self.wavs_dir / filename

            # Export as 22050 Hz mono
            audio_segment = audio_segment.set_frame_rate(22050).set_channels(1)
            audio_segment.export(str(output_path), format="wav")

            # Add to metadata
            self.metadata.append(f"{filename}|{text}|{text}")

            # Save mapping with original text for verification
            mapping_file = self.output_dir / f"{video_id}_audio_mapping.txt"
            with open(mapping_file, 'a', encoding='utf-8') as mf:
                mf.write(f"{filename}|{text}\n")

            # Save detailed timing info
            with open(timing_file, 'a', encoding='utf-8') as tf:
                tf.write(f"{filename}|{text}|{start_sec:.3f}|{end_sec:.3f}|{duration_sec:.3f}\n")

            self.audio_counter += 1
            clips_created += 1

        print(f"  ✓ Created {clips_created} sequential, non-overlapping clips")
        print(f"  ✓ Saved timing information to {timing_file.name}")
        return clips_created

    def process_video(self, video_url, video_index):
        """Process single video."""
        print(f"\n{'='*60}")
        print(f"[{video_index}] Processing: {video_url}")
        print(f"{'='*60}")

        video_id = self.get_video_id(video_url)
        if not video_id:
            print(f"  ❌ Could not extract video ID")
            return False

        # Check if already processed
        transcript_path = self.output_dir / f"{video_id}_transcript.txt"
        if transcript_path.exists():
            print(f"  ⏭️  Already processed, skipping...")
            return False

        # Download
        if not self.download_with_subtitles(video_url, video_id):
            print(f"  ❌ Download failed")
            return False

        # Find subtitle file
        subtitle_file = None
        for ext in ['.bn.json3', '.bn-IN.json3', '.en.json3']:
            sub_path = self.raw_dir / f"{video_id}{ext}"
            if sub_path.exists():
                subtitle_file = sub_path
                lang = ext.split('.')[1]
                print(f"  ✓ Found {lang} subtitles")
                break

        if not subtitle_file:
            print(f"  ❌ No subtitles found")
            return False

        # Parse subtitles
        captions = self.parse_subtitles(subtitle_file)
        if not captions:
            print(f"  ❌ Could not parse subtitles")
            return False

        print(f"  ✓ Parsed {len(captions)} subtitle segments")

        # Save full transcript
        transcript_path = self.output_dir / f"{video_id}_transcript.txt"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            for caption in captions:
                f.write(f"{caption['text']}\n")
        print(f"  ✓ Saved transcript to {transcript_path.name}")

        # Check audio file
        audio_path = self.raw_dir / f"{video_id}.wav"
        if not audio_path.exists():
            print(f"  ❌ Audio file not found")
            return False

        # Segment
        clips_created = self.segment_audio(audio_path, captions, video_id)

        print(f"  ✓ Total clips so far: {self.audio_counter}")

        return clips_created > 0

    def save_metadata(self):
        """Save metadata.csv."""
        if not self.metadata:
            print("\n⚠️  No clips created - no metadata to save")
            return

        metadata_path = self.output_dir / "metadata.csv"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            for line in self.metadata:
                f.write(line + '\n')

        print(f"\n{'='*60}")
        print("✅ DATASET CREATION COMPLETE!")
        print(f"{'='*60}")
        print(f"Output directory: {self.output_dir}")
        print(f"Audio clips: {self.wavs_dir}")
        print(f"Metadata: {metadata_path}")
        print(f"Total clips: {len(self.metadata)}")
        print(f"{'='*60}")

    def process_channel(self, channel_url):
        """Process entire channel."""
        video_urls = self.download_channel_videos(channel_url)

        if not video_urls:
            print("No videos to process")
            return

        successful = 0
        failed = 0

        for idx, video_url in enumerate(video_urls, 1):
            try:
                if self.process_video(video_url, idx):
                    successful += 1
                else:
                    failed += 1
                # Add delay between videos to avoid rate limiting
                import time
                time.sleep(3)
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed += 1

        self.save_metadata()

        print(f"\nProcessed: {successful} successful, {failed} failed")


def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube videos with subtitles and create LJSpeech dataset"
    )
    parser.add_argument("url", help="YouTube channel or video URL")
    parser.add_argument("--output", "-o", default="ljspeech_dataset",
                        help="Output directory (default: ljspeech_dataset)")
    parser.add_argument("--max-videos", "-n", type=int, default=None,
                        help="Maximum number of videos to process")
    parser.add_argument("--min-duration", type=float, default=1.0,
                        help="Minimum clip duration in seconds (default: 1.0)")
    parser.add_argument("--max-duration", type=float, default=10.0,
                        help="Maximum clip duration in seconds (default: 10.0)")
    parser.add_argument("--cookies-from-browser", "-c",
                        choices=['chrome', 'firefox', 'brave', 'edge', 'safari', 'chromium'],
                        help="Browser to extract cookies from")
    parser.add_argument("--cookies", "-C",
                        help="Path to cookies.txt file")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("YouTube to LJSpeech Dataset Creator")
    print("="*60 + "\n")

    if args.cookies_from_browser:
        print(f"Using cookies from browser: {args.cookies_from_browser}")
    elif args.cookies:
        print(f"Using cookies from file: {args.cookies}")
    else:
        print("⚠️  WARNING: No cookies specified!")
        print("   YouTube may block requests from cloud servers.")
        print("   Use --cookies cookies.txt or --cookies-from-browser firefox")
    print()

    creator = YouTubeDatasetCreator(
        output_dir=args.output,
        max_videos=args.max_videos,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        cookie_browser=args.cookies_from_browser,
        cookie_file=args.cookies
    )

    creator.process_channel(args.url)


if __name__ == "__main__":
    main()
```

</details>

### Usage

```bash
# Download from YouTube channel with cookies
python download_youtube_dataset.py \
    "https://www.youtube.com/@YourChannel/videos" \
    --cookies youtube_cookies.txt \
    --max-videos 5 \
    --min-duration 1.0 \
    --max-duration 10.0
```

**Output:**
- `ljspeech_dataset/wavs/` - Audio files
- `ljspeech_dataset/metadata.csv` - Text mappings
- `ljspeech_dataset/raw/` - Original downloads

---

## Step 3: Background Music Removal (Demucs AI)

Remove background music using AI-based vocal separation. Demucs uses deep learning to separate vocals from all background sounds including music, providing the highest quality results.

### Code: `separate_vocals_demucs.py`

<details>
<summary>Click to see full code</summary>

```python
#!/usr/bin/env python3
"""
Separate vocals from background music using Demucs AI model.
This is the most effective method for removing background music.
"""
import os
import sys
import shutil
from pathlib import Path
import subprocess

def separate_vocals_batch(input_dir, output_dir, model="htdemucs"):
    """
    Use Demucs to separate vocals from music for all files in a directory.

    Args:
        input_dir: Directory containing audio files
        output_dir: Directory to save separated vocals
        model: Demucs model to use (htdemucs is best quality)
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(input_dir.glob("*.wav"))
    total = len(wav_files)

    print(f"Found {total} audio files to process")
    print(f"Model: {model}")
    print(f"This will take some time (1-2 min per file)...\n")

    temp_dir = Path("demucs_temp")
    successful = 0
    failed = 0

    for i, wav_file in enumerate(wav_files, 1):
        print(f"[{i}/{total}] Processing: {wav_file.name}")

        try:
            # Run Demucs separation
            cmd = [
                "demucs",
                "--two-stems=vocals",  # Only separate vocals
                "-n", model,
                "-o", str(temp_dir),
                str(wav_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                print(f"  ❌ Failed: {result.stderr}")
                failed += 1
                continue

            # Find the output vocals file
            vocals_file = temp_dir / model / wav_file.stem / "vocals.wav"

            if vocals_file.exists():
                shutil.copy(vocals_file, output_dir / wav_file.name)
                print(f"  ✓ Success")
                successful += 1
            else:
                print(f"  ❌ Vocals file not found")
                failed += 1

        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout (>120s)")
            failed += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1

        # Clean up temp files for this clip
        if (temp_dir / model / wav_file.stem).exists():
            shutil.rmtree(temp_dir / model / wav_file.stem)

    # Clean up temp directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}")

    return successful, failed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Separate vocals from background music using Demucs AI"
    )
    parser.add_argument("--input", "-i", default="ljspeech_dataset/wavs",
                       help="Input directory")
    parser.add_argument("--output", "-o", default="ljspeech_dataset/wavs_vocals",
                       help="Output directory")
    parser.add_argument("--model", "-m", default="htdemucs",
                       choices=["htdemucs", "htdemucs_ft", "mdx_extra"],
                       help="Demucs model (htdemucs is best)")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Demucs Vocal Separation Tool")
    print("="*60)
    print("This uses AI to separate vocals from music")
    print("First run will download the model (~300MB)")
    print("="*60 + "\n")

    separate_vocals_batch(args.input, args.output, args.model)
```

</details>

### Usage

```bash
# Install Demucs
pip install demucs

# Separate vocals from audio files
python separate_vocals_demucs.py \
    --input ljspeech_dataset/wavs \
    --output ljspeech_dataset/wavs_vocals \
    --model htdemucs
```

**Processing Time:** 1-2 minutes per file. For 188 files, expect 3-6 hours.

**Output:** Clean vocal-only audio files with background music completely removed.

---

## Step 4: Silence Trimming & Smooth Endings

Trim silence and add smooth fade-out.

### Code: `trim_silence_and_clean_audio.py`

<details>
<summary>Click to see full code</summary>

```python
#!/usr/bin/env python3
"""
Process audio: trim silence, add smooth endings.
"""
import os
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import detect_leading_silence


def trim_silence(audio_segment, silence_threshold=-50.0, chunk_size=10,
                 add_fade_in=False, add_fade_out=True, fade_duration=100):
    """Trim silence and add fades for smooth transitions."""
    # Detect leading silence
    start_trim = detect_leading_silence(audio_segment, silence_threshold=silence_threshold, chunk_size=chunk_size)

    # Detect trailing silence
    end_trim = detect_leading_silence(audio_segment.reverse(), silence_threshold=silence_threshold, chunk_size=chunk_size)

    # Trim
    duration = len(audio_segment)
    trimmed = audio_segment[start_trim:duration-end_trim]

    # Apply fades
    if add_fade_in and len(trimmed) > fade_duration:
        trimmed = trimmed.fade_in(duration=fade_duration)

    if add_fade_out and len(trimmed) > fade_duration:
        trimmed = trimmed.fade_out(duration=fade_duration)

    return trimmed, start_trim, end_trim


def process_audio_file(input_path, output_path, trim_silence_enabled=True,
                       add_fade_out=True, fade_duration=100):
    """Process single audio file."""
    try:
        # Load audio
        audio = AudioSegment.from_wav(str(input_path))

        # Trim silence and add fade
        if trim_silence_enabled:
            audio, start_trim, end_trim = trim_silence(
                audio,
                add_fade_out=add_fade_out,
                fade_duration=fade_duration
            )

        # Export
        audio.export(str(output_path), format="wav")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def process_dataset(input_dir, output_dir):
    """Process all files in directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(input_dir.glob("*.wav"))

    for i, wav_file in enumerate(wav_files, 1):
        if i % 50 == 0 or i == 1:
            print(f"Processing {i}/{len(wav_files)}: {wav_file.name}")

        output_path = output_dir / wav_file.name
        process_audio_file(wav_file, output_path)

    print(f"\n✓ Processed {len(wav_files)} files")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default="ljspeech_dataset/wavs_vocals")
    parser.add_argument("--output", "-o", default="ljspeech_dataset/wavs_smooth")
    args = parser.parse_args()

    process_dataset(args.input, args.output)
```

</details>

### Usage

```bash
# Process Demucs-separated vocals
python trim_silence_and_clean_audio.py \
    --input ljspeech_dataset/wavs_vocals \
    --output ljspeech_dataset/wavs_smooth
```

---

## Step 5: Combine Short Clips

Combine 3 consecutive clips into longer segments.

### Code: `combine_audio_clips.py`

<details>
<summary>Click to see full code</summary>

```python
#!/usr/bin/env python3
"""
Combine multiple short clips into longer segments.
"""
from pathlib import Path
from pydub import AudioSegment


def load_metadata(metadata_file):
    """Load metadata from CSV."""
    metadata = []
    with open(metadata_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 2:
                metadata.append({'filename': parts[0], 'text': parts[1]})
    return metadata


def combine_clips(input_dir, output_dir, metadata, clips_per_segment=3, pause_ms=100):
    """Combine clips into longer segments."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    silence = AudioSegment.silent(duration=pause_ms)
    new_metadata = []
    combined_count = 0
    i = 0

    while i < len(metadata):
        combined_audio = None
        combined_text = []
        clips_in_segment = 0

        # Combine up to N clips
        while i < len(metadata) and clips_in_segment < clips_per_segment:
            clip_info = metadata[i]
            audio_path = input_dir / clip_info['filename']

            if audio_path.exists():
                audio = AudioSegment.from_wav(str(audio_path))

                if combined_audio is None:
                    combined_audio = audio
                else:
                    combined_audio = combined_audio + silence + audio

                combined_text.append(clip_info['text'])
                clips_in_segment += 1

            i += 1

        # Save combined clip
        if combined_audio:
            video_id = metadata[0]['filename'].split('_')[0]
            output_filename = f"{video_id}_combined_{combined_count:06d}.wav"
            output_path = output_dir / output_filename

            combined_audio.export(str(output_path), format="wav")

            new_metadata.append({
                'filename': output_filename,
                'text': ' '.join(combined_text)
            })

            combined_count += 1

            if combined_count % 50 == 0:
                print(f"Created {combined_count} segments...")

    print(f"\n✓ Created {combined_count} combined segments")
    return new_metadata


def save_metadata(metadata, output_file):
    """Save metadata to CSV."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in metadata:
            f.write(f"{item['filename']}|{item['text']}|{item['text']}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default="ljspeech_dataset/wavs_smooth")
    parser.add_argument("--output", "-o", default="ljspeech_dataset/wavs_combined")
    parser.add_argument("--metadata", "-m", default="ljspeech_dataset/metadata.csv")
    parser.add_argument("--clips", "-n", type=int, default=3)
    args = parser.parse_args()

    # Load metadata
    metadata = load_metadata(args.metadata)

    # Combine clips
    new_metadata = combine_clips(args.input, args.output, metadata, clips_per_segment=args.clips)

    # Save new metadata
    output_metadata = Path(args.output).parent / "metadata_combined.csv"
    save_metadata(new_metadata, output_metadata)

    print(f"✓ Saved metadata to {output_metadata}")
```

</details>

### Usage

```bash
python combine_audio_clips.py \
    --input ljspeech_dataset/wavs_smooth \
    --output ljspeech_dataset/wavs_combined \
    --metadata ljspeech_dataset/metadata.csv \
    --clips 3
```

---

## Step 6: Slow Down Audio (Optional)

Slow down audio while preserving voice pitch.

### Code: `slow_audio_preserve_pitch.py`

<details>
<summary>Click to see full code</summary>

```python
#!/usr/bin/env python3
"""
Slow down audio while preserving pitch using librosa.
"""
from pathlib import Path
import librosa
import soundfile as sf


def slow_audio(input_path, output_path, speed_factor=0.9):
    """
    Slow down audio while preserving pitch.
    speed_factor: 0.9 = 10% slower, 0.85 = 15% slower
    """
    # Load audio
    y, sr = librosa.load(input_path, sr=None)

    # Time stretch (preserves pitch)
    y_stretched = librosa.effects.time_stretch(y, rate=speed_factor)

    # Save
    sf.write(output_path, y_stretched, sr, subtype='PCM_16')


def process_dataset(input_dir, output_dir, speed_factor=0.9):
    """Process all files."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(input_dir.glob("*.wav"))

    for i, wav_file in enumerate(wav_files, 1):
        if i % 20 == 0 or i == 1:
            print(f"Processing {i}/{len(wav_files)}: {wav_file.name}")

        output_path = output_dir / wav_file.name
        slow_audio(wav_file, output_path, speed_factor)

    print(f"\n✓ Processed {len(wav_files)} files")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default="ljspeech_dataset/wavs_combined")
    parser.add_argument("--output", "-o", default="ljspeech_dataset/wavs_natural_slow")
    parser.add_argument("--speed", "-s", type=float, default=0.9)
    args = parser.parse_args()

    process_dataset(args.input, args.output, args.speed)
```

</details>

### Usage

```bash
# 10% slower
python slow_audio_preserve_pitch.py \
    --input ljspeech_dataset/wavs_combined \
    --output ljspeech_dataset/wavs_natural_slow \
    --speed 0.9
```

---

## Complete Pipeline Script

Run all steps sequentially:

```bash
#!/bin/bash
# complete_pipeline.sh

echo "=== Step 1: Download from YouTube ==="
python download_youtube_dataset.py \
    "https://www.youtube.com/@YourChannel/videos" \
    --cookies youtube_cookies.txt \
    --max-videos 5

echo ""
echo "=== Step 2: AI Vocal Separation (Demucs) ==="
python separate_vocals_demucs.py \
    --input ljspeech_dataset/wavs \
    --output ljspeech_dataset/wavs_vocals \
    --model htdemucs

echo ""
echo "=== Step 3: Silence Trimming & Smooth Endings ==="
python trim_silence_and_clean_audio.py \
    --input ljspeech_dataset/wavs_vocals \
    --output ljspeech_dataset/wavs_smooth

echo ""
echo "=== Step 4: Combine Short Clips ==="
python combine_audio_clips.py \
    --input ljspeech_dataset/wavs_smooth \
    --output ljspeech_dataset/wavs_combined \
    --metadata ljspeech_dataset/metadata.csv \
    --clips 3

echo ""
echo "=== Step 5: Slow Down Audio (Optional) ==="
python slow_audio_preserve_pitch.py \
    --input ljspeech_dataset/wavs_combined \
    --output ljspeech_dataset/wavs_natural_slow \
    --speed 0.9

echo ""
echo "=== Copy metadata ==="
cp ljspeech_dataset/metadata_combined.csv ljspeech_dataset/metadata_final.csv

echo ""
echo "✅ Pipeline Complete!"
echo "Final dataset: ljspeech_dataset/wavs_natural_slow/"
echo "Metadata: ljspeech_dataset/metadata_final.csv"
```

---

## Final Dataset

### Structure

```
ljspeech_dataset/
├── wavs_natural_slow/          # ✅ Final audio (use this)
│   ├── video_combined_000000.wav
│   ├── video_combined_000001.wav
│   └── ...
├── metadata_final.csv          # ✅ Final metadata (use this)
├── wavs/                       # Original short clips
├── wavs_smooth/                # Cleaned short clips
├── wavs_combined/              # Combined clips (normal speed)
└── raw/                        # Original YouTube downloads
```

### Dataset Properties

- **Format:** WAV, 22050 Hz, Mono
- **Duration:** 6-9 seconds per clip
- **Language:** Bengali
- **Quality:**
  - ✅ Background music removed
  - ✅ Silence trimmed
  - ✅ Smooth fade-out
  - ✅ Natural speaking pace
  - ✅ Sequential text mapping

### Usage in Training

```python
import pandas as pd
from pathlib import Path

# Load metadata
metadata = pd.read_csv(
    'ljspeech_dataset/metadata_final.csv',
    sep='|',
    names=['filename', 'text', 'normalized_text']
)

# Audio directory
audio_dir = Path('ljspeech_dataset/wavs_natural_slow')

# Example: Load first sample
audio_file = audio_dir / metadata.iloc[0]['filename']
text = metadata.iloc[0]['text']

print(f"Audio: {audio_file}")
print(f"Text: {text}")
```

---

## Troubleshooting

### YouTube Download Fails
- Refresh cookies: Re-export from browser
- Try different cookie format: Browser vs file
- Check internet connection

### Audio Quality Issues
- **Demucs processing errors:** Ensure you have enough disk space and RAM
- **Adjust silence threshold:** Default -50 dBFS, increase for more aggressive trimming
- **Fade duration too long/short:** Adjust `fade_duration` parameter (default 100ms)

### Speed Issues
- **Demucs too slow:** Processing takes 1-2 min/file, plan accordingly
- **Skip optional steps:** Don't slow down audio if not needed
- **Process in batches:** Use `--max-videos` parameter for testing

---

## Summary

This pipeline creates production-ready TTS datasets from YouTube videos with:

1. ✅ Sequential audio segmentation (accurate text mapping)
2. ✅ AI-based background music removal (Demucs)
3. ✅ Silence trimming
4. ✅ Smooth fade-out endings
5. ✅ Combined longer segments (3 clips per segment)
6. ✅ Natural speaking pace (pitch-preserved slowdown)
7. ✅ LJSpeech-compatible format

**Processing Time:**
- **Download & Segmentation:** 10-20 minutes for 5 videos
- **Demucs Vocal Separation:** 1-2 min/file (3-6 hours for 188 files)
- **Silence Trimming & Combining:** 5-10 minutes
- **Pitch-Preserved Slowdown:** 10-15 minutes
- **Total:** ~4-7 hours for complete pipeline

**Key Features:**
- **Demucs AI:** Highest quality vocal separation, removes all background music and noise
- **Sequential Mapping:** Accurate audio-text alignment (no overlaps)
- **Smooth Audio:** 100ms fade-out for natural endings
- **Optimal Length:** 6-9 second clips (ideal for TTS training)

**Ready for:** TTS model training (Tacotron, FastSpeech, VITS, Coqui TTS, etc.)
