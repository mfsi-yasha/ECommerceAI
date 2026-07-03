import logging
from langgraph.prebuilt import create_react_agent

from .tools import product_search_tool, calculator_tool
from .clients.llm_client import get_llm
from .config import LOCAL_MODEL_LABEL

logger = logging.getLogger(__name__)

TOOLS = [product_search_tool, calculator_tool]

AGENT_SYSTEM_PROMPT = (
    "You are a helpful and friendly e-commerce shopping assistant. "
    "You have access to tools for searching the product catalog and performing calculations.\n\n"
    "RULES:\n"
    "1. When a customer asks about products, ALWAYS use the product_search_tool to find real products. "
    "NEVER make up product names, prices, or details.\n"
    "2. When calculations are needed (discounts, totals, tax, comparisons), ALWAYS use the calculator_tool. "
    "NEVER do math in your head.\n"
    "3. For greetings or general conversation, respond naturally without using tools.\n"
    "4. After getting product results, present them in a warm, conversational way. "
    "Keep responses concise (3-5 sentences max).\n"
    "5. When presenting products, always mention their names, brands, and prices from the tool results.\n"
    "6. If the product search returns no results, suggest broadening the search.\n"
)


def build_agent(provider: str = LOCAL_MODEL_LABEL):
    """
    Build a ReAct agent graph with the given LLM provider.

    The agent is constructed per-request so the user can dynamically
    switch between Local and Cloud LLMs from the frontend.

    Args:
        provider: The LLM provider string from the frontend dropdown.

    Returns:
        A compiled LangGraph agent ready for invocation.
    """
    llm = get_llm(provider)
    agent = create_react_agent(llm, TOOLS, prompt=AGENT_SYSTEM_PROMPT)
    logger.info(f"Built ReAct agent with provider='{provider}' and {len(TOOLS)} tools")
    return agent
