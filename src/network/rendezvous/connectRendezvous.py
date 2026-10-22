from socket import *
import json
from .register import REGISTER

def connectServer():
    #Nome do servidor rendezvous
    serverName = "pyp2p.mfcaetano.cc"
    #Conecta a porta 8080
    serverPort = 8080
    clientSocket = socket(AF_INET,SOCK_STREAM) #Cria o socket cliente da conexão TCP
    try: 
        #TimeOut para deixar a comunicação TCP eficaz
        #Operações bloqueantes teram um tempo de espera de 5 seg- a operação não fica presa por um tempo indefinido
        clientSocket.settimeout(5)

        print("Conectado ao Rendevouz")
        #pega a mensagem JSON
        mensagem = REGISTER()

        clientSocket.connect((serverName,serverPort)) #Conecta com o servidor Rendevouz
        clientSocket.sendall(mensagem.encode("utf-8"))
        resposta = clientSocket.recv(1024) # Buffer de 1024 bytes
        #JSON -> DICIONARIO
        respostaJSON = json.loads(resposta.decode("utf-8"))
        # Exibe a resposta
        print("Resposta do Rendevouz: ", respostaJSON)
        #Se o status da resposta for OK, então o registro deu certo
        if(respostaJSON["status"] == "OK"):
            print("Registro feito com sucesso")
        #Se não, informa o motivo
        else:
            print("Erro no registro: ", respostaJSON.get("message"))
    #Se passou de 5 seg para estabelecer a conexão
    except timeout:
        print("Tempo de conexão excedeu")
    #Fecha a conexão
    finally:
        clientSocket.close()

if __name__ == "__main__":
    connectServer()
