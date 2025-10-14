import os
import json
from typing import Optional
from kiteconnect import KiteConnect

# Store the session OUTSIDE the code root so a docker volume doesn't overlay source.
# Compose should mount a named volume at /app/app/data/session
SESSION_DIR = os.path.join(os.path.dirname(__file__), "data", "session")
os.makedirs(SESSION_DIR, exist_ok=True)
SESSION_PATH = os.path.join(SESSION_DIR, ".kite_session.json")


class KiteSession:
    def __init__(self):
        self.api_key: str = os.getenv("KITE_API_KEY", "")
        self.api_secret: str = os.getenv("KITE_API_SECRET", "")
        self.redirect_uri: str = os.getenv("KITE_REDIRECT_URI", "")
        self.kite = KiteConnect(api_key=self.api_key)
        self.access_token: Optional[str] = None

    def login_url(self) -> str:
        # Redirect the user to this URL to initiate OAuth
        return self.kite.login_url()

    def exchange_for_token(self, request_token: str) -> dict:
        """
        Exchange the one-time request_token for an access_token and persist it.
        NOTE: The response contains datetime objects; use default=str for JSON.
        """
        data = self.kite.generate_session(request_token, api_secret=self.api_secret)
        self.access_token = data["access_token"]
        self.kite.set_access_token(self.access_token)
        with open(SESSION_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return data

    def restore(self) -> bool:
        """Load a previously saved session from disk (if any) and set access_token."""
        if not os.path.exists(SESSION_PATH):
            return False
        try:
            with open(SESSION_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return False
        tok = data.get("access_token")
        if not tok:
            return False
        self.access_token = tok
        self.kite.set_access_token(tok)
        return True


_kite: Optional[KiteSession] = None


def get_kite() -> KiteSession:
    """Singleton accessor; restores session if present."""
    global _kite
    if _kite is None:
        _kite = KiteSession()
        _kite.restore()
    return _kite
