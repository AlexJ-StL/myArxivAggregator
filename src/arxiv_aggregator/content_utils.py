"""
Shared utilities for content generation across all aggregators.
Implements DRY methodology to eliminate code redundancy.
"""

import json
import re
from datetime import datetime

import requests

from arxiv_aggregator.config import OLLAMA_API_URL, OLLAMA_MODEL


def log(message):
    """Shared logging utility."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")


def call_ollama(prompt, max_tokens=200, temperature=0.2):
    """Shared Ollama API call function."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        log(f"Error calling Ollama: {e}")
        return None

    full_text = ""
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            chunk = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "response" in chunk:
            full_text += chunk["response"]
        if chunk.get("done"):
            break

    return full_text.strip()


def clean_generated_text(text):
    """Clean up LLM-generated text to remove narrative elements and XSS.

    This function handles both text formatting AND XSS sanitization as a
    defense-in-depth measure. HTML escaping is also done in generate_html.py
    at output time, but we sanitize early to prevent any potential issues.
    """
    if not text:
        return "[Generation failed]"

    # P0: XSS Sanitization - remove dangerous HTML/script content
    # This is defense-in-depth; generate_html.py also uses html.escape()
    xss_patterns = [
        (r"<script[^>]*>.*?</script>", ""),  # Remove <script> tags
        (r"<img[^>]*onerror[^>]*>", ""),  # Remove img onerror
        (r"<svg[^>]*onload[^>]*>", ""),  # Remove svg onload
        (r"<iframe[^>]*>.*?</iframe>", ""),  # Remove iframes
        (r"javascript:", ""),  # Remove javascript: URLs
        (r"onerror=", ""),  # Remove onerror attributes
        (r"onload=", ""),  # Remove onload attributes
        (r"onfocus=", ""),  # Remove onfocus attributes
        (r"onclick=", ""),  # Remove onclick attributes
        (r"<object[^>]*data[^>]*>", ""),  # Remove object with data
        (r"<embed[^>]*>", ""),  # Remove embed tags
        (r"<link[^>]*>", ""),  # Remove link tags
        (r"<body[^>]*onload[^>]*>", ""),  # Remove body onload
        (r"<input[^>]*onfocus[^>]*>", ""),  # Remove input onfocus
        (r"<marquee[^>]*onstart[^>]*>", ""),  # Remove marquee onstart
    ]

    cleaned = text.strip()
    
    # P0: First decode HTML entities to catch encoded attacks, then apply patterns
    # This ensures &lt;script&gt; becomes <script> and gets removed
    entity_map = {
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&#39;': "'",
        '&apos;': "'",
    }
    for entity, char in entity_map.items():
        cleaned = cleaned.replace(entity, char)
    
    # Also handle numeric entities
    cleaned = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), cleaned)
    cleaned = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), cleaned)

    for pattern, replacement in xss_patterns:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE | re.DOTALL)

    # Remove any remaining angle brackets that might be HTML
    # But be careful not to break legitimate text
    cleaned = re.sub(r"<[^>]*>", "", cleaned)
    
    # P0: If the cleaned text still contains dangerous patterns, fail secure
    dangerous_patterns = [
        r'<script',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*=',
        r'onfocus\s*=',
        r'onmouse',
        r'onkey',
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return "[Generation failed]"

    # Continue with text formatting (use cleaned, not text!)
    if not cleaned:
        return "[Generation failed]"

    # Remove common narrative prefixes and explanations
    narrative_patterns = [
        r"^Here.*?:",
        r"^Two sentences.*?:",
        r"^Explanation.*?:",
        r"^Story.*?:",
        r"^Headline.*?:",
        r"^\*\*.*?\*\*",  # Remove **Style 1:** etc.
        r"^Style \d+.*?:",
        r"^Option \d+.*?:",
        r"^Possible.*?:",
        r"^This headline.*",
        r"^I removed.*",
        r"^I also.*",
        r"^The word.*",
        r"^\d+\.\s*\*\*.*?\*\*",  # Remove numbered options
        r"^\d+\.\s*\".*?\"",  # Remove numbered quotes
        r"^\d+\.\s+",  # Remove numbered lists
        r"\(I.*?\)",  # Remove parenthetical explanations
        r"This headline.*",
        r"The focus is.*",
        r"rather than.*",
    ]

    for pattern in narrative_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)

    # P1: Remove numbered list items throughout the text (not just at start)
    cleaned = re.sub(r"\d+\.\s+", "", cleaned)

    # Remove quotes at the beginning and end
    cleaned = cleaned.strip('"').strip("'").strip()

    # Remove multiple newlines and clean up
    cleaned = re.sub(r"\n\s*\n", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)

    # P1: Remove trailing periods from headlines (they shouldn't end with periods)
    cleaned = cleaned.rstrip(".")

    # Check for explanatory phrases that indicate the LLM added extra content
    explanatory_phrases = ["this headline", "the word", "i removed", "the focus"]
    if any(phrase in cleaned.lower() for phrase in explanatory_phrases):
        # Split on common explanation starters and take the first part
        split_phrases = [" This headline", " The word", " I removed", " The focus", " (I"]
        for split_phrase in split_phrases:
            if split_phrase in cleaned:
                cleaned = cleaned.split(split_phrase)[0].strip()
                break

    # For summaries, take only the first two sentences
    sentences = re.split(r"[.!?]+", cleaned)
    if len(sentences) >= 2:
        cleaned = ". ".join(sentences[:2]).strip() + "."
    elif len(sentences) == 1 and sentences[0].strip():
        cleaned = sentences[0].strip() + "."

    return cleaned.strip()


def rewrite_title(
    original_title,
    category="research",
    original_synopsis=None,
    rewritten_summary=None,
):
    """Generate an engaging headline from an academic title.

    Args:
        original_title: The original academic title from the paper.
        category: The research category.
        original_synopsis: Optional original synopsis from the feed.
        rewritten_summary: Optional rewritten summary for context.

    Returns:
        A concise, engaging headline for general audiences.
    """
    # Build context information for better headline generation
    context_info = ""
    if original_synopsis:
        context_info += f'\n\nOriginal Synopsis: "{original_synopsis}"'
    if rewritten_summary:
        context_info += f'\n\nRewritten Summary: "{rewritten_summary}"'

    # Enhanced headline prompt
    prompt = (
        "Rewrite the following academic title as a concise, engaging headline "
        "for a general audience interested in AI breakthroughs. Use plain "
        "language; avoid technical jargon and opt for more accessible terms. "
        "Focus on the core idea. Keep it under 60 characters. Use title case. "
        "Do NOT use clickbait or sensational phrasing. OUTPUT ONLY the "
        "headline text. Do NOT include any explanations, quotes, extra "
        "punctuation, line breaks. Do NOT use periods. "
        f"Original Title and Context Info: {original_title} {context_info}"
    )

    # Call Ollama API to generate the headline
    text = call_ollama(prompt, max_tokens=1024, temperature=0.2)
    cleaned = clean_generated_text(text)

    # P1: Check if generation failed, fallback to original title
    if cleaned == "[Generation failed]":
        return original_title

    # Take only the first line if multiple lines
    lines = cleaned.split("\n")
    headline = lines[0].strip().strip('"').strip("'")

    return headline if headline else original_title


def rewrite_blurb(title, summary, category="research"):
    """Generate an engaging summary from an academic abstract."""
    # Sentence-level prompt
    prompt = (
        "Rewrite the following abstract into two plain-language sentences "
        "for a general readership. Sentence 1 must explain what the "
        "researchers did, using simple terms instead of technical phrases. "
        "Sentence 2 must describe why it matters (impact, potential, or "
        "benefit), again without jargon."
    )

    # Restrictions prompt
    prompt += (
        " Do NOT: Use or explain advanced terminology like 'Differential "
        "Information Distribution' or 'log-ratio reward parameterization.' "
        "Instead, replace those with brief, easy-to-understand descriptions "
        "(e.g., 'smarter data signals')."
    )

    # More restrictions
    prompt += (
        " Do NOT begin with 'Researchers' or any variant. Do NOT use "
        "directive/opening phrases like 'Imagine…', 'You'll want to…', or "
        "'In this paper…'."
    )

    # Final instruction
    prompt += (
        " Do NOT include more than two sentences or add any commentary. "
        f"OUTPUT ONLY the two sentences as a single block. Abstract: '{summary}'"
    )

    text = call_ollama(prompt, max_tokens=4096, temperature=0.2)
    cleaned = clean_generated_text(text)

    return (
        cleaned if cleaned and cleaned != "[Generation failed]" else "[Summary generation failed]"
    )


def generate_search_keywords(title, summary, category="technology"):
    """Generate search keywords for Unsplash based on article content."""
    prompt = f"{title}\n\nOne visual keyword for photos:"

    text = call_ollama(prompt, max_tokens=5, temperature=0.2)
    if text:
        # Clean up the response aggressively
        cleaned = clean_generated_text(text)
        # Take only the first word/phrase
        keywords = [k.strip().strip('"').strip("'") for k in cleaned.split(",")]
        keyword = keywords[0] if keywords else category
        # Remove any remaining explanatory text
        keyword = keyword.split("\n")[0].split(".")[0].strip()
        
        # P0: Path traversal prevention - remove dangerous path characters
        keyword = keyword.replace("..", "")
        keyword = keyword.replace("/", "")
        keyword = keyword.replace("\\", "")
        keyword = keyword.replace("file://", "")
        
        return keyword if keyword else category
    return category
