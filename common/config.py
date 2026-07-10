"""Tiny .env loader; env vars override file values. No dependencies."""
import os

_loaded = False


def _load_dotenv() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def get(key: str, default: str = "") -> str:
    _load_dotenv()
    return os.environ.get(key, default)


def root_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path(rel: str) -> str:
    """Path relative to project root, dirs created."""
    p = os.path.join(root_dir(), rel)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    return p
