"""Lead qualification and sentiment analysis."""

import logging
from typing import Tuple
from textblob import TextBlob

logger = logging.getLogger(__name__)


class LeadClassifier:
    """Classify leads based on customer data and conversation."""
    
    # Lead classification thresholds
    HOT_THRESHOLD = 7
    WARM_THRESHOLD = 4
    
    @staticmethod
    def classify_lead(
        budget: float,
        buying_timeline: str,
        requirements_match: float,
        sentiment: str,
    ) -> str:
        """Classify lead as Hot, Warm, or Cold.
        
        Args:
            budget: Customer budget in dollars.
            buying_timeline: Timeline for purchase (e.g., "This week", "This month").
            requirements_match: Score 0-10 indicating how well products match needs.
            sentiment: Sentiment of conversation (Positive, Neutral, Negative).
            
        Returns:
            Lead classification: "Hot", "Warm", or "Cold".
        """
        score = 0
        
        # Budget scoring
        if budget and budget > 500:
            score += 3
        elif budget and budget > 0:
            score += 1
        
        # Timeline scoring
        timeline_lower = buying_timeline.lower() if buying_timeline else ""
        if "today" in timeline_lower or "this week" in timeline_lower:
            score += 3
        elif "this month" in timeline_lower:
            score += 2
        elif "this quarter" in timeline_lower:
            score += 1
        
        # Requirements match scoring
        score += min(requirements_match / 2, 2)  # 0-2 points
        
        # Sentiment scoring
        if sentiment == "Positive":
            score += 2
        elif sentiment == "Negative":
            score -= 2
        
        # Classify based on score
        if score >= LeadClassifier.HOT_THRESHOLD:
            return "Hot"
        elif score >= LeadClassifier.WARM_THRESHOLD:
            return "Warm"
        else:
            return "Cold"
    
    @staticmethod
    def analyze_sentiment(text: str) -> str:
        """Analyze sentiment of text using TextBlob.
        
        Args:
            text: Text to analyze.
            
        Returns:
            Sentiment: "Positive", "Neutral", or "Negative".
        """
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                return "Positive"
            elif polarity < -0.1:
                return "Negative"
            else:
                return "Neutral"
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return "Neutral"
    
    @staticmethod
    def calculate_requirements_match(
        requirements: str,
        recommended_products: str,
    ) -> float:
        """Calculate how well recommended products match requirements.
        
        Args:
            requirements: Customer requirements text.
            recommended_products: Recommended products text.
            
        Returns:
            Match score 0-10.
        """
        try:
            requirements_lower = requirements.lower() if requirements else ""
            products_lower = recommended_products.lower() if recommended_products else ""
            
            # Count keyword matches
            keywords = ["gaming", "work", "business", "video", "editing", "fast", "light", "portable", "performance"]
            matches = sum(1 for keyword in keywords if keyword in requirements_lower and keyword in products_lower)
            
            # Calculate score
            score = min(matches * 2, 10)
            return float(score)
        except Exception as e:
            logger.error(f"Error calculating requirements match: {e}")
            return 5.0
