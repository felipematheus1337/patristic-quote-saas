import json
import re

# Fontes por tipo de padre
FONTES_PATRISTICAS = [
    "catenabible.com",
    "newadvent.org",
    "ccel.org",
    "documentacatholicaomnia.eu",
]

FONTES_MODERNAS_CATOLICAS = [
    "vatican.va",
    "papalencyclicals.net",
]

FONTES_MODERNAS_ORTODOXAS = [
    "orthodoxinfo.com",
    "orthodoxchurchquotes.com",
    "rocorstudies.org",
]

TODAS_FONTES_AUTORIZADAS = (
    FONTES_PATRISTICAS + FONTES_MODERNAS_CATOLICAS + FONTES_MODERNAS_ORTODOXAS
)

ALIASES = {
    "João Crisóstomo": "São João Crisóstomo",
    "Crisóstomo": "São João Crisóstomo",
    "Agostinho de Hipona": "Santo Agostinho de Hipona",
    "Santo Agostinho": "Santo Agostinho de Hipona",
    "Agostinho": "Santo Agostinho de Hipona",
    "Jerônimo": "São Jerônimo",
    "Tomás de Aquino": "São Tomás de Aquino",
    "Glossa Ordinária": None,  # None = filtrar fora
}


def normalizar_nomes(citacoes: list) -> list:
    normalizadas = []
    for c in citacoes:
        nome = c.get("nome", "")
        if nome in ALIASES:
            novo_nome = ALIASES[nome]
            if novo_nome is None:  # filtra Glossa Ordinária e similares
                continue
            c["nome"] = novo_nome
        normalizadas.append(c)
    return normalizadas


def extract_text_from_response(response) -> str:
    for block in response.output:
        if block.type == "message":
            for content in block.content:
                if content.type == "output_text":
                    return content.text
    return ""


def parse_response(text: str) -> list:
    if not text.strip():
        print("[AVISO] Resposta vazia do modelo.")
        return []

    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[ERRO] Falha ao parsear JSON: {e}")
        print(f"[DEBUG] Texto recebido:\n{text[:500]}")
        return []


def validar_fontes(citacoes: list) -> list:
    return [
        c
        for c in citacoes
        if c.get("confianca") in ("alta", "media")
        and c.get("texto")
        and c.get("fonte")
        and c.get("nome")
    ]


def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()
