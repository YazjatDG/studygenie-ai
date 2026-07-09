import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables. Support both a standard ".env" and the
# project's "api.env" file that ships alongside this module.
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "api.env"))

api_key = os.getenv("GEMINI_API_KEY", "").strip()

# Treat the shipped placeholder value as "no key configured".
if api_key == "your_actual_gemini_api_key_here":
    api_key = ""

if api_key:
    genai.configure(api_key=api_key)

class AIService:
    @staticmethod
    def _call_gemini(prompt: str) -> str:
        if not api_key:
            return "⚠️ Gemini API key is missing. Please set GEMINI_API_KEY in your .env file."
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            return response.text if response.text else "No response generated."
        except Exception as e:
            return f"Error connecting to AI engine: {str(e)}"

    @classmethod
    def generate_timetable(cls, subjects: list, hours_per_day: int) -> str:
        prompt = f"Create a structured weekly study timetable for these subjects: {', '.join(subjects)}. Target: {hours_per_day} hours/day. Respond in a clean, clean Markdown table format with days as rows and columns as time frames."
        return cls._call_gemini(prompt)

    @classmethod
    def rearrange_timetable(cls, missed_subject: str, reason: str) -> str:
        prompt = f"The student missed their study session for '{missed_subject}' because of: '{reason}'. Give a dynamic, high-priority list of actionable shifts to recover this session over the next 48 hours without burning out."
        return cls._call_gemini(prompt)

    @classmethod
    def suggest_weak_subjects(cls, history_summary: str) -> str:
        prompt = f"Analyze this historical logging metric string of a student:\n{history_summary}\nIdentify weakness profiles, subject attention deficit points, and provide three customized architectural recommendations."
        return cls._call_gemini(prompt)

    @classmethod
    def chat_assistant(cls, user_message: str, dynamic_context: str = "") -> str:
        prompt = f"Context metrics:\n{dynamic_context}\nUser question: {user_message}\nAct as StudyGenie, an expert structural academic guide. Respond clearly with formatting."
        return cls._call_gemini(prompt)

    @classmethod
    def summarize_notes(cls, content: str) -> str:
        prompt = f"Provide a complete hierarchical architectural summary with clear headings and bold terms for the following context:\n{content}"
        return cls._call_gemini(prompt)

    @classmethod
    def generate_flashcards(cls, content: str) -> str:
        prompt = f"Extract exactly 5 key flashcard items from the following content. Format cleanly as Front/Back pairings:\n{content}"
        return cls._call_gemini(prompt)

    @classmethod
    def create_mcqs(cls, content: str) -> str:
        prompt = f"Generate exactly 3 Multiple Choice Questions with clear structural options A, B, C, D and an explicit correct answer marker based on this content:\n{content}"
        return cls._call_gemini(prompt)

    @classmethod
    def predict_readiness(cls, performance_data: str) -> str:
        prompt = f"Given these raw metrics: {performance_data}. Extrapolate an structural readiness score percentage (e.g. 84%) and output a 2-line strategic recommendation matrix."
        return cls._call_gemini(prompt)

    @classmethod
    def daily_motivation(cls, current_streak: int) -> str:
        prompt = f"Write a powerful, concise motivational quote for a student who has a {current_streak}-day study streak. Keep it under 2 sentences."
        return cls._call_gemini(prompt)

    @classmethod
    def weekly_report(cls, statistics_string: str) -> str:
        prompt = f"Synthesize this weekly raw study dataset into an analytical performance summary report:\n{statistics_string}"
        return cls._call_gemini(prompt)
