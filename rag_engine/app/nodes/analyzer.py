import json
import logging
from ..clients.llm_client import generate_response

logger = logging.getLogger(__name__)


# ─── LangGraph Node ──────────────────────────────────────────────────────────

def analyze_query(state: dict) -> dict:
    """
    LangGraph node: Analyzes intent using LLM and chat history, rewrites query if needed,
    and extracts numeric filters dynamically.
    """
    query = state["query"]
    chat_history = state.get("chat_history", [])
    
    # 1. Format compact history for LLM
    history_text = "No history."
    if chat_history:
        lines = []
        for msg in chat_history[-4:]:
            content = msg['message']
            if msg['role'] == 'assistant' and len(content) > 100:
                content = content[:100] + "... [truncated]"
            lines.append(f"{msg['role'].capitalize()}: {content}")
        history_text = "\n".join(lines)

    sys_prompt = (
        "You are a query analyzer for an e-commerce assistant. "
        "Analyze the user's latest query given the chat history. "
        "Output ONLY a JSON object with these keys:\n"
        "1. 'intent': either 'search' (looking for products) or 'chat' (general conversation/greeting/math).\n"
        "2. 'search_query': if intent is search and the user says 'load more' or 'next page', rewrite this to "
        "the actual product they are looking for based on history (e.g. 'samsung phones'). Otherwise use their query.\n"
        "3. 'offset': if they are asking for more/next page, output an integer like 10, 20, etc based on how many they've seen. Default is 0.\n"
        "4. 'min_price': (optional) float value if the user specifies a minimum price or 'over $X'.\n"
        "5. 'max_price': (optional) float value if the user specifies a maximum price or 'under $X'.\n"
        "6. 'brand': (optional) string value if the user explicitly specifies a brand (e.g. 'Samsung', 'Apple', 'Nike').\n"
        "7. 'type': (optional) string value if the user explicitly specifies a broad category (e.g. 'Electronics', 'Apparel').\n"
        "8. 'subtype': (optional) string value if the user explicitly specifies a sub-category (e.g. 'Mobile', 'Laptop', 'Shirt', 'Shoes').\n"
        "Do not include optional keys if not explicitly mentioned."
    )
    
    user_prompt = f"Chat History:\n{history_text}\n\nLatest Query: {query}\n\nOutput JSON only."
    
    intent = "search"
    search_query = query
    offset = 0
    filters = {}
    
    try:
        # Ask LLM for JSON intent and filters
        llm_response = generate_response(user_prompt, system_prompt=sys_prompt, json_mode=True)
        
        if llm_response:
            # Extract JSON from potential markdown blocks
            json_str = llm_response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            data = json.loads(json_str)
            intent = data.get("intent", "search").lower()
            
            if "search_query" in data and data["search_query"] not in (None, ""):
                search_query = data["search_query"]
            
            if "offset" in data and isinstance(data["offset"], int):
                offset = data["offset"]
            
            if "min_price" in data and data["min_price"] not in (None, ""):
                filters["min_price"] = float(data["min_price"])
            if "max_price" in data and data["max_price"] not in (None, ""):
                filters["max_price"] = float(data["max_price"])
                
            if "brand" in data and data["brand"] not in (None, ""):
                filters["brand"] = data["brand"]
            if "type" in data and data["type"] not in (None, ""):
                filters["type"] = data["type"]
            if "subtype" in data and data["subtype"] not in (None, ""):
                filters["subtype"] = data["subtype"]
                
            logger.info(f"Analyzer LLM output: {data}")
    except Exception as e:
        logger.warning(f"Failed to parse analyzer JSON from LLM: {e}. Falling back to default chat intent.")
        intent = "chat"
    
    # If the user is just chatting, skip filtering
    if intent == "chat":
        return {
            "intent": "chat",
            "search_query": query,
            "filters": {},
            "offset": 0,
            "requested_count": 0
        }

    logger.info(f"Analyzed query '{query}' → intent='{intent}', search='{search_query}', offset={offset}, filters={filters}")

    return {
        "intent": intent,
        "search_query": search_query,
        "offset": offset,
        "filters": filters,
        "requested_count": 10, # Keep a default page size of 10
    }
