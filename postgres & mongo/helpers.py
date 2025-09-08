"""Helpers"""
import json
import re
from typing import Optional


def extract_and_validate_json(text: str) -> Optional[str]:
    """
    Extracts and validates JSON from a string, handling code block
    markers and other potential issues. Returns the cleaned JSON
    string if valid, or None if invalid.
    """
    try:
        cleaned_text = re.sub(r"^```(json)?\s*|```\s*$",
                              "",
                              text.strip(),
                              flags=re.MULTILINE
                              ).strip()

        cleaned_text = re.sub(
            r',\s*([}\]])',
            r'\1',
            cleaned_text
        )

        # Parse the JSON
        parsed = json.loads(cleaned_text)
        return parsed

    except json.JSONDecodeError as e:
        print("JSON Decode Error: %s",
                     e,
                     exc_info=True
                     )
        return None
    except ValueError as e:
        print("Value Error during JSON extraction: %s",
                     e,
                     exc_info=True
                     )
        return None

    except (TypeError, AttributeError) as e:
        print("Type or Attribute Error during JSON extraction: %s",
                     e,
                     exc_info=True
                     )
        return None
