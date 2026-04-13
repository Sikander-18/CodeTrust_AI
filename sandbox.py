import subprocess
import tempfile
import os
import sys
import re


def run_code_safely(solution_code: str, test_code: str, timeout: int = 15):
    """
    Executes the solution and test code in separate files within an isolated
    temporary directory. The test file imports from the solution file, ensuring
    we test the EXACT code the Developer agent wrote — not a copy.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write the Developer's code to solution.py
        solution_path = os.path.join(tmpdir, "solution.py")
        with open(solution_path, "w") as f:
            f.write(solution_code)

        # Prepend the import and write the test file
        full_test_code = f"from solution import *\n\n{test_code}"
        test_path = os.path.join(tmpdir, "test_solution.py")
        with open(test_path, "w") as f:
            f.write(full_test_code)

        try:
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "test_solution"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Error: Execution timed out after {timeout} seconds.",
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"System Error: {str(e)}",
            }


def parse_test_results(stderr_text: str) -> dict:
    """
    Parses the unittest output to extract real pass/fail counts.
    unittest prints its summary to stderr, not stdout.
    Returns grounded numbers — never hallucinated.
    """
    total = 0
    failures = 0
    errors = 0

    # unittest prints "Ran X test(s)" to stderr
    ran_match = re.search(r"Ran (\d+) test", stderr_text)
    if ran_match:
        total = int(ran_match.group(1))

    fail_match = re.search(r"failures=(\d+)", stderr_text)
    if fail_match:
        failures = int(fail_match.group(1))

    err_match = re.search(r"errors=(\d+)", stderr_text)
    if err_match:
        errors = int(err_match.group(1))

    passed = max(0, total - failures - errors)

    return {"total": total, "passed": passed, "failed": failures + errors}


def run_static_analysis(code: str) -> dict:
    """
    Runs pylint and radon on the provided code string.
    Returns objective, tool-measured quality metrics.
    Silently returns N/A if tools are not installed.
    """
    result = {"pylint_score": "N/A", "complexity_grade": "N/A"}

    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = os.path.join(tmpdir, "analyzed_code.py")
        with open(code_path, "w") as f:
            f.write(code)

        # --- Pylint ---
        try:
            pylint_result = subprocess.run(
                [sys.executable, "-m", "pylint", "--score=y", "--output-format=text", code_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            score_match = re.search(
                r"Your code has been rated at ([\d.]+)/10", pylint_result.stdout
            )
            if score_match:
                result["pylint_score"] = score_match.group(1)
        except Exception:
            pass  # pylint not installed or failed — keep N/A

        # --- Radon (Cyclomatic Complexity) ---
        try:
            radon_result = subprocess.run(
                [sys.executable, "-m", "radon", "cc", "-s", "-a", code_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Radon prints "Average complexity: X (Y)" on the last meaningful line
            lines = radon_result.stdout.strip().splitlines()
            if lines:
                last_line = lines[-1]
                grade_match = re.search(r"\(([A-F])\)", last_line)
                if grade_match:
                    result["complexity_grade"] = grade_match.group(1)
        except Exception:
            pass  # radon not installed or failed — keep N/A

    return result


if __name__ == "__main__":
    sol = "def add(a, b):\n    return a + b"
    tests = """import unittest

class TestAdd(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(add(1, 2), 3)
    def test_negative(self):
        self.assertEqual(add(-1, -2), -3)

if __name__ == '__main__':
    unittest.main()
"""
    res = run_code_safely(sol, tests)
    print("Execution:", res)
    print("Parsed:", parse_test_results(res["stderr"]))
    print("Static:", run_static_analysis(sol))
