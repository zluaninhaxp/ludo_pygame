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
      0-50  → caminho principal
      51-55 → corredor de chegada colorido
      56    → centro (vitória)
    """

    def __init__(self, pid: int, idx: int):
        self.pid   = pid    # id do jogador (0-3)
        self.idx   = idx    # índice dentro do jogador (0-3)
        self.state = "home"
        self.steps = 0

    @property
    def grid(self):
        if self.state != "active":
            return None
        if self.steps <= 50:
            return MPATH[(ENTRY[self.pid] + self.steps) % 52]
        hs = self.steps - 51
        if hs < 5:
            return HSTRETCH[self.pid][hs]
        return CENTER

    @property
    def pixel(self):
        if self.state == "home":
            return YARDS[self.pid][self.idx]
        if self.state == "done":
            return steps_to_px(self.pid, 56)
        return steps_to_px(self.pid, self.steps)

    def can_move(self, roll: int) -> bool:
        if self.state == "done":
            return False
        if self.state == "home":
            return roll == 6
        return (self.steps + roll) <= 56

    def move(self, roll: int):
        if self.state == "home":
            self.state = "active"
            self.steps = 0
            return
        self.steps += roll
        if self.steps >= 56:
            self.steps = 56
            self.state = "done"

    def send_home(self):
        self.state = "home"
        self.steps = 0

    def __repr__(self):
        from constants import PN
        return f"Piece({PN[self.pid]}[{self.idx}] {self.state} s={self.steps})"


class Player:
    def __init__(self, pid: int, human: bool):
        self.pid    = pid
        self.human  = human
        self.pieces = [Piece(pid, i) for i in range(4)]
        self.done   = False

    def movable(self, roll: int) -> list:
        return [p for p in self.pieces if p.can_move(roll)]

    def all_done(self) -> bool:
        return all(p.state == "done" for p in self.pieces)

    def __repr__(self):
        from constants import PN
        return f"Player({PN[self.pid]} {'H' if self.human else 'CPU'})"