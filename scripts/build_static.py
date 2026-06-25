"""정적 배포용 스냅샷 빌더.

수집 + 분석 파이프라인을 '한 번' 실행해 결과를 정적 파일로 굳힙니다.
산출물(site/)은 서버 없이 GitHub Pages 등으로 호스팅할 수 있습니다.

    python scripts/build_static.py              # index.html + feed.json 생성
    python scripts/build_static.py --keep-feed  # index.html만 갱신(feed.json 보존)

ANTHROPIC_API_KEY가 있으면 llm.py 파이프라인으로 AI 해석을 생성하고,
없으면 룰 해석으로 폴백합니다(meta.analyzer 로 확인).
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.service import DisclosureService  # noqa: E402

SITE = ROOT / "site"
SRC_HTML = ROOT / "app" / "static" / "index.html"
_INJECT = '</title>\n<script>window.__FEED_URL__="./feed.json";</script>'


def build_index() -> None:
    SITE.mkdir(exist_ok=True)
    html = SRC_HTML.read_text(encoding="utf-8")
    # 동적 UI를 정적 스냅샷(./feed.json)을 읽도록 변환
    html = html.replace("</title>", _INJECT, 1)
    (SITE / "index.html").write_text(html, encoding="utf-8")
    print("✓ site/index.html")


def build_feed() -> None:
    svc = DisclosureService()
    items = asyncio.run(svc.feed(min_importance=1, limit=200))
    payload = {
        "meta": {
            "count": len(items),
            "collector": svc.collector.name,
            "analyzer": svc.engine_name,
            "generated_at": dt.date.today().isoformat(),
        },
        "items": [i.to_dict() for i in items],
    }
    (SITE / "feed.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"✓ site/feed.json ({len(items)}건, analyzer={svc.engine_name})")
    if svc.engine_name != "llm":
        print("  ⚠ ANTHROPIC_API_KEY 없이 생성 → 룰 해석. AI 해석은 키 설정 후 재실행하세요.")


def main() -> None:
    build_index()
    if "--keep-feed" in sys.argv:
        print("· feed.json 보존(재생성 생략)")
    else:
        build_feed()


if __name__ == "__main__":
    main()
