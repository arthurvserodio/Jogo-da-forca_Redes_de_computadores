from .palavra import normalizando_word, valida_word
from .jogada import *

class Forca:
    def __init__(self, palavra,vidas):
        #Valida palavra secreta
        if not valida_word(normalizando_word(palavra)):
            raise ValueError("Palavra secreta inválida")

       #Guarda a palavra normalizada
        self.palavra = normalizando_word(palavra) #Palavra secreta normalizada
        self.vidas = vidas #Quantidade de vidas
        self.letras_usadas = set() #Letras já usadas
        self.letras_certas = set() #Letras que os jogadores acertaram
        self.terminou = False #Indica se o jogo terminou ou não
        self.vitoria = False #Indica se os jogadores venceram

    #GUESS LETRA
    def tentar_letra(self,letra):
        #Se o jogo já terminou, não pode mais jogar
        if self.terminou:
            return {
                "aceito": False,
                "erro": "game_not_running",
            }
        #Normaliza a letra
        letra = normalizando_word(letra)
        #Valida a tentativa
        erro = validade_palpite(letra,self.letras_usadas)
        #Se deu errado, retorna falso
        if erro is not None:
            return {
                "aceito": False,
                "erro": erro,
            }
        #Adiciona a letra a lista de usadas
        self.letras_usadas.add(letra)
        #Se o palpite está na palavra, então a letra vai para a lista de acerto
        if letra in self.palavra:
            self.letras_certas.add(letra)
            self.resultado_jogo()
            return {
                "aceito": True,
                "correto": True,
                "pontuacao": self.pontuacao_gerada_letra(letra),
            }
        #Se não estiver na palavra, então perde 1 de vida
        else:
            self.vidas-=1
            self.resultado_jogo()
            return {
                "aceito": True,
                "correto": False,
                "pontuacao": 0,
            }
        
    #GUESS PALAVRA
    def tentar_palavra(self,palavra):
        #Se o jogo já terminou, não pode mais jogar
        if self.terminou:
            return {
                "aceito": False,
                "erro": "game_not_running",
            }
        #Normaliza a letra
        palavra = normalizando_word(palavra)
        #Valida a tentativa
        erro = validade_palpite(palavra,self.letras_usadas)
        #Se deu errado, retorna falso
        if erro is not None:
            return {
            "aceito": False,
            "erro": erro,
        }
        #Se o palpite de palavra é a palavra secreta, retorna True
        if palavra == self.palavra:
            pontos = self.pontuacao_gerada_palavra() #Calcula a pontuação
            self.letras_certas.update(palavra) #Coloca todas as letras da palavra certa no set
            self.resultado_jogo()
            return {
            "aceito": True,
            "correto": True,
            "pontuacao": pontos,
            }
        #Se não for a palavra certa, então perde 1 de vida
        else:
            self.vidas-=1
            self.resultado_jogo()
            return {
                "aceito": True,
                "correto": False,
                "pontuacao": 0,
            }

    #Verificar o resultado do jogo
    def resultado_jogo(self):
        #Verifica se as vidas acabaram
        if self.vidas <= 0:
            self.terminou=True #O jogo termina
            self.vitoria= False #Perdeu
        #Verifica se todas as letras certas, estão na palavra, então venceu
        elif all(letra in self.letras_certas for letra in self.palavra):
            self.terminou=True #O jogo termina
            self.vitoria= True #Venceu
        return self.terminou

    #Verifica quantos pontos a jogada de palavra fez
    def pontuacao_gerada_palavra(self):
        pontos = 0
        #Cada letra revelada pela palavra vale 1 ponto
        for letra in self.palavra:
            if letra not in self.letras_certas:
                pontos+=1
        return pontos
    #Verifica quantos pontos a jogada de letra fez
    def pontuacao_gerada_letra(self,letra_palpite):
        pontos = 0
        #Cada letra revelada pela letra vale 1 ponto
        for letra in self.palavra:
            #
            if letra == letra_palpite:
                pontos+=1
        return pontos