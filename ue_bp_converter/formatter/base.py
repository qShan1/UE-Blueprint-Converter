from abc import ABC, abstractmethod

from ..transformer.models import TransformedGraph


class BaseFormatter(ABC):
    @abstractmethod
    def format(self, graph: TransformedGraph, include_stats: bool = False) -> str:
        pass