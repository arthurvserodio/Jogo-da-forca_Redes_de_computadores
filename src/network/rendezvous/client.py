import json
from socket import AF_INET, SOCK_STREAM, socket
from typing import Any

from src.config.settings import Settings


class RendezvousClient:
    def __init__(self, config: Settings) -> None:
        self._config = config

    def register(self) -> dict[str, Any] | None:
        return self._request(
            {
                "type": "REGISTER",
                "namespace": str(self._config.namespace),
                "name": str(self._config.name),
                "port": self._config.listen_port,
                "ttl": self._config.register_ttl,
            }
        )

    def unregister(self) -> dict[str, Any] | None:
        return self._request(
            {
                "type": "UNREGISTER",
                "namespace": str(self._config.namespace),
                "name": str(self._config.name),
                "port": self._config.listen_port,
            }
        )

    def discover(self) -> list[dict[str, Any]]:
        response = self._request(
            {
                "type": "DISCOVER",
                "namespace": str(self._config.namespace),
            }
        )
        if not response:
            return []

        peers = response.get("peers")
        if not isinstance(peers, list):
            return []

        return self._discover_filter(peers)

    def _request(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        client_socket = socket(AF_INET, SOCK_STREAM)

        try:
            client_socket.settimeout(5.0)
            client_socket.connect((str(self._config.rdv_host), self._config.rdv_port))
            message = json.dumps(payload) + "\n"
            client_socket.sendall(message.encode("utf-8"))
            raw = client_socket.recv(4096)
            if not raw:
                return None
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else None
        except (OSError, json.JSONDecodeError):
            return None
        finally:
            client_socket.close()

    def _discover_filter(self, peers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            peer
            for peer in peers
            if peer.get("name") != self._config.name
            or peer.get("namespace") != self._config.namespace
        ]
