#!/usr/bin/env python3
"""
Adjust audio playback speed without changing pitch.
Slows down or speeds up audio while preserving voice quality.
"""
import os
from pathlib import Path
from pydub import AudioSegment
from pydub.effects import speedup
import argparse


def change_speed(audio_segment, speed=1.0):
    """
    Change audio speed without changing pitch.

    Args:
        audio_segment: AudioSegment to process
        speed: Speed multiplier (default: 1.0)
               < 1.0 = slower (e.g., 0.9 = 10% slower)
               > 1.0 = faster (e.g., 1.1 = 10% faster)

    Returns:
        AudioSegment with adjusted speed
    """
    # If speed is 1.0, no change needed
    if speed == 1.0:
        return audio_segment

    # For slowing down (speed < 1.0), we need to use a different approach
    # We'll change the frame rate and then resample
    if speed < 1.0:
        # Calculate new frame rate
        # Lower frame rate = slower playback
        new_frame_rate = int(audio_segment.frame_rate * speed)

        # Change frame rate (this slows it down)
        slowed = audio_segment._spawn(
            audio_segment.raw_data,
            overrides={'frame_rate': new_frame_rate}
        )

        # Resample back to original rate to maintain compatibility
        return slowed.set_frame_rate(audio_segment.frame_rate)

    else:
        # For speeding up (speed > 1.0), use speedup function
        return speedup(audio_segment, playback_speed=speed)


def process_audio_file(input_path, output_path, speed=0.9):
    """
    Process a single audio file to adjust speed.

    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        speed: Speed multiplier (0.9 = 10% slower)

    Returns:
        dict with processing stats or None if failed
    """
    try:
        # Load audio
        audio = AudioSegment.from_wav(str(input_path))
        original_duration = len(audio) / 1000.0

        # Adjust speed
        adjusted = change_speed(audio, speed=speed)
        new_duration = len(adjusted) / 1000.0

        # Export processed audio
        adjusted.export(str(output_path), format="wav")

        return {
            'success': True,
            'original_duration': original_duration,
            'new_duration': new_duration,
            'speed_factor': speed,
            'duration_change': new_duration - original_duration
        }

    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return None


def process_dataset(input_dir, output_dir, speed=0.9):
    """Process all audio files in a directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all wav files
    wav_files = sorted(input_dir.glob("*.wav"))
    total = len(wav_files)

    print(f"Found {total} audio files to process")
    print(f"Speed adjustment: {speed:.2f}x")

    if speed < 1.0:
        percentage = (1.0 - speed) * 100
        print(f"Making audio {percentage:.0f}% slower")
    else:
        percentage = (speed - 1.0) * 100
        print(f"Making audio {percentage:.0f}% faster")

    print(f"Output directory: {output_dir}\n")

    successful = 0
    failed = 0
    total_duration_added = 0

    for i, wav_file in enumerate(wav_files, 1):
        if i % 50 == 0 or i == 1:
            print(f"Processing {i}/{total}: {wav_file.name}")

        output_path = output_dir / wav_file.name

        result = process_audio_file(wav_file, output_path, speed=speed)

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
    print(f"Average per file: {total_duration_added/successful:.2f} seconds")
    print(f"{'='*60}")

    return successful, failed


def main():
    parser = argparse.ArgumentParser(
        description="Adjust audio playback speed without changing pitch"
    )
    parser.add_argument("--input", "-i", default="ljspeech_dataset/wavs_combined",
                       help="Input directory or file")
    parser.add_argument("--output", "-o", default="ljspeech_dataset/wavs_slowed",
                       help="Output directory or file")
    parser.add_argument("--speed", "-s", type=float, default=0.9,
                       help="Speed multiplier (default: 0.9 = 10%% slower)")
    parser.add_argument("--single", action="store_true",
                       help="Process single file instead of directory")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Audio Speed Adjustment Tool")
    print("="*60 + "\n")

    if args.speed <= 0:
        print("Error: Speed must be greater than 0")
        return

    if args.single:
        # Process single file
        result = process_audio_file(args.input, args.output, speed=args.speed)
        if result:
            print(f"\n✓ Success!")
            print(f"  Original duration: {result['original_duration']:.2f}s")
            print(f"  New duration: {result['new_duration']:.2f}s")
            print(f"  Speed factor: {result['speed_factor']:.2f}x")
            print(f"  Duration change: +{result['duration_change']:.2f}s")
            print(f"  Output: {args.output}")
    else:
        # Process directory
        process_dataset(args.input, args.output, speed=args.speed)


if __name__ == "__main__":
    main()
