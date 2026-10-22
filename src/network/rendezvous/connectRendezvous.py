from socket import *
import json
from .register import REGISTER
from .discover import *

def connectServer(mensagemRequisicao):
    #Nome do servidor rendezvous
    serverName = "pyp2p.mfcaetano.cc"
    #Conecta a porta 8080
    serverPort = 8080
    clientSocket = socket(AF_INET,SOCK_STREAM) #Cria o socket cliente da conexão TCP
    try: 
        #TimeOut para deixar a comunicação TCP eficaz
        #Operações bloqueantes teram um tempo de espera de 5 seg- a operação não fica presa por um tempo indefinido
        clientSocket.settimeout(5)

        clientSocket.connect((serverName,serverPort)) #Conecta com o servidor Rendevouz
        clientSocket.sendall(mensagemRequisicao.encode("utf-8"))
        resposta = clientSocket.recv(1024) # Buffer de 1024 bytes
        #JSON -> DICIONARIO
        respostaJSON = json.loads(resposta.decode("utf-8"))
        # Return da resposta
        return respostaJSON
    #Se passou de 5 seg para estabelecer a conexão
    except timeout:
        print("Tempo de conexão excedeu")
    #Fecha a conexão
    finally:
        clientSocket.close()

if __name__ == "__main__":
    print("Conectado ao Rendevouz")
    #pega a mensagem JSON
    mensagemRegister = REGISTER()
    respostaRegister = connectServer(mensagemRegister)
    print("Resposta do Rendevouz: ", respostaRegister)
    #Se o status da resposta for OK, então o registro deu certo
    if(respostaRegister["status"] == "OK"):
        print("Registro feito com sucesso")
        dadosRegister = json.loads(mensagemRegister)
        #Quem sou eu?
        meu_peer = {
            "name": dadosRegister["name"],
            "ip": respostaRegister["ip"],
            "port": respostaRegister["port"]
        }
        #Se o registro foi um sucesso, descubra os nós que estão registrados
        respostaDiscover = connectServer(DISCOVER())
        print("Resposta do Discover: ", respostaDiscover)
        print("Resposta do Discover FILTRADO: ", filtro_discover(respostaDiscover["peers"], meu_peer))
    #Se não, informa o motivo
    else:
        print("Erro no registro: ", respostaRegister.get("message"))

