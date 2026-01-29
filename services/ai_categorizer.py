"""AI-powered job categorization using local/public AI APIs."""

import os
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from utils.logger import logger


@dataclass
class CategorizationResult:
    """Result of job categorization."""
    category: str
    confidence: float
    reasoning: str


class JobCategorizer:
    """Categorize jobs using AI/ML models."""
    
    VALID_CATEGORIES = ["jobs", "remote", "internships", "scholarships"]
    
    def __init__(self):
        self.use_local_ai = os.getenv("USE_LOCAL_AI", "false").lower() == "true"
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        
    def categorize(self, title: str, description: str = "", company: str = "") -> CategorizationResult:
        """Categorize a job posting using AI.
        
        Args:
            title: Job title
            description: Job description (optional)
            company: Company name (optional)
            
        Returns:
            CategorizationResult with category and confidence
        """
        # First try rule-based categorization
        category = self._rule_based_categorize(title, description, company)
        if category:
            return CategorizationResult(
                category=category,
                confidence=0.9,
                reasoning="Rule-based classification"
            )
        
        # If local AI is enabled, try AI categorization
        if self.use_local_ai and self.openrouter_api_key:
            return self._ai_categorize(title, description, company)
        
        # Default to "jobs" if no clear category
        return CategorizationResult(
            category="jobs",
            confidence=0.5,
            reasoning="Default category - no clear indicators found"
        )
    
    def _rule_based_categorize(self, title: str, description: str, company: str) -> Optional[str]:
        """Categorize based on keywords and rules.
        
        Args:
            title: Job title
            description: Job description
            company: Company name
            
        Returns:
            Category string or None if no match
        """
        text = f"{title} {description} {company}".lower()
        
        # Scholarship indicators
        scholarship_keywords = [
            "scholarship", "fellowship", "grant", "stipend", "financial aid",
            "tuition", "academic award", "education grant", "student award",
            "merit scholarship", "need-based", "full ride", "partial scholarship"
        ]
        if any(keyword in text for keyword in scholarship_keywords):
            return "scholarships"
        
        # Internship indicators
        internship_keywords = [
            "intern", "internship", "co-op", "coop", "trainee", "apprenticeship",
            "summer intern", "winter intern", "student position", "entry level",
            "new grad", "new graduate", "fresh graduate"
        ]
        if any(keyword in text for keyword in internship_keywords):
            return "internships"
        
        # Remote work indicators
        remote_keywords = [
            "remote", "work from home", "wfh", "telecommute", "virtual",
            "distributed team", "anywhere", "location independent",
            "fully remote", "100% remote", "remote first"
        ]
        if any(keyword in text for keyword in remote_keywords):
            return "remote"
        
        return None
    
    def _ai_categorize(self, title: str, description: str, company: str) -> CategorizationResult:
        """Categorize using OpenRouter AI API (free tier available).
        
        Args:
            title: Job title
            description: Job description
            company: Company name
            
        Returns:
            CategorizationResult
        """
        try:
            import requests
            
            prompt = f"""Categorize this job posting into one of: jobs, remote, internships, scholarships

Title: {title}
Company: {company}
Description: {description}

Respond with ONLY a JSON object in this format:
{{"category": "one_of_the_four", "confidence": 0.95, "reasoning": "brief explanation"}}
"""
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://job-alert-bot.com",
                    "X-Title": "Job Alert Bot"
                },
                json={
                    "model": "meta-llama/llama-3.2-3b-instruct:free",  # Free tier
                    "messages": [
                        {"role": "system", "content": "You are a job categorization assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 150
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Parse JSON response
                try:
                    result = json.loads(content)
                    category = result.get("category", "jobs")
                    confidence = result.get("confidence", 0.5)
                    reasoning = result.get("reasoning", "AI categorization")
                    
                    # Validate category
                    if category not in self.VALID_CATEGORIES:
                        category = "jobs"
                    
                    return CategorizationResult(
                        category=category,
                        confidence=confidence,
                        reasoning=reasoning
                    )
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse AI response: {content}")
            
        except Exception as e:
            logger.error(f"AI categorization failed: {e}")
        
        # Fallback to rule-based
        category = self._rule_based_categorize(title, description, company)
        return CategorizationResult(
            category=category or "jobs",
            confidence=0.7,
            reasoning="Fallback to rule-based after AI failure"
        )


# Global categorizer instance
_categorizer: Optional[JobCategorizer] = None


def get_categorizer() -> JobCategorizer:
    """Get or create global categorizer instance."""
    global _categorizer
    if _categorizer is None:
        _categorizer = JobCategorizer()
    return _categorizer


def categorize_job(title: str, description: str = "", company: str = "") -> str:
    """Convenience function to categorize a job.
    
    Args:
        title: Job title
        description: Job description (optional)
        company: Company name (optional)
        
    Returns:
        Category string
    """
    categorizer = get_categorizer()
    result = categorizer.categorize(title, description, company)
    return result.category
