"""공시 수집기.

새 소스를 추가하려면 BaseCollector를 상속해 collect()만 구현하면 됩니다.
"""
from __future__ import annotations

from ..config import settings
from .base import BaseCollector
from .dart import DartCollector
from .sample import SampleCollector


def build_collector() -> BaseCollector:
    """설정에 따라 적절한 수집기를 생성한다 (DART 키 있으면 실데이터)."""
    if settings.collector_kind == "dart":
        return DartCollector(
            api_key=settings.dart_api_key,  # type: ignore[arg-type]
            lookback_days=settings.lookback_days,
        )
    return SampleCollector()


__all__ = ["BaseCollector", "DartCollector", "SampleCollector", "build_collector"]
