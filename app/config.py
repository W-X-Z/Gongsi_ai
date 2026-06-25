"""환경설정. 값은 모두 .env / 환경변수로 덮어쓸 수 있습니다."""
from __future__ import annotations

import os
from dataclasses import dataclass

try:  # .env 자동 로딩 (없어도 동작)
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


def _clean(v: str | None) -> str | None:
    v = (v or "").strip()
    return v or None


@dataclass(frozen=True)
class Settings:
    # 수집
    dart_api_key: str | None = _clean(os.getenv("DART_API_KEY"))
    lookback_days: int = int(os.getenv("LOOKBACK_DAYS", "1") or 1)

    # 분석
    feed_limit: int = int(os.getenv("FEED_LIMIT", "20") or 20)
    min_importance: int = int(os.getenv("MIN_IMPORTANCE", "2") or 2)

    # LLM 해석
    anthropic_api_key: str | None = _clean(os.getenv("ANTHROPIC_API_KEY"))
    model: str = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8") or "claude-opus-4-8"
    use_llm: str = (os.getenv("USE_LLM", "auto") or "auto").lower()

    @property
    def collector_kind(self) -> str:
        return "dart" if self.dart_api_key else "sample"

    @property
    def llm_enabled(self) -> bool:
        if self.use_llm == "off":
            return False
        if self.use_llm == "on":
            return True
        return bool(self.anthropic_api_key)  # auto


settings = Settings()
