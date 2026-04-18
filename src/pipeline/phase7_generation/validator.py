import re
from datetime import datetime

class ConstraintValidator:
    """
    Acts as the strict formatting and rules gatekeeper for all LLM Outputs
    as per Phase 7 of the RAG Architecture.
    """
    
    @staticmethod
    def enforce_sentence_limit(text: str, max_sentences: int = 3) -> str:
        """
        Forcefully splits text on punctuation boundaries and drops sentences
        exceeding the numerical hard-limit to prevent LLM run-on generation.
        """
        # Split purely on punctuation indicating ends of sentences
        sentences = re.split(r'(?<=[.!?]) +', text.strip())
        
        # Filter arbitrary empty chunks from double spacing
        valid_sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(valid_sentences) > max_sentences:
            valid_sentences = valid_sentences[:max_sentences]
            
        # Reconstruct into a single string safely
        return " ".join(valid_sentences)

    @staticmethod
    def format_final_payload(raw_llm_text: str, source_url: str, last_updated: str) -> dict:
        """
        Executes the three core validation rules:
        1. Validates length (<= 3 sentences)
        2. Appends URL uniquely
        3. Appends Date uniquely
        
        Returns a structured dictionary for the UI.
        """
        
        # Rule 1: Length Validation
        constrained_text = ConstraintValidator.enforce_sentence_limit(raw_llm_text, 3)
        
        # Edge Case Fallbacks
        final_url = source_url if source_url else "N/A"
        date_str = "N/A"
        
        # Parse ISO datetime if possible to make it human readable, or just fallback to raw string
        if last_updated:
            try:
                # Attempt to parse ISO string e.g. "2026-04-17T15:05:16.414925+00:00"
                dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                date_str = dt.strftime("%B %d, %Y")
            except Exception:
                # If it's just a raw date string like "2023-10-01" from the architecture dummy
                date_str = last_updated
        
        return {
            "answer": constrained_text,
            "source_url": final_url,
            "last_updated": date_str
        }
