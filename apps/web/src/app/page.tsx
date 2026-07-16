"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  getDashboardSummary,
  listAgentRuns,
  listTriggers,
} from "@/lib/api";
import type {
  AgentRunSummary,
  DashboardSummaryRead,
  TriggerRead,
} from "@/lib/api";


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
      return part.charAt(0).toUpperCase() + part.slice(1);
    })
    .join(" ");
}


export default function DashboardPage() {
  const [summary, setSummary] =
    useState<DashboardSummaryRead | null>(null);

  const [recentAgentRuns, setRecentAgentRuns] =
    useState<AgentRunSummary[]>([]);

  const [recentTriggers, setRecentTriggers] =
    useState<TriggerRead[]>([]);

  const [isLoading, setIsLoading] =
    useState<boolean>(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard(): Promise<void> {
      try {
        setIsLoading(true);
        setErrorMessage(null);

        const [
          summaryData,
          agentRunsData,
          triggersData,
        ] = await Promise.all([
          getDashboardSummary(),
          listAgentRuns(),
          listTriggers(),
        ]);

        setSummary(summaryData);
        setRecentAgentRuns(agentRunsData.slice(0, 5));
        setRecentTriggers(triggersData.slice(0, 5));
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Failed to load dashboard.";

        setErrorMessage(message);
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  if (isLoading) {
    return (
      <main className="p-6">
        <p className="text-sm text-muted-foreground">
          Loading dashboard...
        </p>
      </main>
    );
  }

  if (errorMessage !== null) {
    return (
      <main className="p-6">
        <p className="text-sm text-red-500">
          {errorMessage}
        </p>
      </main>
    );
  }

  if (summary === null) {
    return (
      <main className="p-6">
        <p className="text-sm text-muted-foreground">
          Dashboard summary is unavailable.
        </p>
      </main>
    );
  }

  const averageScore =
    summary.average_priority_score === null
      ? "N/A"
      : summary.average_priority_score.toFixed(1);

  return (
    <main className="space-y-8 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Origination Dashboard
          </h1>

          <p className="text-muted-foreground">
            Monitor target companies, business triggers, agent runs,
            and human-approved outreach drafts.
          </p>
        </div>

        <Link
          href="/companies"
          className={buttonVariants()}
        >
          View Target Companies
        </Link>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Target Companies"
          value={summary.total_companies}
          description="Active companies under monitoring"
        />

        <MetricCard
          title="News Articles"
          value={summary.total_news_articles}
          description="External company signals ingested"
        />

        <MetricCard
          title="Business Triggers"
          value={summary.total_triggers}
          description="Detected origination events"
        />

        <MetricCard
          title="Agent Runs"
          value={summary.total_agent_runs}
          description={`${summary.completed_agent_runs} completed`}
        />

        <MetricCard
          title="Pending Drafts"
          value={summary.pending_drafts}
          description="Waiting for human approval"
        />

        <MetricCard
          title="Approved Drafts"
          value={summary.approved_drafts}
          description="Approved outreach drafts"
        />

        <MetricCard
          title="Average Score"
          value={averageScore}
          description="Average priority score"
        />

        <MetricCard
          title="Failed Runs"
          value={summary.failed_agent_runs}
          description="Workflow executions requiring review"
        />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent Agent Runs</CardTitle>

            <CardDescription>
              Latest trigger-aware workflow executions.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {recentAgentRuns.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No agent runs found.
              </p>
            ) : (
              recentAgentRuns.map((agentRun) => (
                <div
                  key={agentRun.id}
                  className="flex flex-col gap-3 rounded-lg border p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="space-y-1">
                    <Link
                      href={`/companies/${agentRun.company_id}`}
                      className="font-medium hover:underline"
                    >
                      {agentRun.company_name}
                    </Link>

                    <p className="text-sm text-muted-foreground">
                      Run #{agentRun.id} · Score{" "}
                      {agentRun.overall_score ?? "N/A"}
                    </p>

                    <p className="text-xs text-muted-foreground">
                      {formatDate(agentRun.created_at)}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary">
                      {agentRun.status}
                    </Badge>

                    {agentRun.email_draft_status !== null ? (
                      <Badge variant="outline">
                        {agentRun.email_draft_status}
                      </Badge>
                    ) : null}
                  </div>
                </div>
              ))
            )}

            <Link
              href="/agent-runs"
              className={buttonVariants({
                variant: "outline",
              })}
            >
              View All Agent Runs
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Triggers</CardTitle>

            <CardDescription>
              Latest business signals used by the scoring workflow.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {recentTriggers.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No triggers found.
              </p>
            ) : (
              recentTriggers.map((trigger) => (
                <div
                  key={trigger.id}
                  className="space-y-2 rounded-lg border p-4"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge>
                      {formatTriggerType(
                        trigger.trigger_type
                      )}
                    </Badge>

                    <span className="text-sm text-muted-foreground">
                      {Math.round(
                        trigger.confidence_score * 100
                      )}
                      % confidence
                    </span>
                  </div>

                  <Link
                    href={`/companies/${trigger.company_id}`}
                    className="block font-medium hover:underline"
                  >
                    {trigger.title}
                  </Link>

                  <p className="line-clamp-2 text-sm text-muted-foreground">
                    {trigger.description ??
                      "No trigger description available."}
                  </p>
                </div>
              ))
            )}

            <Link
              href="/triggers"
              className={buttonVariants({
                variant: "outline",
              })}
            >
              View All Triggers
            </Link>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}


type MetricCardProps = {
  title: string;
  value: number | string;
  description: string;
};


function MetricCard({
  title,
  value,
  description,
}: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>

        <CardTitle className="text-3xl">
          {value}
        </CardTitle>
      </CardHeader>

      <CardContent>
        <p className="text-sm text-muted-foreground">
          {description}
        </p>
      </CardContent>
    </Card>
  );
}