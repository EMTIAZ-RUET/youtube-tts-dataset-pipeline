#!/usr/bin/env python3
"""
Remove background music from audio clips using audio processing techniques.
This script uses multiple methods to reduce background music.
"""
import os
import sys
from pathlib import Path
import numpy as np
from pydub import AudioSegment
from pydub.effects import high_pass_filter, low_pass_filter

def reduce_music_simple(audio_segment):
    """
    Simple method: Use frequency filtering to reduce music.
    Human speech is typically in 300-3400 Hz range.
    Music often has more bass and treble.
    """
    # Apply high-pass filter to remove low frequency music (bass)
    audio_segment = high_pass_filter(audio_segment, cutoff=200)

    # Apply low-pass filter to remove high frequency music
    audio_segment = low_pass_filter(audio_segment, cutoff=3500)

    # Boost volume slightly to compensate for filtering
    audio_segment = audio_segment + 2  # +2 dB

    return audio_segment


def reduce_music_noisereduce(audio_segment):
    """
    Advanced method: Use noisereduce library with spectral gating.
    This is better at preserving speech quality.
    """
    try:
        import noisereduce as nr

        # Convert to numpy array
        samples = np.array(audio_segment.get_array_of_samples())
        sample_rate = audio_segment.frame_rate

        # Apply noise reduction (treats music as noise)
        reduced = nr.reduce_noise(
            y=samples,
            sr=sample_rate,
            stationary=False,  # Non-stationary noise (music changes)
            prop_decrease=0.8   # How much to reduce (0-1)
        )

        # Convert back to AudioSegment
        reduced_audio = audio_segment._spawn(reduced.tobytes())
        return reduced_audio

    except ImportError:
        print("Warning: noisereduce not installed, falling back to simple method")
        return reduce_music_simple(audio_segment)


def process_audio_file(input_path, output_path, method="simple"):
    """Process a single audio file to reduce background music."""
    try:
        # Load audio
        audio = AudioSegment.from_wav(str(input_path))

        if method == "simple":
            # Use simple frequency filtering
            processed = reduce_music_simple(audio)
        elif method == "noisereduce":
            # Use advanced noise reduction
            processed = reduce_music_noisereduce(audio)
        else:
            processed = audio

        # Export processed audio
        processed.export(str(output_path), format="wav")
        return True

    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False


def process_dataset(input_dir="ljspeech_dataset/wavs",
                   output_dir="ljspeech_dataset/wavs_cleaned",
                   method="simple"):
    """Process all audio files in the dataset."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all wav files
    wav_files = sorted(input_dir.glob("*.wav"))
    total = len(wav_files)

    print(f"Found {total} audio files to process")
    print(f"Method: {method}")
    print(f"Output directory: {output_dir}\n")

    successful = 0
    failed = 0

    for i, wav_file in enumerate(wav_files, 1):
        if i % 50 == 0 or i == 1:
            print(f"Processing {i}/{total}: {wav_file.name}")

        output_path = output_dir / wav_file.name

        if process_audio_file(wav_file, output_path, method=method):
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
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove background music from audio clips"
    )
    parser.add_argument("--input", "-i", default="ljspeech_dataset/wavs",
                       help="Input directory with audio files")
    parser.add_argument("--output", "-o", default="ljspeech_dataset/wavs_cleaned",
                       help="Output directory for cleaned audio")
    parser.add_argument("--method", "-m", default="simple",
                       choices=["simple", "noisereduce"],
                       help="Method: simple (fast) or noisereduce (better quality)")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Background Music Reduction Tool")
    print("="*60 + "\n")

    process_dataset(args.input, args.output, args.method)


if __name__ == "__main__":
    main()
