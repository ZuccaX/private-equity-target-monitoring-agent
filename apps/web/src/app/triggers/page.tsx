"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
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
  TriggerRead,
  listTriggers,
} from "@/lib/api";

function formatTriggerType(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatConfidenceScore(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

export default function TriggersPage() {
  const [triggers, setTriggers] = useState<TriggerRead[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadTriggers(): Promise<void> {
      try {
        setIsLoading(true);
        setErrorMessage(null);

        const data = await listTriggers();

        setTriggers(data);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Failed to load triggers.";

        setErrorMessage(message);
      } finally {
        setIsLoading(false);
      }
    }

    void loadTriggers();
  }, []);

  return (
    <main className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Triggers
        </h1>
        <p className="text-muted-foreground">
          Business trigger events extracted from company news articles.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Extracted Business Triggers</CardTitle>
          <CardDescription>
            These records are used by the trigger-aware scoring and email
            generation workflow.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">
              Loading triggers...
            </p>
          ) : errorMessage !== null ? (
            <p className="text-sm text-red-500">{errorMessage}</p>
          ) : triggers.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No triggers found.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Company ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Detected</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {triggers.map((trigger) => (
                  <TableRow key={trigger.id}>
                    <TableCell className="font-medium">
                      {trigger.id}
                    </TableCell>

                    <TableCell>{trigger.company_id}</TableCell>

                    <TableCell>
                      <Badge>
                        {formatTriggerType(trigger.trigger_type)}
                      </Badge>
                    </TableCell>

                    <TableCell>
                      <div className="space-y-1">
                        <p className="font-medium">{trigger.title}</p>
                        <p className="max-w-2xl text-sm text-muted-foreground">
                          {trigger.description}
                        </p>
                      </div>
                    </TableCell>

                    <TableCell>
                      {formatConfidenceScore(trigger.confidence_score)}
                    </TableCell>

                    <TableCell>
                      {formatDate(trigger.detected_at)}
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