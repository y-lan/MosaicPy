from typing import Optional
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import Function
from pydantic import BaseModel
from mosaicpy.llm.schema import Event

from mosaicpy.utils.event import SimpleEventManager


class ToolCallAggregator(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    arguments: Optional[str] = None

    def update(self, tool_call):
        if tool_call.id and not self.id:
            self.id = tool_call.id
        if tool_call.type and not self.type:
            self.type = tool_call.type

        func = tool_call.function

        if func.name:
            if not self.name:
                self.name = func.name
            else:
                self.name += func.name

        if func.arguments:
            if not self.arguments:
                self.arguments = func.arguments
            else:
                self.arguments += func.arguments

    def to_tool_call(self):
        return ChatCompletionMessageToolCall(
            id=self.id,
            function=Function(
                arguments=self.arguments,
                name=self.name
            ),
            type=self.type
        )


class ChoiceAggregator(BaseModel):
    event_manger: Optional[SimpleEventManager] = None
    content: Optional[str] = None
    role: Optional[int] = None
    finish_reason: Optional[str] = None
    tool_calls: Optional[ToolCallAggregator] = None

    class Config:
        arbitrary_types_allowed = True

    def update(self, choice):
        if choice.finish_reason and not self.finish_reason:
            self.finish_reason = choice.finish_reason
        elif hasattr(choice, 'finish_details') and choice.finish_details and not self.finish_reason:
            self.finish_reason = choice.finish_details['type']

        delta = choice.delta
        if delta.content:
            if not self.content:
                self.content = delta.content
            else:
                self.content += delta.content

            if self.event_manger:
                self.event_manger.publish(
                    Event.NEW_CHAT_TOKEN,
                    content=delta.content)
        if delta.role and not self.role:
            self.role = delta.role
        if delta.tool_calls:
            if not self.tool_calls:
                self.tool_calls = []

            for i, tool_call in enumerate(delta.tool_calls):
                if i >= len(self.tool_calls):
                    self.tool_calls.append(ToolCallAggregator())

                self.tool_calls[i].update(tool_call)

    def to_choice(self):
        return Choice(
            index=0,
            finish_reason=self.finish_reason,
            message=ChatCompletionMessage(
                content=self.content,
                role=self.role,
                tool_calls=[tool_call.to_tool_call(
                ) for tool_call in self.tool_calls] if self.tool_calls else None,
            )
        )


class ChunkAggregator(BaseModel):
    event_manger: SimpleEventManager = None
    id: Optional[str] = None
    created: Optional[int] = None
    model: Optional[str] = None
    choices: Optional[ChoiceAggregator] = None
    chunk_cnt: int = 0

    class Config:
        arbitrary_types_allowed = True

    def update(self, chunk):
        if chunk.id and not self.id:
            self.id = chunk.id
        if chunk.model and not self.model:
            self.model = chunk.model
        if chunk.created and not self.created:
            self.created = chunk.created

        if chunk.choices:
            if not self.choices:
                self.choices = []

            for i, choice in enumerate(chunk.choices):
                if i >= len(self.choices):
                    self.choices.append(
                        ChoiceAggregator(
                            # only emit event for the first choice
                            event_manger=self.event_manger if i == 0 else None)
                    )

                self.choices[i].update(choice)

        self.chunk_cnt += 1

    def to_chat_completion(self):
        return ChatCompletion(
            id=self.id,
            created=self.created,
            model=self.model,
            choices=[choice.to_choice() for choice in self.choices],
            object="chat.completion"
        )
