const templates = {
  sum: {
    cpp: `#include <iostream>\nusing namespace std;\n\nint main() {\n  int arr[] = {2, 4, 6, 8, 10};\n  int sum = 0;\n\n  for (int i = 0; i < 5; i++) {\n    sum += arr[i];\n  }\n\n  cout << sum;\n}`,
    python: `arr = [2, 4, 6, 8, 10]\ntotal = 0\n\nfor i in range(len(arr)):\n    total += arr[i]\n\nprint(total)`,
    javascript: `const arr = [2, 4, 6, 8, 10];\nlet sum = 0;\n\nfor (let i = 0; i < arr.length; i++) {\n  sum += arr[i];\n}\n\nconsole.log(sum);`
  },
  bubble_sort: {
    cpp: `#include <algorithm>\n\nvoid bubbleSort(int arr[], int n) {\n  for (int end = n - 1; end > 0; end--) {\n    for (int i = 0; i < end; i++) {\n      if (arr[i] > arr[i + 1]) {\n        swap(arr[i], arr[i + 1]);\n      }\n    }\n  }\n}`,
    python: `def bubble_sort(values):\n    n = len(values)\n    for end in range(n - 1, 0, -1):\n        for i in range(end):\n            if values[i] > values[i + 1]:\n                values[i], values[i + 1] = values[i + 1], values[i]\n    return values`,
    javascript: `function bubbleSort(values) {\n  for (let end = values.length - 1; end > 0; end--) {\n    for (let i = 0; i < end; i++) {\n      if (values[i] > values[i + 1]) {\n        [values[i], values[i + 1]] = [values[i + 1], values[i]];\n      }\n    }\n  }\n  return values;\n}`
  },
  binary_search: {
    cpp: `int binarySearch(int arr[], int low, int high, int target) {\n  if (low > high) return -1;\n  int mid = low + (high - low) / 2;\n  if (arr[mid] == target) return mid;\n  if (arr[mid] < target)\n    return binarySearch(arr, mid + 1, high, target);\n  return binarySearch(arr, low, mid - 1, target);\n}\n// initial call: binarySearch(arr, 0, n - 1, target)`,
    python: `def binary_search(values, low, high, target):\n    if low > high:\n        return -1\n    mid = (low + high) // 2\n    if values[mid] == target:\n        return mid\n    if values[mid] < target:\n        return binary_search(values, mid + 1, high, target)\n    return binary_search(values, low, mid - 1, target)\n\n# initial call: binary_search(values, 0, len(values) - 1, target)`,
    javascript: `function binarySearch(values, low, high, target) {\n  if (low > high) return -1;\n  const mid = Math.floor((low + high) / 2);\n  if (values[mid] === target) return mid;\n  if (values[mid] < target)\n    return binarySearch(values, mid + 1, high, target);\n  return binarySearch(values, low, mid - 1, target);\n}\n// initial call: binarySearch(values, 0, values.length - 1, target)`
  },
  sliding_window: {
    cpp: `int maxWindowSum(vector<int>& arr, int k) {\n  int windowSum = 0;\n  for (int i = 0; i < k; i++) windowSum += arr[i];\n  int best = windowSum;\n  for (int right = k; right < arr.size(); right++) {\n    windowSum += arr[right] - arr[right - k];\n    best = max(best, windowSum);\n  }\n  return best;\n}`,
    python: `def max_window_sum(values, k):\n    window_sum = sum(values[:k])\n    best = window_sum\n    for right in range(k, len(values)):\n        window_sum += values[right] - values[right - k]\n        best = max(best, window_sum)\n    return best`,
    javascript: `function maxWindowSum(values, k) {\n  let sum = values.slice(0, k).reduce((a, b) => a + b, 0);\n  let best = sum;\n  for (let right = k; right < values.length; right++) {\n    sum += values[right] - values[right - k];\n    best = Math.max(best, sum);\n  }\n  return best;\n}`
  },
  two_pointers: {
    cpp: `pair<int, int> findPair(vector<int>& a, int target) {\n  int left = 0, right = a.size() - 1;\n  while (left < right) {\n    int sum = a[left] + a[right];\n    if (sum == target) return {left, right};\n    if (sum < target) left++;\n    else right--;\n  }\n  return {-1, -1};\n}`,
    python: `def find_pair(values, target):\n    values.sort()\n    left, right = 0, len(values) - 1\n    while left < right:\n        total = values[left] + values[right]\n        if total == target:\n            return values[left], values[right]\n        if total < target:\n            left += 1\n        else:\n            right -= 1\n    return None`,
    javascript: `function findPair(values, target) {\n  values.sort((a, b) => a - b);\n  let left = 0, right = values.length - 1;\n  while (left < right) {\n    const sum = values[left] + values[right];\n    if (sum === target) return [values[left], values[right]];\n    if (sum < target) left++;\n    else right--;\n  }\n  return null;\n}`
  },
  bfs: {
    cpp: `void bfs(vector<vector<int>>& graph, int start) {\n  queue<int> q;\n  vector<bool> seen(graph.size(), false);\n  q.push(start); seen[start] = true;\n  while (!q.empty()) {\n    int node = q.front(); q.pop();\n    for (int next : graph[node]) {\n      if (!seen[next]) {\n        seen[next] = true; q.push(next);\n      }\n    }\n  }\n}`,
    python: `from collections import deque\n\ndef bfs(graph, start):\n    queue = deque([start])\n    seen = {start}\n    while queue:\n        node = queue.popleft()\n        for neighbor in graph[node]:\n            if neighbor not in seen:\n                seen.add(neighbor)\n                queue.append(neighbor)`,
    javascript: `function bfs(graph, start) {\n  const queue = [start];\n  const seen = new Set([start]);\n  while (queue.length) {\n    const node = queue.shift();\n    for (const next of graph[node]) {\n      if (!seen.has(next)) {\n        seen.add(next); queue.push(next);\n      }\n    }\n  }\n}`
  }
};

const extensions = { cpp: "cpp", python: "py", javascript: "js" };
const algorithmNames = { sum: "Array sum", bubble_sort: "Bubble sort", binary_search: "Binary search", sliding_window: "Sliding window", two_pointers: "Two pointers", bfs: "Graph traversal · BFS" };
const lineMaps = {
  sum: { python: { 6: 2, 8: 4, 9: 5, 12: 7 }, javascript: { 6: 2, 8: 4, 9: 5, 12: 8 } },
  bubble_sort: { python: { 3: 1, 4: 3, 6: 5, 7: 6, 11: 7 }, javascript: { 3: 1, 4: 2, 6: 4, 7: 5, 11: 9 } },
  binary_search: {
    python: { 9: 11, 1: 1, 2: 2, 3: 4, 4: 5, 5: 7, 6: 8, 7: 9, 8: 11 },
    javascript: { 9: 9, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 9 }
  },
  sliding_window: { python: { 1: 1, 3: 2, 6: 5, 9: 7 }, javascript: { 1: 1, 3: 2, 6: 5, 9: 8 } },
  two_pointers: { python: { 1: 1, 4: 5, 5: 7, 7: 9, 8: 11, 10: 12 }, javascript: { 1: 1, 4: 5, 5: 7, 7: 9, 8: 11, 10: 13 } },
  bfs: { python: { 1: 3, 6: 7, 8: 9, 9: 10, 12: 6 }, javascript: { 1: 1, 6: 5, 8: 7, 9: 8, 12: 4 } }
};
const elements = Object.fromEntries([
  "code-input", "line-gutter", "language-select", "filename", "line-count", "sample-input", "target-input", "window-input", "target-label", "target-field", "window-field", "run-button", "run-state", "step-counter", "empty-state", "trace-content", "trace-step-label", "array-track", "array-detail", "pointer-rail", "graph-section", "graph-svg", "variable-grid", "operation-tag", "operation-text", "condition-row", "call-stack-wrap", "stack-items", "recursion-section", "recursion-tree", "previous-button", "play-button", "play-icon", "play-label", "next-button", "progress-fill", "progress-knob", "progress-caption", "skip-button", "speed-select", "toast", "reset-code", "load-example", "new-session", "share-button"
].map((id) => [id, document.getElementById(id)]));

let selectedAlgorithm = "sum";
let steps = [];
let currentStep = -1;
let activeCodeLine = 0;
let timer = null;
let toastTimer = null;

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => elements.toast.classList.remove("show"), 2400);
}

function setCode(language = elements["language-select"].value) {
  elements["code-input"].value = templates[selectedAlgorithm][language];
  elements.filename.textContent = `${selectedAlgorithm === "sum" ? "main" : selectedAlgorithm}.${extensions[language]}`;
  updateGutter();
}

function updateGutter(activeLine = activeCodeLine) {
  const count = elements["code-input"].value.split("\n").length;
  activeLine = Math.max(0, Math.min(activeLine, count));
  elements["line-gutter"].replaceChildren();
  for (let line = 1; line <= count; line += 1) {
    const marker = document.createElement("span");
    marker.textContent = String(line);
    if (line === activeLine) marker.className = "current";
    elements["line-gutter"].append(marker);
  }
  elements["line-count"].textContent = `${count} lines`;
  if (activeLine) {
    const top = 15 + (activeLine - 1) * 21;
    elements["code-input"].style.backgroundImage = `linear-gradient(to bottom, transparent 0, transparent ${top}px, rgba(114,146,255,.11) ${top}px, rgba(114,146,255,.11) ${top + 21}px, transparent ${top + 21}px)`;
  } else {
    elements["code-input"].style.backgroundImage = "none";
  }
}

function updateParameters() {
  const showTarget = selectedAlgorithm === "binary_search" || selectedAlgorithm === "two_pointers";
  const showWindow = selectedAlgorithm === "sliding_window";
  elements["target-field"].classList.toggle("parameter-hidden", !showTarget);
  elements["window-field"].classList.toggle("parameter-hidden", !showWindow);
  elements["target-label"].textContent = selectedAlgorithm === "binary_search" ? "TARGET VALUE" : "TARGET SUM";
  if (selectedAlgorithm === "binary_search") elements["sample-input"].value = "1, 3, 5, 7, 9, 11";
  if (selectedAlgorithm === "two_pointers") elements["sample-input"].value = "1, 2, 4, 6, 8, 9";
  if (selectedAlgorithm === "sum" || selectedAlgorithm === "bubble_sort" || selectedAlgorithm === "sliding_window" || selectedAlgorithm === "bfs") {
    if (elements["sample-input"].value === "1, 3, 5, 7, 9, 11" || elements["sample-input"].value === "1, 2, 4, 6, 8, 9") elements["sample-input"].value = "2, 4, 6, 8, 10";
  }
  if (selectedAlgorithm === "binary_search") elements["target-input"].value = "7";
  if (selectedAlgorithm === "two_pointers") elements["target-input"].value = "10";
  resetTrace();
}

function setAlgorithm(algorithm) {
  if (!templates[algorithm]) return;
  selectedAlgorithm = algorithm;
  document.querySelectorAll(".algorithm-card").forEach((card) => card.classList.toggle("active", card.dataset.algorithm === algorithm));
  setCode();
  updateParameters();
}

function resetTrace() {
  stopPlayback();
  steps = [];
  currentStep = -1;
  activeCodeLine = 0;
  elements["empty-state"].classList.remove("hidden");
  elements["trace-content"].classList.add("hidden");
  elements["run-state"].className = "run-state";
  elements["run-state"].innerHTML = "<span></span> Ready";
  elements["step-counter"].innerHTML = "STEP <b>0</b> <span>OF 0</span>";
  elements["progress-fill"].style.width = "0%";
  elements["progress-knob"].style.left = "0%";
  elements["progress-caption"].textContent = "Run the code to begin";
  ["previous-button", "play-button", "next-button", "skip-button"].forEach((id) => { elements[id].disabled = true; });
  updateGutter();
}

function parseValues() {
  const raw = elements["sample-input"].value.trim();
  if (!raw) throw new Error("Enter at least one integer.");
  const values = raw.split(/[\s,]+/).filter(Boolean).map((token) => {
    if (!/^-?\d+$/.test(token)) throw new Error(`“${token}” is not an integer.`);
    const value = Number(token);
    if (!Number.isSafeInteger(value) || Math.abs(value) > 1_000_000) throw new Error("Use integers between −1,000,000 and 1,000,000.");
    return value;
  });
  if (values.length > 16) throw new Error("Use 16 values or fewer for a clear visualization.");
  return values;
}

async function runVisualization() {
  stopPlayback();
  elements["run-button"].disabled = true;
  elements["run-state"].className = "run-state";
  elements["run-state"].innerHTML = "<span></span> Preparing";
  try {
    const values = parseValues();
    if (selectedAlgorithm === "binary_search" && values.some((value, index) => index > 0 && value < values[index - 1])) {
      throw new Error("Binary search needs values in ascending order.");
    }
    const targetValue = Number(elements["target-input"].value);
    const windowValue = Number(elements["window-input"].value);
    if ((selectedAlgorithm === "binary_search" || selectedAlgorithm === "two_pointers") && !Number.isInteger(targetValue)) throw new Error("Enter an integer target.");
    if (selectedAlgorithm === "sliding_window" && (!Number.isInteger(windowValue) || windowValue < 1)) throw new Error("Window size must be a positive integer.");
    const response = await fetch("/api/visualize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        algorithm: selectedAlgorithm,
        values,
        target: selectedAlgorithm === "binary_search" || selectedAlgorithm === "two_pointers" ? targetValue : null,
        window_size: selectedAlgorithm === "sliding_window" ? windowValue : 3
      })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Unable to create the trace.");
    steps = result.steps;
    currentStep = 0;
    elements["empty-state"].classList.add("hidden");
    elements["trace-content"].classList.remove("hidden");
    elements["run-state"].className = "run-state paused";
    elements["run-state"].innerHTML = "<span></span> Paused";
    ["previous-button", "play-button", "next-button", "skip-button"].forEach((id) => { elements[id].disabled = false; });
    renderStep();
    showToast(result.summary);
  } catch (error) {
    elements["run-state"].className = "run-state";
    elements["run-state"].innerHTML = "<span></span> Ready";
    showToast(error.message || "Could not reach the AlgoLens API. Start the FastAPI server and try again.");
  } finally {
    elements["run-button"].disabled = false;
  }
}

function prettyValue(value) {
  if (Array.isArray(value)) return `[${value.join(", ")}]`;
  if (value === null || value === undefined) return "—";
  return String(value);
}

function sourceLine(logicalLine) {
  const language = elements["language-select"].value;
  return lineMaps[selectedAlgorithm]?.[language]?.[logicalLine] ?? logicalLine;
}

function renderStep() {
  if (currentStep < 0 || currentStep >= steps.length) return;
  const step = steps[currentStep];
  const progress = steps.length <= 1 ? 100 : currentStep / (steps.length - 1) * 100;
  elements["step-counter"].innerHTML = `STEP <b>${currentStep + 1}</b> <span>OF ${steps.length}</span>`;
  const highlightedLine = Math.min(sourceLine(step.line), elements["code-input"].value.split("\n").length);
  elements["trace-step-label"].textContent = `${algorithmNames[selectedAlgorithm]} · line ${highlightedLine}`;
  elements["array-detail"].textContent = `${step.array.length} ${step.array.length === 1 ? "element" : "elements"}`;
  elements["operation-text"].textContent = step.operation;
  elements["condition-row"].replaceChildren();
  if (step.condition) {
    const condition = document.createElement("span");
    condition.textContent = step.condition;
    elements["condition-row"].append(condition);
    if (step.condition_result !== null && step.condition_result !== undefined) {
      const result = document.createElement("span");
      result.className = step.condition_result ? "truth" : "false";
      result.textContent = `  →  ${step.condition_result ? "true" : "false"}`;
      elements["condition-row"].append(result);
    }
  }
  elements["operation-tag"].textContent = currentStep === steps.length - 1 ? "COMPLETE" : "LINE " + step.line;
  elements["array-track"].replaceChildren();
  const active = new Set(step.active_indices || []);
  const compared = new Set(step.compare_indices || []);
  const sorted = new Set(step.sorted_indices || []);
  step.array.forEach((value, index) => {
    const cell = document.createElement("div");
    cell.className = "array-cell";
    if (active.has(index)) cell.classList.add("active");
    if (compared.has(index)) cell.classList.add("compared");
    if (sorted.has(index)) cell.classList.add("sorted");
    if (currentStep > 0 && selectedAlgorithm === "bubble_sort" && active.has(index)) cell.classList.add("swapped");
    cell.append(document.createTextNode(String(value)));
    const indexLabel = document.createElement("span");
    indexLabel.className = "cell-index";
    indexLabel.textContent = index;
    cell.append(indexLabel);
    elements["array-track"].append(cell);
  });
  renderGraph(step);
  elements["pointer-rail"].replaceChildren();
  (step.pointers || []).forEach((pointer) => {
    const marker = document.createElement("span");
    marker.className = "pointer-marker" + (pointer.kind === "secondary" ? " secondary" : "");
    marker.style.left = `${((pointer.index + 0.5) / step.array.length) * 100}%`;
    marker.textContent = `▲ ${pointer.name}`;
    elements["pointer-rail"].append(marker);
  });
  elements["variable-grid"].replaceChildren();
  const variableEntries = Object.entries(step.variables || {});
  if (step.queue && (selectedAlgorithm === "bfs" || step.queue.length)) variableEntries.push(["queue", step.queue]);
  variableEntries.forEach(([name, value]) => {
    const card = document.createElement("div");
    card.className = "variable-card";
    const variableName = document.createElement("span");
    variableName.className = "variable-name";
    variableName.textContent = name;
    const variableValue = document.createElement("span");
    variableValue.className = "variable-value";
    variableValue.textContent = prettyValue(value);
    card.append(variableName, variableValue);
    elements["variable-grid"].append(card);
  });
  elements["stack-items"].replaceChildren();
  const frames = step.call_stack?.length ? step.call_stack : ["main()"];
  frames.forEach((frame) => {
    const item = document.createElement("span");
    item.className = "stack-frame";
    item.textContent = frame;
    elements["stack-items"].append(item);
  });
  elements["call-stack-wrap"].classList.toggle("hidden", selectedAlgorithm !== "binary_search");
  renderRecursionTree(step);
  elements["progress-fill"].style.width = `${progress}%`;
  elements["progress-knob"].style.left = `${progress}%`;
  elements["progress-caption"].textContent = currentStep === steps.length - 1 ? "Trace complete" : `Step ${currentStep + 1} of ${steps.length}`;
  elements["previous-button"].disabled = currentStep === 0;
  elements["next-button"].disabled = currentStep === steps.length - 1;
  elements["play-button"].disabled = steps.length < 2;
  elements["skip-button"].disabled = currentStep === steps.length - 1;
  const isRunning = Boolean(timer);
  elements["play-icon"].textContent = isRunning ? "Ⅱ" : "▶";
  elements["play-label"].textContent = isRunning ? "Pause" : "Play";
  elements["run-state"].className = currentStep === steps.length - 1 ? "run-state" : isRunning ? "run-state running" : "run-state paused";
  elements["run-state"].innerHTML = currentStep === steps.length - 1 ? "<span></span> Complete" : isRunning ? "<span></span> Running" : "<span></span> Paused";
  activeCodeLine = highlightedLine;
  updateGutter(activeCodeLine);
  const currentMarker = elements["line-gutter"].querySelector(".current");
  if (currentMarker) currentMarker.scrollIntoView({ block: "nearest" });
}

function renderGraph(step) {
  const isGraph = selectedAlgorithm === "bfs";
  elements["graph-section"].classList.toggle("hidden", !isGraph);
  if (!isGraph) return;
  const values = step.array;
  const gap = 48;
  const width = Math.max(130, values.length * gap + 20);
  const yFor = (index) => index % 2 === 0 ? 31 : 59;
  const active = new Set(step.active_indices || []);
  const queuedValues = new Set(step.queue || []);
  const visitedValues = new Set(step.variables?.visited || []);
  const svg = elements["graph-svg"];
  svg.replaceChildren();
  svg.setAttribute("viewBox", `0 0 ${width} 92`);
  svg.style.width = `${width}px`;
  const makeSvg = (name, attrs) => {
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  };
  values.forEach((_, index) => {
    for (const neighbor of [index + 1, index + 2]) {
      if (neighbor >= values.length) continue;
      const path = makeSvg("path", { d: `M ${index * gap + 22} ${yFor(index)} Q ${(index + neighbor) * gap / 2 + 22} 45 ${neighbor * gap + 22} ${yFor(neighbor)}`, class: "graph-edge" });
      svg.append(path);
    }
  });
  values.forEach((value, index) => {
    const group = makeSvg("g", { class: `graph-node${active.has(index) ? " is-active" : ""}${queuedValues.has(value) ? " is-queued" : ""}${visitedValues.has(value) ? " is-visited" : ""}` });
    group.append(makeSvg("circle", { cx: index * gap + 22, cy: yFor(index), r: 13 }));
    const label = makeSvg("text", { x: index * gap + 22, y: yFor(index) + 3.5, "text-anchor": "middle" });
    label.textContent = String(value);
    group.append(label);
    const indexLabel = makeSvg("text", { x: index * gap + 22, y: 86, "text-anchor": "middle", class: "graph-index" });
    indexLabel.textContent = String(index);
    group.append(indexLabel);
    svg.append(group);
  });
}

function renderRecursionTree(step) {
  const isRecursive = selectedAlgorithm === "binary_search";
  elements["recursion-section"].classList.toggle("hidden", !isRecursive);
  if (!isRecursive) return;
  elements["recursion-tree"].replaceChildren();
  (step.call_tree || []).forEach((node) => {
    const depth = node.parent === null ? 0 : node.parent + 1;
    const row = document.createElement("div");
    row.className = `recursion-node ${node.status === "active" ? "is-current" : node.status === "found" ? "is-found" : "is-returned"}`;
    row.style.marginLeft = `${depth * 15}px`;
    const branch = document.createElement("span");
    branch.className = "recursion-branch";
    branch.textContent = depth ? "↳" : "•";
    const label = document.createElement("span");
    label.className = "recursion-call";
    label.textContent = node.label;
    const state = document.createElement("span");
    state.className = "recursion-status";
    state.textContent = node.status;
    row.append(branch, label, state);
    elements["recursion-tree"].append(row);
  });
}

function stopPlayback() {
  if (timer) clearInterval(timer);
  timer = null;
  if (elements["play-icon"]) elements["play-icon"].textContent = "▶";
  if (elements["play-label"]) elements["play-label"].textContent = "Play";
}

function togglePlayback() {
  if (!steps.length) return;
  if (timer) {
    stopPlayback();
    elements["run-state"].className = "run-state paused";
    elements["run-state"].innerHTML = "<span></span> Paused";
    return;
  }
  if (currentStep === steps.length - 1) currentStep = 0;
  elements["play-icon"].textContent = "Ⅱ";
  elements["play-label"].textContent = "Pause";
  elements["run-state"].className = "run-state running";
  elements["run-state"].innerHTML = "<span></span> Running";
  timer = setInterval(() => {
    if (currentStep >= steps.length - 1) {
      stopPlayback();
      renderStep();
      return;
    }
    currentStep += 1;
    renderStep();
  }, Number(elements["speed-select"].value));
  renderStep();
}

function stepBy(amount) {
  stopPlayback();
  currentStep = Math.max(0, Math.min(steps.length - 1, currentStep + amount));
  renderStep();
}

function bindEvents() {
  document.querySelectorAll(".algorithm-card").forEach((card) => card.addEventListener("click", () => setAlgorithm(card.dataset.algorithm)));
  elements["language-select"].addEventListener("change", () => setCode());
  elements["code-input"].addEventListener("input", () => updateGutter());
  elements["code-input"].addEventListener("scroll", () => { elements["line-gutter"].scrollTop = elements["code-input"].scrollTop; });
  elements["run-button"].addEventListener("click", runVisualization);
  elements["previous-button"].addEventListener("click", () => stepBy(-1));
  elements["next-button"].addEventListener("click", () => stepBy(1));
  elements["play-button"].addEventListener("click", togglePlayback);
  elements["skip-button"].addEventListener("click", () => { stopPlayback(); currentStep = steps.length - 1; renderStep(); });
  elements["reset-code"].addEventListener("click", () => { setCode(); showToast("Example template restored."); });
  elements["load-example"].addEventListener("click", () => {
    elements["sample-input"].value = selectedAlgorithm === "binary_search" ? "1, 3, 5, 7, 9, 11" : selectedAlgorithm === "two_pointers" ? "1, 2, 4, 6, 8, 9" : "2, 4, 6, 8, 10";
    elements["target-input"].value = selectedAlgorithm === "binary_search" ? "7" : "10";
    elements["window-input"].value = "3";
  });
  elements["new-session"].addEventListener("click", () => { setAlgorithm("sum"); showToast("New visualization session ready."); });
  elements["share-button"].addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      showToast("Workspace link copied to clipboard.");
    } catch {
      showToast("Copy the page URL to share this workspace.");
    }
  });
  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      runVisualization();
    } else if (event.code === "Space" && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName) && steps.length) {
      event.preventDefault();
      togglePlayback();
    }
  });
}

bindEvents();
setCode();
updateParameters();
