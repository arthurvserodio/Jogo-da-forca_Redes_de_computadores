import threading

from ..connectRendezvous import connectServer
from ..types import Config
from .register import REGISTER


# Refresh do registro no rendevouz
def refresh_registro(config: Config, ttl: int, parar: threading.Event) -> None:
    # Calcular 80% do ttl
    intervalo = ttl * 0.8
    # Aguarda o momento de renovação
    while not parar.wait(intervalo):
        # Envia novamente uma operação REGISTER
        respostaRegister = connectServer(REGISTER(config), config)
        if respostaRegister and respostaRegister["status"] == "OK":
            print("Registro renovado com sucesso!")
            # Renovação do intervalo
            intervalo = respostaRegister["ttl"] * 0.8
        else:
            print("Falha ao renovar registro!")
            # Tente novamente daqui 10 seg
            intervalo = 10


def iniciar_refresh(config: Config, ttl: int) -> tuple[threading.Event, threading.Thread]:
    # Evento utilizado para interromper o refresh
    parar = threading.Event()
    # Cria uma thread para executar em paralelo
    thread = threading.Thread(
        target=refresh_registro,
        args=(config, ttl, parar),
        daemon=True,  # Executa em segundo plano
    )
    # Inicia a thread
    thread.start()
    return parar, thread
