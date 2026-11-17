import logging
import time
import uuid
from collections import deque
from datetime import UTC, datetime
from typing import TypedDict

logger = logging.getLogger("KeepAlive")


class PingPongMessage(TypedDict):
    type: str
    msg_id: str
    timestamp: str
    ttl: int


class PeerStats:
    def __init__(self, ping_miss_limit: int = 3) -> None:
        if ping_miss_limit < 1:
            raise ValueError("ping_miss_limit deve ser >= 1")
        self.rtt_history: deque[float] = deque(maxlen=10)
        self.missed_pings = 0
        self.ping_miss_limit = ping_miss_limit
        self.is_stale = False
        self.pending_pings: dict[str, tuple[float, str]] = {}

    def create_ping(self) -> PingPongMessage:
        msg_id = str(uuid.uuid4())
        # Formato de data ISO 8601 UTC terminado em Z
        timestamp_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        self.pending_pings[msg_id] = (time.monotonic(), timestamp_iso)
        return {
            "type": "PING",
            "msg_id": msg_id,
            "timestamp": timestamp_iso,
            "ttl": 1,
        }

    def create_pong(self, ping_msg_id: str, ping_timestamp: str) -> PingPongMessage:
        # PONG repete o msg_id e o timestamp do PING recebido
        return {"type": "PONG", "msg_id": ping_msg_id, "timestamp": ping_timestamp, "ttl": 1}

    def process_pong(self, ping_msg_id: str, ping_timestamp_iso: str) -> bool:
        pendente = self.pending_pings.get(ping_msg_id)
        if pendente is None:
            logger.debug("PONG desconhecido, repetido ou atrasado: %s", ping_msg_id)
            return False
        enviado_em, timestamp_original = pendente
        if ping_timestamp_iso != timestamp_original:
            logger.warning("Timestamp divergente no PONG %s", ping_msg_id)
            return False
        del self.pending_pings[ping_msg_id]
        rtt_ms = (time.monotonic() - enviado_em) * 1000.0
        self.rtt_history.append(rtt_ms)
        self.missed_pings = 0
        self.is_stale = False
        logger.debug("RTT=%.1f ms (média %.1f ms)", rtt_ms, self.get_avg_rtt())
        return True

    def check_timeouts(self, timeout_seconds: float) -> int:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds deve ser > 0")

        agora = time.monotonic()
        expirados = [
            msg_id
            for msg_id, (enviado_em, _) in self.pending_pings.items()
            if agora - enviado_em >= timeout_seconds
        ]
        for msg_id in expirados:
            del self.pending_pings[msg_id]

        if expirados:
            self.missed_pings += len(expirados)
            if not self.is_stale and self.missed_pings >= self.ping_miss_limit:
                self.is_stale = True
                logger.warning("%d PINGs sem resposta — peer STALE", self.missed_pings)
        return len(expirados)

    def get_avg_rtt(self) -> float:
        if not self.rtt_history:
            return 0.0
        return sum(self.rtt_history) / len(self.rtt_history)
