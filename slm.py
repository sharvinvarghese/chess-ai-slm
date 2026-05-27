from pathlib import Path

MODEL_ID = 'HuggingFaceTB/SmolLM2-135M-Instruct'

_FALLBACK = {
    'move':  ['Nice move. I still like my position though.',
              'You are pushing pieces. I am pushing a plan.',
              'That move had courage. Let us see if it had calculation.'],
    'check': ['Check? Cute. I am still in this.',
              'You found a tactic. Respect.',
              'Sharp move. I noticed a little late.'],
    'loss':  ['Well played. I will remember this line.',
              'You got me. Clean finish.',
              'That was stronger than I expected.'],
    'chat':  ['I hear you. The board still matters more.',
              'Talk is cheap. Tempo is priceless.',
              'Interesting words. Show me better moves.'],
}


class TrashTalkSLM:
    def __init__(self, model_dir: Path):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.tokenizer = None
        self.local_path = self.model_dir / 'smollm2-135m-instruct'
        self.last_error = None
        self._try_load()

    def _try_load(self):
        if not self.local_path.exists():
            self.last_error = 'Model not downloaded. Run: python scripts/download_model.py'
            return
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.local_path))
            self.model = AutoModelForCausalLM.from_pretrained(str(self.local_path))
        except Exception as exc:
            self.last_error = str(exc)
            self.model = None
            self.tokenizer = None

    def is_ready(self):
        return self.model is not None and self.tokenizer is not None

    def status(self):
        return {
            'ready': self.is_ready(),
            'model_id': MODEL_ID,
            'local_path': str(self.local_path),
            'message': 'Loaded and ready' if self.is_ready() else (self.last_error or 'Not ready'),
        }

    def _fallback(self, event='move'):
        import random
        pool = _FALLBACK.get(event, _FALLBACK['move'])
        return random.choice(pool)

    def _generate(self, system_prompt, user_prompt, max_new_tokens=60):
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
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.8,
                top_p=0.9,
            )
            decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            if decoded.startswith(text):
                decoded = decoded[len(text):].strip()
            return decoded.strip() or None
        except Exception as exc:
            self.last_error = str(exc)
            return None

    def generate_trash_talk(self, event, fen, move_stack, side_to_move):
        prompt = (
            f'FEN: {fen}\n'
            f'Last 8 moves: {move_stack[-8:]}\n'
            f'Side to move: {side_to_move}\n'
            f'Event: {event}\n'
            'Give one short witty trash-talk line as the chess opponent (max 20 words).'
        )
        reply = self._generate(
            system_prompt='You are a witty chess rival. Keep replies short, sharp, and not toxic.',
            user_prompt=prompt,
            max_new_tokens=40,
        )
        return reply or self._fallback(event)

    def reply_to_chat(self, user_message, fen, move_stack, side_to_move):
        prompt = (
            f'FEN: {fen}\n'
            f'Last 8 moves: {move_stack[-8:]}\n'
            f'Side to move: {side_to_move}\n'
            f'User said: "{user_message}"\n'
            'Reply in 1-2 short sentences as a playful chess rival.'
        )
        reply = self._generate(
            system_prompt='You are a local chess persona. Be concise, playful, and sharp.',
            user_prompt=prompt,
            max_new_tokens=70,
        )
        return reply or self._fallback('chat')
