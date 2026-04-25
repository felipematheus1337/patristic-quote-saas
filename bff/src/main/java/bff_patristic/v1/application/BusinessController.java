package bff_patristic.v1.application;

import bff_patristic.v1.application.dto.SaintQuoteDTO;
import bff_patristic.v1.domain.SaintQuote;
import bff_patristic.v1.service.QuoteService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/quotes")
public class BusinessController {

    private final QuoteService quoteService;

    public BusinessController(QuoteService quoteService) {
        this.quoteService = quoteService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.OK)
    ResponseEntity<List<SaintQuote>> getQuotes(@RequestBody SaintQuoteDTO saintQuoteDTO) {
        return ResponseEntity.ok(quoteService.get(saintQuoteDTO));
    }
}
