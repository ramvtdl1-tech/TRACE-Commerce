"""Offline source/configuration checks; this does not submit or determine eligibility."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from commerce.settings import Settings

REQUIRED_ARTIFACTS = (
    "README.md", "LICENSE", ".env.example", "requirements.txt", "Dockerfile",
    "compose.yaml", "render.yaml", "catalog.json", "commerce/app.py",
    "static/index.html", "static/app.js", "static/styles.css",
    "docs/HACKATHON.md", "docs/SUBMISSION.md", "docs/DEMO_SCRIPT.md",
    "docs/JUDGE_GUIDE.md", "docs/RESOURCES.md", "docs/VERIFICATION.md",
    "postman/trace-commerce.postman_collection.json",
    "postman/trace-commerce.postman_environment.json", "postman/README.md",
)


def artifact_issues(root=ROOT):
    root = Path(root)
    issues = []
    for name in REQUIRED_ARTIFACTS:
        path = root / name
        if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
            issues.append("Missing, empty or unsafe source artifact: " + name)
    if issues:
        return issues
    license_text = (root / "LICENSE").read_text()
    if not license_text.startswith("MIT License") or "Permission is hereby granted" not in license_text:
        issues.append("Review the repository's open-source license.")
    try:
        collection = json.loads((root / "postman/trace-commerce.postman_collection.json").read_text())
        environment = json.loads((root / "postman/trace-commerce.postman_environment.json").read_text())
        if collection["info"]["schema"] != "https://schema.getpostman.com/json/collection/v2.1.0/collection.json":
            raise ValueError()
        if not collection.get("item") or environment.get("_postman_variable_scope") != "environment":
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        issues.append("The included Postman collection/environment is not valid expected JSON.")
    return issues


def configuration_issues(settings):
    issues = []
    try:
        settings.validate()
    except (ValueError, TypeError):
        # Never echo configuration values, including malformed inputs containing keys.
        issues.append("Server configuration is invalid. Run scripts/check_config.py and review .env privately.")
    if settings.payment_mode != "sandbox":
        issues.append("Set PAYMENT_MODE=sandbox for the submitted PayPal demonstration.")
    if not (settings.paypal_client_id and settings.paypal_client_secret):
        issues.append("Configure merchant PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET on the server.")
    if settings.ai_mode != "provider":
        issues.append("Set AI_MODE=provider; deterministic local matching is rehearsal only.")
    if not (settings.ai_api_key and settings.ai_model):
        issues.append("Configure a real AI provider key and an available model on the server.")
    return issues


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-only", action="store_true", help="Check source handoff files without requiring credentials; suitable for CI.")
    args = parser.parse_args(argv)
    issues = artifact_issues()
    if not args.artifacts_only:
        try:
            issues.extend(configuration_issues(Settings.from_env()))
        except (ValueError, TypeError):
            issues.append("Server configuration could not be read. Review environment values privately.")
    for issue in issues:
        print("USER ACTION: " + issue)
    if issues:
        print("CHECK FAILED: missing preparation remains. No API call, payment or submission was made.")
        return 1
    print("PASS: required source handoff artifacts are present.")
    if not args.artifacts_only:
        print("PASS: provider AI and PayPal sandbox are configured (not live-verified by this command).")
    print("USER ACTION: verify the combined live-provider + sandbox buyer flow, public source/license,")
    print("judge access, publicly visible YouTube video under 3 minutes, entrant eligibility and Devpost entry.")
    print("No API call, payment or submission was made. This check cannot determine eligibility or acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
