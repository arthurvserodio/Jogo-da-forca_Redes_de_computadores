from .palavra import normalizando_word, valida_word
#Verifica se o palpite que coloquei pode
def validade_palpite(string, letras_usadas):
    #Normaliza o digitado
    string = normalizando_word(string)
    #Se o tamanho da string for 1, a gente confere o comportamento de letra
    if len(string) == 1:
        #A letra tem que estar entre a até z, se não estiver, não é válido
        if not 'a' <= string <= 'z':
            return 'invalid_letter'
        #Se a gente já usou aquela letra como palpite, a gente avisa
        if string in letras_usadas:
            return 'letter_already_used'
    #Tamanho > 1, comportamento de palavra
    else:
        #Verifica se a palavra é valida
        if not valida_word(string):
            return 'invalid_word'
    return None
