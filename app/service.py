"""오케스트레이션: 수집 → 룰 1차 선별 → LLM 해석 → 정렬.

파이프라인을 한곳에 모아 두어, 단계별로 교체/수정하기 쉽게 했습니다.
"""
from __future__ import annotations

import asyncio

from .analyzers import RuleScorer, build_interpreter
from .analyzers.base import BaseInterpreter, RuleResult
from .collectors import build_collector
from .collectors.base import BaseCollector
from .config import settings
from .models import AnalyzedDisclosure, Disclosure


class DisclosureService:
    def __init__(
        self,
        collector: BaseCollector | None = None,
        scorer: RuleScorer | None = None,
        interpreter: BaseInterpreter | None = None,
    ) -> None:
        self.collector = collector or build_collector()
        self.scorer = scorer or RuleScorer()
        # interpreter는 None일 수 있음(룰 폴백). 명시 인자가 없으면 설정대로 생성.
        self.interpreter = interpreter if interpreter is not None else build_interpreter()

    @property
    def engine_name(self) -> str:
        return "llm" if self.interpreter else "rules"

    async def feed(
        self,
        limit: int | None = None,
        min_importance: int | None = None,
    ) -> list[AnalyzedDisclosure]:
        limit = limit or settings.feed_limit
        min_importance = (
            settings.min_importance if min_importance is None else min_importance
        )

        # 1) 수집
        items = self.collector.collect()

        # 2) 룰 기반 1차 선별 (중요도 점수화 → 임계값 이상만 통과)
        scored: list[tuple[Disclosure, RuleResult]] = [
            (d, self.scorer.score(d)) for d in items
        ]
        selected = [(d, r) for d, r in scored if r.importance >= min_importance]

        # 중요도 → 최신 → 접수번호 순으로 정렬 후 상위 N건
        selected.sort(
            key=lambda x: (x[1].importance, x[0].rcept_dt, x[0].rcept_no),
            reverse=True,
        )
        selected = selected[:limit]

        # 3) 해석 (LLM 동시 호출, 실패 시 건별 룰 폴백)
        analyses = await asyncio.gather(
            *(self._interpret(d, r) for d, r in selected)
        )

        return [
            AnalyzedDisclosure(disclosure=d, analysis=a)
            for (d, _), a in zip(selected, analyses)
        ]

    async def _interpret(self, disclosure: Disclosure, rule: RuleResult):
        if self.interpreter is not None:
            try:
                return await self.interpreter.interpret(disclosure, rule)
            except Exception:
                pass  # 한 건 실패가 전체를 막지 않도록 룰로 폴백
        return rule.to_analysis(engine="rules")


# FastAPI에서 공유할 단일 인스턴스
service = DisclosureService()
