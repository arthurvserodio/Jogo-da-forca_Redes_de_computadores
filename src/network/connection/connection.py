import json
import socket
from threading import Lock

from src.constants import MAX_MESSAGE_BYTES
from src.erros.app_erros import ProtocolError

type JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
type Message = dict[str, JsonValue]


class PeerConnection:
    def __init__(self, sock: socket.socket, outgoing: bool) -> None:
        self._socket = sock
        self.outgoing = outgoing

        self._buffer = bytearray()
        self._send_lock = Lock()
        self._close_lock = Lock()
        self._closed = False

    def set_timeout(self, seconds: float | None) -> None:
        self._socket.settimeout(seconds)

    def send(self, message: Message) -> None:
        payload = json.dumps(message, ensure_ascii=False, allow_nan=False).encode("utf-8")

        if len(payload) > MAX_MESSAGE_BYTES:
            raise ProtocolError(
                f"Mensagem maior que o tamanho permitido: payload={len(payload)} > MAX_BYTES {MAX_MESSAGE_BYTES}"
            )

        with self._send_lock:
            self._socket.sendall(payload + b"\n")

    def receive(self) -> Message | None:
        while True:
            newline = self._buffer.find(b"\n")

            if newline > MAX_MESSAGE_BYTES:
                raise ProtocolError(
                    f"Mensagem maior que o tamanho permitido: newline={newline} > MAX_BYTES {MAX_MESSAGE_BYTES}"
                )

            if newline >= 0:
                raw = bytes(self._buffer[:newline])
                del self._buffer[: newline + 1]
                return self._decode(raw)

            if len(self._buffer) > MAX_MESSAGE_BYTES:
                raise ProtocolError(
                    f"Mensagem maior que o tamanho permitido: buffer={len(self._buffer)} > MAX_BYTES {MAX_MESSAGE_BYTES}"
                )

            chunk = self._socket.recv(4096)

            if not chunk:
                if self._buffer:
                    raise ProtocolError("Conexão com mensagem incompleta")
                return None

            self._buffer.extend(chunk)

    def _decode(self, raw: bytes) -> Message:
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeError, ValueError) as error:
            raise ProtocolError("Formato do payload inválido (JSON inválido)") from error

        if not isinstance(value, dict):
            raise ProtocolError("Mensagem deve ser um JSON")

        if not isinstance(value.get("type"), str):
            raise ProtocolError("Mensagem deve conter um tipo")

        return value

    def close(self) -> None:
        with self._close_lock:
            if self._closed:
                return

            self._closed = True

            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                self._socket.close()
