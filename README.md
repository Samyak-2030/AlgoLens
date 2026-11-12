# AlgoLens

AlgoLens is a browser-based code dry-run playground. Start with a blank editor or optionally load a starter program, then step through a trace with variable snapshots, sequence data when the code creates a list, pointer positions, conditions, and call frames.

## Project structure

```text
AlgoLens/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── analyzer.py      # Restricted Python AST dry-run interpreter
│   │   └── main.py          # FastAPI API and built-in algorithm traces
│   ├── tests/
│   │   └── test_analyzer.py
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

## Analyze your own code

The editor starts blank; selecting a built-in starter program is optional. The program input field is raw stdin passed line-by-line to calls to `input()` without rewriting it. Use new lines for separate input calls. For a LeetCode-style `class Solution` with exactly one public method, AlgoLens safely instantiates the class and calls that method automatically. Enter multiple method arguments as one JSON array, for example `[[2, 7, 11, 15], 9]`; for a single list parameter, either `[1, 2, 1]` or `[[1, 2, 1]]` is accepted. A single top-level function is also auto-called with JSON arguments. The analyzer labels recognizable patterns such as sorting, binary search, sliding windows, two pointers, BFS, monotonic stacks, aggregation, and recursion; otherwise it reports a custom program. Sequence visualization appears when the running code has created a list.

For safety, submitted code is parsed and evaluated by a restricted AST interpreter. It is **not** passed to Python `exec`, a shell, or an external runtime. Supported constructs include basic assignments and arithmetic, lists/tuples/sets/dictionaries and indexing, conditions, bounded loops, functions and recursion, simple classes/instance methods, instance fields, and a small set of safe built-ins and collection methods. Only `typing` annotation imports are accepted; inheritance, decorators, file/network access, and unsupported syntax are rejected. Source size, loop counts, recursion depth, collection size, and trace length are bounded. This supports common LeetCode-style `Solution` methods, not every LeetCode data structure/runtime feature. C++ and JavaScript remain template-only; Python is the current code-aware dry-run language.

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

`POST /api/analyze` accepts `{ "language": "python", "code": "...", "sample_input": "..." }` and returns per-statement execution snapshots. Unsupported syntax returns HTTP 422 with an explanation instead of being executed unrestricted.
