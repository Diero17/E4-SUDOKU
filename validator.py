from typing import List

from sudoku_board import SudokuBoard


class Validator:
    @staticmethod
    def _count_duplicates(values: List[int]) -> int:
        """Cuenta cuántos valores repetidos hay en una lista ignorando ceros."""
        nums = [v for v in values if v != 0]
        return len(nums) - len(set(nums))

    @classmethod
    def fitness_penalty(cls, board: SudokuBoard) -> int:
        """Penalización: 0 = tablero perfecto.
        Suma repeticiones en filas, columnas y subcuadrículas.
        """
        size = board.size
        grid = board.grid
        penalty = 0

        # Filas
        for row in grid:
            penalty += cls._count_duplicates(row)

        # Columnas
        for c in range(size):
            col = [grid[r][c] for r in range(size)]
            penalty += cls._count_duplicates(col)

        # Subcuadrículas
        sg_r, sg_c = board.subgrid_size()
        for br in range(0, size, sg_r):
            for bc in range(0, size, sg_c):
                block = [
                    grid[r][c]
                    for r in range(br, br + sg_r)
                    for c in range(bc, bc + sg_c)
                ]
                penalty += cls._count_duplicates(block)

        return penalty

    @classmethod
    def is_valid_solution(cls, board: SudokuBoard) -> bool:
        """Retorna True si el tablero no tiene duplicados en filas, columnas ni bloques."""
        return cls.fitness_penalty(board) == 0

    @classmethod
    def is_move_valid(cls, board: SudokuBoard, row: int, col: int, value: int) -> bool:
        """Valida un movimiento interactivo según reglas de Sudoku.
        value = 0 se interpreta como 'borrar' y siempre es válido (si no es fija).
        """
        size = board.size
        if not (0 <= row < size and 0 <= col < size):
            return False
        if board.is_fixed(row, col):
            return False
        if value == 0:
            return True
        if not (1 <= value <= size):
            return False

        # Verificar fila
        for c in range(size):
            if c != col and board.grid[row][c] == value:
                return False

        # Verificar columna
        for r in range(size):
            if r != row and board.grid[r][col] == value:
                return False

        # Verificar subcuadrícula
        sg_r, sg_c = board.subgrid_size()
        start_r = (row // sg_r) * sg_r
        start_c = (col // sg_c) * sg_c
        for r in range(start_r, start_r + sg_r):
            for c in range(start_c, start_c + sg_c):
                if (r != row or c != col) and board.grid[r][c] == value:
                    return False

        return True
