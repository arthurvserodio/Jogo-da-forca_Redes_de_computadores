from .forca import Forca

def testar_forca():
    jogo = Forca("banana", 6)

    # TESTE 1 — Acertar a letra "a"
    print("\nTESTE 1 — Letra correta")
    resultado = jogo.tentar_letra("a")
    print("Resultado:", resultado)

    assert resultado["aceito"] is True
    assert resultado["correto"] is True
    assert resultado["pontuacao"] == 3
    print("TESTE 1 PASSOU!")

    # TESTE 2 — Tentar a mesma letra novamente
    print("\nTESTE 2 — Letra repetida")
    resultado = jogo.tentar_letra("a")
    print("Resultado:", resultado)

    assert resultado["aceito"] is False
    assert resultado["erro"] == "letter_already_used"
    print("TESTE 2 PASSOU!")

    # TESTE 3 — Acertar a palavra inteira
    print("\nTESTE 3 — Palavra correta")
    resultado = jogo.tentar_palavra("banana")
    print("Resultado:", resultado)

    assert resultado["aceito"] is True
    assert resultado["correto"] is True
    assert resultado["pontuacao"] == 3
    assert jogo.terminou is True
    assert jogo.vitoria is True
    print("TESTE 3 PASSOU!")

    # TESTE 4 — Tentar jogar depois da vitória
    print("\nTESTE 4 — Jogada após o encerramento")
    resultado = jogo.tentar_letra("z")
    print("Resultado:", resultado)

    assert resultado["aceito"] is False
    assert resultado["erro"] == "game_not_running"
    print("TESTE 4 PASSOU!")

    print("\nTODOS OS TESTES PASSARAM!")


if __name__ == "__main__":
    testar_forca()
