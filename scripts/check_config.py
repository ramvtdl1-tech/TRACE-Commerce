"""Validate settings without calling paid providers or displaying secrets."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from commerce.settings import Settings


def main():
    try:
        settings = Settings.from_env()
        settings.validate()
    except (ValueError, TypeError) as exc:
        print("Configuration invalid: " + str(exc))
        return 1
    print("Configuration valid.")
    print("Payments: " + settings.payment_mode)
    print("Planner: " + settings.ai_mode)
    if settings.payment_mode != "sandbox" or settings.ai_mode != "provider":
        print("Rehearsal configuration: enable sandbox + provider for the hackathon demo.")
    print("No provider request or payment was made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
