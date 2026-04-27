def garantir_campo_icone(citacoes: list) -> list:
    for c in citacoes:
        if "icone_url" not in c:
            c["icone_url"] = None

    return citacoes


def remover_icones_do_modelo(citacoes: list) -> list:
    """
    Nunca confiar em icone_url vindo do modelo principal.
    O ícone deve ser preenchido apenas pela etapa própria de enriquecimento.
    """
    for c in citacoes:
        c["icone_url"] = None

    return citacoes


def limpar_caracteres_invalidos(texto: str) -> str:
    if not isinstance(texto, str):
        return texto

    substituicoes = {
        "\x13": "á",
        "\x1e": "ã",
        "\x1a3": "ó",
    }

    for ruim, bom in substituicoes.items():
        texto = texto.replace(ruim, bom)

    # remove caracteres de controle restantes
    texto = "".join(ch for ch in texto if ch.isprintable() or ch in ("\n", "\t"))

    return texto


def limpar_citacoes(citacoes: list) -> list:
    for c in citacoes:
        c["nome"] = limpar_caracteres_invalidos(c.get("nome", ""))
        c["texto"] = limpar_caracteres_invalidos(c.get("texto", ""))
        c["fonte"] = limpar_caracteres_invalidos(c.get("fonte", ""))
    return citacoes


def deduplicate(citacoes: list) -> list:
    vistos_texto = set()
    vistos_nome = set()
    unicas = []

    for c in citacoes:
        chave_texto = c.get("texto", "")[:80].strip()
        nome = c.get("nome", "").strip()

        if not chave_texto or not nome:
            continue

        if chave_texto not in vistos_texto and nome not in vistos_nome:
            vistos_texto.add(chave_texto)
            vistos_nome.add(nome)

            c["icone_url"] = None
            unicas.append(c)

    return unicas
