"""분석기 인터페이스 + 룰 매칭 결과 모델."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..models import Analysis, Disclosure


@dataclass
class RuleResult:
    """공시 유형(룰) 기반 1차 선별 결과."""

    importance: int
    sentiment: str
    headline: str
    action: str
    tags: list[str] = field(default_factory=list)
    metric: str = ""
    matched: bool = False

    def to_analysis(self, engine: str = "rules") -> Analysis:
        """LLM 미사용 시, 룰 결과를 그대로 분석 결과로 변환."""
        return Analysis(
            importance=self.importance,
            sentiment=self.sentiment,
            headline=self.headline,
            metric=self.metric or (self.tags[0] if self.tags else ""),
            actions=[self.action],
            tags=list(self.tags),
            engine=engine,
        )


class BaseInterpreter(ABC):
    """공시 해석기(호재/악재/중립·요약·후속액션) 인터페이스."""

    @abstractmethod
    async def interpret(self, disclosure: Disclosure, rule: RuleResult) -> Analysis:
        raise NotImplementedError
