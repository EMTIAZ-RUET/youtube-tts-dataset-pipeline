#!/usr/bin/env python3
"""
Final fix: Rebuild metadata by properly parsing JSON3 files
and combining subtitle segments that belong together.
"""

import os
import json
from pathlib import Path
import re

def parse_subtitles_with_newlines(subtitle_file):
    """Parse JSON3 and keep track of segments with newlines to combine properly."""
    try:
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        captions = []
        current_text_parts = []
        current_start = None
        current_end = None

        for event in data.get('events', []):
            if 'segs' not in event:
                continue

            # Extract text from this event
            text = ''.join(seg.get('utf8', '') for seg in event['segs'])

            # Check if this is a newline append event
            is_newline = event.get('aAppend') == 1 and text.strip() == ''

            if is_newline and current_text_parts:
                # This is a continuation marker, keep accumulating
                continue

            # Get timing
            start_sec = event.get('tStartMs', 0) / 1000.0
            duration_ms = event.get('dDurationMs', 0)
            duration_sec = duration_ms / 1000.0
            end_sec = start_sec + duration_sec

            # If we have accumulated text and this is a new segment, save the previous one
            if current_text_parts and not is_newline:
                combined_text = ' '.join(current_text_parts).replace('\n', ' ').replace('  ', ' ').strip()
                if combined_text:
                    captions.append({
                        'text': combined_text,
                        'start': current_start,
                        'duration': current_end - current_start
                    })
                current_text_parts = []

            # Start new accumulation
            if text.strip():
                if not current_text_parts:
                    current_start = start_sec
                current_text_parts.append(text.strip())
                current_end = end_sec

        # Don't forget the last accumulated segment
        if current_text_parts:
            combined_text = ' '.join(current_text_parts).replace('\n', ' ').replace('  ', ' ').strip()
            if combined_text:
                captions.append({
                    'text': combined_text,
                    'start': current_start,
                    'duration': current_end - current_start
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
            video_groups[video_id].append((index, audio_file.name))

    print(f"Found {len(video_groups)} videos\n")

    # Build metadata
    metadata_lines = []
    total_matched = 0

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
            continue

        # Parse captions with proper newline handling
        all_captions = parse_subtitles_with_newlines(subtitle_file)

        # Filter by duration and overlaps
        filtered_captions = []
        last_end_time = 0.0

        for caption in sorted(all_captions, key=lambda x: x['start']):
            start_sec = caption['start']
            duration_sec = caption['duration']
            end_sec = start_sec + duration_sec

            # Skip overlaps
            if start_sec < last_end_time:
                continue

            # Filter by duration
            if duration_sec < min_duration or duration_sec > max_duration:
                continue

            text = caption['text']
            if text:
                filtered_captions.append(text)
                last_end_time = end_sec

        # Map to audio files
        audio_list = sorted(video_groups[video_id], key=lambda x: x[0])

        print(f"  Audio files: {len(audio_list)}")
        print(f"  Filtered captions: {len(filtered_captions)}")

        for i, (index, audio_filename) in enumerate(audio_list):
            if i < len(filtered_captions):
                text = filtered_captions[i]
                metadata_lines.append(f"{audio_filename}|{text}|{text}")
                total_matched += 1
            else:
                print(f"  ⚠️  {audio_filename} has no caption")

        print(f"  Matched: {total_matched}\n")

    # Write metadata.csv
    metadata_path = dataset_path / "metadata.csv"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        for line in metadata_lines:
            f.write(line + '\n')

    print(f"{'='*60}")
    print(f"✅ Metadata rebuilt with newline handling!")
    print(f"{'='*60}")
    print(f"Output: {metadata_path}")
    print(f"Total entries: {len(metadata_lines)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    rebuild_metadata()
