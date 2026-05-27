"""
First-run model download script.
Downloads only .safetensors + config files (~280 MB) from
HuggingFaceTB/SmolLM2-135M-Instruct into models/smollm2-135m-instruct/.

IMPORTANT: Wipes any previous partial download first so stale .bin
blobs from an earlier interrupted run do not get resumed.

Usage:
    python scripts/download_model.py
"""
import shutil
from pathlib import Path
from huggingface_hub import snapshot_download

MODEL_ID = 'HuggingFaceTB/SmolLM2-135M-Instruct'
TARGET = Path(__file__).resolve().parents[1] / 'models' / 'smollm2-135m-instruct'

# ------------------------------------------------------------------
# Wipe any previous partial/stale download so ignore_patterns takes
# effect cleanly (HF Hub resumes incomplete blobs by default which
# bypasses ignore_patterns for already-started transfers).
# ------------------------------------------------------------------
if TARGET.exists():
    print(f'Removing stale download at {TARGET} ...')
    shutil.rmtree(TARGET)

TARGET.mkdir(parents=True, exist_ok=True)

print(f'Downloading {MODEL_ID}')
print(f'Target directory: {TARGET}')
print('Fetching safetensors only — skipping legacy .bin (~280 MB total)...')

snapshot_download(
    repo_id=MODEL_ID,
    local_dir=str(TARGET),
    # skip legacy pytorch .bin files (same weights, just an older format)
    ignore_patterns=[
        '*.bin',
        '*.bin.index.json',
        'flax_model*',
        'tf_model*',
        'rust_model*',
        'onnx*',
    ],
)

print('\nDownload complete!')
print(f'Model saved to: {TARGET}')
print('You can now run: python app.py')
