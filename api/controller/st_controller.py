from domain.saint_quote import Saint_Quote, Saint_Quote_Input
import service as quote_service
from fastapi import FastAPI

app = FastAPI(title="Patristic Quotes")

@app.post(path="/quotes", response_model=list[Saint_Quote])
async def st_list_quotes(dto: Saint_Quote_Input):
    return  quote_service.get_patristic_text(dto.passagem, dto.father)