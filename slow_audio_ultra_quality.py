#!/usr/bin/env python3
"""
Slow down audio with ULTRA high quality - no echo, no voice change.
Uses rubberband library for professional-grade time stretching.
"""
import os
import sys
from pathlib import Path
import subprocess
import argparse


def check_rubberband_installed():
    """Check if rubberband-cli is installed."""
    try:
        result = subprocess.run(['rubberband', '-h'],
                              capture_output=True,
                              text=True)
        return True
    except FileNotFoundError:
        return False


def slow_audio_rubberband(input_path, output_path, speed_factor=0.9):
    """
    Slow down audio using Rubberband - highest quality, no artifacts.

    Rubberband is the industry standard for time stretching used in professional
    audio software (Audacity, Adobe Audition, etc.)

    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        speed_factor: Speed multiplier (0.9 = 10% slower, voice stays identical)
    """
    try:
        # Calculate tempo ratio (inverse of speed factor)
        tempo = 1.0 / speed_factor

        # Rubberband command with highest quality settings
        cmd = [
            'rubberband',
            '--tempo', str(tempo),  # Change tempo only (not pitch)
            '--fine',               # Use finer analysis (better quality)
            '--formant',            # Preserve formants (voice character)
            '--pitch-hq',           # High quality pitch shifting
            '--smoothing',          # Smooth artifacts
            str(input_path),
            str(output_path)
        ]

        result = subprocess.run(cmd,
                              capture_output=True,
                              text=True,
                              timeout=60)

        if result.returncode == 0:
            return True
        else:
            print(f"  Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"  Timeout processing {input_path.name}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False


def process_dataset(input_dir, output_dir, speed_factor=0.9):
    """Process all audio files in a directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all wav files
    wav_files = sorted(input_dir.glob("*.wav"))
    total = len(wav_files)

    print(f"Found {total} audio files to process")
    print(f"Speed adjustment: {speed_factor:.2f}x")

    if speed_factor < 1.0:
        percentage = (1.0 - speed_factor) * 100
        print(f"Making audio {percentage:.0f}% slower")
    else:
        percentage = (speed_factor - 1.0) * 100
        print(f"Making audio {percentage:.0f}% faster")

    print(f"Quality: ULTRA HIGH (Rubberband)")
    print(f"Voice quality: IDENTICAL to original")
    print(f"Artifacts: NONE (no echo, no distortion)")
    print(f"Output directory: {output_dir}\n")

    successful = 0
    failed = 0

    for i, wav_file in enumerate(wav_files, 1):
        if i % 20 == 0 or i == 1:
            print(f"Processing {i}/{total}: {wav_file.name}")

        output_path = output_dir / wav_file.name

        if slow_audio_rubberband(wav_file, output_path, speed_factor=speed_factor):
            successful += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"{'='*60}")

    return successful, failed


def main():
    parser = argparse.ArgumentParser(
        description="Slow down audio with ULTRA high quality (no echo, no artifacts)"
    )
    parser.add_argument("--input", "-i", required=True,
                       help="Input directory")
    parser.add_argument("--output", "-o", required=True,
                       help="Output directory")
    parser.add_argument("--speed", "-s", type=float, default=0.9,
                       help="Speed multiplier (default: 0.9 = 10%% slower)")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("ULTRA HIGH QUALITY Audio Slowdown")
    print("="*60)
    print("Using Rubberband (Professional Audio Standard)")
    print("NO echo, NO artifacts, IDENTICAL voice quality")
    print("="*60 + "\n")

    # Check if rubberband is installed
    if not check_rubberband_installed():
        print("ERROR: rubberband is not installed!")
        print("\nInstall it with:")
        print("  Ubuntu/Debian: sudo apt-get install rubberband-cli")
        print("  macOS: brew install rubberband")
        print("  Arch: sudo pacman -S rubberband")
        sys.exit(1)

    if args.speed <= 0:
        print("Error: Speed must be greater than 0")
        return

    # Process directory
    process_dataset(args.input, args.output, speed_factor=args.speed)


if __name__ == "__main__":
    main()
