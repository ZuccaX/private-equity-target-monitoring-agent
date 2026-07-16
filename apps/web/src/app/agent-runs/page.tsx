"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { listAgentRuns, type AgentRunSummary } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
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

export default function AgentRunsPage() {
  const [agentRuns, setAgentRuns] = useState<AgentRunSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function fetchAgentRuns(): Promise<void> {
      try {
        const agentRunsData =
          await listAgentRuns();

        if (isCancelled) {
          return;
        }

        setAgentRuns(agentRunsData);
      } catch (error) {
        if (isCancelled) {
          return;
        }

        const message =
          error instanceof Error
            ? error.message
            : "Failed to load agent runs.";

        setErrorMessage(message);
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void fetchAgentRuns();

    return () => {
      isCancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto max-w-7xl p-6">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Agent Runs</h1>
          <p className="mt-2 text-muted-foreground">
            Track origination agent executions, priority scores, and generated
            outreach drafts.
          </p>
        </div>

        <Link className={buttonVariants({ variant: "outline" })} href="/companies">
          Run New Agent
        </Link>
      </div>

      {errorMessage !== null && (
        <div className="mb-4 rounded-md border p-4 text-sm">
          {errorMessage}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Workflow History</CardTitle>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading agent runs...</p>
          ) : agentRuns.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No agent runs yet. Go to Companies and click Run Agent.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Run ID</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Score</TableHead>
                  <TableHead>Draft Status</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {agentRuns.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell className="font-medium">#{run.id}</TableCell>
                    <TableCell>{run.company_name}</TableCell>
                    <TableCell>{run.run_type}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{run.status}</Badge>
                    </TableCell>
                    <TableCell className="text-right font-semibold">
                      {run.overall_score ?? "-"}
                    </TableCell>
                    <TableCell>
                      {run.email_draft_status !== null ? (
                        <Badge variant="secondary">
                          {run.email_draft_status}
                        </Badge>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(run.created_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
