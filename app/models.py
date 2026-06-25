"""도메인 모델.

의존성을 가볍게 유지하기 위해 dataclass를 사용합니다.
FastAPI에는 to_dict()로 직렬화해 반환합니다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# 중요도 점수 → 라벨
IMPORTANCE_LABELS = {1: "낮음", 2: "보통", 3: "높음"}

# 감성(투자 영향) 분류
SENTIMENTS = ("호재", "악재", "중립")


@dataclass
class Disclosure:
    """수집된 원천 공시 1건."""

    corp_name: str           # 회사명
    report_nm: str           # 공시(보고서)명
    rcept_no: str            # 접수번호 (DART 문서 고유키)
    rcept_dt: str            # 접수일자 YYYYMMDD
    stock_code: str | None = None   # 종목코드
    flr_nm: str | None = None       # 공시 제출인
    source: str = "DART"

    @property
    def url(self) -> str:
        """DART 원문 링크."""
        return f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={self.rcept_no}"

    def to_dict(self) -> dict:
        return {
            "corp_name": self.corp_name,
            "report_nm": self.report_nm,
            "rcept_no": self.rcept_no,
            "rcept_dt": self.rcept_dt,
            "stock_code": self.stock_code,
            "flr_nm": self.flr_nm,
            "source": self.source,
            "url": self.url,
        }


@dataclass
class Analysis:
    """공시 1건에 대한 분석 결과 (모바일 카드에 그대로 노출)."""

    importance: int                       # 1~3
    sentiment: str                        # 호재/악재/중립
    headline: str                         # 한 줄 요약 (간결)
    actions: list[str] = field(default_factory=list)  # 후속 액션 안내
    tags: list[str] = field(default_factory=list)      # 분류 태그
    engine: str = "rules"                 # rules / llm

    @property
    def importance_label(self) -> str:
        return IMPORTANCE_LABELS.get(self.importance, "보통")

    def to_dict(self) -> dict:
        return {
            "importance": self.importance,
            "importance_label": self.importance_label,
            "sentiment": self.sentiment,
            "headline": self.headline,
            "actions": self.actions,
            "tags": self.tags,
            "engine": self.engine,
        }


@dataclass
class AnalyzedDisclosure:
    """공시 + 분석 결과 묶음."""

    disclosure: Disclosure
    analysis: Analysis

    def to_dict(self) -> dict:
        return {**self.disclosure.to_dict(), "analysis": self.analysis.to_dict()}
