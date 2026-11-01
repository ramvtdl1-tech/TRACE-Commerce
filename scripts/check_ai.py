"""Make one bounded real AI planning request using configured server credentials."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from commerce.settings import ROOT, Settings
from commerce.providers import AIClient, ProviderError
from commerce.planner import make_plan


def main():
    settings = Settings.from_env()
    settings.ai_mode = "provider"
    try:
        settings.validate()
        catalog = json.loads((ROOT / "catalog.json").read_text())
        prompt = "Build a calm home office for video calls under $300"
        recommendation = AIClient(settings).recommend(prompt, 30000, catalog)
        plan = make_plan(prompt, 30000, recommendation, catalog, "provider")
    except (ProviderError, ValueError) as error:
        print("AI check failed: " + str(error))
        return 1
    print("Real AI planning and server catalog/budget validation passed.")
    print("Items: " + str(len(plan["items"])))
    print("Total: $" + format(plan["total_cents"] / 100, ".2f") + " / $300.00 USD")
    print("No payment was created or captured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
