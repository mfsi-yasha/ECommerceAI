import logging

logger = logging.getLogger(__name__)

DEFAULT_LIMIT = 10


def rank_results(state: dict) -> dict:
    """
    LangGraph node: Apply pagination logic and classify the result scenario.
    """
    candidate_ids = state["candidate_ids"]
    product_context = state["product_context"]
    total_matches = state["total_matches"]
    requested_count = state["requested_count"]
    filters = state["filters"]

    # Allow exceeding the 10-product cap only when the user explicitly asked
    # for more AND provided a specific category filter.
    has_category = bool(filters.get("type") or filters.get("subtype"))

    if requested_count > DEFAULT_LIMIT and has_category:
        effective_limit = requested_count
    else:
        effective_limit = min(requested_count, DEFAULT_LIMIT)

    # ── Classify scenario ────────────────────────────────────────────────────
    if total_matches == 0:
        scenario = "empty"
        final_ids: list[int] = []
        final_context: list[dict] = []

    elif total_matches <= effective_limit:
        scenario = "shortage" if total_matches < requested_count else "normal"
        final_ids = candidate_ids[:total_matches]
        final_context = product_context[:total_matches]

    else:
        scenario = "overflow"
        final_ids = candidate_ids[:effective_limit]
        final_context = product_context[:effective_limit]

    logger.info(
        f"Ranking: total={total_matches}, requested={requested_count}, "
        f"effective_limit={effective_limit}, returning={len(final_ids)}, "
        f"scenario={scenario}"
    )

    return {
        "product_ids": final_ids,
        "product_context": final_context,
        "scenario": scenario,
    }
