import time
import secrets
from src.game.fsm.MaqEstadosJogo import MaqEstadosJogo
from src.network.rendezvous.importConfig.carregaConfig import carregaConfig
from src.game.forca.forca import Forca

class GameHost: 
    def __init__(self, host_id, config):
        self.host_id = host_id #Id do host, que é o mesmo id do jogador que criou o jogo
        self.game_id = None #Gera um id aleatório para o jogo

        self.game_state = MaqEstadosJogo.IDLE #Informa o estado do jogo, que começa como IDLE

        self.players = [] #Lista de jogadores no jogo por um id[nome@namespace]
        self.pontuacao = {} #dicionário de pontuação dos jogadores, onde a chave é o id do jogador e o valor é a pontuação

        self.max_players = config["max_players"] #Obtém o número máximo de jogadores do arquivo de configuração
        self.turno_timeout = config["turn_timeout"] #Obtém o tempo limite de turno do arquivo de configuração

        self.forca = None #Instância do jogo da forca, que será criada quando o jogo começar
        self.turno_atual = None #Id do jogador que está no turno atual, que será definido quando o jogo começar
        self.seq = 0 #Número de sequência do jogo, que será incrementado a cada jogada

    def criar_jogo(self, palavra, vidas):
        #Só cria um jogo se o estado atual for IDLE
        if self.game_state != MaqEstadosJogo.IDLE:
            return False
        self.game_id = f"{self.host_id}/{secrets.token_hex(4)}" #Gera um id aleatório para o jogo
        self.forca = Forca(palavra, vidas) #Cria uma instância do jogo da forca com a palavra e vidas fornecidas
        self.game_state = MaqEstadosJogo.OPEN #Muda o estado do jogo para OPEN, permitindo que jogadores se juntem
        return True

    def cancelar_jogo(self):
        #Só tem como cancelar o jogo que estiver no estado OPEN
        if self.game_state != MaqEstadosJogo.OPEN:
            return False
        self.game_state = MaqEstadosJogo.FINISHED #Muda o estado do jogo para FINISHED, encerrando o jogo
        self.forca = None #Remove a instância do jogo da forca
        self.game_state = MaqEstadosJogo.IDLE #Muda o estado do jogo para IDLE
        return True

    def adicionar_jogador(self, player_id, metodo):
        #Só tem como adicionar jogador se o estado atual for OPEN(JOIN) ou RUNNING(REJOIN)
        if self.game_state != MaqEstadosJogo.OPEN :
            return 'game_running' if self.game_state ==  MaqEstadosJogo.RUNNING else "game_not_open"
        #Se o número de jogadores for igual ao máximo permitido, não adiciona o jogador
        if len(self.players) >= self.max_players:
            return 'game_full'
        if player_id in self.players:
            return 'already_joined'
        #Adiciona o jogador à lista de jogadores
        self.players.append(player_id) 
        #Inicializa a pontuação do jogador como 0
        self.pontuacao[player_id] = 0
        return 'join_ok'

    def remover_jogador(self, player_id):
        #Removendo o jogador da lista de jogadores e do dicionário de pontuação
        if player_id in self.players:
            self.players.remove(player_id)
        return 'Player_removed_successfully'

    def iniciar_jogo(self):
        #Só inicia se tiver no estado OPEN e tiver pelo menos 1 jogador
        if self.game_state != MaqEstadosJogo.OPEN or len(self.players) == 0:
            return False
        self.game_state = MaqEstadosJogo.RUNNING #Muda o estado para running
        self.turno_atual = self.players[0] #Define o primeiro jogador da lista como o jogador do turno atual
        return True