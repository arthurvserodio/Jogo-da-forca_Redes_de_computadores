from unidecode import unidecode
#Normalizando a palavra
def normalizando_word(palavra):
    palavra = palavra.lower() #Transforma a palavra em letra minuscula
    palavra = unidecode(palavra) #Tira a acentuação da palavra
    return palavra
#Valida a palavra
def valida_word(palavra):
    #Se a palavra tiver menos de 3 letras, mais de 20, tiver hífen ou espaço, ela é inaválida
    if len(palavra) < 3 or len(palavra) > 20 or '-' in palavra or ' ' in palavra:
        return False
    #Não pode haver números, só pode ter caracteres entre a e z
    if not all('a' <= letra <= 'z' for letra in palavra):
        return False
    return True
#Mascara para a palavra
def mask(palavra,letras_certas):
    mascara = ''
    for letra in palavra:
        if letra in letras_certas:
            mascara += letra.lower()
        else:
            mascara += '_'
        mascara+= ' '
    return mascara