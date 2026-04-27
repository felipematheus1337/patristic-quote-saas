from pydantic import BaseModel, Field
from typing import Literal, Optional


class Saint_Quote(BaseModel):
    nome: str
    texto: str
    fonte: str
    confianca: Literal["alta", "media", "baixa"]
    icone_url: Optional[str] = None


class Saint_Quote_Input(BaseModel):
    passagem: str = Field(..., min_length=3, example="Mateus 4:12-25")
    father: str = Field(..., min_length=3, example="São João Crisóstomo")
