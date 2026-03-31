"""
fix_videoprism_gcs.py — Patches videoprism to use a local sentencepiece model
instead of the gs:// GCS path that requires Google Cloud filesystem support.

Downloads the sentencepiece model via HTTPS and patches all copies of models.py
to reference the local file.
"""
import os
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(SCRIPT_DIR, "app")

# Where to save the downloaded model
LOCAL_MODEL = os.path.join(APP_DIR, "videoprism", "cc_en.32000.model")

# HTTPS mirror of the GCS file
HTTPS_URL = "https://storage.googleapis.com/t5-data/vocabs/cc_en.32000/sentencepiece.model"

# The GCS string to replace
GCS_PATH = "gs://t5-data/vocabs/cc_en.32000/sentencepiece.model"

# All copies of models.py that need patching
TARGETS = [
    os.path.join(APP_DIR, "videoprism", "videoprism", "models.py"),
    os.path.join(APP_DIR, "videoprism", "build", "lib", "videoprism", "models.py"),
]

# Also patch the installed site-packages copy
env_sp = os.path.join(APP_DIR, "env", "Lib", "site-packages", "videoprism", "models.py")
if os.path.exists(env_sp):
    TARGETS.append(env_sp)


def main():
    # 1. Download the sentencepiece model if missing
    if not os.path.exists(LOCAL_MODEL):
        print(f"Downloading sentencepiece model to {LOCAL_MODEL} ...")
        os.makedirs(os.path.dirname(LOCAL_MODEL), exist_ok=True)
        urllib.request.urlretrieve(HTTPS_URL, LOCAL_MODEL)
        print("Done.")
    else:
        print(f"Sentencepiece model already exists at {LOCAL_MODEL}")

    # Use forward slashes for the replacement path (works on all platforms)
    local_path_str = LOCAL_MODEL.replace("\\", "/")

    # 2. Patch all copies of models.py
    patched = 0
    for target in TARGETS:
        if not os.path.exists(target):
            print(f"  SKIP (not found): {target}")
            continue

        with open(target, "r", encoding="utf-8") as f:
            content = f.read()

        if GCS_PATH in content:
            content = content.replace(GCS_PATH, local_path_str)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  PATCHED: {target}")
            patched += 1
        else:
            print(f"  OK (already patched): {target}")

    print(f"\nDone. Patched {patched} file(s).")


if __name__ == "__main__":
    main()
