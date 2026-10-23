import base64
import hashlib
import hmac
import json
import time

from app.errors import ApiError


class CursorCodec:
    def __init__(self, secret):
        self.secret = secret.encode()

    def encode(self, state, partition):
        raw = json.dumps({"state": base64.b64encode(state).decode(), "partition": partition,
                          "expires": int(time.time())+3600}, separators=(",", ":")).encode()
        signature = hmac.digest(self.secret, raw, hashlib.sha256)
        return base64.urlsafe_b64encode(signature+raw).decode()

    def decode(self, token, partition):
        if token is None:
            return None
        try:
            data = base64.b64decode(token, altchars=b"-_", validate=True)
            signature, raw = data[:32], data[32:]
            if not hmac.compare_digest(signature, hmac.digest(self.secret, raw, hashlib.sha256)):
                raise ValueError()
            payload = json.loads(raw)
            if payload["partition"] != partition or payload["expires"] < time.time():
                raise ValueError()
            return base64.b64decode(payload["state"], validate=True)
        except (ValueError, KeyError, TypeError):
            raise ApiError(422, "cursor_invalido", "El cursor es invalido, expiro o corresponde a otra consulta.") from None
