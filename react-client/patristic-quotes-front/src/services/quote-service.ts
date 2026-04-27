import type { QuoteSearchPayload, SaintQuote } from "@/types/quote";

export async function searchQuotes(
  payload: QuoteSearchPayload,
): Promise<SaintQuote[]> {
  console.log("Payload enviado para o backend:", payload);

  await new Promise((resolve) => setTimeout(resolve, 1500));

  return [
    {
      nome: "São Jerônimo",
      texto:
        "Não realmente atingidos pela lua, mas que eram acreditados como tal através da sutileza dos demônios, que, observando as fases da lua, buscavam trazer uma má reputação à criatura, para que isso redundasse em blasfêmia contra o Criador.",
      fonte: "https://catenabible.com/mt/4/25",
      confianca: "alta",
    },
    {
      nome: "São João Crisóstomo",
      texto:
        "Vês como Ele não fica em um lugar, mas viaja de cidade em cidade? Isso para que ninguém pudesse dizer que os que vieram a Ele foram forçados ou obrigados. Pois, se Ele tivesse permanecido em um lugar, talvez alguém dissesse: 'Aqueles que vieram a Ele foram compelidos por necessidade.' Mas, ao ir de cidade em cidade, Ele mostra que todos vieram livremente, impelidos pelo desejo e sede da doutrina.",
      fonte: "https://catenabible.com/mt/4/12-25#chrysostom",
      confianca: "alta",
    },
    {
      nome: "Santo Agostinho de Hipona",
      texto:
        "Pode-se questionar por que João relata que, próximo ao Jordão, não na Galileia, André seguiu o Senhor com outro cujo nome não menciona; e novamente, que Pedro recebeu esse nome do Senhor. Enquanto os outros três evangelistas escrevem que foram chamados de sua pesca, concordando suficientemente entre si, especialmente Mateus e Marcos; Lucas não nomeia André, que, no entanto, é entendido como estando no mesmo barco com ele. Há uma aparente discrepância adicional, pois em Lucas é dito apenas a Pedro: 'De agora em diante, serás pescador de homens'; Mateus e Marcos escrevem que isso foi dito a ambos. Quanto ao relato diferente em João, deve-se considerar cuidadosamente, e será encontrado que é um tempo, lugar e chamado diferentes que são ali mencionados.",
      fonte: "https://catenabible.com/mt/4/25",
      confianca: "alta",
    },
  ];
}

/*
import type { QuoteSearchPayload, SaintQuote } from "@/types/quote";

const API_URL = "http://localhost:8082/quotes";
export async function searchQuotes(
  payload: QuoteSearchPayload,
): Promise<SaintQuote[]> {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorMessage = "Erro ao buscar citações.";

    try {
      const errorBody = await response.json();

      if (errorBody?.message) {
        errorMessage = errorBody.message;
      }
    } catch {
      // Se o backend não devolver JSON no erro, mantém a mensagem padrão.
    }

    throw new Error(errorMessage);
  }

  return response.json();
}
  */
