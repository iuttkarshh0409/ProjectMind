import os

# Config keys for system setup
PORT = int(os.getenv("PORT", "8080"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/taskdb")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretjwtkey")
AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "firebase")
