"use client";

import Link from "next/link";
import {
  type FormEvent,
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
  retrieveRAGContext,
} from "@/lib/api";
import type {
  RAGRetrievalResponse,
  RAGRetrievalRequest,
} from "@/lib/api";

type CompanyRAGSectionProps = {
  companyId: number;
};

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

export function CompanyRAGSection({
  companyId,
}: CompanyRAGSectionProps) {
  const [query, setQuery] = useState<string>(
    "What are the main investment opportunities and risks?"
  );

  const [topK, setTopK] = useState<number>(3);

  const [result, setResult] =
    useState<RAGRetrievalResponse | null>(null);

  const [isSearching, setIsSearching] =
    useState<boolean>(false);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ): Promise<void> {
    event.preventDefault();

    const normalizedQuery = query.trim();

    if (normalizedQuery === "") {
      setErrorMessage(
        "Enter a question before retrieving context."
      );
      return;
    }

    const request: RAGRetrievalRequest = {
      query: normalizedQuery,
      company_id: companyId,
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
          : "Failed to retrieve company document context.";

      setErrorMessage(message);
    } finally {
      setIsSearching(false);
    }
  }

  return (
    <section className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>
            Ask Internal Documents
          </CardTitle>

          <CardDescription>
            Retrieve evidence from internal documents
            linked specifically to this company.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form
            className="space-y-5"
            onSubmit={(event) => {
              void handleSubmit(event);
            }}
          >
            <div className="space-y-2">
              <label
                htmlFor={`company-rag-query-${companyId}`}
                className="text-sm font-medium"
              >
                Investment question
              </label>

              <textarea
                id={`company-rag-query-${companyId}`}
                value={query}
                rows={4}
                maxLength={2000}
                placeholder="Ask about risks, growth, management, customers, market position, or investment opportunities."
                className="flex w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm outline-none placeholder:text-muted-foreground focus-visible:ring-1 focus-visible:ring-ring"
                onChange={(event) => {
                  setQuery(event.target.value);
                }}
              ></textarea>

              <div className="flex items-center justify-between gap-4">
                <p className="text-xs text-muted-foreground">
                  Retrieval is restricted to company{" "}
                  {companyId}.
                </p>

                <p className="text-xs text-muted-foreground">
                  {query.length}/2000
                </p>
              </div>
            </div>

            <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <div className="w-full space-y-2 sm:w-48">
                <label
                  htmlFor={`company-rag-top-k-${companyId}`}
                  className="text-sm font-medium"
                >
                  Number of sources
                </label>

                <select
                  id={`company-rag-top-k-${companyId}`}
                  value={topK}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  onChange={(event) => {
                    setTopK(
                      Number(event.target.value)
                    );
                  }}
                >
                  <option value={1}>
                    Top 1
                  </option>

                  <option value={3}>
                    Top 3
                  </option>

                  <option value={5}>
                    Top 5
                  </option>

                  <option value={10}>
                    Top 10
                  </option>
                </select>
              </div>

              <Button
                type="submit"
                disabled={
                  isSearching
                  || query.trim() === ""
                }
              >
                {isSearching
                  ? "Retrieving..."
                  : "Retrieve Evidence"}
              </Button>

              <Link
                href="/rag"
                className={buttonVariants({
                  variant: "outline",
                })}
              >
                Open RAG Explorer
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>

      {errorMessage !== null ? (
        <div
          role="alert"
          className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
        >
          {errorMessage}
        </div>
      ) : null}

      {result !== null ? (
        <>
          {result.status === "empty" ? (
            <div className="rounded-md border p-4 text-sm text-muted-foreground">
              No eligible context met the company-scoped retrieval filters.
            </div>
          ) : null}

          {result.fallback_used || result.warnings.length > 0 ? (
            <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-4 text-sm">
              <p>Effective model: {result.effective_model}</p>
              {result.warnings.map((warning) => (
                <p key={warning}>{formatLabel(warning)}</p>
              ))}
            </div>
          ) : null}

          <Card>
            <CardHeader>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <CardTitle>
                    Retrieved Context
                  </CardTitle>

                  <CardDescription>
                    Context assembled from this
                    company&apos;s indexed documents.
                  </CardDescription>
                </div>

                <Badge variant="secondary">
                  {result.result_count} sources
                </Badge>
              </div>
            </CardHeader>

            <CardContent>
              <pre className="max-h-[32rem] overflow-auto whitespace-pre-wrap rounded-md border bg-muted/40 p-4 font-mono text-sm leading-6">
                {result.context}
              </pre>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>
                Supporting Sources
              </CardTitle>

              <CardDescription>
                Document chunks selected by the
                pgvector retrieval service.
              </CardDescription>
            </CardHeader>

            <CardContent>
              {result.sources.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No relevant indexed document chunks
                  were found.
                </p>
              ) : (
                <div className="space-y-4">
                  {result.sources.map(
                    (source, index) => (
                      <article
                        key={source.chunk_id}
                        className="space-y-4 rounded-lg border p-4"
                      >
                        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                          <div>
                            <p className="font-medium">
                              Source {index + 1}:{" "}
                              {source.document_title}
                            </p>

                            <p className="mt-1 text-sm text-muted-foreground">
                              {formatLabel(
                                source.document_type
                              )}
                              {" · "}
                              Chunk{" "}
                              {source.chunk_index}
                              {" · "}
                              {source.token_count} tokens
                            </p>
                          </div>

                          <div className="flex flex-wrap gap-2">
                            <Badge variant="outline">
                              Similarity{" "}
                              {formatSimilarity(
                                source.similarity
                              )}
                            </Badge>

                            <Badge variant="secondary">
                              {source.source_system}
                            </Badge>
                          </div>
                        </div>

                        <div className="whitespace-pre-wrap rounded-md bg-muted/30 p-4 text-sm leading-7">
                          {source.chunk_text}
                        </div>

                        <div>
                          <p className="mb-1 text-sm font-medium">
                            Source path
                          </p>

                          <code className="block break-all rounded-md bg-muted p-3 text-xs">
                            {source.source_path ?? "N/A"}
                          </code>
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <Link
                            href="/documents"
                            className={buttonVariants({
                              variant: "outline",
                              size: "sm",
                            })}
                          >
                            View Documents
                          </Link>

                          <Link
                            href="/rag"
                            className={buttonVariants({
                              variant: "secondary",
                              size: "sm",
                            })}
                          >
                            Open Full Explorer
                          </Link>
                        </div>
                      </article>
                    )
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </section>
  );
}
