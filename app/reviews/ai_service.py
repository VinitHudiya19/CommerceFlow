from typing import List
from app.reviews.models import Review

class AISummarizerService:
    @staticmethod
    async def summarize_reviews(reviews: List[Review]) -> str:
        """
        Pluggable AI Review Summary engine.
        Runs a rule-based NLP parser locally by default (offline-friendly).
        
        To swap to a real LLM (e.g. HuggingFace, Gemini, OpenAI):
        See the commented out integrations below.
        """
        if not reviews:
            return "No customer reviews available yet to summarize."

        # Compute stats
        total_rating = sum(r.rating for r in reviews)
        avg_rating = total_rating / len(reviews)
        comments = [r.comment.lower() for r in reviews]

        # Extract hot topics
        keywords = {
            "keyboard": "Tactile response, typing ergonomics, and premium build material quality.",
            "mat": "Texture smoothness, premium desk mat size, and mouse sensor precision.",
            "hoodie": "Heavyweight premium cotton thickness, fit warmth, and stitching durability.",
            "backpack": "Waterproof capacity storage, laptop compartment padding, and travel comfort.",
            "notebook": "Paper page thickness, ink-proof layout, and solid linen hardcover durability.",
            "fast": "Highly praised quick shipping and responsive customer care delivery.",
            "quality": "Exceptional manufacturing craftsmanship and long-term durability features."
        }

        found_bullets = []
        for word, summary in keywords.items():
            if any(word in comment for comment in comments):
                found_bullets.append(f"- **{word.capitalize()}**: {summary}")

        # Add general mood indicator
        mood = "excellent" if avg_rating >= 4.0 else ("satisfactory" if avg_rating >= 3.0 else "mixed")
        found_bullets.insert(0, f"- **Overall Sentiment**: Customer feedback is **{mood}** with an average rating of **{avg_rating:.1f}/5.0** stars.")
        
        if len(found_bullets) == 1:
            found_bullets.append("- **Core Feedback**: Users note general satisfaction with purchase experience and item utility.")

        return "\n".join(found_bullets)

        # =====================================================================
        # OPTION A: Integrating with Google Gemini API
        # =====================================================================
        # import google.generativeai as genai
        # genai.configure(api_key="YOUR_GEMINI_API_KEY")
        # model = genai.GenerativeModel('gemini-pro')
        # 
        # text_to_summarize = "\n".join([f"Rating {r.rating}/5: {r.comment}" for r in reviews])
        # prompt = f"Summarize the following product reviews into a concise bulleted list highlighting key highlights and flaws:\n{text_to_summarize}"
        # 
        # response = model.generate_content(prompt)
        # return response.text

        # =====================================================================
        # OPTION B: Integrating with HuggingFace Pipelines (Local Model)
        # =====================================================================
        # from transformers import pipeline
        # # Load small BART summarization pipeline
        # summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        # 
        # text_to_summarize = " ".join([r.comment for r in reviews])
        # if len(text_to_summarize) < 50:
        #     return "Not enough review details to compile a model-based summary."
        # 
        # summary_list = summarizer(text_to_summarize, max_length=130, min_length=30, do_sample=False)
        # return summary_list[0]['summary_text']
