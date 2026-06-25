"""분석 모듈: 룰 기반 1차 선별 + (선택) LLM 해석."""
from __future__ import annotations

from ..config import settings
from .base import BaseInterpreter, RuleResult
from .rules import RuleScorer


def build_interpreter() -> BaseInterpreter | None:
    """LLM 해석기를 생성한다. 사용 불가하면 None (룰 폴백)."""
    if not settings.llm_enabled or not settings.anthropic_api_key:
        return None
    try:
        from .llm import LLMInterpreter

        return LLMInterpreter(
            api_key=settings.anthropic_api_key,
            model=settings.model,
        )
    except Exception:  # anthropic 미설치 등
        return None


__all__ = ["BaseInterpreter", "RuleResult", "RuleScorer", "build_interpreter"]
