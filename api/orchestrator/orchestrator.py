import asyncio
import json
from functools import partial

from utils.helper import load_prompt, normalizar_nomes

from cache import PatristicCache
from search.icon_search import IconSearchService
from search.quote_search import PatristicQuoteSearchService
from utils.quote_utils import (
    deduplicate,
    garantir_campo_icone,
    remover_icones_do_modelo,
)


class PatristicQuoteOrchestrator:
    def __init__(self):
        self.cache = PatristicCache()
        self.quote_search = PatristicQuoteSearchService()
        self.icon_search = IconSearchService()

    async def get_patristic_text(self, passagem: str, padre: str) -> list:
        cache_key = self.cache.build_cache_key(passagem, padre)
        loop = asyncio.get_event_loop()

        cached = await self.cache.get(cache_key)

        if cached is not None:
            resultado = garantir_campo_icone(cached)

            precisa_enriquecer = any(not c.get("icone_url") for c in resultado)

            if resultado and precisa_enriquecer:
                print(f"[CACHE HIT] Cache antigo/sem ícone detectado: {cache_key}")

                resultado = await loop.run_in_executor(
                    None,
                    partial(self.icon_search.enriquecer_icones, resultado),
                )

                resultado = garantir_campo_icone(resultado)
                await self.cache.set(cache_key, resultado)

            print(
                "[DEBUG CACHE FINAL]",
                json.dumps(resultado, ensure_ascii=False, indent=2),
            )
            return resultado

        print(f"[CACHE MISS] {cache_key} — chamando OpenAI")

        prompt = load_prompt("prompts/search.md")
        fila = self.quote_search.montar_fila(padre)

        citacoes = await loop.run_in_executor(
            None,
            partial(self.quote_search.buscar_em_paralelo, passagem, fila, prompt),
        )

        citacoes = remover_icones_do_modelo(citacoes)
        citacoes = garantir_campo_icone(citacoes)

        citacoes = normalizar_nomes(citacoes)

        citacoes = remover_icones_do_modelo(citacoes)
        citacoes = garantir_campo_icone(citacoes)

        resultado = deduplicate(citacoes)[:5]
        resultado = garantir_campo_icone(resultado)

        if not resultado:
            print("[AVISO] Nenhuma citação encontrada após deduplicação.")
            return []

        print("[ICONE] Iniciando enriquecimento de ícones...")

        resultado = await loop.run_in_executor(
            None,
            partial(self.icon_search.enriquecer_icones, resultado),
        )

        resultado = garantir_campo_icone(resultado)

        await self.cache.set(cache_key, resultado)

        print("[DEBUG FINAL]", json.dumps(resultado, ensure_ascii=False, indent=2))

        return resultado
