"""A bounded, allow-listed Python interpreter for AlgoLens dry runs.

This evaluates Python AST nodes in-process; submitted source is never passed to
exec/eval, a shell, or an external interpreter. Unsupported syntax fails closed.
"""

from __future__ import annotations

import ast
import json
import operator
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable


MAX_SOURCE_LENGTH = 8_000
MAX_STEPS = 350
MAX_LOOP_ITEMS = 100
MAX_CALL_DEPTH = 16
MAX_COLLECTION_SIZE = 100
MAX_ABS_NUMBER = 1_000_000_000


class AnalysisError(ValueError):
    """The submitted program is invalid or outside the safe language subset."""


@dataclass(frozen=True)
class SafeFunction:
    name: str
    function: Callable[..., Any]


@dataclass
class UserClass:
    name: str
    methods: dict[str, ast.FunctionDef]


@dataclass
class UserInstance:
    user_class: UserClass
    attributes: dict[str, Any]


@dataclass
class BoundUserMethod:
    instance: UserInstance
    name: str


@dataclass
class ReturnSignal(Exception):
    value: Any


@dataclass
class BreakSignal(Exception):
    pass


@dataclass
class ContinueSignal(Exception):
    pass


BIN_OPS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
UNARY_OPS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}
COMPARE_OPS: dict[type[ast.cmpop], Callable[[Any, Any], bool]] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda left, right: left in right,
    ast.NotIn: lambda left, right: left not in right,
}


def _call_range(*args: int) -> range:
    if not 1 <= len(args) <= 3 or any(not isinstance(value, int) for value in args):
        raise AnalysisError("range() accepts one to three integer arguments.")
    result = range(*args)
    if len(result) > MAX_LOOP_ITEMS:
        raise AnalysisError(f"Loops are limited to {MAX_LOOP_ITEMS} iterations per range.")
    return result


def _safe_int(value: Any = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError, OverflowError) as error:
        raise AnalysisError(f"Cannot convert {value!r} to an integer.") from error


def _safe_number(value: Any) -> None:
    if isinstance(value, (int, float)) and abs(value) > MAX_ABS_NUMBER:
        raise AnalysisError("Numeric values are limited to 1,000,000,000 in magnitude.")


def detect_algorithm(source: str, tree: ast.Module) -> str:
    """Infer a human-readable pattern label from the submitted syntax."""
    compact = " ".join(source.lower().split())
    names = {node.id.lower() for node in ast.walk(tree) if isinstance(node, ast.Name)}
    calls = {node.func.id.lower() for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    if "nextgreater" in compact or {"stack", "doubled"}.issubset(names):
        return "Monotonic stack · next greater element"
    if any(token in compact for token in ("popleft(", "queue", "deque(")) or {"graph", "visited"}.issubset(names):
        return "Graph traversal · BFS"
    if any(token in compact for token in ("binary_search", "binarysearch", "bisect")) or ("mid" in names and {"low", "high"}.issubset(names)):
        return "Binary search"
    if {"left", "right"}.issubset(names) and any(token in names for token in ("target", "total", "pair_sum")):
        return "Two pointers"
    if any(token in names for token in ("window_sum", "window_start", "window_end", "window_size")):
        return "Sliding window"
    nested_loops = sum(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree)) >= 2
    if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sorted" for node in ast.walk(tree)):
        return "Sorting"
    has_comparison = any(isinstance(node, ast.Compare) for node in ast.walk(tree))
    has_indexed_values = any(isinstance(node, ast.Subscript) for node in ast.walk(tree))
    has_swap = any(
        isinstance(node, ast.Assign)
        and any(isinstance(target, (ast.Tuple, ast.List)) for target in node.targets)
        and isinstance(node.value, (ast.Tuple, ast.List))
        for node in ast.walk(tree)
    )
    if nested_loops and has_comparison and has_indexed_values and has_swap:
        return "Sorting · comparison and swap"
    if any(
        isinstance(node, ast.FunctionDef)
        and any(
            isinstance(call, ast.Call)
            and (
                isinstance(call.func, ast.Name) and call.func.id == node.name
                or isinstance(call.func, ast.Attribute) and call.func.attr == node.name
            )
            for call in ast.walk(node)
        )
        for node in ast.walk(tree)
    ):
        return "Recursive algorithm"
    if any(isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add) for node in ast.walk(tree)) and names.intersection({"total", "sum", "result", "accumulator"}):
        return "Array aggregation · sum"
    if any(isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree)):
        return "Iteration / custom algorithm"
    if calls.intersection({"sum", "max", "min"}):
        return "Array aggregation"
    return "Custom Python program"


class DryRunInterpreter:
    """Interpret a small Python subset and emit snapshots after each operation."""

    def __init__(self, source: str, sample_input: str) -> None:
        if len(source) > MAX_SOURCE_LENGTH:
            raise AnalysisError(f"Code is limited to {MAX_SOURCE_LENGTH} characters.")
        try:
            self.tree = ast.parse(source, mode="exec")
        except SyntaxError as error:
            message = error.msg or "Invalid Python syntax"
            if error.lineno:
                message += f" on line {error.lineno}"
            raise AnalysisError(message) from error
        self.source = source
        normalized_input = sample_input.replace("\r\n", "\n").replace("\r", "\n")
        self.input_lines = normalized_input.split("\n") if sample_input else []
        self.input_index = 0
        self.functions: dict[str, ast.FunctionDef] = {}
        self.classes: dict[str, UserClass] = {}
        self.global_environment: dict[str, Any] = {}
        self.steps: list[dict[str, Any]] = []
        self.frames: list[str] = ["<module>"]
        self.outputs: list[str] = []
        self.builtins: dict[str, SafeFunction] = {
            "abs": SafeFunction("abs", abs),
            "enumerate": SafeFunction("enumerate", lambda values: list(enumerate(values))),
            "int": SafeFunction("int", _safe_int),
            "len": SafeFunction("len", len),
            "list": SafeFunction("list", list),
            "map": SafeFunction("map", lambda function, values: [self.call_safe(function, [value]) for value in values]),
            "max": SafeFunction("max", max),
            "min": SafeFunction("min", min),
            "print": SafeFunction("print", self._print),
            "range": SafeFunction("range", _call_range),
            "reversed": SafeFunction("reversed", lambda values: list(reversed(values))),
            "sorted": SafeFunction("sorted", sorted),
            "str": SafeFunction("str", str),
            "sum": SafeFunction("sum", sum),
            "input": SafeFunction("input", self._input),
        }

    def _input(self, prompt: Any = "") -> str:
        if self.input_index >= len(self.input_lines):
            raise AnalysisError("input() requested another line, but the sample input has no more lines.")
        value = self.input_lines[self.input_index]
        self.input_index += 1
        return value

    def _snapshot(self, value: Any) -> Any:
        if isinstance(value, UserInstance):
            return {"__class__": value.user_class.name, **{key: self._snapshot(item) for key, item in value.attributes.items()}}
        if isinstance(value, BoundUserMethod):
            return f"<bound method {value.instance.user_class.name}.{value.name}>"
        if isinstance(value, list):
            return [self._snapshot(item) for item in value]
        if isinstance(value, tuple):
            return [self._snapshot(item) for item in value]
        if isinstance(value, set):
            return sorted((self._snapshot(item) for item in value), key=repr)
        if isinstance(value, dict):
            return {str(key): self._snapshot(item) for key, item in value.items()}
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return repr(value)

    def _display(self, value: Any) -> str:
        if isinstance(value, UserInstance):
            return f"<{value.user_class.name} instance>"
        return repr(value)

    def _print(self, *values: Any, sep: str = " ", end: str = "\n") -> None:
        self.outputs.append(sep.join(str(value) for value in values) + end.rstrip("\n"))

    def _tick(self, node: ast.AST, operation: str, environment: dict[str, Any], condition: str = "", result: bool | None = None) -> None:
        if len(self.steps) >= MAX_STEPS:
            raise AnalysisError(f"Dry runs are limited to {MAX_STEPS} steps. Reduce the input size or loop count.")
        scope = {**self.global_environment, **environment}
        visible = {key: self._snapshot(value) for key, value in scope.items() if not key.startswith("__")}
        arrays = [(key, value) for key, value in visible.items() if isinstance(value, list)]
        arrays.sort(key=lambda item: (item[0].lower() in {"arr", "array", "data", "items", "nums", "numbers", "values"}, item[0].lower() not in {"queue", "seen", "visited", "stack"}, len(item[1])), reverse=True)
        sequence_name = arrays[0][0] if arrays else None
        array = list(arrays[0][1][:MAX_COLLECTION_SIZE]) if arrays else []
        pointers: list[dict[str, Any]] = []
        active: list[int] = []
        for name, value in visible.items():
            if isinstance(value, int) and not isinstance(value, bool) and name.lower() in {"i", "j", "k", "index", "idx", "left", "right", "low", "high", "mid", "start", "end", "window_start", "window_end"} and 0 <= value < len(array):
                active.append(value)
                pointers.append({"name": name, "index": value, "kind": "secondary" if name.lower() in {"j", "right", "high", "end", "window_end"} else "primary"})
        self.steps.append({
            "line": max(1, getattr(node, "lineno", 1)),
            "operation": operation[:300],
            "variables": visible,
            "array": array,
            "sequence_name": sequence_name,
            "active_indices": list(dict.fromkeys(active)),
            "compare_indices": [],
            "sorted_indices": [],
            "pointers": pointers,
            "condition": condition[:200],
            "condition_result": result,
            "call_stack": list(self.frames),
            "call_tree": [],
            "queue": [],
        })

    def _resolve(self, name: str, environment: dict[str, Any]) -> Any:
        if name in environment:
            return environment[name]
        if name in self.global_environment:
            return self.global_environment[name]
        if name in self.builtins:
            return self.builtins[name]
        if name in self.classes:
            return self.classes[name]
        raise AnalysisError(f"Name {name!r} is not defined.")

    def _construct_instance(self, user_class: UserClass, args: list[Any], keywords: dict[str, Any]) -> UserInstance:
        instance = UserInstance(user_class, {})
        if "__init__" in user_class.methods:
            self._call_user_function(f"{user_class.name}.__init__", [instance, *args], keywords, user_class.methods["__init__"])
        elif args or keywords:
            raise AnalysisError(f"{user_class.name}() does not accept constructor arguments.")
        return instance

    def _get_attribute(self, receiver: Any, name: str) -> Any:
        if isinstance(receiver, UserInstance):
            if name in receiver.attributes:
                return receiver.attributes[name]
            if name in receiver.user_class.methods:
                return BoundUserMethod(receiver, name)
            raise AnalysisError(f"{receiver.user_class.name} has no attribute {name!r}.")
        raise AnalysisError(f"Attribute access {name!r} is not supported on this value.")

    def _checked(self, value: Any) -> Any:
        if isinstance(value, (int, float)):
            _safe_number(value)
        if isinstance(value, (list, tuple, set, str, dict)) and len(value) > MAX_COLLECTION_SIZE:
            raise AnalysisError(f"Collections are limited to {MAX_COLLECTION_SIZE} items.")
        return value

    def call_safe(self, function: Any, args: list[Any], keywords: dict[str, Any] | None = None) -> Any:
        keywords = keywords or {}
        if not isinstance(function, SafeFunction):
            raise AnalysisError("Only the documented safe built-in functions can be called.")
        try:
            return self._checked(function.function(*args, **keywords))
        except AnalysisError:
            raise
        except (TypeError, ValueError, IndexError, KeyError, ZeroDivisionError, OverflowError) as error:
            raise AnalysisError(f"{function.name}(): {error}") from error

    def _call_method(self, receiver: Any, name: str, args: list[Any], keywords: dict[str, Any]) -> Any:
        if isinstance(receiver, str) and name in {"split", "strip"}:
            method = getattr(receiver, name)
            return self._checked(method(*args, **keywords))
        if isinstance(receiver, list) and name in {"append", "extend", "insert", "pop", "remove", "reverse", "sort", "clear"}:
            method = getattr(receiver, name)
            result = method(*args, **keywords)
            self._checked(receiver)
            return result
        if isinstance(receiver, dict) and name in {"get", "keys", "values", "items", "pop", "setdefault", "clear", "update"}:
            method = getattr(receiver, name)
            result = method(*args, **keywords)
            self._checked(receiver)
            return self._checked(list(result) if name in {"keys", "values", "items"} else result)
        if isinstance(receiver, set) and name in {"add", "discard", "remove", "pop", "clear", "copy"}:
            method = getattr(receiver, name)
            result = method(*args, **keywords)
            self._checked(receiver)
            return self._checked(result)
        raise AnalysisError(f"Method {name!r} is not allowed on this value.")

    def evaluate(self, node: ast.AST, environment: dict[str, Any]) -> Any:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (str, int, float, bool, type(None))):
                return self._checked(node.value)
        elif isinstance(node, ast.Name):
            return self._resolve(node.id, environment)
        elif isinstance(node, (ast.List, ast.Tuple)):
            values = [self.evaluate(item, environment) for item in node.elts]
            return self._checked(values if isinstance(node, ast.List) else tuple(values))
        elif isinstance(node, ast.Set):
            return {self.evaluate(item, environment) for item in node.elts}
        elif isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
            left, right = self.evaluate(node.left, environment), self.evaluate(node.right, environment)
            if isinstance(node.op, ast.Pow) and isinstance(right, (int, float)) and abs(right) > 10:
                raise AnalysisError("Exponent values are limited to 10.")
            return self._checked(BIN_OPS[type(node.op)](left, right))
        elif isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
            return self._checked(UNARY_OPS[type(node.op)](self.evaluate(node.operand, environment)))
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                for value in node.values:
                    result = self.evaluate(value, environment)
                    if not result:
                        return result
                return result
            if isinstance(node.op, ast.Or):
                for value in node.values:
                    result = self.evaluate(value, environment)
                    if result:
                        return result
                return result
        elif isinstance(node, ast.Compare):
            left = self.evaluate(node.left, environment)
            for operation, comparator in zip(node.ops, node.comparators):
                right = self.evaluate(comparator, environment)
                if type(operation) not in COMPARE_OPS or not COMPARE_OPS[type(operation)](left, right):
                    return False
                left = right
            return True
        elif isinstance(node, ast.IfExp):
            return self.evaluate(node.body if self.evaluate(node.test, environment) else node.orelse, environment)
        elif isinstance(node, ast.Subscript):
            value = self.evaluate(node.value, environment)
            key = self.evaluate(node.slice, environment)
            try:
                return self._checked(value[key])
            except (TypeError, IndexError, KeyError) as error:
                raise AnalysisError(f"Invalid index: {error}") from error
        elif isinstance(node, ast.Slice):
            lower = self.evaluate(node.lower, environment) if node.lower else None
            upper = self.evaluate(node.upper, environment) if node.upper else None
            step = self.evaluate(node.step, environment) if node.step else None
            return slice(lower, upper, step)
        elif isinstance(node, ast.Call):
            args = [self.evaluate(argument, environment) for argument in node.args]
            if any(keyword.arg is None for keyword in node.keywords):
                raise AnalysisError("Keyword unpacking is not supported.")
            keywords = {keyword.arg: self.evaluate(keyword.value, environment) for keyword in node.keywords if keyword.arg is not None}
            if isinstance(node.func, ast.Attribute):
                receiver = self.evaluate(node.func.value, environment)
                if isinstance(receiver, UserInstance) and node.func.attr in receiver.user_class.methods:
                    return self._call_user_function(
                        f"{receiver.user_class.name}.{node.func.attr}",
                        [receiver, *args],
                        keywords,
                        node,
                    )
                return self._checked(self._call_method(receiver, node.func.attr, args, keywords))
            if isinstance(node.func, ast.Name) and node.func.id in {"dict", "set", "tuple"}:
                if keywords:
                    raise AnalysisError(f"{node.func.id}() does not accept keyword arguments in this dry run.")
                if len(args) > 1:
                    raise AnalysisError(f"{node.func.id}() accepts at most one argument.")
                constructor = {"dict": dict, "set": set, "tuple": tuple}[node.func.id]
                return self._checked(constructor(*args))
            if isinstance(node.func, ast.Name) and node.func.id in environment and isinstance(environment[node.func.id], BoundUserMethod):
                bound = environment[node.func.id]
                return self._call_user_function(
                    f"{bound.instance.user_class.name}.{bound.name}",
                    [bound.instance, *args],
                    keywords,
                    node,
                )
            if not isinstance(node.func, ast.Name):
                raise AnalysisError("Calls must use a named safe built-in or a function defined in this code.")
            if node.func.id in self.functions:
                return self._call_user_function(node.func.id, args, keywords, node)
            resolved = self._resolve(node.func.id, environment)
            if isinstance(resolved, UserClass):
                return self._construct_instance(resolved, args, keywords)
            return self.call_safe(resolved, args, keywords)
        elif isinstance(node, ast.Attribute):
            return self._get_attribute(self.evaluate(node.value, environment), node.attr)
        elif isinstance(node, ast.ListComp):
            if len(node.generators) != 1 or node.generators[0].is_async:
                raise AnalysisError("Only single-clause list comprehensions are supported.")
            generator = node.generators[0]
            values = self.evaluate(generator.iter, environment)
            results = []
            for value in values:
                self._assign(generator.target, value, environment)
                if all(self.evaluate(condition, environment) for condition in generator.ifs):
                    results.append(self.evaluate(node.elt, environment))
                if len(results) > MAX_COLLECTION_SIZE:
                    raise AnalysisError(f"Collections are limited to {MAX_COLLECTION_SIZE} items.")
            return results
        elif isinstance(node, ast.Dict):
            return {self.evaluate(key, environment): self.evaluate(value, environment) for key, value in zip(node.keys, node.values) if key is not None}
        raise AnalysisError(f"Unsupported expression {type(node).__name__} on line {getattr(node, 'lineno', '?')}.")

    def _assign(self, target: ast.AST, value: Any, environment: dict[str, Any]) -> None:
        if isinstance(target, ast.Name):
            environment[target.id] = deepcopy(value)
        elif isinstance(target, (ast.Tuple, ast.List)):
            try:
                values = list(value)
            except TypeError as error:
                raise AnalysisError("Cannot unpack a non-iterable value.") from error
            if len(values) != len(target.elts):
                raise AnalysisError("Unpacking count does not match the assigned values.")
            for child, item in zip(target.elts, values):
                self._assign(child, item, environment)
        elif isinstance(target, ast.Subscript):
            collection = self.evaluate(target.value, environment)
            index = self.evaluate(target.slice, environment)
            if isinstance(collection, list) and isinstance(index, int):
                try:
                    collection[index] = deepcopy(value)
                except IndexError as error:
                    raise AnalysisError("List assignment index is out of range.") from error
            elif isinstance(collection, dict):
                collection[index] = deepcopy(value)
                self._checked(collection)
            else:
                raise AnalysisError("Assignments by index must target a list or dictionary.")
        elif isinstance(target, ast.Attribute):
            receiver = self.evaluate(target.value, environment)
            if not isinstance(receiver, UserInstance):
                raise AnalysisError("Instance attributes can only be assigned on a submitted class instance.")
            receiver.attributes[target.attr] = deepcopy(value)
        else:
            raise AnalysisError(f"Unsupported assignment target {type(target).__name__}.")

    def _call_user_function(self, name: str, args: list[Any], keywords: dict[str, Any], call_node: ast.Call) -> Any:
        if len(self.frames) >= MAX_CALL_DEPTH:
            raise AnalysisError(f"Function calls are limited to depth {MAX_CALL_DEPTH}.")
        function = self.functions[name]
        parameters = function.args.args
        if len(args) > len(parameters):
            raise AnalysisError(f"{name}() received too many arguments.")
        local_environment: dict[str, Any] = {}
        for index, parameter in enumerate(parameters):
            if index < len(args):
                local_environment[parameter.arg] = deepcopy(args[index])
            elif parameter.arg in keywords:
                local_environment[parameter.arg] = deepcopy(keywords[parameter.arg])
            else:
                raise AnalysisError(f"{name}() is missing argument {parameter.arg!r}.")
        allowed_keywords = {parameter.arg for parameter in parameters}
        if set(keywords) - allowed_keywords or set(keywords).intersection(parameter.arg for parameter in parameters[:len(args)]):
            raise AnalysisError(f"{name}() received an unexpected or duplicate keyword argument.")
        label = f"{name}({', '.join(self._display(value) for value in args)})"
        if "." in name and args and isinstance(args[0], UserInstance):
            label = f"{name}({', '.join(self._display(value) for value in args[1:])})"
        self.frames.append(label)
        self._tick(call_node, f"Call {label}", local_environment)
        try:
            self._execute_block(function.body, local_environment)
        except ReturnSignal as returned:
            result = returned.value
        else:
            result = None
        self.frames.pop()
        self._tick(call_node, f"Return from {name}: {self._display(result)}", local_environment)
        return result

    def _execute_block(self, statements: list[ast.stmt], environment: dict[str, Any]) -> None:
        for statement in statements:
            self.execute(statement, environment)

    def execute(self, node: ast.stmt, environment: dict[str, Any]) -> None:
        if isinstance(node, ast.FunctionDef):
            if node.decorator_list or node.args.vararg or node.args.kwarg or node.args.kwonlyargs:
                raise AnalysisError("Decorators and advanced function parameters are not supported.")
            self.functions[node.name] = node
            self._tick(node, f"Define function {node.name}()", environment)
        elif isinstance(node, ast.ClassDef):
            if node.decorator_list or node.bases or node.keywords:
                raise AnalysisError("Class decorators, inheritance, and metaclasses are not supported.")
            methods: dict[str, ast.FunctionDef] = {}
            for member in node.body:
                if isinstance(member, ast.FunctionDef):
                    if member.decorator_list or member.args.vararg or member.args.kwarg or member.args.kwonlyargs:
                        raise AnalysisError("Class methods cannot use decorators or advanced parameter syntax.")
                    methods[member.name] = member
                elif isinstance(member, ast.Pass):
                    continue
                elif isinstance(member, ast.AnnAssign) and member.value is None:
                    continue
                else:
                    raise AnalysisError(f"Unsupported class member {type(member).__name__} in {node.name}.")
            if not methods:
                raise AnalysisError(f"Class {node.name} must define at least one method.")
            user_class = UserClass(node.name, methods)
            self.classes[node.name] = user_class
            for method_name, method in methods.items():
                self.functions[f"{node.name}.{method_name}"] = method
            self._tick(node, f"Define class {node.name}", environment)
        elif isinstance(node, ast.ImportFrom):
            if node.level or node.module != "typing" or any(alias.name not in {"Any", "Dict", "List", "Optional", "Set", "Tuple"} for alias in node.names):
                raise AnalysisError("Only type annotation imports from the typing module are supported.")
            self._tick(node, "Load type annotations", environment)
        elif isinstance(node, ast.Assign):
            value = self.evaluate(node.value, environment)
            for target in node.targets:
                self._assign(target, value, environment)
            self._tick(node, "Assign variable", environment)
        elif isinstance(node, ast.AnnAssign):
            if node.value is not None:
                self._assign(node.target, self.evaluate(node.value, environment), environment)
                self._tick(node, "Assign variable", environment)
        elif isinstance(node, ast.AugAssign):
            if type(node.op) not in BIN_OPS:
                raise AnalysisError(f"Unsupported augmented operator {type(node.op).__name__}.")
            old = self.evaluate(node.target, environment)
            new = BIN_OPS[type(node.op)](old, self.evaluate(node.value, environment))
            self._assign(node.target, self._checked(new), environment)
            self._tick(node, "Update variable", environment)
        elif isinstance(node, ast.Expr):
            value = self.evaluate(node.value, environment)
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "print":
                operation = "Output: " + (self.outputs[-1] if self.outputs else "")
            else:
                operation = "Evaluate expression" if value is None else f"Expression result: {value!r}"
            self._tick(node, operation, environment)
        elif isinstance(node, ast.If):
            result = bool(self.evaluate(node.test, environment))
            self._tick(node, "Check if condition", environment, ast.unparse(node.test), result)
            self._execute_block(node.body if result else node.orelse, environment)
        elif isinstance(node, ast.For):
            if node.orelse or node.type_comment:
                raise AnalysisError("Loop else blocks and type comments are not supported.")
            values = self.evaluate(node.iter, environment)
            if not isinstance(values, (range, list, tuple, str)):
                raise AnalysisError("for loops must iterate over a list, tuple, string, or range.")
            if len(values) > MAX_LOOP_ITEMS:
                raise AnalysisError(f"Loops are limited to {MAX_LOOP_ITEMS} iterations.")
            for value in values:
                self._assign(node.target, value, environment)
                self._tick(node, "Begin loop iteration", environment)
                try:
                    self._execute_block(node.body, environment)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        elif isinstance(node, ast.While):
            if node.orelse:
                raise AnalysisError("Loop else blocks are not supported.")
            count = 0
            while True:
                result = bool(self.evaluate(node.test, environment))
                self._tick(node, "Check while condition", environment, ast.unparse(node.test), result)
                if not result:
                    break
                count += 1
                if count > MAX_LOOP_ITEMS:
                    raise AnalysisError(f"Loops are limited to {MAX_LOOP_ITEMS} iterations.")
                try:
                    self._execute_block(node.body, environment)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        elif isinstance(node, ast.Return):
            value = self.evaluate(node.value, environment) if node.value else None
            self._tick(node, f"Return {value!r}", environment)
            raise ReturnSignal(value)
        elif isinstance(node, ast.Break):
            raise BreakSignal()
        elif isinstance(node, ast.Continue):
            raise ContinueSignal()
        elif isinstance(node, ast.Pass):
            self._tick(node, "Pass", environment)
        else:
            raise AnalysisError(f"Unsupported statement {type(node).__name__} on line {getattr(node, 'lineno', '?')}.")

    def run(self) -> dict[str, Any]:
        environment: dict[str, Any] = {}
        self.global_environment = environment
        try:
            self._execute_block(self.tree.body, environment)
        except ReturnSignal as error:
            raise AnalysisError("return can only be used inside a function.") from error
        except (BreakSignal, ContinueSignal) as error:
            raise AnalysisError("break and continue can only be used inside a loop.") from error
        top_level_definitions_only = all(
            isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.ImportFrom, ast.Pass))
            for node in self.tree.body
        )
        result: Any = None
        did_call_entrypoint = False
        if top_level_definitions_only and self.classes:
            if "Solution" in self.classes:
                entry_class = self.classes["Solution"]
            elif len(self.classes) == 1:
                entry_class = next(iter(self.classes.values()))
            else:
                raise AnalysisError("Define one class named Solution, or keep only one class for automatic dry run.")
            method_names = [name for name in entry_class.methods if not name.startswith("_")]
            if len(method_names) != 1:
                raise AnalysisError(
                    f"{entry_class.name} needs exactly one public method for automatic invocation; found {len(method_names)}."
                )
            method_name = method_names[0]
            method = entry_class.methods[method_name]
            method_parameters = method.args.args[1:]
            arguments = self._entry_arguments(method_parameters)
            instance = self._construct_instance(entry_class, [], {})
            self._tick(self.tree, f"Create {entry_class.name}()", environment)
            result = self._call_user_function(
                f"{entry_class.name}.{method_name}",
                [instance, *arguments],
                {},
                method,
            )
            environment["result"] = deepcopy(result)
            self._tick(entry_class.methods[method_name], f"LeetCode result: {self._display(result)}", environment)
            did_call_entrypoint = True
        elif top_level_definitions_only:
            public_functions = [name for name in self.functions if not name.startswith("_") and "." not in name]
            if len(public_functions) == 1:
                function_name = public_functions[0]
                arguments = self._entry_arguments(self.functions[function_name].args.args)
                result = self._call_user_function(function_name, arguments, {}, self.functions[function_name])
                environment["result"] = deepcopy(result)
                self._tick(self.functions[function_name], f"Function result: {self._display(result)}", environment)
                did_call_entrypoint = True
        if not self.steps:
            self._tick(self.tree, "Program completed", environment)
        if did_call_entrypoint and result is not None:
            summary = json.dumps(self._snapshot(result), ensure_ascii=False)
        elif did_call_entrypoint:
            summary = "None"
        else:
            summary = self.outputs[-1] if self.outputs and self.outputs[-1] else f"Dry run complete · {len(self.steps)} steps."
        return {
            "algorithm": "custom_python",
            "title": detect_algorithm(self.source, self.tree),
            "steps": self.steps,
            "summary": summary,
        }

    def _entry_arguments(self, parameters: list[ast.arg]) -> list[Any]:
        expected_count = len(parameters)
        if not self.input_lines or not "".join(self.input_lines).strip():
            if expected_count:
                raise AnalysisError(f"This entry point needs {expected_count} argument(s). Enter them as a JSON array.")
            return []
        raw_arguments = "\n".join(self.input_lines).strip()
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError as error:
            raise AnalysisError(
                "For LeetCode-style functions, enter arguments as JSON, e.g. [[2, 7, 11, 15], 9] or [1, 2, 1] for one list argument."
            ) from error
        if expected_count == 1:
            parameter_annotation = parameters[0].annotation
            expects_list = isinstance(parameter_annotation, ast.Subscript) and isinstance(parameter_annotation.value, ast.Name) and parameter_annotation.value.id in {"list", "List"}
            if not isinstance(arguments, list):
                arguments = [arguments]
            elif (expects_list or len(arguments) != 1) and not (len(arguments) == 1 and isinstance(arguments[0], list)):
                # Accept the intuitive LeetCode sample form [1, 2, 1] for a
                # method whose sole parameter is nums: list[int], as well as
                # the explicit positional-argument form [[1, 2, 1]].
                arguments = [arguments]
        elif not isinstance(arguments, list):
            raise AnalysisError("LeetCode-style input must be a JSON array of positional method arguments.")
        if len(arguments) != expected_count:
            raise AnalysisError(
                f"This entry point expects {expected_count} argument(s), but the input provides {len(arguments)}. "
                "For a single list parameter, enter [1, 2, 1] or [[1, 2, 1]]."
            )
        return [self._validate_json_value(value) for value in arguments]

    def _validate_json_value(self, value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return self._checked(value)
        if isinstance(value, list):
            return self._checked([self._validate_json_value(item) for item in value])
        if isinstance(value, dict):
            return self._checked({str(key): self._validate_json_value(item) for key, item in value.items()})
        raise AnalysisError("Method input must contain JSON values only.")


def analyze_python(source: str, sample_input: str = "") -> dict[str, Any]:
    """Analyze and dry-run source code using the restricted interpreter."""
    if not source.strip():
        raise AnalysisError("Write Python code in the editor before running the dry run.")
    try:
        return DryRunInterpreter(source, sample_input).run()
    except AnalysisError:
        raise
    except (TypeError, ValueError, IndexError, KeyError, ZeroDivisionError, OverflowError) as error:
        raise AnalysisError(f"Dry run stopped safely: {error}") from error
