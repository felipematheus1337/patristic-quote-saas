package bff_patristic.v1.service;

import bff_patristic.v1.application.dto.SaintQuoteDTO;
import bff_patristic.v1.client.QuoteClient;
import bff_patristic.v1.domain.SaintQuote;
import bff_patristic.v1.exception.FastApiUnavailableException;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;

@Service
public class QuoteService {


    private final QuoteClient client;

    public QuoteService(QuoteClient client) {
        this.client = client;
    }

    @CircuitBreaker(name = "fastapi", fallbackMethod = "fallbackQuotes")
    public List<SaintQuote> get(SaintQuoteDTO saintQuoteDTO) {
        return client.find(saintQuoteDTO);
    }

    public List<SaintQuote> fallbackQuotes(SaintQuoteDTO dto, Exception e) {
        throw new FastApiUnavailableException("Falha ao consultar citações patrísticas.", e);

    }
}
