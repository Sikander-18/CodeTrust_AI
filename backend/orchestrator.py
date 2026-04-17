from agents.architect import ArchitectAgent
from agents.developer import DeveloperAgent
from agents.test_engineer import TestEngineerAgent
from agents.evaluator import EvaluatorAgent
from llm_client import LLMClient
from sandbox import run_code_safely, parse_test_results, run_static_analysis
from typing import Iterator
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

            # 1. Architect Stage
            self.log("Architect", "Analyzing problem and generating technical specification...")
            spec = self.architect.analyze_problem(problem_description)

            if spec.problem_name == "Error Analyzing Problem":
                self.log("Architect", "⚠️ Spec parse failed. Retrying with cleaner prompt...")
                spec = self.architect.analyze_problem(
                    f"Analyze this DSA problem carefully and return ONLY valid JSON:\n\n{problem_description}"
                )

            self.log("Architect", f"Spec generated: {spec.problem_name}")

            # 2. Developer Stage
            self.log("Developer", "Writing Python implementation...")
            code = self.developer.implement_solution(spec)

            if not code or not code.strip():
                self.log("Developer", "⚠️ Empty code generated. Skipping this iteration.")
                iteration += 1
                continue

            # 3. Test Engineer Stage
            self.log("Test Engineer", "Generating adversarial test suite...")
            test_script = self.test_engineer.generate_tests(spec, code)

            if not test_script or not test_script.strip():
                self.log("Test Engineer", "⚠️ Empty test script generated. Skipping sandbox run.")
                iteration += 1
                continue

            # 4. Sandbox Stage
            self.log("Sandbox", "Executing code and tests in isolated environment...")
            execution_result = run_code_safely(code, test_script)

            test_output = (
                f"STDOUT:\n{execution_result['stdout']}\n\n"
                f"STDERR:\n{execution_result['stderr']}"
            )

            # 5. Parse real test results
            self.log("Sandbox", "Parsing objective test results...")
            parsed = parse_test_results(execution_result["stderr"])
            self.log(
                "Sandbox",
                f"Ground truth: {parsed['passed']}/{parsed['total']} passed, "
                f"{parsed['failed']} failed",
            )

            # 6. Static analysis
            self.log("Sandbox", "Running static analysis (pylint & radon)...")
            static = run_static_analysis(code)
            self.log(
                "Sandbox",
                f"Pylint: {static['pylint_score']}/10 | "
                f"Complexity: {static['complexity_grade']}",
            )

            objective_metrics = {
                "passed": parsed["passed"],
                "total": parsed["total"],
                "failed": parsed["failed"],
                "pylint_score": static["pylint_score"],
                "complexity_grade": static["complexity_grade"],
            }

            # 7. Evaluator Stage
            self.log("Evaluator", "Assessing correctness, complexity, and trust score...")
            report = self.evaluator.evaluate(spec, code, test_output, objective_metrics)

            self.log(
                "Evaluator",
                f"Evaluation Complete. Grade: {report.trust_grade} | "
                f"Score: {report.trust_score} | Verdict: {report.verdict}",
            )

            if report.verdict == "APPROVED" or iteration == max_retries - 1:
                if report.verdict != "APPROVED":
                    self.log("Orchestrator", "Max retries reached. Returning best available result.")
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

            # Self-Healing
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

        return None

    # ──────────────────────────────────────────────────────────────────
    # STREAMING VERSION — yields events for SSE / real-time frontend
    # ──────────────────────────────────────────────────────────────────
    def run_pipeline_stream(
        self, problem_description: str, max_retries: int = 3
    ) -> Iterator[dict]:
        """
        Generator version of run_pipeline().
        Yields structured event dicts at every meaningful step so a FastAPI
        SSE endpoint can forward them to the browser in real time.

        Event types:
          log       — agent thought-stream message
          progress  — pipeline step indicator
          code      — generated Python implementation
          tests     — generated test suite
          execution — raw stdout/stderr from sandbox
          metrics   — ground-truth test + static analysis numbers
          report    — full EvaluationReport as dict
          done      — final packaged result
          error     — a non-fatal problem was encountered
        """
        def _log(agent: str, message: str) -> dict:
            ts = time.strftime("%H:%M:%S")
            self.logs.append({"timestamp": ts, "agent": agent, "message": message})
            return {"type": "log", "timestamp": ts, "agent": agent, "message": message}

        def _progress(iteration: int, max_r: int, step: str) -> dict:
            return {
                "type": "progress",
                "iteration": iteration + 1,
                "max_retries": max_r,
                "step": step,
            }

        yield _log("Orchestrator", "Starting pipeline for new problem...")

        iteration = 0
        while iteration < max_retries:
            yield _log("Orchestrator", f"--- Iteration {iteration + 1}/{max_retries} ---")

            # 1. Architect
            yield _progress(iteration, max_retries, "architect")
            yield _log("Architect", "Analyzing problem and generating technical specification...")
            spec = self.architect.analyze_problem(problem_description)

            if spec.problem_name == "Error Analyzing Problem":
                yield _log("Architect", "⚠️ Spec parse failed. Retrying with cleaner prompt...")
                yield {"type": "error", "message": "Architect spec parse failed — retrying"}
                spec = self.architect.analyze_problem(
                    f"Analyze this DSA problem carefully and return ONLY valid JSON:\n\n{problem_description}"
                )

            yield _log("Architect", f"Spec generated: {spec.problem_name}")

            # 2. Developer
            yield _progress(iteration, max_retries, "developer")
            yield _log("Developer", "Writing Python implementation...")
            code = self.developer.implement_solution(spec)

            if not code or not code.strip():
                yield _log("Developer", "⚠️ Empty code generated. Skipping iteration.")
                yield {"type": "error", "message": "Developer returned empty code"}
                iteration += 1
                continue

            yield {"type": "code", "content": code}

            # 3. Test Engineer
            yield _progress(iteration, max_retries, "test_engineer")
            yield _log("Test Engineer", "Generating adversarial test suite...")
            test_script = self.test_engineer.generate_tests(spec, code)

            if not test_script or not test_script.strip():
                yield _log("Test Engineer", "⚠️ Empty test script. Skipping sandbox run.")
                yield {"type": "error", "message": "Test Engineer returned empty test script"}
                iteration += 1
                continue

            yield {"type": "tests", "content": test_script}

            # 4. Sandbox
            yield _progress(iteration, max_retries, "sandbox")
            yield _log("Sandbox", "Executing code and tests in isolated environment...")
            execution_result = run_code_safely(code, test_script)

            test_output = (
                f"STDOUT:\n{execution_result['stdout']}\n\n"
                f"STDERR:\n{execution_result['stderr']}"
            )

            yield {
                "type": "execution",
                "stdout": execution_result["stdout"],
                "stderr": execution_result["stderr"],
            }

            # 5. Parse test results
            yield _log("Sandbox", "Parsing objective test results...")
            parsed = parse_test_results(execution_result["stderr"])
            yield _log(
                "Sandbox",
                f"Ground truth: {parsed['passed']}/{parsed['total']} passed, "
                f"{parsed['failed']} failed",
            )

            # 6. Static analysis
            yield _log("Sandbox", "Running static analysis (pylint & radon)...")
            static = run_static_analysis(code)
            yield _log(
                "Sandbox",
                f"Pylint: {static['pylint_score']}/10 | Complexity: {static['complexity_grade']}",
            )

            objective_metrics = {
                "passed": parsed["passed"],
                "total": parsed["total"],
                "failed": parsed["failed"],
                "pylint_score": static["pylint_score"],
                "complexity_grade": static["complexity_grade"],
            }

            yield {"type": "metrics", "data": objective_metrics}

            # 7. Evaluator
            yield _progress(iteration, max_retries, "evaluator")
            yield _log("Evaluator", "Assessing correctness, complexity, and trust score...")
            report = self.evaluator.evaluate(spec, code, test_output, objective_metrics)

            yield _log(
                "Evaluator",
                f"Evaluation Complete. Grade: {report.trust_grade} | "
                f"Score: {report.trust_score} | Verdict: {report.verdict}",
            )

            yield {"type": "report", "data": report.model_dump()}

            result = {
                "spec": spec.model_dump(),
                "code": code,
                "test_script": test_script,
                "report": report.model_dump(),
                "execution_output": test_output,
                "objective_metrics": objective_metrics,
                "logs": list(self.logs),
                "iterations_used": iteration + 1,
            }

            if report.verdict == "APPROVED" or iteration == max_retries - 1:
                if report.verdict != "APPROVED":
                    yield _log("Orchestrator", "Max retries reached. Returning best available result.")
                else:
                    yield _log("Orchestrator", "Pipeline finished — code APPROVED. ✅")

                yield {"type": "done", "result": result}
                return

            # Self-heal
            stderr = execution_result["stderr"]
            failure_lines = [
                line for line in stderr.splitlines()
                if any(kw in line for kw in ["FAIL", "ERROR", "AssertionError", "Exception", "Traceback"])
            ]
            failure_summary = "\n".join(failure_lines[:30]) if failure_lines else stderr[:500]

            yield _log(
                "Orchestrator",
                f"Feeding {parsed['failed']} specific failure(s) back to Architect...",
            )

            problem_description = (
                f"{problem_description.split('=== PREVIOUS')[0].strip()}\n\n"
                f"=== PREVIOUS ATTEMPT FAILED ===\n"
                f"Tests: {parsed['passed']}/{parsed['total']} passed | "
                f"Pylint: {static['pylint_score']}/10\n"
                f"Expert Feedback: {report.feedback}\n\n"
                f"Specific Failures:\n{failure_summary}\n"
                f"Fix these exact failures in your next implementation."
            )
            iteration += 1


if __name__ == "__main__":
    orch = Orchestrator()
    results = orch.run_pipeline(
        "Write a function to find the maximum sum of a contiguous subarray."
    )
    if results:
        print(f"Final Grade: {results['report'].trust_grade}")
        print(f"Iterations: {results['iterations_used']}")
