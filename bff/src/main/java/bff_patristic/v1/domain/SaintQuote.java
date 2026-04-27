package bff_patristic.v1.domain;

import bff_patristic.v1.domain.enums.Confianca;
import com.fasterxml.jackson.annotation.JsonProperty;

public class SaintQuote {

    private String nome;
    private String texto;
    private String fonte;
    private Confianca confianca;
    @JsonProperty(value = "icone_url")
    private String iconeUrl;

    public SaintQuote() {
    }

    public SaintQuote(String nome, String texto, String fonte, Confianca confianca) {
        this.nome = nome;
        this.texto = texto;
        this.fonte = fonte;
        this.confianca = confianca;
    }

    public String getNome() {
        return nome;
    }

    public void setNome(String nome) {
        this.nome = nome;
    }

    public String getTexto() {
        return texto;
    }

    public void setTexto(String texto) {
        this.texto = texto;
    }

    public String getFonte() {
        return fonte;
    }

    public void setFonte(String fonte) {
        this.fonte = fonte;
    }

    public Confianca getConfianca() {
        return confianca;
    }

    public void setConfianca(Confianca confianca) {
        this.confianca = confianca;
    }

    public String getIconeUrl() {
        return iconeUrl;
    }

    public void setIconeUrl(String iconeUrl) {
        this.iconeUrl = iconeUrl;
    }
}

