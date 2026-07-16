"use client";

import Link from "next/link";
import {
  useEffect,
  useMemo,
  useState,
} from "react";

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
  listCompanies,
  listCRMContacts,
  listCRMInteractions,
} from "@/lib/api";
import type {
  CompanyRead,
  ContactRead,
  CRMInteractionRead,
} from "@/lib/api";


function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}


function formatInteractionType(
  value: string
): string {
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


function getRelationshipLabel(
  value: number
): string {
  if (value >= 81) {
    return "Strong";
  }

  if (value >= 61) {
    return "Good";
  }

  if (value >= 41) {
    return "Moderate";
  }

  if (value >= 21) {
    return "Weak";
  }

  return "Minimal";
}


function getSentimentLabel(
  value: number
): string {
  if (value >= 0.6) {
    return "Positive";
  }

  if (value >= 0.2) {
    return "Slightly Positive";
  }

  if (value <= -0.6) {
    return "Negative";
  }

  if (value <= -0.2) {
    return "Slightly Negative";
  }

  return "Neutral";
}


function getSentimentVariant(
  value: number
): "default" | "secondary" | "destructive" | "outline" {
  if (value >= 0.2) {
    return "default";
  }

  if (value <= -0.2) {
    return "destructive";
  }

  return "secondary";
}


export default function CRMPage() {
  const [companies, setCompanies] =
    useState<CompanyRead[]>([]);

  const [contacts, setContacts] =
    useState<ContactRead[]>([]);

  const [interactions, setInteractions] =
    useState<CRMInteractionRead[]>([]);

  const [selectedCompanyId, setSelectedCompanyId] =
    useState<string>("all");

  const [isLoading, setIsLoading] =
    useState<boolean>(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadCRMData(): Promise<void> {
      try {
        setIsLoading(true);
        setErrorMessage(null);

        const [
          companiesData,
          contactsData,
          interactionsData,
        ] = await Promise.all([
          listCompanies(),
          listCRMContacts(),
          listCRMInteractions(),
        ]);

        setCompanies(companiesData);
        setContacts(contactsData);
        setInteractions(interactionsData);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Failed to load CRM data.";

        setErrorMessage(message);
      } finally {
        setIsLoading(false);
      }
    }

    void loadCRMData();
  }, []);

  const companyNameById = useMemo(() => {
    return new Map(
      companies.map((company) => {
        return [
          company.id,
          company.name,
        ];
      })
    );
  }, [companies]);

  const selectedCompanyIdNumber =
    selectedCompanyId === "all"
      ? null
      : Number(selectedCompanyId);

  const filteredContacts = useMemo(() => {
    if (selectedCompanyIdNumber === null) {
      return contacts;
    }

    return contacts.filter((contact) => {
      return (
        contact.company_id
        === selectedCompanyIdNumber
      );
    });
  }, [
    contacts,
    selectedCompanyIdNumber,
  ]);

  const filteredInteractions = useMemo(() => {
    if (selectedCompanyIdNumber === null) {
      return interactions;
    }

    return interactions.filter((interaction) => {
      return (
        interaction.company_id
        === selectedCompanyIdNumber
      );
    });
  }, [
    interactions,
    selectedCompanyIdNumber,
  ]);

  const averageRelationshipStrength =
    useMemo(() => {
      if (filteredContacts.length === 0) {
        return null;
      }

      const total = filteredContacts.reduce(
        (sum, contact) => {
          return (
            sum
            + contact.relationship_strength
          );
        },
        0
      );

      return Math.round(
        total / filteredContacts.length
      );
    }, [filteredContacts]);

  const positiveInteractionCount =
    useMemo(() => {
      return filteredInteractions.filter(
        (interaction) => {
          return (
            interaction.sentiment_score >= 0.2
          );
        }
      ).length;
    }, [filteredInteractions]);

  if (isLoading) {
    return (
      <main className="p-6">
        <p className="text-sm text-muted-foreground">
          Loading CRM data...
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

  return (
    <main className="space-y-8 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            CRM Relationships
          </h1>

          <p className="text-muted-foreground">
            Review target company contacts and
            historical interactions used by the
            CRM-aware scoring workflow.
          </p>
        </div>

        <div className="w-full md:w-72">
          <label
            htmlFor="company-filter"
            className="mb-2 block text-sm font-medium"
          >
            Filter by company
          </label>

          <select
            id="company-filter"
            value={selectedCompanyId}
            onChange={(event) => {
              setSelectedCompanyId(
                event.target.value
              );
            }}
            className="h-10 w-full rounded-md border bg-background px-3 text-sm"
          >
            <option value="all">
              All companies
            </option>

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
      </div>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="CRM Contacts"
          value={filteredContacts.length}
          description="Contacts linked to monitored companies"
        />

        <MetricCard
          title="CRM Interactions"
          value={filteredInteractions.length}
          description="Recorded historical touchpoints"
        />

        <MetricCard
          title="Average Relationship"
          value={
            averageRelationshipStrength === null
              ? "N/A"
              : `${averageRelationshipStrength}/100`
          }
          description="Average CRM relationship strength"
        />

        <MetricCard
          title="Positive Interactions"
          value={positiveInteractionCount}
          description="Interactions with positive sentiment"
        />
      </section>

      <Card>
        <CardHeader>
          <CardTitle>CRM Contacts</CardTitle>

          <CardDescription>
            Contacts are ordered using their stored
            relationship strength.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {filteredContacts.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No CRM contacts found.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Contact</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Relationship</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {filteredContacts.map((contact) => (
                  <TableRow key={contact.id}>
                    <TableCell className="font-medium">
                      {contact.full_name}
                    </TableCell>

                    <TableCell>
                      <Link
                        href={`/companies/${contact.company_id}`}
                        className="hover:underline"
                      >
                        {companyNameById.get(
                          contact.company_id
                        ) ?? `Company ${contact.company_id}`}
                      </Link>
                    </TableCell>

                    <TableCell>
                      {contact.job_title ?? "N/A"}
                    </TableCell>

                    <TableCell>
                      {contact.email ?? "N/A"}
                    </TableCell>

                    <TableCell>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge>
                          {
                            contact.relationship_strength
                          }
                          /100
                        </Badge>

                        <span className="text-sm text-muted-foreground">
                          {getRelationshipLabel(
                            contact.relationship_strength
                          )}
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>CRM Interactions</CardTitle>

          <CardDescription>
            Historical meetings, calls, emails,
            introductions, and conference interactions.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {filteredInteractions.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No CRM interactions found.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead>Summary</TableHead>
                  <TableHead>Sentiment</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {filteredInteractions.map(
                  (interaction) => (
                    <TableRow key={interaction.id}>
                      <TableCell>
                        <Link
                          href={`/companies/${interaction.company_id}`}
                          className="font-medium hover:underline"
                        >
                          {companyNameById.get(
                            interaction.company_id
                          ) ?? `Company ${interaction.company_id}`}
                        </Link>
                      </TableCell>

                      <TableCell>
                        {formatInteractionType(
                          interaction.interaction_type
                        )}
                      </TableCell>

                      <TableCell>
                        <Badge variant="outline">
                          {interaction.direction}
                        </Badge>
                      </TableCell>

                      <TableCell>
                        <p className="max-w-xl text-sm">
                          {interaction.summary}
                        </p>
                      </TableCell>

                      <TableCell>
                        <div className="space-y-1">
                          <Badge
                            variant={getSentimentVariant(
                              interaction.sentiment_score
                            )}
                          >
                            {getSentimentLabel(
                              interaction.sentiment_score
                            )}
                          </Badge>

                          <p className="text-xs text-muted-foreground">
                            {
                              interaction.sentiment_score
                            }
                          </p>
                        </div>
                      </TableCell>

                      <TableCell>
                        {formatDate(
                          interaction.occurred_at
                        )}
                      </TableCell>
                    </TableRow>
                  )
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
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
        <CardDescription>
          {title}
        </CardDescription>

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