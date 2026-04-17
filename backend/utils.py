"""
Shared utility functions used across all agents.
Centralizing here prevents code duplication and circular imports.
"""
import json
import re


def extract_json_from_text(text: str) -> dict:
    """
    Robustly extracts a JSON object from LLM output that may contain
    markdown fences, explanations, or other surrounding text.
    Used by ArchitectAgent, EvaluatorAgent, and any future agents.
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

    # Strategy 3: Find the first { ... } block via brace-depth matching
    start = cleaned.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(cleaned)):
            if cleaned[i] == "{":
                depth += 1
            elif cleaned[i] == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start: i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break

    # Strategy 4: Regex fallback for the outermost JSON object
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not extract valid JSON from LLM response: {text[:200]}..."
    )
