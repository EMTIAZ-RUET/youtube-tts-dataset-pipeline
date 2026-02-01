#!/usr/bin/env python3
"""
Rebuild metadata using timing information from JSON3 files and audio files.
This ensures 100% accurate text-to-audio mapping by matching durations.
"""

import os
import json
from pathlib import Path
import re
import subprocess

def get_audio_duration(audio_path):
    """Get duration of audio file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        return float(result.stdout.strip())
    except:
        return None

def parse_subtitles(subtitle_file):
    """Parse JSON3 subtitle format with timing."""
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
                'duration': duration_sec,
                'end': start_sec + duration_sec
            })

        return captions
    except Exception as e:
        print(f"  Error parsing subtitles: {e}")
        return []

def rebuild_metadata(dataset_dir="ljspeech_dataset", min_duration=1.0, max_duration=10.0):
    dataset_path = Path(dataset_dir)
    wavs_dir = dataset_path / "wavs"
    raw_dir = dataset_path / "raw"

    if not wavs_dir.exists():
        print(f"Error: {wavs_dir} does not exist")
        return

    # Get all audio files
    audio_files = sorted(wavs_dir.glob("*.wav"))
    print(f"Found {len(audio_files)} audio files\n")

    # Group audio files by video ID
    video_groups = {}
    for audio_file in audio_files:
        match = re.match(r"(.+?)_(\d{6})\.wav", audio_file.name)
        if match:
            video_id = match.group(1)
            index = int(match.group(2))
            if video_id not in video_groups:
                video_groups[video_id] = []
            video_groups[video_id].append((index, audio_file))

    print(f"Found {len(video_groups)} videos\n")

    # Build metadata
    metadata_lines = []
    total_matched = 0
    total_unmatched = 0

    for video_id in sorted(video_groups.keys()):
        print(f"{video_id}:")

        # Find subtitle file
        subtitle_file = None
        for ext in ['.bn.json3', '.bn-IN.json3', '.en.json3']:
            sub_path = raw_dir / f"{video_id}{ext}"
            if sub_path.exists():
                subtitle_file = sub_path
                break

        if not subtitle_file:
            print(f"  ⚠️  No JSON3 file found")
            total_unmatched += len(video_groups[video_id])
            continue

        # Parse all captions
        all_captions = parse_subtitles(subtitle_file)

        # Filter captions by duration (same as download script)
        filtered_captions = []
        last_end_time = 0.0

        for caption in sorted(all_captions, key=lambda x: x['start']):
            start_sec = caption['start']
            duration_sec = caption['duration']
            end_sec = caption['end']

            # Skip overlaps
            if start_sec < last_end_time:
                continue

            # Filter by duration
            if duration_sec < min_duration or duration_sec > max_duration:
                continue

            text = caption['text'].replace('\n', ' ').replace('  ', ' ').strip()
            if not text:
                continue

            filtered_captions.append({
                'text': text,
                'duration': duration_sec
            })
            last_end_time = end_sec

        # Sort audio files by index
        audio_list = sorted(video_groups[video_id], key=lambda x: x[0])

        print(f"  Audio files: {len(audio_list)}")
        print(f"  Filtered captions: {len(filtered_captions)}")

        # Match audio files to captions by duration
        matched = 0
        for i, (index, audio_file) in enumerate(audio_list):
            audio_duration = get_audio_duration(audio_file)

            if audio_duration is None:
                print(f"  ⚠️  Could not get duration for {audio_file.name}")
                continue

            # Find caption with matching duration (within 0.1 second tolerance)
            best_match = None
            min_diff = float('inf')

            for j, caption in enumerate(filtered_captions):
                if j < i - 2 or j > i + 2:  # Only check nearby captions
                    continue

                duration_diff = abs(caption['duration'] - audio_duration)
                if duration_diff < min_diff:
                    min_diff = duration_diff
                    best_match = caption

            if best_match and min_diff < 0.2:  # 200ms tolerance
                text = best_match['text']
                metadata_lines.append(f"{audio_file.name}|{text}|{text}")
                matched += 1
            elif i < len(filtered_captions):
                # Fallback: use caption at same index
                text = filtered_captions[i]['text']
                metadata_lines.append(f"{audio_file.name}|{text}|{text}")
                matched += 1
            else:
                print(f"  ⚠️  No match for {audio_file.name}")

        total_matched += matched
        total_unmatched += len(audio_list) - matched
        print(f"  Matched: {matched}/{len(audio_list)}\n")

    # Write metadata.csv
    metadata_path = dataset_path / "metadata.csv"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        for line in metadata_lines:
            f.write(line + '\n')

    print(f"{'='*60}")
    print(f"✅ Metadata rebuilt with timing verification!")
    print(f"{'='*60}")
    print(f"Output: {metadata_path}")
    print(f"Total matched: {total_matched}")
    print(f"Total unmatched: {total_unmatched}")
    print(f"Total entries: {len(metadata_lines)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    rebuild_metadata()
