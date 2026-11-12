from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.analyzer import AnalysisError, analyze_python

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"

app = FastAPI(title="AlgoLens API", version="1.0.0", description="Safe, deterministic algorithm trace generation for AlgoLens.")


class VisualizeRequest(BaseModel):
    algorithm: str = "sum"
    values: list[int] = Field(default_factory=lambda: [2, 4, 6, 8, 10], min_length=1, max_length=16)
    target: int | None = None
    window_size: int = Field(default=3, ge=1, le=16)


class CodeAnalysisRequest(BaseModel):
    code: str = Field(min_length=1, max_length=8_000)
    language: str = "python"
    sample_input: str = Field(default="", max_length=512)


class TraceStep(BaseModel):
    line: int
    operation: str
    variables: dict[str, Any]
    array: list[Any]
    sequence_name: str | None = None
    active_indices: list[int] = Field(default_factory=list)
    compare_indices: list[int] = Field(default_factory=list)
    sorted_indices: list[int] = Field(default_factory=list)
    pointers: list[dict[str, Any]] = Field(default_factory=list)
    condition: str = ""
    condition_result: bool | None = None
    call_stack: list[str] = Field(default_factory=list)
    call_tree: list[dict[str, Any]] = Field(default_factory=list)
    queue: list[int] = Field(default_factory=list)


class VisualizeResponse(BaseModel):
    algorithm: str
    title: str
    steps: list[TraceStep]
    summary: str


def _step(
    line: int,
    operation: str,
    variables: dict[str, Any],
    array: list[int],
    *,
    active: list[int] | None = None,
    compare: list[int] | None = None,
    sorted_indices: list[int] | None = None,
    pointers: list[dict[str, Any]] | None = None,
    condition: str = "",
    condition_result: bool | None = None,
    stack: list[str] | None = None,
    tree: list[dict[str, Any]] | None = None,
    queue: list[int] | None = None,
) -> dict[str, Any]:
    return {
        "line": line,
        "operation": operation,
        "variables": variables,
        "array": list(array),
        "active_indices": active or [],
        "compare_indices": compare or [],
        "sorted_indices": sorted_indices or [],
        "pointers": pointers or [],
        "condition": condition,
        "condition_result": condition_result,
        "call_stack": stack or [],
        "call_tree": [dict(node) for node in tree] if tree else [],
        "queue": queue or [],
    }


def trace_sum(values: list[int], _: int | None, __: int) -> tuple[list[dict[str, Any]], str]:
    steps = [_step(6, "Initialize sum and loop index", {"sum": 0, "i": 0}, values)]
    total = 0
    for i, value in enumerate(values):
        steps.append(_step(8, f"Check loop: {i} < {len(values)} → true", {"sum": total, "i": i}, values,
                          active=[i], pointers=[{"name": "i", "index": i}], condition=f"{i} < {len(values)}", condition_result=True))
        before = total
        total += value
        steps.append(_step(9, f"sum = {before} + {value} = {total}", {"sum": total, "i": i, "arr[i]": value}, values,
                          active=[i], pointers=[{"name": "i", "index": i}], condition=f"{before} + {value} = {total}"))
    steps.append(_step(8, f"Check loop: {len(values)} < {len(values)} → false", {"sum": total, "i": len(values)}, values,
                       condition=f"{len(values)} < {len(values)}", condition_result=False))
    steps.append(_step(12, f"Return total: {total}", {"sum": total}, values))
    return steps, f"The values add up to {total}."


def trace_bubble_sort(values: list[int], _: int | None, __: int) -> tuple[list[dict[str, Any]], str]:
    array = list(values)
    steps: list[dict[str, Any]] = [_step(3, "Start sorting the array", {"n": len(array), "pass": 0}, array)]
    sorted_indices: list[int] = []
    n = len(array)
    for end in range(n - 1, 0, -1):
        for j in range(end):
            left, right = array[j], array[j + 1]
            should_swap = left > right
            steps.append(_step(6, f"Compare {left} and {right}", {"i": j, "j": j + 1, "left": left, "right": right}, array,
                               active=[j, j + 1], compare=[j, j + 1], sorted_indices=sorted_indices,
                               pointers=[{"name": "i", "index": j}, {"name": "j", "index": j + 1, "kind": "secondary"}],
                               condition=f"{left} > {right}", condition_result=should_swap))
            if should_swap:
                array[j], array[j + 1] = array[j + 1], array[j]
                steps.append(_step(7, f"Swap positions {j} and {j + 1}", {"i": j, "j": j + 1}, array,
                                   active=[j, j + 1], sorted_indices=sorted_indices, pointers=[{"name": "i", "index": j}, {"name": "j", "index": j + 1, "kind": "secondary"}]))
        sorted_indices.append(end)
        steps.append(_step(4, f"{array[end]} is in its final position", {"pass": n - end}, array,
                           active=[end], sorted_indices=sorted_indices))
    if n:
        sorted_indices.append(0)
    steps.append(_step(11, "Array is sorted", {"length": n}, array, sorted_indices=sorted_indices))
    return steps, f"Sorted {n} values in ascending order."


def trace_binary_search(values: list[int], target: int | None, __: int) -> tuple[list[dict[str, Any]], str]:
    array = list(values)
    target = target if target is not None else array[len(array) // 2]
    steps: list[dict[str, Any]] = [_step(9, f"Start recursive search for {target}", {"target": target}, array)]
    stack: list[str] = []
    tree: list[dict[str, Any]] = []

    def search(low: int, high: int, parent: int | None = None) -> int:
        node_id = len(tree)
        label = f"binarySearch({low}, {high})"
        tree.append({"id": node_id, "parent": parent, "label": label, "status": "active"})
        stack.append(label)
        steps.append(_step(1, f"Call {label}", {"low": low, "high": high, "target": target}, array,
                           active=[(low + high) // 2] if low <= high else [], condition=f"{low} > {high}", condition_result=low > high,
                           stack=stack, tree=tree))
        if low > high:
            tree[node_id]["status"] = "not found"
            steps.append(_step(2, "Base case: range is empty, return −1", {"low": low, "high": high, "result": -1}, array,
                               condition=f"{low} > {high}", condition_result=True, stack=stack, tree=tree))
            stack.pop()
            return -1
        mid = (low + high) // 2
        steps.append(_step(3, f"Compute mid = ({low} + {high}) // 2 = {mid}", {"low": low, "high": high, "mid": mid, "target": target}, array,
                           active=[mid], pointers=[{"name": "low", "index": low}, {"name": "mid", "index": mid, "kind": "secondary"}, {"name": "high", "index": high, "kind": "secondary"}],
                           stack=stack, tree=tree))
        value = array[mid]
        steps.append(_step(4, f"Compare arr[{mid}] = {value} with target {target}", {"low": low, "high": high, "mid": mid, "target": target}, array,
                           active=[mid], compare=[mid], pointers=[{"name": "mid", "index": mid}],
                           condition=f"{value} == {target}", condition_result=value == target, stack=stack, tree=tree))
        if value == target:
            tree[node_id]["status"] = "found"
            steps.append(_step(4, f"Target found at index {mid}; return {mid}", {"mid": mid, "result": mid}, array,
                               active=[mid], sorted_indices=[mid], stack=stack, tree=tree))
            stack.pop()
            return mid
        goes_right = value < target
        steps.append(_step(5, f"Check whether {value} < {target}", {"low": low, "mid": mid, "high": high, "target": target}, array,
                           active=[mid], condition=f"{value} < {target}", condition_result=goes_right, stack=stack, tree=tree))
        if goes_right:
            next_low, next_high = mid + 1, high
            call_line = 6
        else:
            next_low, next_high = low, mid - 1
            call_line = 7
        result = search(next_low, next_high, node_id)
        tree[node_id]["status"] = "found" if result >= 0 else "not found"
        steps.append(_step(call_line, f"Return {result} to {label}", {"low": low, "high": high, "result": result}, array,
                           active=[mid], stack=stack, tree=tree))
        stack.pop()
        return result

    found = search(0, len(array) - 1)
    if found >= 0:
        steps.append(_step(8, f"Search complete: index {found}", {"target": target, "result": found}, array, active=[found], sorted_indices=[found], tree=tree))
        summary = f"Found {target} at index {found}."
    else:
        steps.append(_step(8, f"Search complete: {target} was not found", {"target": target, "result": -1}, array, tree=tree))
        summary = f"{target} was not found."
    return steps, summary


def trace_sliding_window(values: list[int], _: int | None, window_size: int) -> tuple[list[dict[str, Any]], str]:
    array = list(values)
    k = min(window_size, len(array))
    current = sum(array[:k])
    best, best_start = current, 0
    steps: list[dict[str, Any]] = [_step(3, f"Create a window of size {k}", {"k": k, "window_sum": current, "max_sum": best}, array,
                                           active=list(range(k)), pointers=[{"name": "start", "index": 0}, {"name": "end", "index": k - 1, "kind": "secondary"}])]
    for start in range(1, len(array) - k + 1):
        outgoing, incoming = array[start - 1], array[start + k - 1]
        current += incoming - outgoing
        steps.append(_step(6, f"Slide: add {incoming}, remove {outgoing} → {current}", {"start": start, "window_sum": current, "max_sum": max(best, current)}, array,
                           active=list(range(start, start + k)), pointers=[{"name": "start", "index": start}, {"name": "end", "index": start + k - 1, "kind": "secondary"}],
                           condition=f"{current} > {best}", condition_result=current > best))
        if current > best:
            best, best_start = current, start
    steps.append(_step(9, f"Maximum window sum is {best}", {"max_sum": best, "start": best_start, "end": best_start + k - 1}, array,
                       active=list(range(best_start, best_start + k)), sorted_indices=list(range(best_start, best_start + k))))
    return steps, f"Maximum sum {best} is in window {best_start}–{best_start + k - 1}."


def trace_two_pointers(values: list[int], target: int | None, __: int) -> tuple[list[dict[str, Any]], str]:
    array = sorted(values)
    target = target if target is not None else (array[0] + array[-1])
    left, right = 0, len(array) - 1
    steps: list[dict[str, Any]] = [_step(1, f"Find a pair that sums to {target}", {"left": left, "right": right, "target": target}, array)]
    found: tuple[int, int] | None = None
    while left < right:
        pair_sum = array[left] + array[right]
        match = pair_sum == target
        steps.append(_step(4, f"Check {array[left]} + {array[right]} = {pair_sum}", {"left": left, "right": right, "sum": pair_sum, "target": target}, array,
                           active=[left, right], compare=[left, right], pointers=[{"name": "left", "index": left}, {"name": "right", "index": right, "kind": "secondary"}],
                           condition=f"{pair_sum} == {target}", condition_result=match))
        if match:
            found = (array[left], array[right])
            break
        if pair_sum < target:
            left += 1
            steps.append(_step(7, "Sum is too small: move left pointer right", {"left": left, "right": right, "target": target}, array,
                               active=[left, right], pointers=[{"name": "left", "index": left}, {"name": "right", "index": right, "kind": "secondary"}],
                               condition=f"sum < {target}", condition_result=True))
        else:
            right -= 1
            steps.append(_step(8, "Sum is too large: move right pointer left", {"left": left, "right": right, "target": target}, array,
                               active=[left, right], pointers=[{"name": "left", "index": left}, {"name": "right", "index": right, "kind": "secondary"}],
                               condition=f"sum > {target}", condition_result=True))
    if found:
        steps.append(_step(5, f"Pair found: {found[0]} + {found[1]}", {"pair": list(found), "target": target}, array, active=[left, right], sorted_indices=[left, right]))
        summary = f"Found the pair {found[0]} and {found[1]}."
    else:
        steps.append(_step(10, f"No pair sums to {target}", {"target": target, "found": False}, array))
        summary = f"No pair sums to {target}."
    return steps, summary


def trace_bfs(values: list[int], _: int | None, __: int) -> tuple[list[dict[str, Any]], str]:
    # The sample values label nodes. A small chain graph plus skip edges keeps the graph deterministic and visible.
    array = list(values)
    adjacency = {i: [j for j in (i + 1, i + 2) if j < len(array)] for i in range(len(array))}
    q: deque[int] = deque([0])
    visited = {0}
    order: list[int] = []
    steps: list[dict[str, Any]] = [_step(1, f"Start BFS at node {array[0]}", {"visited": [array[0]], "current": "—"}, array,
                                           active=[0], queue=[array[0]], pointers=[{"name": "start", "index": 0}])]
    while q:
        node = q.popleft()
        order.append(node)
        steps.append(_step(6, f"Dequeue node {array[node]}", {"current": array[node], "visited": [array[i] for i in sorted(visited)]}, array,
                           active=[node], queue=[array[i] for i in q]))
        for neighbor in adjacency[node]:
            is_new = neighbor not in visited
            steps.append(_step(8, f"Check neighbor {array[neighbor]}", {"current": array[node], "neighbor": array[neighbor], "visited": [array[i] for i in sorted(visited)]}, array,
                               active=[node, neighbor], compare=[node, neighbor], queue=[array[i] for i in q],
                               condition=f"{array[neighbor]} not visited", condition_result=is_new))
            if is_new:
                visited.add(neighbor)
                q.append(neighbor)
                steps.append(_step(9, f"Mark {array[neighbor]} visited and enqueue", {"current": array[node], "visited": [array[i] for i in sorted(visited)]}, array,
                                   active=[neighbor], queue=[array[i] for i in q]))
    steps.append(_step(12, "Queue is empty — traversal complete", {"visit_order": [array[i] for i in order]}, array,
                       sorted_indices=order, queue=[]))
    return steps, "BFS visit order: " + " → ".join(str(array[i]) for i in order) + "."


TRACE_BUILDERS: dict[str, tuple[str, Callable[..., tuple[list[dict[str, Any]], str]]]] = {
    "sum": ("Array sum", trace_sum),
    "bubble_sort": ("Bubble sort", trace_bubble_sort),
    "binary_search": ("Binary search", trace_binary_search),
    "sliding_window": ("Sliding window", trace_sliding_window),
    "two_pointers": ("Two pointers", trace_two_pointers),
    "bfs": ("Graph traversal · BFS", trace_bfs),
}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "AlgoLens"}


@app.get("/api/algorithms")
def algorithms() -> list[dict[str, str]]:
    return [{"id": key, "name": name} for key, (name, _) in TRACE_BUILDERS.items()]


@app.post("/api/analyze", response_model=VisualizeResponse)
def analyze_code(request: CodeAnalysisRequest) -> VisualizeResponse:
    if request.language != "python":
        raise HTTPException(status_code=400, detail="Safe code-aware dry runs currently support Python. Select Python or use a built-in algorithm template.")
    try:
        result = analyze_python(request.code, request.sample_input)
    except AnalysisError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return VisualizeResponse(**result)


@app.post("/api/visualize", response_model=VisualizeResponse)
def visualize(request: VisualizeRequest) -> VisualizeResponse:
    if request.algorithm not in TRACE_BUILDERS:
        raise HTTPException(status_code=400, detail="Choose a supported algorithm.")
    if any(abs(value) > 1_000_000 for value in request.values):
        raise HTTPException(status_code=400, detail="Values must be between -1,000,000 and 1,000,000.")
    if request.target is not None and abs(request.target) > 1_000_000:
        raise HTTPException(status_code=400, detail="Target must be between -1,000,000 and 1,000,000.")
    if request.algorithm == "binary_search" and request.values != sorted(request.values):
        raise HTTPException(status_code=400, detail="Binary search needs values in ascending order.")
    title, builder = TRACE_BUILDERS[request.algorithm]
    steps, summary = builder(request.values, request.target, request.window_size)
    return VisualizeResponse(algorithm=request.algorithm, title=title, steps=steps, summary=summary)


@app.get("/sample.png", include_in_schema=False)
def sample_image() -> FileResponse:
    image = ROOT / "sample.png"
    if not image.exists():
        raise HTTPException(status_code=404, detail="Reference image not found.")
    return FileResponse(image, media_type="image/png")


# Keep the catch-all static mount last so it cannot shadow the API routes.
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
