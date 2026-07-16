"use client";

import Link from "next/link";
import {
  type FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import { Badge } from "@/components/ui/badge";
import {
  Button,
  buttonVariants,
} from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  listCompanies,
  retrieveRAGContext,
} from "@/lib/api";
import type {
  CompanyRead,
  RAGRetrievalRequest,
  RAGRetrievalResponse,
} from "@/lib/api";


function formatLabel(value: string): string {
  return value
    .split("_")
    .map((part) => {
      return (
        part.charAt(0).toUpperCase()
        + part.slice(1)
      );
    })
    .join(" ");
}


function formatSimilarity(value: number): string {
  return value.toFixed(4);
}


export default function RAGExplorerPage() {
  const [companies, setCompanies] =
    useState<CompanyRead[]>([]);

  const [query, setQuery] =
    useState<string>(
      "What are the main investment opportunities and risks?"
    );

  const [selectedCompanyId, setSelectedCompanyId] =
    useState<string>("");

  const [topK, setTopK] =
    useState<number>(3);

  const [result, setResult] =
    useState<RAGRetrievalResponse | null>(null);

  const [
    isLoadingCompanies,
    setIsLoadingCompanies,
  ] = useState<boolean>(true);

  const [isSearching, setIsSearching] =
    useState<boolean>(false);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function loadCompanies(): Promise<void> {
      try {
        setIsLoadingCompanies(true);
        setErrorMessage(null);

        const companiesData =
          await listCompanies();

        if (!isCancelled) {
          setCompanies(companiesData);
          setSelectedCompanyId((current) => {
            return current || String(companiesData[0]?.id ?? "");
          });
        }
      } catch (error) {
        if (isCancelled) {
          return;
        }

        const message =
          error instanceof Error
            ? error.message
            : "Failed to load companies.";

        setErrorMessage(message);
      } finally {
        if (!isCancelled) {
          setIsLoadingCompanies(false);
        }
      }
    }

    void loadCompanies();

    return () => {
      isCancelled = true;
    };
  }, []);

  const companyNameById = useMemo(() => {
    return new Map<number, string>(
      companies.map((company) => {
        return [
          company.id,
          company.name,
        ];
      })
    );
  }, [companies]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ): Promise<void> {
    event.preventDefault();

    const normalizedQuery = query.trim();

    if (normalizedQuery === "") {
      setErrorMessage(
        "Enter a search question before retrieving context."
      );

      return;
    }

    if (selectedCompanyId === "") {
      setErrorMessage("Select a company before retrieving context.");
      return;
    }

    const request: RAGRetrievalRequest = {
      query: normalizedQuery,
      company_id: Number(selectedCompanyId),
      top_k: topK,
    };

    try {
      setIsSearching(true);
      setErrorMessage(null);
      setResult(null);

      const response =
        await retrieveRAGContext(request);

      setResult(response);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to retrieve RAG context.";

      setErrorMessage(message);
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-7xl space-y-8 p-6">
      <section>
        <h1 className="text-3xl font-bold tracking-tight">
          RAG Explorer
        </h1>

        <p className="mt-2 text-muted-foreground">
          Search internal documents using pgvector
          and inspect the context supplied to the
          origination agent.
        </p>
      </section>

      <Card>
        <CardHeader>
          <CardTitle>Retrieval Query</CardTitle>

          <CardDescription>
            Choose one company. RAG retrieval is deliberately
            company-scoped to prevent cross-company context leakage.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form
            onSubmit={(event) => {
              void handleSubmit(event);
            }}
            className="space-y-5"
          >
            <div className="space-y-2">
              <label
                htmlFor="rag-query"
                className="text-sm font-medium"
              >
                Question
              </label>

              <textarea
                id="rag-query"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                }}
                rows={4}
                maxLength={2000}
                placeholder="Ask about investment opportunities, risks, management, growth, or market position."
                className="flex w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm outline-none placeholder:text-muted-foreground focus-visible:ring-1 focus-visible:ring-ring"
              />

              <p className="text-xs text-muted-foreground">
                {query.length}/2000 characters
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label
                  htmlFor="rag-company"
                  className="text-sm font-medium"
                >
                  Company scope
                </label>

                <select
                  id="rag-company"
                  value={selectedCompanyId}
                  disabled={isLoadingCompanies}
                  onChange={(event) => {
                    setSelectedCompanyId(
                      event.target.value
                    );
                  }}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  {companies.map((company) => (
                    <option
                      key={company.id}
                      value={company.id}
                    >
                      {company.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label
                  htmlFor="rag-top-k"
                  className="text-sm font-medium"
                >
                  Number of sources
                </label>

                <select
                  id="rag-top-k"
                  value={topK}
                  onChange={(event) => {
                    setTopK(
                      Number(event.target.value)
                    );
                  }}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  <option value={1}>Top 1</option>
                  <option value={3}>Top 3</option>
                  <option value={5}>Top 5</option>
                  <option value={10}>Top 10</option>
                </select>
              </div>
            </div>

            <Button
              type="submit"
              disabled={
                isSearching
                || query.trim() === ""
                || selectedCompanyId === ""
              }
            >
              {isSearching
                ? "Retrieving..."
                : "Retrieve Context"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {errorMessage !== null ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {errorMessage}
        </div>
      ) : null}

      {result === null ? (
        <Card>
          <CardHeader>
            <CardTitle>
              No Retrieval Performed
            </CardTitle>

            <CardDescription>
              Submit a question above to inspect
              pgvector retrieval results.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>
                  Retrieved Sources
                </CardDescription>

                <CardTitle className="text-3xl">
                  {result.result_count}
                </CardTitle>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>
                  Company Scope
                </CardDescription>

                <CardTitle className="text-lg">
                  {companyNameById.get(result.company_id)
                    ?? `Company ${result.company_id}`}
                </CardTitle>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>
                  Requested Top-K
                </CardDescription>

                <CardTitle className="text-3xl">
                  {result.top_k}
                </CardTitle>
              </CardHeader>
            </Card>
          </section>

          {result.status === "empty" ? (
            <div className="rounded-md border p-4 text-sm text-muted-foreground">
              No eligible company-scoped context met the retrieval filters.
            </div>
          ) : null}

          {result.fallback_used || result.warnings.length > 0 ? (
            <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-4 text-sm">
              <p>
                Effective model: {result.effective_model}
              </p>
              {result.warnings.map((warning) => (
                <p key={warning}>{formatLabel(warning)}</p>
              ))}
            </div>
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle>
                Assembled RAG Context
              </CardTitle>

              <CardDescription>
                This is the context block that can
                later be supplied to an LLM prompt.
              </CardDescription>
            </CardHeader>

            <CardContent>
              <pre className="max-h-[36rem] overflow-auto whitespace-pre-wrap rounded-md border bg-muted/40 p-4 font-mono text-sm leading-6">
                {result.context}
              </pre>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Retrieved Sources</CardTitle>

              <CardDescription>
                Structured evidence returned by the
                vector search service.
              </CardDescription>
            </CardHeader>

            <CardContent>
              {result.sources.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No indexed document chunks were found.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>
                          Document
                        </TableHead>

                        <TableHead>
                          Company
                        </TableHead>

                        <TableHead>
                          Type
                        </TableHead>

                        <TableHead>
                          Chunk
                        </TableHead>

                        <TableHead>
                          Similarity
                        </TableHead>

                        <TableHead className="text-right">
                          Action
                        </TableHead>
                      </TableRow>
                    </TableHeader>

                    <TableBody>
                      {result.sources.map(
                        (source) => (
                          <TableRow
                            key={source.chunk_id}
                          >
                            <TableCell>
                              <div className="space-y-1">
                                <p className="font-medium">
                                  {source.document_title}
                                </p>

                                <p className="max-w-md truncate text-xs text-muted-foreground">
                                  {source.chunk_text}
                                </p>
                              </div>
                            </TableCell>

                            <TableCell>
                              <Link
                                href={
                                  `/companies/${source.company_id}`
                                }
                                className="hover:underline"
                              >
                                {companyNameById.get(
                                  source.company_id
                                )
                                  ?? `Company ${source.company_id}`}
                              </Link>
                            </TableCell>

                            <TableCell>
                              <Badge variant="secondary">
                                {formatLabel(
                                  source.document_type
                                )}
                              </Badge>
                            </TableCell>

                            <TableCell>
                              {source.chunk_index}
                            </TableCell>

                            <TableCell>
                              <Badge
                                variant={
                                  source.similarity > 0
                                    ? "default"
                                    : "outline"
                                }
                              >
                                {formatSimilarity(
                                  source.similarity
                                )}
                              </Badge>
                            </TableCell>

                            <TableCell className="text-right">
                              <Link
                                href="/documents"
                                className={buttonVariants({
                                  variant: "outline",
                                  size: "sm",
                                })}
                              >
                                Documents
                              </Link>
                            </TableCell>
                          </TableRow>
                        )
                      )}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>

          <section className="space-y-4">
            {result.sources.map(
              (source, index) => (
                <Card key={source.chunk_id}>
                  <CardHeader>
                    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                      <div>
                        <CardTitle className="text-lg">
                          Source {index + 1}:{" "}
                          {source.document_title}
                        </CardTitle>

                        <CardDescription>
                          Chunk {source.chunk_index}
                          {" · "}
                          {source.token_count} words
                          {" · "}
                          {source.embedding_model}
                        </CardDescription>
                      </div>

                      <Badge variant="outline">
                        Similarity{" "}
                        {formatSimilarity(
                          source.similarity
                        )}
                      </Badge>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    <div className="whitespace-pre-wrap rounded-md border bg-muted/30 p-4 text-sm leading-7">
                      {source.chunk_text}
                    </div>

                    <div>
                      <p className="mb-1 text-sm font-medium">
                        Source Path
                      </p>

                      <code className="block break-all rounded-md bg-muted p-3 text-xs">
                        {source.source_path ?? "N/A"}
                      </code>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Link
                        href={
                          `/companies/${source.company_id}`
                        }
                        className={buttonVariants({
                          variant: "outline",
                          size: "sm",
                        })}
                      >
                        View Company
                      </Link>

                      <Link
                        href="/documents"
                        className={buttonVariants({
                          variant: "secondary",
                          size: "sm",
                        })}
                      >
                        View Documents
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              )
            )}
          </section>
        </>
      )}
    </main>
  );
}
