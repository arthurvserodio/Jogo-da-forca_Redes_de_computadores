import uuid
from typing import Any, cast
from threading import RLock

from src.domain.peer import Peer
from src.game.lobby.lobby import Lobby
from src.interface.executar import mostrar_partidas
from src.interface.cli import mostrar_Player
from src.network.connection.connection import Message
from src.network.connection.manager import ConnectionManager
from src.game.forca.gamePlayer import (
    GameOverMessage,
    GameStartMessage,
    StateMessage,
)
from src.interface.executar import mostra_gameOver
from src.interface.executar import mostra_status_jogo
from src.config.types import ConfigJogo


# Ponte entre a implementação do TCP e a lógica do jogo
class RoteadorJogo:
    def __init__(self, lobby: Lobby, config: ConfigJogo) -> None:
        self.config = config #  Configurações do jogo
        self.lobby = lobby # Pega o looby do jogo
        self.rede: ConnectionManager | None = None # Pega o gerenciador de conexões
        self.local_peer_id = lobby.game_host.host_id # Pega o host da partida
        self.host_lock = RLock()
        self.peers_aguardando: set[str] = set()
    # Conecta a rede ao gerenciador
    def conectar_rede(self, rede: ConnectionManager) -> None:
        self.rede = rede

    # Envia uma mensagem a outro peer
    def _enviar(self, peer_id: str, mensagem: dict[str, Any]) -> None:
        if self.rede is None:
            raise RuntimeError("Rede TCP ainda não configurada")
        self.rede.send(peer_id, cast(Message, mensagem))

    #Envelope usado para enviar as mensagens do lobby
    def _envelope(self, peer_id: str, mensagem: dict[str, Any], msg_id: str | None = None) -> dict[str, Any]:
        return {
            **mensagem,
            "msg_id": msg_id if msg_id is not None else str(uuid.uuid4()),
            "src": self.local_peer_id,
            "dst": peer_id,
            "ttl": 1,
        }

    #FUNÇÕES DO PLAYER
    # Solicita as partidas para outros peers pela mensagem GAME_LIST
    def solicitar_partidas(self) -> None:
        if self.rede is None:
            raise RuntimeError("Rede TCP ainda não configurada")
        mensagem = self.lobby.gerar_mensagem_GAMELIST()
        conectados = self.rede.connected_peer_list()
        if not conectados:
            print("[GAME] Nenhum peer conectado para consultar partidas.")
            return
        self.peers_aguardando = set(conectados)
        for peer_id in conectados:
            self._enviar(peer_id, self._envelope(peer_id, mensagem))
        print(f"[GAME] Consultando partidas em {len(conectados)} peer(s)...")

    # Envia a mensagem de solicitação para entrar em uma partida
    def entrar_partida(self, host_id: str) -> None:
        partida = self.lobby.partidas_encontradas.get(host_id)
        if partida is None or partida.get("status") != "OPEN":
            print(f"[PLAYER] Nenhuma partida aberta encontrada para {host_id}")
            return
        self._enviar(host_id, self._envelope(host_id, self.lobby.mensagemJOIN(partida["game_id"])))

    # Envia o palpite para o host, colocando ele dentro do envelope
    def enviar_palpite(self, palpite: str) -> None:
        jogador = self.lobby.game_player
        # Verifica se o jogador pode enviar o palpite
        mensagem = jogador.gerar_guess(palpite)
        if mensagem is None:
            print("[PLAYER] Não foi possível enviar o palpite. Verifique se é sua vez.")
            return
        # Identifica o host da partida
        host_id = jogador.host_id
        if host_id is None:
            print("[PLAYER] Host da partida não encontrado.")
            return
        # Envia o GUESS pela conexão TCP
        self._enviar(host_id,self._envelope(host_id, mensagem))

    # Envia a mensagem de LEAVE para o host
    def enviar_leave(self) -> None:
        jogador = self.lobby.game_player
        # Gera a mensagem LEAVE
        mensagem = self.lobby.mensagemLEAVE()
        if mensagem is None:
            print("[PLAYER] Você não está participando de uma partida.")
            return
        # Identifica o host da partida
        host_id = jogador.host_id
        if host_id is None:
            print("[PLAYER] Host da partida não encontrado.")
            return
        # Envia LEAVE pela conexão TCP
        self._enviar(host_id,self._envelope(host_id, mensagem))
        print("[PLAYER] Solicitando saída da partida...")


    # Recebe uma mensagem de outro peer pelo TCP
    def receber_mensagem(self, peer: Peer, mensagem: Message) -> None:
            tipo = mensagem.get("type")
            dados = cast(dict[str, Any], mensagem)
            if mensagem.get("type") == "GAME_OVER":
                print(f"[DEBUG PLAYER] GAME_OVER chegou de {peer.peer_id}")
                print(f"[DEBUG PLAYER] Conteúdo: {mensagem}")
            if (
                mensagem.get("ttl") != 1
                or mensagem.get("src") != peer.peer_id
                or mensagem.get("dst") != self.local_peer_id
                or not isinstance(mensagem.get("msg_id"), str)
            ):
                print(f"[REDE] Envelope inválido de {peer.peer_id}: {tipo}")
                return
            if tipo == "GAME_LIST":
                with self.host_lock:
                    resposta = self.lobby.GameList_Ok()
                self._enviar(
                    peer.peer_id,
                    self._envelope(peer.peer_id, resposta, str(dados["msg_id"])),
                )
            elif tipo == "GAME_LIST_OK":
                with self.host_lock:
                    if self.lobby.recebe_GAMELIST_Ok(dados):
                        self.peers_aguardando.discard(peer.peer_id)

                        if not self.peers_aguardando:
                            mostrar_partidas(self.lobby.partidas_encontradas)
            
            elif tipo == "JOIN":
                with self.host_lock:
                    resposta = self.lobby.processar_JOIN(dados)
                    # Envia JOIN_OK ou JOIN_ERR.
                    self._enviar(peer.peer_id,self._envelope(peer.peer_id,resposta,str(dados["msg_id"])))

                    # Se for uma reentrada, envia o estado atual.
                    if (resposta.get("type") == "JOIN_OK" and resposta.get("rejoin") is True):
                        estado = self.lobby.game_host.obter_UltimoEstado()
                        if estado is not None:
                            self._enviar(
                                peer.peer_id,
                                self._envelope(
                                    peer.peer_id,
                                    {
                                        "type": "STATE",
                                        **estado,
                                    },
                                ),
                            )

    
            elif tipo == "JOIN_OK":
                self.lobby.recebe_JoinOk(dados)
    
            elif tipo == "JOIN_ERR":
                self.lobby.recebe_JoinErr(dados)

            elif tipo == "GAME_START":
                jogador = self.lobby.game_player
                # Aceita somente mensagens do host da partida atual
                if peer.peer_id != jogador.host_id:
                    return
                jogador.receber_gameStart(cast(GameStartMessage, dados))

            elif tipo == "STATE":
                jogador = self.lobby.game_player
                if peer.peer_id != jogador.host_id:
                    return

                atualizado = jogador.atualizaState(cast(StateMessage, dados))
                if atualizado:
                    status = {
                        "game_id": jogador.game_id,
                        "host_id": jogador.host_id,
                        "estado": "RUNNING",
                        "palavra_mask": " ".join(jogador.mask_word or ""),
                        "vidas": jogador.vidas,
                        "letras_erradas": jogador.letras_erradas,
                        "jogadores": jogador.players,
                        "turno_atual": jogador.turno,
                    }
                    mostra_status_jogo(status, self.config)


            elif tipo == "GUESS_RESULT":
                jogador = self.lobby.game_player

                if peer.peer_id != jogador.host_id:
                    return

                jogador.receber_guessResult(dados)

            elif tipo == "GAME_OVER":
                jogador = self.lobby.game_player
                print(f"[DEBUG PLAYER] Host esperado: {jogador.host_id}")
                print(f"[DEBUG PLAYER] Host recebido: {peer.peer_id}")
                if peer.peer_id != jogador.host_id:
                    print("[DEBUG PLAYER] Mensagem rejeitada: host incorreto")
                    return
                if peer.peer_id != jogador.host_id:
                    print("[DEBUG] GAME_OVER ignorado: host diferente")
                    return
                resultado = jogador.receber_gameOver(cast(GameOverMessage, dados))
                print(f"[DEBUG PLAYER] Resultado: {resultado}")
                print(f"[DEBUG PLAYER] Estado atual: {jogador.estado.name}")
                
                if resultado is True:
                    mostra_gameOver(dados)
                elif isinstance(resultado, str):
                    print(f"[GAME] Erro de integridade: {resultado}")

            elif tipo == "LEAVE":
                # O host processa a saída do jogador
                with self.host_lock:
                    resposta = self.lobby.processa_Leave(dados)
                if resposta is not None:
                    self._enviar(peer.peer_id,self._envelope(peer.peer_id,resposta,str(dados["msg_id"])))
                host = self.lobby.game_host
                # Se todos os jogadores saíram, exibe o encerramento.
                if host.game_state.name == "FINISHED" and not host.players:
                    game_over = host.gerar_gameOver()

                    if game_over is not None:
                        mostra_gameOver(game_over)

            elif tipo == "LEAVE_OK":
                # O jogador confirma a saída da partida
                if peer.peer_id == self.lobby.game_player.host_id:
                    self.lobby.recebe_LeaveOK(dados)

            elif tipo == "GUESS":
                self.processar_guess(peer, dados)
    
            elif tipo == "ERROR":
                print(f"[REDE] Erro de {peer.peer_id}: {dados.get('code')}: {dados.get('message')}")


    # FUNÇÕES DO HOST
    # Inicia a partida
    def iniciar_partida(self) -> None:
        with self.host_lock:
            host = self.lobby.game_host
            # Inicia a partida
            resultado = host.iniciar_jogo()
            if not resultado["aceito"]:
                print(f"[HOST] {resultado['mensagem']}")
                return

            print(f"[HOST] {resultado['mensagem']}")
            print(f"[HOST] Jogadores: {', '.join(host.players)}")
            print(f"[HOST] Primeiro turno: {host.turno_atual}")

            # Mensagens geradas pelo GameHost
            game_start = host.gerar_gameStart()
            estado = host.obter_UltimoEstado()
            if game_start is None or estado is None:
                print("[HOST] Erro ao gerar mensagens iniciais.")
                return
            # Envia as mensagens a todos os jogadores
            for player_id in host.players:
                self._enviar(player_id,self._envelope(player_id,{"type": "GAME_START", **game_start}))
                self._enviar(player_id,self._envelope(player_id,{"type": "STATE", **estado}))

            status = host.obter_status()
            if status is not None:
                mostra_status_jogo(status, self.config)

    # Envia o State e Game_Over a todos os jogadores
    def enviar_para_jogadores(self, mensagem: dict[str, Any]) -> None:
        host = self.lobby.game_host
        for player_id in host.players.copy():
            try:
                self._enviar(player_id,self._envelope(player_id, mensagem))
            except (OSError, RuntimeError) as erro:
                print(f"[HOST] Falha ao enviar para {player_id}: {erro}")

    # Processa o Guess do jogador e o que faz com ele
    def processar_guess(self, peer: Peer, mensagem: dict[str, Any]) -> None:
        with self.host_lock:
            host = self.lobby.game_host
            # Identifica o tipo do palpite
            letra = mensagem.get("letter")
            palavra = mensagem.get("word")
            if isinstance(letra, str) and palavra is None:
                tipo = "letter"
                palpite = letra
            elif isinstance(palavra, str) and letra is None:
                tipo = "word"
                palpite = palavra
            else:
                tipo = ""
                palpite = ""

            # Guarda o número de sequência anterior
            seq_anterior = host.seq
            # Processa a jogada utilizando o GameHost
            resultado = host.processar_jogada(peer.peer_id,tipo,palpite)
            # Responde apenas ao jogador que enviou o palpite
            resposta = host.gerar_guessResult(resultado)

            self._enviar(peer.peer_id,self._envelope(peer.peer_id,resposta,str(mensagem["msg_id"])))

            # A partida terminou
            if host.game_state.name == "FINISHED":
                if resultado.get("aceito"):
                    game_over = host.gerar_gameOver()
                    if game_over is not None:
                        self.enviar_para_jogadores(game_over)
                        mostra_gameOver(game_over)
                return
            # Se um novo STATE foi gerado, envia aos jogadores
            if host.seq > seq_anterior:
                estado = host.obter_UltimoEstado()
                if estado is not None:
                    self.enviar_para_jogadores({
                        "type": "STATE",
                        **estado,
                    })
                    status = host.obter_status()
                    if status is not None:
                        mostra_status_jogo(status, self.config)

    # Tratando das desconexões por meio do PING PONG - se percebeu que não ta respondendo, retira o jogador
    def tratar_desconexao(self, peer: Peer) -> None:
        with self.host_lock:
            host = self.lobby.game_host
            jogador = self.lobby.game_player

            # Se nosso host perdeu um dos jogadores, retira-o da partida.
            if peer.peer_id in host.players:
                resultado = host.remover_jogador(peer.peer_id, "disconnect")
                if resultado == "Player_removed_successfully":
                    print(f"[HOST] Jogador {peer.peer_id} desconectou.")
                    if host.game_state.name == "RUNNING":
                        estado = host.obter_UltimoEstado()
                        if estado is not None:
                            self.enviar_para_jogadores({"type": "STATE", **estado})
                            status = host.obter_status()
                            if status is not None:
                                mostra_status_jogo(status, self.config)

           # Preservar os dados para tentar recuperar a sessão depois.
            if jogador.host_id == peer.peer_id:
                mostrar_Player(f"Host {peer.peer_id} indisponível — tentando reconectar.")

    # Tratar a reconexão de quem caiu do jogo
    def tratar_reconexao(self, peer: Peer) -> None:
        with self.host_lock:
            jogador = self.lobby.game_player
            # Verifica se o peer reconectado é o host da partida atual.
            if (
                jogador.host_id == peer.peer_id
                and jogador.game_id is not None
                and jogador.estado.name == "PLAYING"
            ):
                mostrar_Player(f"Conexão com o host {peer.peer_id} restabelecida.")
                # Solicita a reentrada na mesma partida.
                mensagem = self.lobby.mensagemJOIN(jogador.game_id)
                self._enviar(peer.peer_id,self._envelope(peer.peer_id, mensagem),)
                mostrar_Player("Solicitando retorno à partida...")
            else:
                print(f"[REDE] Conexão restabelecida com {peer.peer_id}.")


    # Verifica se o jogador perdeu a vez
    def verificar_timeout_turno(self) -> None:
        host = self.lobby.game_host
        with self.host_lock:
            # O próprio GameHost verifica o estado, o turno atual e o tempo transcorrido.
            jogador = host.verifica_timeout()
            if jogador is False:
                return
            # Teve timeout, novo STATE
            estado = host.obter_UltimoEstado()
            print(f"[HOST] Tempo esgotado para {jogador}.")
            if estado is not None:
                self.enviar_para_jogadores({
                    "type": "STATE",
                    **estado,
                })
                status = host.obter_status()
                if status is not None:
                    mostra_status_jogo(status, self.config)

    # Cancela a partida -> /cancel
    def cancelar_partida(self) -> None:
        with self.host_lock:
            host = self.lobby.game_host

            # Guarda os participantes antes do cancelamento.
            jogadores = host.players.copy()

            if not host.cancelar_jogo():
                print("[HOST] Não foi possível cancelar a partida.")
                return

            print("[HOST] Partida cancelada!")

            game_over = host.gerar_gameOver()
            if game_over is None:
                return

            # Informa o cancelamento aos jogadores.
            for player_id in jogadores:
                try:
                    print(f"[DEBUG HOST] Enviando GAME_OVER para {player_id}")
                    print(f"[DEBUG HOST] Mensagem: {game_over}")        
                    self._enviar(player_id,self._envelope(player_id, game_over))
                except (OSError, RuntimeError) as erro:
                    print(f"[HOST] Falha ao enviar GAME_OVER para {player_id}: {erro}")

            # Exibe o encerramento também no host.
            mostra_gameOver(game_over)

