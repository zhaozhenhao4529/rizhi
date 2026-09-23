"""全局配置：从环境变量 / .env 读取，无 key 时自动进入 Mock 模式。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "wardrobe.db"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)


def _load_dotenv():
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

# ---- AI 配置（OpenAI 兼容接口，默认指向阿里云百炼 DashScope）----
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen-vl-plus")
TEXT_MODEL = os.getenv("TEXT_MODEL", "qwen-plus")

# AI_MOCK: "true" 强制 mock；"false" 强制真实 API；"auto" 无 key 时自动 mock
_mock_env = os.getenv("AI_MOCK", "auto").lower()
if _mock_env == "true":
    AI_MOCK = True
elif _mock_env == "false":
    AI_MOCK = False
else:
    AI_MOCK = not bool(AI_API_KEY)

DEFAULT_CITY = os.getenv("DEFAULT_CITY", "北京")
