import socket
from collections.abc import Callable
from ipaddress import ip_address
from threading import Lock, Thread

from src.domain.peer import Peer, PeerAddress
from src.erros.app_erros import ProtocolError
from src.network.connection.connection import Message, PeerConnection
from src.network.connection.peer_table import PeerTable
from src.network.connection.server import TCPServer

MessageHandler = Callable[[Peer, Message], None]


class ConnectionManager:
    def __init__(
        self,
        local_peer: Peer,
        peer_table: PeerTable,
        on_message: MessageHandler,
        # TODO: Colocar constantes
        bind_host: str = "0.0.0.0",  # verificar se localhost também funciona
        handshake_timeout: float = 5.0,
    ) -> None:
        self._local_peer = local_peer.model_copy(deep=True)
        self._peer_table = peer_table
        self._on_message = on_message
        self._handshake_timeout = handshake_timeout

        self._connections: dict[str, PeerConnection] = {}
        self._pending: set[PeerConnection] = set()
        self._lock = Lock()
        self._stopping = False

        self._server = TCPServer(
            host=bind_host, port=local_peer.address.port, on_accept=self._accept
        )

    def start(self) -> None:
        self._server.start()

    def _accept(self, sock: socket.socket, remote_ip: str) -> None:
        connection = PeerConnection(sock, outgoing=False)

        if not self._track_pending(connection):
            return

        Thread(target=self._serve, args=(connection, remote_ip, None), daemon=True).start()

    def connect(self, peer: Peer) -> None:
        # TODO: Verificar se aplicamos essa regra de negócio aqui ou na listagem do rendezvous
        if peer.peer_id == self._local_peer.peer_id:
            return

        with self._lock:
            if self._stopping:
                raise RuntimeError("O gerenciador está encerrado")

            # Não abrir novas conexões com peers já conectados
            if peer.peer_id in self._connections:
                return

        sock = socket.create_connection(
            (str(peer.address.ip), peer.address.port),
            timeout=self._handshake_timeout,
        )

        connection = PeerConnection(sock, outgoing=True)
        remote_ip = str(sock.getpeername()[0])

        if not self._track_pending(connection):
            return

        Thread(target=self._serve, args=(connection, remote_ip, peer.peer_id), daemon=True).start()

    def _track_pending(self, connection: PeerConnection) -> bool:
        with self._lock:
            accept = not self._stopping
            if accept:
                self._pending.add(connection)

        if not accept:
            connection.close()

        return accept

    def _hello(self, message_type: str) -> Message:
        return {
            "type": message_type,
            "name": self._local_peer.name,
            "namespace": self._local_peer.namespace,
            "port": self._local_peer.address.port,
        }

    def _read_identity(self, message: Message | None, expected_type: str, remote_ip: str) -> Peer:
        if message is None:
            raise ProtocolError("Conexão encerrada durante handshake")

        if message.get("type") != expected_type:
            raise ProtocolError(f"Esperava mensagem do tipo {expected_type}")

        name = message.get("name")
        namespace = message.get("namespace")
        port = message.get("port")
        if port is None:
            port = message.get("listen_port")

        if not isinstance(name, str) or not name.strip():
            raise ProtocolError("Nome inválido")

        if not isinstance(namespace, str) or not namespace.strip():
            raise ProtocolError("Namespace inválido")

        if namespace != self._local_peer.namespace:
            raise ProtocolError("Namespace não compatível")

        if not isinstance(port, int) or not 1 <= port <= 65535:
            raise ProtocolError("Porta de escuta inválida")

        return Peer(
            name=name,
            namespace=namespace,
            address=PeerAddress(ip=ip_address(remote_ip), port=port),
        )

    def _handshake(
        self, connection: PeerConnection, remote_ip: str, expected_peer_id: str | None
    ) -> Peer:
        connection.set_timeout(self._handshake_timeout)

        if connection.outgoing:
            connection.send(self._hello("HELLO"))

            peer = self._read_identity(
                connection.receive(),
                "HELLO_OK",
                remote_ip,
            )

            if expected_peer_id is not None and peer.peer_id != expected_peer_id:
                raise ProtocolError("ID diferente do peer esperado")
        else:
            peer = self._read_identity(
                connection.receive(),
                "HELLO",
                remote_ip,
            )

            connection.send(self._hello("HELLO_OK"))

        connection.set_timeout(None)
        return peer

    def _adopt(self, peer: Peer, connection: PeerConnection) -> bool:
        old_connection: PeerConnection | None

        with self._lock:
            if self._stopping:
                return False

            old_connection = self._connections.get(peer.peer_id)

            if old_connection is not None:
                # Preferir conexão em ordem alfabética do peer_id
                prefer_outgoing = self._local_peer.peer_id < peer.peer_id

                old_connection_is_preferred = old_connection.outgoing == prefer_outgoing
                new_connection_is_preferred = connection.outgoing == prefer_outgoing

                if old_connection_is_preferred or not new_connection_is_preferred:
                    return False

            self._connections[peer.peer_id] = connection
            self._pending.discard(connection)
            self._peer_table.add_or_update(peer)

        if old_connection is not None:
            old_connection.close()

        return True

    def _serve(
        self, connection: PeerConnection, remote_ip: str, expected_peer_id: str | None
    ) -> None:
        peer: Peer | None = None

        try:
            peer = self._handshake(connection, remote_ip, expected_peer_id)

            if not self._adopt(peer, connection):
                return

            # TODO: Colocar essa mensagem no sistema de logs
            print(f"Conexão estabelecida com peer com ID: {peer.peer_id}")

            # TODO: Lógica do jogo
            while True:
                message = connection.receive()

                if message is None:
                    break

                if message.get("type") == "BYE":
                    break

                self._on_message(peer, message)

        except (OSError, ValueError) as error:
            # TODO: Colocar essa mensagem no sistema de logs
            print(f"Conexão encerrada: {error}")

        except Exception:
            # TODO: Colocar essa mensagem no sistema de logs
            print("Falha ao manter conexão")

        finally:
            with self._lock:
                self._pending.discard(connection)

                if peer is not None and self._connections.get(peer.peer_id) is connection:
                    del self._connections[peer.peer_id]

            connection.close()

    def send(self, peer_id: str, message: Message) -> None:
        with self._lock:
            connection = self._connections.get(peer_id)

        if connection is None:
            raise RuntimeError(f"Peer com ID {peer_id} desconhecido")

        connection.send(message)

    def connected_peer_list(self) -> list[str]:
        with self._lock:
            return list(self._connections)

    def stop(self) -> None:
        with self._lock:
            self._stopping = True
            connections = set(self._connections.values()) | self._pending
            self._connections.clear()
            self._pending.clear()

        self._server.stop()

        for connection in connections:
            connection.close()
