import logging
import json
import time
import socket
import uuid
from collections.abc import Callable
from threading import Event, Lock, Thread
from typing import cast

from src.domain.peer import Peer
from src.erros.app_erros import ProtocolError
from src.network.connection.connection import Message, PeerConnection
from src.network.connection.peer_table import PeerTable
from src.network.connection.server import TCPServer
from src.network.keepalive.keepAlive import PeerStats

MessageHandler = Callable[[Peer, Message], None]
DisconnectHandler = Callable[[Peer], None]
ReconnectHandler = Callable[[Peer], None]
logger = logging.getLogger(__name__)



class ConnectionManager:
    def __init__(
        self,
        local_peer: Peer,
        peer_table: PeerTable,
        on_message: MessageHandler,
        # TODO: Colocar constantes
        bind_host: str = "0.0.0.0",  # verificar se localhost também funciona
        handshake_timeout: float = 5.0,
        ping_interval: float = 30.0,
        ping_miss_limit: int = 3,
        on_disconnect: DisconnectHandler | None = None,
        max_reconnect_attempts: int = 5,
        base_backoff: float = 2.0,
        max_backoff: float = 60.0,
        on_reconnect: ReconnectHandler | None = None,
) -> None:
        self._local_peer = local_peer.model_copy(deep=True)
        self._peer_table = peer_table
        self._on_message = on_message
        self._handshake_timeout = handshake_timeout
        if ping_interval <= 0:
            raise ValueError("ping_interval deve ser > 0")
        self._ping_interval = ping_interval
        self._ping_miss_limit = ping_miss_limit
        self._on_disconnect = on_disconnect
        self._on_reconnect = on_reconnect
        if max_reconnect_attempts < 1 or base_backoff <= 0 or max_backoff <= 0:
            raise ValueError("Parâmetros de reconexão inválidos")
        self._max_reconnect_attempts = max_reconnect_attempts
        self._base_backoff = base_backoff
        self._max_backoff = max_backoff
        self._stop_event = Event()
        self._reconnecting: set[str] = set()
        self._reconnect_exhausted: set[str] = set()
        self._dialing: set[str] = set()
        self._disconnected: set[str] = set()
        self._stats: dict[str, PeerStats] = {}
        self._stats_lock = Lock()

        self._connections: dict[str, PeerConnection] = {}
        self._pending: set[PeerConnection] = set()
        self._lock = Lock()
        self._stopping = False
        # Confirmações BYE_OK aguardadas por conexão TCP.
        self._bye_pending: dict[PeerConnection, tuple[str, Event]] = {}

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

    def connect(self, peer: Peer, _from_retry: bool = False) -> None:
        # TODO: Verificar se aplicamos essa regra de negócio aqui ou na listagem do rendezvous
        if peer.peer_id == self._local_peer.peer_id:
            return

        with self._lock:
            if self._stopping:
                raise RuntimeError("O gerenciador está encerrado")
            # Descoberta periódica não pode atropelar o backoff.
            if not _from_retry and (
                peer.peer_id in self._reconnecting
                or peer.peer_id in self._reconnect_exhausted
            ):
                return
            if peer.peer_id in self._connections or peer.peer_id in self._dialing:
                return
            self._dialing.add(peer.peer_id)
        try:
            sock = socket.create_connection(
                (str(peer.address.ip), peer.address.port),
                timeout=self._handshake_timeout,
            )
            self._peer_table.add_or_update(peer)
            connection = PeerConnection(sock, outgoing=True)
            remote_ip = str(sock.getpeername()[0])
            if not self._track_pending(connection):
                with self._lock:
                    self._dialing.discard(peer.peer_id)
                return
            Thread(
                target=self._serve,
                args=(connection, remote_ip, peer.peer_id),
                daemon=True,
            ).start()
        except Exception:
            with self._lock:
                self._dialing.discard(peer.peer_id)
            raise

    def _track_pending(self, connection: PeerConnection) -> bool:
        with self._lock:
            accept = not self._stopping
            if accept:
                self._pending.add(connection)

        if not accept:
            connection.close()

        return accept

    def _hello(self, message_type: str, msg_id: str) -> Message:
        return {
            "type": message_type,
            "msg_id": msg_id,
            "peer_id": self._local_peer.peer_id,
            "version": "1.0",
            "features": ["hangman"],
            "ttl": 1,
        }

    def _read_identity(self, message: Message | None, expected_type: str) -> Peer:
        if message is None:
            raise ProtocolError("Conexão encerrada durante handshake")

        if message.get("type") != expected_type:
            raise ProtocolError(f"Esperava mensagem do tipo {expected_type}")
        if message.get("ttl") != 1 or not isinstance(message.get("msg_id"), str):
            raise ProtocolError("Envelope HELLO inválido")
        if message.get("version") != "1.0":
            raise ProtocolError("Versão do protocolo incompatível")
        features = message.get("features")
        if not isinstance(features, list) or not all(isinstance(f, str) for f in features):
            raise ProtocolError("Lista de features inválida")
        
        peer_id = message.get("peer_id")
        if not isinstance(peer_id, str) or peer_id.count("@") != 1:
            raise ProtocolError("peer_id inválido")
        name, namespace = peer_id.split("@", 1)
        if not name or namespace != self._local_peer.namespace:
            raise ProtocolError("Identidade ou namespace incompatível")
        if peer_id == self._local_peer.peer_id:
            raise ProtocolError("Conexão com o próprio peer")
        
        # O protocolo HELLO não fornece porta: usar o endereço já descoberto.
        peer = self._peer_table.get(peer_id)
        if peer is None:
            raise ProtocolError(f"Peer {peer_id} ainda não conhecido no Rendezvous")
        return peer


    def _handshake(
        self, connection: PeerConnection, remote_ip: str, expected_peer_id: str | None
    ) -> Peer:
        connection.set_timeout(self._handshake_timeout)

        if connection.outgoing:
            msg_id = str(uuid.uuid4())
            hello = self._hello("HELLO", msg_id)
            connection.send(hello)
            logger.debug("TX HELLO: %s", json.dumps(hello, ensure_ascii=False))
            resposta = connection.receive()
            logger.debug("RX HELLO_OK: %s", json.dumps(resposta, ensure_ascii=False))
            peer = self._read_identity(resposta, "HELLO_OK")
            if resposta is None or resposta.get("msg_id") != msg_id:
                raise ProtocolError("HELLO_OK não corresponde ao HELLO enviado")
            
            if expected_peer_id is not None and peer.peer_id != expected_peer_id:
                raise ProtocolError(
                    f"Conectou a {remote_ip} esperando {expected_peer_id}, "
                    f"mas recebeu {peer.peer_id}"
                )
        else:
            pedido = connection.receive()
            logger.debug("RX HELLO: %s", json.dumps(pedido, ensure_ascii=False))
            peer = self._read_identity(pedido, "HELLO")
            if pedido is None:
                raise ProtocolError("HELLO ausente")

            hello_ok = self._hello("HELLO_OK", str(pedido["msg_id"]))
            connection.send(hello_ok)

            logger.debug(
                "TX HELLO_OK: %s",
                json.dumps(hello_ok, ensure_ascii=False),
            )

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
        stats: PeerStats | None = None
        parar_keepalive = Event()
        keepalive_thread: Thread | None = None
        desconectou_ativo = False
        encerramento_voluntario = False

        try:
            peer = self._handshake(connection, remote_ip, expected_peer_id)

            if not self._adopt(peer, connection):
                return
            with self._lock:
                self._dialing.discard(peer.peer_id)
                reconectado = peer.peer_id in self._disconnected
                self._disconnected.discard(peer.peer_id)
                self._reconnect_exhausted.discard(peer.peer_id)
            if reconectado and self._on_reconnect is not None:
                try:
                    self._on_reconnect(peer)
                except Exception:
                    logger.exception("Erro ao notificar reconexão de %s", peer.peer_id)
            stats = PeerStats(self._ping_miss_limit)
            with self._stats_lock:
                self._stats[peer.peer_id] = stats
            keepalive_thread = Thread(
                target=self._keepalive_loop,
                args=(peer.peer_id, connection, stats, parar_keepalive),
                name=f"keepalive-{peer.peer_id}",
                daemon=True,
            )
            keepalive_thread.start()
            logger.info("Conexão estabelecida com %s", peer.peer_id)
            # TODO: Colocar essa mensagem no sistema de logs
            # NÃO PODE ESQUECER DISSO, TEM QUE IMPLEMENTAR NO /LOG

            # TODO: Lógica do jogo
            while True:
                message = connection.receive()

                if message is None:
                    break
                logger.debug(
                    "RX de %s: %s",
                    peer.peer_id,
                    json.dumps(message, ensure_ascii=False),
                )
                if message.get("type") == "BYE":
                    if (message.get("ttl") == 1 and isinstance(message.get("msg_id"), str)):
                        connection.send({
                            "type": "BYE_OK",
                            "msg_id": message["msg_id"],
                            "src": self._local_peer.peer_id,
                            "dst": peer.peer_id,
                            "ttl": 1,
                            "reason": "quit",
                        })
                        encerramento_voluntario = True
                        break
                    logger.debug("BYE inválido recebido de %s", peer.peer_id)
                    continue
                
                if message.get("type") == "BYE_OK":
                    with self._lock:
                        pendente = self._bye_pending.get(connection)
                        if (
                            pendente is not None
                            and message.get("ttl") == 1
                            and message.get("msg_id") == pendente[0]
                        ):
                            pendente[1].set()
                            encerramento_voluntario = True
                            break
                    logger.debug("BYE_OK inesperado de %s", peer.peer_id)
                    continue
                # PING/PONG são mensagens de sessão, não do jogo
                if message.get("type") == "PING":
                    if (
                        message.get("ttl") == 1
                        and isinstance(message.get("msg_id"), str)
                        and isinstance(message.get("timestamp"), str)
                        and stats is not None
                    ):
                        pong = stats.create_pong(message["msg_id"], message["timestamp"])
                        connection.send(cast(Message, pong))
                    continue

                if message.get("type") == "PONG":
                    if (
                        message.get("ttl") == 1
                        and isinstance(message.get("msg_id"), str)
                        and isinstance(message.get("timestamp"), str)
                        and stats is not None
                    ):
                        with self._stats_lock:
                            stats.process_pong(message["msg_id"], message["timestamp"])
                    continue
                self._on_message(peer, message)

        except (OSError, ValueError) as error:
            logger.debug("Conexão encerrada (%s): %s", remote_ip, error)

        except Exception:
            logger.exception("Falha ao manter conexão com %s", remote_ip)

        finally:
            parar_keepalive.set()
            with self._lock:
                self._pending.discard(connection)
                if expected_peer_id is not None:
                    self._dialing.discard(expected_peer_id)
                if peer is not None and self._connections.get(peer.peer_id) is connection:
                    del self._connections[peer.peer_id]
                    desconectou_ativo = True
                    if not encerramento_voluntario and not self._stopping:
                        self._disconnected.add(peer.peer_id)
                        # Reservar o ID antes da notificação e da thread de retry.
                        if peer.peer_id not in self._reconnecting:
                            self._reconnecting.add(peer.peer_id)
                            iniciar_retry = True
                        else:
                            iniciar_retry = False
                    else:
                        iniciar_retry = False
                else:
                    iniciar_retry = False

            if desconectou_ativo and peer is not None and stats is not None:
                with self._stats_lock:
                    if self._stats.get(peer.peer_id) is stats:
                        del self._stats[peer.peer_id]
            connection.close()
            if keepalive_thread is not None and keepalive_thread.is_alive():
                keepalive_thread.join(timeout=1.0)

            
            if desconectou_ativo and peer is not None and not self._stopping:
                # O jogo precisa saber que o peer saiu,
                # mesmo quando o encerramento foi voluntário.
                if self._on_disconnect is not None:
                    try:
                        self._on_disconnect(peer)
                    except Exception:
                        logger.exception(
                            "Erro ao notificar desconexão de %s",
                            peer.peer_id,
                        )

                # Reconectar somente em caso de falha.
                if not encerramento_voluntario and iniciar_retry:
                    Thread(
                        target=self._reconnect_loop,
                        args=(peer.peer_id,),
                        name=f"reconnect-{peer.peer_id}",
                        daemon=True,
                    ).start()


    def _reconnect_loop(self, peer_id: str) -> None:
        try:
            for tentativa in range(1, self._max_reconnect_attempts + 1):
                atraso = min(
                    self._base_backoff * (2 ** (tentativa - 1)),
                    self._max_backoff,
                )
                if self._stop_event.wait(atraso):
                    return
                with self._lock:
                    if self._stopping or peer_id in self._connections:
                        return
                # Recuperar endereço atualizado na PeerTable, quando houver.
                peer = self._peer_table.get(peer_id)
                if peer is None:
                    logger.warning("Sem endereço para reconectar %s", peer_id)
                    return
                logger.info("Reconexão %s: tentativa %d/%d", peer_id, tentativa, self._max_reconnect_attempts)
                try:
                    self.connect(peer, _from_retry=True)
                except (OSError, RuntimeError, ValueError) as erro:
                    logger.debug("Tentativa de reconexão a %s falhou: %s", peer_id, erro)
                    continue
                # connect() inicia handshake em outra thread. Só considerar
                # sucesso após a conexão aparecer em _connections.
                limite = time.monotonic() + self._handshake_timeout + 1.0
                while time.monotonic() < limite:
                    with self._lock:
                        if self._stopping or peer_id in self._connections:
                            return
                        pendente = peer_id in self._dialing
                    if not pendente or self._stop_event.wait(0.1):
                        break
            with self._lock:
                if not self._stopping and peer_id not in self._connections:
                    self._reconnect_exhausted.add(peer_id)
                    logger.warning("Reconexão com %s esgotou %d tentativas", peer_id, self._max_reconnect_attempts)
        finally:
            with self._lock:
                self._reconnecting.discard(peer_id)

    def send(self, peer_id: str, message: Message) -> None:
        with self._lock:
            connection = self._connections.get(peer_id)

        if connection is None:
            logger.warning("Tentativa de envio para peer desconectado: %s", peer_id)
            raise RuntimeError(f"Peer com ID {peer_id} desconhecido")

        connection.send(message)
        logger.debug(
            "TX para %s: %s",
            peer_id,
            json.dumps(message, ensure_ascii=False),
        )

    def reset_reconnect(self, peer_id: str | None = None) -> None:
        with self._lock:
            if peer_id is None:
                self._reconnect_exhausted.clear()
            else:
                self._reconnect_exhausted.discard(peer_id)

    def connected_peer_list(self) -> list[str]:
        with self._lock:
            return list(self._connections)

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            if self._stopping:
                return
            self._stopping = True
            conexoes_ativas = list(self._connections.values())
            ids_por_conexao = {
                conexao: peer_id
                for peer_id, conexao in self._connections.items()
            }
            connections = set(conexoes_ativas) | self._pending
            confirmacoes: list[Event] = []
            for connection in conexoes_ativas:
                msg_id = str(uuid.uuid4())
                confirmado = Event()
                self._bye_pending[connection] = (msg_id, confirmado)
                confirmacoes.append(confirmado)

        # Não manter self._lock enquanto envia ou aguarda ACKs.
        for connection in conexoes_ativas:
            peer_id = ids_por_conexao[connection]
            with self._lock:
                pendente = self._bye_pending.get(connection)
            if pendente is None:
                continue
            try:
                bye = {
                    "type": "BYE",
                    "msg_id": pendente[0],
                    "src": self._local_peer.peer_id,
                    "dst": peer_id,
                    "ttl": 1,
                    "reason": "quit",
                }

                connection.send(bye)
                logger.debug(
                    "TX BYE: %s",
                    json.dumps(bye, ensure_ascii=False),
                )

            except (OSError, RuntimeError, ValueError) as erro:
                logger.debug("Não foi possível enviar BYE: %s", erro)

        # Prazo global para todas as confirmações, sem travar indefinidamente.
        limite = time.monotonic() + 2.0
        for confirmado in confirmacoes:
            restante = limite - time.monotonic()
            if restante <= 0:
                break
            confirmado.wait(restante)

        with self._lock:
            self._bye_pending.clear()
            self._connections.clear()
            self._pending.clear()

        self._server.stop()
        for connection in connections:
            connection.close()

    def _keepalive_loop(
        self,
        peer_id: str,
        connection: PeerConnection,
        stats: PeerStats,
        stop_event: Event,
    ) -> None:
        # O primeiro PING é enviado após ping_interval segundos.
        while not stop_event.wait(self._ping_interval):
            with self._lock:
                if self._stopping or self._connections.get(peer_id) is not connection:
                    return

            with self._stats_lock:
                stats.check_timeouts(self._ping_interval)
                if stats.is_stale:
                    logger.warning("Peer %s STALE após %d perdas", peer_id, stats.missed_pings)
                    connection.close()
                    return
                ping = stats.create_ping()

            try:
                connection.send(cast(Message, ping))
            except OSError as error:
                logger.debug("Falha ao enviar PING para %s: %s", peer_id, error)
                connection.close()
                return

    #Fornece o rtt médio para o comando
    def get_rtt(self) -> dict[str, float]:
        with self._lock:
            ativos = set(self._connections)
        with self._stats_lock:
            return {
                peer_id: stats.get_avg_rtt()
                for peer_id, stats in self._stats.items()
                if peer_id in ativos
            }