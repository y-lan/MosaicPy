from abc import ABC, abstractmethod
from typing import Optional, Type
from pydantic import BaseModel, Field


class Tool(BaseModel, ABC):
    name: str
    description: str
    args_schema: Optional[Type[BaseModel]] = None

    @abstractmethod
    def _run(self, *args, **kwargs):
        pass


class CalculatorSchema(BaseModel):
    expr: str = Field(..., description="The expression to evaluate")


class CalculatorTool(Tool):
    name: str = "Calculator"
    description: str = "A simple calculator"
    args_schema: Type[BaseModel] = CalculatorSchema

    def _run(self, expr: str):
        import numexpr as ne
        result = ne.evaluate(expr)

        return result.item()
