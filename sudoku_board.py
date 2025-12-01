from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SudokuBoard:
    size: int  # 4, 6 o 9
    grid: List[List[int]]          # 0 = casilla vacía
    fixed: List[List[bool]]        # True si es casilla fija del tablero inicial

    @classmethod
    def from_list(cls, grid: List[List[int]]) -> "SudokuBoard":
        if not grid or any(len(row) != len(grid) for row in grid):
            raise ValueError("La grilla debe ser cuadrada y no vacía")
        size = len(grid)
        if size not in (4, 6, 9):
            raise ValueError(f"Tamaño de Sudoku no soportado: {size}")
        fixed = [[cell != 0 for cell in row] for row in grid]
        return cls(size=size, grid=[row[:] for row in grid], fixed=fixed)

    def copy(self) -> "SudokuBoard":
        return SudokuBoard.from_list(self.grid)

    def subgrid_size(self) -> Tuple[int, int]:
        if self.size == 9:
            return 3, 3
        if self.size == 6:
            return 2, 3
        if self.size == 4:
            return 2, 2
        raise ValueError(f"Tamaño de Sudoku no soportado: {self.size}")

    def is_fixed(self, row: int, col: int) -> bool:
        return self.fixed[row][col]

    def set_value(self, row: int, col: int, value: int) -> None:
        if self.fixed[row][col]:
            raise ValueError("No se puede modificar una casilla fija")
        self.grid[row][col] = value

    def __str__(self) -> str:
        return "\n".join(" ".join(str(v) for v in row) for row in self.grid)
