import { useMemo, useState } from "react";
import { Loader2, Search, ArrowLeft } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AnimatePresence, motion } from "framer-motion";

import { GOSPELS } from "@/data/bible";
import { FATHERS } from "@/data/fathers";
import {
  quoteSearchSchema,
  type QuoteSearchFormData,
} from "@/schemas/quote-search-schema";
import { searchQuotes } from "@/services/quote-service";
import type { QuoteSearchPayload, SaintQuote } from "@/types/quote";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { QuoteResultCard } from "@/components/quote-result-card";

import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

type ScreenMode = "form" | "results";

const inputClassName =
  "h-11 border-[#b38b59]/50 bg-white/85 text-zinc-950 shadow-sm placeholder:text-zinc-500";

const selectTriggerClassName =
  "h-11 border-[#b38b59]/50 bg-white/85 text-zinc-950 shadow-sm";

const selectContentClassName =
  "z-[9999] border-[#b38b59] bg-[#f5ecd8] text-zinc-950 shadow-2xl";

const selectItemClassName =
  "cursor-pointer focus:bg-[#ead7b1] focus:text-zinc-950";

const helperTextClassName = "text-xs font-medium text-zinc-700";

const errorTextClassName = "text-sm font-medium text-red-700";

export function QuoteSearchForm() {
  const [quotes, setQuotes] = useState<SaintQuote[]>([]);
  const [apiError, setApiError] = useState<string | null>(null);
  const [screenMode, setScreenMode] = useState<ScreenMode>("form");
  const [loadingResults, setLoadingResults] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<QuoteSearchFormData>({
    resolver: zodResolver(quoteSearchSchema),
    defaultValues: {
      gospel: "",
      fatherMode: "preset",
      father: "",
      customFather: "",
      chapter: 1,
      startVerse: 1,
      endVerse: 1,
    },
  });

  const selectedGospelName = watch("gospel");
  const selectedChapter = watch("chapter");
  const fatherMode = watch("fatherMode");

  const selectedGospel = useMemo(() => {
    return GOSPELS.find((gospel) => gospel.name === selectedGospelName);
  }, [selectedGospelName]);

  const maxVerse = useMemo(() => {
    if (!selectedGospel || !selectedChapter) {
      return undefined;
    }

    return selectedGospel.versesByChapter[
      Number(selectedChapter) as keyof typeof selectedGospel.versesByChapter
    ];
  }, [selectedGospel, selectedChapter]);

  async function onSubmit(data: QuoteSearchFormData) {
    setApiError(null);
    setQuotes([]);
    setScreenMode("results");
    setLoadingResults(true);

    const passagem = `${data.gospel} ${data.chapter}:${data.startVerse}-${data.endVerse}`;

    const chosenFather =
      data.fatherMode === "custom"
        ? data.customFather?.trim()
        : data.father?.trim();

    const payload: QuoteSearchPayload = {
      passagem,
      ...(chosenFather ? { father: chosenFather } : {}),
    };

    try {
      const response = await searchQuotes(payload);
      setQuotes(response);
    } catch {
      setApiError("Não foi possível buscar as citações. Tente novamente.");
    } finally {
      setLoadingResults(false);
    }
  }

  function handleBackToMenu() {
    setScreenMode("form");
    setLoadingResults(false);
    setApiError(null);
  }

  return (
    <main
      className="relative min-h-screen w-screen overflow-x-hidden bg-cover bg-center bg-no-repeat bg-fixed"
      style={{ backgroundImage: "url('/images/wallpaper.jpg')" }}
    >
      <div className="absolute inset-0 bg-black/45" />

      <div className="relative z-10 flex min-h-screen w-full items-center justify-center px-4 py-10">
        <div className="w-full max-w-4xl">
          <AnimatePresence mode="wait">
            {screenMode === "form" ? (
              <motion.div
                key="form-screen"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{ duration: 0.35 }}
              >
                <div className="mb-8 text-center">
                  <p className="mb-3 text-sm font-semibold uppercase tracking-[0.35em] text-[#f5ecd8] drop-shadow-md">
                    Patristic Quotes
                  </p>

                  <h1 className="mx-auto max-w-5xl text-4xl font-extrabold tracking-tight text-[#fff7e6] drop-shadow-2xl md:text-6xl">
                    Busque comentários dos Santos Padres
                  </h1>

                  <p className="mx-auto mt-6 max-w-3xl text-lg font-semibold leading-8 text-[#f5ecd8] drop-shadow-lg md:text-xl">
                    Escolha o Evangelho, capítulo e intervalo de versículos para
                    montar a passagem enviada ao backend.
                  </p>
                </div>

                <Card className="border border-[#b38b59]/70 bg-[#f3e7cf]/88 shadow-2xl backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-center text-2xl font-bold text-zinc-950">
                      Buscar passagem
                    </CardTitle>
                  </CardHeader>

                  <CardContent>
                    <form
                      onSubmit={handleSubmit(onSubmit)}
                      className="space-y-7"
                    >
                      <div className="grid gap-6 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label className="text-sm font-semibold text-zinc-900">
                            Evangelho
                          </Label>

                          <Select
                            value={selectedGospelName}
                            onValueChange={(value) => {
                              setValue("gospel", value, {
                                shouldValidate: true,
                              });
                              setValue("chapter", 1, { shouldValidate: true });
                              setValue("startVerse", 1, {
                                shouldValidate: true,
                              });
                              setValue("endVerse", 1, { shouldValidate: true });
                            }}
                          >
                            <SelectTrigger className={selectTriggerClassName}>
                              <SelectValue placeholder="Selecione o Evangelho" />
                            </SelectTrigger>

                            <SelectContent className={selectContentClassName}>
                              {GOSPELS.map((gospel) => (
                                <SelectItem
                                  key={gospel.name}
                                  value={gospel.name}
                                  className={selectItemClassName}
                                >
                                  {gospel.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>

                          {errors.gospel && (
                            <p className={errorTextClassName}>
                              {errors.gospel.message}
                            </p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label className="text-sm font-semibold text-zinc-900">
                            Como deseja informar o Padre?
                          </Label>

                          <RadioGroup
                            value={fatherMode}
                            onValueChange={(value) => {
                              const nextMode = value as "preset" | "custom";

                              setValue("fatherMode", nextMode, {
                                shouldValidate: true,
                              });

                              if (nextMode === "preset") {
                                setValue("customFather", "", {
                                  shouldValidate: false,
                                });
                              }

                              if (nextMode === "custom") {
                                setValue("father", "", {
                                  shouldValidate: false,
                                });
                              }
                            }}
                            className="flex flex-col gap-3 rounded-lg border border-[#d8b76f] bg-white/55 p-4 shadow-sm"
                          >
                            <div className="flex items-center space-x-3">
                              <RadioGroupItem
                                value="preset"
                                id="preset"
                                className="border-zinc-900 text-zinc-900 data-[state=checked]:border-zinc-900 data-[state=checked]:bg-zinc-900 data-[state=checked]:text-white"
                              />
                              <Label
                                htmlFor="preset"
                                className="cursor-pointer text-sm font-medium text-zinc-900"
                              >
                                Selecionar da lista
                              </Label>
                            </div>

                            <div className="flex items-center space-x-3">
                              <RadioGroupItem
                                value="custom"
                                id="custom"
                                className="border-zinc-900 text-zinc-900 data-[state=checked]:border-zinc-900 data-[state=checked]:bg-zinc-900 data-[state=checked]:text-white"
                              />
                              <Label
                                htmlFor="custom"
                                className="cursor-pointer text-sm font-medium text-zinc-900"
                              >
                                Digitar manualmente
                              </Label>
                            </div>
                          </RadioGroup>
                        </div>
                      </div>

                      <div className="rounded-lg border border-[#d8b76f]/60 bg-white/35 p-4">
                        {fatherMode === "preset" ? (
                          <div className="space-y-2">
                            <Label className="text-sm font-semibold text-zinc-900">
                              Padre da Igreja, opcional
                            </Label>

                            <Select
                              onValueChange={(value) => {
                                setValue("father", value, {
                                  shouldValidate: true,
                                });
                                setValue("customFather", "", {
                                  shouldValidate: false,
                                });
                              }}
                            >
                              <SelectTrigger className={selectTriggerClassName}>
                                <SelectValue placeholder="Todos os Padres" />
                              </SelectTrigger>

                              <SelectContent className={selectContentClassName}>
                                {FATHERS.map((father) => (
                                  <SelectItem
                                    key={father}
                                    value={father}
                                    className={selectItemClassName}
                                  >
                                    {father}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <Label
                              htmlFor="customFather"
                              className="text-sm font-semibold text-zinc-900"
                            >
                              Digite o nome do Padre
                            </Label>

                            <Input
                              id="customFather"
                              placeholder="Ex: São João Damasceno"
                              className={inputClassName}
                              {...register("customFather")}
                            />

                            {errors.customFather && (
                              <p className={errorTextClassName}>
                                {errors.customFather.message}
                              </p>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="grid gap-5 md:grid-cols-3">
                        <div className="space-y-2">
                          <Label
                            htmlFor="chapter"
                            className="text-sm font-semibold text-zinc-900"
                          >
                            Capítulo
                          </Label>

                          <Input
                            id="chapter"
                            type="number"
                            min={1}
                            max={selectedGospel?.chapters}
                            placeholder="Ex: 4"
                            className={inputClassName}
                            {...register("chapter")}
                          />

                          {selectedGospel && (
                            <p className={helperTextClassName}>
                              {selectedGospel.name} possui{" "}
                              {selectedGospel.chapters} capítulos.
                            </p>
                          )}

                          {errors.chapter && (
                            <p className={errorTextClassName}>
                              {errors.chapter.message}
                            </p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label
                            htmlFor="startVerse"
                            className="text-sm font-semibold text-zinc-900"
                          >
                            Versículo inicial
                          </Label>

                          <Input
                            id="startVerse"
                            type="number"
                            min={1}
                            max={maxVerse}
                            placeholder="Ex: 12"
                            className={inputClassName}
                            {...register("startVerse")}
                          />

                          {maxVerse && (
                            <p className={helperTextClassName}>
                              Máximo neste capítulo: {maxVerse}
                            </p>
                          )}

                          {errors.startVerse && (
                            <p className={errorTextClassName}>
                              {errors.startVerse.message}
                            </p>
                          )}
                        </div>

                        <div className="space-y-2">
                          <Label
                            htmlFor="endVerse"
                            className="text-sm font-semibold text-zinc-900"
                          >
                            Versículo final
                          </Label>

                          <Input
                            id="endVerse"
                            type="number"
                            min={1}
                            max={maxVerse}
                            placeholder="Ex: 25"
                            className={inputClassName}
                            {...register("endVerse")}
                          />

                          {maxVerse && (
                            <p className={helperTextClassName}>
                              Máximo neste capítulo: {maxVerse}
                            </p>
                          )}

                          {errors.endVerse && (
                            <p className={errorTextClassName}>
                              {errors.endVerse.message}
                            </p>
                          )}
                        </div>
                      </div>

                      <Button
                        type="submit"
                        className="h-12 w-full bg-zinc-900 text-base font-semibold text-white shadow-lg hover:bg-zinc-800"
                      >
                        <Search className="mr-2 h-5 w-5" />
                        Buscar
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              </motion.div>
            ) : (
              <motion.div
                key="results-screen"
                initial={{ opacity: 0, y: 70 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 70 }}
                transition={{ duration: 0.35 }}
                className="mx-auto w-full max-w-4xl"
              >
                <div className="mb-6 flex items-center justify-between">
                  <Button
                    variant="outline"
                    onClick={handleBackToMenu}
                    className="border-[#b38b59] bg-[#f3e7cf]/90 font-semibold text-zinc-900 shadow-lg backdrop-blur-sm hover:bg-[#ead7b1]"
                  >
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Voltar ao menu
                  </Button>
                </div>

                <Card className="border border-[#b38b59]/70 bg-[#f3e7cf]/88 shadow-2xl backdrop-blur-md">
                  <CardHeader>
                    <CardTitle className="text-center text-2xl font-bold text-zinc-950">
                      Resultado da busca
                    </CardTitle>
                  </CardHeader>

                  <CardContent>
                    {loadingResults ? (
                      <div className="flex min-h-[180px] flex-col items-center justify-center gap-4">
                        <Loader2 className="h-8 w-8 animate-spin text-zinc-800" />
                        <p className="font-medium text-zinc-800">
                          Buscando comentários patrísticos...
                        </p>
                      </div>
                    ) : apiError ? (
                      <Alert variant="destructive">
                        <AlertDescription>{apiError}</AlertDescription>
                      </Alert>
                    ) : (
                      <QuoteResultCard quotes={quotes} />
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </main>
  );
}
