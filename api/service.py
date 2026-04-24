from openai import OpenAI
from dotenv import load_dotenv
from utils.helper import extract_text_from_response, parse_response, load_prompt

load_dotenv()

client = OpenAI()

def get_patristic_text(passagem: str, padre: str):
    prompt = load_prompt("prompts/search.md")

    response = client.responses.create(
        model="gpt-4.1",
        tools=[{"type": "web_search_preview"}],
        input=prompt + f"\n\nPassagem: {passagem}\nSanto Padre: {padre}"
    )

    raw_text = extract_text_from_response(response)
    return parse_response(raw_text)

payload = get_patristic_text("Mateus 1:1-8", "São João Crisóstomo")
print(payload)