from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple, Optional

from sudoku_board import SudokuBoard
from validator import Validator


# ==========================================================
# Parámetros del algoritmo genético (los que usa la web)
# ==========================================================

@dataclass
class GeneticParams:
    population_size: int = 200
    max_generations: int = 2000
    mutation_rate: float = 0.05
    elite_ratio: float = 0.1


# ==========================================================
# Implementación GA estilo "algo.py" (tableros como listas)
#   - Soporta 4x4, 6x6 y 9x9
# ==========================================================

def _copiar_tablero(tablero: List[List[int]]) -> List[List[int]]:
    return [fila[:] for fila in tablero]


def _obtener_dimensiones(tablero: List[List[int]]) -> Tuple[int, int, int]:
    size = len(tablero)
    if any(len(fila) != size for fila in tablero):
        raise ValueError("El tablero debe ser cuadrado (NxN).")

    if size == 4:
        return size, 2, 2
    elif size == 6:
        return size, 2, 3
    elif size == 9:
        return size, 3, 3
    else:
        raise ValueError("Sólo se admiten tamaños 4x4, 6x6 o 9x9.")


def _construir_pistas_fijas(tablero_inicial: List[List[int]]) -> List[List[bool]]:
    size, _, _ = _obtener_dimensiones(tablero_inicial)
    pista_fija = [[False] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            if tablero_inicial[i][j] != 0:
                pista_fija[i][j] = True
    return pista_fija


def _generar_individuo_inicial(tablero_inicial: List[List[int]]) -> List[List[int]]:
    """Llena las casillas vacías POR FILA, garantizando unicidad por fila."""
    individuo = _copiar_tablero(tablero_inicial)
    size, _, _ = _obtener_dimensiones(tablero_inicial)

    for fila in range(size):
        presentes = set()
        vacias = []

        for col in range(size):
            val = individuo[fila][col]
            if val != 0:
                presentes.add(val)
            else:
                vacias.append(col)

        faltantes = [n for n in range(1, size + 1) if n not in presentes]
        random.shuffle(faltantes)

        for col, valor in zip(vacias, faltantes):
            individuo[fila][col] = valor

    return individuo


def _generar_poblacion_inicial(tablero_inicial: List[List[int]], tam_poblacion: int) -> List[List[List[int]]]:
    return [_generar_individuo_inicial(tablero_inicial) for _ in range(tam_poblacion)]


def _contar_repetidos_en_lista(lista: List[int]) -> int:
    conteo = {}
    for x in lista:
        conteo[x] = conteo.get(x, 0) + 1

    repetidos = 0
    for freq in conteo.values():
        if freq > 1:
            repetidos += (freq - 1)
    return repetidos


def _calcular_penalizacion(individuo: List[List[int]]) -> int:
    size, br, bc = _obtener_dimensiones(individuo)
    penalizacion = 0

    # Filas
    for fila in range(size):
        lista = [individuo[fila][col] for col in range(size)]
        penalizacion += _contar_repetidos_en_lista(lista)

    # Columnas
    for col in range(size):
        lista = [individuo[fila][col] for fila in range(size)]
        penalizacion += _contar_repetidos_en_lista(lista)

    # Subcuadrículas
    for bf in range(0, size, br):
        for bc_ini in range(0, size, bc):
            lista = []
            for i in range(br):
                for j in range(bc):
                    lista.append(individuo[bf + i][bc_ini + j])
            penalizacion += _contar_repetidos_en_lista(lista)

    return penalizacion


def _fitness(individuo: List[List[int]]) -> float:
    """Función fitness original de algo.py: 1 / (1 + penalización)."""
    penal = _calcular_penalizacion(individuo)
    return 1.0 / (1.0 + penal)


def _reparar_filas(individuo: List[List[int]], pista_fija: List[List[bool]]) -> None:
    """Reparación por filas: reemplaza duplicados en casillas NO fijas."""
    size, _, _ = _obtener_dimensiones(individuo)

    for fila in range(size):
        conteo = {}
        posiciones = []

        for col in range(size):
            val = individuo[fila][col]
            conteo[val] = conteo.get(val, 0) + 1
            posiciones.append((col, val))

        faltantes = [n for n in range(1, size + 1) if conteo.get(n, 0) == 0]
        random.shuffle(faltantes)

        for col, val in posiciones:
            if not pista_fija[fila][col] and conteo[val] > 1 and faltantes:
                nuevo = faltantes.pop()
                conteo[val] -= 1
                individuo[fila][col] = nuevo
                conteo[nuevo] = conteo.get(nuevo, 0) + 1


def _cruce_subcuadriculas(
    padreA: List[List[int]],
    padreB: List[List[int]],
    pista_fija: List[List[bool]],
) -> Tuple[List[List[int]], List[List[int]]]:
    """Cruce especializado: intercambia un bloque entre dos padres."""
    hijo1 = _copiar_tablero(padreA)
    hijo2 = _copiar_tablero(padreB)

    size, br, bc = _obtener_dimensiones(padreA)

    bloques_por_fila = size // bc
    bloques_por_col = size // br
    total_bloques = bloques_por_fila * bloques_por_col

    bloque_idx = random.randint(0, total_bloques - 1)
    bloque_fila = bloque_idx // bloques_por_fila
    bloque_col = bloque_idx % bloques_por_fila

    bf = bloque_fila * br
    bc_ini = bloque_col * bc

    for i in range(br):
        for j in range(bc):
            f = bf + i
            c = bc_ini + j
            if not pista_fija[f][c]:
                hijo1[f][c], hijo2[f][c] = hijo2[f][c], hijo1[f][c]

    _reparar_filas(hijo1, pista_fija)
    _reparar_filas(hijo2, pista_fija)

    return hijo1, hijo2


def _mutar(individuo: List[List[int]], pista_fija: List[List[bool]]) -> None:
    """Mutación: intercambia dos casillas no fijas dentro de una fila."""
    size, _, _ = _obtener_dimensiones(individuo)
    fila = random.randint(0, size - 1)

    mutables = [col for col in range(size) if not pista_fija[fila][col]]
    if len(mutables) < 2:
        return

    c1, c2 = random.sample(mutables, 2)
    individuo[fila][c1], individuo[fila][c2] = individuo[fila][c2], individuo[fila][c1]

    _reparar_filas(individuo, pista_fija)


def _crear_pool(
    poblacion: List[List[List[int]]],
    lista_fitness: List[float],
    tam_pool: int,
    proporcion_elitismo: float,
) -> Tuple[List[List[List[int]]], int]:
    pares = list(zip(poblacion, lista_fitness))
    pares.sort(key=lambda x: x[1], reverse=True)

    n_elite = int(tam_pool * proporcion_elitismo)
    pool: List[List[List[int]]] = []

    for i in range(n_elite):
        pool.append(_copiar_tablero(pares[i][0]))

    while len(pool) < tam_pool:
        idx = random.randint(0, len(poblacion) - 1)
        pool.append(_copiar_tablero(poblacion[idx]))

    return pool, n_elite


# ==========================================================
# Motor que conecta el GA "algo.py" con la app Flask
# ==========================================================

class GeneticEngine:
    """
    Adaptador entre el GA de algo.py y la interfaz que usa la app.
    - Trabaja internamente con listas de listas (como algo.py).
    - Expone SudokuBoard + métricas para el resto del sistema.
    """

    def __init__(self, initial_board: SudokuBoard, params: GeneticParams):
        self.initial_board = initial_board
        self.params = params

        self.population: List[List[List[int]]] = []
        self.best_board: Optional[SudokuBoard] = None
        self.best_fitness: Optional[int] = None   # penalización mínima
        self.best_generation: int = 0
        self.best_fitness_history: List[int] = []  # historial de penalización

    # ------------------------------------------------------
    # Inicializar población a partir del SudokuBoard inicial
    # ------------------------------------------------------
    def _init_population(self) -> Tuple[List[List[int]], List[List[bool]]]:
        base_grid = [row[:] for row in self.initial_board.grid]
        pista_fija = _construir_pistas_fijas(base_grid)
        self.population = _generar_poblacion_inicial(base_grid, self.params.population_size)

        self.best_board = None
        self.best_fitness = None
        self.best_generation = 0
        self.best_fitness_history = []

        return base_grid, pista_fija

    # ------------------------------------------------------
    # Ejecutar GA (versión casi 1:1 con ga_sudoku_filas)
    # ------------------------------------------------------
    def run(self) -> Tuple[SudokuBoard, int, str]:
        """
        Devuelve:
          - mejor tablero encontrado (SudokuBoard)
          - generaciones realmente usadas
          - causa de término: "solucion", "estancamiento" o "max_generaciones"
        """
        base_grid, pista_fija = self._init_population()

        tam_poblacion = self.params.population_size
        max_generaciones = self.params.max_generations

        # parámetros internos derivados del algo.py original
        tam_pool = max(2, tam_poblacion // 2)
        proporcion_elitismo = self.params.elite_ratio
        tasa_cruce = 0.9
        tasa_mutacion = self.params.mutation_rate

        mejor_global: Optional[List[List[int]]] = None
        mejor_penal_global: Optional[int] = None

        mejor_penal_antes: Optional[int] = None
        gens_sin_mejora = 0
        umbral_estancamiento = 500
        tasa_mutacion_base = tasa_mutacion
        tasa_mutacion_boost = 0.5

        causa = "max_generaciones"

        for gen in range(max_generaciones):
            # calcular fitness actual
            lista_fitness = [_fitness(ind) for ind in self.population]

            # mejor individuo de esta generación (por fitness)
            idx_mejor = max(range(len(self.population)), key=lambda i: lista_fitness[i])
            mejor_ind = self.population[idx_mejor]
            penal = _calcular_penalizacion(mejor_ind)

            # registrar en historial (siempre penalización, para graficar)
            self.best_fitness_history.append(penal)

            # actualizar mejor global si corresponde
            if (mejor_penal_global is None) or (penal < mejor_penal_global):
                mejor_penal_global = penal
                mejor_global = _copiar_tablero(mejor_ind)
                self.best_fitness = penal
                self.best_board = SudokuBoard.from_list(mejor_global)
                self.best_generation = gen

            # control de estancamiento
            if (mejor_penal_antes is None) or (penal < mejor_penal_antes):
                mejor_penal_antes = penal
                gens_sin_mejora = 0
            else:
                gens_sin_mejora += 1

            if gens_sin_mejora > umbral_estancamiento:
                if gens_sin_mejora > umbral_estancamiento * 2:
                    tasa_mutacion_actual = 0.90
                else:
                    tasa_mutacion_actual = tasa_mutacion_boost
                causa = "estancamiento"
            else:
                tasa_mutacion_actual = tasa_mutacion_base

            # ¿solución perfecta?
            if penal == 0:
                causa = "solucion"
                # aseguramos best_board consistente
                if self.best_board is None:
                    self.best_board = SudokuBoard.from_list(mejor_ind)
                    self.best_fitness = 0
                    self.best_generation = gen
                return self.best_board, gen + 1, causa

            # crear pool (elitismo + aleatorio)
            pool, _ = _crear_pool(self.population, lista_fitness, tam_pool, proporcion_elitismo)

            # nueva población con reemplazo generacional + elitismo
            nueva_poblacion: List[List[List[int]]] = []

            # copiar mejores directamente (elitismo fuerte)
            n_elite_poblacion = max(1, int(tam_poblacion * proporcion_elitismo))
            pares = list(zip(self.population, lista_fitness))
            pares.sort(key=lambda x: x[1], reverse=True)
            for i in range(n_elite_poblacion):
                nueva_poblacion.append(_copiar_tablero(pares[i][0]))

            # resto mediante cruce + mutación
            while len(nueva_poblacion) < tam_poblacion:
                p1 = _copiar_tablero(random.choice(pool))
                p2 = _copiar_tablero(random.choice(pool))

                hijos: List[List[List[int]]] = []
                if random.random() < tasa_cruce:
                    h1, h2 = _cruce_subcuadriculas(p1, p2, pista_fija)
                    hijos.extend([h1, h2])
                else:
                    hijos.extend([p1, p2])

                for h in hijos:
                    if random.random() < tasa_mutacion_actual:
                        _mutar(h, pista_fija)

                    if len(nueva_poblacion) < tam_poblacion:
                        nueva_poblacion.append(h)
                    else:
                        break

            self.population = nueva_poblacion

        # fin del bucle: no se encontró solución perfecta
        if self.best_board is None:
            # fallback: usar mejor tablero conocido (o el inicial)
            if mejor_global is not None:
                self.best_board = SudokuBoard.from_list(mejor_global)
                self.best_fitness = _calcular_penalizacion(mejor_global)
            else:
                self.best_board = self.initial_board.copy()
                self.best_fitness = Validator.fitness_penalty(self.best_board)
            self.best_generation = max_generaciones

        return self.best_board, max_generaciones, causa
