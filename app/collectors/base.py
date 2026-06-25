"""수집기 인터페이스."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Disclosure


class BaseCollector(ABC):
    name: str = "base"

    @abstractmethod
    def collect(self) -> list[Disclosure]:
        """최근 공시 목록을 수집해 반환한다."""
        raise NotImplementedError
