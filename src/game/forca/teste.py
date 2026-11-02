from .forca import *
from ...network.rendezvous.importConfig.carregaConfig import carregaConfig

jogo = Forca("banana", carregaConfig()["lives"])

print(jogo.tentar_letra("a"))   # True
print(jogo.tentar_letra("z"))   # False
print(jogo.tentar_letra("z"))   # letter_already_used
print(jogo.tentar_letra("5"))   # invalid_letter

print(jogo.tentar_palavra("ab"))       # invalid_word
print(jogo.tentar_palavra("morango"))  # False
print(jogo.tentar_palavra("banana"))   # True

print(jogo.vidas)  # 4