"""
First-run model download script.
Downloads HuggingFaceTB/SmolLM2-135M-Instruct into models/smollm2-135m-instruct/.

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
print('This is a ~270 MB download on first run...')

snapshot_download(
    repo_id=MODEL_ID,
    local_dir=str(TARGET),
    local_dir_use_symlinks=False,
)
print('Download complete. You can now run: python app.py')
