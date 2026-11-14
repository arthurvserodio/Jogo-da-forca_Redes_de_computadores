import json
from socket import AF_INET, SOCK_STREAM, gaierror, socket
from threading import Event
from typing import cast

from src.config.settings import Settings
from src.network.rendezvous.operacoes.discover import DISCOVER, filtro_discover
from src.network.rendezvous.operacoes.refresh import iniciar_refresh
from src.network.rendezvous.operacoes.register import REGISTER
from src.network.rendezvous.operacoes.unregister import UNREGISTER

from .types import (
    Peer,
    ResponseRegisterError,
    ResponseRegisterOK,
    ResponseServer,
)


class RendezvousManeger:
    def __init__(self, config):
        self.config = config  # Pega informações do arquivo de configurações
        self.registrado = False  # Guarda se o peer está registrado no rendevouz
        self.peers = [Peer]  # Guarda os peers que estão registrados -> pelo DISCOVER
        self.parar_refresh = None  # Usado para parar nossa thread de renovação, pois o usuario que deu /quit não precisa ser renovado
        self.thread_refresh = None  # Guarda a thread de renovação

    # Método para conectar ao Rendezvous
    def connectServer(self, mensagemOperacao: str) -> ResponseServer | None:
        # Nome e porta do servidor rendezvous
        if isinstance(self.config, Settings):
            server_name = str(self.config.rdv_host)
            server_port = self.config.rdv_port
        else:
            server_name = self.config["rdv_host"]
            server_port = self.config["rdv_port"]

        client_socket = socket(AF_INET, SOCK_STREAM)  # Cria o socket cliente da conexão TCP
        try:
            # TimeOut para deixar a comunicação TCP eficaz
            # Operações bloqueantes terão um tempo de espera de 5 seg - a operação não fica presa indefinidamente
            client_socket.settimeout(5)

            client_socket.connect((server_name, server_port))  # Conecta com o servidor Rendezvous
            client_socket.sendall(mensagemOperacao.encode("utf-8"))
            resposta = bytearray()
            # Como não é garantido que a mensagem chegue de uma vez, a gente precisa ir montando até encontrar um \n
            while b"\n" not in resposta:
                dados = client_socket.recv(2048)
                # Se não tiver recebendo dados, quebra o while
                if not dados:
                    break
                # Vai acumulando os dados na resposta
                resposta.extend(dados)
                # Proteção contra mensagem muito grandes
                if len(resposta) > 65536:
                    return None
            # Se a mensagem ta vazia, então nada foi recebido
            if not resposta:
                return None
            mensagem = bytes(resposta).split(b"\n", 1)[0]
            # JSON -> DICIONÁRIO
            resposta_json = json.loads(mensagem.decode("utf-8"))
            # Retorno da resposta
            return cast(ResponseServer, resposta_json)
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

    # Método para se registrar no Rendezvous
    def registrar(self) -> ResponseServer | None:
        # Pega a mensagem register e envia ao servidor
        mensagem = REGISTER(self.config)
        respostaServer = self.connectServer(mensagem)
        # Se a resposta existir e tiver status OK, o peer está registrado
        if respostaServer is not None and respostaServer["status"] == "OK":
            self.registrado = True
        # Retorna a mensagem dada pelo servidor
        return respostaServer

    # Método para descobrir os peers registrados no servidor
    def descobrir_peers(self) -> ResponseServer | None:
        # Monta a mensasgem de discover para ser enviada
        mensagem = DISCOVER(self.config)
        respostaServer = self.connectServer(mensagem)
        # Se a resposta existir e tiver status OK, pegamos a lista de peers
        if respostaServer is not None and respostaServer["status"] == "OK":
            self.peers = filtro_discover(respostaServer["peers"], self.config)
        # Retorna a mensagem dada pelo servidor
        return respostaServer

    # Método para desresgistrar do servidor
    def desregistrar(self) -> ResponseServer | None:
        # Fecha a thread de refresh
        self.termina_refresh()
        # Monta a mensasgem de unregister para ser enviada
        mensagem = UNREGISTER(self.config)
        respostaServer = self.connectServer(mensagem)
        # Se a resposta existir e tiver status OK, o peer foi desregistrado
        if respostaServer is not None and respostaServer["status"] == "OK":
            self.registrado = False
        # Retorna a mensagem dada pelo servidor
        return respostaServer

    # Refresh do registro no rendevouz
    def refresh_registro(self, ttl: int, parar: Event) -> None:
        # Calcular 80% do ttl
        intervalo = ttl * 0.8
        # Aguarda o momento de renovação
        while not parar.wait(intervalo):
            # Envia novamente uma operação REGISTER
            respostaRegister = self.registrar()
            if respostaRegister is not None and respostaRegister["status"] == "OK":
                # Renovação do intervalo
                intervalo = respostaRegister["ttl"] * 0.8
            else:
                # Tente novamente daqui 10 seg
                intervalo = 10

    # FUNÇÃO DE REFRESH
    def refresh_peer(
        self, respostaRegister: ResponseRegisterOK | ResponseRegisterError | None
    ) -> None:
        # Se não tiver resposta do register ou o register deu erro, não tem como fazer refresh
        if respostaRegister is None or respostaRegister["status"] == "ERROR":
            return None
        ttl = respostaRegister.get("ttl")
        # Verifica se ocorreu um erro e o ttl ta negativo ou não é int
        if not isinstance(ttl, int) or ttl <= 0:
            return
        # Se já temos uma thread, não precisa criar outra
        if self.thread_refresh is not None and self.thread_refresh.is_alive():
            return None
        self.parar_refresh, self.thread_refresh = iniciar_refresh(
            self.refresh_registro, respostaRegister["ttl"]
        )

    # FUNÇÃO PARA PARAR O REFRESH
    def termina_refresh(self) -> None:
        # Se já é None, já foi limpado
        if self.parar_refresh is None or self.thread_refresh is None:
            return
        self.parar_refresh.set()
        self.thread_refresh.join()
        self.parar_refresh = None
        self.thread_refresh = None
