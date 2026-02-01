#!/usr/bin/env python3
"""
Create truly sequential, non-overlapping audio segments.
This approach detects natural speech boundaries and creates clean segments.
"""
import json
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

def parse_subtitles(subtitle_file):
    """Parse JSON3 subtitle format."""
    with open(subtitle_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    segments = []
    for event in data.get('events', []):
        if 'segs' not in event:
            continue
        text = ''.join(seg.get('utf8', '') for seg in event['segs']).strip()
        if not text or text == '\n':
            continue

        start_sec = event.get('tStartMs', 0) / 1000.0
        duration_sec = event.get('dDurationMs', 0) / 1000.0
        end_sec = start_sec + duration_sec

        segments.append({
            'text': text,
            'start': start_sec,
            'end': end_sec,
            'duration': duration_sec
        })

    return sorted(segments, key=lambda x: x['start'])


def create_sequential_segments(audio_path, subtitles, video_id, output_dir,
                                min_duration=1.0, max_duration=10.0):
    """
    Create sequential segments by using the START time of each subtitle
    and the START time of the NEXT subtitle as the end point.
    This creates truly sequential, non-overlapping segments.
    """
    print(f"Creating sequential segments...")

    try:
        audio = AudioSegment.from_wav(str(audio_path))
    except Exception as e:
        print(f"Error loading audio: {e}")
        return 0

    wavs_dir = output_dir / "wavs"
    wavs_dir.mkdir(parents=True, exist_ok=True)

    metadata = []
    clips_created = 0

    timing_file = output_dir / f"{video_id}_timing_info.txt"
    mapping_file = output_dir / f"{video_id}_audio_mapping.txt"

    with open(timing_file, 'w', encoding='utf-8') as tf:
        tf.write("filename|text|start_time|end_time|duration\n")

    with open(mapping_file, 'w', encoding='utf-8') as mf:
        mf.write("")

    # Process each subtitle, using next subtitle's start as the end
    for i, subtitle in enumerate(subtitles):
        # Determine end time: use next subtitle's start, or add reasonable duration
        if i < len(subtitles) - 1:
            # Use next subtitle's start time
            next_start = subtitles[i + 1]['start']
            # But don't let it be too long
            max_end = subtitle['start'] + max_duration
            end_time = min(next_start, max_end)
        else:
            # Last subtitle - use a reasonable duration
            end_time = min(subtitle['start'] + subtitle['duration'],
                          subtitle['start'] + max_duration)

        start_time = subtitle['start']
        duration = end_time - start_time

        # Apply duration filters
        if duration < min_duration or duration > max_duration:
            continue

        # Ensure we don't go beyond audio length
        start_ms = int(start_time * 1000)
        end_ms = int(end_time * 1000)

        if end_ms > len(audio):
            end_ms = len(audio)
            duration = (end_ms - start_ms) / 1000.0

        if start_ms >= end_ms or start_ms < 0:
            continue

        # Extract audio segment
        try:
            audio_segment = audio[start_ms:end_ms]
        except Exception as e:
            print(f"Warning: Could not extract at {start_time}s: {e}")
            continue

        # Generate filename
        filename = f"{video_id}_{clips_created:06d}.wav"
        output_path = wavs_dir / filename

        # Export as 22050 Hz mono
        audio_segment = audio_segment.set_frame_rate(22050).set_channels(1)
        audio_segment.export(str(output_path), format="wav")

        text = subtitle['text']
        metadata.append(f"{filename}|{text}|{text}")

        with open(mapping_file, 'a', encoding='utf-8') as mf:
            mf.write(f"{filename}|{text}\n")

        with open(timing_file, 'a', encoding='utf-8') as tf:
            tf.write(f"{filename}|{text}|{start_time:.3f}|{end_time:.3f}|{duration:.3f}\n")

        clips_created += 1

        if clips_created % 50 == 0:
            print(f"  Created {clips_created} clips...")

    # Save metadata
    metadata_path = output_dir / "metadata.csv"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        for line in metadata:
            f.write(line + '\n')

    print(f"\n✓ Created {clips_created} sequential clips")
    print(f"✓ Saved metadata to {metadata_path}")

    return clips_created


def main():
    output_dir = Path("ljspeech_dataset")
    raw_dir = output_dir / "raw"

    video_id = "ZvnE04N8INo"
    audio_path = raw_dir / f"{video_id}.wav"
    subtitle_file = raw_dir / f"{video_id}.bn.json3"

    if not audio_path.exists():
        print(f"Error: Audio file not found")
        return

    if not subtitle_file.exists():
        print(f"Error: Subtitle file not found")
        return

    print("="*80)
    print("Creating Sequential Non-Overlapping Segments")
    print("="*80)
    print("Strategy: Use subtitle START time as segment start")
    print("          Use NEXT subtitle START time as segment end")
    print("="*80)
    print()

    # Clear old files
    import shutil
    wavs_dir = output_dir / "wavs"
    if wavs_dir.exists():
        shutil.rmtree(wavs_dir)
    wavs_dir.mkdir(parents=True, exist_ok=True)

    # Parse subtitles
    print("Parsing subtitles...")
    subtitles = parse_subtitles(subtitle_file)
    print(f"Found {len(subtitles)} subtitle segments\n")

    # Show first 5 with timing
    print("First 5 subtitle timings:")
    for i, sub in enumerate(subtitles[:5], 1):
        print(f"  [{i}] {sub['start']:.3f}s - {sub['end']:.3f}s: {sub['text'][:50]}...")
    print()

    # Create sequential segments
    clips_created = create_sequential_segments(
        audio_path, subtitles, video_id, output_dir,
        min_duration=1.0, max_duration=10.0
    )

    print(f"\n{'='*80}")
    print("✅ PROCESSING COMPLETE!")
    print(f"{'='*80}")
    print(f"Total clips: {clips_created}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
