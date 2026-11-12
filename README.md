# AlgoLens

AlgoLens is a browser-based algorithm dry-run playground. Pick an algorithm, enter sample values, and step through a generated trace with animated arrays, variable snapshots, pointer positions, conditions, a call stack, and a BFS queue/graph view.

## Project structure

```text
AlgoLens/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI API and trace builders
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── sample.png               # Supplied visual reference
├── .gitignore
└── README.md
```

## Run locally

From the project root, create and activate a virtual environment, then install the backend dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). FastAPI serves the static frontend and exposes interactive API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). The health endpoint is `/api/health`.

## Included visualizations

- Array sum: loop progress, array references, and a running accumulator.
- Bubble sort: comparisons, swaps, and sorted positions.
- Binary search: recursive call frames, bounds, midpoint, and condition outcomes. Input must be sorted ascending.
- Sliding window: window boundaries and the rolling maximum sum.
- Two pointers: sorted values, pointer movement, and pair-sum checks.
- Graph traversal (BFS): deterministic small adjacency graph, visited nodes, active queue, and traversal order.

The language selector switches the illustrative C++, Python, and JavaScript templates. AlgoLens generates traces from its safe built-in algorithm implementations; it does **not** execute arbitrary code entered into the editor. This avoids running untrusted source on the API server. The editor is an inspectable template surface, not a general-purpose debugger yet.

## API

`POST /api/visualize` accepts JSON such as:

```json
{
  "algorithm": "bubble_sort",
  "values": [5, 1, 4, 2],
  "target": null,
  "window_size": 3
}
```

Supported algorithm IDs are `sum`, `bubble_sort`, `binary_search`, `sliding_window`, `two_pointers`, and `bfs`. Inputs are bounded to 16 integers (each between -1,000,000 and 1,000,000) so traces remain responsive and legible.
