import logging
from ..clients.llm_client import generate_response

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful and friendly e-commerce shopping assistant. "
    "Based on the product information provided, draft a brief, conversational "
    "response for the customer. Be concise, warm, and helpful. "
    "Do NOT list or describe products in detail — just acknowledge what you "
    "found and guide the customer. Keep your response to 2-3 sentences."
)


def _build_product_list(product_context: list[dict]) -> str:
    """Format lightweight product info for inclusion in the LLM prompt."""
    if not product_context:
        return "No products available."

    lines: list[str] = []
    for i, p in enumerate(product_context, 1):
        parts = [p.get("name", "Unknown")]
        if p.get("brand"):
            parts.append(f"by {p['brand']}")
        if p.get("type"):
            sub = f"/{p['subtype']}" if p.get("subtype") else ""
            parts.append(f"({p['type']}{sub})")
        if p.get("price"):
            parts.append(f"- ${p['price']}")
        lines.append(f"{i}. {' '.join(parts)}")

    return "\n".join(lines)


def _build_scenario_instruction(
    scenario: str, total_matches: int, returned_count: int, requested_count: int
) -> str:
    """Generate scenario-specific guidance for the LLM prompt."""
    if scenario == "empty":
        return (
            "No products matched the customer's search. Suggest they broaden "
            "their search or explore different categories. Be helpful and encouraging."
        )
    elif scenario == "shortage":
        return (
            f"Only {returned_count} products matched their request "
            f"(they wanted {requested_count}). Gently acknowledge that the "
            f"selection is limited but highlight what's available."
        )
    elif scenario == "overflow":
        return (
            f"Found {total_matches} matching products but showing the top "
            f"{returned_count}. Let the customer know there are more options "
            f"available if they'd like to see them."
        )
    else:
        return f"Here are {returned_count} matching products. Present them enthusiastically."


def _build_fallback_response(
    scenario: str, total_matches: int, returned_count: int, requested_count: int
) -> str:
    """Template responses used when the LLM is unavailable."""
    if scenario == "empty":
        return (
            "I couldn't find any products matching your search. "
            "Try broadening your criteria or exploring different categories "
            "— I'm here to help!"
        )
    elif scenario == "shortage":
        return (
            f"I could only find {returned_count} products matching your search. "
            f"Here's what I found — let me know if you'd like to explore other options!"
        )
    elif scenario == "overflow":
        return (
            f"Great news! I found {total_matches} products matching your search. "
            f"Here are the top {returned_count} results. "
            f"Let me know if you'd like to see more!"
        )
    else:
        return (
            f"Here are {returned_count} products I found for you. "
            f"Let me know if any of these catch your eye!"
        )


def respond(state: dict) -> dict:
    """
    LangGraph node: Generate the final conversational AI response.
    The RAG Engine returns ONLY {ai_response, product_ids} — no full product objects.
    """
    query = state["query"]
    intent = state.get("intent", "search")
    chat_history = state.get("chat_history", [])
    
    # Format compact history for LLM
    history_text = ""
    if chat_history:
        lines = []
        for msg in chat_history[-4:]:
            content = msg['message']
            if msg['role'] == 'assistant' and len(content) > 100:
                content = content[:100] + "... [truncated]"
            lines.append(f"{msg['role'].capitalize()}: {content}")
        history_text = f"Previous Conversation:\n" + "\n".join(lines) + "\n\n"

    if intent == "chat":
        prompt = f'{history_text}Customer\'s query: "{query}"\n\nPlease answer naturally.'
        sys_prompt = (
            "You are a helpful and friendly e-commerce shopping assistant. "
            "Answer the customer's conversational or general question. "
            "Be concise, warm, and helpful. Keep it to 2-3 sentences. "
            "IMPORTANT: Do NOT output any internal notes, thoughts, or explanations of your strategy. Just output the final response directly to the user."
        )
        llm_response = generate_response(prompt, system_prompt=sys_prompt)
        ai_response = llm_response.strip() if llm_response else "I'm here to help with your shopping or any questions you have!"
        logger.info(f"Generated chat response: {ai_response[:100]}...")
        return {"ai_response": ai_response, "product_ids": []}

    product_context = state.get("product_context", [])
    scenario = state.get("scenario", "normal")
    total_matches = state.get("total_matches", 0)
    product_ids = state.get("product_ids", [])
    requested_count = state.get("requested_count", 10)
    returned_count = len(product_ids)

    # Build the LLM prompt
    product_list = _build_product_list(product_context)
    scenario_instruction = _build_scenario_instruction(
        scenario, total_matches, returned_count, requested_count
    )

    prompt = (
        f'{history_text}Customer\'s query: "{query}"\n\n'
        f"{scenario_instruction}\n\n"
        f"Available products:\n{product_list}\n\n"
        f"Draft a brief, natural response (2-3 sentences max). "
        f"Do NOT list products — just acknowledge the results conversationally."
    )

    # Try LLM, fall back to template
    llm_response = generate_response(prompt, system_prompt=SYSTEM_PROMPT)

    if llm_response:
        ai_response = llm_response.strip()
    else:
        ai_response = _build_fallback_response(
            scenario, total_matches, returned_count, requested_count
        )

    logger.info(f"Generated response (scenario={scenario}): {ai_response[:100]}...")

    return {
        "ai_response": ai_response,
    }
