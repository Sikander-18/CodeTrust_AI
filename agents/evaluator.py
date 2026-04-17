from pydantic import BaseModel, Field
from llm_client import LLMClient
from agents.architect import TechnicalSpec
import json
import re


class EvaluationReport(BaseModel):
    trust_score: int = Field(ge=0, le=100)
    trust_grade: str  # A, B, C, D, F
    time_complexity: str
    space_complexity: str
    passed_tests: int
    total_tests: int
    edge_case_resilience: str
    verdict: str  # "APPROVED" or "NEEDS_REFINEMENT"
    feedback: str


def extract_json_from_text(text: str) -> dict:
    """
    Robustly extracts a JSON object from LLM output that may contain
    markdown fences, explanations, or other surrounding text.
    """
    cleaned = text.strip()

    # Strategy 1: Try the raw text as-is
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown code fences
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Find the first { ... } block using brace matching
    start = cleaned.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(cleaned)):
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break

    # Strategy 4: Regex for JSON-like block
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from LLM response: {text[:200]}...")


class EvaluatorAgent:
    def __init__(self, client: LLMClient):
        self.client = client
        self.system_prompt = """
        You are the Supreme Evaluator and Judge of AI-generated code.
        Your responsibility is to calculate a 'Trust Score' based on ADVERSARIAL resilience.
        
        CRITERIA:
        1. Correctness: Did it pass standard AND adversarial 'Generator Killer' tests?
        2. Efficiency: Is it the optimal Big O? Is it memory-efficient?
        3. Resilience: Does it handle high-frequency skew and random operation sequences?
        4. State Integrity: Do internal markers (like counters/pointers) stay synced under stress?
        
        TRUST GRADE SCALE:
        - A: 90-100 (Optimal, Passes all Adversarial Stress Tests)
        - B: 80-89 (Correct, passes standard but might have minor stress issues)
        - C: 70-79 (Correct but inefficient or shows memory growth risk)
        - D: 50-69 (Fails adversarial tests but passes basic logic)
        - F: <50 (Major logic failures)
        
        NEVER invent or guess passed_tests or total_tests.
        Always use the OBJECTIVE MEASUREMENTS provided.
        
        You MUST respond with ONLY a valid JSON object. No explanations, no markdown, no text before or after the JSON.
        """

    def evaluate(
        self,
        spec: TechnicalSpec,
        code: str,
        test_output: str,
        objective_metrics: dict,
    ) -> EvaluationReport:
        user_prompt = f"""
        Evaluate this implementation based on the testing results.
        
        SPECIFICATION:
        {spec.model_dump_json(indent=2)}
        
        IMPLEMENTATION:
        ```python
        {code}
        ```
        
        TEST EXECUTION OUTPUT:
        {test_output}
        
        OBJECTIVE MEASUREMENTS (ground truth — do not override these):
        - Tests passed: {objective_metrics['passed']}/{objective_metrics['total']}  |  Failed: {objective_metrics['failed']}
        - Pylint code quality score: {objective_metrics['pylint_score']}/10
        - Cyclomatic complexity grade: {objective_metrics['complexity_grade']}
        
        Use these exact numbers for passed_tests and total_tests in your JSON output.
        Only use your judgment for trust_score, trust_grade, complexity analysis,
        edge_case_resilience, verdict, and feedback.
        
        Respond with ONLY a JSON object matching this schema (no other text):
        {json.dumps(EvaluationReport.model_json_schema(), indent=2)}
        """

        response = self.client.generate(self.system_prompt, user_prompt)

        try:
            eval_data = extract_json_from_text(response)

            # FORCE ground-truth metrics — never trust the LLM for these
            eval_data["passed_tests"] = objective_metrics["passed"]
            eval_data["total_tests"] = objective_metrics["total"]

            # FORCE verdict to valid enum — LLM often writes descriptive text
            # which permanently breaks the loop exit condition
            raw_verdict = str(eval_data.get("verdict", "")).upper()
            if "APPROVED" in raw_verdict or eval_data.get("trust_score", 0) >= 90:
                eval_data["verdict"] = "APPROVED"
            else:
                eval_data["verdict"] = "NEEDS_REFINEMENT"

            return EvaluationReport(**eval_data)
        except Exception as e:
            print(f"Error parsing Evaluator response: {e}")
            print(f"Raw response was: {response[:500]}")

            # Compute a basic trust score from ground truth so it's not always 0
            if objective_metrics["total"] > 0:
                raw_score = int(
                    (objective_metrics["passed"] / objective_metrics["total"]) * 100
                )
            else:
                raw_score = 0

            grade_map = {
                range(90, 101): "A",
                range(80, 90): "B",
                range(70, 80): "C",
                range(50, 70): "D",
                range(0, 50): "F",
            }
            grade = "F"
            for r, g in grade_map.items():
                if raw_score in r:
                    grade = g
                    break

            return EvaluationReport(
                trust_score=raw_score,
                trust_grade=grade,
                time_complexity="Unknown (Evaluator parse error)",
                space_complexity="Unknown (Evaluator parse error)",
                passed_tests=objective_metrics.get("passed", 0),
                total_tests=objective_metrics.get("total", 0),
                edge_case_resilience="Could not determine",
                verdict="NEEDS_REFINEMENT" if raw_score < 80 else "APPROVED",
                feedback=f"Evaluator failed to return valid JSON. "
                f"Ground-truth score: {objective_metrics['passed']}/{objective_metrics['total']} tests passed.",
            )


if __name__ == "__main__":
    from llm_client import LLMClient

    client = LLMClient()
    evaluator = EvaluatorAgent(client)
    # Test call...
