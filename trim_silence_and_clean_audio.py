#!/usr/bin/env python3
"""
Remove background music AND trim silence from audio files.
This combines music removal with silence trimming in one pass.
"""
import os
from pathlib import Path
import numpy as np
from pydub import AudioSegment
from pydub.effects import high_pass_filter, low_pass_filter
from pydub.silence import detect_leading_silence


def trim_silence(audio_segment, silence_threshold=-50.0, chunk_size=10,
                 add_fade_in=False, add_fade_out=True, fade_duration=50):
    """
    Trim silence from the beginning and end of audio.
    Optionally add fade in/out for smooth transitions.

    Args:
        audio_segment: AudioSegment to trim
        silence_threshold: dBFS threshold for silence (default: -50.0)
        chunk_size: Size of chunks to analyze in ms (default: 10)
        add_fade_in: Add fade-in at the beginning (default: False)
        add_fade_out: Add fade-out at the end (default: True)
        fade_duration: Duration of fade in ms (default: 50ms)

    Returns:
        Trimmed AudioSegment with fades
    """
    # Detect leading silence
    start_trim = detect_leading_silence(audio_segment, silence_threshold=silence_threshold, chunk_size=chunk_size)

    # Detect trailing silence by reversing
    end_trim = detect_leading_silence(audio_segment.reverse(), silence_threshold=silence_threshold, chunk_size=chunk_size)

    # Get duration
    duration = len(audio_segment)

    # Trim the audio
    trimmed = audio_segment[start_trim:duration-end_trim]

    # Apply fades for smooth transitions
    if add_fade_in and len(trimmed) > fade_duration:
        trimmed = trimmed.fade_in(duration=fade_duration)

    if add_fade_out and len(trimmed) > fade_duration:
        trimmed = trimmed.fade_out(duration=fade_duration)

    return trimmed, start_trim, end_trim


def reduce_music_simple(audio_segment):
    """
    Simple method: Use frequency filtering to reduce music.
    Human speech is typically in 300-3400 Hz range.
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
    """
    try:
        import noisereduce as nr

        # Convert to numpy array
        samples = np.array(audio_segment.get_array_of_samples())
        sample_rate = audio_segment.frame_rate

        # Apply noise reduction
        reduced = nr.reduce_noise(
            y=samples,
            sr=sample_rate,
            stationary=False,
            prop_decrease=0.8
        )

        # Convert back to AudioSegment
        reduced_audio = audio_segment._spawn(reduced.tobytes())
        return reduced_audio

    except ImportError:
        print("Warning: noisereduce not installed, falling back to simple method")
        return reduce_music_simple(audio_segment)


def process_audio_file(input_path, output_path, remove_music=True, trim_silence_enabled=True,
                       method="simple", silence_threshold=-50.0, add_fade_in=False,
                       add_fade_out=True, fade_duration=50):
    """
    Process audio: remove music and/or trim silence.

    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        remove_music: Whether to remove background music
        trim_silence_enabled: Whether to trim silence
        method: Music removal method ("simple" or "noisereduce")
        silence_threshold: Silence detection threshold in dBFS
        add_fade_in: Add fade-in at beginning (default: False)
        add_fade_out: Add fade-out at end (default: True)
        fade_duration: Fade duration in ms (default: 50ms)

    Returns:
        dict with processing stats or None if failed
    """
    try:
        # Load audio
        audio = AudioSegment.from_wav(str(input_path))
        original_duration = len(audio) / 1000.0  # Convert to seconds

        # Step 1: Remove background music
        if remove_music:
            if method == "simple":
                audio = reduce_music_simple(audio)
            elif method == "noisereduce":
                audio = reduce_music_noisereduce(audio)

        # Step 2: Trim silence and add fades
        start_trim_ms = 0
        end_trim_ms = 0
        if trim_silence_enabled:
            audio, start_trim_ms, end_trim_ms = trim_silence(
                audio,
                silence_threshold=silence_threshold,
                add_fade_in=add_fade_in,
                add_fade_out=add_fade_out,
                fade_duration=fade_duration
            )

        final_duration = len(audio) / 1000.0

        # Export processed audio
        audio.export(str(output_path), format="wav")

        return {
            'success': True,
            'original_duration': original_duration,
            'final_duration': final_duration,
            'trimmed_start': start_trim_ms / 1000.0,
            'trimmed_end': end_trim_ms / 1000.0,
            'total_trimmed': (start_trim_ms + end_trim_ms) / 1000.0
        }

    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return None


def process_dataset(input_dir="ljspeech_dataset/wavs",
                   output_dir="ljspeech_dataset/wavs_cleaned",
                   remove_music=True,
                   trim_silence_enabled=True,
                   method="simple",
                   silence_threshold=-50.0,
                   add_fade_in=False,
                   add_fade_out=True,
                   fade_duration=50):
    """Process all audio files in the dataset."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all wav files
    wav_files = sorted(input_dir.glob("*.wav"))
    total = len(wav_files)

    print(f"Found {total} audio files to process")
    print(f"Music removal: {'Yes' if remove_music else 'No'} ({method})")
    print(f"Silence trimming: {'Yes' if trim_silence_enabled else 'No'}")
    print(f"Fade-out: {'Yes' if add_fade_out else 'No'} ({fade_duration}ms)")
    print(f"Output directory: {output_dir}\n")

    successful = 0
    failed = 0
    total_silence_removed = 0

    for i, wav_file in enumerate(wav_files, 1):
        if i % 50 == 0 or i == 1:
            print(f"Processing {i}/{total}: {wav_file.name}")

        output_path = output_dir / wav_file.name

        result = process_audio_file(
            wav_file,
            output_path,
            remove_music=remove_music,
            trim_silence_enabled=trim_silence_enabled,
            method=method,
            silence_threshold=silence_threshold,
            add_fade_in=add_fade_in,
            add_fade_out=add_fade_out,
            fade_duration=fade_duration
        )

        if result and result['success']:
            successful += 1
            total_silence_removed += result['total_trimmed']
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    if trim_silence_enabled:
        print(f"Total silence removed: {total_silence_removed:.2f} seconds")
        print(f"Average per file: {total_silence_removed/successful:.2f} seconds")
    print(f"{'='*60}")

    return successful, failed


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove background music and trim silence from audio clips"
    )
    parser.add_argument("--input", "-i", default="ljspeech_dataset/wavs",
                       help="Input directory or file")
    parser.add_argument("--output", "-o", default="ljspeech_dataset/wavs_cleaned",
                       help="Output directory or file")
    parser.add_argument("--method", "-m", default="simple",
                       choices=["simple", "noisereduce"],
                       help="Music removal method")
    parser.add_argument("--no-music-removal", action="store_true",
                       help="Skip background music removal")
    parser.add_argument("--no-trim", action="store_true",
                       help="Skip silence trimming")
    parser.add_argument("--silence-threshold", type=float, default=-50.0,
                       help="Silence threshold in dBFS (default: -50.0)")
    parser.add_argument("--fade-in", action="store_true",
                       help="Add fade-in at the beginning")
    parser.add_argument("--no-fade-out", action="store_true",
                       help="Disable fade-out at the end")
    parser.add_argument("--fade-duration", type=int, default=50,
                       help="Fade duration in milliseconds (default: 50ms)")
    parser.add_argument("--single", "-s", action="store_true",
                       help="Process single file instead of directory")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Audio Cleaning Tool")
    print("="*60 + "\n")

    if args.single:
        # Process single file
        result = process_audio_file(
            args.input,
            args.output,
            remove_music=not args.no_music_removal,
            trim_silence_enabled=not args.no_trim,
            method=args.method,
            silence_threshold=args.silence_threshold,
            add_fade_in=args.fade_in,
            add_fade_out=not args.no_fade_out,
            fade_duration=args.fade_duration
        )
        if result:
            print(f"\n✓ Success!")
            print(f"  Original duration: {result['original_duration']:.2f}s")
            print(f"  Final duration: {result['final_duration']:.2f}s")
            print(f"  Trimmed from start: {result['trimmed_start']:.2f}s")
            print(f"  Trimmed from end: {result['trimmed_end']:.2f}s")
            print(f"  Fade-out applied: {'Yes' if not args.no_fade_out else 'No'}")
            print(f"  Output: {args.output}")
    else:
        # Process directory
        process_dataset(
            args.input,
            args.output,
            remove_music=not args.no_music_removal,
            trim_silence_enabled=not args.no_trim,
            method=args.method,
            silence_threshold=args.silence_threshold,
            add_fade_in=args.fade_in,
            add_fade_out=not args.no_fade_out,
            fade_duration=args.fade_duration
        )


if __name__ == "__main__":
    main()
