import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load .env from the backend/ directory first, then project root as fallback
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv()  # fallback to project root .env


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in .env file")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_retries: int = 2,
    ) -> str:
        """
        Sends a prompt to the Groq API and returns the response content.
        Retries up to max_retries times if the response is empty or an API error occurs.
        On retry, uses a stricter prompt to force the model to follow instructions.
        """
        last_error = ""
        for attempt in range(max_retries + 1):
            try:
                effective_system = system_prompt
                if attempt > 0:
                    effective_system = (
                        "IMPORTANT: Your previous response was invalid or empty. "
                        "You MUST respond strictly as instructed. No preamble, no explanations.\n\n"
                        + system_prompt
                    )
                    time.sleep(1)  # Brief back-off before retrying

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": effective_system},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                )

                content = response.choices[0].message.content

                if content and content.strip():
                    return content.strip()

                last_error = f"Empty response on attempt {attempt + 1}"
                print(f"[LLMClient] Warning: {last_error}")

            except Exception as e:
                last_error = str(e)
                print(f"[LLMClient] API error on attempt {attempt + 1}: {e}")

        return f"Error calling Groq API after {max_retries + 1} attempts: {last_error}"


if __name__ == "__main__":
    client = LLMClient()
    result = client.generate("You are a helpful assistant.", "Say hello!")
    print(result)
