package bff_patristic.v1.exception;

import bff_patristic.v1.exception.ApiErrorResponse;
import feign.FeignException;
import feign.RetryableException;
import io.github.resilience4j.circuitbreaker.CallNotPermittedException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(FastApiUnavailableException.class)
    public ResponseEntity<ApiErrorResponse> handleFastApiUnavailable(FastApiUnavailableException ex) {
        return ResponseEntity
                .status(HttpStatus.SERVICE_UNAVAILABLE)
                .body(ApiErrorResponse.of(
                        HttpStatus.SERVICE_UNAVAILABLE.value(),
                        mensagemOuPadrao(ex.getMessage())
                ));
    }

    @ExceptionHandler(FeignException.NotFound.class)
    public ResponseEntity<ApiErrorResponse> handleFeignNotFound(FeignException.NotFound ex) {
        return ResponseEntity
                .status(HttpStatus.NOT_FOUND)
                .body(ApiErrorResponse.of(
                        HttpStatus.NOT_FOUND.value(),
                        "Nenhuma citação patrística verificável encontrada."
                ));
    }

    @ExceptionHandler(FeignException.BadRequest.class)
    public ResponseEntity<ApiErrorResponse> handleFeignBadRequest(FeignException.BadRequest ex) {
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiErrorResponse.of(
                        HttpStatus.BAD_REQUEST.value(),
                        "Requisição inválida ao consultar citações patrísticas."
                ));
    }

    @ExceptionHandler(RetryableException.class)
    public ResponseEntity<ApiErrorResponse> handleRetryableException(RetryableException ex) {
        return ResponseEntity
                .status(HttpStatus.GATEWAY_TIMEOUT)
                .body(ApiErrorResponse.of(
                        HttpStatus.GATEWAY_TIMEOUT.value(),
                        "Tempo esgotado ao consultar o serviço de citações."
                ));
    }

    @ExceptionHandler(CallNotPermittedException.class)
    public ResponseEntity<ApiErrorResponse> handleCircuitBreakerOpen(CallNotPermittedException ex) {
        return ResponseEntity
                .status(HttpStatus.SERVICE_UNAVAILABLE)
                .body(ApiErrorResponse.of(
                        HttpStatus.SERVICE_UNAVAILABLE.value(),
                        "Serviço de citações temporariamente indisponível."
                ));
    }

    @ExceptionHandler(FeignException.class)
    public ResponseEntity<ApiErrorResponse> handleFeignException(FeignException ex) {
        HttpStatus status = HttpStatus.resolve(ex.status());

        if (status == null) {
            status = HttpStatus.BAD_GATEWAY;
        }

        return ResponseEntity
                .status(status)
                .body(ApiErrorResponse.of(
                        status.value(),
                        "Falha ao consultar citações patrísticas."
                ));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiErrorResponse> handleGenericException(Exception ex) {
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiErrorResponse.of(
                        HttpStatus.INTERNAL_SERVER_ERROR.value(),
                        "Falha ao consultar."
                ));
    }

    private String mensagemOuPadrao(String mensagem) {
        if (mensagem == null || mensagem.isBlank()) {
            return "Falha ao consultar.";
        }

        return mensagem;
    }
}