from typing import Any

from src.interface.cli import mostrar_Host, mostrar_Player


class Lobby:
    def __init__(self, game_host: Any, game_player: Any) -> None:
        self.game_host = game_host  # Guarda a partida que esse peer está hospedando
        self.game_player = game_player  # Guarda a partida que este peer está participando
        self.partidas_encontradas: dict[
            str, dict[str, Any]
        ] = {}  # Guarda as partidas descobertas em outros peers

    # Gera a mensagem a ser enviada aos outros peers solicitando o GAME LIST
    def gerar_mensagem_GAMELIST(self) -> dict[str, Any]:
        # Limpa as partidas armazenadas encontradas, para não contecer uma mistura de partidas
        self.partidas_encontradas.clear()
        return {"type": "GAME_LIST"}

    # Resposta a ser enviada para a requisição GAME_LIST
    def GameList_Ok(self) -> dict[str, Any]:
        jogos: list[dict[str, Any]] = []
        # Verifica se uma partida está em FINISHED e se já passou seu periodo de retenção
        self.game_host.limpar_jogo()
        if self.game_host.game_id is not None:
            # Gera as informações necessárias para enviar
            jogo = {
                "game_id": self.game_host.game_id,
                "host": self.game_host.host_id,
                "status": self.game_host.game_state.name,
                "players": self.game_host.players.copy(),
                "max_players": self.game_host.max_players,
                "lives": self.game_host.forca.vidas,
                "word_length": len(self.game_host.forca.palavra),
            }
            # Adiciona o jogo na lista
            jogos.append(jogo)
        return {"type": "GAME_LIST_OK", "games": jogos}

    # Recebe as informações recebidas do GAME_LIST_OK
    def recebe_GAMELIST_Ok(self, mensagem: dict[str, Any]) -> bool:
        # Se o que foi recebido não é GAME_LIST, então nem olha
        if mensagem["type"] != "GAME_LIST_OK":
            return False

        # Percorre a lista de partidas
        for jogo in mensagem["games"]:
            host_id = jogo["host"]
            # Guarda a partida na variavel do peer
            self.partidas_encontradas[host_id] = jogo.copy()

        return True

    # Gera a mensagem de solicitação para entra em uma partida
    def mensagemJOIN(self, game_id: str) -> dict[str, Any]:
        return {"type": "JOIN", "game_id": game_id}

    # Aceita solicitação para entrar na partida
    def processar_JOIN(self, mensagem: dict[str, Any]) -> dict[str, Any]:
        game_id = mensagem["game_id"]
        player_id = mensagem["src"]

        # Se a partida não existe, retorna JOIN_ERR
        if self.game_host.game_id != game_id:
            mostrar_Host(f"Entrada de {player_id} recusada: jogo não encontrado")
            return {"type": "JOIN_ERR", "game_id": game_id, "reason": "unknown_game"}
        # Solicita a entrada ao GameHost
        resultado = self.game_host.adicionar_jogador(player_id)
        if resultado == "join_ok":
            mostrar_Host(f"{player_id} entrou na partida")
            mostrar_Host(f"Jogadores: ({len(self.game_host.players)}/{self.game_host.max_players})")
            return {
                "type": "JOIN_OK",
                "game_id": game_id,
                "players": self.game_host.players.copy(),
                "rejoin": False,
            }

        # Se for uma reconexão
        if resultado == "rejoin_ok":
            mostrar_Host(f"{player_id} reconectou-se à partida.")
            return {
                "type": "JOIN_OK",
                "game_id": game_id,
                "players": self.game_host.players.copy(),
                "rejoin": True,
            }
        else:
            erros_join = {
                "already_joined": "O jogador já está na partida.",
                "game_finished": "A partida já foi finalizada.",
                "game_full": "A partida está cheia.",
                "game_running": "A partida já está em andamento.",
                "game_not_open": "A partida não está aberta.",
            }
            mostrar_Host(f"Entrada de {player_id} recusada: {erros_join.get(resultado, resultado)}")
            return {"type": "JOIN_ERR", "game_id": game_id, "reason": resultado}

    # Sua solicitação para entrar na partida foi aprovada
    def recebe_JoinOk(self, mensagem: dict[str, Any]) -> bool:
        # Se a mensagem não for do tipo JOIN_OK, Faz nada
        if mensagem["type"] != "JOIN_OK":
            return False

        # Rejoin de jogador que o programa não fechou
        if mensagem["rejoin"]:
            # Se o game_id do jogador não for igual ao da mensagem, não era para ter recebido essa mensagem
            if mensagem["game_id"] != self.game_player.game_id:
                return False
            # Se o jogador não ta no estado playing, não entra
            if self.game_player.estado.name != "PLAYING":
                return False
            mostrar_Player("Reconexão com a partida realizada!")
            return True
        # Entrada normal
        sucesso = self.game_player.entrar_Partida(mensagem["game_id"], mensagem["src"])
        if sucesso:
            mostrar_Player(f"Você entrou na partida({self.game_player.game_id}) com sucesso!")
            mostrar_Player(f"Aguardando o host({self.game_player.host_id}) iniciar a partida...")

        return bool(sucesso)

    # Gera a mensagem de solicitação para sair em uma partida
    def mensagemLEAVE(self) -> dict[str, Any] | None:
        # Se o jogador não estiver jogando uma partida(não tem game_id), então não sai de nada
        if self.game_player.game_id is None:
            return None
        return {"type": "LEAVE", "game_id": self.game_player.game_id}

    def recebe_LeaveOK(self, mensagem: dict[str, Any]) -> bool:
        # Se a mensagem não for do tipo LEAVEOK ou o game_id não bater com o do game_player, não sai
        if mensagem["type"] != "LEAVE_OK" or mensagem["game_id"] != self.game_player.game_id:
            return False
        self.game_player.sair_jogo()
        mostrar_Player("Você saiu da partida com sucesso!")
        return True

    def processa_Leave(self, mensagem: dict[str, Any]) -> dict[str, Any] | None:
        # Se a mensagem não for LEAVE ou o game id do host não bate com o da mensagem, não faz nada
        if mensagem["type"] != "LEAVE" or mensagem["game_id"] != self.game_host.game_id:
            return None
        player_id = mensagem["src"]
        # O host exclui o jogador do jogo
        resultado = self.game_host.remover_jogador(player_id, "leave")
        # Se o jogador não foi removido com sucesso, então retorna nada
        if resultado != "Player_removed_successfully":
            return None

        # Retorna LEAVE_OK
        mostrar_Host(f"{player_id} saiu da partida")
        mostrar_Host(f"Jogadores: ({len(self.game_host.players)}/{self.game_host.max_players})")
        return {"type": "LEAVE_OK", "game_id": mensagem["game_id"]}

    # Processa o que aparece para o jogador ao receber um JOIN_ERR
    def recebe_JoinErr(self, mensagem: dict[str, Any]) -> bool:
        # Se não for do tipo join error, então faz nada
        if mensagem.get("type") != "JOIN_ERR":
            return False
        erros_join = {
            "unknown_game": "A partida não existe.",
            "already_joined": "Você já está na partida.",
            "game_finished": "A partida já foi finalizada.",
            "game_full": "A partida está cheia.",
            "game_running": "A partida já está em andamento.",
            "game_not_open": "A partida não está aberta.",
        }
        motivo = mensagem.get("reason", "unknown_error")
        mostrar_Player(f"Entrada recusada: {erros_join.get(motivo, motivo)}")

        return True
