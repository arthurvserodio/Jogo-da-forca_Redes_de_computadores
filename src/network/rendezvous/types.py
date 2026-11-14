"""Contratos estáticos; casts em JSON não substituem validação do protocolo."""

from typing import TypedDict


class Config(TypedDict):
    rdv_host: str
    rdv_port: int
    namespace: str
    name: str
    listen_port: int
    register_ttl: int


class Peer(TypedDict):
    name: str
    namespace: str


class Response(TypedDict, total=False):
    status: str
    ttl: int
    peers: list[Peer]

class ResponseRegisterOK(TypedDict):
    status: str
    ttl: int
    ip: str
    port: int

class ResponseRegisterError(TypedDict):
    status: str
    message: str

class ResponseDiscoverOk(TypedDict):
    status: str
    peers: list[Peer]

class ResponseDiscoverError(TypedDict):
    status: str
    message: str

class ResponseUnregisterOk(TypedDict):
    status: str

class ResponseUnregisterError(TypedDict):
    status: str
    message: str

ResponseServer = (
    ResponseRegisterOK
    | ResponseRegisterError
    | ResponseDiscoverOk
    | ResponseDiscoverError
    | ResponseUnregisterOk
    | ResponseUnregisterError
)