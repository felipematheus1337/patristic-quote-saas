import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from infra.openai_client import client
from utils.helper import (
    extract_text_from_response,
    validar_fontes,
)

from const import (
    PADRES_ALTA_COBERTURA,
    PADRES_MEDIA_COBERTURA,
)

from application.constants.constantes import (
    BAIXA_ORTODOXOS_MODERNOS,
    BAIXA_OUTROS,
    PRIORIDADE_EVANGELHOS,
)
from application.constants.constantes import (
    garantir_campo_icone,
    remover_icones_do_modelo,
)


class PatristicQuoteSearchService:
    def buscar_citacao(self, passagem: str, padre: str, prompt: str) -> list:
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

            resultado = remover_icones_do_modelo(resultado)
            resultado = garantir_campo_icone(resultado)

            validado = validar_fontes(resultado)

            validado = remover_icones_do_modelo(validado)
            validado = garantir_campo_icone(validado)

            print(f"[OK] {padre} → {len(validado)} citação(ões)")
            return validado

        except Exception as e:
            print(f"[ERRO] {padre}: {e}")
            return []

    def montar_fila(self, padre: str) -> list[str]:
        fila = []

        if padre and padre not in fila:
            fila.append(padre)

        for p in PRIORIDADE_EVANGELHOS:
            if p not in fila:
                fila.append(p)

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

    def buscar_em_paralelo(self, passagem: str, fila: list[str], prompt: str) -> list:
        citacoes = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(
                    self.buscar_citacao, passagem, candidato, prompt
                ): candidato
                for candidato in fila
            }

            for future in as_completed(futures):
                candidato = futures[future]

                try:
                    resultado = future.result()

                    resultado = remover_icones_do_modelo(resultado)
                    resultado = garantir_campo_icone(resultado)

                    citacoes.extend(resultado)

                    print(f"[CONCLUÍDO] {candidato}")

                except Exception as e:
                    print(f"[FUTURE ERRO] {candidato}: {e}")

                if len(citacoes) >= 5:
                    break

        citacoes = remover_icones_do_modelo(citacoes)
        return garantir_campo_icone(citacoes)
