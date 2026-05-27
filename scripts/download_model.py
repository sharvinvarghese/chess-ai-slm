"""
First-run model download script.
Downloads only .safetensors + config files (~280 MB) from
HuggingFaceTB/SmolLM2-135M-Instruct into models/smollm2-135m-instruct/.

Skips the legacy pytorch_model.bin to avoid downloading 270 MB twice.

Usage:
    python scripts/download_model.py
"""
from pathlib import Path
from huggingface_hub import snapshot_download

MODEL_ID = 'HuggingFaceTB/SmolLM2-135M-Instruct'
TARGET = Path(__file__).resolve().parents[1] / 'models' / 'smollm2-135m-instruct'
TARGET.parent.mkdir(parents=True, exist_ok=True)

print(f'Downloading {MODEL_ID}')
print(f'Target directory: {TARGET}')
print('Skipping legacy .bin weights — only safetensors (~280 MB total)...')

snapshot_download(
    repo_id=MODEL_ID,
    local_dir=str(TARGET),
    # skip legacy pytorch .bin files (same weights, just an older format)
    ignore_patterns=['*.bin', '*.bin.index.json', 'flax_model*', 'tf_model*'],
)

print('\nDownload complete!')
print(f'Model saved to: {TARGET}')
print('You can now run: python app.py')
