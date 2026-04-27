import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import httpx

from infra.openai_client import client
from utils.helper import extract_text_from_response

from application.constants.constantes import (
    EXTENSOES_IMAGEM_VALIDAS,
    FONTES_IMAGEM_PRIORITARIAS,
    USER_AGENT,
)
from utils.quote_utils import garantir_campo_icone


class IconSearchService:
    def dominio_da_url(self, url: str) -> str:
        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return ""

    def pontuar_url_icone(self, url: str) -> int:
        dominio = self.dominio_da_url(url)
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

    def ordenar_urls_por_prioridade(self, urls: list[str]) -> list[str]:
        urls_unicas = []

        for url in urls:
            if url and url not in urls_unicas:
                urls_unicas.append(url)

        return sorted(urls_unicas, key=self.pontuar_url_icone, reverse=True)

    def url_tem_extensao_imagem(self, url: str) -> bool:
        if not url or not isinstance(url, str):
            return False

        url = url.strip()

        if not url.startswith("https://"):
            return False

        return url.endswith(EXTENSOES_IMAGEM_VALIDAS)

    def url_imagem_funciona(self, url: str) -> bool:
        if not self.url_tem_extensao_imagem(url):
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

    def parse_lista_urls(self, texto: str) -> list[str]:
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
                    if isinstance(url, str)
                    and self.url_tem_extensao_imagem(url.strip())
                ]

        except Exception:
            pass

        urls = re.findall(
            r"https://[^\s\"'\]\)<>]+?\.(?:jpg|jpeg|png|webp)",
            cleaned,
            flags=re.IGNORECASE,
        )

        return [
            url.strip() for url in urls if self.url_tem_extensao_imagem(url.strip())
        ]

    def buscar_icone_wikimedia_commons(self, nome: str) -> str | None:
        termos = [
            f"{nome} icon",
            f"{nome} orthodox icon",
            f"{nome} byzantine icon",
            f"{nome} saint icon",
        ]

        headers = {"User-Agent": USER_AGENT}

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

                        if "abreu" in title_lower or "sousa" in title_lower:
                            continue

                        if not mime.startswith("image/"):
                            continue

                        if not self.url_tem_extensao_imagem(url):
                            continue

                        candidatos.append(url)

                    candidatos = self.ordenar_urls_por_prioridade(candidatos)

                    for url in candidatos:
                        if self.url_imagem_funciona(url):
                            print(f"[ICONE COMMONS OK] {nome} → {url}")
                            return url

                        print(f"[ICONE COMMONS DESCARTADO] {nome} → {url}")

                    print(
                        f"[ICONE COMMONS] Nenhum resultado válido para termo: {termo}"
                    )

            return None

        except Exception as e:
            print(f"[ICONE COMMONS ERRO] {nome}: {e}")
            return None

    def buscar_icones_openai_web(self, nome: str) -> list[str]:
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
""",
            )

            raw = extract_text_from_response(response).strip()
            urls = self.parse_lista_urls(raw)
            urls = self.ordenar_urls_por_prioridade(urls)

            print(f"[ICONE OPENAI CANDIDATOS] {nome} → {urls}")

            return urls

        except Exception as e:
            print(f"[ICONE OPENAI ERRO] {nome}: {e}")
            return []

    def google_custom_search_configurado(self) -> bool:
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

    def buscar_icones_google_custom_search(self, nome: str) -> list[str]:
        if not self.google_custom_search_configurado():
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

                if url and self.url_tem_extensao_imagem(url):
                    urls.append(url)

            urls = self.ordenar_urls_por_prioridade(urls)

            print(f"[ICONE GOOGLE CANDIDATOS] {nome} → {urls}")

            return urls

        except Exception as e:
            print(f"[ICONE GOOGLE ERRO] {nome}: {e}")
            return []

    def buscar_icone_santo(self, nome: str) -> str | None:
        url = self.buscar_icone_wikimedia_commons(nome)

        if url:
            return url

        candidatos_openai = self.buscar_icones_openai_web(nome)

        for url in candidatos_openai:
            if self.url_imagem_funciona(url):
                print(f"[ICONE OK OPENAI] {nome} → {url}")
                return url

            print(f"[ICONE DESCARTADO OPENAI] {nome} → {url}")

        candidatos_google = self.buscar_icones_google_custom_search(nome)

        for url in candidatos_google:
            if self.url_imagem_funciona(url):
                print(f"[ICONE OK GOOGLE] {nome} → {url}")
                return url

            print(f"[ICONE DESCARTADO GOOGLE] {nome} → {url}")

        print(f"[ICONE NÃO ENCONTRADO] {nome}")
        return None

    def enriquecer_icones(self, resultado: list) -> list:
        resultado = garantir_campo_icone(resultado)

        sem_icone = [c for c in resultado if not c.get("icone_url") and c.get("nome")]

        print(f"[ICONE] Citações sem ícone válido: {len(sem_icone)}")

        if not sem_icone:
            return resultado

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.buscar_icone_santo, c["nome"]): c
                for c in sem_icone
            }

            for future in as_completed(futures):
                citacao = futures[future]

                try:
                    icone_url = future.result()

                    if icone_url and self.url_imagem_funciona(icone_url):
                        citacao["icone_url"] = icone_url
                    else:
                        citacao["icone_url"] = None

                    print(
                        f"[ICONE SET] {citacao.get('nome')} → {citacao.get('icone_url')}"
                    )

                except Exception as e:
                    print(f"[ICONE FUTURE ERRO] {citacao.get('nome')}: {e}")
                    citacao["icone_url"] = None

        return garantir_campo_icone(resultado)
