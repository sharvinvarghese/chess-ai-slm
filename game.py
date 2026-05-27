import random
import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

PIECE_SYMBOLS = {
    'P': '\u2659', 'N': '\u2658', 'B': '\u2657', 'R': '\u2656', 'Q': '\u2655', 'K': '\u2654',
    'p': '\u265f', 'n': '\u265e', 'b': '\u265d', 'r': '\u265c', 'q': '\u265b', 'k': '\u265a',
}


class ChessGame:
    def __init__(self):
        self.board = chess.Board()
        self.ai_level = 2

    def reset(self):
        self.board.reset()

    def board_payload(self):
        squares = []
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            squares.append({
                'name': chess.square_name(square),
                'piece': piece.symbol() if piece else None,
                'unicode': PIECE_SYMBOLS.get(piece.symbol()) if piece else None,
                'color': 'white' if piece and piece.color == chess.WHITE else ('black' if piece else None)
            })
        return squares

    def legal_moves_from(self, square_name):
        sq = chess.parse_square(square_name)
        return [m.uci() for m in self.board.legal_moves if m.from_square == sq]

    def state_payload(self):
        return {
            'fen': self.board.fen(),
            'turn': 'white' if self.board.turn == chess.WHITE else 'black',
            'board': self.board_payload(),
            'legal_moves': [m.uci() for m in self.board.legal_moves],
            'check': self.board.is_check(),
            'checkmate': self.board.is_checkmate(),
            'stalemate': self.board.is_stalemate(),
            'insufficient_material': self.board.is_insufficient_material(),
            'game_over': self.board.is_game_over(),
            'result': self.board.result() if self.board.is_game_over() else None,
            'san_moves': self.san_history(),
            'move_count': len(self.board.move_stack),
        }

    def san_history(self):
        replay = chess.Board()
        sans = []
        for move in self.board.move_stack:
            sans.append(replay.san(move))
            replay.push(move)
        return sans

    def player_move(self, move_uci):
        try:
            move = chess.Move.from_uci(move_uci)
        except ValueError:
            return {'ok': False, 'error': 'Invalid move format.'}
        if move not in self.board.legal_moves:
            return {'ok': False, 'error': 'Illegal move for current position.'}
        san = self.board.san(move)
        self.board.push(move)
        return {
            'ok': True,
            'player_move': move_uci,
            'player_san': san,
            'state': self.state_payload()
        }

    def ai_move(self):
        if self.board.is_game_over():
            return {'ok': False, 'error': 'Game is already over.', 'state': self.state_payload()}
        if self.board.turn != chess.BLACK:
            return {'ok': False, 'error': 'AI moves only for black.', 'state': self.state_payload()}
        move = self._choose_ai_move()
        if move is None:
            return {'ok': False, 'error': 'No legal AI move found.', 'state': self.state_payload()}
        san = self.board.san(move)
        self.board.push(move)
        return {
            'ok': True,
            'ai_move': move.uci(),
            'ai_san': san,
            'state': self.state_payload()
        }

    def _choose_ai_move(self):
        depth_map = {1: 1, 2: 2, 3: 2, 4: 3}
        depth = depth_map.get(self.ai_level, 2)
        best_score = 10 ** 9
        best_moves = []
        for move in self.board.legal_moves:
            self.board.push(move)
            score = self._minimax(depth - 1, -(10 ** 9), 10 ** 9, maximizing=True)
            self.board.pop()
            if score < best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        return random.choice(best_moves) if best_moves else None

    def _minimax(self, depth, alpha, beta, maximizing):
        if depth == 0 or self.board.is_game_over():
            return self._evaluate()
        if maximizing:
            value = -(10 ** 9)
            for move in self.board.legal_moves:
                self.board.push(move)
                value = max(value, self._minimax(depth - 1, alpha, beta, False))
                self.board.pop()
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        value = 10 ** 9
        for move in self.board.legal_moves:
            self.board.push(move)
            value = min(value, self._minimax(depth - 1, alpha, beta, True))
            self.board.pop()
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

    def _evaluate(self):
        if self.board.is_checkmate():
            return -999999 if self.board.turn == chess.WHITE else 999999
        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0
        score = 0
        for piece_type, value in PIECE_VALUES.items():
            score += len(self.board.pieces(piece_type, chess.WHITE)) * value
            score -= len(self.board.pieces(piece_type, chess.BLACK)) * value
        return score
