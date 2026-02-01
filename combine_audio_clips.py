#!/usr/bin/env python3
"""
Combine multiple short audio clips into longer segments.
This creates longer training samples by concatenating consecutive clips.
"""
import os
from pathlib import Path
from pydub import AudioSegment
import argparse


def load_metadata(metadata_file):
    """Load metadata from CSV file."""
    metadata = []
    with open(metadata_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 2:
                filename = parts[0]
                text = parts[1]
                metadata.append({'filename': filename, 'text': text})
    return metadata


def combine_audio_clips(input_dir, output_dir, metadata,
                       clips_per_segment=3,
                       max_duration=10.0,
                       add_pause=100):
    """
    Combine multiple audio clips into longer segments.

    Args:
        input_dir: Directory with audio files
        output_dir: Directory to save combined audio
        metadata: List of metadata dicts
        clips_per_segment: Number of clips to combine (default: 3)
        max_duration: Maximum duration in seconds (default: 10.0)
        add_pause: Pause between clips in ms (default: 100ms)

    Returns:
        New metadata list
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    new_metadata = []
    combined_count = 0
    i = 0

    print(f"Combining {len(metadata)} clips into longer segments...")
    print(f"Target: {clips_per_segment} clips per segment")
    print(f"Max duration: {max_duration}s")
    print(f"Pause between clips: {add_pause}ms\n")

    # Silence segment for pauses
    silence = AudioSegment.silent(duration=add_pause)

    while i < len(metadata):
        combined_audio = None
        combined_text = []
        combined_filenames = []
        current_duration = 0.0
        clips_in_segment = 0

        # Combine up to clips_per_segment clips
        while i < len(metadata) and clips_in_segment < clips_per_segment:
            clip_info = metadata[i]
            audio_path = input_dir / clip_info['filename']

            if not audio_path.exists():
                print(f"Warning: {audio_path} not found, skipping")
                i += 1
                continue

            try:
                # Load audio
                audio = AudioSegment.from_wav(str(audio_path))
                clip_duration = len(audio) / 1000.0

                # Check if adding this clip exceeds max duration
                if current_duration + clip_duration > max_duration and clips_in_segment > 0:
                    # Don't add this clip, save it for next segment
                    break

                # Add to combined audio
                if combined_audio is None:
                    combined_audio = audio
                else:
                    combined_audio = combined_audio + silence + audio

                combined_text.append(clip_info['text'])
                combined_filenames.append(clip_info['filename'])
                current_duration += clip_duration + (add_pause / 1000.0)
                clips_in_segment += 1
                i += 1

            except Exception as e:
                print(f"Error loading {audio_path}: {e}")
                i += 1
                continue

        # Save combined audio
        if combined_audio and clips_in_segment > 0:
            # Generate output filename
            video_id = combined_filenames[0].split('_')[0]
            output_filename = f"{video_id}_combined_{combined_count:06d}.wav"
            output_path = output_dir / output_filename

            # Export combined audio
            combined_audio.export(str(output_path), format="wav")

            # Create combined text (join with space)
            full_text = ' '.join(combined_text)

            # Add to new metadata
            new_metadata.append({
                'filename': output_filename,
                'text': full_text,
                'original_files': combined_filenames,
                'num_clips': clips_in_segment,
                'duration': current_duration
            })

            combined_count += 1

            if combined_count % 50 == 0 or combined_count == 1:
                print(f"Created {combined_count} combined segments...")

    print(f"\n✓ Created {combined_count} combined audio segments")
    print(f"  Original clips: {len(metadata)}")
    print(f"  Combined segments: {combined_count}")
    print(f"  Reduction: {len(metadata) - combined_count} clips")

    return new_metadata


def save_metadata(metadata, output_file):
    """Save metadata to CSV file in LJSpeech format."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in metadata:
            # LJSpeech format: filename|text|normalized_text
            line = f"{item['filename']}|{item['text']}|{item['text']}\n"
            f.write(line)
    print(f"✓ Saved metadata to {output_file}")


def save_detailed_mapping(metadata, output_file):
    """Save detailed mapping showing which clips were combined."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("combined_filename|original_files|num_clips|duration|text\n")
        for item in metadata:
            original_files = ','.join(item.get('original_files', []))
            num_clips = item.get('num_clips', 1)
            duration = item.get('duration', 0.0)
            text = item['text']
            line = f"{item['filename']}|{original_files}|{num_clips}|{duration:.2f}|{text}\n"
            f.write(line)
    print(f"✓ Saved detailed mapping to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Combine multiple audio clips into longer segments"
    )
    parser.add_argument("--input", "-i", default="ljspeech_dataset/wavs_smooth",
                       help="Input directory with audio files")
    parser.add_argument("--output", "-o", default="ljspeech_dataset/wavs_combined",
                       help="Output directory for combined audio")
    parser.add_argument("--metadata", "-m", default="ljspeech_dataset/metadata.csv",
                       help="Input metadata CSV file")
    parser.add_argument("--clips-per-segment", "-n", type=int, default=3,
                       help="Number of clips to combine per segment (default: 3)")
    parser.add_argument("--max-duration", "-d", type=float, default=10.0,
                       help="Maximum duration per segment in seconds (default: 10.0)")
    parser.add_argument("--pause", "-p", type=int, default=100,
                       help="Pause between clips in milliseconds (default: 100ms)")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Audio Clip Combination Tool")
    print("="*60 + "\n")

    # Load metadata
    print(f"Loading metadata from {args.metadata}...")
    metadata = load_metadata(args.metadata)
    print(f"✓ Loaded {len(metadata)} clips\n")

    # Combine audio clips
    new_metadata = combine_audio_clips(
        args.input,
        args.output,
        metadata,
        clips_per_segment=args.clips_per_segment,
        max_duration=args.max_duration,
        add_pause=args.pause
    )

    # Save new metadata
    output_metadata = Path(args.output).parent / "metadata_combined.csv"
    save_metadata(new_metadata, output_metadata)

    # Save detailed mapping
    output_mapping = Path(args.output).parent / "combined_audio_mapping.txt"
    save_detailed_mapping(new_metadata, output_mapping)

    print(f"\n{'='*60}")
    print("✅ COMBINATION COMPLETE!")
    print(f"{'='*60}")
    print(f"Combined audio: {args.output}")
    print(f"New metadata: {output_metadata}")
    print(f"Detailed mapping: {output_mapping}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
