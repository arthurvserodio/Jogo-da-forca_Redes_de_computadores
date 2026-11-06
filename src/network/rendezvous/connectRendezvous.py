import json
from socket import AF_INET, SOCK_STREAM, gaierror, socket
from typing import cast

from .types import Config, Response


def connectServer(mensagemOperacao: str, config: Config) -> Response | None:
    # Nome do servidor rendezvous
    serverName = config["rdv_host"]
    # Conecta a porta 8080
    serverPort = config["rdv_port"]
    clientSocket = socket(AF_INET, SOCK_STREAM)  # Cria o socket cliente da conexão TCP
    try:
        # TimeOut para deixar a comunicação TCP eficaz
        # Operações bloqueantes teram um tempo de espera de 5 seg- a operação não fica presa por um tempo indefinido
        clientSocket.settimeout(5)

        clientSocket.connect((serverName, serverPort))  # Conecta com o servidor Rendevouz
        clientSocket.sendall(mensagemOperacao.encode("utf-8"))
        resposta = clientSocket.recv(1024)  # Buffer de 1024 bytes
        # JSON -> DICIONARIO
        respostaJSON = json.loads(resposta.decode("utf-8"))
        # Return da resposta
        return cast(Response, respostaJSON)
    # Se passou de 5 seg para estabelecer a conexão
    except TimeoutError:
        print("Erro: Tempo de conexão excedeu")
        return None
    # Não encontrou o servidor
    except gaierror:
        print("Erro de DNS: não foi possível localizar o servidor")
        return None
    # O servidor recusou a conexão
    except ConnectionRefusedError:
        print("Erro: conexão recusada pelo servidor")
        return None
    # O servidor interrompeu a conexão
    except ConnectionResetError:
        print("Erro: conexão interrompida pelo servidor")
        return None
    # A resposta JSON é inválida
    except json.JSONDecodeError:
        print("Erro: resposta JSON inválida")
        return None
    # Um erro mais geral, pega os erros que pode dar no OS
    except OSError as erro:
        print("Erro de comunicação TCP:", erro)
        return None
    # Fecha a conexão
    finally:
        clientSocket.close()
