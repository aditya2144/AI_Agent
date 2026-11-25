"""AI Sales Agent using Google Gemini."""

import logging
import os
from typing import List, Tuple, Optional
import google.genai as genai
from google.genai import types
from google.genai.types import GenerateContentConfig

logger = logging.getLogger(__name__)

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class SalesAgent:
    """AI Sales Agent powered by Google Gemini."""
    
    def __init__(self):
        """Initialize the sales agent."""
        self.model_name = "gemini-3.8-flash"
        self.conversation_history = []
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the sales agent.
        
        Returns:
            System prompt string.
        """
        return """You are an enthusiastic and professional sales representative for TechStore, a laptop selling company.

Your responsibilities:
1. Greet customers warmly and professionally
2. Ask about their laptop needs, budget, and use cases
3. Provide personalized laptop recommendations
4. Answer questions about products honestly
5. Help customers book appointments
6. Maintain a friendly, helpful tone throughout the conversation

Guidelines:
- Always be honest about product features and prices
- Never make up specifications or prices
- If a product isn't suitable, suggest alternatives
- Be patient and answer follow-up questions
- Encourage customers to book appointments for further discussion
- Maintain conversation context throughout the interaction

Remember: You're helping customers find the right laptop, not just making a sale."""
    
    def _format_conversation_history(self, conversation_history: List[Tuple[str, str]]) -> List[types.Content]:
        """Format conversation history into proper Content objects.
        
        Args:
            conversation_history: List of (user, assistant) message tuples.
            
        Returns:
            List of properly formatted Content objects.
        """
        formatted_history = []
        
        if not conversation_history:
            return formatted_history
        
        for user_msg, assistant_msg in conversation_history:
            # Add user message
            formatted_history.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_msg)]
                )
            )
            # Add assistant message
            formatted_history.append(
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=assistant_msg)]
                )
            )
        
        return formatted_history
    
    def send_message(
        self,
        user_message: str,
        product_context: str = "",
        conversation_history: List[Tuple[str, str]] = None,
    ) -> str:
        """Send a message to the AI agent and get a response.
        
        Args:
            user_message: User's input message.
            product_context: Product information from RAG.
            conversation_history: List of (user, assistant) message tuples.
            
        Returns:
            Agent's response.
        """
        try:
            if not GEMINI_API_KEY:
                return "Error: Gemini API key not configured. Please set GEMINI_API_KEY in .env"
            
            # Add product context if available
            context_message = ""
            if product_context:
                context_message = f"\n\nRelevant Product Information:\n{product_context}"
            
            # Add current user message with context
            full_message = user_message + context_message
            
            # Initialize client with API key
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            # Format conversation history
            contents = self._format_conversation_history(conversation_history)
            
            # Add current message
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=full_message)]
                )
            )
            
            # Generate response
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.7,
                    max_output_tokens=1024,
                )
            )
            
            assistant_response = response.text
            
            logger.info(f"Agent response generated successfully")
            return assistant_response
            
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            return f"I apologize, but I encountered an error processing your message. Please try again. Error: {str(e)}"
    
    def generate_summary(
        self,
        conversation_history: List[Tuple[str, str]],
        customer_name: str = "Customer",
    ) -> str:
        """Generate a summary of the conversation.
        
        Args:
            conversation_history: List of (user, assistant) message tuples.
            customer_name: Name of the customer.
            
        Returns:
            Conversation summary.
        """
        try:
            if not GEMINI_API_KEY:
                return "Error: Gemini API key not configured."
            
            # Build conversation text
            conversation_text = ""
            for i, (user_msg, assistant_msg) in enumerate(conversation_history):
                conversation_text += f"Customer: {user_msg}\n"
                conversation_text += f"Agent: {assistant_msg}\n\n"
            
            # Create summary prompt
            summary_prompt = f"""Please analyze this customer conversation and provide a detailed summary in the following format:

CONVERSATION ANALYSIS FOR {customer_name}

SUMMARY:
[2-3 sentence overview of the conversation]

CUSTOMER REQUIREMENTS:
[What the customer is looking for]

BUDGET:
[Mentioned budget or range]

SENTIMENT:
[Overall sentiment: Positive, Neutral, or Negative]

RECOMMENDED PRODUCTS:
[Products discussed or recommended]

NEXT STEPS:
[Recommended follow-up actions]

CONVERSATION:
{conversation_text}"""
            
            # Initialize client
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            # Get summary from Gemini
            response = client.models.generate_content(
                model=self.model_name,
                contents=summary_prompt,
                config=GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                )
            )
            
            logger.info("Call summary generated successfully")
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Could not generate summary. Error: {str(e)}"
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
