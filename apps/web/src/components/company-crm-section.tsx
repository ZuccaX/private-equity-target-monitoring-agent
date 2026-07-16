"use client";

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
  listCRMContacts,
  listCRMInteractions,
} from "@/lib/api";
import type {
  ContactRead,
  CRMInteractionRead,
} from "@/lib/api";


type CompanyCRMSectionProps = {
  companyId: number;
};


function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}


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
): "default" | "secondary" | "destructive" {
  if (value >= 0.2) {
    return "default";
  }

  if (value <= -0.2) {
    return "destructive";
  }

  return "secondary";
}


export function CompanyCRMSection({
  companyId,
}: CompanyCRMSectionProps) {
  const [contacts, setContacts] =
    useState<ContactRead[]>([]);

  const [interactions, setInteractions] =
    useState<CRMInteractionRead[]>([]);

  const [isLoading, setIsLoading] =
    useState<boolean>(true);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function loadCRMData(): Promise<void> {
      try {
        setIsLoading(true);
        setErrorMessage(null);

        const [
          contactsData,
          interactionsData,
        ] = await Promise.all([
          listCRMContacts(companyId),
          listCRMInteractions(companyId),
        ]);

        if (isCancelled) {
          return;
        }

        setContacts(contactsData);
        setInteractions(interactionsData);
      } catch (error) {
        if (isCancelled) {
          return;
        }

        const message =
          error instanceof Error
            ? error.message
            : "Failed to load CRM data.";

        setErrorMessage(message);
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadCRMData();

    return () => {
      isCancelled = true;
    };
  }, [companyId]);

  const primaryContact = useMemo(() => {
    if (contacts.length === 0) {
      return null;
    }

    return contacts.reduce(
      (strongestContact, contact) => {
        if (
          contact.relationship_strength
          > strongestContact.relationship_strength
        ) {
          return contact;
        }

        return strongestContact;
      }
    );
  }, [contacts]);

  const latestInteraction = useMemo(() => {
    if (interactions.length === 0) {
      return null;
    }

    return interactions.reduce(
      (latest, interaction) => {
        const latestDate = new Date(
          latest.occurred_at
        ).getTime();

        const interactionDate = new Date(
          interaction.occurred_at
        ).getTime();

        if (interactionDate > latestDate) {
          return interaction;
        }

        return latest;
      }
    );
  }, [interactions]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>CRM Relationships</CardTitle>
        </CardHeader>

        <CardContent>
          <p className="text-sm text-muted-foreground">
            Loading CRM relationships...
          </p>
        </CardContent>
      </Card>
    );
  }

  if (errorMessage !== null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>CRM Relationships</CardTitle>
        </CardHeader>

        <CardContent>
          <p className="text-sm text-red-500">
            {errorMessage}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>
            CRM Relationship Summary
          </CardTitle>

          <CardDescription>
            Relationship signals used by the
            CRM-aware priority-scoring workflow.
          </CardDescription>
        </CardHeader>

        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border p-4">
            <p className="text-sm text-muted-foreground">
              Primary Contact
            </p>

            <p className="mt-1 font-medium">
              {primaryContact?.full_name ?? "N/A"}
            </p>

            <p className="text-sm text-muted-foreground">
              {primaryContact?.job_title
                ?? "No CRM contact available"}
            </p>
          </div>

          <div className="rounded-lg border p-4">
            <p className="text-sm text-muted-foreground">
              Relationship Strength
            </p>

            <p className="mt-1 text-2xl font-semibold">
              {primaryContact === null
                ? "N/A"
                : `${primaryContact.relationship_strength}/100`}
            </p>

            <p className="text-sm text-muted-foreground">
              {primaryContact === null
                ? "No relationship score"
                : getRelationshipLabel(
                    primaryContact.relationship_strength
                  )}
            </p>
          </div>

          <div className="rounded-lg border p-4">
            <p className="text-sm text-muted-foreground">
              Latest Interaction
            </p>

            <p className="mt-1 font-medium">
              {latestInteraction === null
                ? "N/A"
                : formatLabel(
                    latestInteraction.interaction_type
                  )}
            </p>

            <p className="text-sm text-muted-foreground">
              {latestInteraction === null
                ? "No interaction recorded"
                : formatDate(
                    latestInteraction.occurred_at
                  )}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>CRM Contacts</CardTitle>

          <CardDescription>
            Known contacts associated with this
            target company.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {contacts.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No CRM contacts found.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Relationship</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {contacts.map((contact) => (
                  <TableRow key={contact.id}>
                    <TableCell className="font-medium">
                      {contact.full_name}
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
                          {contact.relationship_strength}
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
            Previous meetings, calls, emails, and
            other recorded touchpoints.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {interactions.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No CRM interactions found.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead>Summary</TableHead>
                  <TableHead>Sentiment</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {interactions.map((interaction) => (
                  <TableRow key={interaction.id}>
                    <TableCell>
                      {formatLabel(
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
                          {interaction.sentiment_score.toFixed(2)}
                        </p>
                      </div>
                    </TableCell>

                    <TableCell>
                      {formatDate(
                        interaction.occurred_at
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}