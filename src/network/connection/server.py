import socket
from collections.abc import Callable
from threading import Event, Thread

AcceptHandler = Callable[[socket.socket, str], None]


class TCPServer:
    def __init__(self, host: str, port: int, on_accept: AcceptHandler) -> None:
        self._host = host
        self._port = port
        self._on_accept = on_accept

        self._stop = Event()
        self._listener: socket.socket | None = None
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._listener is not None:
            raise RuntimeError("Servidor já está rodando")

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((self._host, self._port))
            listener.listen()
            # Operações bloqueantes terão timeout para permitir parada graciosa
            listener.settimeout(0.5)
        except OSError:
            listener.close()
            raise

        self._stop.clear()
        self._listener = listener

        self._thread = Thread(
            target=self._accept_loop,
            args=(listener,),
            name="tcp-listener",
            daemon=True,
        )
        self._thread.start()

    def _accept_loop(self, listener: socket.socket) -> None:
        while not self._stop.is_set():
            try:
                client, address = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                if not self._stop.is_set():
                    # TODO: Definir Error handler ou logger
                    print("Erro ao aceitar conexão")
                break

            try:
                self._on_accept(client, str(address[0]))
            except Exception:
                client.close()
                # TODO: Definir Error handler ou logger
                print("Erro ao entregar conexão para o gerenciador")

    def stop(self) -> None:
        self._stop.set()

        if self._listener is not None:
            self._listener.close()

        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

        self._listener = None
        self._thread = None
