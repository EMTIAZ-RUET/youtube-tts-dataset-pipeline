#!/usr/bin/env python3
"""
Fix metadata mapping by correlating transcript lines with JSON3 captions.
Handles cases where some transcript lines were skipped during audio creation.
"""

import os
import json
from pathlib import Path
import re

def parse_subtitles(subtitle_file):
    """Parse JSON3 subtitle format."""
    try:
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        captions = []
        for event in data.get('events', []):
            if 'segs' not in event:
                continue

            text = ''.join(seg.get('utf8', '') for seg in event['segs'])
            text = text.replace('\n', ' ').replace('  ', ' ').strip()

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
            print(f"  ⚠️  No JSON3 file found, skipping")
            continue

        # Read transcript file
        transcript_file = dataset_path / f"{video_id}_transcript.txt"
        if not transcript_file.exists():
            print(f"  ⚠️  No transcript file found, skipping")
            continue

        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_lines = [line.strip() for line in f if line.strip()]

        # Parse JSON3 captions and filter by duration
        all_captions = parse_subtitles(subtitle_file)

        # Apply same filtering as download script
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

        # Now match filtered captions with transcript lines
        # Each caption might span 1 or 2 transcript lines
        audio_list = sorted(video_groups[video_id], key=lambda x: x[0])

        print(f"  Audio files: {len(audio_list)}")
        print(f"  Filtered captions from JSON: {len(filtered_captions)}")
        print(f"  Transcript lines: {len(transcript_lines)}")

        # Try to match each caption with transcript lines
        matched_texts = []
        for caption_text in filtered_captions:
            # Find matching transcript lines by combining consecutive lines
            best_match = None
            for i in range(len(transcript_lines)):
                # Try 1 line
                if i < len(transcript_lines):
                    combined1 = transcript_lines[i]
                    if caption_text.startswith(combined1.split()[0] if combined1.split() else ""):
                        best_match = combined1

                # Try 2 lines
                if i + 1 < len(transcript_lines):
                    combined2 = transcript_lines[i] + " " + transcript_lines[i + 1]
                    # Check if caption matches the combined lines (allowing for minor differences)
                    if len(combined2) > len(best_match or ""):
                        words_cap = caption_text.split()[:5]
                        words_trans = combined2.split()[:5]
                        if words_cap == words_trans:
                            best_match = combined2

            if best_match:
                matched_texts.append(best_match)
            else:
                # Use caption text as fallback
                matched_texts.append(caption_text)

        # Map to audio files
        for i, (index, audio_filename) in enumerate(audio_list):
            if i < len(matched_texts):
                text = matched_texts[i]
                metadata_lines.append(f"{audio_filename}|{text}|{text}")
                total_matched += 1
            else:
                print(f"  ⚠️  {audio_filename} has no matching text")

        print(f"  Matched: {total_matched}/{len(audio_list)}\n")

    # Write metadata.csv
    metadata_path = dataset_path / "metadata.csv"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        for line in metadata_lines:
            f.write(line + '\n')

    print(f"{'='*60}")
    print(f"✅ Metadata fixed!")
    print(f"{'='*60}")
    print(f"Output: {metadata_path}")
    print(f"Total entries: {len(metadata_lines)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    rebuild_metadata()
