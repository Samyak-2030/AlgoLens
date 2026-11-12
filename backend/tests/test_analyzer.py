import unittest

from app.analyzer import AnalysisError, analyze_python


class AnalyzePythonTests(unittest.TestCase):
    def test_reads_sample_input_and_traces_accumulator(self) -> None:
        result = analyze_python(
            "raw = input()\nvalues = list(map(int, raw.split()))\ntotal = 0\n"
            "for value in values:\n    total += value\nprint(total)",
            "3 5 7",
        )
        self.assertEqual(result["summary"], "15")
        self.assertEqual(result["title"], "Array aggregation · sum")
        self.assertTrue(any(step["variables"].get("total") == 15 for step in result["steps"]))

    def test_input_is_raw_and_consumed_one_line_per_call(self) -> None:
        result = analyze_python(
            "first = input()\nsecond = input()\nprint(first)\nprint(second)",
            "alpha,beta\n42",
        )
        self.assertEqual(result["summary"], "42")
        self.assertEqual(result["steps"][0]["variables"]["first"], "alpha,beta")
        self.assertEqual(result["steps"][1]["variables"]["second"], "42")

    def test_sequence_snapshot_is_optional_and_named(self) -> None:
        scalar = analyze_python("value = int(input())", "9")
        sequence = analyze_python("names = ['Ada', 'Lin']")
        self.assertIsNone(scalar["steps"][0]["sequence_name"])
        self.assertEqual(sequence["steps"][0]["sequence_name"], "names")
        self.assertEqual(sequence["steps"][0]["array"], ["Ada", "Lin"])

    def test_leetcode_solution_class_is_instantiated_and_method_is_called(self) -> None:
        result = analyze_python(
            "from typing import List\n\nclass Solution:\n"
            "    def twoSum(self, nums: List[int], target: int) -> List[int]:\n"
            "        seen = {}\n"
            "        for i, value in enumerate(nums):\n"
            "            needed = target - value\n"
            "            if needed in seen:\n"
            "                return [seen[needed], i]\n"
            "            seen[value] = i\n",
            "[[2, 7, 11, 15], 9]",
        )
        self.assertEqual(result["summary"], "[0, 1]")
        self.assertTrue(any("Solution.twoSum" in frame for step in result["steps"] for frame in step["call_stack"]))
        self.assertTrue(any(step["array"] == [2, 7, 11, 15] for step in result["steps"]))

    def test_single_top_level_function_uses_json_arguments(self) -> None:
        result = analyze_python("def double(value: int) -> int:\n    return value * 2", "[7]")
        self.assertEqual(result["summary"], "14")

    def test_leetcode_class_rejects_non_json_arguments_with_guidance(self) -> None:
        with self.assertRaisesRegex(AnalysisError, "enter arguments as JSON"):
            analyze_python("class Solution:\n    def answer(self, n):\n        return n", "not-json")

    def test_next_greater_elements_accepts_direct_single_list_input(self) -> None:
        source = (
            "class Solution:\n"
            "    def nextGreaterElements(self, nums: list[int]) -> list[int]:\n"
            "        n = len(nums)\n"
            "        doubled = nums + nums\n"
            "        ans = [-1] * n\n"
            "        stack = []\n"
            "        for i in range(2 * n - 1, -1, -1):\n"
            "            while stack and stack[-1] <= doubled[i]:\n"
            "                stack.pop()\n"
            "            if i < n:\n"
            "                if stack:\n"
            "                    ans[i] = stack[-1]\n"
            "            stack.append(doubled[i])\n"
            "        return ans\n"
        )
        direct_input = analyze_python(source, "[1, 2, 1]")
        wrapped_input = analyze_python(source, "[[1, 2, 1]]")
        self.assertEqual(direct_input["title"], "Monotonic stack · next greater element")
        self.assertEqual(direct_input["summary"], "[2, -1, 2]")
        self.assertEqual(wrapped_input["summary"], "[2, -1, 2]")
        self.assertTrue(any(step["array"] == [1, 2, 1] for step in direct_input["steps"]))

    def test_traces_condition_results_and_array_state(self) -> None:
        result = analyze_python(
            "values = [1, 2, 3]\nfor i in range(len(values)):\n"
            "    if values[i] > 1:\n        picked = values[i]\nprint(picked)"
        )
        branch_steps = [step for step in result["steps"] if step["condition"]]
        self.assertEqual([step["condition_result"] for step in branch_steps], [False, True, True])
        self.assertEqual(branch_steps[0]["array"], [1, 2, 3])

    def test_supports_recursive_function_calls(self) -> None:
        result = analyze_python(
            "def factorial(n):\n    if n <= 1:\n        return 1\n"
            "    return n * factorial(n - 1)\nprint(factorial(int(input())))",
            "5",
        )
        self.assertEqual(result["title"], "Recursive algorithm")
        self.assertEqual(result["summary"], "120")
        self.assertTrue(any(len(step["call_stack"]) > 2 for step in result["steps"]))

    def test_rejects_imports_and_unrestricted_calls(self) -> None:
        with self.assertRaisesRegex(AnalysisError, "Unsupported statement Import"):
            analyze_python("import os\nos.system('whoami')")

    def test_bounds_loop_work(self) -> None:
        with self.assertRaisesRegex(AnalysisError, "limited to 100 iterations"):
            analyze_python("for i in range(101):\n    print(i)")


if __name__ == "__main__":
    unittest.main()
