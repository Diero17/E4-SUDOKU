from __future__ import annotations

from sudoku_board import SudokuBoard
from validator import Validator
from controller import SudokuController
from io_board import BoardIO


def print_board(board: SudokuBoard) -> None:
    size = board.size
    sg_r, sg_c = board.subgrid_size()
    for r in range(size):
        row_str = ""
        for c in range(size):
            v = board.grid[r][c]
            row_str += ("." if v == 0 else str(v)) + " "
            if (c + 1) % sg_c == 0 and c < size - 1:
                row_str += "| "
        print(row_str.rstrip())
        if (r + 1) % sg_r == 0 and r < size - 1:
            print("-" * (size * 2 + sg_c - 1))


def main_menu():
    controller = SudokuController()
    while True:
        print("\n=== Solucionador de Sudoku con AG ===")
        print("1) Generar nuevo tablero")
        print("2) Cargar tablero desde archivo (.txt/.csv)")
        print("3) Mostrar tablero actual")
        print("4) Jugar de forma interactiva")
        print("5) Configurar parámetros del AG")
        print("6) Ejecutar Algoritmo Genético")
        print("7) Ver historial de ejecuciones")
        print("8) Exportar tablero y métricas de última ejecución")
        print("0) Salir")
        option = input("Opción: ").strip()

        try:
            if option == "1":
                size = int(input("Tamaño (4, 6, 9): "))
                difficulty = input("Dificultad (facil/medio/dificil): ").strip().lower()
                board = controller.generate_puzzle(size, difficulty)
                print("Tablero generado:")
                print_board(board)

            elif option == "2":
                path = input("Ruta del archivo: ").strip()
                board = controller.load_board_from_file(path)
                print("Tablero cargado:")
                print_board(board)

            elif option == "3":
                if not controller.current_board:
                    print("No hay tablero cargado.")
                else:
                    print_board(controller.current_board)

            elif option == "4":
                if not controller.current_board:
                    print("No hay tablero cargado.")
                    continue
                while True:
                    print_board(controller.current_board)
                    print("Ingrese movimiento: fila col valor (1..n) o 0 para borrar, 'r' reiniciar, 'q' salir.")
                    mov = input(">>> ").strip()
                    if mov.lower() == "q":
                        break
                    if mov.lower() == "r":
                        controller.reset_board()
                        continue
                    parts = mov.split()
                    if len(parts) != 3:
                        print("Formato inválido.")
                        continue
                    r, c, v = map(int, parts)
                    r -= 1
                    c -= 1
                    if not controller.apply_move(r, c, v):
                        print("Movimiento inválido (reglas de Sudoku o casilla fija).")
                    else:
                        if Validator.is_valid_solution(controller.current_board):
                            print_board(controller.current_board)
                            print("¡Sudoku resuelto correctamente!")
                            break

            elif option == "5":
                print(f"Parámetros actuales: {controller.params}")
                try:
                    pop = int(
                        input(f"Tamaño población [{controller.params.population_size}]: ")
                        or controller.params.population_size
                    )
                    gens = int(
                        input(f"Máx. generaciones [{controller.params.max_generations}]: ")
                        or controller.params.max_generations
                    )
                    mut = float(
                        input(f"Tasa mutación [{controller.params.mutation_rate}]: ")
                        or controller.params.mutation_rate
                    )
                    elite = float(
                        input(f"Elite ratio [{controller.params.elite_ratio}]: ")
                        or controller.params.elite_ratio
                    )
                except ValueError:
                    print("Entrada inválida, se mantienen parámetros anteriores.")
                else:
                    controller.params.population_size = pop
                    controller.params.max_generations = gens
                    controller.params.mutation_rate = mut
                    controller.params.elite_ratio = elite
                    print("Parámetros actualizados.")

            # ==========================================
            # 6) EJECUTAR ALGORITMO GENÉTICO (MEJORADO)
            # ==========================================
            elif option == "6":
                metrics = controller.run_genetic_solver()
                print("Ejecución completada.")
                print_board(controller.current_board)

                secs = metrics.duration.total_seconds()
                if secs < 5:
                    stars = 3
                elif secs < 15:
                    stars = 2
                else:
                    stars = 1

                # Validación final del Sudoku (RF-04)
                if Validator.is_valid_solution(controller.current_board):
                    print("\n✔ La solución encontrada es un Sudoku válido (fitness = 0).")
                else:
                    print("\n✘ No se encontró una solución perfecta.")
                    print("   Se muestra el mejor individuo encontrado por el algoritmo genético.")

                print(f"\nFitness final: {metrics.final_fitness} (mejor: {metrics.best_fitness})")
                print(f"Generaciones usadas: {metrics.generations_used}")
                print(f"Causa de término: {metrics.termination_cause}")
                print(f"Bonificación visual (estrellas): {'★' * stars}{'☆' * (3 - stars)}")

            elif option == "7":
                runs = controller.get_history()
                if not runs:
                    print("No hay ejecuciones registradas.")
                else:
                    for r in runs:
                        print(
                            f"Run {r.run_id}: {r.start_time}, size={r.board_size}, "
                            f"dif={r.difficulty}, best_fitness={r.best_fitness}, "
                            f"gens={r.generations_used}, causa={r.termination_cause}"
                        )

            elif option == "8":
                runs = controller.get_history()
                if not runs:
                    print("No hay ejecuciones para exportar.")
                    continue
                last = runs[-1]
                path = input("Ruta del archivo de salida (.txt recomendado): ").strip()
                if not controller.current_board:
                    print("No hay tablero actual para exportar.")
                    continue
                BoardIO.export_solution_and_metrics(controller.current_board, last, path)
                print(f"Exportado a {path}")

            elif option == "0":
                print("Adiós.")
                break

            else:
                print("Opción inválida.")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main_menu()
