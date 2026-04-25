package bff_patristic.v1.domain.enums;

public enum Confianca {

    ALTA("alta"), MEDIA("media"), BAIXA("baixa");

    private final String valor;

    Confianca(String valor) {
        this.valor = valor;
    }
}
