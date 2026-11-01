import re
import uuid
from .store import now_iso


def local_recommend(prompt, budget, catalog):
    words = set(re.findall(r"[a-z]+", prompt.lower()))
    synonyms = {
        "programming": "coding", "developer": "coding", "programmer": "coding",
        "studying": "study", "student": "study", "college": "study", "lighting": "night",
        "comfortable": "comfort", "ergonomics": "ergonomic", "meeting": "calls",
        "meetings": "calls", "zoom": "calls", "remote": "calls", "minimal": "desk",
    }
    words.update(synonyms[word] for word in list(words) if word in synonyms)
    default = {"rise-stand": 3, "quiet-keyboard": 2, "arc-lamp": 1}
    ranking = sorted(catalog, key=lambda item: (
        -(sum(3 for tag in item["tags"] if tag in words) + default.get(item["id"], 0)),
        item["price_cents"],
    ))
    chosen, total = [], 0
    for item in ranking:
        if len(chosen) == 4:
            break
        if total + item["price_cents"] <= budget:
            matched = [tag for tag in item["tags"] if tag in words]
            reason = ("Matches your " + ", ".join(matched[:2]) + " priorities.") if matched else "A practical complement within your budget."
            chosen.append({"product_id": item["id"], "quantity": 1, "reason": reason})
            total += item["price_cents"]
    return {"summary": "A practical desk setup selected from your priorities, with every price checked against your budget.",
            "items": chosen,
            "tradeoffs": ["These are fictional catalog products for a sandbox demonstration.",
                          "Local rehearsal uses keyword matching; enable the AI provider for model-generated recommendations."]}


def make_plan(prompt, budget_cents, recommendation, catalog, source):
    if not isinstance(recommendation, dict):
        raise ValueError("The recommendation must be a structured object.")
    suggested = recommendation.get("items")
    if not isinstance(suggested, list) or not 1 <= len(suggested) <= 12:
        raise ValueError("No suitable products fit this request. Increase your budget or revise your preferences.")
    products = {item["id"]: item for item in catalog}
    items, seen, total = [], set(), 0
    for suggestion in suggested:
        if not isinstance(suggestion, dict):
            raise ValueError("Invalid product suggestion.")
        product_id, quantity = suggestion.get("product_id"), suggestion.get("quantity", 1)
        if not isinstance(product_id, str) or product_id not in products or product_id in seen:
            raise ValueError("The recommendation contains an unknown or duplicate catalog product.")
        if type(quantity) is not int or not 1 <= quantity <= 5:
            raise ValueError("Each product quantity must be between one and five.")
        seen.add(product_id)
        product = products[product_id]
        line_total = quantity * product["price_cents"]
        total += line_total
        reason = suggestion.get("reason", "Selected by you.")
        if not isinstance(reason, str):
            raise ValueError("Invalid product explanation.")
        items.append({"product_id": product_id, "quantity": quantity, "name": product["name"],
                      "unit_price_cents": product["price_cents"], "line_total_cents": line_total,
                      "reason": reason[:400]})
    if total > budget_cents:
        raise ValueError("This cart exceeds your budget. Remove a product or reduce its quantity.")
    summary = recommendation.get("summary", "Your reviewed desk setup.")
    tradeoffs = recommendation.get("tradeoffs", [])
    if not isinstance(summary, str) or not isinstance(tradeoffs, list) or any(not isinstance(x, str) for x in tradeoffs):
        raise ValueError("The recommendation contains invalid explanations.")
    return {"id": str(uuid.uuid4()), "prompt": prompt, "budget_cents": budget_cents,
            "items": items, "total_cents": total, "remaining_cents": budget_cents - total,
            "summary": summary[:800], "tradeoffs": [x[:400] for x in tradeoffs[:5]],
            "ai_source": source, "created_at": now_iso()}
