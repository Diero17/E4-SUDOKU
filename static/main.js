let currentGrid = null;
let initialGrid = null; // para saber qué casillas son fijas
let currentDifficulty = "medio";
let fitnessChart = null;


function createBoardTable(grid) {
  if (!Array.isArray(grid) || grid.length === 0) {
    return document.createElement("table");
  }

  const size = grid.length;
  const table = document.createElement("table");
  table.classList.add("sudoku-table");
  table.classList.add(`size-${size}`); // para las líneas gruesas por bloque

  for (let r = 0; r < size; r++) {
    const tr = document.createElement("tr");

    for (let c = 0; c < size; c++) {
      const td = document.createElement("td");
      const input = document.createElement("input");

      input.type = "text";
      input.inputMode = "numeric";
      input.maxLength = 1;

      const value = grid[r][c] ?? 0;
      const isFixed =
        initialGrid &&
        Array.isArray(initialGrid[r]) &&
        initialGrid[r][c] !== 0;

      if (value !== 0) {
        input.value = value;
      }

      input.dataset.row = String(r);
      input.dataset.col = String(c);

      if (isFixed) {
        td.classList.add("cell-fixed");
        input.classList.add("input-fixed");
        input.readOnly = true;
        input.tabIndex = -1;
      } else {
        td.classList.add("cell-editable");
        input.classList.add("input-editable");
      }

      input.addEventListener("input", (e) => {
        const target = e.target;
        const row = parseInt(target.dataset.row, 10);
        const col = parseInt(target.dataset.col, 10);

        if (!currentGrid || Number.isNaN(row) || Number.isNaN(col)) {
          return;
        }

        // Solo dejamos un dígito 1-9
        const raw = target.value.replace(/[^1-9]/g, "");
        const val = raw === "" ? "" : raw.charAt(raw.length - 1);
        target.value = val;

        if (val === "") {
          currentGrid[row][col] = 0;
        } else {
          currentGrid[row][col] = parseInt(val, 10);
        }
      });

      td.appendChild(input);
      tr.appendChild(td);
    }

    table.appendChild(tr);
  }

  return table;
}


function renderBoard() {
  const container = document.getElementById("board-container");
  container.innerHTML = "";
  if (currentGrid) {
    container.appendChild(createBoardTable(currentGrid));
  }
}

async function generateSudoku() {
  const size = document.getElementById("size").value;
  const difficulty = document.getElementById("difficulty").value;
  currentDifficulty = difficulty;

  const res = await fetch(`/api/generate?size=${size}&difficulty=${difficulty}`);
  const data = await res.json();

  // Tablero base que define qué casillas son fijas
  initialGrid = JSON.parse(JSON.stringify(data.grid));
  currentGrid = data.grid;

  renderBoard();
  document.getElementById("metrics").textContent = "";
  updateFitnessChart([]);
}


async function uploadBoard() {
  const fileInput = document.getElementById("file-input");
  if (!fileInput.files || fileInput.files.length === 0) {
    alert("Selecciona un archivo primero.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const res = await fetch("/api/upload_board", {
    method: "POST",
    body: formData,
  });

  const data = await res.json();
  if (data.error) {
    alert(data.error);
    return;
  }

  // Lo que venga como no-cero desde archivo se considera “fijo”
  initialGrid = JSON.parse(JSON.stringify(data.grid));
  currentGrid = data.grid;
  currentDifficulty = data.difficulty || "medio";

  renderBoard();
  document.getElementById("metrics").textContent = "";
  updateFitnessChart([]);
}


async function solveWithGA() {
  if (!currentGrid) {
    alert("Primero genera o carga un Sudoku.");
    return;
  }

  const pop = parseInt(document.getElementById("param-population").value, 10);
  const gens = parseInt(document.getElementById("param-generations").value, 10);
  const mut = parseFloat(document.getElementById("param-mutation").value);
  const elite = parseFloat(document.getElementById("param-elite").value);

  const res = await fetch("/api/solve", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      grid: currentGrid,
      difficulty: currentDifficulty,
      population_size: pop,
      max_generations: gens,
      mutation_rate: mut,
      elite_ratio: elite,
    }),
  });

  const data = await res.json();
  if (data.error) {
    alert(data.error);
    return;
  }

  currentGrid = data.grid;
  renderBoard();

  const isValid = data.is_valid;
  const m = data.metrics;
  const metricsText = [
    isValid
      ? "✔ Sudoku válido (fitness = 0)."
      : "✘ No se encontró solución perfecta. (mejor individuo alcanzado)",
    `Fitness final: ${m.final_fitness}`,
    `Mejor fitness: ${m.best_fitness}`,
    `Generaciones: ${m.generations}`,
    `Causa de término: ${m.termination_cause}`,
    `Duración (s): ${m.duration_seconds.toFixed(3)}`
  ].join("\n");

  document.getElementById("metrics").textContent = metricsText;
  // Cortar el historial al número REAL de generaciones usadas
  const history = (m.fitness_history || []).slice(0, m.generations);

  // Graficar solo las generaciones realmente ejecutadas
  updateFitnessChart(history);
}

async function exportResult() {
  const res = await fetch("/api/export");
  if (!res.ok) {
    const data = await res.json();
    alert(data.error || "No se pudo exportar.");
    return;
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "sudoku_resultado.txt";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

async function loadHistory() {
  const res = await fetch("/api/history");
  const data = await res.json();

  const container = document.getElementById("history-list");
  container.innerHTML = "";

  if (!data.length) {
    container.textContent = "No hay ejecuciones registradas.";
    return;
  }

  const table = document.createElement("table");
  table.classList.add("history-table");

  const thead = document.createElement("thead");
  thead.innerHTML = `
    <tr>
      <th>ID</th>
      <th>Inicio</th>
      <th>Tamaño</th>
      <th>Dificultad</th>
      <th>Mejor fitness</th>
      <th>Generaciones</th>
      <th>Causa término</th>
    </tr>
  `;
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  data.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.run_id}</td>
      <td>${r.start_time}</td>
      <td>${r.board_size}</td>
      <td>${r.difficulty ?? "-"}</td>
      <td>${r.best_fitness}</td>
      <td>${r.generations_used}</td>
      <td>${r.termination_cause}</td>
    `;
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);

  container.appendChild(table);
}

function updateFitnessChart(history) {
  const canvas = document.getElementById("fitness-chart");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");

  if (fitnessChart) {
    fitnessChart.destroy();
    fitnessChart = null;
  }

  if (!history || history.length === 0) {
    return;
  }

  const labels = history.map((_, idx) => idx + 1);

  fitnessChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Mejor fitness",
          data: history,
          borderWidth: 2,
          tension: 0.25,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: "#e5e7eb",
            font: { size: 11 },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#9ca3af",
            font: { size: 10 },
          },
          grid: {
            color: "rgba(148, 163, 184, 0.25)",
          },
          title: {
            display: true,
            text: "Generaciones",
            color: "#9ca3af",
            font: { size: 11 },
          },
        },
        y: {
          ticks: {
            color: "#9ca3af",
            font: { size: 10 },
          },
          grid: {
            color: "rgba(148, 163, 184, 0.18)",
          },
          title: {
            display: true,
            text: "Fitness",
            color: "#9ca3af",
            font: { size: 11 },
          },
          beginAtZero: true,
        },
      },
    },
  });
}


document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-generate").addEventListener("click", generateSudoku);
  document.getElementById("btn-solve").addEventListener("click", solveWithGA);
  document.getElementById("btn-upload").addEventListener("click", uploadBoard);
  document.getElementById("btn-export").addEventListener("click", exportResult);
  document.getElementById("btn-history").addEventListener("click", loadHistory);
});
