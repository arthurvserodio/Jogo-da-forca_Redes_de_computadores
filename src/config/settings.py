from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Port = Annotated[int, Field(ge=1, le=65535)]
PositiveInt = Annotated[int, Field(ge=1)]
NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Settings(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", validate_default=True)

    rdv_host: NonEmptyString
    rdv_port: Port

    namespace: NonEmptyString
    name: NonEmptyString

    listen_port: Port
    register_ttl: PositiveInt
    discover_interval: PositiveInt
    ping_interval: PositiveInt
    ping_miss_limit: PositiveInt
    max_reconnect_attempts: PositiveInt
    base_backoff: PositiveInt
    max_backoff: PositiveInt
    lives: PositiveInt
    max_players: PositiveInt
    turn_timeout: PositiveInt
    words_file: NonEmptyString
    log_file: NonEmptyString | None = None

    @property
    def peer_id(self) -> str:
        return f"{self.name}@{self.namespace}"
