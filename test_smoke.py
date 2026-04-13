"""Quick smoke test for the new sandbox logic."""
from sandbox import run_code_safely, parse_test_results, run_static_analysis

solution = "def add(a, b):\n    return a + b\n"

tests = """import unittest

class TestAdd(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(add(1, 2), 3)

    def test_negative(self):
        self.assertEqual(add(-1, -2), -3)

    def test_zero(self):
        self.assertEqual(add(0, 0), 0)

if __name__ == '__main__':
    unittest.main()
"""

print("=== Running sandbox ===")
result = run_code_safely(solution, tests)
print(f"Success: {result['success']}")
print(f"STDOUT: {result['stdout']}")
print(f"STDERR: {result['stderr']}")

print("\n=== Parsing test results ===")
parsed = parse_test_results(result["stderr"])
print(f"Parsed: {parsed}")

print("\n=== Static analysis ===")
static = run_static_analysis(solution)
print(f"Static: {static}")
