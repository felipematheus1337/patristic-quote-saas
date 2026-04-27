package bff_patristic.v1.exception;

public class FastApiUnavailableException extends RuntimeException {

    public FastApiUnavailableException(String message, Throwable cause) {
        super(message, cause);
    }
}