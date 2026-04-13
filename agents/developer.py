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
        3. ALWAYS provide a standalone function.
        4. DO NOT include test cases in the code output; only the implementation.
        5. OUTPUT ONLY THE PYTHON CODE within markdown code blocks.
        """

    def implement_solution(self, spec: TechnicalSpec) -> str:
        user_prompt = f"Implement the solution for '{spec.problem_name}' based on this spec:\n\n{spec.model_dump_json(indent=2)}"
        
        response = self.client.generate(self.system_prompt, user_prompt)
        
        # Clean up the response to extract just the code
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0].strip()
        elif "```" in response:
            code = response.split("```")[1].split("```")[0].strip()
        else:
            code = response.strip()
            
        return code

if __name__ == "__main__":
    # Test the developer
    from llm_client import LLMClient
    from agents.architect import TechnicalSpec
    
    client = LLMClient()
    dev = DeveloperAgent(client)
    
    dummy_spec = TechnicalSpec(
        problem_name="First Non-Repeating Character",
        logic_requirements=["Find first char that appears once", "Return index or -1"],
        constraints=["O(n) time", "O(k) space"],
        edge_cases=["Empty string", "All repeating", "All unique"],
        suggested_data_structures=["Frequency Hash Map"]
    )
    
    code = dev.implement_solution(dummy_spec)
    print("--- GENERATED CODE ---")
    print(code)
