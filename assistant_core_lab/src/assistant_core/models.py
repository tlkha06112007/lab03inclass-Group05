from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Intent(str, Enum):
    GREETING = "greeting"
    FEE = "fee"
    OFFICE = "office"
    RULE = "rule"
    UNKNOWN = "unknown"


class Message(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1, max_length=2000)
    session_id: str = "local"


class Source(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    title: str


class Response(BaseModel):
    model_config = ConfigDict(frozen=True)

    answer: str
    intent: Intent
    sources: list[Source] = Field(default_factory=list)
    degraded: bool = False
