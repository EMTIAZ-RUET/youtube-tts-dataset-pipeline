# Background Music Removal Guide

This guide explains how to remove or reduce background music from your audio dataset.

---

## Available Methods

### Method 1: Simple Filtering (FASTEST - Recommended for Testing)

**Speed:** Very fast (~1-2 seconds per file)
**Quality:** Good for light background music
**How it works:** Filters out frequencies outside human speech range (200-3500 Hz)

```bash
python remove_background_music.py \
    --input ljspeech_dataset/wavs \
    --output ljspeech_dataset/wavs_cleaned \
    --method simple
```

**Pros:**
- Very fast processing
- No additional downloads needed
- Works well for light background music
- Preserves speech quality

**Cons:**
- May not remove all music
- Music in speech frequency range remains

---

### Method 2: Noise Reduction (BETTER QUALITY)

**Speed:** Slower (~5-10 seconds per file)
**Quality:** Better at removing persistent background sounds
**Requires:** `pip install noisereduce`

```bash
# Install first
pip install noisereduce

# Then process
python remove_background_music.py \
    --input ljspeech_dataset/wavs \
    --output ljspeech_dataset/wavs_cleaned \
    --method noisereduce
```

**Pros:**
- Better at removing background music
- Adapts to changing music
- Good speech preservation

**Cons:**
- Slower than simple method
- May introduce artifacts if music is very loud

---

### Method 3: AI Vocal Separation (BEST QUALITY - Recommended)

**Speed:** Slowest (~10-30 seconds per file)
**Quality:** Excellent - uses AI to separate vocals from music
**Requires:** Demucs (already installed)
**First run downloads:** ~300MB model

```bash
python separate_vocals_demucs.py \
    --input ljspeech_dataset/wavs \
    --output ljspeech_dataset/wavs_vocals \
    --model htdemucs
```

**Pros:**
- Best quality - AI-powered separation
- Removes music completely
- Preserves speech perfectly
- Industry standard

**Cons:**
- Slowest method
- First run downloads model
- Requires more RAM/CPU

**Model Options:**
- `htdemucs` - Best quality (recommended)
- `htdemucs_ft` - Fine-tuned version
- `mdx_extra` - Alternative model

---

## Quick Start Recommendations

### If you have light background music:
```bash
python remove_background_music.py --method simple
```

### If you have moderate background music:
```bash
pip install noisereduce
python remove_background_music.py --method noisereduce
```

### If you want the best quality:
```bash
python separate_vocals_demucs.py
```

---

## Processing Your Dataset

### Option A: Replace Original Files
```bash
# Backup first!
cp -r ljspeech_dataset/wavs ljspeech_dataset/wavs_backup

# Process and replace
python remove_background_music.py \
    --input ljspeech_dataset/wavs \
    --output ljspeech_dataset/wavs \
    --method simple
```

### Option B: Keep Both Versions
```bash
# Create cleaned version in new directory
python remove_background_music.py \
    --input ljspeech_dataset/wavs \
    --output ljspeech_dataset/wavs_cleaned \
    --method simple

# Compare and choose which to use
```

---

## Test on Sample Files First

Test on a few files before processing the entire dataset:

```bash
# Create test directory
mkdir -p test_audio_in test_audio_out

# Copy a few files
cp ljspeech_dataset/wavs/ZvnE04N8INo_00000[0-4].wav test_audio_in/

# Test processing
python remove_background_music.py \
    --input test_audio_in \
    --output test_audio_out \
    --method simple

# Listen to results and compare with originals
```

---

## Processing Single Files

To process just one file for testing:

```bash
# Simple method
python -c "
from remove_background_music import process_audio_file
process_audio_file('ljspeech_dataset/wavs/ZvnE04N8INo_000000.wav',
                   'test_output.wav',
                   method='simple')
"

# Demucs method
python separate_vocals_demucs.py \
    --single \
    --input ljspeech_dataset/wavs/ZvnE04N8INo_000000.wav \
    --output test_output.wav
```

---

## Performance Comparison

| Method | Time per File | Quality | RAM Usage | Best For |
|--------|--------------|---------|-----------|----------|
| Simple | 1-2 sec | Good | Low | Light music, testing |
| NoiseReduce | 5-10 sec | Better | Medium | Moderate music |
| Demucs AI | 10-30 sec | Best | High | Heavy music, production |

**For 555 files:**
- Simple: ~10-20 minutes
- NoiseReduce: ~45-90 minutes
- Demucs: ~1.5-4 hours

---

## Current Status

Your dataset: **555 audio files in ljspeech_dataset/wavs/**

**Test results available:**
- ✅ Simple filtering tested: ljspeech_dataset/wavs_test_cleaned/
- Compare original vs cleaned to verify quality

---

## Next Steps

1. **Listen to test files** in `wavs_test_cleaned/` to verify quality
2. **Choose method** based on music level and time available
3. **Process full dataset** with chosen method
4. **Update metadata** if needed (filenames stay the same)

---

## Tips for Best Results

1. **Test first:** Always process 5-10 files first to check quality
2. **Listen carefully:** Compare original and cleaned versions
3. **Check speech quality:** Make sure voices aren't distorted
4. **Consider music level:** Heavy music needs AI separation
5. **Backup originals:** Always keep unprocessed copies

---

## Troubleshooting

### Music still audible after simple filtering?
→ Try `noisereduce` or `demucs` method

### Speech sounds muffled?
→ Reduce filtering strength or use different method

### Processing too slow?
→ Use simpler method or process in batches

### Out of memory with Demucs?
→ Process smaller batches or use simpler method

---

## Integration with Download Script

To automatically clean audio during download, modify the segmentation function to include filtering. See `download_youtube_dataset.py` for implementation.

---

**Current dataset:** 555 clips @ 61MB (original)
**Test cleaned:** 555 clips @ 61MB (filtered)
