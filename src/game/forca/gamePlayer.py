import hashlib
from typing import TypedDict

from src.game.fsm.MaqEstadosJogador import MaqEstadosJogadores


class GameStartMessage(TypedDict):
    game_id: str
    players: list[str]
    lives: int
    word_hash: str
    word_length: int


class StateMessage(TypedDict):
    game_id: str
    seq: int
    masked: str
    wrong_letters: list[str]
    lives: int
    turn: str | None
    players: list[str]
    last_guess: dict[str, object] | None


class GameOverMessage(TypedDict):
    game_id: str
    word: str
    result: str
    winner: str | None
    scores: dict[str, int]


class GamePlayer:
    def __init__(self, player_id: str) -> None:
        # ATRIBUTOS
        self.player_id = player_id

        # Jogo que entrou
        self.host_id: str | None = None  # Guarda quem é o host da partida
        self.game_id: str | None = None  # Guarda o id da partida que está participoando

        # Estado do jogador
        self.estado = MaqEstadosJogadores.IDLE  # Ele inicia no estado IDLE

        # Informações que recebe do jogo
        self.players: list[str] = []  # Guarda quem está jogando a partida
        self.vidas: int | None = None  # Guarda quantas vidas tem
        self.tam_word = 0  # Guarda o tamanho da palavra secreta
        self.hash_word: str | None = None  # Guarda a o hash da palavra para conferir no final
        self.mask_word: str | None = None  # Guarda o estado da palavra que está ttentando adivinhar
        self.letras_erradas: list[str] = []  # Guarda as letras que tentaram e tava errado
        self.turno: str | None = None  # Guarda de quem é o turno

        # Controle de atualização
        self.seq = 0
        self.ultimaJogada: dict[str, object] | None = None  # Guarda a última jogada realizada

        # Informações finais
        self.resultado: str | None = None  # Guarda o resultado da partida -> WON, LOST e ABORTED
        self.vencedor: str | None = None  # Guarda quem acertou a palavra
        self.pontuacao = 0  # Guarda a pontuação

    # Registra a entrada em uma partida
    def entrar_Partida(self, game_id: str, host_id: str) -> bool:
        # Se o estado do jogador não for IDLE, então retorna
        if self.estado != MaqEstadosJogadores.IDLE:
            return False

        # Limpa os dados da partida anterior
        self.limpar_jogo()
        # Pega as informações da partida que quer entrar
        self.game_id = game_id
        self.host_id = host_id
        self.estado = MaqEstadosJogadores.JOINED

        return True

    # Recebe informações vindas da mensagem GAME_START do host
    def receber_gameStart(self, mensagemHost: GameStartMessage) -> bool:
        # Se o jogador não estiver no estado JOIN, então essa mensagem não é para ele
        if self.estado != MaqEstadosJogadores.JOINED:
            return False
        # Se o game_id da mensagem não bate com o do jogador, então a mensagem também não é para ele
        if self.game_id != mensagemHost["game_id"]:
            return False
        # Recebe todas as informações da mensagem GAME_START
        self.players = mensagemHost["players"].copy()
        self.vidas = mensagemHost["lives"]
        self.hash_word = mensagemHost["word_hash"]
        self.tam_word = mensagemHost["word_length"]
        self.mask_word = "_" * self.tam_word
        self.estado = MaqEstadosJogadores.PLAYING

        return True

    # Atualiza seus dados de acordo com o STATE recebido
    def atualizaState(self, mensagemHost: StateMessage) -> bool:
        # Se o jogador não estiver jogando, ele não atualiza seu estado
        if self.estado != MaqEstadosJogadores.PLAYING:
            return False
        # Verifica se a mensagem é do jogo em que estou jogando
        if self.game_id != mensagemHost["game_id"]:
            return False
        # Ignora estados antigos ou repetidos que chagaram depois de já ter recebido
        if self.seq >= mensagemHost["seq"]:
            return False
        # Recebe todas as informações provenientes da mensagem STATE
        self.seq = mensagemHost["seq"]
        self.mask_word = mensagemHost["masked"]
        self.letras_erradas = mensagemHost["wrong_letters"].copy()
        self.vidas = mensagemHost["lives"]
        self.turno = mensagemHost["turn"]
        self.players = mensagemHost["players"].copy()
        # Só guarda a última jogada se ela não for None
        if mensagemHost["last_guess"] is not None:
            self.ultimaJogada = mensagemHost["last_guess"]
        else:
            self.ultimaJogada = None

        return True

    # Gera a mensagem de GUESS
    def gerar_guess(self, palpite: str) -> dict[str, str] | None:
        # Se o jogador não estiver jogando, então não tem guess
        if self.estado != MaqEstadosJogadores.PLAYING:
            return None
        # Se não é o turno do jogador, também não tem guess
        if self.turno != self.player_id:
            return None

        if self.game_id is None:
            return None

        if len(palpite) == 1:
            return {"type": "GUESS", "game_id": self.game_id, "letter": palpite}
        else:
            return {"type": "GUESS", "game_id": self.game_id, "word": palpite}

    # Recebe informações vindas da mensagem GAME_OVER do host
    def receber_gameOver(self, mensagemHost: GameOverMessage) -> bool | str:
        # Se o jogador não estiver no estado JOIN, então essa mensagem não é para ele
        if self.estado != MaqEstadosJogadores.PLAYING:
            return False
        # Se o game_id da mensagem não bate com o do jogador, então a mensagem também não é para ele
        if self.game_id != mensagemHost["game_id"]:
            return False
        # Calcula o hash da palavra secreta
        hash_palavraOriginal = hashlib.sha256(mensagemHost["word"].encode("utf-8")).hexdigest()
        # Confere se a palavra original é igual a palvara no final do jogo, se não for, o host roubou
        if self.hash_word != hash_palavraOriginal:
            return "host cheated: hash mismatch"
        # Recebe todas as informações da mensagem GAME_OVER
        self.resultado = mensagemHost["result"]
        self.vencedor = mensagemHost["winner"]
        self.pontuacao = mensagemHost["scores"][self.player_id]
        # Retorna para IDLE
        self.estado = MaqEstadosJogadores.IDLE

        return True

    # Saída do jogo limpa o estado do jogador
    def limpar_jogo(self) -> bool:
        self.host_id = None
        self.game_id = None

        # Estado do jogador
        self.estado = MaqEstadosJogadores.IDLE

        # Informações que recebe do jogo
        self.players = []
        self.vidas = None
        self.tam_word = 0
        self.hash_word = None
        self.mask_word = None
        self.letras_erradas = []
        self.turno = None

        # Controle de atualização
        self.seq = 0
        self.ultimaJogada = None

        # Informações finais
        self.resultado = None
        self.vencedor = None
        self.pontuacao = 0

        return True

    # Limpa o estado do jogador
    def sair_jogo(self) -> bool:
        return self.limpar_jogo()
