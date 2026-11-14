import threading
from collections.abc import Callable
from ..connectRendezvous import connectServer
from ..types import Config
from .register import REGISTER


def iniciar_refresh( refresh_registro: Callable[[int, threading.Event], None], ttl: int) -> tuple[threading.Event, threading.Thread]:
    # Evento utilizado para interromper o refresh
    parar = threading.Event()
    # Cria uma thread para executar em paralelo
    thread = threading.Thread(
        target=refresh_registro,
        args=(ttl, parar),
        daemon=True,  # Executa em segundo plano
    )
    # Inicia a thread
    thread.start()
    return parar, thread
