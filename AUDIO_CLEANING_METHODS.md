# Audio Cleaning Methods - Complete Guide

This document lists all available audio cleaning techniques for your dataset.

---

## ✅ Already Applied

### 1. Background Music Removal (Frequency Filtering)
**Status:** ✅ Applied to all 555 files
**Location:** `ljspeech_dataset/wavs_final_cleaned/`

**What it does:**
- Removes low-frequency music (bass below 200 Hz)
- Removes high-frequency music (above 3500 Hz)
- Preserves human speech range (200-3500 Hz)
- Boosts volume +2dB to compensate

### 2. Silence Trimming
**Status:** ✅ Applied to all 555 files
**Location:** `ljspeech_dataset/wavs_final_cleaned/`

**What it does:**
- Removes silence from the beginning of audio
- Removes silence from the end of audio
- Detected at -50 dBFS threshold
- Saved 15.03 seconds total across all files

---

## 🎯 Additional Methods Available

### 3. Noise Reduction (Spectral Gating)
**Status:** Not yet applied
**Tool:** NoiseReduce library
**Processing time:** ~45-90 minutes

**What it does:**
- Advanced noise reduction using spectral analysis
- Better at removing persistent background sounds
- Adapts to non-stationary noise (changing background)
- Preserves speech quality better than simple filtering

**How to apply:**
```bash
pip install noisereduce

python trim_silence_and_clean_audio.py \
    --input ljspeech_dataset/wavs \
    --output ljspeech_dataset/wavs_noisereduced \
    --method noisereduce \
    --silence-threshold -50.0
```

---

### 4. AI Vocal Separation (Demucs)
**Status:** Partially applied (86 files only)
**Tool:** Demucs AI
**Processing time:** ~3-4 hours for all files

**What it does:**
- Uses deep learning to separate vocals from music
- Best quality - professional studio level
- Completely removes background music
- Preserves natural voice quality

**How to apply:**
```bash
python separate_vocals_demucs.py \
    --input ljspeech_dataset/wavs \
    --output ljspeech_dataset/wavs_demucs_vocals \
    --model htdemucs
```

**Note:** 86 files already processed in `ljspeech_dataset/wavs_vocals/`

---

### 5. Audio Normalization
**Status:** Not yet applied
**What it does:**
- Normalizes volume levels across all files
- Ensures consistent loudness
- Prevents clipping and distortion
- Standard levels: -20 dBFS or -16 dBFS

**Implementation:**
```python
from pydub import AudioSegment
from pydub.effects import normalize

audio = AudioSegment.from_wav("input.wav")
normalized = normalize(audio, headroom=0.1)
normalized.export("output.wav", format="wav")
```

---

### 6. Dynamic Range Compression
**Status:** Not yet applied
**What it does:**
- Compresses loud parts
- Boosts quiet parts
- Makes speech more consistent
- Improves clarity

**Use case:** If some clips are too quiet or too loud

---

### 7. De-clicking / De-popping
**Status:** Not yet applied
**What it does:**
- Removes mouth clicks
- Removes lip smacks
- Removes plosives (p, t, k sounds that pop)
- Cleans up recording artifacts

**Tool:** Can be done with audio editing tools or specialized libraries

---

### 8. Spectral Noise Gate
**Status:** Not yet applied
**What it does:**
- Frequency-specific noise gating
- Removes noise only in specific frequency bands
- More precise than simple filtering
- Preserves more speech detail

---

### 9. Resampling / Sample Rate Conversion
**Status:** Already at 22050 Hz
**What it does:**
- Converts sample rate to target
- Current: 22050 Hz (standard for TTS)
- Common rates: 16000 Hz, 22050 Hz, 44100 Hz

**Note:** Already optimized at 22050 Hz

---

### 10. Click Removal
**Status:** Not yet applied
**What it does:**
- Removes digital clicks
- Removes glitches
- Smooths sudden jumps in waveform

---

### 11. Hum Removal
**Status:** Not yet applied
**What it does:**
- Removes electrical hum (50/60 Hz)
- Removes power line interference
- Removes AC hum

**Implementation:**
```python
# Apply notch filter at 50 Hz or 60 Hz
from pydub.effects import band_reject
audio = band_reject(audio, center_freq=50, q=30)
```

---

### 12. Voice Activity Detection (VAD) + Splitting
**Status:** Not yet applied
**What it does:**
- Detects actual speech vs silence
- Can split long audio into speech segments
- More accurate than simple silence detection
- Preserves natural pauses

---

### 13. Clipping Prevention
**Status:** Not yet applied
**What it does:**
- Prevents audio from exceeding max amplitude
- Applies soft limiting
- Preserves dynamics while preventing distortion

---

### 14. Equalization (EQ)
**Status:** Partially applied (simple filtering)
**What it does:**
- Boosts or cuts specific frequencies
- Can enhance voice clarity
- Can reduce muddiness
- Professional voice EQ curve

---

### 15. De-essing
**Status:** Not yet applied
**What it does:**
- Reduces harsh sibilance (s, sh, ch sounds)
- Makes speech smoother
- Commonly used in professional recording

---

### 16. Noise Profile Reduction
**Status:** Not yet applied
**What it does:**
- Records a "noise profile" from silent parts
- Subtracts that noise from entire audio
- Very effective for consistent background noise

**Tool:** Audacity-style noise profiling

---

### 17. Audio Enhancement with AI
**Status:** Not yet applied
**What it does:**
- Uses AI to enhance speech quality
- Can upscale audio quality
- Removes artifacts
- Improves clarity

**Tools:**
- Adobe Enhance Speech (online)
- Krisp AI
- Resemble AI Enhance

---

## 📊 Recommended Workflow

### For Best Quality (Comprehensive):
```bash
# Step 1: AI Vocal Separation (best music removal)
python separate_vocals_demucs.py --input wavs --output wavs_step1

# Step 2: Noise Reduction
python trim_silence_and_clean_audio.py \
    --input wavs_step1 \
    --output wavs_step2 \
    --method noisereduce \
    --no-music-removal

# Step 3: Normalize Volume
# (would need separate script)
```

### For Quick & Good (Current):
```bash
# Already done! ✅
# Music removal + silence trimming in one pass
```

### For Maximum Quality (Time-consuming):
```bash
# 1. Demucs (3-4 hours)
# 2. NoiseReduce (1 hour)
# 3. Normalization (5 min)
# 4. Manual review and cleanup
```

---

## 🎯 Current Dataset Status

**Location:** `ljspeech_dataset/wavs_final_cleaned/`

**Applied:**
- ✅ Frequency filtering (music removal)
- ✅ Silence trimming
- ✅ Volume boost (+2dB)

**Not Applied (Optional):**
- ⭕ Noise reduction (spectral)
- ⭕ AI vocal separation (Demucs) - only 86/555 done
- ⭕ Normalization
- ⭕ Compression
- ⭕ De-essing
- ⭕ Click removal

---

## 💡 Recommendations

### For TTS Training:
Your current cleaned dataset (`wavs_final_cleaned`) is **good enough** for most TTS training:
- ✅ Background music removed
- ✅ Silence trimmed
- ✅ Consistent format (22050 Hz, mono)
- ✅ Speech preserved

### If Audio Quality is Still Poor:
1. **Try NoiseReduce** - 1 hour processing, better quality
2. **Try Demucs** - 3-4 hours processing, best quality

### If Training Results are Poor:
Consider applying:
- Normalization (volume consistency)
- Voice Activity Detection (better segmentation)
- Manual review and removal of bad samples

---

## 🛠️ Quick Commands

### Test different methods on one file:
```bash
# Current method (simple)
python trim_silence_and_clean_audio.py --single \
    --input ljspeech_dataset/wavs/ZvnE04N8INo_000000.wav \
    --output test_simple.wav \
    --method simple

# NoiseReduce method
python trim_silence_and_clean_audio.py --single \
    --input ljspeech_dataset/wavs/ZvnE04N8INo_000000.wav \
    --output test_noisereduce.wav \
    --method noisereduce

# Demucs method
python separate_vocals_demucs.py --single \
    --input ljspeech_dataset/wavs/ZvnE04N8INo_000000.wav \
    --output test_demucs.wav

# Compare all three and choose best!
```

---

## 📈 Performance vs Quality Matrix

| Method | Speed | Quality | Preserves Voice | Removes Music | Removes Noise |
|--------|-------|---------|-----------------|---------------|---------------|
| Simple Filter | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| NoiseReduce | ⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Demucs AI | ⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Normalization | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | N/A | N/A |

---

## ✅ Summary

**Your current dataset** (`wavs_final_cleaned`) has been cleaned with:
- Background music reduction
- Silence trimming
- Volume optimization

This is **ready for TTS training**. Additional methods are available if needed for better quality, but they're optional!
