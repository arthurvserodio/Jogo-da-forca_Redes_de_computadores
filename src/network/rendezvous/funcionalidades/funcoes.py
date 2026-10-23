from ..operacoes.register import REGISTER
from ..operacoes.discover import *
from ..operacoes.unregister import UNREGISTER
from ..connectRendezvous import connectServer
from ..importConfig.carregaConfig import *

#FUNÇÃO PARA REGISTRAR O PEER
def registrar_peer():
    #Carregando as configurações
    config = carregaConfig()
    #Resposta do rendevouz para a operação REGISTER
    respostaRegister = connectServer(REGISTER(config),config)
    print("Resposta do Rendevouz: ", respostaRegister)
    #Se o status da resposta for OK, então o registro deu certo
    if(respostaRegister["status"] == "OK"):
        print("Registro feito com sucesso")
    #Se não, informa o motivo
    else:
        print("Erro no registro: ", respostaRegister.get("message"))

#FUNÇÃO DE DESCOBRIR PEERS
def descobrir_peers():
    #Carregando as configurações
    config = carregaConfig()
    #Resposta do rendevouz para a operação DISCOVER
    respostaDiscover = connectServer(DISCOVER(config),config)
    #Status da resposta
    print("Status do Discover: ", respostaDiscover["status"])
    #Se a mensagem de DISCOVER deu certo, então a gente filtra os peers
    if(respostaDiscover["status"] == "OK"):
        #Peers filtrados
        peers_filtrados = filtro_discover(respostaDiscover["peers"], config)
        return peers_filtrados
    #Se não, informa o erro
    else:
        print("Erro no Discover: ", respostaDiscover.get("message"))

#FUNÇÃO DE UNREGISTER
def desregistrar_peer():
    #Carregando as configurações
    config = carregaConfig()
    #Resposta do rendevouz para a operação UNREGISTER
    respostaUnregister = connectServer(UNREGISTER(config),config)
    print("Status do Unregister: ", respostaUnregister["status"])
    if(respostaUnregister["status"] != "OK"):
        print("Erro no Unregister: ", respostaUnregister.get("message"))