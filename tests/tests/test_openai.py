from typing import Optional, Type
import unittest

from pydantic import BaseModel, Field
from mosaicpy.llm.openai.function import build_function_signature

from mosaicpy.llm.openai.tools import Tool


class TestOpenAIFunctions(unittest.TestCase):
    def test_build_function_signature(self):
        class TestSchema(BaseModel):
            a: int = Field(..., description="param a")
            b: Optional[str] = Field("test", description="param b")

        class TestTool(Tool):
            name: str = "test"
            description: str = "test"
            args_schema: Type[BaseModel] = TestSchema

            def _run(self, a: int, b: str):
                pass

        signature = build_function_signature(TestTool())

        print(signature)

        expected_signature = {
            "type": "function",
            "function": {
                "name": "test",
                "description": "test",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"title": "A", "description": "param a", "type": "integer"},
                        "b": {
                            "title": "B",
                            "description": "param b",
                            "default": "test",
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                        },
                    },
                    "required": ["a"],
                },
            },
        }
        self.assertDictEqual(signature, expected_signature)


if __name__ == "__main__":
    unittest.main()
