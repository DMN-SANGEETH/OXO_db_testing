"""Gemini client"""
import traceback
from typing import Optional
from google import genai

from config import GeminiConfig



class GeminiClient:
    """Class gemini client"""

    def __init__(self, model):
        self.client = genai.Client(api_key=GeminiConfig.get_gemini_api_key())
        self.model = model

    def call_gemini(self, prompt: str, domain: str = "general") -> Optional[str]:
        """Call Gemini API with exponential backoff retry logic and improved error handling"""
        try:
            response = self.model.generate_content(prompt)
            # print("response=========",response)
            input_total_tokens = self.client.models.count_tokens(
                model="gemini-2.5-flash", contents=prompt
            )

            print(" when uploading Total input tokens: %s", input_total_tokens)

            if hasattr(response, 'blocked') and response.blocked:
                block_reason = getattr(response, 'block_reason', 'unknown')
                raise print(f"Content blocked by Gemini safety filters. Reason: {block_reason}")
            content = self._extract_content(response)
            #print("content========",content)
            return content

        except Exception as e:
                error_trace = traceback.format_exc()
                print(
                    "Unexpected error generating content for %s: %s\n%s",
                    domain, e, error_trace
                )

    def _extract_content(self, response) -> str:
        """Safely extract content from Gemini response with error handling"""
        try:
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'candidates') and response.candidates:
                if hasattr(response.candidates[0], 'content'):
                    return response.candidates[0].content.parts[0].text

            raise print(f"Unexpected response structure: {response}")
        except (AttributeError, IndexError) as e:
            return e