"""
game.py — Lógica central do jogo (Game).
"""
import random
import constants as C
from constants import MPATH, ENTRY, HSTRETCH, SAFE, PN, PLAYER_DISPLAY_NAMES

def _pname(pid):
    return PLAYER_DISPLAY_NAMES.get(pid, PN[pid])

class Game:
    def __init__(self, players):
        self.players    = players
        self.n          = len(players)
        self.turn       = 0
        self.roll       = None
        self.phase      = "roll"
        self.movable    = []
        self.extra_turn = False
        self.rankings   = []
        self.msg        = ""

        self.dice_spin  = 0
        self.dice_show  = 1
        self.dice_final = 1

        self.anim_piece = None
        self.anim_path  = []
        self.anim_step  = 0
        self.anim_timer = 0
        self.captures_queue = [] 
        
        # NOVO: Sistema de partículas para o confete!
        self.particles  = [] 

        self.ai_wait = 1000

    def cp(self):
        return self.players[self.turn]

    def start_roll(self):
        self.dice_final = random.randint(1, 6)
        self.dice_spin  = 28

    def _finish_roll(self):
        self.roll      = self.dice_final
        self.dice_show = self.dice_final
        cp             = self.cp()
        self.movable   = cp.movable(self.roll)

        if not self.movable:
            self.msg   = f"{_pname(cp.pid)}: sem movimentos — vez passada."
            self.phase = "wait"
            self.ai_wait = 1300
        else:
            self.msg = (f"{_pname(cp.pid)} tirou {self.roll}!"
                        + (" Joga de novo!" if self.roll == 6 else ""))
            if self.roll == 6:
                self.extra_turn = True
            self.phase   = "aipick" if not cp.human else "pick"
            self.ai_wait = 700

    def pick(self, piece):
        self.anim_piece = piece
        self.anim_path  = self._build_anim(piece, self.roll)
        self.anim_step  = 0
        self.anim_timer = 0
        self.phase      = "anim"

    def _build_anim(self, piece, roll):
        pts = []
        if piece.state == "home":
            pts.append(C.YARDS[piece.pid][piece.idx])
            pts.append(C.steps_to_px(piece.pid, 0))
            return pts
            
        pts.append(C.steps_to_px(piece.pid, piece.steps))
        
        for s in range(1, roll + 1):
            ns = min(piece.steps + s, 56)
            pts.append(C.steps_to_px(piece.pid, ns))
        return pts

    # NOVO: Gatilho de Confetes
    def spawn_confetti(self):
        cx, cy = C.gpx(*C.CENTER)
        colors = [C.PC[0], C.PC[1], C.PC[2], C.PC[3], C.WHITE, (255, 150, 50), (50, 200, 255)]
        # Gera 60 pedacinhos de papel com gravidade e direções aleatórias
        for _ in range(60): 
            sx = random.uniform(-6, 6)
            sy = random.uniform(-12, -3) # Explosão forte para cima
            size = random.randint(6, 12)
            life = random.randint(60, 120)
            color = random.choice(colors)
            self.particles.append([cx, cy, sx, sy, color, size, life])

    def apply_move(self):
        piece = self.anim_piece
        cp    = self.cp()
        piece.move(self.roll)

        # Dispara o confete se a peça acabou de chegar no centro!
        if piece.state == "done":
            self.spawn_confetti()

        captured_pieces = []
        if piece.state == "active" and piece.steps <= 50:
            gp = piece.grid
            if gp and gp not in SAFE:
                for pl in self.players:
                    if pl.pid == cp.pid:
                        continue
                    for op in pl.pieces:
                        if op.state == "active" and op.grid == gp:
                            captured_pieces.append(op)

        if captured_pieces:
            self.extra_turn = True
            p_names = ", ".join([_pname(op.pid) for op in captured_pieces])
            self.msg = f"💥 {_pname(cp.pid)} capturou {p_names}!"
            self.captures_queue = captured_pieces
            self._start_next_capture()
        else:
            self._finalize_turn()

    def _start_next_capture(self):
        if not self.captures_queue:
            self._finalize_turn()
            return

        op = self.captures_queue.pop(0)
        self.anim_piece = op
        start_px = C.gpx(*op.grid) 
        end_px = C.YARDS[op.pid][op.idx] 
        
        self.anim_path = [start_px, end_px]
        self.anim_step = 0
        self.anim_timer = 0
        self.phase = "anim_capture"

    def _finalize_turn(self):
        cp = self.cp()
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

    def ai_choose(self):
        m  = self.movable
        cp = self.cp()

        for p in m:
            if p.state == "active" and p.steps <= 50:
                ns = p.steps + self.roll
                if ns <= 50:
                    ng = MPATH[(ENTRY[cp.pid] + ns) % 52]
                    for pl in self.players:
                        if pl.pid == cp.pid:
                            continue
                        for op in pl.pieces:
                            if (op.state == "active"
                                    and op.grid == ng
                                    and ng not in SAFE):
                                return p

        for p in m:
            if p.state == "active" and (p.steps + self.roll) >= 51:
                return p

        for p in m:
            if p.state == "home":
                return p

        active = [p for p in m if p.state == "active"]
        if active:
            return max(active, key=lambda p: p.steps)

        return m[0]

    def update(self, dt: int):
        # NOVO: Física dos confetes caindo
        for p in getattr(self, 'particles', []):
            p[0] += p[2]  # X soma a velocidade X
            p[1] += p[3]  # Y soma a velocidade Y
            p[3] += 0.35  # Gravidade (puxa o confete para baixo)
            p[6] -= 1     # Perde tempo de vida
        # Remove os confetes que já "morreram"
        self.particles = [p for p in getattr(self, 'particles', []) if p[6] > 0]

        if self.phase == "end":
            return

        if self.dice_spin > 0:
            self.dice_spin -= 1
            self.dice_show = random.randint(1, 6)
            if self.dice_spin == 0:
                self._finish_roll()
            return

        if self.phase == "anim" and self.anim_piece:
            self.anim_timer += dt
            if self.anim_timer >= 200:
                self.anim_timer = 0
                self.anim_step += 1
                if self.anim_step >= len(self.anim_path) - 1:
                    self.apply_move()
            return

        if self.phase == "anim_capture" and self.anim_piece:
            self.anim_timer += dt
            if self.anim_timer >= 500:
                self.anim_timer = 0
                self.anim_step += 1
                if self.anim_step >= len(self.anim_path) - 1:
                    self.anim_piece.send_home()
                    self._start_next_capture() 
            return

        if self.phase == "wait":
            self.ai_wait -= dt
            if self.ai_wait <= 0:
                self.ai_wait = 0
                self._next()
            return

        if self.phase == "roll" and not self.cp().human:
            self.ai_wait -= dt
            if self.ai_wait <= 0:
                self.ai_wait = 0
                self.start_roll()
            return

        if self.phase == "aipick":
            self.ai_wait -= dt
            if self.ai_wait <= 0:
                self.ai_wait = 0
                self.pick(self.ai_choose())
            return

    def click(self, mx: int, my: int):
        if self.phase != "pick":
            return
        HALF = C.CELL // 2 + 2
        for p in self.movable:
            if p.state == "home":
                hx, hy = C.YARDS[p.pid][p.idx]
            elif p.state == "active":
                g = p.grid
                if not g:
                    continue
                hx, hy = C.gpx(*g)
            else:
                continue
            if abs(mx - hx) < HALF and abs(my - hy) < HALF:
                self.pick(p)
                return