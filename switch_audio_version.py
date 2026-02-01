#!/usr/bin/env python3
"""
Switch between original and cleaned audio versions.
"""
import shutil
from pathlib import Path

def switch_to_cleaned():
    """Switch to using cleaned audio (background music removed)."""
    wavs_dir = Path("ljspeech_dataset/wavs")
    cleaned_dir = Path("ljspeech_dataset/wavs_cleaned")
    backup_dir = Path("ljspeech_dataset/wavs_original_backup")

    if not cleaned_dir.exists():
        print("Error: Cleaned audio directory not found!")
        print("Run: python remove_background_music.py first")
        return False

    # Backup original if not already backed up
    if not backup_dir.exists():
        print("Creating backup of original audio...")
        shutil.copytree(wavs_dir, backup_dir)
        print(f"✓ Original audio backed up to: {backup_dir}")

    # Replace with cleaned
    print("Switching to cleaned audio...")
    shutil.rmtree(wavs_dir)
    shutil.copytree(cleaned_dir, wavs_dir)

    print("\n✅ Switched to cleaned audio!")
    print(f"Active: ljspeech_dataset/wavs/ (cleaned)")
    print(f"Backup: {backup_dir} (original)")
    return True


def switch_to_original():
    """Switch back to original audio."""
    wavs_dir = Path("ljspeech_dataset/wavs")
    backup_dir = Path("ljspeech_dataset/wavs_original_backup")

    if not backup_dir.exists():
        print("Error: No backup found!")
        print("Original audio may already be active.")
        return False

    print("Restoring original audio...")
    shutil.rmtree(wavs_dir)
    shutil.copytree(backup_dir, wavs_dir)

    print("\n✅ Switched to original audio!")
    print(f"Active: ljspeech_dataset/wavs/ (original)")
    return True


def show_status():
    """Show current audio version status."""
    wavs_dir = Path("ljspeech_dataset/wavs")
    cleaned_dir = Path("ljspeech_dataset/wavs_cleaned")
    backup_dir = Path("ljspeech_dataset/wavs_original_backup")

    print("\n" + "="*60)
    print("Audio Version Status")
    print("="*60)

    # Check what's active
    if wavs_dir.exists():
        count = len(list(wavs_dir.glob("*.wav")))
        size = sum(f.stat().st_size for f in wavs_dir.glob("*.wav")) / (1024*1024)
        print(f"\n📁 Active (wavs/): {count} files, {size:.1f} MB")

    # Check if cleaned exists
    if cleaned_dir.exists():
        count = len(list(cleaned_dir.glob("*.wav")))
        size = sum(f.stat().st_size for f in cleaned_dir.glob("*.wav")) / (1024*1024)
        print(f"🧹 Cleaned (wavs_cleaned/): {count} files, {size:.1f} MB")

    # Check if backup exists
    if backup_dir.exists():
        count = len(list(backup_dir.glob("*.wav")))
        size = sum(f.stat().st_size for f in backup_dir.glob("*.wav")) / (1024*1024)
        print(f"💾 Original Backup: {count} files, {size:.1f} MB")

    print("\n" + "="*60)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Switch between original and cleaned audio versions"
    )
    parser.add_argument("action", choices=["status", "use-cleaned", "use-original"],
                       help="Action to perform")

    args = parser.parse_args()

    if args.action == "status":
        show_status()
    elif args.action == "use-cleaned":
        if switch_to_cleaned():
            show_status()
    elif args.action == "use-original":
        if switch_to_original():
            show_status()


if __name__ == "__main__":
    main()
