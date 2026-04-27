export type QuoteSearchPayload = {
  passagem: string;
  father?: string;
};

export type SaintQuote = {
  nome: string;
  texto: string;
  fonte?: string;
  confianca?: "baixa" | "media" | "alta";
};
