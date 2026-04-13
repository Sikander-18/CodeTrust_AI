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
        3. Cover core requirements AND 'Generator Killer' cases:
            - Adversarial Stress Tests: Perform 100+ random operations (put/get/etc.) in a loop.
            - Pattern-Breakers: High frequency skew, alternating access, large data volumes.
            - Deep Invariants: Test if internal pointers (like min_freq in LFU) stay synced.
        4. Print clearly which specific adversarial test passed or failed.
        5. OUTPUT ONLY THE PYTHON CODE within markdown code blocks.
        """

    def generate_tests(self, spec: TechnicalSpec, solution_code: str) -> str:
        user_prompt = f"""
        Generate an adversarial test suite for the implementation of '{spec.problem_name}'.
        
        SPECIFICATION:
        {spec.model_dump_json(indent=2)}
        
        IMPLEMENTATION (for reference only — do NOT copy this into your output):
        ```python
        {solution_code}
        ```
        
        Write tests assuming `from solution import *` is already at the top of the file.
        Do NOT include or redefine the implementation. Only write test classes and the runner.
        """

        response = self.client.generate(self.system_prompt, user_prompt)

        # Clean up the response to extract just the code
        if "```python" in response:
            test_code = response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            test_code = response.split("```")[1].split("```")[0].strip()
        else:
            test_code = response.strip()

        return test_code


if __name__ == "__main__":
    from llm_client import LLMClient
    from agents.architect import TechnicalSpec

    client = LLMClient()
    test_eng = TestEngineerAgent(client)

    dummy_spec = TechnicalSpec(
        problem_name="Add Two Numbers",
        logic_requirements=["Add two integers"],
        constraints=["O(1)"],
        edge_cases=["Negative numbers", "Zero"],
        suggested_data_structures=["None"],
    )

    dummy_code = "def add(a, b):\n    return a + b"

    tests = test_eng.generate_tests(dummy_spec, dummy_code)
    print("--- GENERATED TESTS ---")
    print(tests)
