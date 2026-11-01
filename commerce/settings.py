import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent


def truth(value):
    return str(value).lower() in {"1", "true", "yes"}


@dataclass
class Settings:
    payment_mode: str = "rehearsal"
    ai_mode: str = "local"
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_max_tokens: int = 4000
    ai_base_url: str = "https://api.tokenfactory.nebius.com/v1"
    public_base_url: str = "http://localhost:8000"
    database_path: str = str(ROOT / "data" / "commerce.db")
    cookie_secure: bool = False
    ai_session_limit: int = 20
    ai_global_limit: int = 100
    payment_session_limit: int = 40
    payment_global_limit: int = 200
    session_days: int = 7

    def planner_identity(self):
        """Public labels only: never expose a key or configurable API URL."""
        if self.ai_mode != "provider":
            return {"ai_provider": "Local rehearsal planner", "ai_model": None}
        hostname = urlparse(self.ai_base_url).hostname
        provider = "Nebius Token Factory" if hostname in {
            "api.tokenfactory.nebius.com", "api.studio.nebius.ai"
        } else "Configured AI provider"
        return {"ai_provider": provider, "ai_model": self.ai_model}

    @classmethod
    def from_env(cls):
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env", override=False)
        return cls(
            payment_mode=os.getenv("PAYMENT_MODE", "rehearsal"),
            ai_mode=os.getenv("AI_MODE", "local"),
            paypal_client_id=os.getenv("PAYPAL_CLIENT_ID", ""),
            paypal_client_secret=os.getenv("PAYPAL_CLIENT_SECRET", ""),
            ai_api_key=os.getenv("AI_API_KEY") or os.getenv("NEBIUS_API_KEY", ""),
            ai_model=os.getenv("AI_MODEL") or os.getenv("NEBIUS_MODEL", ""),
            ai_max_tokens=int(os.getenv("AI_MAX_TOKENS", "4000")),
            ai_base_url=os.getenv("AI_BASE_URL") or os.getenv("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"),
            public_base_url=(os.getenv("PUBLIC_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "http://localhost:8000").rstrip("/"),
            database_path=os.getenv("DATABASE_PATH", str(ROOT / "data" / "commerce.db")),
            cookie_secure=truth(os.getenv("COOKIE_SECURE", "false")),
            ai_session_limit=int(os.getenv("AI_SESSION_HOURLY_LIMIT", "20")),
            ai_global_limit=int(os.getenv("AI_GLOBAL_HOURLY_LIMIT", "100")),
            payment_session_limit=int(os.getenv("PAYMENT_SESSION_HOURLY_LIMIT", "40")),
            payment_global_limit=int(os.getenv("PAYMENT_GLOBAL_HOURLY_LIMIT", "200")),
        )

    def validate(self):
        if self.payment_mode not in {"rehearsal", "sandbox"}:
            raise ValueError("PAYMENT_MODE must be rehearsal or sandbox; live payments are disabled.")
        if self.ai_mode not in {"local", "provider"}:
            raise ValueError("AI_MODE must be local or provider.")
        if self.payment_mode == "sandbox" and not (self.paypal_client_id and self.paypal_client_secret):
            raise ValueError("Sandbox mode requires PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.")
        if self.ai_mode == "provider" and not (self.ai_api_key and self.ai_model):
            raise ValueError("Provider mode requires AI_API_KEY and AI_MODEL.")
        parsed = urlparse(self.public_base_url)
        local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
            raise ValueError("PUBLIC_BASE_URL must be an origin without credentials, path, query, or fragment.")
        if parsed.scheme != "https" and not (local and parsed.scheme == "http"):
            raise ValueError("PUBLIC_BASE_URL requires HTTPS, except for localhost development.")
        if not local and not self.cookie_secure:
            raise ValueError("Set COOKIE_SECURE=true for HTTPS deployment.")
        ai_url = urlparse(self.ai_base_url)
        if ai_url.scheme != "https" or not ai_url.hostname or ai_url.username or ai_url.password or ai_url.query or ai_url.fragment:
            raise ValueError("AI_BASE_URL must be an HTTPS API base URL without credentials/query/fragment.")
        if not 512 <= self.ai_max_tokens <= 8192:
            raise ValueError("AI_MAX_TOKENS must be between 512 and 8192.")
        if min(self.ai_session_limit, self.ai_global_limit, self.payment_session_limit, self.payment_global_limit) < 1:
            raise ValueError("Hourly rate limits must be positive.")
