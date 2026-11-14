from threading import Lock

from src.domain.peer import Peer, PeerAddress


class PeerTable:
    def __init__(self) -> None:
        self._peers: dict[str, Peer] = {}
        self._lock = Lock()

    def add_or_update(self, peer: Peer) -> None:
        with self._lock:
            self._peers[peer.peer_id] = peer.model_copy(deep=True)

    def get(self, peer_id: str) -> Peer | None:
        with self._lock:
            peer = self._peers.get(peer_id)
            if peer is not None:
                return peer.model_copy(deep=True)
            return None

    def update_address(self, peer_id: str, address: PeerAddress) -> Peer | None:
        with self._lock:
            peer = self._peers.get(peer_id)
            if peer is not None:
                peer.address = address.model_copy(deep=True)
                return peer.model_copy(deep=True)
            return None

    def remove(self, peer_id: str) -> bool:
        with self._lock:
            return self._peers.pop(peer_id, None) is not None

    def list_peers(self) -> list[Peer]:
        with self._lock:
            return [peer.model_copy(deep=True) for peer in self._peers.values()]

    def __len__(self) -> int:
        with self._lock:
            return len(self._peers)
