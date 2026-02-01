#!/usr/bin/env python3
"""
Separate vocals from background music using Demucs AI model.
This is the most effective method for removing background music.
"""
import os
import sys
import shutil
from pathlib import Path
import subprocess

def separate_vocals_batch(input_dir, output_dir, model="htdemucs"):
    """
    Use Demucs to separate vocals from music for all files in a directory.

    Args:
        input_dir: Directory containing audio files
        output_dir: Directory to save separated vocals
        model: Demucs model to use (htdemucs is best quality)
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all wav files
    wav_files = sorted(input_dir.glob("*.wav"))
    total = len(wav_files)

    print(f"Found {total} audio files to process")
    print(f"Model: {model}")
    print(f"This will take some time...\n")

    # Create temporary directory for Demucs output
    temp_dir = Path("demucs_temp")

    successful = 0
    failed = 0

    for i, wav_file in enumerate(wav_files, 1):
        print(f"[{i}/{total}] Processing: {wav_file.name}")

        try:
            # Run Demucs separation
            cmd = [
                "demucs",
                "--two-stems=vocals",  # Only separate vocals
                "-n", model,
                "-o", str(temp_dir),
                str(wav_file)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                print(f"  ❌ Failed: {result.stderr}")
                failed += 1
                continue

            # Find the output vocals file
            # Demucs creates: temp_dir/model_name/filename/vocals.wav
            vocals_file = temp_dir / model / wav_file.stem / "vocals.wav"

            if vocals_file.exists():
                # Copy to output directory with original name
                shutil.copy(vocals_file, output_dir / wav_file.name)
                print(f"  ✓ Success")
                successful += 1
            else:
                print(f"  ❌ Vocals file not found")
                failed += 1

        except subprocess.TimeoutExpired:
            print(f"  ❌ Timeout (>120s)")
            failed += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1

        # Clean up temp files for this clip
        if (temp_dir / model / wav_file.stem).exists():
            shutil.rmtree(temp_dir / model / wav_file.stem)

    # Clean up temp directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}")

    return successful, failed


def separate_single_file(input_file, output_file, model="htdemucs"):
    """Separate vocals from a single audio file."""
    input_file = Path(input_file)
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    temp_dir = Path("demucs_temp")

    print(f"Processing: {input_file.name}")
    print(f"Model: {model}\n")

    try:
        # Run Demucs
        cmd = [
            "demucs",
            "--two-stems=vocals",
            "-n", model,
            "-o", str(temp_dir),
            str(input_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False

        # Find vocals file
        vocals_file = temp_dir / model / input_file.stem / "vocals.wav"

        if vocals_file.exists():
            shutil.copy(vocals_file, output_file)
            print(f"✓ Vocals saved to: {output_file}")

            # Clean up
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            return True
        else:
            print("Error: Vocals file not found")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Separate vocals from background music using Demucs AI"
    )
    parser.add_argument("--input", "-i", default="ljspeech_dataset/wavs",
                       help="Input directory or file")
    parser.add_argument("--output", "-o", default="ljspeech_dataset/wavs_vocals",
                       help="Output directory or file")
    parser.add_argument("--model", "-m", default="htdemucs",
                       choices=["htdemucs", "htdemucs_ft", "mdx_extra"],
                       help="Demucs model (htdemucs is best)")
    parser.add_argument("--single", "-s", action="store_true",
                       help="Process single file instead of directory")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Demucs Vocal Separation Tool")
    print("="*60)
    print("This uses AI to separate vocals from music")
    print("First run will download the model (~300MB)")
    print("="*60 + "\n")

    if args.single:
        separate_single_file(args.input, args.output, args.model)
    else:
        separate_vocals_batch(args.input, args.output, args.model)


if __name__ == "__main__":
    main()
