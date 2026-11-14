import socket
import unittest
from ipaddress import ip_address

from src.constants import MAX_MESSAGE_BYTES
from src.domain.peer import Peer, PeerAddress
from src.erros.app_erros import ProtocolError
from src.network.connection.connection import PeerConnection
from src.network.connection.peer_table import PeerTable


class PeerTableTests(unittest.TestCase):
    def test_add_get_and_remove_peer(self) -> None:
        table = PeerTable()
        peer = Peer(
            name="alice",
            namespace="CIC",
            address=PeerAddress(ip=ip_address("127.0.0.1"), port=8001),
        )

        table.add_or_update(peer)
        self.assertEqual(len(table), 1)

        retrieved = table.get(peer.peer_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.peer_id, "alice@CIC")

        new_address = PeerAddress(ip=ip_address("127.0.0.1"), port=8002)
        table.update_address(peer.peer_id, new_address)
        updated = table.get(peer.peer_id)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.address.port, 8002)

        self.assertTrue(table.remove(peer.peer_id))
        self.assertEqual(len(table), 0)
        self.assertIsNone(table.get(peer.peer_id))


class PeerConnectionTests(unittest.TestCase):
    def test_send_and_receive_message(self) -> None:
        sock_a, sock_b = socket.socketpair()
        try:
            conn_a = PeerConnection(sock_a, outgoing=True)
            conn_b = PeerConnection(sock_b, outgoing=False)

            msg = {"type": "HELLO", "name": "alice", "namespace": "CIC", "port": 8001}
            conn_a.send(msg)
            received = conn_b.receive()

            self.assertEqual(received, msg)
        finally:
            conn_a.close()
            conn_b.close()

    def test_message_exceeds_max_bytes_raises_protocol_error(self) -> None:
        sock_a, sock_b = socket.socketpair()
        try:
            conn = PeerConnection(sock_a, outgoing=True)
            oversized = {"type": "BIG", "payload": "x" * (MAX_MESSAGE_BYTES + 10)}
            with self.assertRaises(ProtocolError):
                conn.send(oversized)
        finally:
            conn.close()
            sock_b.close()
