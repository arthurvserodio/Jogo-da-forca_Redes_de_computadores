from threading import Event, Thread

from ..connectRendezvous import connectServer
from ..importConfig.carregaConfig import carregaConfig
from ..operacoes.discover import DISCOVER, filtro_discover
from ..operacoes.refresh import iniciar_refresh
from ..operacoes.register import REGISTER
from ..operacoes.unregister import UNREGISTER
from ..types import Peer, Response


# FUNÇÃO PARA REGISTRAR O PEER
def registrar_peer() -> Response | None:
    # Carregando as configurações
    config = carregaConfig()
    # Resposta do rendevouz para a operação REGISTER
    respostaRegister = connectServer(REGISTER(config), config)
    print("Resposta do Rendevouz: ", respostaRegister)
    # Se o status da resposta for OK, então o registro deu certo
    if respostaRegister and respostaRegister["status"] == "OK":
        print("Registro feito com sucesso")
    # Se não, informa o motivo
    else:
        print("Erro no registro: ", respostaRegister)
    return respostaRegister


# FUNÇÃO DE DESCOBRIR PEERS
def descobrir_peers() -> list[Peer] | None:
    # Carregando as configurações
    config = carregaConfig()
    # Resposta do rendevouz para a operação DISCOVER
    respostaDiscover = connectServer(DISCOVER(config), config)
    # Se a mensagem de DISCOVER deu certo, então a gente filtra os peers
    if respostaDiscover and respostaDiscover["status"] == "OK":
        # Status da resposta
        print("Status do Discover: ", respostaDiscover["status"])
        # Peers filtrados
        peers_filtrados = filtro_discover(respostaDiscover["peers"], config)
        return peers_filtrados
    # Se não, informa o erro
    else:
        print("Erro no Discover: ", respostaDiscover)
        return None


# FUNÇÃO DE UNREGISTER
def desregistrar_peer() -> None:
    # Carregando as configurações
    config = carregaConfig()
    # Resposta do rendevouz para a operação UNREGISTER
    respostaUnregister = connectServer(UNREGISTER(config), config)
    # Se tiver dado errado, printa a resposta do Rendezvous
    if not respostaUnregister or respostaUnregister["status"] != "OK":
        print("Erro no Unregister: ", respostaUnregister)
    # Se deu certo, fala OK
    else:
        print("Status do Unregister: ", respostaUnregister["status"])


# FUNÇÃO DE REFRESH
def refresh_peer(respostaRegister: Response) -> tuple[Event, Thread]:
    # Carregando as configurações
    config = carregaConfig()
    return iniciar_refresh(config, respostaRegister["ttl"])


# FUNÇÃO PARA PARAR O REFRESH
def termina_refresh(parar: Event, thread: Thread) -> None:
    parar.set()
    thread.join()
