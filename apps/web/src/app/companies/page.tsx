"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  listCompanies,
  runAgentForCompany,
  type CompanyRead,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
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

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<CompanyRead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [runningCompanyId, setRunningCompanyId] = useState<number | null>(null);

  async function handleRunAgent(companyId: number): Promise<void> {
    try {
      setRunningCompanyId(companyId);
      setErrorMessage(null);

      await runAgentForCompany(companyId);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to run agent."
      );
    } finally {
      setRunningCompanyId(null);
    }
  }

  useEffect(() => {
    let isCancelled = false;

    async function fetchCompanies(): Promise<void> {
      try {
        const companiesData =
          await listCompanies();

        if (isCancelled) {
          return;
        }

        setCompanies(companiesData);
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
          setIsLoading(false);
        }
      }
    }

    void fetchCompanies();

    return () => {
      isCancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto max-w-7xl p-6">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">Target Companies</h1>
          <p className="mt-2 text-muted-foreground">
            Review target companies, recent business context, and trigger the
            origination agent workflow.
          </p>
        </div>

        <Link className={buttonVariants({ variant: "outline" })} href="/agent-runs">
          View Agent Runs
        </Link>
      </div>

      {errorMessage !== null && (
        <div className="mb-4 rounded-md border p-4 text-sm">
          {errorMessage}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Company Pipeline</CardTitle>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading companies...</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company</TableHead>
                  <TableHead>Sector</TableHead>
                  <TableHead>Country</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {companies.map((company) => (
                  <TableRow key={company.id}>
                    <TableCell>
                      <div className="font-medium">{company.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {company.website ?? company.domain ?? "No website"}
                      </div>
                    </TableCell>

                    <TableCell>{company.sector}</TableCell>
                    <TableCell>{company.country}</TableCell>

                    <TableCell>
                      <Badge variant="outline">{company.status}</Badge>
                    </TableCell>

                    <TableCell className="max-w-md">
                      <span className="line-clamp-2 text-sm text-muted-foreground">
                        {company.description ?? "No description available."}
                      </span>
                    </TableCell>

                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        onClick={() => void handleRunAgent(company.id)}
                        disabled={runningCompanyId === company.id}
                      >
                        {runningCompanyId === company.id
                          ? "Running..."
                          : "Run Agent"}
                      </Button>
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
