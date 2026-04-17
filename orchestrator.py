from agents.architect import ArchitectAgent
from agents.developer import DeveloperAgent
from agents.test_engineer import TestEngineerAgent
from agents.evaluator import EvaluatorAgent
from llm_client import LLMClient
from sandbox import run_code_safely, parse_test_results, run_static_analysis
import time


class Orchestrator:
    def __init__(self):
        self.client = LLMClient()
        self.architect = ArchitectAgent(self.client)
        self.developer = DeveloperAgent(self.client)
        self.test_engineer = TestEngineerAgent(self.client)
        self.evaluator = EvaluatorAgent(self.client)
        self.logs = []

    def log(self, agent_name: str, message: str):
        """Helper to track agent thoughts for the UI."""
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(
            {"timestamp": timestamp, "agent": agent_name, "message": message}
        )

    def run_pipeline(self, problem_description: str, max_retries: int = 2):
        """
        Runs the full agentic pipeline: Spec -> Code -> Test -> Evaluate -> Refine.
        The spec is regenerated on every iteration so self-healing actually works.
        """
        self.log("Orchestrator", "Starting pipeline for new problem...")

        iteration = 0
        while iteration < max_retries:
            self.log("Orchestrator", f"--- Iteration {iteration + 1}/{max_retries} ---")

            # 1. Architect Stage — runs EVERY iteration so feedback is incorporated
            self.log("Architect", "Analyzing problem and generating technical specification...")
            spec = self.architect.analyze_problem(problem_description)

            # Bug 1 Fix: Detect architect failure and retry ONCE before wasting
            # an entire developer/test/eval cycle on a garbage fallback spec.
            if spec.problem_name == "Error Analyzing Problem":
                self.log("Architect", "⚠️ Spec parse failed. Retrying with cleaner prompt...")
                spec = self.architect.analyze_problem(
                    f"Analyze this DSA problem carefully and return ONLY valid JSON:\n\n{problem_description}"
                )

            self.log("Architect", f"Spec generated: {spec.problem_name}")

            # 2. Developer Stage
            self.log("Developer", "Writing Python implementation...")
            code = self.developer.implement_solution(spec)

            # 3. Test Engineer Stage
            self.log("Test Engineer", "Generating adversarial test suite...")
            test_script = self.test_engineer.generate_tests(spec, code)

            # 4. Sandbox Stage — solution and tests in SEPARATE files
            self.log("Sandbox", "Executing code and tests in isolated environment...")
            execution_result = run_code_safely(code, test_script)

            # Combine stdout and stderr for the evaluator's context
            test_output = (
                f"STDOUT:\n{execution_result['stdout']}\n\n"
                f"STDERR:\n{execution_result['stderr']}"
            )

            # 5. Parse REAL test results — no hallucination
            self.log("Sandbox", "Parsing objective test results...")
            parsed = parse_test_results(execution_result["stderr"])
            self.log(
                "Sandbox",
                f"Ground truth: {parsed['passed']}/{parsed['total']} passed, "
                f"{parsed['failed']} failed",
            )

            # 6. Static Analysis — pylint + radon
            self.log("Sandbox", "Running static analysis (pylint & radon)...")
            static = run_static_analysis(code)
            self.log(
                "Sandbox",
                f"Pylint: {static['pylint_score']}/10 | "
                f"Complexity: {static['complexity_grade']}",
            )

            # 7. Build objective metrics dict
            objective_metrics = {
                "passed": parsed["passed"],
                "total": parsed["total"],
                "failed": parsed["failed"],
                "pylint_score": static["pylint_score"],
                "complexity_grade": static["complexity_grade"],
            }

            # 8. Evaluator Stage — grounded in real measurements
            self.log("Evaluator", "Assessing correctness, complexity, and trust score...")
            report = self.evaluator.evaluate(spec, code, test_output, objective_metrics)

            self.log(
                "Evaluator",
                f"Evaluation Complete. Grade: {report.trust_grade} | "
                f"Score: {report.trust_score} | Verdict: {report.verdict}",
            )

            # Check for success or final iteration
            if report.verdict == "APPROVED" or iteration == max_retries - 1:
                if report.verdict != "APPROVED":
                    self.log(
                        "Orchestrator",
                        "Max retries reached. Returning best available result.",
                    )
                else:
                    self.log("Orchestrator", "Pipeline finished — code APPROVED.")
                return {
                    "spec": spec,
                    "code": code,
                    "test_script": test_script,
                    "report": report,
                    "execution_output": test_output,
                    "objective_metrics": objective_metrics,
                    "logs": self.logs,
                    "iterations_used": iteration + 1,
                }

            # Self-Healing: Feed PRECISE failure information back for next iteration
            # Extract only the failure details from stderr — not the entire output
            stderr = execution_result["stderr"]
            failure_lines = [
                line for line in stderr.splitlines()
                if any(kw in line for kw in ["FAIL", "ERROR", "AssertionError", "Exception", "Traceback"])
            ]
            failure_summary = "\n".join(failure_lines[:30]) if failure_lines else stderr[:500]

            self.log(
                "Orchestrator",
                f"Feeding {parsed['failed']} specific failure(s) back to Architect...",
            )
            problem_description = (
                f"{problem_description.split('REFINEMENT FEEDBACK')[0].strip()}\n\n"
                f"=== PREVIOUS ATTEMPT FAILED ===\n"
                f"Tests: {parsed['passed']}/{parsed['total']} passed | "
                f"Pylint: {static['pylint_score']}/10\n"
                f"Expert Feedback: {report.feedback}\n\n"
                f"Specific Failures:\n{failure_summary}\n"
                f"Fix these exact failures in your next implementation."
            )
            iteration += 1

        return None  # Should not reach here


if __name__ == "__main__":
    orch = Orchestrator()
    results = orch.run_pipeline(
        "Write a function to find the maximum sum of a contiguous subarray."
    )
    if results:
        print(f"Final Grade: {results['report'].trust_grade}")
        print(f"Iterations: {results['iterations_used']}")
