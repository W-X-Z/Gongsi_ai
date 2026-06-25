"""DART 상세 공시(주요사항보고서 주요정보) 보강 유틸.

list 응답의 `corp_code`로 유형별 상세 엔드포인트를 호출하면 금액 등 구조화 값이 나온다.
이 모듈은 두 가지를 제공한다.
  (1) detail_url()      : 유형별 상세 엔드포인트 URL 빌더
  (2) extract()         : 상세 JSON의 list 항목 → 보강 필드(metric/amount/fields)

이 환경에선 DART egress가 막혀 직접 호출은 못 하지만, 붙여넣은 상세 JSON을
extract()에 통과시키면 동일하게 금액을 뽑아 카드(metric/headline)에 채울 수 있다.
나중에 키가 있는 로컬에서 fetch를 붙이면 그대로 자동화된다.
"""
from __future__ import annotations

BASE = "https://opendart.fss.or.kr/api"

# 공시명 포함 키워드 → (상세 엔드포인트, 추출기 키)
#   ※ 거래소 수시공시(단일판매·공급계약, 현금배당, 타법인취득 등)는 구조화 상세 API가 없어
#     여기 없음 → 원문(document.xml) 파싱 또는 수치 직접 입력 필요.
DETAIL_MAP: dict[str, tuple[str, str]] = {
    "자기주식취득신탁계약체결결정": ("tsstkAqTrctrCnclsDecsn", "tsstk_trust"),
    "자기주식취득결정": ("tsstkAqDecsn", "tsstk_aq"),
    "자기주식처분결정": ("tsstkDpDecsn", "tsstk_dp"),
    "유상증자결정": ("piicDecsn", "rights_issue"),
    "전환사채": ("cvbdIsDecsn", "cb_issue"),
    "감자결정": ("crDecsn", "capital_reduction"),
}


def detail_url(endpoint: str, corp_code: str, bgn_de: str, end_de: str,
               key: str = "발급키") -> str:
    return (f"{BASE}/{endpoint}.json?crtfc_key={key}"
            f"&corp_code={corp_code}&bgn_de={bgn_de}&end_de={end_de}")


def lookup(report_nm: str) -> tuple[str, str] | None:
    """공시명으로 (엔드포인트, 추출기 키)를 찾는다."""
    for kw, ep in DETAIL_MAP.items():
        if kw in report_nm:
            return ep
    return None


# ── 금액 포맷 ────────────────────────────────────────────
def fmt_won(value) -> str | None:
    """원 단위 문자열/숫자 → '125억', '5,000만' 같은 한글 표기."""
    s = str(value).replace(",", "").strip()
    if not s or s in {"-", "0"}:
        return None
    try:
        n = int(float(s))
    except ValueError:
        return None
    if n <= 0:
        return None
    조, 억, 만 = 10**12, 10**8, 10**4
    if n >= 조:
        v = n / 조
        return f"{v:.1f}조".replace(".0조", "조")
    if n >= 억:
        v = n / 억
        return f"{v:,.0f}억" if v == int(v) else f"{v:,.1f}억"
    if n >= 만:
        return f"{n // 만:,}만"
    return f"{n:,}원"


def _amount(item: dict, keys: list[str]) -> str | None:
    for k in keys:
        v = item.get(k)
        if v not in (None, "", "-"):
            return fmt_won(v)
    return None


# ── 유형별 추출기: 상세 list 항목 dict → 보강 필드 ──────────
def tsstk_aq(it: dict) -> dict:
    won = _amount(it, ["aqpln_prc_ostk", "aqpln_prc_estk"])
    return {
        "metric": f"자사주취득 {won}" if won else "자사주 취득",
        "amount": won,
        "fields": {"방법": it.get("aq_mth"), "기간": it.get("aqexpd_bgd")},
    }


def tsstk_trust(it: dict) -> dict:
    won = _amount(it, ["ctr_prc"])
    return {
        "metric": f"자사주신탁 {won}" if won else "자사주 신탁",
        "amount": won,
        "fields": {"계약기간": it.get("ctr_pd_bgd"), "중개사": it.get("cs_iv_bk")},
    }


def tsstk_dp(it: dict) -> dict:
    won = _amount(it, ["dppln_prc_ostk", "dppln_prc_estk"])
    return {"metric": f"자사주처분 {won}" if won else "자사주 처분", "amount": won}


def rights_issue(it: dict) -> dict:
    # 유상증자는 단일 '총액' 필드가 없어 자금조달목적 합으로 추정
    keys = ["fdpp_fclt", "fdpp_bsninh", "fdpp_op", "fdpp_dtrp", "fdpp_ocsa", "fdpp_etc"]
    total = 0
    for k in keys:
        try:
            total += int(str(it.get(k, "0")).replace(",", "") or 0)
        except ValueError:
            pass
    won = fmt_won(total)
    return {"metric": f"유상증자 {won}" if won else "유상증자", "amount": won,
            "fields": {"증자방식": it.get("ic_mthn")}}


def cb_issue(it: dict) -> dict:
    won = _amount(it, ["bd_fta"])
    return {"metric": f"CB발행 {won}" if won else "전환사채 발행", "amount": won}


def capital_reduction(it: dict) -> dict:
    return {"metric": "감자", "amount": None, "fields": {"감자비율": it.get("cr_rt")}}


_EXTRACTORS = {
    "tsstk_aq": tsstk_aq, "tsstk_trust": tsstk_trust, "tsstk_dp": tsstk_dp,
    "rights_issue": rights_issue, "cb_issue": cb_issue,
    "capital_reduction": capital_reduction,
}


def extract(report_nm: str, detail_item: dict) -> dict | None:
    """공시명 + 상세 list 항목 → 보강 필드. 매핑 없으면 None."""
    ep = lookup(report_nm)
    if not ep:
        return None
    return _EXTRACTORS[ep[1]](detail_item)


if __name__ == "__main__":  # 자체 점검
    print(fmt_won("12,500,000,000"))  # 125억
    print(fmt_won("50,000,000"))       # 5,000만
    print(extract("주요사항보고서(자기주식취득결정)",
                  {"aqpln_prc_ostk": "10,000,000,000", "aq_mth": "장내매수"}))
    print(extract("주요사항보고서(자기주식취득신탁계약체결결정)",
                  {"ctr_prc": "5,000,000,000", "cs_iv_bk": "미래에셋증권"}))
