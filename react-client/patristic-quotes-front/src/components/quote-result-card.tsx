import type { SaintQuote } from "@/types/quote";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type QuoteResultCardProps = {
  quotes: SaintQuote[];
};

export function QuoteResultCard({ quotes }: QuoteResultCardProps) {
  if (quotes.length === 0) {
    return null;
  }

  return (
    <div className="mt-2 w-full space-y-4">
      {quotes.map((quote, index) => (
        <Card
          key={`${quote.nome}-${index}`}
          className="border-amber-200 bg-white/60 shadow-sm backdrop-blur-sm"
        >
          <CardHeader>
            <CardTitle className="text-lg text-zinc-900">
              {quote.nome}
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-3">
            <p className="leading-7 text-zinc-700">“{quote.texto}”</p>

            {quote.fonte && (
              <p className="text-sm text-zinc-500">Fonte: {quote.fonte}</p>
            )}

            {quote.confianca && (
              <span className="inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-900">
                Confiança: {quote.confianca}
              </span>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
