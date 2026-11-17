"""Create the signing key pairs (main + backup) in ./keys/. Run once; never commit keys/."""
from pathlib import Path

from .signing import generate_pem

out = Path("keys")
out.mkdir(exist_ok=True)
for name in ("main", "backup"):
    priv, pub = generate_pem()
    (out / f"{name}_private.pem").write_bytes(priv)
    (out / f"{name}_public.pem").write_bytes(pub)
print("Keys written to ./keys. Read robot/keygen.py for what to do with each file.")
