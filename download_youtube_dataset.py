#!/usr/bin/env python3
"""
Download YouTube videos with Bengali subtitles and create LJSpeech format dataset.
Uses yt-dlp with browser cookies to bypass bot detection.
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
        """Get list of video URLs from channel or single video."""
        print(f"Fetching video list from: {channel_url}\n")

        # Check if it's a single video URL
        if 'watch?v=' in channel_url or 'youtu.be/' in channel_url:
            print("Detected single video URL")
            return [channel_url]

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
                    # Single video
                    if 'id' in info:
                        return [f"https://www.youtube.com/watch?v={info['id']}"]
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
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['bn', 'bn-IN', 'en'],
            'subtitlesformat': 'json3',
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
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

        print(f"  ✓ Created {clips_created} non-overlapping clips")
        print(f"  Total clips so far: {self.audio_counter}")

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
        print("   Run: bash export_cookies.sh for help")
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
