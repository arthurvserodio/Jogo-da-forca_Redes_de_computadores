from ..operacoes.register import REGISTER
from ..operacoes.discover import *
from ..operacoes.unregister import UNREGISTER
from ..connectRendezvous import connectServer
from ..importConfig.carregaConfig import *
from ..operacoes.refresh import iniciar_refresh

#FUNÇÃO PARA REGISTRAR O PEER
def registrar_peer():
    #Carregando as configurações
    config = carregaConfig()
    #Resposta do rendevouz para a operação REGISTER
    respostaRegister = connectServer(REGISTER(config),config)
    print("Resposta do Rendevouz: ", respostaRegister)
    #Se o status da resposta for OK, então o registro deu certo
    if(respostaRegister and respostaRegister["status"] == "OK"):
        print("Registro feito com sucesso")
    #Se não, informa o motivo
    else:
        print("Erro no registro: ", respostaRegister)
    return respostaRegister

#FUNÇÃO DE DESCOBRIR PEERS
def descobrir_peers():
    #Carregando as configurações
    config = carregaConfig()
    #Resposta do rendevouz para a operação DISCOVER
    respostaDiscover = connectServer(DISCOVER(config),config)
    #Se a mensagem de DISCOVER deu certo, então a gente filtra os peers
    if(respostaDiscover and respostaDiscover["status"] == "OK"):
        #Status da resposta
        print("Status do Discover: ", respostaDiscover["status"])
        #Peers filtrados
        peers_filtrados = filtro_discover(respostaDiscover["peers"], config)
        return peers_filtrados
    #Se não, informa o erro
    else:
        print("Erro no Discover: ", respostaDiscover)

#FUNÇÃO DE UNREGISTER
def desregistrar_peer():
    #Carregando as configurações
    config = carregaConfig()
    #Resposta do rendevouz para a operação UNREGISTER
    respostaUnregister = connectServer(UNREGISTER(config),config)
    #Se tiver dado errado, printa a resposta do Rendezvous
    if(respostaUnregister and respostaUnregister["status"] != "OK"):
        print("Erro no Unregister: ", respostaUnregister)
    #Se deu certo, fala OK
    else: print("Status do Unregister: ", respostaUnregister["status"])

#FUNÇÃO DE REFRESH
def refresh_peer(respostaRegister):
    #Carregando as configurações
    config = carregaConfig()
    return iniciar_refresh(config,respostaRegister["ttl"])

#FUNÇÃO PARA PARAR O REFRESH
def termina_refresh(parar,thread):
    parar.set()
    thread.join()