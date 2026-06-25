"""MTS 주요 공시 요약 프로토타입.

모듈 구성
- collectors : 공시 수집 (DART 실데이터 / 샘플 폴백)
- analyzers  : 룰 기반 1차 선별 + LLM 해석
- service    : 수집→선별→해석 오케스트레이션
- main       : FastAPI 앱 / 모바일 친화 UI 서빙
"""
