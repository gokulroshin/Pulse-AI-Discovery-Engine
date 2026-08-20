"""Gemini API client wrapper for structured reason extraction with rate limiting and retry logic."""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from app.config import settings
from app.extraction.schema import BatchExtractionResponse, DocumentExtractionResponse

logger = logging.getLogger("pulse.extraction.gemini")


class TokenBucketRateLimiter:
    """Simple token bucket rate limiter to prevent API 429 rate limit errors."""

    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 10):
        self.capacity = burst_limit
        self.tokens = burst_limit
        self.fill_rate = requests_per_minute / 60.0
        self.last_update = time.monotonic()

    def acquire(self):
        """Block until a token is available."""
        while True:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return
            else:
                sleep_time = (1.0 - self.tokens) / self.fill_rate
                time.sleep(min(1.0, sleep_time))


class GeminiExtractionClient:
    """High-reliability client for calling Google Gemini with structured JSON output."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key
        self._model = model
        self._client: Optional[genai.Client] = None
        self.rate_limiter = TokenBucketRateLimiter(requests_per_minute=60, burst_limit=5)

        self._load_prompts()

    @property
    def api_key(self) -> str:
        return self._api_key or settings.GEMINI_API_KEY

    @property
    def model(self) -> str:
        return self._model or settings.GEMINI_FLASH_MODEL

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            key = self.api_key or "DUMMY_KEY_FOR_TESTS"
            self._client = genai.Client(api_key=key)
        return self._client

    def _load_prompts(self):
        """Load system prompt and few-shot examples from prompts/ directory."""
        current_dir = os.path.dirname(__file__)
        system_prompt_path = os.path.join(current_dir, "prompts", "extraction_system.txt")
        few_shot_path = os.path.join(current_dir, "prompts", "extraction_few_shot.json")

        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_instruction = f.read().strip()

        with open(few_shot_path, "r", encoding="utf-8") as f:
            self.few_shot_examples = json.load(f)

    def format_batch_prompt(self, documents: List[Dict[str, str]]) -> str:
        """Format input document batch into prompt string for structured extraction."""
        batch_input = [
            {"doc_id": doc["doc_id"], "content_text": doc["content_text"]}
            for doc in documents
        ]

        prompt = (
            "Analyze the following batch of user-generated documents and extract all discrete reasons, "
            "frictions, behaviors, motivations, and decision factors per document in the structured schema:\n\n"
            f"INPUT DOCUMENTS:\n{json.dumps(batch_input, ensure_ascii=False, indent=2)}\n\n"
            "Return the extraction output conforming strictly to the requested BatchExtractionResponse schema."
        )
        return prompt

    def extract_batch(
        self,
        documents: List[Dict[str, str]],
        max_retries: int = 3,
    ) -> Optional[BatchExtractionResponse]:
        """Send a batch of documents to Gemini and return parsed BatchExtractionResponse.

        Args:
            documents: List of dicts with 'doc_id' and 'content_text'.
            max_retries: Max retry attempts on transient network or API errors.

        Returns:
            BatchExtractionResponse or None if extraction failed.
        """
        if not documents:
            return BatchExtractionResponse(documents=[])

        prompt_text = self.format_batch_prompt(documents)

        # Build few-shot context prefix
        few_shot_str = "FEW-SHOT EXAMPLES FOR REFERENCE:\n" + json.dumps(
            self.few_shot_examples, ensure_ascii=False, indent=2
        )
        full_system_instruction = f"{self.system_instruction}\n\n{few_shot_str}"

        for attempt in range(1, max_retries + 1):
            self.rate_limiter.acquire()
            try:
                logger.debug(f"Calling Gemini ({self.model}) for batch of {len(documents)} docs (attempt {attempt}/{max_retries})...")
                
                config = types.GenerateContentConfig(
                    system_instruction=full_system_instruction,
                    response_mime_type="application/json",
                    response_schema=BatchExtractionResponse,
                    temperature=0.1,
                )

                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt_text,
                    config=config,
                )

                if not response.text:
                    logger.warning(f"Empty response text from Gemini on attempt {attempt}")
                    time.sleep(2.0 * attempt)
                    continue

                # Parse JSON into Pydantic model
                raw_json = json.loads(response.text)
                parsed = BatchExtractionResponse.model_validate(raw_json)
                logger.debug(f"Gemini returned {len(parsed.documents)} extracted documents.")
                return parsed

            except json.JSONDecodeError as jde:
                logger.warning(f"JSON decode error on attempt {attempt}: {jde}")
                if attempt == max_retries:
                    logger.error(f"Failed to parse JSON response: {response.text[:300] if 'response' in locals() else 'None'}")
            except Exception as e:
                err_str = str(e)
                logger.warning(f"Gemini API error on attempt {attempt}/{max_retries}: {e}")

                # Check if retryDelay was specified in error details (e.g. 'retryDelay': '29s')
                custom_wait = None
                if "retry in " in err_str:
                    try:
                        import re
                        match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str)
                        if match:
                            custom_wait = float(match.group(1)) + 1.0
                    except Exception:
                        pass
                elif "retryDelay" in err_str:
                    try:
                        import re
                        match = re.search(r"['\"]retryDelay['\"]:\s*['\"](\d+)s['\"]", err_str)
                        if match:
                            custom_wait = float(match.group(1)) + 1.0
                    except Exception:
                        pass

                if custom_wait:
                    logger.info(f"Rate limit hit. Pausing for {custom_wait:.1f}s as requested by Gemini API...")
                    time.sleep(custom_wait)
                else:
                    wait_time = (2.0 ** attempt) + (0.5 * attempt)
                    time.sleep(wait_time)

        logger.error(f"Failed to extract batch of {len(documents)} documents after {max_retries} retries.")
        return None


# Global singleton instance
gemini_client = GeminiExtractionClient()
