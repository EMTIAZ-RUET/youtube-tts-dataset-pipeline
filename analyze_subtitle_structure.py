#!/usr/bin/env python3
"""
Analyze the subtitle structure to understand timing issues.
"""
import json
from pathlib import Path

def analyze_subtitles(subtitle_file):
    """Analyze subtitle timing and text content."""
    with open(subtitle_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Analyzing: {subtitle_file}")
    print(f"{'='*80}\n")

    events = data.get('events', [])
    print(f"Total events: {len(events)}\n")

    text_events = []
    for i, event in enumerate(events[:30]):  # First 30 events
        if 'segs' not in event:
            continue

        text = ''.join(seg.get('utf8', '') for seg in event['segs']).strip()
        if not text or text == '\n':
            continue

        start_ms = event.get('tStartMs', 0)
        duration_ms = event.get('dDurationMs', 0)
        start_sec = start_ms / 1000.0
        duration_sec = duration_ms / 1000.0
        end_sec = start_sec + duration_sec

        text_events.append({
            'index': i,
            'text': text,
            'start': start_sec,
            'duration': duration_sec,
            'end': end_sec
        })

    print("First 20 text-containing subtitle segments:\n")
    for i, evt in enumerate(text_events[:20], 1):
        print(f"[{i}] Event index: {evt['index']}")
        print(f"    Time: {evt['start']:.3f}s - {evt['end']:.3f}s (duration: {evt['duration']:.3f}s)")
        print(f"    Text: {evt['text'][:80]}")

        # Check for overlap with previous
        if i > 1:
            prev = text_events[i-2]
            if evt['start'] < prev['end']:
                overlap = prev['end'] - evt['start']
                print(f"    ⚠️  OVERLAP with previous: {overlap:.3f}s")
        print()

if __name__ == "__main__":
    subtitle_file = Path("ljspeech_dataset/raw/ZvnE04N8INo.bn.json3")
    analyze_subtitles(subtitle_file)
