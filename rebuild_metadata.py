#!/usr/bin/env python3
"""
Rebuild metadata.csv by mapping transcript lines to audio files.
Each line in transcript file maps to one audio file.
"""

import os
from pathlib import Path
import re

def rebuild_metadata(dataset_dir="ljspeech_dataset"):
    dataset_path = Path(dataset_dir)
    wavs_dir = dataset_path / "wavs"

    if not wavs_dir.exists():
        print(f"Error: {wavs_dir} does not exist")
        return

    # Get all audio files
    audio_files = sorted(wavs_dir.glob("*.wav"))
    print(f"Found {len(audio_files)} audio files")

    # Group audio files by video ID
    video_groups = {}
    for audio_file in audio_files:
        # Extract video ID from filename (e.g., "_iueYd-yybM_000000.wav")
        match = re.match(r"(.+?)_(\d{6})\.wav", audio_file.name)
        if match:
            video_id = match.group(1)
            index = int(match.group(2))
            if video_id not in video_groups:
                video_groups[video_id] = []
            video_groups[video_id].append((index, audio_file.name))

    print(f"Found {len(video_groups)} videos")

    # Build metadata
    metadata_lines = []

    for video_id in sorted(video_groups.keys()):
        # Find transcript file
        transcript_file = dataset_path / f"{video_id}_transcript.txt"

        if not transcript_file.exists():
            print(f"Warning: No transcript file for {video_id}")
            continue

        # Read transcript lines
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_lines = [line.strip() for line in f if line.strip()]

        # Sort audio files by index
        audio_list = sorted(video_groups[video_id], key=lambda x: x[0])

        print(f"\n{video_id}:")
        print(f"  Transcript lines: {len(transcript_lines)}")
        print(f"  Audio files: {len(audio_list)}")

        # Map each audio file to 2 transcript lines combined
        for i, (index, audio_filename) in enumerate(audio_list):
            # Calculate the line indices (2 lines per audio)
            line_index_1 = i * 2
            line_index_2 = i * 2 + 1

            if line_index_1 < len(transcript_lines):
                # Combine 2 lines for this audio file
                text_parts = [transcript_lines[line_index_1]]
                if line_index_2 < len(transcript_lines):
                    text_parts.append(transcript_lines[line_index_2])

                text = " ".join(text_parts)
                # LJSpeech format: filename|text|normalized_text
                metadata_lines.append(f"{audio_filename}|{text}|{text}")
            else:
                print(f"  Warning: Audio {audio_filename} has no matching transcript lines")

    # Write metadata.csv
    metadata_path = dataset_path / "metadata.csv"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        for line in metadata_lines:
            f.write(line + '\n')

    print(f"\n{'='*60}")
    print(f"✅ Metadata rebuilt successfully!")
    print(f"{'='*60}")
    print(f"Output: {metadata_path}")
    print(f"Total entries: {len(metadata_lines)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    rebuild_metadata()
