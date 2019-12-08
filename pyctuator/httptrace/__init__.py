from dataclasses import dataclass
from datetime import datetime
from typing import List, Mapping, Optional


@dataclass
class TraceResponse:
    status: int
    headers: Mapping[str, List[str]]


@dataclass
class TraceRequest:
    method: str
    uri: str
    headers: Mapping[str, List[str]]


@dataclass
class Session:
    id: str


@dataclass
class Principal:
    name: str


@dataclass
class TraceRecord:
    timestamp: datetime
    principal: Optional[Principal]
    session: Optional[Session]
    request: TraceRequest
    response: TraceResponse
    timeTaken: int


@dataclass
class Traces:
    traces: List[TraceRecord]
