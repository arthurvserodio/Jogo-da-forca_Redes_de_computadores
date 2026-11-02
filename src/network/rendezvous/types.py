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
