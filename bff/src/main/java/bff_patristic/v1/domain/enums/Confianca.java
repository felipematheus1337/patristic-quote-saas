package bff_patristic.v1.domain.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum Confianca {
    ALTA,
    MEDIA,
    BAIXA;

    @JsonCreator
    public static Confianca fromValue(String value) {
        return Confianca.valueOf(value.toUpperCase());
    }

    @JsonValue
    public String toValue() {
        return this.name().toLowerCase();
    }
}