from __future__ import annotations

import os
import csv
from typing import List

from sudoku_board import SudokuBoard
from metrics import RunMetrics


class BoardIO:
    SUPPORTED_SIZES = (4, 6, 9)

    @staticmethod
    def _parse_lines(lines: List[str]) -> List[List[int]]:
        grid: List[List[int]] = []
        for raw in lines:
            line = raw.strip()
            if not line:
                continue

            # Detecta CSV o espacio
            if "," in line:
                parts = line.split(",")
            else:
                parts = line.split()

            row: List[int] = []
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                try:
                    row.append(int(p))
                except ValueError:
                    raise ValueError(f"Valor no numérico encontrado: {p}")

            if row:
                grid.append(row)

        if not grid:
            raise ValueError("El archivo no contiene datos de tablero")

        size = len(grid)
        if any(len(r) != size for r in grid):
            raise ValueError("El tablero debe ser cuadrado (N x N)")

        if size not in BoardIO.SUPPORTED_SIZES:
            raise ValueError(f"Tamaño de Sudoku no soportado: {size}")

        max_val = size
        for r in grid:
            for v in r:
                if not (0 <= v <= max_val):
                    raise ValueError(f"Valor fuera de rango (0..{max_val}): {v}")

        return grid

    @staticmethod
    def load_board(path: str) -> SudokuBoard:
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        grid = BoardIO._parse_lines(lines)
        return SudokuBoard.from_list(grid)

    @staticmethod
    def save_board(board: SudokuBoard, path: str) -> None:
        ext = os.path.splitext(path)[1].lower()
        with open(path, "w", encoding="utf-8", newline="") as f:
            if ext == ".csv":
                writer = csv.writer(f)
                for row in board.grid:
                    writer.writerow(row)
            else:
                for row in board.grid:
                    f.write(" ".join(str(v) for v in row) + "\n")

    @staticmethod
    def export_solution_and_metrics(board: SudokuBoard, metrics: RunMetrics, path: str) -> None:
        """Exporta tablero y métricas en un solo archivo."""
        with open(path, "w", encoding="utf-8") as f:
            f.write("# TABLERO FINAL\n")
            for row in board.grid:
                f.write(" ".join(str(v) for v in row) + "\n")

            f.write("\n# MÉTRICAS\n")
            f.write(f"run_id: {metrics.run_id}\n")
            f.write(f"inicio: {metrics.start_time}\n")
            f.write(f"duracion: {metrics.duration.total_seconds():.3f} seg\n")
            f.write(f"tamano: {metrics.board_size}\n")
            f.write(f"dificultad: {metrics.difficulty}\n")

            f.write("\n# PARÁMETROS DEL AG\n")
            f.write(f"poblacion: {metrics.params.population_size}\n")
            f.write(f"max_generaciones: {metrics.params.max_generations}\n")
            f.write(f"tasa_mutacion: {metrics.params.mutation_rate}\n")
            f.write(f"elite_ratio: {metrics.params.elite_ratio}\n")

            f.write("\n# RESULTADOS\n")
            f.write(f"fitness_inicial: {metrics.initial_fitness}\n")
            f.write(f"fitness_final: {metrics.final_fitness}\n")
            f.write(f"mejor_fitness: {metrics.best_fitness}\n")
            f.write(f"mejor_generacion: {metrics.best_generation}\n")
            f.write(f"generaciones_usadas: {metrics.generations_used}\n")
            f.write(f"causa_termino: {metrics.termination_cause}\n")

            f.write("\n# HISTORIAL FITNESS\n")
            f.write(", ".join(str(x) for x in metrics.fitness_history) + "\n")
