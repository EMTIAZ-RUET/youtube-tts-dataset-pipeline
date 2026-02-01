#!/usr/bin/env python3
"""
Verify LJSpeech format dataset quality and statistics.
"""

import os
import sys
from pathlib import Path
from pydub import AudioSegment
import argparse


def verify_dataset(dataset_dir):
    """Verify and show statistics for LJSpeech dataset."""
    dataset_path = Path(dataset_dir)
    wavs_dir = dataset_path / "wavs"
    metadata_file = dataset_path / "metadata.csv"

    print("="*60)
    print(f"Verifying dataset: {dataset_dir}")
    print("="*60)

    # Check directory structure
    if not dataset_path.exists():
        print(f"❌ Dataset directory not found: {dataset_dir}")
        return False

    if not wavs_dir.exists():
        print(f"❌ wavs directory not found: {wavs_dir}")
        return False

    if not metadata_file.exists():
        print(f"❌ metadata.csv not found: {metadata_file}")
        return False

    print(f"✓ Dataset directory exists")
    print(f"✓ wavs directory exists")
    print(f"✓ metadata.csv exists")
    print()

    # Read metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"Total entries in metadata.csv: {len(lines)}")
    print()

    # Verify audio files
    audio_files = list(wavs_dir.glob("*.wav"))
    print(f"Total WAV files in wavs/: {len(audio_files)}")

    if len(audio_files) != len(lines):
        print(f"⚠️  Warning: Mismatch between metadata entries ({len(lines)}) and audio files ({len(audio_files)})")
    else:
        print(f"✓ Metadata count matches audio file count")

    print()

    # Analyze audio statistics
    print("Analyzing audio files (this may take a moment)...")
    durations = []
    sample_rates = set()
    channels = set()

    for i, audio_file in enumerate(audio_files[:100], 1):  # Sample first 100
        try:
            audio = AudioSegment.from_wav(str(audio_file))
            duration_sec = len(audio) / 1000.0
            durations.append(duration_sec)
            sample_rates.add(audio.frame_rate)
            channels.add(audio.channels)
        except Exception as e:
            print(f"⚠️  Error reading {audio_file.name}: {e}")

    if durations:
        print(f"\nAudio Statistics (from {len(durations)} sampled files):")
        print(f"  Average duration: {sum(durations)/len(durations):.2f} seconds")
        print(f"  Min duration: {min(durations):.2f} seconds")
        print(f"  Max duration: {max(durations):.2f} seconds")
        print(f"  Sample rates: {sample_rates}")
        print(f"  Channels: {channels}")

        if 22050 not in sample_rates:
            print(f"  ⚠️  Warning: Expected 22050 Hz sample rate for TTS")

        if 1 not in channels:
            print(f"  ⚠️  Warning: Expected mono (1 channel) for TTS")
        else:
            print(f"  ✓ All files are mono")

    # Show sample entries
    print("\n" + "="*60)
    print("Sample entries from metadata.csv:")
    print("="*60)
    for i, line in enumerate(lines[:5], 1):
        parts = line.strip().split('|')
        if len(parts) >= 2:
            filename = parts[0]
            text = parts[1]
            print(f"{i}. {filename}")
            print(f"   Text: {text[:80]}{'...' if len(text) > 80 else ''}")
            print()

    # Dataset size
    total_size = sum(f.stat().st_size for f in audio_files)
    total_size_mb = total_size / (1024 * 1024)
    total_size_gb = total_size / (1024 * 1024 * 1024)

    print("="*60)
    print("Dataset Summary:")
    print("="*60)
    print(f"Total clips: {len(audio_files)}")
    print(f"Total size: {total_size_mb:.1f} MB ({total_size_gb:.2f} GB)")

    if durations:
        total_duration_hours = sum(durations) * (len(audio_files) / len(durations)) / 3600
        print(f"Estimated total duration: {total_duration_hours:.2f} hours")

    print("="*60)
    print("\n✅ Dataset verification complete!")

    return True


def main():
    parser = argparse.ArgumentParser(description="Verify LJSpeech format TTS dataset")
    parser.add_argument("dataset_dir", nargs='?', default="ljspeech_dataset",
                        help="Path to dataset directory (default: ljspeech_dataset)")

    args = parser.parse_args()

    verify_dataset(args.dataset_dir)


if __name__ == "__main__":
    main()
