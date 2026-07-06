"""
Prompt Templates (Phase 3.3)

Defines how the context and user query are assembled before
being sent to the LLM.
"""

from config.settings import SYSTEM_PROMPT

def build_context_prompt(context_block: str, user_query: str) -> str:
    """
    Assemble retrieved chunks and query into a structured LLM prompt string.
    """
    prompt = f"""
CONTEXT INFORMATION:
{context_block}

USER QUERY:
{user_query}

INSTRUCTIONS:
Using ONLY the context provided above, answer the user query.
If the context does not contain the answer, strictly reply with the fallback message.
Do not hallucinate or use outside knowledge.
"""
    return prompt.strip()
