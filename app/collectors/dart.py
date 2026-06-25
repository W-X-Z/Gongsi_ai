"""DART(금융감독원 전자공시) OpenAPI 수집기 — 실데이터.

문서: https://opendart.fss.or.kr  (공시정보 > 공시검색 list)
- 엔드포인트: https://opendart.fss.or.kr/api/list.json
- 인증키(crtfc_key) 필요
"""
from __future__ import annotations

import datetime as dt

import httpx

from ..models import Disclosure
from .base import BaseCollector

_BASE_URL = "https://opendart.fss.or.kr/api/list.json"


class DartCollector(BaseCollector):
    name = "dart"

    def __init__(
        self,
        api_key: str,
        lookback_days: int = 1,
        page_count: int = 100,
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.lookback_days = max(0, lookback_days)
        self.page_count = page_count
        self.timeout = timeout

    def collect(self) -> list[Disclosure]:
        end = dt.date.today()
        begin = end - dt.timedelta(days=self.lookback_days)
        params = {
            "crtfc_key": self.api_key,
            "bgn_de": begin.strftime("%Y%m%d"),
            "end_de": end.strftime("%Y%m%d"),
            "page_no": "1",
            "page_count": str(self.page_count),
            # pblntf_ty 미지정 = 전체 유형 수집 → 중요도 선별은 분석 단계에서 수행
        }

        resp = httpx.get(_BASE_URL, params=params, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status")
        if status == "013":  # 조회된 데이터 없음
            return []
        if status != "000":
            raise RuntimeError(f"DART API 오류 {status}: {data.get('message')}")

        out: list[Disclosure] = []
        for item in data.get("list", []):
            out.append(
                Disclosure(
                    corp_name=item.get("corp_name", "").strip(),
                    report_nm=item.get("report_nm", "").strip(),
                    rcept_no=item.get("rcept_no", "").strip(),
                    rcept_dt=item.get("rcept_dt", "").strip(),
                    stock_code=(item.get("stock_code") or "").strip() or None,
                    flr_nm=(item.get("flr_nm") or "").strip() or None,
                    source="DART",
                )
            )
        return out
