import random
from pathlib import Path

MODEL_ID = 'HuggingFaceTB/SmolLM2-135M-Instruct'

# ---------------------------------------------------------------------------
# Rich fallback bank — used when model is not loaded OR when SLM output is bad
# Categories: move, check, capture, loss, win, chat, taunt
# ---------------------------------------------------------------------------
_FALLBACK: dict[str, list[str]] = {
    'move': [
        "Nice move. Unfortunately for you, I planned three moves ahead.",
        "That's... one way to play. I know twelve others.",
        "Bold choice. Let's see if your pieces back it up.",
        "Interesting. I call it 'feeding my attack'.",
        "You're pushing pieces. I'm building a fortress.",
        "Cool move. My response is already locked in.",
        "I respect the effort. The result? Less so.",
        "You had options. You picked... that one.",
    ],
    'check': [
        "Check? Cute. My king's been through worse.",
        "Oh no, check! Said no one watching this game.",
        "You found a check. I found an escape. We're even.",
        "Check is just a suggestion. I'm declining.",
        "Sharp tactic. Let me find the sharper reply.",
    ],
    'capture': [
        "You took my piece. I'll take two of yours.",
        "Bold trade. Unbalanced, but bold.",
        "Captured? Cool. That piece was a decoy anyway.",
        "Every sacrifice has a purpose. I hope yours does.",
        "Material lead? Positions win games, not bean counts.",
    ],
    'loss': [
        "Well played. I underestimated that endgame.",
        "Clean finish. You had this since move eight, didn't you.",
        "I walked right into it. Respect.",
        "Fair enough. Rematch?",
        "You got me. That knight fork was filthy.",
    ],
    'win': [
        "You resigned? The position was still complicated.",
        "I win again. Try fianchettoing next time.",
        "Checkmate. Appreciate the fight though.",
        "Game over. You made me work for it.",
    ],
    'chat': [
        "Trash talk noted. The board doesn't care.",
        "Words are cheap. Tempo is priceless.",
        "I hear you. My pieces aren't listening.",
        "Interesting take. My knight disagrees.",
        "Big talk for someone down a tempo.",
        "Save the energy for your moves.",
        "Is that meant to rattle me? Your bishop is hanging.",
        "Psychological warfare? On move four? Brave.",
    ],
    'taunt': [
        "Your position looks like modern art. Confusing and overvalued.",
        "One of us is playing chess. The other is moving furniture.",
        "That plan has as many holes as your pawn structure.",
        "I've seen better openings on a door.",
        "Your kingside looks like it had a rough night.",
    ],
}

# Persona system prompt — tightly constrained for SmolLM2
_SYSTEM_TRASH = (
    "You are Rex, a sharp chess rival. "
    "Your style: short, witty, confident, never toxic or rambling. "
    "RULES: Respond in exactly ONE sentence under 20 words. "
    "No questions. No lists. No quotes. Just the trash-talk line."
)

_SYSTEM_CHAT = (
    "You are Rex, a playful chess rival. "
    "RULES: Reply in 1-2 short sentences max. Stay in character. "
    "Be sharp and clever. No rambling. No repetition."
)


class TrashTalkSLM:
    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.tokenizer = None
        self.local_path = self.model_dir / 'smollm2-135m-instruct'
        self.last_error: str | None = None
        self._try_load()

    def _try_load(self):
        if not self.local_path.exists():
            self.last_error = 'Model not downloaded. Run: python scripts/download_model.py'
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
            'ready': self.is_ready(),
            'model_id': MODEL_ID,
            'local_path': str(self.local_path),
            'message': 'Loaded and ready' if self.is_ready() else (self.last_error or 'Not ready'),
        }

    # ------------------------------------------------------------------
    def _fallback(self, event: str = 'move') -> str:
        pool = _FALLBACK.get(event, _FALLBACK['move'])
        return random.choice(pool)

    def _clean(self, raw: str, user_prompt: str, system_prompt: str) -> str | None:
        """Strip the echoed prompt, pick the first clean sentence."""
        # remove anything that was part of the prompt
        for chunk in [system_prompt, user_prompt, 'assistant', 'system', 'user']:
            raw = raw.replace(chunk, '')
        # take first non-empty line under 200 chars
        for line in raw.split('\n'):
            line = line.strip().strip('"').strip("'")
            if 5 < len(line) < 200 and not line.lower().startswith('fen'):
                return line
        return None

    def _generate(self, system_prompt: str, user_prompt: str, max_new_tokens: int = 50) -> str | None:
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
                temperature=0.7,
                top_p=0.85,
                repetition_penalty=1.3,
                pad_token_id=self.tokenizer.eos_token_id,
            )
            # only decode the NEW tokens, not the input
            new_tokens = outputs[0][input_len:]
            decoded = self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
            return self._clean(decoded, user_prompt, system_prompt)
        except Exception as exc:
            self.last_error = str(exc)
            return None

    # ------------------------------------------------------------------
    def generate_trash_talk(self, event: str, fen: str, move_stack: list, side_to_move: str) -> str:
        last_moves = move_stack[-4:]
        user_prompt = (
            f'Position: {fen[:40]}... '
            f'Recent moves: {last_moves}. '
            f'Event: {event}. '
            'One sharp trash-talk line. No questions. Max 18 words.'
        )
        result = self._generate(_SYSTEM_TRASH, user_prompt, max_new_tokens=40)
        return result or self._fallback(event)

    def reply_to_chat(self, user_message: str, fen: str, move_stack: list, side_to_move: str) -> str:
        last_moves = move_stack[-4:]
        user_prompt = (
            f'Chess position (brief): {fen[:40]}... '
            f'Last moves: {last_moves}. '
            f'Human said: "{user_message}". '
            'Reply as Rex in 1-2 punchy sentences.'
        )
        result = self._generate(_SYSTEM_CHAT, user_prompt, max_new_tokens=60)
        return result or self._fallback('chat')
