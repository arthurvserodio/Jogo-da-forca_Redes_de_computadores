from typing import TypedDict


class ConfigJogo(TypedDict):
    rdv_host: str
    rdv_port: int
    namespace: str
    name: str
    listen_port: int
    register_ttl: int
    discover_interval: int
    ping_interval: int
    ping_miss_limit: int
    max_reconnect_attempts: int
    base_backoff: int
    max_backoff: int
    lives: int
    max_players: int
    turn_timeout: int
    words_file: str
    log_file: str | None
