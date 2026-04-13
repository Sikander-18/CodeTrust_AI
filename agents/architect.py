from pydantic import BaseModel, Field
from typing import List, Optional
from llm_client import LLMClient
import json

class TechnicalSpec(BaseModel):
    problem_name: str
    entry_point: str = Field(description="The main function or class name to test, e.g. 'LFUCache' or 'max_subarray'")
    logic_requirements: List[str] = Field(description="Core functional requirements")
    constraints: List[str] = Field(description="Time and space complexity constraints")
    edge_cases: List[str] = Field(description="Specific edge cases to handle")
    suggested_data_structures: List[str]


class ArchitectAgent:
    def __init__(self, client: LLMClient):
        self.client = client
        self.system_prompt = """
        You are an Expert Software Architect specializing in Data Structures and Algorithms (DSA).
        Your job is to analyze a coding problem and create a rigorous Technical Specification.
        Focus on:
        1. Explicit logic requirements.
        2. Big O complexity constraints (Time & Space).
        3. Critical edge cases (empty inputs, large values, duplicates, etc.).
        4. Optimal choice of data structures.
        
        OUTPUT ONLY VALID JSON that matches the provided schema.
        """

    def analyze_problem(self, problem_description: str) -> TechnicalSpec:
        user_prompt = f"Analyze this problem and provide a technical spec:\n\n{problem_description}"
        
        # We add schema instructions to ensure the LLM follows the Pydantic model
        schema_instruction = f"\n\nReturn the result as JSON matching this structure: {TechnicalSpec.model_json_schema()}"
        
        response = self.client.generate(self.system_prompt, user_prompt + schema_instruction)
        
        try:
            # Strip any markdown code blocks if present
            clean_json = response.strip().replace("```json", "").replace("```", "").strip()
            spec_data = json.loads(clean_json)
            return TechnicalSpec(**spec_data)
        except Exception as e:
            # Fallback/Error handling
            print(f"Error parsing Architect response: {e}")
            return TechnicalSpec(
                problem_name="Error Analyzing Problem",
                entry_point="solution",
                logic_requirements=["Error in analysis"],
                constraints=["N/A"],
                edge_cases=["N/A"],
                suggested_data_structures=["N/A"]
            )

if __name__ == "__main__":
    # Test the architect
    from llm_client import LLMClient
    client = LLMClient()
    architect = ArchitectAgent(client)
    spec = architect.analyze_problem("Write a function to find the first non-repeating character in a string.")
    print(spec.model_dump_json(indent=2))
