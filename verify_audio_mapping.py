#!/usr/bin/env python3
"""
Verify that audio files are correctly mapped to text by checking timing.
"""
import json
import os
from pathlib import Path
from pydub import AudioSegment

def load_subtitle_data(subtitle_file):
    """Load subtitle timing data from JSON3 file."""
    with open(subtitle_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    segments = []
    for event in data.get('events', []):
        if 'segs' not in event:
            continue

        text = ''.join(seg.get('utf8', '') for seg in event['segs']).strip()
        if not text:
            continue

        start_sec = event.get('tStartMs', 0) / 1000.0
        duration_ms = event.get('dDurationMs', 0)
        duration_sec = duration_ms / 1000.0

        segments.append({
            'text': text,
            'start': start_sec,
            'duration': duration_sec,
            'end': start_sec + duration_sec
        })

    return segments

def verify_mapping(dataset_dir="ljspeech_dataset"):
    """Verify audio-text mappings."""
    dataset_dir = Path(dataset_dir)

    # Read metadata
    metadata_file = dataset_dir / "metadata.csv"
    metadata = {}
    with open(metadata_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 2:
                filename = parts[0]
                text = parts[1]
                metadata[filename] = text

    print(f"Total clips in metadata: {len(metadata)}")

    # Find video IDs
    video_ids = set()
    for filename in metadata.keys():
        video_id = filename.split('_')[0]
        video_ids.add(video_id)

    print(f"Video IDs found: {video_ids}\n")

    # Verify each video
    for video_id in video_ids:
        print(f"{'='*60}")
        print(f"Verifying: {video_id}")
        print(f"{'='*60}")

        # Load subtitle data
        subtitle_file = None
        for ext in ['.bn.json3', '.bn-IN.json3', '.en.json3']:
            path = dataset_dir / "raw" / f"{video_id}{ext}"
            if path.exists():
                subtitle_file = path
                break

        if not subtitle_file:
            print(f"  ❌ No subtitle file found")
            continue

        print(f"  Loading subtitle data from {subtitle_file.name}")
        subtitle_segments = load_subtitle_data(subtitle_file)
        print(f"  Total subtitle segments: {len(subtitle_segments)}")

        # Get clips for this video
        video_clips = [(f, metadata[f]) for f in metadata if f.startswith(video_id)]
        video_clips.sort()

        print(f"  Audio clips created: {len(video_clips)}\n")

        # Verify first 5 clips
        print(f"  Verifying first 5 clips:")
        for i, (filename, text) in enumerate(video_clips[:5]):
            # Extract counter from filename
            counter = int(filename.split('_')[1].split('.')[0])

            # Get audio duration
            wav_path = dataset_dir / "wavs" / filename
            if wav_path.exists():
                audio = AudioSegment.from_wav(str(wav_path))
                audio_duration = len(audio) / 1000.0  # Convert to seconds

                # Find matching subtitle segment (by counter)
                if counter < len(subtitle_segments):
                    subtitle_info = subtitle_segments[counter]

                    print(f"\n  [{i+1}] {filename}")
                    print(f"      Text: {text[:50]}...")
                    print(f"      Audio duration: {audio_duration:.2f}s")
                    print(f"      Expected duration: {subtitle_info['duration']:.2f}s")
                    print(f"      Timing: {subtitle_info['start']:.2f}s - {subtitle_info['end']:.2f}s")

                    # Check if durations are close (within 0.5 seconds)
                    duration_diff = abs(audio_duration - subtitle_info['duration'])
                    if duration_diff < 0.5:
                        print(f"      ✓ Timing matches!")
                    else:
                        print(f"      ⚠️  Duration mismatch: {duration_diff:.2f}s difference")

        print(f"\n  {'='*60}\n")

if __name__ == "__main__":
    verify_mapping()
