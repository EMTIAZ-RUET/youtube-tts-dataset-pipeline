#!/usr/bin/env python3
"""
Reprocess existing raw audio files with corrected timing.
"""
import json
from pathlib import Path
from pydub import AudioSegment

def parse_subtitles(subtitle_file):
    """Parse JSON3 subtitle format."""
    try:
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        captions = []
        for event in data.get('events', []):
            if 'segs' not in event:
                continue

            text = ''.join(seg.get('utf8', '') for seg in event['segs'])
            text = text.strip()

            if not text or text == '\n':
                continue

            start_sec = event.get('tStartMs', 0) / 1000.0
            duration_ms = event.get('dDurationMs', 0)
            duration_sec = duration_ms / 1000.0

            captions.append({
                'text': text,
                'start': start_sec,
                'duration': duration_sec
            })

        return captions
    except Exception as e:
        print(f"Error parsing subtitles: {e}")
        return []


def segment_audio(audio_path, captions, video_id, output_dir, min_duration=1.0, max_duration=10.0):
    """
    Segment audio using EXACT subtitle timing - no adjustments.
    """
    print(f"Segmenting audio into clips...")

    try:
        audio = AudioSegment.from_wav(str(audio_path))
    except Exception as e:
        print(f"Error loading audio: {e}")
        return 0

    wavs_dir = output_dir / "wavs"
    wavs_dir.mkdir(parents=True, exist_ok=True)

    # Sort captions by start time
    sorted_captions = sorted(captions, key=lambda x: x['start'])

    clips_created = 0
    skipped_overlaps = 0
    metadata = []

    # Save detailed timing information
    timing_file = output_dir / f"{video_id}_timing_info.txt"
    with open(timing_file, 'w', encoding='utf-8') as tf:
        tf.write("filename|text|original_start|original_duration|original_end\n")

    mapping_file = output_dir / f"{video_id}_audio_mapping.txt"
    with open(mapping_file, 'w', encoding='utf-8') as mf:
        mf.write("")  # Clear file

    # Track used time regions to prevent duplicate extractions
    used_regions = []

    for caption in sorted_captions:
        # Use ORIGINAL timing from subtitle - no adjustments
        start_sec = caption['start']
        duration_sec = caption['duration']
        end_sec = start_sec + duration_sec

        # Filter by duration
        if duration_sec < min_duration or duration_sec > max_duration:
            continue

        text = caption['text'].replace('\n', ' ').replace('  ', ' ').strip()
        if not text:
            continue

        # Check if this time region significantly overlaps with already used regions
        skip_this = False
        for used_start, used_end in used_regions:
            overlap_start = max(start_sec, used_start)
            overlap_end = min(end_sec, used_end)
            overlap_duration = max(0, overlap_end - overlap_start)

            # If more than 80% of this segment overlaps with a used one, skip it
            overlap_pct = overlap_duration / duration_sec
            if overlap_pct > 0.8:
                skip_this = True
                skipped_overlaps += 1
                break

        if skip_this:
            continue

        # Extract segment using EXACT original timing
        start_ms = int(start_sec * 1000)
        end_ms = int(end_sec * 1000)

        # Ensure we don't go beyond audio length
        if end_ms > len(audio):
            end_ms = len(audio)
            duration_sec = (end_ms - start_ms) / 1000.0

        # Safety check for valid segment
        if start_ms >= end_ms or start_ms < 0:
            continue

        try:
            audio_segment = audio[start_ms:end_ms]
        except Exception as e:
            print(f"Warning: Could not extract segment at {start_sec}s: {e}")
            continue

        # Generate filename
        filename = f"{video_id}_{clips_created:06d}.wav"
        output_path = wavs_dir / filename

        # Export as 22050 Hz mono
        audio_segment = audio_segment.set_frame_rate(22050).set_channels(1)
        audio_segment.export(str(output_path), format="wav")

        # Add to metadata
        metadata.append(f"{filename}|{text}|{text}")

        # Save mapping
        with open(mapping_file, 'a', encoding='utf-8') as mf:
            mf.write(f"{filename}|{text}\n")

        # Save timing info
        with open(timing_file, 'a', encoding='utf-8') as tf:
            tf.write(f"{filename}|{text}|{start_sec:.3f}|{duration_sec:.3f}|{end_sec:.3f}\n")

        # Mark this time region as used
        used_regions.append((start_sec, end_sec))

        clips_created += 1

        if clips_created % 50 == 0:
            print(f"  Created {clips_created} clips...")

    # Save metadata.csv
    metadata_path = output_dir / "metadata.csv"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        for line in metadata:
            f.write(line + '\n')

    print(f"\n✓ Created {clips_created} clips (skipped {skipped_overlaps} highly overlapping segments)")
    print(f"✓ Saved metadata to {metadata_path}")
    print(f"✓ Saved timing info to {timing_file}")
    print(f"✓ Saved audio mapping to {mapping_file}")

    return clips_created


def main():
    output_dir = Path("ljspeech_dataset")
    raw_dir = output_dir / "raw"

    video_id = "ZvnE04N8INo"
    audio_path = raw_dir / f"{video_id}.wav"
    subtitle_file = raw_dir / f"{video_id}.bn.json3"

    if not audio_path.exists():
        print(f"Error: Audio file not found: {audio_path}")
        return

    if not subtitle_file.exists():
        print(f"Error: Subtitle file not found: {subtitle_file}")
        return

    print("="*60)
    print("Reprocessing existing audio with corrected timing")
    print("="*60)
    print(f"Video ID: {video_id}")
    print(f"Audio: {audio_path}")
    print(f"Subtitles: {subtitle_file}")
    print()

    # Parse subtitles
    print("Parsing subtitles...")
    captions = parse_subtitles(subtitle_file)
    print(f"Found {len(captions)} subtitle segments\n")

    # Segment audio
    clips_created = segment_audio(audio_path, captions, video_id, output_dir)

    print(f"\n{'='*60}")
    print("✅ PROCESSING COMPLETE!")
    print(f"{'='*60}")
    print(f"Total clips created: {clips_created}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
