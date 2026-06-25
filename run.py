"""로컬 실행 진입점.

    python run.py
    # 또는
    uvicorn app.main:app --reload
"""
from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=bool(os.getenv("RELOAD", "1") == "1"),
    )
