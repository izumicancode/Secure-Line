"""Base64 wire-encoding helpers shared by every module that puts
ciphertext or key bytes into a JSON envelope."""
import base64


def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))
