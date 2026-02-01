#!/usr/bin/env python3
"""
Slow down audio while preserving the original pitch/voice quality.
Uses librosa's time stretching algorithm (phase vocoder).
"""
import os
from pathlib import Path
import numpy as np
import librosa
import soundfile as sf
import argparse


def slow_audio_preserve_pitch(audio_path, output_path, speed_factor=0.9):
    """
    Slow down audio while preserving pitch.

    Args:
        audio_path: Input audio file path
        output_path: Output audio file path
        speed_factor: Speed multiplier (0.9 = 10% slower, voice stays same)

    Returns:
        dict with processing stats or None if failed
    """
    try:
        # Load audio
        y, sr = librosa.load(audio_path, sr=None)
        original_duration = len(y) / sr

        # Time stretch while preserving pitch
        # speed_factor < 1.0 = slower
        # This uses phase vocoder to maintain pitch
        y_stretched = librosa.effects.time_stretch(y, rate=speed_factor)

        new_duration = len(y_stretched) / sr

        # Save the stretched audio
        sf.write(output_path, y_stretched, sr, subtype='PCM_16')

        return {
            'success': True,
            'original_duration': original_duration,
            'new_duration': new_duration,
            'speed_factor': speed_factor,
            'duration_change': new_duration - original_duration
        }

    except Exception as e:
        print(f"Error processing {audio_path}: {e}")
        return None


def process_dataset(input_dir, output_dir, speed_factor=0.9):
    """Process all audio files in a directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all wav files
    wav_files = sorted(input_dir.glob("*.wav"))
    total = len(wav_files)

    print(f"Found {total} audio files to process")
    print(f"Speed adjustment: {speed_factor:.2f}x (pitch preserved)")

    if speed_factor < 1.0:
        percentage = (1.0 - speed_factor) * 100
        print(f"Making audio {percentage:.0f}% slower WITHOUT changing voice")
    else:
        percentage = (speed_factor - 1.0) * 100
        print(f"Making audio {percentage:.0f}% faster WITHOUT changing voice")

    print(f"Output directory: {output_dir}\n")

    successful = 0
    failed = 0
    total_duration_added = 0

    for i, wav_file in enumerate(wav_files, 1):
        if i % 20 == 0 or i == 1:
            print(f"Processing {i}/{total}: {wav_file.name}")

        output_path = output_dir / wav_file.name

        result = slow_audio_preserve_pitch(wav_file, output_path, speed_factor=speed_factor)

        if result and result['success']:
            successful += 1
            total_duration_added += result['duration_change']
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total duration added: {total_duration_added:.2f} seconds")
    if successful > 0:
        print(f"Average per file: {total_duration_added/successful:.2f} seconds")
    print(f"{'='*60}")

    return successful, failed


def main():
    parser = argparse.ArgumentParser(
        description="Slow down audio while preserving original pitch/voice"
    )
    parser.add_argument("--input", "-i", default="ljspeech_dataset/wavs_combined",
                       help="Input directory or file")
    parser.add_argument("--output", "-o", default="ljspeech_dataset/wavs_slowed_pitch_preserved",
                       help="Output directory or file")
    parser.add_argument("--speed", "-s", type=float, default=0.9,
                       help="Speed multiplier (default: 0.9 = 10%% slower, voice unchanged)")
    parser.add_argument("--single", action="store_true",
                       help="Process single file instead of directory")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Audio Speed Adjustment (Pitch Preserved)")
    print("="*60)
    print("Using librosa time stretching")
    print("Voice quality will remain natural!")
    print("="*60 + "\n")

    if args.speed <= 0:
        print("Error: Speed must be greater than 0")
        return

    if args.single:
        # Process single file
        result = slow_audio_preserve_pitch(args.input, args.output, speed_factor=args.speed)
        if result:
            print(f"\n✓ Success!")
            print(f"  Original duration: {result['original_duration']:.2f}s")
            print(f"  New duration: {result['new_duration']:.2f}s")
            print(f"  Speed factor: {result['speed_factor']:.2f}x")
            print(f"  Duration change: +{result['duration_change']:.2f}s")
            print(f"  Pitch: PRESERVED (voice sounds natural)")
            print(f"  Output: {args.output}")
    else:
        # Process directory
        process_dataset(args.input, args.output, speed_factor=args.speed)


if __name__ == "__main__":
    main()
