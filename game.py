"""
game.py — Lógica central do jogo (Game).

Fases:
  'roll'   — aguardando rolar o dado (humano: ESPAÇO; CPU: automático)
  'pick'   — humano escolhe qual peça mover
  'aipick' — CPU escolhe automaticamente
  'anim'   — animação da peça se movendo
  'wait'   — sem movimentos possíveis, passando a vez
  'end'    — partida encerrada
"""
import random
from constants import MPATH, ENTRY, HSTRETCH, SAFE, PN, YARDS, steps_to_px, gpx


class Game:
    def __init__(self, players):
        self.players    = players
        self.n          = len(players)
        self.turn       = 0
        self.roll       = None
        self.phase      = "roll"
        self.movable    = []
        self.extra_turn = False
        self.rankings   = []   # pids na ordem de chegada
        self.msg        = ""

        # Dado animado
        self.dice_spin  = 0    # frames restantes de animação
        self.dice_show  = 1    # valor exibido durante spin
        self.dice_final = 1    # valor sorteado

        # Animação de peça
        self.anim_piece = None
        self.anim_path  = []   # lista de (px, py)
        self.anim_step  = 0
        self.anim_timer = 0    # ms acumulados no step atual

        # Espera da CPU
        self.ai_wait = 1000    # ms

    # ── Acessores ─────────────────────────────────────────────────────────────

    def cp(self):
        return self.players[self.turn]

    # ── Dado ──────────────────────────────────────────────────────────────────

    def start_roll(self):
        """Inicia a animação do dado e sorteia o resultado."""
        self.dice_final = random.randint(1, 6)
        self.dice_spin  = 28   # ~0.5 s a 60 fps

    def _finish_roll(self):
        self.roll      = self.dice_final
        self.dice_show = self.dice_final
        cp             = self.cp()
        self.movable   = cp.movable(self.roll)

        if not self.movable:
            self.msg   = f"{PN[cp.pid]}: sem movimentos — vez passada."
            self.phase = "wait"
            self.ai_wait = 1300
        else:
            self.msg = (f"{PN[cp.pid]} tirou {self.roll}!"
                        + (" Joga de novo!" if self.roll == 6 else ""))
            if self.roll == 6:
                self.extra_turn = True
            self.phase   = "aipick" if not cp.human else "pick"
            self.ai_wait = 700

    # ── Movimento ─────────────────────────────────────────────────────────────

    def pick(self, piece):
        """Inicia a animação de movimento para a peça escolhida."""
        self.anim_piece = piece
        self.anim_path  = self._build_anim(piece, self.roll)
        self.anim_step  = 0
        self.anim_timer = 0
        self.phase      = "anim"

    def _build_anim(self, piece, roll):
        """Constrói lista de pixels para a animação passo a passo."""
        pts = []
        if piece.state == "home":
            pts.append(YARDS[piece.pid][piece.idx])   # posição no yard
            pts.append(steps_to_px(piece.pid, 0))     # casa de entrada
            return pts
        for s in range(1, roll + 1):
            ns = min(piece.steps + s, 57)
            pts.append(steps_to_px(piece.pid, ns))
        return pts

    def apply_move(self):
        """Aplica o movimento, verifica captura e vitória."""
        piece = self.anim_piece
        cp    = self.cp()
        piece.move(self.roll)

        # Captura
        if piece.state == "active" and piece.steps <= 51:
            gp = piece.grid
            if gp and gp not in SAFE:
                for pl in self.players:
                    if pl.pid == cp.pid:
                        continue
                    for op in pl.pieces:
                        if op.state == "active" and op.grid == gp:
                            op.send_home()
                            self.extra_turn = True
                            self.msg = (f"💥 {PN[cp.pid]} capturou "
                                        f"{PN[pl.pid]}!")

        # Verificar vitória do jogador
        if cp.all_done() and not cp.done:
            cp.done = True
            self.rankings.append(cp.pid)
            active_left = [p for p in self.players if not p.done]
            if len(active_left) <= 1:
                if active_left:
                    self.rankings.append(active_left[0].pid)
                self.phase      = "end"
                self.anim_piece = None
                return

        self.anim_piece = None
        self._next()

    def _next(self):
        """Avança para o próximo turno."""
        if not self.extra_turn:
            for _ in range(self.n):
                self.turn = (self.turn + 1) % self.n
                if not self.players[self.turn].done:
                    break
        self.extra_turn = False
        self.roll       = None
        self.phase      = "roll"
        self.movable    = []
        self.ai_wait    = 800

    # ── IA ────────────────────────────────────────────────────────────────────

    def ai_choose(self):
        """
        Estratégia da CPU (ordem de prioridade):
          1. Capturar adversário
          2. Entrar no corredor de chegada
          3. Entrar em jogo (sair do yard)
          4. Mover a peça mais avançada
        """
        m  = self.movable
        cp = self.cp()

        # 1. Captura
        for p in m:
            if p.state == "active" and p.steps <= 51:
                ns = p.steps + self.roll
                if ns <= 51:
                    ng = MPATH[(ENTRY[cp.pid] + ns) % 52]
                    for pl in self.players:
                        if pl.pid == cp.pid:
                            continue
                        for op in pl.pieces:
                            if (op.state == "active"
                                    and op.grid == ng
                                    and ng not in SAFE):
                                return p

        # 2. Entrar no corredor de chegada
        for p in m:
            if p.state == "active" and (p.steps + self.roll) >= 52:
                return p

        # 3. Sair do yard
        for p in m:
            if p.state == "home":
                return p

        # 4. Peça mais avançada
        active = [p for p in m if p.state == "active"]
        if active:
            return max(active, key=lambda p: p.steps)

        return m[0]

    # ── Update (chamado a cada frame) ─────────────────────────────────────────

    def update(self, dt: int):
        """
        dt: delta time em ms desde o último frame.
        """
        if self.phase == "end":
            return

        # Dado girando
        if self.dice_spin > 0:
            self.dice_spin -= 1
            self.dice_show = random.randint(1, 6)
            if self.dice_spin == 0:
                self._finish_roll()
            return

        # Animação de peça
        if self.phase == "anim" and self.anim_piece:
            self.anim_timer += dt
            if self.anim_timer >= 130:
                self.anim_timer = 0
                self.anim_step += 1
                if self.anim_step >= len(self.anim_path):
                    self.apply_move()
            return

        # Passando vez (sem movimentos)
        if self.phase == "wait":
            self.ai_wait -= dt
            if self.ai_wait <= 0:
                self.ai_wait = 0
                self._next()
            return

        # CPU rola dado
        if self.phase == "roll" and not self.cp().human:
            self.ai_wait -= dt
            if self.ai_wait <= 0:
                self.ai_wait = 0
                self.start_roll()
            return

        # CPU escolhe peça
        if self.phase == "aipick":
            self.ai_wait -= dt
            if self.ai_wait <= 0:
                self.ai_wait = 0
                self.pick(self.ai_choose())
            return

    # ── Input do humano ───────────────────────────────────────────────────────

    def click(self, mx: int, my: int):
        """Processa clique do mouse para selecionar peça."""
        if self.phase != "pick":
            return
        HALF = CELL_HIT = 22   # raio de clique em pixels
        from constants import CELL
        HALF = CELL // 2 + 2
        for p in self.movable:
            if p.state == "home":
                hx, hy = YARDS[p.pid][p.idx]
            elif p.state == "active":
                g = p.grid
                if not g:
                    continue
                hx, hy = gpx(*g)
            else:
                continue
            if abs(mx - hx) < HALF and abs(my - hy) < HALF:
                self.pick(p)
                return
