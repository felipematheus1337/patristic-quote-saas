package bff_patristic.v1.service;

import bff_patristic.v1.application.dto.SaintQuoteDTO;
import bff_patristic.v1.client.QuoteClient;
import bff_patristic.v1.domain.SaintQuote;
import org.jspecify.annotations.Nullable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class QuoteService {

    private final QuoteClient client;

    public QuoteService(QuoteClient client) {
        this.client = client;
    }

    public List<SaintQuote> get(SaintQuoteDTO saintQuoteDTO) {
        return client.find(saintQuoteDTO);
    }
}
