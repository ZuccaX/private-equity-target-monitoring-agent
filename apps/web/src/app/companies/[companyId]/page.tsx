"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import {
  CompanyCRMSection,
} from "@/components/company-crm-section";
import {
  CompanyDocumentsSection,
} from "@/components/company-documents-section";
import {
  CompanyRAGSection,
} from "@/components/company-rag-section";
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
  getCompany,
  listAgentRuns,
  listDrafts,
  listNewsArticles,
  listTriggers,
  runAgentForCompany,
} from "@/lib/api";
import type {
  AgentRunSummary,
  CompanyRead,
  EmailDraftRead,
  NewsArticleRead,
  TriggerRead,
} from "@/lib/api";


type CompanyDetailData = {
  company: CompanyRead;
  newsArticles: NewsArticleRead[];
  triggers: TriggerRead[];
  agentRuns: AgentRunSummary[];
  drafts: EmailDraftRead[];
};


type CompanyDetailState = {
  loadedCompanyId: number | null;
  company: CompanyRead | null;
  newsArticles: NewsArticleRead[];
  triggers: TriggerRead[];
  agentRuns: AgentRunSummary[];
  drafts: EmailDraftRead[];
  loadErrorMessage: string | null;
};


function formatDate(value: string | null): string {
  if (value === null) {
    return "N/A";
  }

  return new Date(value).toLocaleString();
}


function formatTriggerType(value: string): string {
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


function formatConfidenceScore(
  value: number
): string {
  return `${Math.round(value * 100)}%`;
}


function getErrorMessage(
  error: unknown,
  fallbackMessage: string
): string {
  return error instanceof Error
    ? error.message
    : fallbackMessage;
}


async function fetchCompanyDetailData(
  companyId: number
): Promise<CompanyDetailData> {
  const [
    companyData,
    newsData,
    triggerData,
    agentRunData,
    draftData,
  ] = await Promise.all([
    getCompany(companyId),
    listNewsArticles(companyId),
    listTriggers(companyId),
    listAgentRuns(),
    listDrafts(),
  ]);

  return {
    company: companyData,
    newsArticles: newsData,
    triggers: triggerData,
    agentRuns: agentRunData.filter(
      (agentRun) => {
        return agentRun.company_id === companyId;
      }
    ),
    drafts: draftData.filter((draft) => {
      return draft.company_id === companyId;
    }),
  };
}


function createLoadedState(
  companyId: number,
  data: CompanyDetailData
): CompanyDetailState {
  return {
    loadedCompanyId: companyId,
    company: data.company,
    newsArticles: data.newsArticles,
    triggers: data.triggers,
    agentRuns: data.agentRuns,
    drafts: data.drafts,
    loadErrorMessage: null,
  };
}


function createLoadErrorState(
  companyId: number,
  message: string
): CompanyDetailState {
  return {
    loadedCompanyId: companyId,
    company: null,
    newsArticles: [],
    triggers: [],
    agentRuns: [],
    drafts: [],
    loadErrorMessage: message,
  };
}


export default function CompanyDetailPage() {
  const params = useParams();

  const rawCompanyId = params.companyId;

  const companyId = Number(
    Array.isArray(rawCompanyId)
      ? rawCompanyId[0]
      : rawCompanyId
  );

  const isValidCompanyId =
    Number.isInteger(companyId)
    && companyId > 0;

  const [
    detailState,
    setDetailState,
  ] = useState<CompanyDetailState>(() => {
    return {
      loadedCompanyId: null,
      company: null,
      newsArticles: [],
      triggers: [],
      agentRuns: [],
      drafts: [],
      loadErrorMessage: null,
    };
  });

  const [
    isRunningAgent,
    setIsRunningAgent,
  ] = useState<boolean>(false);

  const [
    actionErrorMessage,
    setActionErrorMessage,
  ] = useState<string | null>(null);

  useEffect(() => {
    if (
      !Number.isInteger(companyId)
      || companyId <= 0
    ) {
      return;
    }

    let isCancelled = false;

    async function fetchInitialData(): Promise<void> {
      try {
        const data =
          await fetchCompanyDetailData(companyId);

        if (isCancelled) {
          return;
        }

        setDetailState(
          createLoadedState(
            companyId,
            data
          )
        );
      } catch (error) {
        if (isCancelled) {
          return;
        }

        const message = getErrorMessage(
          error,
          "Failed to load company detail."
        );

        setDetailState(
          createLoadErrorState(
            companyId,
            message
          )
        );
      }
    }

    void fetchInitialData();

    return () => {
      isCancelled = true;
    };
  }, [companyId]);

  async function handleRunAgent(): Promise<void> {
    if (!isValidCompanyId) {
      return;
    }

    try {
      setIsRunningAgent(true);
      setActionErrorMessage(null);

      await runAgentForCompany(companyId);

      const refreshedData =
        await fetchCompanyDetailData(companyId);

      setDetailState(
        createLoadedState(
          companyId,
          refreshedData
        )
      );
    } catch (error) {
      const message = getErrorMessage(
        error,
        "Failed to run agent."
      );

      setActionErrorMessage(message);
    } finally {
      setIsRunningAgent(false);
    }
  }

  if (!isValidCompanyId) {
    return (
      <main className="mx-auto w-full max-w-7xl space-y-6 p-6">
        <div
          role="alert"
          className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
        >
          Invalid company id.
        </div>

        <Link
          href="/companies"
          className={buttonVariants({
            variant: "outline",
          })}
        >
          Back to Companies
        </Link>
      </main>
    );
  }

  if (
    detailState.loadedCompanyId
    !== companyId
  ) {
    return (
      <main className="mx-auto w-full max-w-7xl space-y-6 p-6">
        <p className="text-sm text-muted-foreground">
          Loading company detail...
        </p>
      </main>
    );
  }

  if (
    detailState.loadErrorMessage
    !== null
  ) {
    return (
      <main className="mx-auto w-full max-w-7xl space-y-6 p-6">
        <div
          role="alert"
          className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
        >
          {detailState.loadErrorMessage}
        </div>

        <Link
          href="/companies"
          className={buttonVariants({
            variant: "outline",
          })}
        >
          Back to Companies
        </Link>
      </main>
    );
  }

  if (detailState.company === null) {
    return (
      <main className="mx-auto w-full max-w-7xl space-y-6 p-6">
        <p className="text-sm text-muted-foreground">
          Company not found.
        </p>

        <Link
          href="/companies"
          className={buttonVariants({
            variant: "outline",
          })}
        >
          Back to Companies
        </Link>
      </main>
    );
  }

  const {
    company,
    newsArticles,
    triggers,
    agentRuns,
    drafts,
  } = detailState;

  return (
    <main className="mx-auto w-full max-w-7xl space-y-6 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            {company.name}
          </h1>

          <p className="text-muted-foreground">
            Company detail view for target monitoring,
            trigger analysis, and agent-generated
            outreach.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Link
            href="/companies"
            className={buttonVariants({
              variant: "outline",
            })}
          >
            Back
          </Link>

          <Button
            type="button"
            disabled={isRunningAgent}
            onClick={() => {
              void handleRunAgent();
            }}
          >
            {isRunningAgent
              ? "Running..."
              : "Run Agent"}
          </Button>
        </div>
      </div>

      {actionErrorMessage !== null ? (
        <div
          role="alert"
          className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
        >
          {actionErrorMessage}
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>
            Company Profile
          </CardTitle>

          <CardDescription>
            Basic target company information used by
            the origination workflow.
          </CardDescription>
        </CardHeader>

        <CardContent className="grid gap-4 md:grid-cols-2">
          <div>
            <p className="text-sm text-muted-foreground">
              Sector
            </p>

            <p className="font-medium">
              {company.sector}
            </p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground">
              Country
            </p>

            <p className="font-medium">
              {company.country}
            </p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground">
              Domain
            </p>

            <p className="font-medium">
              {company.domain ?? "N/A"}
            </p>
          </div>

          <div>
            <p className="text-sm text-muted-foreground">
              Status
            </p>

            <Badge variant="secondary">
              {company.status}
            </Badge>
          </div>

          <div className="md:col-span-2">
            <p className="text-sm text-muted-foreground">
              Description
            </p>

            <p className="font-medium">
              {company.description
                ?? "No description available."}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            News Articles
          </CardTitle>

          <CardDescription>
            Seeded news records linked to this
            company.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {newsArticles.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No news articles found.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      Title
                    </TableHead>

                    <TableHead>
                      Source
                    </TableHead>

                    <TableHead>
                      Published
                    </TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {newsArticles.map((article) => (
                    <TableRow key={article.id}>
                      <TableCell>
                        <div className="space-y-1">
                          <p className="font-medium">
                            {article.title}
                          </p>

                          <p className="text-sm text-muted-foreground">
                            {article.summary}
                          </p>
                        </div>
                      </TableCell>

                      <TableCell>
                        <Badge variant="secondary">
                          {article.source}
                        </Badge>
                      </TableCell>

                      <TableCell>
                        {formatDate(
                          article.published_at
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Extracted Triggers
          </CardTitle>

          <CardDescription>
            Business events extracted from company
            news and used by scoring.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {triggers.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No triggers found.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      Type
                    </TableHead>

                    <TableHead>
                      Title
                    </TableHead>

                    <TableHead>
                      Confidence
                    </TableHead>

                    <TableHead>
                      Detected
                    </TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {triggers.map((trigger) => (
                    <TableRow key={trigger.id}>
                      <TableCell>
                        <Badge>
                          {formatTriggerType(
                            trigger.trigger_type
                          )}
                        </Badge>
                      </TableCell>

                      <TableCell>
                        <div className="space-y-1">
                          <p className="font-medium">
                            {trigger.title}
                          </p>

                          <p className="text-sm text-muted-foreground">
                            {trigger.description}
                          </p>
                        </div>
                      </TableCell>

                      <TableCell>
                        {formatConfidenceScore(
                          trigger.confidence_score
                        )}
                      </TableCell>

                      <TableCell>
                        {formatDate(
                          trigger.detected_at
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <CompanyCRMSection
        companyId={companyId}
      />

      <CompanyDocumentsSection
        companyId={companyId}
      />

      <CompanyRAGSection
        companyId={companyId}
      />

      <Card>
        <CardHeader>
          <CardTitle>
            Agent Runs
          </CardTitle>

          <CardDescription>
            Previous workflow executions for this
            company.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {agentRuns.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No agent runs found.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      Run ID
                    </TableHead>

                    <TableHead>
                      Status
                    </TableHead>

                    <TableHead>
                      Score
                    </TableHead>

                    <TableHead>
                      Draft Status
                    </TableHead>

                    <TableHead>
                      Created
                    </TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {agentRuns.map((agentRun) => (
                    <TableRow key={agentRun.id}>
                      <TableCell className="font-medium">
                        {agentRun.id}
                      </TableCell>

                      <TableCell>
                        <Badge variant="secondary">
                          {agentRun.status}
                        </Badge>
                      </TableCell>

                      <TableCell>
                        {agentRun.overall_score
                          ?? "N/A"}
                      </TableCell>

                      <TableCell>
                        {agentRun.email_draft_status
                          ?? "N/A"}
                      </TableCell>

                      <TableCell>
                        {formatDate(
                          agentRun.created_at
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Email Drafts
          </CardTitle>

          <CardDescription>
            Outreach drafts generated for this
            company.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {drafts.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No email drafts found.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>
                      Draft ID
                    </TableHead>

                    <TableHead>
                      Subject
                    </TableHead>

                    <TableHead>
                      Status
                    </TableHead>

                    <TableHead>
                      Created
                    </TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {drafts.map((draft) => (
                    <TableRow key={draft.id}>
                      <TableCell className="font-medium">
                        {draft.id}
                      </TableCell>

                      <TableCell>
                        {draft.subject}
                      </TableCell>

                      <TableCell>
                        <Badge variant="secondary">
                          {draft.status}
                        </Badge>
                      </TableCell>

                      <TableCell>
                        {formatDate(
                          draft.created_at
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </main>
  );
}