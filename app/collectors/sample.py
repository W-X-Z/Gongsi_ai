"""샘플 수집기 — DART 키/네트워크 없이도 데모가 돌도록 하는 폴백.

실제 DART 공시 유형을 반영한 가상의 데이터입니다.
"""
from __future__ import annotations

import datetime as dt

from ..models import Disclosure
from .base import BaseCollector

# (회사명, 종목코드, 보고서명, 제출인)
_SAMPLES = [
    ("삼성전자", "005930", "단일판매ㆍ공급계약체결", "삼성전자"),
    ("에코프로비엠", "247540", "유상증자결정", "에코프로비엠"),
    ("카카오", "035720", "주식등의대량보유상황보고서", "국민연금공단"),
    ("HLB", "028300", "투자판단관련주요경영사항(임상)", "HLB"),
    ("두산에너빌리티", "034020", "자기주식취득결정", "두산에너빌리티"),
    ("셀트리온", "068270", "무상증자결정", "셀트리온"),
    ("CJ제일제당", "097950", "현금ㆍ현물배당결정", "CJ제일제당"),
    ("코스모신소재", "005070", "전환사채권발행결정", "코스모신소재"),
    ("위메이드", "112040", "횡령ㆍ배임혐의발생", "위메이드"),
    ("LG화학", "051910", "기업설명회(IR)개최(안내공시)", "LG화학"),
    ("네이버", "035420", "분기보고서", "네이버"),
    ("한미반도체", "042700", "신규시설투자등", "한미반도체"),
    ("신라젠", "215600", "감사보고서제출", "삼정회계법인"),
    ("대한항공", "003490", "소송등의제기ㆍ신청", "대한항공"),
]


class SampleCollector(BaseCollector):
    name = "sample"

    def collect(self) -> list[Disclosure]:
        today = dt.date.today().strftime("%Y%m%d")
        out: list[Disclosure] = []
        for i, (corp, code, report, flr) in enumerate(_SAMPLES):
            out.append(
                Disclosure(
                    corp_name=corp,
                    report_nm=report,
                    rcept_no=f"SAMPLE{today}{i:04d}",
                    rcept_dt=today,
                    stock_code=code,
                    flr_nm=flr,
                    source="SAMPLE",
                )
            )
        return out
