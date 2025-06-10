import random
import time
import itertools

class Board:
    def __init__(self, filename):
        self.filename = filename
        self.board = []
        self.rows = 0
        self.cols = 0
        self.num_mines = 0
        self.revealed = set()
        self.flagged = set()
        self.load_board()

    def load_board(self):
        with open(self.filename, 'r') as f:
            header = f.readline().strip().split()
            if len(header) != 3:
                raise ValueError("First line must be: rows cols num_mines")
            self.rows, self.cols, self.num_mines = map(int, header)
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                if len(parts) != self.cols:
                    raise ValueError(f"Expected {self.cols} cols, got {len(parts)}")
                row = [('*' if v == '*' else int(v)) for v in parts]
                self.board.append(row)
        if len(self.board) != self.rows:
            raise ValueError(f"Expected {self.rows} rows, got {len(self.board)}")

    def print_board(self, reveal_all=False):
        header = '   ' + ' '.join(f"{c:>2}" for c in range(self.cols))
        print(header)
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                if reveal_all or (r, c) in self.revealed:
                    row.append(str(self.board[r][c]).rjust(2))
                elif (r, c) in self.flagged:
                    row.append('F'.rjust(2))
                else:
                    row.append('?'.rjust(2))
            print(str(r).rjust(2), ' '.join(row))

    def reveal(self, r, c):
        if (r, c) in self.revealed or (r, c) in self.flagged:
            return None
        self.revealed.add((r, c))
        return self.board[r][c]

    def flag(self, r, c):
        if (r, c) not in self.revealed:
            self.flagged.add((r, c))

    def apply_move(self, action, r, c):
        if action == 'R':
            if (r, c) in self.flagged:
                return 'flagged_cell'
            res = self.reveal(r, c)
            if res is None:
                return 'already_revealed'
            if res == '*':
                return 'hit_mine'
            return res
        elif action == 'F':
            self.flag(r, c)
            return 'flagged'
        else:
            return 'invalid'

    def is_solved(self):
        return len(self.revealed) == self.rows * self.cols - self.num_mines

class MinesweeperAgent:
    COVERED = 9
    FLAGGED = 10

    def __init__(self, state):
        self.state = [row[:] for row in state]
        self.rows = len(state)
        self.cols = len(state[0])

    def neighbors(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    yield nr, nc

    def propagate(self):
        new_safe, new_mines = set(), set()
        for r in range(self.rows):
            for c in range(self.cols):
                v = self.state[r][c]
                if isinstance(v, int) and 0 <= v <= 8:
                    covered, flagged = [], 0
                    for nr, nc in self.neighbors(r, c):
                        if self.state[nr][nc] == self.COVERED:
                            covered.append((nr, nc))
                        elif self.state[nr][nc] == self.FLAGGED:
                            flagged += 1
                    rem = v - flagged
                    if rem == 0 and covered:
                        new_safe.update(covered)
                    if rem == len(covered) and rem > 0:
                        new_mines.update(covered)
        for (r, c) in new_safe:
            if self.state[r][c] == self.COVERED:
                self.state[r][c] = 'S'
        for (r, c) in new_mines:
            if self.state[r][c] == self.COVERED:
                self.state[r][c] = self.FLAGGED
        return new_safe, new_mines

    def get_forced_actions(self):
        actions = []
        while True:
            safe, mines = self.propagate()
            if not safe and not mines:
                break
            for c in mines:
                actions.append(('F', c[0], c[1], 'forced flag'))
            for c in safe:
                actions.append(('R', c[0], c[1], 'forced reveal'))
        return actions

    def estimate_probabilities(self):
        constraints, frontier = [], set()
        for r in range(self.rows):
            for c in range(self.cols):
                v = self.state[r][c]
                if isinstance(v, int) and 0 <= v <= 8:
                    covered, flagged = [], 0
                    for nr, nc in self.neighbors(r, c):
                        if self.state[nr][nc] == self.COVERED:
                            covered.append((nr, nc))
                        elif self.state[nr][nc] == self.FLAGGED:
                            flagged += 1
                    if covered:
                        frontier.update(covered)
                        constraints.append((covered, v - flagged))
        frontier = list(frontier)
        n = len(frontier)
        if n > 20:
            raise NotImplementedError
        counts = {cell: 0 for cell in frontier}
        total = 0
        for bits in itertools.product([0, 1], repeat=n):
            assign = dict(zip(frontier, bits))
            if all(sum(assign[cell] for cell in cells) == req for cells, req in constraints):
                total += 1
                for cell, val in assign.items():
                    counts[cell] += val
        return {cell: (counts[cell] / total if total else 0) for cell in frontier}

    # ------------------ New Assumption-based Inference ------------------
    def number_of_assumptions(self, unopened, mines_left):
        from math import comb
        return comb(unopened, mines_left)

    def combine(self, cells, board):
        prio = {}
        for cell in cells:
            unopened, mines_left = self.get_bomb_left(cell[0], cell[1])
            combos = self.number_of_assumptions(unopened, mines_left)
            if combos <= 10:
                prio[cell] = combos
        return prio or None

    def get_bomb_left(self, r, c):
        unopened = 0
        flagged = 0
        for nr, nc in self.neighbors(r, c):
            if self.state[nr][nc] == self.COVERED:
                unopened += 1
            elif self.state[nr][nc] == self.FLAGGED:
                flagged += 1
        mines_left = self.state[r][c] - flagged
        return unopened, mines_left

    def assumption_actions(self):
        # Pick a number cell with small combination of its covered neighbors
        from math import comb
        candidates = {}
        # Gather numeric clue cells adjacent to covered cells
        for r in range(self.rows):
            for c in range(self.cols):
                v = self.state[r][c]
                if isinstance(v, int) and 0 <= v <= 8:
                    covered = []
                    flagged = 0
                    for nr, nc in self.neighbors(r, c):
                        if self.state[nr][nc] == self.COVERED:
                            covered.append((nr, nc))
                        elif self.state[nr][nc] == self.FLAGGED:
                            flagged += 1
                    mines_left = v - flagged
                    unopened = len(covered)
                    if 0 < mines_left <= unopened:
                        try:
                            combos = comb(unopened, mines_left)
                        except ValueError:
                            continue
                        if combos <= 10:
                            candidates[(r, c)] = (combos, covered, mines_left)
        if not candidates:
            return []
        # Choose the clue cell with fewest possibilities
        cell, (combos, covered, mines_left) = min(candidates.items(), key=lambda kv: kv[1][0])
        # Generate patterns of mines (-1) vs safe (0)
        patterns = [bits for bits in itertools.product([-1, 0], repeat=len(covered))
                    if sum(1 for b in bits if b == -1) == mines_left]
        # Aggregate neighbor outcomes
        counts = {nbr: [] for nbr in covered}
        for pat in patterns:
            for val, nbr in zip(pat, covered):
                counts[nbr].append(val)
        # Propose actions where all patterns agree
        actions = []
        for nbr, vals in counts.items():
            if all(v == -1 for v in vals):
                actions.append(('F', nbr[0], nbr[1], 'assume'))
            if all(v == 0 for v in vals):
                actions.append(('R', nbr[0], nbr[1], 'assume'))
        # Filter out any on non-covered
        filtered = [(act, r, c, reason)
                    for act, r, c, reason in actions
                    if self.state[r][c] == self.COVERED]
        return filtered

    def next_move(self):
        forced = self.get_forced_actions()
        if forced:
            return forced
        try:
            probs = self.estimate_probabilities()
        except NotImplementedError:
            probs = {}
        for cell, p in probs.items():
            if p == 1.0:
                return [('F', cell[0], cell[1], f'prob={p:.2f}')]
        if probs:
            min_p = min(probs.values())
            best = [c for c, p in probs.items() if p == min_p]
            choice = random.choice(best)
            return [('R', choice[0], choice[1], f'prob={min_p:.2f}')]
        assume = self.assumption_actions()
        if assume:
            return assume
        covered = [(r, c) for r in range(self.rows) for c in range(self.cols)
                   if self.state[r][c] == self.COVERED]
        if covered:
            choice = random.choice(covered)
            return [('R', choice[0], choice[1], 'random')]
        return []


def get_csp_state(board):
    state = []
    for r in range(board.rows):
        row = []
        for c in range(board.cols):
            if (r, c) in board.flagged:
                row.append(MinesweeperAgent.FLAGGED)
            elif (r, c) in board.revealed:
                v = board.board[r][c]
                row.append(v if isinstance(v, int) else MinesweeperAgent.COVERED)
            else:
                row.append(MinesweeperAgent.COVERED)
        state.append(row)
    return state


def solve_ai(board):
    import random as _rand, copy as _copy
    # Simulate pure-random playouts to estimate safety of a guess

    def monte_carlo_select(original_board, covered, trials=5):
        best_cell = None
        best_score = -1
        for cell in covered:
            wins = 0
            for _ in range(trials):
                b = Board(original_board.filename)
                b.revealed = set(original_board.revealed)
                b.flagged = set(original_board.flagged)
                # first move
                res = b.apply_move('R', cell[0], cell[1])
                if res == 'hit_mine':
                    continue
                # random playout
                while not b.is_solved():
                    all_cov = [(r, c) for r in range(b.rows) for c in range(b.cols)
                               if (r, c) not in b.revealed and (r, c) not in b.flagged]
                    if not all_cov:
                        break
                    pick = _rand.choice(all_cov)
                    res2 = b.apply_move('R', pick[0], pick[1])
                    if res2 == 'hit_mine':
                        break
                else:
                    wins += 1
            if wins > best_score:
                best_score = wins
                best_cell = cell
        return best_cell

    move_count = 0
    print("AI solving...")
    while not board.is_solved():
        state = get_csp_state(board)
        actions = MinesweeperAgent(state).next_move()
        # intercept pure random guess and improve via Monte Carlo
        if len(actions) == 1 and actions[0][3] == 'random':
            covered = [(r, c) for r in range(board.rows) for c in range(board.cols)
                       if (r, c) not in board.revealed and (r, c) not in board.flagged]
            choice = monte_carlo_select(board, covered, trials=5)
            actions = [('R', choice[0], choice[1], 'monte_carlo')]
        if not actions:
            print("No moves available, stopping.")
            break
        for act, r, c, reason in actions:
            move_count += 1
            # print(f"=== AI Move {move_count} ===")
            # print(f"Action: {act} at ({r}, {c}),  Reason: {reason}")
            res = board.apply_move(act, r, c)
            # print(f"Result: {res}")
            # print("Board after move:")
            # board.print_board()
            # print()
            # time.sleep(.2)
            if res == 'hit_mine':
                # print("AI hit a mine. Game over.")
                # print(f"Total moves: {move_count}")
                return
    if board.is_solved():
        # print("AI solved the board!")
        # print(f"Total moves: {move_count}")
        return

if __name__ == '__main__':
    fn = input("Enter board filename: ")
    b = Board(fn)
    safe_tiles = [(r, c) for r in range(b.rows)
                  for c in range(b.cols)
                  if not b.is_mine(r, c) and b.board[r][c] == 0]
    mode = input("Choose mode: (M)anual or (A)I solve: ").strip().upper()
    if mode == 'M':
        first = random.choice(safe_tiles)
        b.reveal(*first)
        print(f"First move: revealed a safe tile at {first}.")
    elif mode == 'A':
        first = random.choice(safe_tiles)
        b.reveal(*first)
        print(f"First move: revealed a safe tile at {first}.")
        solve_ai(b)
    else:
        print("Unknown mode.\n")
