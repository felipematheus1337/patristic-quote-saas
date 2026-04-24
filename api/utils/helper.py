import json
import re

def extract_text_from_response(response) -> str:
    """Extrai o texto final da resposta, compatível com web search tool."""
    for block in response.output:
        if block.type == "message":
            for content in block.content:
                if content.type == "output_text":
                    return content.text
    return ""

def parse_response(text: str):
    """Tenta fazer parse do JSON, retornando [] em caso de falha."""
    if not text.strip():
        print("[AVISO] Resposta vazia do modelo.")
        return []

    cleaned = re.sub(r"```json|```", "", text).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[ERRO] Falha ao parsear JSON: {e}")
        print(f"[DEBUG] Texto recebido:\n{text[:500]}")
        return []

def load_prompt(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()