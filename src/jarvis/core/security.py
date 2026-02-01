import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path

SEC_PATH = Path("config/security.json")

@dataclass
class AuthState:
    last_ok_ts: float = 0.0

class SecurityManager:
    def __init__(self, auth_window_seconds: int = 60) -> None:
        self._state = AuthState()
        self._window = auth_window_seconds

    def ensure_initialized(self) -> None:
        if SEC_PATH.exists():
            return
        SEC_PATH.parent.mkdir(parents=True, exist_ok=True)
        pw1 = getpass("Criar master password: ")
        pw2 = getpass("Repetir master password: ")
        if pw1 != pw2 or not pw1:
            raise SystemExit("Master password inválida.")
        salt = os.urandom(16)
        digest = self._pbkdf2(pw1.encode("utf-8"), salt)
        SEC_PATH.write_text(
            json.dumps(
                {
                    "kdf": "pbkdf2_sha256",
                    "iters": 200_000,
                    "salt_b64": base64.b64encode(salt).decode("ascii"),
                    "digest_b64": base64.b64encode(digest).decode("ascii"),
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    def authorize(self, reason: str) -> None:
        now = time.time()
        if now - self._state.last_ok_ts <= self._window:
            return

        self.ensure_initialized()
        if not self._verify_master():
            raise SystemExit("Autorização falhou (password).")

        code = f"{secrets.randbelow(1_000_000):06d}"
        print(f"AÇÃO DE RISCO: {reason}")
        print(f"Confirmar com: AUTHORIZE {code}")
        typed = input("> ").strip()
        if typed != f"AUTHORIZE {code}":
            raise SystemExit("Autorização falhou (código).")

        self._state.last_ok_ts = time.time()

    def _verify_master(self) -> bool:
        raw = json.loads(SEC_PATH.read_text(encoding="utf-8"))
        salt = base64.b64decode(raw["salt_b64"])
        good = base64.b64decode(raw["digest_b64"])
        pw = getpass("Master password: ")
        test = self._pbkdf2(pw.encode("utf-8"), salt)
        return hmac.compare_digest(test, good)

    def _pbkdf2(self, password: bytes, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password, salt, 200_000, dklen=32)
