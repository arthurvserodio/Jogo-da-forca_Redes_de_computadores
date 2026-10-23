import threading
from .register import REGISTER
from ..connectRendezvous import connectServer

#Refresh do registro no rendevouz
def refresh_registro(config,ttl,parar):
    #Calcular 80% do ttl
    intervalo = ttl * 0.8
    #Aguarda o momento de renovação
    while not parar.wait(intervalo):
        #Envia novamente uma operação REGISTER
        respostaRegister = connectServer(REGISTER(config),config)
        if respostaRegister and respostaRegister["status"] == "OK":
            print("Registro renovado com sucesso!")
            #Renovação do intervalo
            intervalo = respostaRegister["ttl"] * 0.8
        else:
            print("Falha ao renovar registro!")
            #Tente novamente daqui 10 seg
            intervalo = 10

def iniciar_refresh(config,ttl):
    # Evento utilizado para interromper o refresh
    parar = threading.Event()
    # Cria uma thread para executar em paralelo
    thread = threading.Thread(
        target=refresh_registro,
        args=(config,ttl, parar),
        daemon=True #Executa em segundo plano
    )
    #Inicia a thread
    thread.start()
    return parar, thread