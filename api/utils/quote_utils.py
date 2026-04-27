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
