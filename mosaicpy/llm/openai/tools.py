from abc import ABC, abstractmethod
from pydantic import BaseModel


class Tool(BaseModel, ABC):
    name: str
    description: str

    @abstractmethod
    def _run(self, *args, **kwargs):
        pass


class CalculatorTool(Tool):
    name: str = "Calculator"
    description: str = "A simple calculator"

    def _run(self, expr: str):
        import numexpr as ne
        result = ne.evaluate(expr)

        return result.item()
