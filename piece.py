"""
piece.py — Classe Piece (peça individual) e Player (jogador).
"""
from constants import MPATH, ENTRY, HSTRETCH, CENTER, YARDS, steps_to_px


class Piece:
    """
    Representa uma peça no tabuleiro.

    Estados:
      'home'   — na base, aguardando tirar 6
      'active' — em jogo no tabuleiro
      'done'   — chegou ao centro, fora do jogo

    Passos:
      0-51  → caminho principal  (MPATH[(ENTRY[pid]+steps)%52])
      52-56 → corredor de chegada (HSTRETCH[pid][steps-52])
      57    → centro (done)
    """

    def __init__(self, pid: int, idx: int):
        self.pid   = pid    # id do jogador (0-3)
        self.idx   = idx    # índice dentro do jogador (0-3)
        self.state = "home"
        self.steps = 0

    # ── Propriedades ──────────────────────────────────────────────────────────

    @property
    def grid(self):
        """Retorna (col, row) atual ou None se não estiver ativo."""
        if self.state != "active":
            return None
        if self.steps <= 51:
            return MPATH[(ENTRY[self.pid] + self.steps) % 52]
        hs = self.steps - 52
        if hs < 5:
            return HSTRETCH[self.pid][hs]
        return CENTER

    @property
    def pixel(self):
        """Retorna posição pixel central atual."""
        if self.state == "home":
            return YARDS[self.pid][self.idx]
        if self.state == "done":
            return steps_to_px(self.pid, 57)
        return steps_to_px(self.pid, self.steps)

    # ── Lógica de movimento ───────────────────────────────────────────────────

    def can_move(self, roll: int) -> bool:
        if self.state == "done":
            return False
        if self.state == "home":
            return roll == 6
        return (self.steps + roll) <= 57

    def move(self, roll: int):
        """Aplica o movimento. Se estava em casa, entra no tabuleiro (steps=0)."""
        if self.state == "home":
            self.state = "active"
            self.steps = 0
            return
        self.steps += roll
        if self.steps >= 57:
            self.steps = 57
            self.state = "done"

    def send_home(self):
        """Envia a peça de volta para a base (captura)."""
        self.state = "home"
        self.steps = 0

    def __repr__(self):
        from constants import PN
        return f"Piece({PN[self.pid]}[{self.idx}] {self.state} s={self.steps})"


class Player:
    """
    Representa um jogador com 4 peças.

    Atributos:
      pid   — id (0-3)
      human — True se humano, False se CPU
      done  — True quando todas as peças chegaram ao centro
    """

    def __init__(self, pid: int, human: bool):
        self.pid    = pid
        self.human  = human
        self.pieces = [Piece(pid, i) for i in range(4)]
        self.done   = False

    def movable(self, roll: int) -> list:
        """Retorna lista de peças que podem se mover com este dado."""
        return [p for p in self.pieces if p.can_move(roll)]

    def all_done(self) -> bool:
        return all(p.state == "done" for p in self.pieces)

    def __repr__(self):
        from constants import PN
        return f"Player({PN[self.pid]} {'H' if self.human else 'CPU'})"
