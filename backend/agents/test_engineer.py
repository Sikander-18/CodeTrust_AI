from llm_client import LLMClient
from agents.architect import TechnicalSpec


class TestEngineerAgent:
    def __init__(self, client: LLMClient):
        self.client = client
        self.system_prompt = """
        You are a Senior Adversarial QA Engineer specializing in DSA Unit Testing and Stress Testing.
        Your task is to generate a comprehensive testing script that tries to BREAK the provided implementation.
        
        RULES:
        1. Use the `unittest` framework.
        2. Assume the solution is already available via `from solution import *`.
           Write ONLY the test class and the `if __name__` runner block.
           Do NOT embed, redefine, or copy the implementation code.
        3. Use the EXACT function or class name specified in `entry_point` in all test calls.
        4. Cover core requirements AND 'Generator Killer' cases:
            - Adversarial Stress Tests: Perform 100+ random operations in a loop.
            - Pattern-Breakers: High frequency skew, alternating access, large data volumes.
            - Deep Invariants: Test if internal state stays synced under stress.
        5. The output MUST end with:
           if __name__ == '__main__':
               unittest.main()
        6. OUTPUT ONLY THE PYTHON CODE within markdown code blocks.
        """

    def generate_tests(
        self, spec: TechnicalSpec, solution_code: str, max_retries: int = 2
    ) -> str:
        """
        entry_point is explicitly injected into the prompt.
        Validates the returned test code has unittest structure and
        the mandatory __main__ block. Retries if invalid.
        """
        user_prompt = (
            f"Generate an adversarial test suite for '{spec.problem_name}'.\n\n"
            f"ENTRY POINT (use this EXACT name in all tests): `{spec.entry_point}`\n\n"
            f"SPECIFICATION:\n{spec.model_dump_json(indent=2)}\n\n"
            f"IMPLEMENTATION (for reference only — do NOT copy into your output):\n"
            f"```python\n{solution_code}\n```\n\n"
            f"Write tests assuming `from solution import *` is at the top.\n"
            f"Do NOT include the implementation. Only write test classes and the runner.\n"
            f"End the file with:\n"
            f"if __name__ == '__main__':\n    unittest.main()"
        )

        for attempt in range(max_retries + 1):
            if attempt > 0:
                user_prompt = (
                    f"RETRY {attempt}: Your previous test code was invalid (missing unittest "
                    f"structure or __main__ block). Fix it.\n\n" + user_prompt
                )

            response = self.client.generate(self.system_prompt, user_prompt)
            test_code = self._extract_code(response)

            validation_error = self._validate_tests(test_code, spec.entry_point)
            if validation_error is None:
                return test_code

            print(
                f"[TestEngineerAgent] Attempt {attempt + 1} invalid: {validation_error}. Retrying..."
            )

        print("[TestEngineerAgent] All retries exhausted. Returning last attempt.")
        return test_code

    def _extract_code(self, response: str) -> str:
        """Extracts Python code from markdown fences."""
        if "```python" in response:
            return response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            return response.split("```")[1].split("```")[0].strip()
        return response.strip()

    def _validate_tests(self, test_code: str, entry_point: str) -> str | None:
        """
        Returns None if test code is valid, or an error string.
        Checks: non-empty, uses unittest, has a test class, has __main__ runner, references entry_point.
        """
        if not test_code or not test_code.strip():
            return "Test code is empty"
        if "unittest" not in test_code:
            return "Missing 'unittest' import or usage"
        if "class Test" not in test_code and "class test" not in test_code:
            return "No test class found (expected 'class Test...')"
        if "__main__" not in test_code:
            return "Missing 'if __name__ == __main__' runner block"
        if entry_point not in test_code:
            return f"Entry point '{entry_point}' not referenced in tests"
        return None


if __name__ == "__main__":
    client = LLMClient()
    test_eng = TestEngineerAgent(client)

    dummy_spec = TechnicalSpec(
        problem_name="Add Two Numbers",
        entry_point="add",
        logic_requirements=["Add two integers"],
        constraints=["O(1)"],
        edge_cases=["Negative numbers", "Zero"],
        suggested_data_structures=["None"],
    )

    dummy_code = "def add(a, b):\n    return a + b"
    tests = test_eng.generate_tests(dummy_spec, dummy_code)
    print("--- GENERATED TESTS ---")
    print(tests)
