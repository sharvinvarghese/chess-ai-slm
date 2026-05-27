# ♟ Chess AI SLM

A complete **Flask** chess web app built with:

- **[python-chess](https://python-chess.readthedocs.io/en/latest/core.html)** for move generation, legality, FEN, SAN history, and game-over detection
- **[SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct)** local SLM for trash talk and in-game chat
- **[Flask](https://flask.palletsprojects.com/en/stable/quickstart/)** for routing, templates, and REST API endpoints
- **Gemini Flash Lite** (cloud, API key required) for on-demand coaching hints via the `H` key

---

## Features

| Feature | Detail |
|---|---|
| Chess engine | `python-chess` — fully legal move generation |
| AI opponent | Python minimax with alpha-beta pruning (Black side) |
| Local SLM | SmolLM2-135M-Instruct for trash talk + chat |
| H key hint | Current FEN sent to Gemini Flash Lite for coaching |
| New game | Reset board and state via button or API |
| Move history | SAN notation logged in the sidebar |
| Check / checkmate | Highlighted in UI with badges |

---

## Project Structure

```text
chess-ai-slm/
├── app.py                  # Flask app — routes and API
├── game.py                 # python-chess game state + minimax AI
├── slm.py                  # Local SLM wrapper (trash talk + chat)
├── llm_hint.py             # Gemini hint call using current FEN
├── requirements.txt
├── scripts/
│   └── download_model.py   # First-run SLM download
├── templates/
│   └── index.html          # Jinja2 template
├── static/
│   ├── app.js              # Board interaction + H key + chat
│   └── style.css
└── models/                 # Created by download_model.py
```

---

## Setup

```bash
git clone https://github.com/sharvinvarghese/chess-ai-slm
cd chess-ai-slm
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Download local SLM (one-time, ~270 MB)
python scripts/download_model.py

# Run
python app.py
```

Open **http://127.0.0.1:5000**

---

## How the H key works

1. It is your turn (White).
2. Paste your **Gemini API key** in the hint settings box (or set `GEMINI_API_KEY` env var).
3. Press **H** anywhere on the page (not in an input).
4. The frontend calls `/api/hint`.
5. Flask forwards the current FEN + legal moves to Gemini Flash Lite.
6. The coaching response appears in the hint box.

---

## How the local SLM works

- `scripts/download_model.py` saves `SmolLM2-135M-Instruct` into `models/smollm2-135m-instruct/`.
- `slm.py` loads it at Flask startup.
- Every move event and chat message goes through the SLM for a context-aware response.
- If the model is not downloaded, built-in fallback lines are used — the app still works fully.

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/state` | Current board state (FEN, legal moves, SAN history) |
| POST | `/api/move` | Submit a player move (UCI format) |
| POST | `/api/ai-move` | Trigger AI move for Black |
| POST | `/api/chat` | Send a message to the SLM |
| POST | `/api/trash-talk` | Request event-based trash talk |
| POST | `/api/hint` | Get Gemini hint for current position |
| POST | `/api/new-game` | Reset the board |
| GET | `/api/model-status` | Check if local SLM is loaded |

---

## Contributing

Found a bug or want to add Stockfish support, a stronger evaluator, or streaming chat? Open an issue and raise a PR.
