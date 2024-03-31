import unittest

from mosaicpy.llm import get_agent
from mosaicpy.llm.anthropic.agent import AnthropicAgent
from mosaicpy.llm.openai.agent import OpenAIAgent

from typing import Optional, Type

from pydantic import BaseModel, Field
from mosaicpy.llm.openai.function import build_function_signature

from mosaicpy.llm.openai.tools import Tool


class TestAgentBasic(unittest.TestCase):
    def test_init_agent(self):
        gpt_agent = get_agent("openai")
        self.assertIsInstance(gpt_agent, OpenAIAgent)

        claude_agent = get_agent("anthropic")
        self.assertIsInstance(claude_agent, AnthropicAgent)


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


class TestOpenAIAgent(unittest.TestCase):
    def test_basic(self):
        agent = OpenAIAgent(system_prompt="output the result only", return_all=True)
        result = agent.chat("1+2=")
        self.assertEqual(result, "3")


class TestAnthropicAgent(unittest.TestCase):
    def test_basic(self):
        agent = AnthropicAgent(system_prompt="output the result only", return_all=True)
        result = agent.chat("1+2=")
        self.assertEqual(result, "3")


if __name__ == "__main__":
    unittest.main()
