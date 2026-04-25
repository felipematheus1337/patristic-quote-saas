import asyncio
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

from openai import OpenAI
from dotenv import load_dotenv

from utils.helper import (
    extract_text_from_response,
    parse_response,
    load_prompt,
    validar_fontes,
)
from const import (
    PADRES_ALTA_COBERTURA,
    PADRES_MEDIA_COBERTURA,
)

load_dotenv()
client = OpenAI(timeout=30.0)  # ponto 3 — timeout global

BAIXA_ORTODOXOS_MODERNOS = [
    "São Serafim de Sarov",
    "São Paisios Velichkovsky",
    "São Teófano, o Recluso",
    "São Ignácio Brianchaninov",
    "São Paisios do Monte Athos",
    "São Porfirio de Kavsokalyvia",
    "São Silouano do Monte Athos",
    "Padre Seraphim Rose",
    "São Sophrônio de Essex",
    "São Serafim de Viritsa",
    "São Tikhon de Zadonsk",
    "São João de Kronstadt",
    "São João Maximovitch",
    "Patriarca Bartolomeu I de Constantinopla",
    "Metropolita Antônio Bloom",
    "Arcebispo Averky Taushev",
    "São João Paulo II",
    "Bento XVI (Cardeal Ratzinger)",
    "Cardeal Robert Sarah",
    "São Pio de Pietrelcina (Padre Pio)",
    "São Josemaría Escrivá",
    "Santa Teresa de Calcutá",
    "Santa Teresa d'Ávila",
    "São João da Cruz",
    "São Francisco de Sales",
    "São Afonso de Ligório",
]

BAIXA_OUTROS = [
    "São Macário do Egito",
    "São Macário de Alexandria",
    "São Antão do Deserto",
    "São Pacômio",
    "São Arsênio",
    "Padres do Deserto (Antão, Macário, Arsênio, etc.)",
    "São Justino Mártir",
    "Tertuliano",
    "São Policarpo de Esmirna",
    "São Gregório Taumaturgo",
    "São Metódio de Olimpo",
    "São Dídimo, o Cego",
    "Pseudo-Dionísio Areopagita",
    "São Simeão Estilita",
    "São Barsanúfio",
    "São Anfíloquio de Icônio",
    "São Epifânio de Salamina",
]


# ── ponto 3 — try/except isolado por candidato ──────────────────────────────
def buscar_citacao(passagem: str, padre: str, prompt: str) -> list:
    try:
        response = client.responses.create(
            model="gpt-4.1",
            tools=[{"type": "web_search_preview"}],
            input=prompt + f"\n\nPassagem: {passagem}\nSanto Padre: {padre}",
        )
        raw_text = extract_text_from_response(response)
        resultado = parse_response(raw_text)
        validado = validar_fontes(resultado)
        print(f"[OK] {padre} → {len(validado)} citação(ões)")
        return validado
    except Exception as e:
        print(f"[ERRO] {padre}: {e}")
        return []


def montar_fila(padre: str) -> list[str]:
    fila = [padre]

    alta = [p for p in PADRES_ALTA_COBERTURA if p not in fila]
    fila += random.sample(alta, min(3, len(alta)))

    media = [p for p in PADRES_MEDIA_COBERTURA if p not in fila]
    fila += random.sample(media, min(2, len(media)))

    baixa_mod = [p for p in BAIXA_ORTODOXOS_MODERNOS if p not in fila]
    fila += random.sample(baixa_mod, min(1, len(baixa_mod)))

    baixa_out = [p for p in BAIXA_OUTROS if p not in fila]
    fila += random.sample(baixa_out, min(1, len(baixa_out)))

    return fila[:8]


def deduplicate(citacoes: list) -> list:
    vistos_texto = set()
    vistos_nome = set()
    unicas = []
    for c in citacoes:
        chave_texto = c.get("texto", "")[:80].strip()
        nome = c.get("nome", "")
        if chave_texto not in vistos_texto and nome not in vistos_nome:
            vistos_texto.add(chave_texto)
            vistos_nome.add(nome)
            unicas.append(c)
    return unicas


# ── ponto 2 — paralelo com ThreadPoolExecutor ────────────────────────────────
def _buscar_em_paralelo(passagem: str, fila: list[str], prompt: str) -> list:
    citacoes = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(buscar_citacao, passagem, candidato, prompt): candidato
            for candidato in fila
        }
        for future in as_completed(futures):
            candidato = futures[future]
            try:
                resultado = future.result()
                citacoes.extend(resultado)
                print(f"[CONCLUÍDO] {candidato}")
            except Exception as e:
                print(f"[FUTURE ERRO] {candidato}: {e}")

            if len(citacoes) >= 5:
                break

    return citacoes


# ── ponto 1 — versão async para o FastAPI não bloquear o event loop ──────────
async def get_patristic_text(passagem: str, padre: str) -> list:
    prompt = load_prompt("prompts/search.md")
    fila = montar_fila(padre)

    print(f"[FILA] {fila}")

    loop = asyncio.get_event_loop()
    citacoes = await loop.run_in_executor(
        None, partial(_buscar_em_paralelo, passagem, fila, prompt)
    )

    return deduplicate(citacoes)[:5]
