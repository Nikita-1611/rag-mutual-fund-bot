import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Hardcoded compliance strings
REFUSAL_PAYLOAD = "I can only provide verified factual data. For investment advice, please consult a registered advisor. Facts-only. No investment advice.\n\n*Educational Material: https://www.amfiindia.com/investor-corner*"
PII_REFUSAL_PAYLOAD = "Your query was blocked to protect your privacy. Please do not submit PAN, Aadhaar, phone numbers, or email addresses."

class GuardrailEngine:
    """
    Executes mandatory pre-flight constraints (Phase 6) to intercept PII and stop
    financial advisory attempts using keyword matching.
    """
    
    def __init__(self):
        # Keyword-based advice detection list
        self.advice_keywords = [
            "should i invest",
            "which fund is better",
            "recommend me",
            "best fund",
            "how much wealth",
            "suggest a fund",
            "is better than",
            "future returns",
            "predict",
            "forecast"
        ]

    def _sweep_pii(self, query: str) -> bool:
        """
        Runs fast regex patterns to detect PAN, Aadhaar, emails, or phone drops.
        """
        patterns = [
            r'[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}',          # Indian PAN Profile
            r'\b\d{4}\s?\d{4}\s?\d{4}\b',               # Aadhaar
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', # Standard Email
            r'\b[6-9]\d{9}\b'                           # Indian Phone Numbers
        ]
        
        for pattern in patterns:
            if re.search(pattern, query):
                logger.warning(f"PII Sweep Triggered! Pattern matched: {pattern}")
                return True
        return False

    def validate_query(self, query: str) -> Tuple[bool, str]:
        """
        Executes the dual-layered check (PII + Keywords).
        Returns (is_allowed: bool, refusal_string: str)
        """
        # Layer 1: PII Static Sweeps
        if self._sweep_pii(query):
             return False, PII_REFUSAL_PAYLOAD
             
        # Layer 2: Keyword-based Advice Detection
        query_lower = query.lower()
        for kw in self.advice_keywords:
            if kw in query_lower:
                logger.warning(f"Compliance Block! Advice keyword matched: '{kw}'")
                return False, REFUSAL_PAYLOAD
                
        return True, ""
