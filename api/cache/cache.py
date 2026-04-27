import json
import os

import redis.asyncio as redis

from application.constants.constantes import CACHE_TTL


class PatristicCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True,
        )

    def build_cache_key(self, passagem: str, padre: str) -> str:
        passagem_norm = (
            passagem.lower()
            .strip()
            .replace(" ", "_")
            .replace(":", "_")
            .replace("-", "_")
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

    async def get(self, cache_key: str) -> list | None:
        cached = await self.redis_client.get(cache_key)

        if not cached:
            return None

        try:
            print(f"[CACHE HIT] {cache_key}")
            return json.loads(cached)
        except json.JSONDecodeError:
            print(f"[CACHE ERRO] JSON inválido no cache: {cache_key}")
            return []

    async def set(self, cache_key: str, resultado: list) -> None:
        await self.redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(resultado, ensure_ascii=False),
        )

        print(f"[CACHE SET] {cache_key} — TTL: {CACHE_TTL}s")
