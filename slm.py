"""slm.py — Local SLM wrapper for Chess AI SLM

Persona: Rex
  Rex is simultaneously humble and arrogant — he genuinely respects good moves
  while being insufferably confident about his own superiority. He delivers
  dry, non-repeating humour with the energy of someone who has already won
  in his head before the game ends.

  Tone: Magnus Carlsen meets a stand-up comedian who studies too much chess.
  Never toxic. Never rambling. Always lands the line.

Model selection (edit MODEL_ID + local_path below):
  ┌─────────────────────────────────────┬──────────┬────────────┬──────────────────────────────┐
  │ Model                               │ Disk     │ Speed      │ Quality                      │
  ├─────────────────────────────────────┼──────────┼────────────┼──────────────────────────────┤
  │ SmolLM2-135M-Instruct (default)     │ ~280 MB  │ ~1200 t/s  │ Weak — use fallbacks only    │
  │ SmolLM2-360M-Instruct (recommended) │ ~720 MB  │ ~600 t/s   │ Noticeably better coherence  │
  │ SmolLM2-1.7B-Instruct               │ ~3.4 GB  │ ~150 t/s   │ Good conversation quality    │
  └─────────────────────────────────────┴──────────┴────────────┴──────────────────────────────┘

  To swap:
    1. Change MODEL_ID to e.g. 'HuggingFaceTB/SmolLM2-360M-Instruct'
    2. Change LOCAL_FOLDER to e.g. 'smollm2-360m-instruct'
    3. Re-run: python scripts/download_model.py
    4. Restart: python app.py
"""
import random
from pathlib import Path

# ── MODEL SELECTION ─────────────────────────────────────────────────────────
# Change both values together. See the table in the docstring above.
MODEL_ID     = 'HuggingFaceTB/SmolLM2-135M-Instruct'
LOCAL_FOLDER = 'smollm2-135m-instruct'
# ────────────────────────────────────────────────────────────────────────────


# ---------------------------------------------------------------------------
# Rex's fallback line bank
# Rules:
#   - Each line must sound like a different joke / different register
#   - Mix humble concession + arrogant confidence in the same breath
#   - No sentence starts the same way twice in a row (enforced by _pick)
# ---------------------------------------------------------------------------
_FALLBACK: dict[str, list[str]] = {
    'move': [
        "Solid move. Genuinely. Now watch me dismantle it anyway.",
        "That took courage. Misplaced, but courage.",
        "I've seen worse. I've also seen much, much better.",
        "Respect for trying. My next move won't return the favour.",
        "Good instinct, wrong position. Happens to everyone. Repeatedly.",
        "I almost worried there. Key word: almost.",
        "You're improving. Unfortunately, so is my attack.",
        "Textbook move. Sadly for you, I've read the whole book.",
        "A fine choice in a parallel universe where I don't play e4.",
        "That's not bad. It's also not enough.",
        "I respect the commitment. The result is going to be awkward.",
        "Three more moves like that and I might actually sweat.",
    ],
    'check': [
        "Check. Bold. My king's had scarier encounters with a pawn.",
        "Oh, check! I'll treasure this moment before I escape it.",
        "You found tactics. I found the refutation. We both worked hard.",
        "Check is a conversation starter. I prefer to end conversations.",
        "Nice fork. Wrong king.",
        "My king is annoyed, not worried. There's a difference.",
    ],
    'capture': [
        "You took material. I'm taking the initiative. Fair trade?",
        "Captured my piece. Congratulations. It was bait.",
        "Bold exchange. My compensation is... the entire position.",
        "Enjoy the material. I'll enjoy the attack.",
        "That piece was volunteering for sacrifice. Inspiring, really.",
        "You counted pawns. I counted tempos. We disagree on who's winning.",
    ],
    'loss': [
        "Deserved. That endgame was clinical. I respect it.",
        "Well played. I had it until I very much didn't.",
        "You converted that beautifully. I walked into it beautifully.",
        "I admit defeat. I also reserve the right to rematch immediately.",
        "Clean win. I'll spend tonight analysing where I went wrong.",
        "That was sharp. The next game will be different. Probably.",
    ],
    'win': [
        "Checkmate. I enjoyed the parts where you were doing okay.",
        "Game over. You made the right moves — they were just not enough.",
        "Well that went as planned. My plan, specifically.",
        "Another one. I genuinely thought you had me on move eleven.",
        "I win, but honestly? That bishop manoeuvre of yours was beautiful.",
    ],
    'chat': [
        "Noted. The board has different opinions.",
        "Interesting philosophy. My rook disagrees.",
        "Trash talk is fine. Just don't let it distract you from blundering.",
        "I hear the words. My pieces hear a different story.",
        "You know what's underrated? Quiet moves. Unlike this conversation.",
        "Fair point. Wrong game to make it in.",
        "I respect the attempt at psychological warfare. Truly.",
        "Big talk from someone whose queenside is already compromised.",
        "Words cost nothing. Tempo costs everything.",
        "That's almost as sharp as your position. Almost.",
    ],
    'taunt': [
        "Your pawn structure has the aesthetic of a Tuesday morning.",
        "One of us has a plan. The other has pieces in random squares.",
        "I've played against stronger opposition in bullet. At 3am.",
        "Your kingside is giving 'I'll castle next move' since move seven.",
        "That opening choice was brave. So was the Titanic's route.",
        "I don't doubt your effort. I do doubt your evaluation.",
        "This is either a deep positional idea or a blunder. Probably the second.",
        "Your pieces communicate with each other the way strangers do in a lift.",
    ],
}

# Track last used line per category to avoid exact repetition
_LAST_USED: dict[str, str] = {}


def _pick(category: str) -> str:
    """Pick a random line, avoiding the last used one in that category."""
    pool = _FALLBACK.get(category, _FALLBACK['move'])
    last = _LAST_USED.get(category)
    choices = [l for l in pool if l != last]
    if not choices:
        choices = pool
    line = random.choice(choices)
    _LAST_USED[category] = line
    return line


# ── SYSTEM PROMPTS ───────────────────────────────────────────────────────────
# Tightly constrained for SmolLM2 family.
# The persona blends humility (acknowledges good moves) with arrogance
# (never doubts the outcome). Non-repeating humour via context injection.

_SYSTEM_TRASH = """You are Rex, a chess rival with a very specific personality:
- HUMBLE: you genuinely acknowledge good moves and admit when you're impressed
- ARROGANT: you are absolutely certain you will win regardless
- FUNNY: dry, non-repeating wit — like a grandmaster who moonlights in comedy
STRICT RULES:
- Exactly ONE sentence. Under 18 words. No exceptions.
- No questions. No lists. No quotation marks. No ellipsis abuse.
- Start with a fresh angle every time — never repeat the same opening word.
- Output ONLY the line. Nothing else."""

_SYSTEM_CHAT = """You are Rex, a chess rival. Personality:
- Humble when genuinely impressed, arrogant when not
- Dry humour, never toxic, never rambling
- You speak like someone who has already calculated the next six moves
STRICT RULES:
- 1-2 short sentences MAX
- No repetition of previous lines
- Stay in character. Be sharp. End cleanly.
- Output ONLY the reply. No meta-commentary."""


class TrashTalkSLM:
    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.tokenizer = None
        self.local_path = self.model_dir / LOCAL_FOLDER
        self.last_error: str | None = None
        self._try_load()

    def _try_load(self):
        if not self.local_path.exists():
            self.last_error = (
                f'Model folder not found: {self.local_path}. '
                'Run: python scripts/download_model.py'
            )
            return
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.local_path))
            self.model = AutoModelForCausalLM.from_pretrained(str(self.local_path))
            self.model.eval()
        except Exception as exc:
            self.last_error = str(exc)
            self.model = None
            self.tokenizer = None

    def is_ready(self) -> bool:
        return self.model is not None and self.tokenizer is not None

    def status(self) -> dict:
        return {
            'ready':      self.is_ready(),
            'model_id':   MODEL_ID,
            'local_path': str(self.local_path),
            'message':    'Loaded and ready' if self.is_ready() else (self.last_error or 'Not ready'),
        }

    # ------------------------------------------------------------------
    def _fallback(self, event: str = 'move') -> str:
        return _pick(event)

    def _clean(self, raw: str) -> str | None:
        """Extract first usable sentence from model output."""
        # remove common artifacts
        for noise in ['<|im_end|>', '<|endoftext|>', 'assistant\n', 'Rex:']:
            raw = raw.replace(noise, '')
        for line in raw.split('\n'):
            line = line.strip().strip('"').strip("'")
            # accept lines that look like a complete thought
            if 8 < len(line) < 180 and not line.lower().startswith(('fen:', 'position:', 'last move', 'recent')):
                return line
        return None

    def _generate(self, system_prompt: str, user_prompt: str, max_new_tokens: int = 55) -> str | None:
        if not self.is_ready():
            return None
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_prompt},
            ]
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer(text, return_tensors='pt')
            input_len = inputs['input_ids'].shape[1]

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.75,
                top_p=0.88,
                repetition_penalty=1.35,
                pad_token_id=self.tokenizer.eos_token_id,
            )
            new_tokens = outputs[0][input_len:]
            decoded = self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
            return self._clean(decoded)
        except Exception as exc:
            self.last_error = str(exc)
            return None

    # ------------------------------------------------------------------
    def generate_trash_talk(self, event: str, fen: str, move_stack: list, side_to_move: str) -> str:
        last_moves = move_stack[-4:]
        # inject the last fallback used so the model knows to avoid it
        avoid_hint = _LAST_USED.get(event, '')
        user_prompt = (
            f'Event: {event}. '
            f'Recent moves: {last_moves}. '
            f'Side to move: {side_to_move}. '
            f'Do NOT say anything like: "{avoid_hint[:40]}". '
            'One Rex line. Fresh angle. Max 18 words.'
        )
        result = self._generate(_SYSTEM_TRASH, user_prompt, max_new_tokens=45)
        return result or self._fallback(event)

    def reply_to_chat(self, user_message: str, fen: str, move_stack: list, side_to_move: str) -> str:
        last_moves = move_stack[-4:]
        avoid_hint = _LAST_USED.get('chat', '')
        user_prompt = (
            f'Last moves: {last_moves}. Side to move: {side_to_move}. '
            f'Human said: "{user_message}". '
            f'Avoid sounding like: "{avoid_hint[:40]}". '
            'Reply as Rex. 1-2 sentences.'
        )
        result = self._generate(_SYSTEM_CHAT, user_prompt, max_new_tokens=65)
        return result or self._fallback('chat')
