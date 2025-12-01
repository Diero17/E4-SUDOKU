from __future__ import annotations

import random
from datetime import datetime
from typing import Optional, Tuple, List

from sudoku_board import SudokuBoard
from validator import Validator
from genetic import GeneticEngine, GeneticParams
from metrics import MetricsHistory, RunMetrics
from io_board import BoardIO


class SudokuController:
    DIFFICULTY_RANGES_9X9 = {
        "facil": (36, 40),
        "medio": (28, 32),
        "dificil": (22, 26),
    }

    def __init__(self):
        self.current_board: Optional[SudokuBoard] = None
        self.initial_board: Optional[SudokuBoard] = None
        self.solution_board: Optional[SudokuBoard] = None
        self.difficulty: Optional[str] = None
        self.params = GeneticParams()
        self.metrics_history = MetricsHistory()

    # ---------- utilidades internas ----------
    @staticmethod
    def _compute_difficulty_range(size: int, difficulty: str) -> Tuple[int, int]:
        """Escala los rangos definidos para 9x9 a 4x4 y 6x6 manteniendo la proporción."""
        diff = difficulty.lower()
        if diff not in SudokuController.DIFFICULTY_RANGES_9X9:
            raise ValueError("Dificultad inválida. Use: facil, medio, dificil.")
        min9, max9 = SudokuController.DIFFICULTY_RANGES_9X9[diff]
        total9 = 9 * 9
        ratio_min = min9 / total9
        ratio_max = max9 / total9
        total = size * size
        min_size = max(1, round(ratio_min * total))
        max_size = max(min_size, round(ratio_max * total))
        return min_size, max_size

    @staticmethod
    def _base_solved_board(size: int) -> SudokuBoard:
        """Devuelve un tablero completo válido para el tamaño dado."""
        if size == 4:
            base = [
                [1, 2, 3, 4],
                [3, 4, 1, 2],
                [2, 1, 4, 3],
                [4, 3, 2, 1],
            ]
        elif size == 6:
            base = [
                [1, 2, 3, 4, 5, 6],
                [4, 5, 6, 1, 2, 3],
                [2, 3, 4, 5, 6, 1],
                [5, 6, 1, 2, 3, 4],
                [3, 4, 5, 6, 1, 2],
                [6, 1, 2, 3, 4, 5],
            ]
        elif size == 9:
            base = [
                [1, 2, 3, 4, 5, 6, 7, 8, 9],
                [4, 5, 6, 7, 8, 9, 1, 2, 3],
                [7, 8, 9, 1, 2, 3, 4, 5, 6],
                [2, 3, 4, 5, 6, 7, 8, 9, 1],
                [5, 6, 7, 8, 9, 1, 2, 3, 4],
                [8, 9, 1, 2, 3, 4, 5, 6, 7],
                [3, 4, 5, 6, 7, 8, 9, 1, 2],
                [6, 7, 8, 9, 1, 2, 3, 4, 5],
                [9, 1, 2, 3, 4, 5, 6, 7, 8],
            ]
        else:
            raise ValueError("Tamaño no soportado")
        return SudokuBoard.from_list(base)

    @staticmethod
    def _shuffle_board(board: SudokuBoard) -> SudokuBoard:
        """Aplica permutaciones válidas para obtener un tablero distinto pero correcto."""
        size = board.size
        b = board.copy()

        sg_r, sg_c = b.subgrid_size()

        # permutar filas dentro de cada bloque de subcuadrícula vertical
        for block in range(0, size, sg_r):
            rows = list(range(block, block + sg_r))
            random.shuffle(rows)
            tmp = [b.grid[r][:] for r in rows]
            for i, r in enumerate(range(block, block + sg_r)):
                b.grid[r] = tmp[i]

        # permutar columnas dentro de cada bloque de subcuadrícula horizontal
        for block in range(0, size, sg_c):
            cols = list(range(block, block + sg_c))
            random.shuffle(cols)
            for r in range(size):
                row = b.grid[r]
                tmp = [row[c] for c in cols]
                for i, c in enumerate(range(block, block + sg_c)):
                    row[c] = tmp[i]

        # permutar símbolos (1..size)
        mapping = list(range(1, size + 1))
        random.shuffle(mapping)
        mapping_dict = {i + 1: mapping[i] for i in range(size)}
        for r in range(size):
            for c in range(size):
                v = b.grid[r][c]
                if v != 0:
                    b.grid[r][c] = mapping_dict[v]

        return b

    # ---------- API de generación ----------
    def generate_puzzle(self, size: int, difficulty: str) -> SudokuBoard:
        base = self._base_solved_board(size)
        solution = self._shuffle_board(base)
        min_clues, max_clues = self._compute_difficulty_range(size, difficulty)
        total_cells = size * size
        num_clues = random.randint(min_clues, max_clues)

        puzzle_grid = [row[:] for row in solution.grid]
        positions = [(r, c) for r in range(size) for c in range(size)]
        random.shuffle(positions)
        cells_to_remove = total_cells - num_clues
        for (r, c) in positions:
            if cells_to_remove <= 0:
                break
            puzzle_grid[r][c] = 0
            cells_to_remove -= 1

        puzzle = SudokuBoard.from_list(puzzle_grid)
        self.initial_board = puzzle.copy()
        self.current_board = puzzle
        self.solution_board = solution
        self.difficulty = difficulty.lower()
        return puzzle

    # ---------- API de carga/guardado ----------
    def load_board_from_file(self, path: str) -> SudokuBoard:
        board = BoardIO.load_board(path)
        self.initial_board = board.copy()
        self.current_board = board
        self.solution_board = None
        self.difficulty = None
        return board

    def save_current_board(self, path: str) -> None:
        if not self.current_board:
            raise RuntimeError("No hay tablero cargado")
        BoardIO.save_board(self.current_board, path)

    # ---------- Juego interactivo ----------
    def reset_board(self) -> None:
        if not self.initial_board:
            raise RuntimeError("No hay tablero inicial")
        self.current_board = self.initial_board.copy()

    def apply_move(self, row: int, col: int, value: int) -> bool:
        """Intenta aplicar un movimiento interactivo. Devuelve True si fue válido."""
        if not self.current_board:
            raise RuntimeError("No hay tablero cargado")
        if not Validator.is_move_valid(self.current_board, row, col, value):
            return False
        if value == 0:
            self.current_board.grid[row][col] = 0
        else:
            self.current_board.set_value(row, col, value)
        return True

    # ---------- Ejecución del AG ----------
    def run_genetic_solver(self) -> RunMetrics:
        if not self.initial_board:
            raise RuntimeError("No hay tablero inicial para resolver")
        engine = GeneticEngine(self.initial_board, self.params)
        start = datetime.now()
        initial_fitness = Validator.fitness_penalty(self.initial_board)
        best_board, generations_used, cause = engine.run()
        end = datetime.now()
        duration = end - start

        if best_board is None:
            best_board = self.initial_board.copy()

        final_fitness = Validator.fitness_penalty(best_board)
        self.current_board = best_board.copy()

        metrics = self.metrics_history.add_run(
            start_time=start,
            duration=duration,
            board_size=self.initial_board.size,
            difficulty=self.difficulty,
            params=self.params,
            initial_fitness=initial_fitness,
            final_fitness=final_fitness,
            best_fitness=engine.best_fitness if engine.best_fitness is not None else final_fitness,
            best_generation=engine.best_generation,
            generations_used=generations_used,
            termination_cause=cause,
            fitness_history=list(engine.best_fitness_history),
        )
        return metrics

    # ---------- Consultas de historial / métricas ----------
    def get_history(self) -> List[RunMetrics]:
        return self.metrics_history.list_runs()

    def clear_history(self) -> None:
        self.metrics_history.clear()
