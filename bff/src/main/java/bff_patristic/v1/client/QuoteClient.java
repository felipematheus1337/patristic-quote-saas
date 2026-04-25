package bff_patristic.v1.client;

import bff_patristic.v1.application.dto.SaintQuoteDTO;
import bff_patristic.v1.domain.SaintQuote;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestBody;

import java.util.List;

@FeignClient(name = "quoteClient", url = "${services.fastapi.base-url}")
public interface QuoteClient {

    @GetMapping("api/v1/quotes")
    public List<SaintQuote> find(@RequestBody SaintQuoteDTO dto);
}
