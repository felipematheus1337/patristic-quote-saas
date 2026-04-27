import { z } from "zod";
import { GOSPELS } from "@/data/bible";

export const quoteSearchSchema = z
  .object({
    gospel: z.string().min(1, "Selecione um Evangelho."),
    fatherMode: z.enum(["preset", "custom"]),
    father: z.string().optional(),
    customFather: z.string().optional(),
    chapter: z.coerce
      .number({ message: "Informe um capítulo válido." })
      .int("O capítulo deve ser um número inteiro.")
      .positive("O capítulo deve ser maior que zero."),
    startVerse: z.coerce
      .number({ message: "Informe o versículo inicial." })
      .int("O versículo inicial deve ser um número inteiro.")
      .positive("O versículo inicial deve ser maior que zero."),
    endVerse: z.coerce
      .number({ message: "Informe o versículo final." })
      .int("O versículo final deve ser um número inteiro.")
      .positive("O versículo final deve ser maior que zero."),
  })
  .superRefine((data, ctx) => {
    const selectedGospel = GOSPELS.find(
      (gospel) => gospel.name === data.gospel,
    );

    if (!selectedGospel) {
      ctx.addIssue({
        code: "custom",
        path: ["gospel"],
        message: "Evangelho inválido.",
      });
      return;
    }

    if (data.chapter > selectedGospel.chapters) {
      ctx.addIssue({
        code: "custom",
        path: ["chapter"],
        message: `${data.gospel} possui apenas ${selectedGospel.chapters} capítulos.`,
      });
      return;
    }

    const maxVerse =
      selectedGospel.versesByChapter[
        data.chapter as keyof typeof selectedGospel.versesByChapter
      ];

    if (!maxVerse) {
      ctx.addIssue({
        code: "custom",
        path: ["chapter"],
        message: "Capítulo inválido para este Evangelho.",
      });
      return;
    }

    if (data.startVerse > maxVerse) {
      ctx.addIssue({
        code: "custom",
        path: ["startVerse"],
        message: `O capítulo ${data.chapter} de ${data.gospel} possui apenas ${maxVerse} versículos.`,
      });
    }

    if (data.endVerse > maxVerse) {
      ctx.addIssue({
        code: "custom",
        path: ["endVerse"],
        message: `O capítulo ${data.chapter} de ${data.gospel} possui apenas ${maxVerse} versículos.`,
      });
    }

    if (data.endVerse < data.startVerse) {
      ctx.addIssue({
        code: "custom",
        path: ["endVerse"],
        message: "O versículo final não pode ser menor que o inicial.",
      });
    }

    if (data.fatherMode === "custom" && !data.customFather?.trim()) {
      ctx.addIssue({
        code: "custom",
        path: ["customFather"],
        message: "Digite o nome do Padre.",
      });
    }
  });

export type QuoteSearchFormData = z.infer<typeof quoteSearchSchema>;
