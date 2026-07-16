"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  DocumentPreview,
} from "@/components/document-preview";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  getDocument,
  listDocuments,
} from "@/lib/api";
import type {
  DocumentRead,
  DocumentSummaryRead,
} from "@/lib/api";


type CompanyDocumentsSectionProps = {
  companyId: number;
};


function formatDate(value: string | null): string {
  if (value === null) {
    return "N/A";
  }

  return new Date(value).toLocaleString();
}


function formatDocumentType(value: string): string {
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


export function CompanyDocumentsSection({
  companyId,
}: CompanyDocumentsSectionProps) {
  const [documents, setDocuments] =
    useState<DocumentSummaryRead[]>([]);

  const [selectedDocument, setSelectedDocument] =
    useState<DocumentRead | null>(null);

  const [isLoading, setIsLoading] =
    useState<boolean>(true);

  const [isLoadingDocument, setIsLoadingDocument] =
    useState<boolean>(false);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    async function loadDocuments(): Promise<void> {
      try {
        setIsLoading(true);
        setErrorMessage(null);

        const documentData =
          await listDocuments(companyId);

        if (!isCancelled) {
          setDocuments(documentData);
          setSelectedDocument(null);
        }
      } catch (error) {
        if (isCancelled) {
          return;
        }

        const message =
          error instanceof Error
            ? error.message
            : "Failed to load company documents.";

        setErrorMessage(message);
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadDocuments();

    return () => {
      isCancelled = true;
    };
  }, [companyId]);

  async function handleOpenDocument(
    documentId: number
  ): Promise<void> {
    try {
      setIsLoadingDocument(true);
      setErrorMessage(null);

      const documentData =
        await getDocument(documentId);

      setSelectedDocument(documentData);
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to load document content.";

      setErrorMessage(message);
    } finally {
      setIsLoadingDocument(false);
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Internal Documents</CardTitle>
        </CardHeader>

        <CardContent>
          <p className="text-sm text-muted-foreground">
            Loading internal documents...
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <section className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Internal Documents</CardTitle>

          <CardDescription>
            Mock Egnyte documents linked to this
            company and available for future RAG
            retrieval.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {errorMessage !== null ? (
            <p className="mb-4 text-sm text-destructive">
              {errorMessage}
            </p>
          ) : null}

          {documents.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No internal documents found.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Document</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead className="text-right">
                    Action
                  </TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {documents.map(
                  (documentRecord) => (
                    <TableRow
                      key={documentRecord.id}
                    >
                      <TableCell>
                        <div className="space-y-1">
                          <p className="font-medium">
                            {documentRecord.title}
                          </p>

                          <p className="text-xs text-muted-foreground">
                            {documentRecord.file_name}
                          </p>
                        </div>
                      </TableCell>

                      <TableCell>
                        <Badge>
                          {formatDocumentType(
                            documentRecord.document_type
                          )}
                        </Badge>
                      </TableCell>

                      <TableCell>
                        <Badge variant="secondary">
                          {documentRecord.source_system}
                        </Badge>
                      </TableCell>

                      <TableCell>
                        {formatDate(
                          documentRecord.uploaded_at
                        )}
                      </TableCell>

                      <TableCell className="text-right">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={isLoadingDocument}
                          onClick={() => {
                            void handleOpenDocument(
                              documentRecord.id
                            );
                          }}
                        >
                          Open
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <DocumentPreview
        documentRecord={selectedDocument}
        isLoading={isLoadingDocument}
      />
    </section>
  );
}