import tempfile
from pathlib import Path

# Keep scratch files inside this workspace under restricted Windows sandboxes.
scratch = Path(__file__).resolve().parents[1]/'.superpowers'/'test-tmp'
scratch.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(scratch)
