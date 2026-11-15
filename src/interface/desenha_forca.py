def desenha_forca(erros: int) -> str:
    desenhos = [
        """
        +----+
        |    |
        |    
        |
        |
        |
      ==============
        """,
        """
        +----+
        |    |
        |    O
        |
        |
        |
        ==============
        """,
        """
        +----+
        |    |
        |    O
        |    |
        |
        |
        ==============
        """,
        r"""
        +----+
        |    |
        |    O
        |    |
        |     \
        |
        ==============
        """,
        r"""
        +----+
        |    |
        |    O
        |    |
        |   / \
        |
        ==============
        """,
        r"""
        +----+
        |    |
        |    O
        |    |\
        |   / \
        |
        ==============
        """,
        r"""
        +----+
        |    |
        |    O
        |   /|\
        |   / \
        |
        ==============
        """,
    ]
    # Protege de acessar uma posição invalida da lista, visto que pode ser alterado o numero de vidas no config
    return desenhos[max(0, min(erros, len(desenhos) - 1))]
