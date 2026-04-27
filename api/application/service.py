import asyncio
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import redis.asyncio as redis
import json
import os
import re
import httpx
from urllib.parse import urlparse

from infra.openai_client import client

from utils.helper import (
    extract_text_from_response,
    load_prompt,
    validar_fontes,
    normalizar_nomes,
)

from const import (
    PADRES_ALTA_COBERTURA,
    PADRES_MEDIA_COBERTURA,
)


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


FONTES_IMAGEM_PRIORITARIAS = [
    "upload.wikimedia.org",
    "orthodoxwiki.org",
    "oca.org",
    "goarch.org",
    "antiochian.org",
    "pravoslavie.ru",
    "holytrinityorthodox.com",
]

EXTENSOES_IMAGEM_VALIDAS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".JPG",
    ".JPEG",
    ".PNG",
    ".WEBP",
)

USER_AGENT = (
    "patristic-quote-saas/1.0 " "(local development; contact: example@example.com)"
)


redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)

CACHE_TTL = 60 * 60 * 24 * 30


def _build_cache_key(passagem: str, padre: str) -> str:
    passagem_norm = (
        passagem.lower().strip().replace(" ", "_").replace(":", "_").replace("-", "_")
    )

    padre_norm = (
        padre.lower()
        .strip()
        .replace(" ", "_")
        .replace("ã", "a")
        .replace("õ", "o")
        .replace("ô", "o")
        .replace("ó", "o")
        .replace("í", "i")
        .replace("á", "a")
        .replace("à", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("ç", "c")
    )

    return f"patristic:{passagem_norm}:{padre_norm}"


def _dominio_da_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _pontuar_url_icone(url: str) -> int:
    dominio = _dominio_da_url(url)
    url_lower = url.lower()
    pontos = 0

    for i, fonte in enumerate(FONTES_IMAGEM_PRIORITARIAS):
        if fonte in dominio:
            pontos += 100 - i

    if "icon" in url_lower:
        pontos += 10

    if "orthodox" in url_lower:
        pontos += 10

    if "byzantine" in url_lower:
        pontos += 10

    if "saint" in url_lower:
        pontos += 5

    if url_lower.endswith(".png"):
        pontos += 5

    if url_lower.endswith(".jpg") or url_lower.endswith(".jpeg"):
        pontos += 3

    return pontos


def _ordenar_urls_por_prioridade(urls: list[str]) -> list[str]:
    urls_unicas = []

    for url in urls:
        if url and url not in urls_unicas:
            urls_unicas.append(url)

    return sorted(urls_unicas, key=_pontuar_url_icone, reverse=True)


def _url_tem_extensao_imagem(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False

    url = url.strip()

    if not url.startswith("https://"):
        return False

    return url.endswith(EXTENSOES_IMAGEM_VALIDAS)


def url_imagem_funciona(url: str) -> bool:
    """
    Valida se a URL realmente é uma imagem acessível.
    Evita salvar/cachear link quebrado, 403, 404 ou página HTML.
    """
    if not _url_tem_extensao_imagem(url):
        return False

    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }

        with httpx.Client(
            follow_redirects=True,
            timeout=10.0,
            headers=headers,
        ) as http_client:
            response = http_client.get(url)

        if response.status_code != 200:
            print(f"[ICONE URL INVÁLIDA] status={response.status_code} url={url}")
            return False

        content_type = response.headers.get("content-type", "").lower()

        if not content_type.startswith("image/"):
            print(f"[ICONE URL INVÁLIDA] content-type={content_type} url={url}")
            return False

        return True

    except Exception as e:
        print(f"[ICONE URL ERRO] {url} → {e}")
        return False


def _icone_valido(url: str | None) -> bool:
    if not url:
        return False

    if not isinstance(url, str):
        return False

    url = url.strip()

    if url.lower() in ("null", "none", ""):
        return False

    return url_imagem_funciona(url)


def _garantir_campo_icone(citacoes: list) -> list:
    """
    Garante que todas as citações tenham o campo icone_url.
    Não valida HTTP aqui para evitar requests desnecessários em massa.
    """
    for c in citacoes:
        if "icone_url" not in c:
            c["icone_url"] = None

    return citacoes


def _remover_icones_do_modelo(citacoes: list) -> list:
    """
    Nunca confia em icone_url vindo do modelo principal.
    A imagem deve ser preenchida apenas por _enriquecer_icones().
    """
    for c in citacoes:
        c["icone_url"] = None

    return citacoes


def parse_lista_urls(texto: str) -> list[str]:
    if not texto:
        return []

    cleaned = texto.strip()
    cleaned = re.sub(r"```json|```", "", cleaned).strip()

    try:
        data = json.loads(cleaned)

        if isinstance(data, list):
            return [
                url.strip()
                for url in data
                if isinstance(url, str) and _url_tem_extensao_imagem(url.strip())
            ]

    except Exception:
        pass

    urls = re.findall(
        r"https://[^\s\"'\]\)<>]+?\.(?:jpg|jpeg|png|webp)",
        cleaned,
        flags=re.IGNORECASE,
    )

    return [url.strip() for url in urls if _url_tem_extensao_imagem(url.strip())]


def buscar_icone_wikimedia_commons(nome: str) -> str | None:
    """
    Busca imagens reais no Wikimedia Commons usando a API oficial.
    Reduz URL inventada/quebrada.
    """
    termos = [
        f"{nome} icon",
        f"{nome} orthodox icon",
        f"{nome} byzantine icon",
        f"{nome} saint icon",
    ]

    headers = {
        "User-Agent": USER_AGENT,
    }

    try:
        with httpx.Client(timeout=12.0, headers=headers) as http_client:
            for termo in termos:
                params = {
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": termo,
                    "gsrnamespace": 6,
                    "gsrlimit": 10,
                    "prop": "imageinfo",
                    "iiprop": "url|mime",
                }

                response = http_client.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params=params,
                )

                response.raise_for_status()
                data = response.json()

                pages = data.get("query", {}).get("pages", {})
                candidatos = []

                for page in pages.values():
                    title = page.get("title", "")
                    imageinfo = page.get("imageinfo", [])

                    if not imageinfo:
                        continue

                    info = imageinfo[0]
                    url = info.get("url")
                    mime = info.get("mime", "")

                    if not url:
                        continue

                    title_lower = title.lower()

                    # Evita falso positivo conhecido:
                    # João Crisóstomo de Abreu e Sousa não é São João Crisóstomo.
                    if "abreu" in title_lower or "sousa" in title_lower:
                        continue

                    if not mime.startswith("image/"):
                        continue

                    if not _url_tem_extensao_imagem(url):
                        continue

                    candidatos.append(url)

                candidatos = _ordenar_urls_por_prioridade(candidatos)

                for url in candidatos:
                    if url_imagem_funciona(url):
                        print(f"[ICONE COMMONS OK] {nome} → {url}")
                        return url

                    print(f"[ICONE COMMONS DESCARTADO] {nome} → {url}")

                print(f"[ICONE COMMONS] Nenhum resultado válido para termo: {termo}")

        return None

    except Exception as e:
        print(f"[ICONE COMMONS ERRO] {nome}: {e}")
        return None


def buscar_icones_openai_web(nome: str) -> list[str]:
    """
    Busca múltiplas URLs candidatas via OpenAI web_search_preview.
    Não confia automaticamente nelas.
    """
    try:
        fontes = ", ".join(FONTES_IMAGEM_PRIORITARIAS)

        response = client.responses.create(
            model="gpt-4.1",
            tools=[{"type": "web_search_preview"}],
            input=f"""
Busque imagens diretas de ícone ortodoxo/bizantino de {nome}.

Termos de busca recomendados:
"{nome} icon png"
"{nome} orthodox icon jpg"
"{nome} byzantine icon png"
"{nome} saint icon"

Priorize imagens de domínios como:
{fontes}

Regras obrigatórias:
- Retorne APENAS um JSON array.
- Retorne até 10 URLs diretas de imagem.
- As URLs devem terminar em .jpg, .jpeg, .png ou .webp.
- Não retorne página HTML.
- Não use markdown.
- Não explique.
- Se não encontrar, retorne [].

Exemplo:
[
  "https://exemplo.com/imagem.jpg",
  "https://exemplo.com/imagem.png"
]
""",
        )

        raw = extract_text_from_response(response).strip()
        urls = parse_lista_urls(raw)
        urls = _ordenar_urls_por_prioridade(urls)

        print(f"[ICONE OPENAI CANDIDATOS] {nome} → {urls}")

        return urls

    except Exception as e:
        print(f"[ICONE OPENAI ERRO] {nome}: {e}")
        return []


def google_custom_search_configurado() -> bool:
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")

    if not api_key or not cse_id:
        return False

    placeholders = {
        "sua_chave",
        "seu_custom_search_engine_id",
        "your_api_key",
        "your_cse_id",
        "google_api_key",
        "google_cse_id",
    }

    if api_key.strip().lower() in placeholders:
        return False

    if cse_id.strip().lower() in placeholders:
        return False

    return True


def buscar_icones_google_custom_search(nome: str) -> list[str]:
    """
    Fallback opcional usando Google Custom Search.
    Só roda se GOOGLE_API_KEY e GOOGLE_CSE_ID estiverem configurados de verdade.
    """
    if not google_custom_search_configurado():
        print("[ICONE GOOGLE] Google Custom Search não configurado corretamente.")
        return []

    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")

    query = f"{nome} orthodox icon png OR jpg OR jpeg OR webp"

    try:
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "searchType": "image",
            "num": 10,
            "safe": "active",
        }

        with httpx.Client(timeout=10.0) as http_client:
            response = http_client.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
            )

        response.raise_for_status()
        data = response.json()

        urls = []

        for item in data.get("items", []):
            url = item.get("link")

            if url and _url_tem_extensao_imagem(url):
                urls.append(url)

        urls = _ordenar_urls_por_prioridade(urls)

        print(f"[ICONE GOOGLE CANDIDATOS] {nome} → {urls}")

        return urls

    except Exception as e:
        print(f"[ICONE GOOGLE ERRO] {nome}: {e}")
        return []


def buscar_icone_santo(nome: str) -> str | None:
    """
    Estratégia:
    1. Wikimedia Commons API oficial;
    2. OpenAI web_search_preview com múltiplas URLs;
    3. Google Custom Search, se configurado.
    """

    url = buscar_icone_wikimedia_commons(nome)

    if url:
        return url

    candidatos_openai = buscar_icones_openai_web(nome)

    for url in candidatos_openai:
        if url_imagem_funciona(url):
            print(f"[ICONE OK OPENAI] {nome} → {url}")
            return url

        print(f"[ICONE DESCARTADO OPENAI] {nome} → {url}")

    candidatos_google = buscar_icones_google_custom_search(nome)

    for url in candidatos_google:
        if url_imagem_funciona(url):
            print(f"[ICONE OK GOOGLE] {nome} → {url}")
            return url

        print(f"[ICONE DESCARTADO GOOGLE] {nome} → {url}")

    print(f"[ICONE NÃO ENCONTRADO] {nome}")
    return None


def buscar_citacao(passagem: str, padre: str, prompt: str) -> list:
    """
    Busca citações patrísticas em JSON obrigatório.
    Aqui o modelo NÃO deve decidir ícone.
    """
    try:
        response = client.responses.create(
            model="gpt-4.1",
            tools=[{"type": "web_search_preview"}],
            input=prompt + f"\n\nPassagem: {passagem}\nSanto Padre: {padre}",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "patristic_quotes_response",
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "citacoes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "nome": {"type": "string"},
                                        "texto": {"type": "string"},
                                        "fonte": {"type": "string"},
                                        "confianca": {
                                            "type": "string",
                                            "enum": ["alta", "media", "baixa"],
                                        },
                                    },
                                    "required": [
                                        "nome",
                                        "texto",
                                        "fonte",
                                        "confianca",
                                    ],
                                },
                            }
                        },
                        "required": ["citacoes"],
                    },
                    "strict": True,
                }
            },
        )

        raw_text = extract_text_from_response(response)

        if not raw_text:
            print(f"[AVISO] Resposta vazia do modelo para {padre}")
            return []

        data = json.loads(raw_text)

        resultado = data.get("citacoes", [])

        if not isinstance(resultado, list):
            print(f"[AVISO] Campo citacoes inválido para {padre}: {resultado}")
            return []

        # Nunca confiar em icone_url vindo dessa etapa.
        resultado = _remover_icones_do_modelo(resultado)
        resultado = _garantir_campo_icone(resultado)

        validado = validar_fontes(resultado)

        # Reforço extra: imagem só entra via enriquecimento controlado.
        validado = _remover_icones_do_modelo(validado)
        validado = _garantir_campo_icone(validado)

        print(f"[OK] {padre} → {len(validado)} citação(ões)")
        return validado

    except Exception as e:
        print(f"[ERRO] {padre}: {e}")
        return []


def montar_fila(padre: str) -> list[str]:
    """
    Fila determinística.
    Para Evangelhos/Catena, estes autores costumam ter cobertura melhor.
    Evita depender de sorteio e cair em autores com baixa chance.
    """
    fila = []

    if padre and padre not in fila:
        fila.append(padre)

    prioridade_evangelhos = [
        "São João Crisóstomo",
        "Santo Agostinho de Hipona",
        "São Jerônimo",
        "São Hilário de Poitiers",
        "São Beda, o Venerável",
        "São Gregório Magno",
        "Orígenes",
        "Santo Ambrósio de Milão",
        "São Cirilo de Alexandria",
        "São Remígio",
    ]

    for p in prioridade_evangelhos:
        if p not in fila:
            fila.append(p)

    # Fallback com suas listas originais, mas sem aleatoriedade.
    for p in PADRES_ALTA_COBERTURA:
        if p not in fila:
            fila.append(p)

    for p in PADRES_MEDIA_COBERTURA:
        if p not in fila:
            fila.append(p)

    for p in BAIXA_OUTROS:
        if p not in fila:
            fila.append(p)

    for p in BAIXA_ORTODOXOS_MODERNOS:
        if p not in fila:
            fila.append(p)

    return fila[:10]


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

                resultado = _remover_icones_do_modelo(resultado)
                resultado = _garantir_campo_icone(resultado)

                citacoes.extend(resultado)

                print(f"[CONCLUÍDO] {candidato}")

            except Exception as e:
                print(f"[FUTURE ERRO] {candidato}: {e}")

            if len(citacoes) >= 5:
                break

    citacoes = _remover_icones_do_modelo(citacoes)
    return _garantir_campo_icone(citacoes)


def _enriquecer_icones(resultado: list) -> list:
    """
    Busca ícones em paralelo para citações sem icone_url.
    Garante que todas retornem com icone_url, mesmo que seja None.
    """
    resultado = _garantir_campo_icone(resultado)

    sem_icone = [c for c in resultado if not c.get("icone_url") and c.get("nome")]

    print(f"[ICONE] Citações sem ícone válido: {len(sem_icone)}")

    if not sem_icone:
        return resultado

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(buscar_icone_santo, c["nome"]): c for c in sem_icone}

        for future in as_completed(futures):
            citacao = futures[future]

            try:
                icone_url = future.result()

                if icone_url and url_imagem_funciona(icone_url):
                    citacao["icone_url"] = icone_url
                else:
                    citacao["icone_url"] = None

                print(f"[ICONE SET] {citacao.get('nome')} → {citacao.get('icone_url')}")

            except Exception as e:
                print(f"[ICONE FUTURE ERRO] {citacao.get('nome')}: {e}")
                citacao["icone_url"] = None

    return _garantir_campo_icone(resultado)


async def _salvar_cache(cache_key: str, resultado: list) -> None:
    resultado = _garantir_campo_icone(resultado)

    await redis_client.setex(
        cache_key,
        CACHE_TTL,
        json.dumps(resultado, ensure_ascii=False),
    )

    print(f"[CACHE SET] {cache_key} — TTL: {CACHE_TTL}s")


async def get_patristic_text(passagem: str, padre: str) -> list:
    cache_key = _build_cache_key(passagem, padre)
    loop = asyncio.get_event_loop()

    cached = await redis_client.get(cache_key)

    if cached:
        print(f"[CACHE HIT] {cache_key}")

        try:
            resultado = json.loads(cached)
        except json.JSONDecodeError:
            print(f"[CACHE ERRO] JSON inválido no cache: {cache_key}")
            resultado = []

        resultado = _garantir_campo_icone(resultado)

        precisa_enriquecer = any(not c.get("icone_url") for c in resultado)

        if resultado and precisa_enriquecer:
            print(f"[CACHE HIT] Cache antigo/sem ícone detectado: {cache_key}")

            resultado = await loop.run_in_executor(
                None,
                partial(_enriquecer_icones, resultado),
            )

            resultado = _garantir_campo_icone(resultado)
            await _salvar_cache(cache_key, resultado)

        print(
            "[DEBUG CACHE FINAL]", json.dumps(resultado, ensure_ascii=False, indent=2)
        )
        return resultado

    print(f"[CACHE MISS] {cache_key} — chamando OpenAI")

    prompt = load_prompt("prompts/search.md")
    fila = montar_fila(padre)

    citacoes = await loop.run_in_executor(
        None,
        partial(_buscar_em_paralelo, passagem, fila, prompt),
    )

    citacoes = _remover_icones_do_modelo(citacoes)
    citacoes = _garantir_campo_icone(citacoes)

    citacoes = normalizar_nomes(citacoes)

    # Reforço: depois da normalização, zera ícones novamente.
    citacoes = _remover_icones_do_modelo(citacoes)
    citacoes = _garantir_campo_icone(citacoes)

    resultado = deduplicate(citacoes)[:5]
    resultado = _garantir_campo_icone(resultado)

    if not resultado:
        print("[AVISO] Nenhuma citação encontrada após deduplicação.")
        return []

    print("[ICONE] Iniciando enriquecimento de ícones...")

    resultado = await loop.run_in_executor(
        None,
        partial(_enriquecer_icones, resultado),
    )

    resultado = _garantir_campo_icone(resultado)

    await _salvar_cache(cache_key, resultado)

    print("[DEBUG FINAL]", json.dumps(resultado, ensure_ascii=False, indent=2))

    return resultado
