from llm_client import LLMClient
from agents.architect import TechnicalSpec


class DeveloperAgent:
    def __init__(self, client: LLMClient):
        self.client = client
        self.system_prompt = """
        You are an Elite Python Developer specializing in high-performance DSA implementations.
        Your task is to implement code based on a Technical Specification.
        
        RULES:
        1. Write clean, readable, and efficient Python code.
        2. Follow the constraints and suggestions provided in the spec.
        3. The implementation MUST use the EXACT function or class name specified in `entry_point`.
        4. DO NOT include test cases in the code output; only the implementation.
        5. OUTPUT ONLY THE PYTHON CODE within markdown code blocks.
        """

    def implement_solution(self, spec: TechnicalSpec, max_retries: int = 2) -> str:
        """
        entry_point is explicitly passed in the prompt so the LLM MUST use that exact name.
        The generated code is validated for non-empty output, syntactic validity,
        and presence of the required entry_point name.
        Retries up to max_retries times if validation fails.
        """
        user_prompt = (
            f"Implement the solution for '{spec.problem_name}' based on this spec:\n\n"
            f"{spec.model_dump_json(indent=2)}\n\n"
            f"CRITICAL: Your implementation MUST define a function or class named "
            f"exactly `{spec.entry_point}`. This is non-negotiable."
        )

        for attempt in range(max_retries + 1):
            if attempt > 0:
                user_prompt = (
                    f"RETRY ATTEMPT {attempt}: Your previous code was invalid or missing "
                    f"the required name `{spec.entry_point}`.\n\n" + user_prompt
                )

            response = self.client.generate(self.system_prompt, user_prompt)
            code = self._extract_code(response)

            validation_error = self._validate_code(code, spec.entry_point)
            if validation_error is None:
                return code

            print(
                f"[DeveloperAgent] Attempt {attempt + 1} invalid: {validation_error}. Retrying..."
            )

        print("[DeveloperAgent] All retries exhausted. Returning last attempt.")
        return code

    def _extract_code(self, response: str) -> str:
        """Extracts Python code from markdown fences."""
        if "```python" in response:
            return response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            return response.split("```")[1].split("```")[0].strip()
        return response.strip()

    def _validate_code(self, code: str, entry_point: str) -> str | None:
        """
        Returns None if code is valid, or an error string describing the problem.
        Checks: non-empty, syntactically valid Python, contains the required entry_point name.
        """
        if not code or not code.strip():
            return "Generated code is empty"

        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            return f"SyntaxError: {e}"

        if entry_point not in code:
            return f"Missing required entry_point: '{entry_point}' not found in generated code"

        return None


if __name__ == "__main__":
    client = LLMClient()
    dev = DeveloperAgent(client)

    dummy_spec = TechnicalSpec(
        problem_name="First Non-Repeating Character",
        entry_point="first_non_repeating",
        logic_requirements=["Find first char that appears once", "Return index or -1"],
        constraints=["O(n) time", "O(k) space"],
        edge_cases=["Empty string", "All repeating", "All unique"],
        suggested_data_structures=["Frequency Hash Map"],
    )

    code = dev.implement_solution(dummy_spec)
    print("--- GENERATED CODE ---")
    print(code)
