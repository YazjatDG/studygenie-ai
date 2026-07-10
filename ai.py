import os
from dotenv import load_dotenv
try:
    from google.genai import Client, errors
except Exception:
    Client = None
    class _DummyErrors:
        ClientError = Exception
        ServerError = Exception
        APIError = Exception
    errors = _DummyErrors()

try:
    import openai
    _OPENAI_AVAILABLE = True
except Exception:
    openai = None
    _OPENAI_AVAILABLE = False

load_dotenv("api.env")
load_dotenv()

# Support a legacy `api.env` file that contains only the bare API key (no VAR=VALUE line).
# If `api.env` contains a single token (no '='), treat it as the GEMINI_API_KEY.
try:
    api_env_path = os.path.join(os.path.dirname(__file__), "api.env")
    if "GEMINI_API_KEY" not in os.environ and os.path.exists(api_env_path):
        with open(api_env_path, "r") as f:
            raw_content = f.read().strip()
        if raw_content and "=" not in raw_content:
            os.environ["GEMINI_API_KEY"] = raw_content
except Exception:
    # If reading/parsing fails, fall back to load_dotenv behavior.
    pass

MODEL_CANDIDATES = [
    "models/gemini-flash-latest",
    "models/gemini-2.5-pro",
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-lite",
]


def _get_genai_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or Client is None:
        return None
    return Client(api_key=api_key)


class AIService:
    @staticmethod
    def _is_api_ready():
        return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY"))

    @staticmethod
    def _generate_response(prompt: str, model_name: str | None = None) -> str:
        if not AIService._is_api_ready():
            return (
                "⚠️ API key missing. Set GEMINI_API_KEY or OPENAI_API_KEY in `.env` to enable AI features."
            )

        last_error = None

        # Prefer OpenAI if an OpenAI key is present and the SDK is available.
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key and _OPENAI_AVAILABLE:
            try:
                model = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

                # New OpenAI package versions use the OpenAI client.
                if hasattr(openai, "OpenAI"):
                    client = openai.OpenAI(api_key=openai_key)
                    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
                        resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": str(prompt)}], max_tokens=512)
                        try:
                            return resp.choices[0].message.content.strip()
                        except Exception:
                            return str(resp)
                    elif hasattr(client, "responses"):
                        resp = client.responses.create(model=model, input=str(prompt), max_tokens=512)
                        try:
                            return resp.output[0].content[0].text.strip()
                        except Exception:
                            return str(resp)

                # Older versions used openai.ChatCompletion.create
                if hasattr(openai, "ChatCompletion"):
                    openai.api_key = openai_key
                    resp = openai.ChatCompletion.create(model=model, messages=[{"role": "user", "content": str(prompt)}], max_tokens=512)
                    return resp.choices[0].message.content.strip() if resp and getattr(resp, "choices", None) else str(resp)

            except Exception as oe:
                last_error = oe

            if last_error is not None:
                return f"System note: OpenAI API error. ({str(last_error)})"

        # Fall back to Gemini if OpenAI is not configured or unavailable.
        client = _get_genai_client()
        if client is None:
            if last_error is not None:
                return f"System note: API error. ({str(last_error)})"
            return "System note: No API client available. Please install provider SDK or set a valid key."

        if model_name:
            candidates = [model_name]
        else:
            candidates = MODEL_CANDIDATES

        for candidate in candidates:
            try:
                response = client.models.generate_content(model=candidate, contents=str(prompt))
                return getattr(response, "text", str(response))
            except (errors.ClientError, errors.ServerError, errors.APIError) as api_err:
                last_error = api_err
                if candidate == candidates[-1]:
                    break
                continue
            except Exception as e:
                return f"System note: Please try refreshing the window. ({str(e)})"

        if last_error is not None:
            return f"System note: Gemini API error. ({str(last_error)})"

        return "System note: Unable to generate a response right now. Please try again later."

    @staticmethod
    def daily_motivation(streak: int) -> str:
        prompt = (
            f"You are a friendly study coach. Write a short, uplifting message for a student "
            f"who has maintained a {streak}-day study streak and needs encouragement to keep going."
        )
        return AIService._generate_response(prompt)

    @staticmethod
    def predict_readiness(raw_metrics: str) -> str:
        prompt = (
            "You are an academic readiness evaluator. Based on the following metrics, "
            "provide a concise readiness score explanation and one suggestion for improvement:\n"
            f"{raw_metrics}"
        )
        return AIService._generate_response(prompt)

    @staticmethod
    def generate_timetable(subjects: list[str], hours_target: int) -> str:
        subjects_str = ", ".join(subjects)
        prompt = (
            "Create a balanced daily study timetable for a student. Use the following subjects: "
            f"{subjects_str}. The target daily study time is {hours_target} hours. "
            "Return the timetable in short bullet points."
        )
        return AIService._generate_response(prompt)

    @staticmethod
    def rearrange_timetable(missed_subject: str, reason: str) -> str:
        prompt = (
            "A student missed a study block. Suggest a revised timetable and a short recovery plan. "
            f"Missed subject: {missed_subject}. Reason: {reason}."
        )
        return AIService._generate_response(prompt)

    @staticmethod
    def summarize_notes(content: str) -> str:
        prompt = (
            "Summarize the following study notes into a concise paragraph. "
            f"Notes:\n{content}"
        )
        return AIService._generate_response(prompt)

    @staticmethod
    def generate_flashcards(content: str) -> str:
        prompt = (
            "Read these notes and create 3 short study flashcards in a question-and-answer format. "
            f"Notes:\n{content}"
        )
        return AIService._generate_response(prompt)

    @staticmethod
    def create_mcqs(content: str) -> str:
        prompt = (
            "Generate 3 multiple-choice questions from the notes below. Include one correct answer and "
            "three answer choices for each question.\n"
            f"Notes:\n{content}"
        )
        return AIService._generate_response(prompt)

    @staticmethod
    def chat_assistant(user_query: str, context: str) -> str:
        prompt = (
            "You are a helpful study assistant. Use the context below to answer the user's question. "
            f"Context:\n{context}\nQuestion:\n{user_query}"
        )
        return AIService._generate_response(prompt)

    @staticmethod
    def weekly_report(history_text: str) -> str:
        prompt = (
            "Generate a brief weekly study performance report based on this study session history:\n"
            f"{history_text}"
        )
        return AIService._generate_response(prompt)

    @staticmethod
    def suggest_weak_subjects(history_text: str) -> str:
        prompt = (
            "Review the study session history below and suggest which subjects may need more focus. "
            f"History:\n{history_text}"
        )
        return AIService._generate_response(prompt)


def generate_ai_response(prompt: str) -> str:
    return AIService._generate_response(prompt)
