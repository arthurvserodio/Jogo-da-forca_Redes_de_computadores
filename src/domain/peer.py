from ipaddress import IPv4Address, IPv6Address

from pydantic import BaseModel, ConfigDict, Field


class PeerAddress(BaseModel):
    model_config = ConfigDict(strict=True, validate_default=True)

    ip: IPv4Address | IPv6Address
    port: int = Field(strict=True, ge=1, le=65535)


class Peer(BaseModel):
    model_config = ConfigDict(strict=True, validate_default=True)

    name: str = Field(frozen=True)
    namespace: str = Field(frozen=True)

    address: PeerAddress

    @property
    def peer_id(self) -> str:
        return f"{self.name}@{self.namespace}"
