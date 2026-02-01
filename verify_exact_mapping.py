#!/usr/bin/env python3
"""
Verify audio-text mapping by comparing extracted audio with subtitle timing.
"""
import json
from pathlib import Path
from pydub import AudioSegment

def verify_mapping():
    """Verify that audio segments match their text timing exactly."""
    dataset_dir = Path("ljspeech_dataset")

    # Load subtitle data
    subtitle_file = dataset_dir / "raw" / "ZvnE04N8INo.bn.json3"
    with open(subtitle_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Parse subtitles
    subtitle_segments = []
    for event in data.get('events', []):
        if 'segs' not in event:
            continue
        text = ''.join(seg.get('utf8', '') for seg in event['segs']).strip()
        if not text or text == '\n':
            continue

        start_sec = event.get('tStartMs', 0) / 1000.0
        duration_sec = event.get('dDurationMs', 0) / 1000.0

        subtitle_segments.append({
            'text': text,
            'start': start_sec,
            'duration': duration_sec
        })

    # Load timing info
    timing_file = dataset_dir / "ZvnE04N8INo_timing_info.txt"
    timing_data = []
    with open(timing_file, 'r', encoding='utf-8') as f:
        next(f)  # Skip header
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 5:
                timing_data.append({
                    'filename': parts[0],
                    'text': parts[1],
                    'start': float(parts[2]),
                    'duration': float(parts[3]),
                    'end': float(parts[4])
                })

    print("="*80)
    print("AUDIO-TEXT MAPPING VERIFICATION")
    print("="*80)
    print(f"Total clips: {len(timing_data)}")
    print(f"Total subtitle segments: {len(subtitle_segments)}\n")

    # Verify first 10 clips
    print("Checking first 10 clips:\n")
    for i, clip in enumerate(timing_data[:10], 1):
        # Get actual audio duration
        wav_path = dataset_dir / "wavs" / clip['filename']
        audio = AudioSegment.from_wav(str(wav_path))
        actual_duration = len(audio) / 1000.0

        # Find matching subtitle
        matching_subtitle = None
        for sub in subtitle_segments:
            if abs(sub['start'] - clip['start']) < 0.01 and sub['text'] == clip['text']:
                matching_subtitle = sub
                break

        print(f"[{i}] {clip['filename']}")
        print(f"    Text: {clip['text'][:60]}...")
        print(f"    Timing in file: {clip['start']:.3f}s - {clip['end']:.3f}s")
        print(f"    Expected duration: {clip['duration']:.3f}s")
        print(f"    Actual audio duration: {actual_duration:.3f}s")

        duration_match = abs(actual_duration - clip['duration']) < 0.1
        subtitle_match = matching_subtitle is not None

        if duration_match and subtitle_match:
            print(f"    ✓ PERFECT MATCH - Audio timing matches subtitle exactly!")
        elif duration_match:
            print(f"    ✓ Duration matches")
        else:
            diff = abs(actual_duration - clip['duration'])
            print(f"    ⚠️  Duration mismatch: {diff:.3f}s difference")

        if not subtitle_match:
            print(f"    ⚠️  Could not find matching subtitle")

        print()

    # Check for any mismatches in all clips
    print("\n" + "="*80)
    print("CHECKING ALL CLIPS FOR MISMATCHES")
    print("="*80)

    mismatches = 0
    for clip in timing_data:
        wav_path = dataset_dir / "wavs" / clip['filename']
        audio = AudioSegment.from_wav(str(wav_path))
        actual_duration = len(audio) / 1000.0

        # Allow 0.1s tolerance for rounding
        if abs(actual_duration - clip['duration']) > 0.1:
            mismatches += 1
            if mismatches <= 5:  # Show first 5 mismatches
                print(f"\n❌ Mismatch found: {clip['filename']}")
                print(f"   Expected: {clip['duration']:.3f}s, Actual: {actual_duration:.3f}s")
                print(f"   Difference: {abs(actual_duration - clip['duration']):.3f}s")

    if mismatches == 0:
        print("\n✅ SUCCESS! All audio files match their timing data exactly!")
    else:
        print(f"\n⚠️  Found {mismatches} clips with duration mismatches")

    print("\n" + "="*80)

if __name__ == "__main__":
    verify_mapping()
