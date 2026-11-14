import json
from socket import AF_INET, SOCK_STREAM, gaierror, socket
from typing import cast

from src.config.settings import Settings

from .types import Config, Response


def connectServer(mensagemOperacao: str, config: Config | Settings) -> Response | None:
    # Nome e porta do servidor rendezvous
    if isinstance(config, Settings):
        server_name = str(config.rdv_host)
        server_port = config.rdv_port
    else:
        server_name = config["rdv_host"]
        server_port = config["rdv_port"]

    client_socket = socket(AF_INET, SOCK_STREAM)  # Cria o socket cliente da conexão TCP
    try:
        # TimeOut para deixar a comunicação TCP eficaz
        # Operações bloqueantes terão um tempo de espera de 5 seg - a operação não fica presa indefinidamente
        client_socket.settimeout(5)

        client_socket.connect((server_name, server_port))  # Conecta com o servidor Rendezvous
        client_socket.sendall(mensagemOperacao.encode("utf-8"))
        resposta = client_socket.recv(1024)  # Buffer de 1024 bytes
        # JSON -> DICIONÁRIO
        resposta_json = json.loads(resposta.decode("utf-8"))
        # Retorno da resposta
        return cast(Response, resposta_json)
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
        client_socket.close()
