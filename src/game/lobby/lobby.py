from typing import Any


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
            return {"type": "JOIN_ERR", "game_id": game_id, "reason": "unknown_game"}
        # Solicita a entrada ao GameHost
        resultado = self.game_host.adicionar_jogador(player_id)
        if resultado == "join_ok":
            return {
                "type": "JOIN_OK",
                "game_id": game_id,
                "players": self.game_host.players.copy(),
                "rejoin": False,
            }

        # Se for uma reconexão
        if resultado == "rejoin_ok":
            return {
                "type": "JOIN_OK",
                "game_id": game_id,
                "players": self.game_host.players.copy(),
                "rejoin": True,
            }
        else:
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
            return True
        # Entrada normal
        return bool(self.game_player.entrar_Partida(mensagem["game_id"], mensagem["src"]))

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
        return {"type": "LEAVE_OK", "game_id": mensagem["game_id"]}
