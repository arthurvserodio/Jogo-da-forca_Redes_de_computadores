import uuid
import logging
from datetime import datetime, timezone
from collections import deque

logger = logging.getLogger("KeepAlive")

class PeerStats:
    def __init__(self, ping_miss_limit=3):
        self.rtt_history = deque(maxlen=10)
        self.missed_pings = 0
        self.ping_miss_limit = ping_miss_limit
        self.is_stale = False

    def create_ping(self) -> dict:
        self.missed_pings += 1
        if self.missed_pings >= self.ping_miss_limit:
            self.is_stale = True
            logger.warning("Missed %d PINGs — marking STALE", self.missed_pings)
            
        # Formato de data ISO 8601 UTC terminado em Z
        timestamp_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            
        return {
            "type": "PING",
            "msg_id": str(uuid.uuid4()),
            "timestamp": timestamp_iso,
            "ttl": 1
        }

    def create_pong(self, ping_msg_id: str, ping_timestamp: str) -> dict:
        # PONG repete o msg_id e o timestamp do PING recebido
        return {
            "type": "PONG",
            "msg_id": ping_msg_id,
            "timestamp": ping_timestamp,
            "ttl": 1
        }

    def process_pong(self, ping_timestamp_iso: str):
        self.missed_pings = 0 
        
        try:
            # Converte o timestamp recebido de volta para calcular o RTT
            clean_timestamp = ping_timestamp_iso.replace("Z", "+00:00")
            ping_time = datetime.fromisoformat(clean_timestamp)
            now = datetime.now(timezone.utc)
            
            rtt_ms = (now - ping_time).total_seconds() * 1000
            self.rtt_history.append(rtt_ms)
            logger.debug("RTT=%.1f ms (avg %.1f ms)", rtt_ms, self.get_avg_rtt())
            
        except ValueError as e:
            logger.error("Erro ao processar timestamp do PONG: %s", e)

    def get_avg_rtt(self) -> float:
        if not self.rtt_history:
            return 0.0
        return sum(self.rtt_history) / len(self.rtt_history)