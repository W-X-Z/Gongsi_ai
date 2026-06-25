"""룰 기반 1차 선별기.

공시명(report_nm)을 키워드 테이블과 매칭해 중요도·감성·후속액션을 산출합니다.
이 결과로 '중요 공시'를 거른 뒤, 통과한 건만 LLM 해석으로 넘깁니다.
"""
from __future__ import annotations

from ..models import Disclosure
from .base import RuleResult
from .keywords import DEFAULT_RULE, RULES


class RuleScorer:
    """공시 → RuleResult."""

    def score(self, disclosure: Disclosure) -> RuleResult:
        name = disclosure.report_nm or ""

        matches = [r for r in RULES if any(k in name for k in r.keywords)]
        if matches:
            # 가장 중요도가 높은 규칙을 채택 (동률이면 먼저 정의된 것)
            rule = max(matches, key=lambda r: r.importance)
            return RuleResult(
                importance=rule.importance,
                sentiment=rule.sentiment,
                headline=rule.headline,
                action=rule.action,
                tags=list(rule.tags),
                matched=True,
            )

        return RuleResult(
            importance=DEFAULT_RULE.importance,
            sentiment=DEFAULT_RULE.sentiment,
            headline=DEFAULT_RULE.headline,
            action=DEFAULT_RULE.action,
            tags=list(DEFAULT_RULE.tags),
            matched=False,
        )
