from __future__ import annotations

from flask import Flask, render_template, request, jsonify, Response

from controller import SudokuController
from sudoku_board import SudokuBoard
from validator import Validator
from genetic import GeneticParams
from io_board import BoardIO

app = Flask(__name__)

# Controller global para mantener tablero + historial
controller = SudokuController()


@app.route("/")
def index():
    return render_template("index.html")


# ---------- GENERAR TABLERO ----------
@app.route("/api/generate", methods=["GET"])
def api_generate():
    size = int(request.args.get("size", 9))
    difficulty = request.args.get("difficulty", "medio").lower()

    board = controller.generate_puzzle(size, difficulty)
    return jsonify({
        "size": board.size,
        "grid": board.grid,
        "difficulty": difficulty,
    })


# ---------- SUBIR TABLERO DESDE ARCHIVO ----------
@app.route("/api/upload_board", methods=["POST"])
def api_upload_board():
    if "file" not in request.files:
        return jsonify({"error": "No se recibió archivo."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nombre de archivo vacío."}), 400

    content = file.read().decode("utf-8")
    lines = content.splitlines()
    # Reutilizamos el parser interno de BoardIO
    grid = BoardIO._parse_lines(lines)  # sí, usamos el método interno
    board = SudokuBoard.from_list(grid)

    controller.initial_board = board.copy()
    controller.current_board = board
    controller.solution_board = None
    controller.difficulty = None

    return jsonify({
        "size": board.size,
        "grid": board.grid,
        "difficulty": None,
    })


# ---------- RESOLVER CON AG ----------
@app.route("/api/solve", methods=["POST"])
def api_solve():
    data = request.get_json()
    grid = data.get("grid")
    if not grid:
        return jsonify({"error": "No se recibió tablero."}), 400

    difficulty = data.get("difficulty", None)
    pop = int(data.get("population_size", 200))
    gens = int(data.get("max_generations", 2000))
    mut = float(data.get("mutation_rate", 0.05))
    elite = float(data.get("elite_ratio", 0.1))

    board = SudokuBoard.from_list(grid)

    # Reutilizamos el controller global, pero con este tablero
    controller.initial_board = board.copy()
    controller.current_board = board
    controller.solution_board = None
    controller.difficulty = difficulty

    controller.params = GeneticParams(
        population_size=pop,
        max_generations=gens,
        mutation_rate=mut,
        elite_ratio=elite,
    )

    metrics = controller.run_genetic_solver()
    solved_grid = controller.current_board.grid
    is_valid = Validator.is_valid_solution(controller.current_board)

    return jsonify({
        "grid": solved_grid,
        "is_valid": is_valid,
        "metrics": {
            "final_fitness": metrics.final_fitness,
            "best_fitness": metrics.best_fitness,
            "generations": metrics.generations_used,
            "termination_cause": metrics.termination_cause,
            "duration_seconds": metrics.duration.total_seconds(),
            "fitness_history": metrics.fitness_history,
        }
    })


# ---------- HISTORIAL DE EJECUCIONES ----------
@app.route("/api/history", methods=["GET"])
def api_history():
    runs = controller.get_history()
    serialized = []
    for r in runs:
        serialized.append({
            "run_id": r.run_id,
            "start_time": r.start_time.isoformat(sep=" ", timespec="seconds"),
            "board_size": r.board_size,
            "difficulty": r.difficulty,
            "best_fitness": r.best_fitness,
            "generations_used": r.generations_used,
            "termination_cause": r.termination_cause,
        })
    return jsonify(serialized)


# ---------- EXPORTAR SOLUCIÓN + MÉTRICAS ----------
@app.route("/api/export", methods=["GET"])
def api_export():
    runs = controller.get_history()
    if not runs or not controller.current_board:
        return jsonify({"error": "No hay ejecución ni tablero para exportar."}), 400

    last = runs[-1]
    board = controller.current_board

    lines = []
    lines.append("# TABLERO FINAL")
    for row in board.grid:
        lines.append(" ".join(str(v) for v in row))

    lines.append("")
    lines.append("# MÉTRICAS")
    lines.append(f"run_id: {last.run_id}")
    lines.append(f"inicio: {last.start_time}")
    lines.append(f"duracion: {last.duration.total_seconds():.3f} seg")
    lines.append(f"tamano: {last.board_size}")
    lines.append(f"dificultad: {last.difficulty}")

    lines.append("")
    lines.append("# PARÁMETROS DEL AG")
    lines.append(f"poblacion: {last.params.population_size}")
    lines.append(f"max_generaciones: {last.params.max_generations}")
    lines.append(f"tasa_mutacion: {last.params.mutation_rate}")
    lines.append(f"elite_ratio: {last.params.elite_ratio}")

    lines.append("")
    lines.append("# RESULTADOS")
    lines.append(f"fitness_inicial: {last.initial_fitness}")
    lines.append(f"fitness_final: {last.final_fitness}")
    lines.append(f"mejor_fitness: {last.best_fitness}")
    lines.append(f"mejor_generacion: {last.best_generation}")
    lines.append(f"generaciones_usadas: {last.generations_used}")
    lines.append(f"causa_termino: {last.termination_cause}")

    lines.append("")
    lines.append("# HISTORIAL FITNESS")
    lines.append(", ".join(str(x) for x in last.fitness_history))

    content = "\n".join(lines)

    return Response(
        content,
        mimetype="text/plain",
        headers={
            "Content-Disposition": 'attachment; filename="sudoku_resultado.txt"'
        },
    )


if __name__ == "__main__":
    app.run(debug=True)
