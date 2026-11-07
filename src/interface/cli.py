import argparse
import shlex
import re
import random
from src.network.rendezvous.importConfig.carregaConfig import carregaConfig
from src.game.forca.gameHost import GameHost

class ParserCLI(argparse.ArgumentParser):
    #Evita que o argparse feche o programa ao encontrar um erro, e lança uma exceção ValueError
    def error(self, message):
        raise ValueError(message)
    #Evita que o argparse feche em comandos como --help/--version, e lança uma exceção ValueError
    def exit(self, status=0, message=None):
        if message:
            self._print_message(message)
        raise ValueError("Comando encerrado pelo parser")
    
#Cria as regras da CLI
def criar_parser():
    parser = ParserCLI(prog='PyP2P-Forca', add_help=False)
    #Cria os subcomandos, criando diferentes funções independentes
    comandos = parser.add_subparsers(dest="comando", required=True, parser_class=ParserCLI)
    #Comandos da CLI
    #/peers [* | #namespace]
    peers = comandos.add_parser("/peers", add_help=False)
    peers.add_argument("filtro", nargs="?")

    #/conn (sem argumentos) - Listar conexões ativas 
    conn = comandos.add_parser("/conn", add_help=False)

    #/rtt (sem argumentos) - Exibir RTT médio por peer
    rtt = comandos.add_parser("/rtt", add_help=False)

    #/reconnect (sem argumentos) - Forçar reconciliação imediata com o Rendezvous
    reconnect = comandos.add_parser("/reconnect", add_help=False)

    #/log <nivel> (sem argumentos) - Ajustar nível de log (DEBUG, INFO, WARNING, ERROR)
    log = comandos.add_parser("/log", add_help=False)
    log.add_argument('nivel', choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    #/create palavra [MAX_PLAYERS] ou  - Criar partida com a palavra informada/palavra sorteada de words.txt e tornar-se host
    create = comandos.add_parser("/create", add_help=False)
    create.add_argument('palavra', nargs="?")
    create.add_argument('max_players', nargs="?", type=int) #é opcional e do tipo int
    create.add_argument('--random', action="store_true")

    #/start (sem argumentos) - Iniciar a partida hospedada (exige ≥1 jogador)
    start = comandos.add_parser("/start", add_help=False)

    #/cancel (sem argumentos) - Cancelar a partida hospedada (OPEN ou RUNNING → ABORTED)
    cancel = comandos.add_parser("/cancel", add_help=False)

    #/games (sem argumentos) - Enviar GAME_LIST a todos os vizinhos e listar partidas abertas
    games = comandos.add_parser("/games", add_help=False)

    #/join <host_peer_id> - Entra na partida hospedada pelo peer indicado
    join = comandos.add_parser("/join", add_help=False)
    join.add_argument('host_peer_id')

    #/leave (sem argumentos) - Sai da partida atual
    leave = comandos.add_parser("/leave", add_help=False)

    #/guess <letra> - Palpite de letra 
    guess = comandos.add_parser("/guess", add_help=False)
    guess.add_argument('letra')

    #/word <palavra> - Palpite da palavra
    word = comandos.add_parser("/word", add_help=False)
    word.add_argument('palavra')

    #/status (sem argumentos) - Exibir estado local da partida (forca, letras, vidas, vez de quem)
    status = comandos.add_parser("/status", add_help=False)

    #/quit (sem argumentos) - Encerrar: LEAVE/GAME_OVER conforme o papel, BYE a todos, UNREGISTER
    quit = comandos.add_parser("/quit", add_help=False)

    #/help (sem argumentos) - Listar comandos
    help = comandos.add_parser("/help", add_help=False)

    return parser #Lista de regras da minha CLI

config = carregaConfig()
 #Cria meu conj. de regras
parser = criar_parser()

def interpretar_comando(comando):
    #Separa o que foi digitado
    partes = shlex.split(comando)
    #Rejeita entradas vazias(lista vazia)
    if len(partes) == 0:
        return None
    #Interpreta o que é comando e o que é argumento
    args = parser.parse_args(partes)

    #Validação de casos
    #Tratando os casos de /create
    if args.comando == '/create':
        #Se tiver digitado --random
        if args.random:
            #Não permite uma palavra junto com create
            if not args.palavra == None:
                #Como vc coloca /create --random 4, o 4 é considerado uma palavra, então a gente tem que mudar isso
                if args.palavra.isdigit() and args.max_players == None:
                    args.max_players = int(args.palavra)
                    args.palavra = None
                else:
                    raise ValueError("Use /create --random [max_players]")
            #Trata o caso de tentar usar o /create sem random e sem palavra
        #Não digitou --random
        else:
            #Não é permitido uma argumento sem palavra e --random
            if args.palavra == None:
                raise ValueError("Informe uma palavra ou utilize --random")
            else:
                if not 3<=len(args.palavra)<=20:
                    raise ValueError("A palavra deve ter entre 3 e 20 letras")
                #A palavra não pode conter dígitos
                if bool(re.search(r"\d", args.palavra)):
                    raise ValueError("A palavra não pode conter dígitos")
                #A palavra não pode ter - + ...
                if not re.fullmatch(r"[a-zA-Z]+", args.palavra):
                    raise ValueError("A palavra deve conter apenas letras de a até z")
        #Verificação da quantidade de jogadores permitidos 1<=max_players<=config['max_players']
        if args.max_players != None:
            if not 1<= args.max_players <= config['max_players']:
                raise ValueError(f"O número de jogadores deve estar entre 1 e {config['max_players']}")
            
    #Tratamento do comando /guess
    if args.comando == '/guess':
        #Para ser uma letra tem que ter comprimento 1 e não pode ser nada diferente de uma letra
        if len(args.letra) != 1 or not args.letra.isalpha():
            raise ValueError("Informe apenas uma letra")
        #Não permite letras acentuadas ou ç
        elif not 'a'<=args.letra.lower()<='z':
            raise ValueError("Palpite inválido")
        
    #Tratamento do comando /word
    if args.comando == '/word':
        #A palavra tem um tamanho de 3 até 20
        if not 3<=len(args.palavra)<=20:
             raise ValueError("O palpite deve ter entre 3 e 20 letras")
        #A palavra não pode conter dígitos
        if bool(re.search(r"\d", args.palavra)):
            raise ValueError("O palpite não pode conter dígitos")
        #A palavra não pode ter - + ...
        if not re.fullmatch(r"[a-zA-Z]+", args.palavra):
            raise ValueError("O palpite deve conter apenas letras de a até z")
        
    #Transforma em um dicionario
    return vars(args)

#Comando /help
def mostrar_ajuda():
    print("""
========== PyP2P-FORCA ==========

REDE:
  /peers [* | #namespace]  Lista os peers disponíveis
  /conn                   Lista conexões ativas
  /rtt                    Exibe o RTT médio dos peers
  /reconnect              Atualiza as conexões
  /log <nivel>             Define o nível do log

PARTIDAS:
  /create <palavra> [max_players]  Cria uma partida
  /create --random [max_players]   Cria com palavra aleatória
  /games                         Lista partidas disponíveis
  /join <host_peer_id>            Entra em uma partida
  /leave                         Sai da partida
  /start                         Inicia a partida
  /cancel                        Cancela a partida

JOGO:
  /guess <letra>           Envia um palpite de letra
  /word <palavra>          Envia um palpite de palavra
  /status                  Exibe o estado da partida

SISTEMA:
  /help                    Mostra esta ajuda
  /quit                    Encerra o programa

=================================
""")

def executar_comando(args,game_host,config):
    comando = args['comando']
    #Executar o /create
    if comando ==  '/create':
        #Se for --random
        if args['random']:
            #Pega uma palavra do arquivo word
            with open('words.txt', 'r', encoding='utf-8') as arquivo:
                conteudo = arquivo.read()
                list_palavra = conteudo.split()
                palavra = random.choice(list_palavra) #random choice para pegar uma palavra aleatoria
        else:
            palavra = args['palavra']

        sucesso = game_host.criar_jogo(palavra,config['lives'])
        if sucesso:
            print(f"Partida criada! ID: {game_host.game_id} palavra: {palavra}")
        else:
            print("Não foi possível criar a partida.")
    elif comando == '/start':
        sucesso = game_host.iniciar_jogo()
        if sucesso:
            print("Partida iniciada!")
        else:
            print("Não foi possível iniciar a partida.")
    elif comando == '/cancel':
        sucesso = game_host.cancelar_jogo()
        if sucesso:
            print("Partida cancelada!")
        else:
            print("Não foi possível cancelar a partida.")
            
#Mostra a TAG de game
def mostrar_Game(mensagem):
    print(f"[GAME] {mensagem}")