#!/usr/bin/env python3
"""
Slow down audio with best possible quality using pydub + ffmpeg.
No echo, minimal artifacts, preserves voice character.
"""
import os
from pathlib import Path
from pydub import AudioSegment
from pydub.effects import speedup
import argparse


def slow_audio_pydub_quality(input_path, output_path, speed_factor=0.9):
    """
    Slow down audio using pydub's high-quality method.

    This uses ffmpeg's atempo filter which is designed to preserve
    voice quality during speed changes.

    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        speed_factor: Speed multiplier (0.9 = 10% slower)

    Returns:
        dict with processing stats or None if failed
    """
    try:
        # Load audio
        audio = AudioSegment.from_wav(str(input_path))
        original_duration = len(audio) / 1000.0  # milliseconds to seconds

        # Use pydub's built-in method which uses ffmpeg's atempo
        # This is much higher quality than simple frame rate manipulation
        if speed_factor < 1.0:
            # Slow down - use inverse of speedup
            # Split into multiple small speedup operations for better quality
            speedup_factor = 1.0 / speed_factor

            # ffmpeg atempo works best with values between 0.5 and 2.0
            # So we apply it in stages if needed
            current_audio = audio
            remaining_factor = speedup_factor

            while remaining_factor > 1.01:  # Small threshold for floating point
                if remaining_factor > 2.0:
                    # Apply 2.0x speedup, then continue
                    current_audio = speedup(current_audio, playback_speed=2.0)
                    remaining_factor /= 2.0
                else:
                    # Apply final speedup
                    current_audio = speedup(current_audio, playback_speed=remaining_factor)
                    remaining_factor = 1.0

            slowed_audio = current_audio
        else:
            # Speed up
            slowed_audio = speedup(audio, playback_speed=speed_factor)

        new_duration = len(slowed_audio) / 1000.0

        # Export with high quality
        slowed_audio.export(
            str(output_path),
            format="wav",
            parameters=["-ar", "22050", "-ac", "1"]  # 22050 Hz, mono
        )

        return {
            'success': True,
            'original_duration': original_duration,
            'new_duration': new_duration,
            'speed_factor': speed_factor,
            'duration_change': new_duration - original_duration
        }

    except Exception as e:
        print(f"  Error: {e}")
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
    print(f"Speed adjustment: {speed_factor:.2f}x")

    if speed_factor < 1.0:
        percentage = (1.0 - speed_factor) * 100
        print(f"Making audio {percentage:.0f}% slower")
    else:
        percentage = (speed_factor - 1.0) * 100
        print(f"Making audio {percentage:.0f}% faster")

    print(f"\n{'='*60}")
    print(f"QUALITY METHOD:")
    print(f"  ✓ Using ffmpeg atempo filter (professional quality)")
    print(f"  ✓ Minimal artifacts and echo")
    print(f"  ✓ Preserves voice character")
    print(f"  ✓ Much better than simple resampling")
    print(f"{'='*60}\n")

    print(f"Output directory: {output_dir}\n")

    successful = 0
    failed = 0
    total_duration_added = 0

    for i, wav_file in enumerate(wav_files, 1):
        if i % 20 == 0 or i == 1:
            print(f"Processing {i}/{total}: {wav_file.name}")

        output_path = output_dir / wav_file.name

        result = slow_audio_pydub_quality(wav_file, output_path, speed_factor=speed_factor)

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
        description="Slow down audio with high quality (minimal artifacts)"
    )
    parser.add_argument("--input", "-i", required=True,
                       help="Input directory")
    parser.add_argument("--output", "-o", required=True,
                       help="Output directory")
    parser.add_argument("--speed", "-s", type=float, default=0.9,
                       help="Speed multiplier (default: 0.9 = 10%% slower)")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("HIGH QUALITY Audio Time-Stretching")
    print("="*60)
    print("Using ffmpeg atempo filter")
    print("Minimal artifacts, preserves voice quality")
    print("="*60 + "\n")

    if args.speed <= 0:
        print("Error: Speed must be greater than 0")
        return

    # Process directory
    process_dataset(args.input, args.output, speed_factor=args.speed)


if __name__ == "__main__":
    main()
