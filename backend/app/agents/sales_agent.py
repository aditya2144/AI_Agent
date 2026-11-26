"""AI Sales Agent using Google Gemini."""

import logging
import os
import time
from typing import List, Tuple, Optional
import google.genai as genai
from google.genai import types
from google.genai.types import GenerateContentConfig

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class SalesAgent:
    """AI Sales Agent powered by Google Gemini."""

    def __init__(self):
        self.model_name = "gemini-3.8-flash"
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return """You are Alex, an expert sales representative for TechStore, a premium laptop retailer.

Your role:
- Help customers find the perfect laptop based on their needs and budget
- Give detailed, specific product recommendations with specs and prices
- Answer every question thoroughly and conversationally
- Keep responses natural and engaging, like a real sales conversation
- Remember context from earlier in the conversation

Product catalog:
1. HP Pavilion 15 - Budget friendly, Intel i5, 8GB RAM, 512GB SSD - 42,000 INR
2. Lenovo ThinkPad E14 - Business laptop, Intel i5, 16GB RAM, 512GB SSD - 65,000 INR
3. ASUS ROG Strix G15 - Gaming, AMD Ryzen 7, RTX 3060, 16GB RAM, 512GB SSD - 95,000 INR
4. Dell XPS 15 - Premium, Intel i7, RTX 3050, 32GB RAM, 1TB SSD, 4K OLED - 1,45,000 INR
5. MacBook Pro M2 - Creative work, Apple M2, 16GB RAM, 512GB SSD - 1,30,000 INR
6. Lenovo Legion 5 - Gaming, AMD Ryzen 5, RTX 3060, 16GB RAM, 512GB SSD - 78,000 INR
7. HP Spectre x360 - Ultrabook, Intel i7, 16GB RAM, 512GB SSD, touchscreen - 1,10,000 INR
8. ASUS VivoBook 15 - Mid range, Intel i5, 16GB RAM, 512GB SSD - 55,000 INR

Important rules:
- Always give specific prices in INR
- Give detailed specs when asked
- If budget is mentioned, only recommend laptops within that budget
- Keep answers conversational, not bullet-point heavy
- Ask follow-up questions to understand customer needs better
- Never repeat the same answer twice"""

    def _format_conversation_history(self, conversation_history: List[Tuple[str, str]]) -> List[types.Content]:
        formatted = []
        if not conversation_history:
            return formatted
        for user_msg, assistant_msg in conversation_history:
            formatted.append(types.Content(role="user", parts=[types.Part.from_text(text=user_msg)]))
            formatted.append(types.Content(role="model", parts=[types.Part.from_text(text=assistant_msg)]))
        return formatted

    def send_message(
        self,
        user_message: str,
        product_context: str = "",
        conversation_history: List[Tuple[str, str]] = None,
    ) -> str:
        if not GEMINI_API_KEY:
            raise Exception("Gemini API key not configured")

        full_message = user_message
        if product_context:
            full_message += f"\n\nRelevant Product Info:\n{product_context}"

        client = genai.Client(api_key=GEMINI_API_KEY)
        contents = self._format_conversation_history(conversation_history)
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=full_message)]))

        # Retry up to 3 times on 503
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=GenerateContentConfig(
                        system_instruction=self.system_prompt,
                        temperature=0.7,
                        max_output_tokens=512,
                    )
                )
                logger.info(f"Gemini responded on attempt {attempt + 1}")
                return response.text
            except Exception as e:
                err = str(e)
                if "503" in err or "UNAVAILABLE" in err:
                    logger.warning(f"Gemini 503, attempt {attempt + 1}/3, retrying in 2s...")
                    time.sleep(2)
                    continue
                raise Exception(err)

        raise Exception("Gemini unavailable after 3 attempts")

    def generate_summary(self, conversation_history: List[Tuple[str, str]], customer_name: str = "Customer") -> str:
        try:
            if not conversation_history:
                return "No conversation to summarize."

            # Build summary locally without Gemini
            user_messages = [u for u, a in conversation_history]
            agent_messages = [a for u, a in conversation_history]

            # Extract budget
            budget = "Not mentioned"
            for msg in user_messages:
                words = msg.lower().split()
                for i, word in enumerate(words):
                    if any(x in word for x in ["000", "inr", "rupee", "budget", "thousand"]):
                        budget = msg
                        break

            # Extract requirements
            requirements = []
            keywords = {
                "gaming": "Gaming laptop",
                "video": "Video editing",
                "edit": "Video/Photo editing",
                "business": "Business use",
                "office": "Office/Work use",
                "student": "Student use",
                "light": "Lightweight/Portable",
                "fast": "High performance",
                "cheap": "Budget friendly",
                "design": "Design/Creative work",
            }
            for msg in user_messages:
                for kw, label in keywords.items():
                    if kw in msg.lower() and label not in requirements:
                        requirements.append(label)

            # Extract mentioned products
            products = []
            product_names = ["dell", "hp", "asus", "lenovo", "macbook", "apple", "legion", "rog", "spectre", "xps", "thinkpad", "pavilion", "vivobook"]
            for msg in user_messages + agent_messages:
                for p in product_names:
                    if p in msg.lower() and p.title() not in products:
                        products.append(p.title())

            # Sentiment
            positive_words = ["good", "great", "love", "perfect", "yes", "sure", "interested", "buy", "want"]
            negative_words = ["no", "expensive", "costly", "bad", "not", "cant", "cannot"]
            pos = sum(1 for m in user_messages for w in positive_words if w in m.lower())
            neg = sum(1 for m in user_messages for w in negative_words if w in m.lower())
            sentiment = "Positive" if pos > neg else "Negative" if neg > pos else "Neutral"

            summary = f"""CALL SUMMARY - {customer_name}
{'='*50}

OVERVIEW:
Customer had a {len(conversation_history)}-turn conversation with the TechStore sales agent about laptop purchases.

CUSTOMER REQUIREMENTS:
{chr(10).join(f'- {r}' for r in requirements) if requirements else '- General laptop inquiry'}

BUDGET MENTIONED:
{budget}

PRODUCTS DISCUSSED:
{chr(10).join(f'- {p}' for p in products) if products else '- Various TechStore laptops'}

SENTIMENT: {sentiment}

CONVERSATION HIGHLIGHTS:
- Customer asked {len(user_messages)} questions
- Agent provided detailed recommendations
- Topics covered: {', '.join(requirements) if requirements else 'general laptop needs'}

NEXT STEPS:
- Follow up with specific product demos
- Send pricing details via email
- Schedule in-store visit if interested
{'='*50}"""

            return summary

        except Exception as e:
            return f"Summary error: {str(e)}"
