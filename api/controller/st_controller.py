from fastapi import APIRouter, HTTPException
from domain.saint_quote import Saint_Quote, Saint_Quote_Input
from application import service as quote_service

router = APIRouter()


@router.post(
    "/quotes", response_model=list[Saint_Quote], response_model_exclude_none=False
)
async def st_list_quotes(dto: Saint_Quote_Input):
    try:
        resultado = await quote_service.get_patristic_text(dto.passagem, dto.father)
        if not resultado:
            raise HTTPException(
                status_code=404,
                detail="Nenhuma citação patrística verificável encontrada.",
            )
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
