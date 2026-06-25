# MTS 주요 공시 요약 (MVP)

MTS 고객에게 **주요 공시를 수집·해석해 모바일에서 핵심만** 보여주는 프로토타입.

- **수집**: DART(전자공시) OpenAPI 실데이터 — 키가 없으면 샘플 데이터로 자동 동작
- **1차 선별(룰)**: 공시 *유형* 기반으로 중요도를 점수화해 중요 공시만 통과
- **해석(LLM)**: Claude가 **호재/악재/중립 · 한 줄 요약 · 후속 액션**을 생성 — 키가 없으면 룰 해석으로 폴백
- **UI**: 모바일 친화 카드 피드. 텍스트는 핵심만, 후속 액션은 탭하면 펼쳐보기

분석 파이프라인은 사용자가 의도한 대로 **"유형 기반 룰로 1차 선별 → LLM으로 해석"** 구조입니다.

---

## 빠른 시작

```bash
pip install -r requirements.txt
cp .env.example .env        # (선택) 키 입력
python run.py               # http://localhost:8000
```

키를 하나도 넣지 않아도 **샘플 데이터 + 룰 해석**으로 바로 화면이 뜹니다.

### 실데이터 / AI 해석 켜기

`.env`에 키를 채우면 자동 전환됩니다.

| 변수 | 효과 |
|---|---|
| `DART_API_KEY` | DART 실시간 공시 수집 (발급: https://opendart.fss.or.kr) |
| `ANTHROPIC_API_KEY` | Claude 기반 AI 해석 활성화 |
| `LOOKBACK_DAYS` | 조회 기간(일). 주말엔 3~5 권장 |
| `MIN_IMPORTANCE` | 1차 선별 임계값 (1/2/3) |

현재 동작 모드는 `GET /api/health`로 확인할 수 있습니다.

---

## 구조 (모듈 분리 — 수정·교체 용이)

```
app/
├── collectors/          # 공시 수집
│   ├── base.py          #   인터페이스
│   ├── dart.py          #   DART 실데이터
│   └── sample.py        #   샘플 폴백
├── analyzers/           # 분석
│   ├── keywords.py      #   ⭐ 유형 키워드/중요도/액션 테이블 (정책 수정 지점)
│   ├── rules.py         #   룰 기반 1차 선별
│   ├── llm.py           #   Claude 해석 (호재/악재/중립·요약·액션)
│   └── base.py          #   인터페이스 + 룰 결과 모델
├── service.py           # 수집→선별→해석 오케스트레이션
├── models.py            # 도메인 모델
├── main.py              # FastAPI (API + UI 서빙)
└── static/index.html    # 모바일 친화 UI
```

### 자주 바꾸는 곳
- **공시 분류/중요도/후속 액션 정책** → `app/analyzers/keywords.py` 의 `RULES`
- **LLM 프롬프트/출력 형식** → `app/analyzers/llm.py`
- **새 수집 소스 추가** → `collectors/base.py` 상속 후 `collectors/__init__.py`에 연결
- **UI 톤/문구/색상** → `app/static/index.html`

---

## 정적 배포 (GitHub Pages) — UI만 호스팅

서버 없이 **스냅샷**으로 호스팅합니다. 수집·LLM 해석을 한 번 실행해 `site/feed.json`으로 굳히고, `site/`(정적)만 게시합니다.

```bash
# 스냅샷 재생성 (키 있으면 AI 해석, 없으면 룰 해석)
python scripts/build_static.py
```

산출물
```
site/
├── index.html     # ./feed.json 을 읽는 정적 UI
└── feed.json      # 수집+해석 결과 스냅샷 (meta.analyzer 로 엔진 확인)
```

배포: `site/` 변경을 푸시하면 `.github/workflows/deploy-pages.yml`이 Pages로 게시합니다.
> ⚙️ **최초 1회만**: 저장소 **Settings → Pages → Source = "GitHub Actions"** 로 설정.
> 이후 발급되는 URL이 배포 주소입니다 (`https://<계정>.github.io/<repo>/`).

현재 커밋된 `site/feed.json`은 **Claude가 샘플 공시를 해석해 만든 콘텐츠**입니다.
DART/Anthropic 키를 넣고 `build_static.py`를 다시 돌리면 실데이터·AI 해석으로 교체됩니다.

### 피드백 루프
보시고 → **LLM 문구**는 `app/analyzers/llm.py`(프롬프트)·중요도/액션은 `keywords.py`,
**UI**는 `app/static/index.html`을 고친 뒤 `build_static.py` 재실행 → 재배포.

---

## API (동적 서버 모드)

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/` | 모바일 UI |
| `GET` | `/api/feed?min_importance=2&limit=20` | 분석된 공시 피드(JSON) |
| `GET` | `/api/health` | 동작 모드(수집기/분석기) |

응답 예 (`/api/feed`):

```json
{
  "meta": { "count": 7, "collector": "sample", "analyzer": "rules" },
  "items": [{
    "corp_name": "삼성전자", "stock_code": "005930",
    "report_nm": "단일판매ㆍ공급계약체결",
    "url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=...",
    "analysis": {
      "importance": 3, "importance_label": "높음",
      "sentiment": "호재", "headline": "대규모 공급계약 체결",
      "actions": ["계약 금액의 매출 대비 비중 확인", "계약 기간·상대방 확인"],
      "tags": ["실적", "수주"], "engine": "rules"
    }
  }]
}
```

---

## 메모 / 다음 단계
- 중요도 가중치를 **계약금액/매출 대비 비율** 등 정량 신호로 보강 (현재는 유형 기반)
- 종목 보유/관심 종목 기준 개인화 필터
- 공시 본문(첨부) 파싱으로 LLM 해석 정확도 향상
- 결과 캐싱(같은 공시 재해석 방지) 및 배치 처리
