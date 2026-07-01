import jwt
from config import JWT_SECRET, AUTH_PROVIDER

class AuthManager:
    # Responsibility: Manages tokens and credentials using JWT_SECRET and provider configuration
    def __init__(self):
        self.provider = AUTH_PROVIDER
        self.secret = JWT_SECRET

    def verify_token(self, token: str) -> dict:
        if self.provider == "mock":
            return {"user": "mock_user"}
        try:
            return jwt.decode(token, self.secret, algorithms=["HS256"])
        except Exception:
            return {}
