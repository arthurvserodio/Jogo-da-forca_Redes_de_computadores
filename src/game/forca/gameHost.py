import hashlib
import secrets
import time
from copy import deepcopy

from src.config.types import ConfigJogo
from src.game.forca.forca import Forca
from src.game.forca.palavra import mask
from src.game.fsm.MaqEstadosJogo import MaqEstadosJogo


class GameHost:
    def __init__(self, host_id: str, config: ConfigJogo) -> None:
        self.host_id = host_id  # Id do host, que é o mesmo id do jogador que criou o jogo
        self.game_id: str | None = None  # Gera um id aleatório para o jogo

        self.game_state = MaqEstadosJogo.IDLE  # Informa o estado do jogo, que começa como IDLE

        self.players: list[str] = []  # Lista de jogadores no jogo por um id[nome@namespace]
        self.jogadores_desconectados: set[str] = set()  # Jogadores que cairam do jogo
        self.pontuacao: dict[
            str, int
        ] = {}  # dicionário de pontuação dos jogadores, onde a chave é o id do jogador e o valor é a pontuação

        self.max_playersConfig = config[
            "max_players"
        ]  # Obtém o número máximo de jogadores do arquivo de configuração
        self.max_players = self.max_playersConfig  # Max players selecionado pelo host
        self.turno_timeout = config[
            "turn_timeout"
        ]  # Obtém o tempo limite de turno do arquivo de configuração

        self.forca: Forca | None = (
            None  # Instância do jogo da forca, que será criada quando o jogo começar
        )
        self.turno_atual: str | None = (
            None  # Id do jogador que está no turno atual, que será definido quando o jogo começar
        )
        self.seq = 0  # Número de sequência do jogo, que será incrementado a cada jogada

        self.resultado: str | None = None  # Guarda o resultado do jogo(WON,LOST ou ABORTED)
        self.fim_em: float | None = None  # Guarda quando o jogo terminou
        self.inicio_turno: float | None = None  # Guarda quando começou o turno

        self.ultima_jogada: dict[str, object] | None = None  # Guarda a última jogada já feita

        self.vencedor: str | None = None  # Guarda a pessoa que fez a jogada da vitória
        self.motivo_fim: str | None = None  # Qual foi o motivo do fim quando abortou
        self.ultimo_estado: dict[str, object] | None = None  # Guarda o ultimo estado gerado

    def criar_jogo(
        self, palavra: str, vidas: int, max_players: int | None = None
    ) -> dict[str, bool | str]:
        # Verifica se uma partida antiga já pode ser limpa
        self.limpar_jogo()
        # Só cria um jogo se o estado atual for IDLE
        if self.game_state != MaqEstadosJogo.IDLE:
            return {
                "aceito": False,
                "mensagem": "Já existe uma partida ativa ou aguardando encerramento.",
            }
        # Verifica a quantidade máxima de jogadores
        if max_players is None:
            self.max_players = self.max_playersConfig
        # Verifica se max_players passado é int
        elif type(max_players) is not int:
            return {"aceito": False, "mensagem": "O max_players informado não é um inteiro"}
        else:
            # Se o max players digitado pelo host não estiver entre 1 e a quantidade maxima prevista nas configurações, não pode criar a partida
            if not 1 <= max_players <= self.max_playersConfig:
                return {
                    "aceito": False,
                    "mensagem": "O max_players informado é menor que 1 ou maior que o limite máximo estabelecido pelas configurações",
                }
            self.max_players = max_players
        self.forca = Forca(
            palavra, vidas
        )  # Cria uma instância do jogo da forca com a palavra e vidas fornecidas
        self.game_id = f"{self.host_id}/{secrets.token_hex(4)}"  # Gera um id aleatório para o jogo
        self.game_state = (
            MaqEstadosJogo.OPEN
        )  # Muda o estado do jogo para OPEN, permitindo que jogadores se juntem
        return {"aceito": True, "mensagem": "Partida criada com sucesso!"}

    def cancelar_jogo(self) -> bool:
        # Só tem como cancelar o jogo que estiver no estado OPEN ou RUNNING
        if self.game_state != MaqEstadosJogo.OPEN and self.game_state != MaqEstadosJogo.RUNNING:
            return False
        self.resultado = "ABORTED"  # Aborta o jogo
        self.motivo_fim = "host_shutdown"
        self.fim_em = time.monotonic()  # Guarda quando aconteceu o fim
        self.game_state = MaqEstadosJogo.FINISHED  # Estado do jogo vai para finalizado
        return True

    def adicionar_jogador(self, player_id: str) -> str:
        # Verifica se o jogador já entrou na partida
        if player_id in self.players:
            return "already_joined"
        # Se o jogo estiver em FINISHED, ele retorna game_finished
        if self.game_state == MaqEstadosJogo.FINISHED:
            return "game_finished"
        # Se o jogo estiver em OPEN, a gente pode adicionar
        if self.game_state == MaqEstadosJogo.OPEN:
            # Se o número de jogadores for igual ao máximo permitido, não adiciona o jogador
            if len(self.players) >= self.max_players:
                return "game_full"
            # Adiciona o jogador à lista de jogadores
            self.players.append(player_id)
            # Inicializa a pontuação do jogador como 0
            self.pontuacao[player_id] = 0
            return "join_ok"
        # Se o jogo esta em andamento, permite reconexão
        elif self.game_state == MaqEstadosJogo.RUNNING:
            if player_id not in self.jogadores_desconectados:
                return "game_running"
            # Readiciona o jogador à lista de jogadores
            self.players.append(player_id)
            # Retira o jogador do set de jogadores desconectados
            self.jogadores_desconectados.remove(player_id)
            # Gera um novo estado quando um pessoa dá um rejoin
            self.gerar_estado()
            return "rejoin_ok"
        # Se não ta no estado de OPEN ou RUNNING, então o jogo não está aberto
        return "game_not_open"

    def remover_jogador(self, player_id: str, motivo: str = "leave") -> str:
        # Removendo o jogador da lista de jogadores e do dicionário de pontuação
        if player_id not in self.players:
            return "player_not_found"

        # Guarda o indice de quem foi removido
        indice = self.players.index(player_id)
        # Verifica se era a vez do jogador
        era_sua_vez = self.turno_atual == player_id
        # Remove o jogador
        self.players.remove(player_id)
        # Se o motivo da saída do jogo foi uma desconexão, então ele entra no set de jogadores desconectados
        if motivo == "disconnect" and self.game_state == MaqEstadosJogo.RUNNING:
            self.jogadores_desconectados.add(player_id)

        # Se o jogo não tiver iniciado, tira ele da pontuação
        if self.game_state == MaqEstadosJogo.OPEN:
            self.pontuacao.pop(player_id)
            return "Player_removed_successfully"
        # Se já tiver começado, e
        elif self.game_state == MaqEstadosJogo.RUNNING:
            # Se não sobrou ninguém na partida
            if len(self.players) == 0:
                self.turno_atual = None
                # Motivo de ter finalizado foi que todos saíram da partida
                self.motivo_fim = "no_players"
                self.finalizar_jogo("ABORTED")
                return "Player_removed_successfully"
            # Se era a vez do jogador que caiu ou saiu da partida
            if era_sua_vez:
                # Se o jogador que saiu era o último, ou seja, após a remoção o indice dele ficou maior que o tamanho da lista
                if indice >= len(self.players):
                    self.turno_atual = self.players[0]
                    self.inicio_turno = time.monotonic()
                # Se não for o último, então o próximo ta com o mesmo indice do que foi removido
                else:
                    self.turno_atual = self.players[indice]
                    self.inicio_turno = time.monotonic()
            # Gera um estado quando um jogador sai da partida em andamento
            self.gerar_estado()

        return "Player_removed_successfully"

    def iniciar_jogo(self) -> dict[str, bool | str]:
        # Só inicia se tiver no estado OPEN e tiver pelo menos 1 jogador
        if self.game_state != MaqEstadosJogo.OPEN or len(self.players) == 0:
            return {"aceito": False, "mensagem": "A partida não está aberta ou n° de jogadores é 0"}
        self.game_state = MaqEstadosJogo.RUNNING  # Muda o estado para running
        self.turno_atual = self.players[
            0
        ]  # Define o primeiro jogador da lista como o jogador do turno atual
        self.inicio_turno = time.monotonic()
        self.gerar_estado()  # Gera o estado
        return {"aceito": True, "mensagem": "Partida iniciada!"}

    # Obter o status do jogo
    def obter_status(self) -> dict[str, object] | None:
        # Verifica se existe um jogo
        if self.game_id is None:
            return None

        # Se tem o jogo, retorna várias coisas
        if self.game_state == MaqEstadosJogo.OPEN:
            return {
                "game_id": self.game_id,
                "estado": self.game_state.name,
                "jogadores": self.players.copy(),
                "max_players": self.max_players,
            }
        elif self.game_state == MaqEstadosJogo.RUNNING:
            if self.forca is None:
                return None
            return {
                "game_id": self.game_id,
                "host_id": self.host_id,
                "palavra_mask": mask(self.forca.palavra, self.forca.letras_certas),
                "estado": self.game_state.name,
                "jogadores": self.players.copy(),
                "vidas": self.forca.vidas,
                "letras_erradas": self.forca.letras_erradas.copy(),
                "turno_atual": self.turno_atual,
            }
        return {"game_id": self.game_id, "estado": self.game_state.name}

    # Finaliza o jogo
    def finalizar_jogo(self, resultado: str) -> bool:
        # Só é necessario finalizar o jogo se ele estiver em andamento
        if self.game_state != MaqEstadosJogo.RUNNING:
            return False
        # Verificando o resultado
        if resultado not in ("WON", "LOST", "ABORTED"):
            return False

        # Muda o resultado do gamehost
        self.resultado = resultado
        # Registra quando terminou
        self.fim_em = time.monotonic()
        # Muda o estado da partida
        self.game_state = MaqEstadosJogo.FINISHED
        return True

    # Próximo jogador a jogar
    def proximo_turno(self) -> None:
        # Se não tiver jogador na lista, não tem próximo
        if not self.players:
            self.turno_atual = None
            return
        if self.turno_atual not in self.players:
            self.turno_atual = self.players[0]
            self.inicio_turno = time.monotonic()
            return

        # Pega o indice do jogador atual:
        indice_atual = self.players.index(self.turno_atual)
        # Se o jogador atual for o último da lista, volta ao inicio
        if indice_atual == (len(self.players) - 1):
            proximo = 0
        # Se não for o último, vai para o próximo
        else:
            proximo = indice_atual + 1

        self.turno_atual = self.players[proximo]
        self.inicio_turno = time.monotonic()

    # Função para limpar meu jogo e voltar ao estado inicial
    def limpar_jogo(self) -> bool:
        # Se o jogo não estiver no estado FINISHED, então não faz nada
        if self.game_state != MaqEstadosJogo.FINISHED:
            return False
        if self.fim_em is None:
            return False
        # Se não tiver passado 60 seg, também não faz nada
        if time.monotonic() - self.fim_em < 60:
            return False

        # Limpando os dados da partida anterior
        self.game_id = None
        self.forca = None
        self.players = []
        self.pontuacao = {}
        self.turno_atual = None
        self.seq = 0
        self.resultado = None
        self.fim_em = None
        self.vencedor = None
        self.motivo_fim = None
        self.ultima_jogada = None
        self.inicio_turno = None
        self.jogadores_desconectados = set()
        self.ultimo_estado = None
        self.max_players = self.max_playersConfig
        # Retorna para o estado inicial da maq de estados
        self.game_state = MaqEstadosJogo.IDLE

        return True

    # Processa a jogada feita pelo jogador
    def processar_jogada(
        self, player_id: str, tipo: str, palpite: str
    ) -> dict[str, bool | str | int]:
        # Se o jogo não ta rodando então não pode dá um palpite
        if self.game_state != MaqEstadosJogo.RUNNING:
            return {"aceito": False, "erro": "game_not_running"}
        # Verifica se a forca foi criada
        if self.forca is None:
            return {"aceito": False, "erro": "game_not_running"}
        # Verifica se aquele jogador está na partida
        if player_id not in self.players:
            return {"aceito": False, "erro": "not_in_game"}
        # Verifica se é a vez do jogador
        if player_id != self.turno_atual:
            return {"aceito": False, "erro": "not_your_turn"}
        # Verifica se o tempo do jogador terminou
        jogador_timeout = self.verifica_timeout()
        if jogador_timeout is not False:
            return {"aceito": False, "erro": "not_your_turn"}
        # Identificando o palpite
        if tipo == "letter":
            resultado = self.forca.tentar_letra(palpite)
        elif tipo == "word":
            resultado = self.forca.tentar_palavra(palpite)
        else:
            return {"aceito": False, "erro": "invalid_guess_type"}

        # Atribuindo pontuação e vendo se terminou
        # Se o palpite não foi aceito pela forca, retorna isso
        if not resultado["aceito"]:
            return resultado

        # Registra somente a jogada aceita
        self.ultima_jogada = {
            "player": player_id,
            tipo: palpite.lower(),
            "correct": resultado["correto"],
        }

        # Atribuindo pontuação e vendo se terminou
        # Somando a pontuação
        pontos = resultado["pontuacao"]
        if not isinstance(pontos, int):
            return {"aceito": False, "erro": "invalid_score"}
        self.pontuacao[player_id] += pontos
        # Se o jogo terminou, a gente verifica se houve vitoria ou derrota
        if self.forca.terminou:
            if self.forca.vitoria:
                self.vencedor = player_id
                self.finalizar_jogo("WON")
            else:
                self.finalizar_jogo("LOST")
        # Se não terminou, passa o próximo turno
        else:
            self.proximo_turno()

        # Como o finalizar jogo pode alterar o estado do jogo, então tem que verificar se ta no estado RUNNING
        if self.game_state == MaqEstadosJogo.RUNNING:
            self.gerar_estado()
        return resultado

    def verifica_timeout(self) -> str | bool:
        # Verifica se o jogo está em andamento
        if self.game_state != MaqEstadosJogo.RUNNING:
            return False
        # Verifica se tem um turno ativo
        if self.turno_atual is None or self.inicio_turno is None:
            return False
        # Calcula quanto tempo passou
        tempo_transcorrido = time.monotonic() - self.inicio_turno
        # Se ainda não chegou no timeout ainda tem tempo
        if tempo_transcorrido < self.turno_timeout:
            return False
        # Quem perdeu o turno?
        jogador_timeout = self.turno_atual
        # Passa o turno
        self.proximo_turno()
        # Última jogada gerou timeOut
        self.ultima_jogada = {"player": jogador_timeout, "timeout": True}
        # Gera um novo state
        self.gerar_estado()
        return jogador_timeout

    # Gerar o STATE
    def gerar_estado(self) -> dict[str, object] | None:
        # Se o jogo não estiver em andamento, não precisa de STATE
        if self.game_state != MaqEstadosJogo.RUNNING:
            return None
        if self.forca is None:
            return None
        # Incrementa o num de sequencia
        self.seq += 1
        # Faz a mascara da palavra
        palavra_mask = mask(self.forca.palavra, self.forca.letras_certas)
        estado: dict[str, object] = {
            "game_id": self.game_id,
            "seq": self.seq,
            "masked": palavra_mask.replace(" ", ""),
            "wrong_letters": self.forca.letras_erradas.copy(),
            "lives": self.forca.vidas,
            "turn": self.turno_atual,
            "players": self.players.copy(),
            "last_guess": (self.ultima_jogada.copy() if self.ultima_jogada is not None else None),
        }
        self.ultimo_estado = estado
        return self.ultimo_estado

    # Gerar pega o ultimo estado sem incrementar o STATE
    def obter_UltimoEstado(self) -> dict[str, object] | None:
        # Se não existe ultimo estado, então retorna nada
        if self.ultimo_estado is None:
            return None
        return deepcopy(self.ultimo_estado)

    # Gera GAME_START
    def gerar_gameStart(self) -> dict[str, object] | None:
        # Só gera o estado se o jogo estiver em andamento
        if self.game_state != MaqEstadosJogo.RUNNING:
            return None
        if self.forca is None:
            return None
        # palavra já normalizada
        palavra = self.forca.palavra
        # Calcula o SHA-256 da palavra secreta
        word_hash = hashlib.sha256(palavra.encode("utf-8")).hexdigest()
        return {
            "game_id": self.game_id,
            "players": self.players.copy(),
            "lives": self.forca.vidas,
            "word_length": len(palavra),
            "word_hash": word_hash,
            "turn_timeout": self.turno_timeout,
        }

    # Gera GAME_OVER, de RUNNING -> FINISHED
    def gerar_gameOver(self) -> dict[str, object] | None:
        # Só gera o estado se o jogo estiver em andamento
        if self.game_state != MaqEstadosJogo.FINISHED:
            return None
        if self.forca is None:
            return None
        return {
            "type": "GAME_OVER",
            "game_id": self.game_id,
            "result": self.resultado,
            "word": self.forca.palavra,
            "winner": self.vencedor,
            "scores": self.pontuacao.copy(),
            **(
                {"reason": self.motivo_fim}
                if self.resultado == "ABORTED" and self.motivo_fim is not None
                else {}
            ),
        }

    # Gera GUESS
    def gerar_guessResult(
        self,
        resultado: dict[str, bool | str | int],
    ) -> dict[str, object]:
        # Se a jogada foi recusada então:
        if not resultado["aceito"]:
            return {
                "type": "GUESS_RESULT",
                "game_id": self.game_id,
                "accepted": False,
                "reason": resultado["erro"],
            }
        # Se a jogada foi processada retorna isso:
        return {
            "type": "GUESS_RESULT",
            "game_id": self.game_id,
            "accepted": True,
            "correct": resultado["correto"],
        }
