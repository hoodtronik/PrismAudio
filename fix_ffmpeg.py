"""Copy FFmpeg 6 shared DLLs into torio/lib so torchaudio can use them.

On Windows, torio's libtorio_ffmpeg6.pyd needs avcodec-60.dll (and friends)
to be co-located or on PATH. Conda installs them into Library/bin which is
not visible to a Python venv.  This script copies them next to the .pyd files.
"""
import sys, os, shutil, glob

if sys.platform != "win32":
    print("Not Windows — FFmpeg shared libs are resolved by the system linker.")
    sys.exit(0)

conda_prefix = os.environ.get("CONDA_PREFIX", "")
if not conda_prefix:
    print("WARNING: CONDA_PREFIX not set — cannot locate FFmpeg DLLs, skipping.")
    sys.exit(0)

src_dir = os.path.join(conda_prefix, "Library", "bin")
if not os.path.isdir(src_dir):
    print(f"WARNING: {src_dir} not found — skipping FFmpeg DLL copy.")
    sys.exit(0)

try:
    import torio
    dst_dir = os.path.join(os.path.dirname(torio.__file__), "lib")
except ImportError:
    print("WARNING: torio not installed — skipping.")
    sys.exit(0)

if not os.path.isdir(dst_dir):
    print(f"WARNING: torio/lib dir not found at {dst_dir} — skipping.")
    sys.exit(0)

patterns = ["av*.dll", "sw*.dll", "postproc*.dll"]
copied = 0
for pattern in patterns:
    for src_file in glob.glob(os.path.join(src_dir, pattern)):
        dst_file = os.path.join(dst_dir, os.path.basename(src_file))
        shutil.copy2(src_file, dst_file)
        print(f"  Copied {os.path.basename(src_file)}")
        copied += 1

if copied:
    print(f"Done: {copied} FFmpeg DLLs -> {dst_dir}")
else:
    print("WARNING: No FFmpeg DLLs found to copy. Video decoding may fail.")
