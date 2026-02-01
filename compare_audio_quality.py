#!/usr/bin/env python3
"""
Compare original and cleaned audio files.
"""
from pathlib import Path
from pydub import AudioSegment
import numpy as np

def analyze_audio_file(file_path):
    """Analyze audio characteristics."""
    audio = AudioSegment.from_wav(str(file_path))

    # Get audio properties
    duration = len(audio) / 1000.0  # seconds
    sample_rate = audio.frame_rate
    channels = audio.channels

    # Get samples and calculate RMS (volume)
    samples = np.array(audio.get_array_of_samples())
    rms = np.sqrt(np.mean(samples.astype(float)**2))

    # Calculate dynamic range
    max_amplitude = np.max(np.abs(samples))
    min_amplitude = np.min(np.abs(samples[samples != 0])) if len(samples[samples != 0]) > 0 else 0

    return {
        'duration': duration,
        'sample_rate': sample_rate,
        'channels': channels,
        'rms': rms,
        'max_amplitude': max_amplitude,
        'file_size': file_path.stat().st_size
    }


def compare_versions(num_samples=10):
    """Compare original and cleaned versions."""
    original_dir = Path("ljspeech_dataset/wavs")
    cleaned_dir = Path("ljspeech_dataset/wavs_cleaned")

    if not cleaned_dir.exists():
        print("Error: Cleaned audio not found!")
        print("Run: python remove_background_music.py first")
        return

    print("\n" + "="*70)
    print("Audio Quality Comparison: Original vs Cleaned")
    print("="*70)

    # Get sample files
    original_files = sorted(list(original_dir.glob("*.wav")))[:num_samples]

    total_original_size = 0
    total_cleaned_size = 0

    print(f"\nAnalyzing {num_samples} sample files...\n")

    for i, orig_file in enumerate(original_files, 1):
        cleaned_file = cleaned_dir / orig_file.name

        if not cleaned_file.exists():
            continue

        # Analyze both
        orig_stats = analyze_audio_file(orig_file)
        clean_stats = analyze_audio_file(cleaned_file)

        total_original_size += orig_stats['file_size']
        total_cleaned_size += clean_stats['file_size']

        # Calculate changes
        size_reduction = (1 - clean_stats['file_size'] / orig_stats['file_size']) * 100
        rms_change = ((clean_stats['rms'] - orig_stats['rms']) / orig_stats['rms']) * 100

        print(f"[{i}] {orig_file.name}")
        print(f"    Duration: {orig_stats['duration']:.2f}s")
        print(f"    Original: {orig_stats['file_size']/1024:.1f} KB")
        print(f"    Cleaned:  {clean_stats['file_size']/1024:.1f} KB ({size_reduction:+.1f}%)")
        print(f"    RMS change: {rms_change:+.1f}%")
        print()

    # Overall statistics
    print("="*70)
    print("Overall Statistics:")
    print(f"  Total original size: {total_original_size/1024/1024:.2f} MB")
    print(f"  Total cleaned size:  {total_cleaned_size/1024/1024:.2f} MB")
    avg_reduction = (1 - total_cleaned_size / total_original_size) * 100
    print(f"  Average size reduction: {avg_reduction:.1f}%")

    # Calculate for full dataset
    all_original = sum(f.stat().st_size for f in original_dir.glob("*.wav"))
    all_cleaned = sum(f.stat().st_size for f in cleaned_dir.glob("*.wav"))
    full_reduction = (1 - all_cleaned / all_original) * 100

    print(f"\nFull Dataset ({len(list(original_dir.glob('*.wav')))} files):")
    print(f"  Original total: {all_original/1024/1024:.2f} MB")
    print(f"  Cleaned total:  {all_cleaned/1024/1024:.2f} MB")
    print(f"  Space saved: {(all_original - all_cleaned)/1024/1024:.2f} MB ({full_reduction:.1f}%)")
    print("="*70)

    print("\n💡 Next Steps:")
    print("1. Listen to a few cleaned files to verify quality")
    print("2. If satisfied, switch to cleaned version:")
    print("   python switch_audio_version.py use-cleaned")
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare original and cleaned audio quality"
    )
    parser.add_argument("--samples", "-n", type=int, default=10,
                       help="Number of files to analyze in detail (default: 10)")

    args = parser.parse_args()

    compare_versions(args.samples)


if __name__ == "__main__":
    main()
