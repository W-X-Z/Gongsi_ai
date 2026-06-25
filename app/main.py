"""FastAPI 앱 — 공시 피드 API + 모바일 친화 UI 서빙."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse

from .config import settings
from .service import service

app = FastAPI(title="MTS 공시 요약", version="0.1.0")

_STATIC = Path(__file__).parent / "static"


@app.get("/api/health")
def health() -> dict:
    """현재 동작 모드 점검용."""
    return {
        "status": "ok",
        "collector": settings.collector_kind,   # dart / sample
        "analyzer": service.engine_name,        # llm / rules
        "model": settings.model if service.engine_name == "llm" else None,
    }


@app.get("/api/feed")
async def feed(
    limit: int | None = Query(default=None, ge=1, le=100),
    min_importance: int | None = Query(default=None, ge=1, le=3),
) -> JSONResponse:
    """분석된 주요 공시 피드."""
    items = await service.feed(limit=limit, min_importance=min_importance)
    return JSONResponse(
        {
            "meta": {
                "count": len(items),
                "collector": settings.collector_kind,
                "analyzer": service.engine_name,
            },
            "items": [i.to_dict() for i in items],
        }
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")
