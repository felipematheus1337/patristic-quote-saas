package bff_patristic.v1.exception;

import java.time.LocalDateTime;

public record ApiErrorResponse(
        int status,
        String mensagem,
        LocalDateTime timestamp
) {
    public static ApiErrorResponse of(int status, String mensagem) {
        return new ApiErrorResponse(status, mensagem, LocalDateTime.now());
    }
}