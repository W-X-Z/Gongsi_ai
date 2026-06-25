"""LLM(Claude) 기반 공시 해석기.

룰 기반으로 1차 선별된 '중요 공시'에 대해
호재/악재/중립 판별 · 한 줄 요약 · 후속 액션을 생성합니다.

- 모바일 친화: 짧고 핵심만. headline은 한 문장, action은 1~2개.
- 키가 없거나 호출이 실패하면 service에서 룰 결과로 자동 폴백합니다.
"""
from __future__ import annotations

from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from ..models import SENTIMENTS, Analysis, Disclosure
from .base import BaseInterpreter, RuleResult

_SYSTEM = (
    "당신은 한국 주식 MTS의 공시 분석 어시스턴트입니다. "
    "개별 공시를 모바일 사용자에게 아주 간결하게 전달합니다. "
    "과장 없이 사실 기반으로, 투자 권유 표현은 피하고 정보 제공에 집중하세요."
)

_INSTRUCTION = """다음 공시를 분석해 JSON으로만 답하세요.

[회사] {corp}
[공시명] {report}
[참고: 유형 기반 1차 판단] 중요도={imp}, 성향={sent}

규칙:
- sentiment: "호재" / "악재" / "중립" 중 하나. 주가에 미칠 단기 영향 기준.
- headline: 핵심 키워드를 앞세운 한 문장(40자 이내, 군더더기 없이).
  · 공시명만 보고 단정 말 것. 예: '만기 전 사채취득'은 발행이 아니라 회수,
    '유상증자 철회'는 증자가 아님. 실제 사건의 방향을 정확히 반영하세요.
- metric: 제목 위에 띄울 핵심 키워드 칩 1개(12자 이내). 금액이 확실하면 숫자 포함,
  불확실하면 사건 키워드만(예: "유상증자 철회", "CB 조기상환", "중간배당", "자사주 취득").
  ※ 금액·비율을 추측해 지어내지 말 것.
- actions: 투자자가 추가로 확인할 정보 1~2개. 각 항목 35자 이내, 동작 지시형.
- 모바일 화면이므로 절대 길게 쓰지 마세요."""


class _Verdict(BaseModel):
    sentiment: str = Field(description="호재/악재/중립")
    headline: str = Field(description="키워드를 앞세운 한 줄 요약 (40자 이내)")
    metric: str = Field(description="핵심 키워드/수치 칩 (12자 이내)")
    actions: list[str] = Field(description="후속 액션 1~2개", min_length=1, max_length=3)


class LLMInterpreter(BaseInterpreter):
    def __init__(self, api_key: str, model: str) -> None:
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def interpret(self, disclosure: Disclosure, rule: RuleResult) -> Analysis:
        prompt = _INSTRUCTION.format(
            corp=disclosure.corp_name,
            report=disclosure.report_nm,
            imp=rule.importance,
            sent=rule.sentiment,
        )

        resp = await self.client.messages.parse(
            model=self.model,
            max_tokens=1024,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_format=_Verdict,
        )
        v = resp.parsed_output
        if v is None:  # 파싱 실패 → 룰 폴백
            return rule.to_analysis(engine="rules")

        sentiment = v.sentiment if v.sentiment in SENTIMENTS else rule.sentiment
        actions = [a.strip() for a in v.actions if a.strip()] or [rule.action]
        return Analysis(
            importance=rule.importance,  # 중요도는 룰 기반 선별값을 유지
            sentiment=sentiment,
            headline=v.headline.strip() or rule.headline,
            metric=(v.metric or "").strip() or (rule.tags[0] if rule.tags else ""),
            actions=actions[:2],
            tags=list(rule.tags),
            engine="llm",
        )
