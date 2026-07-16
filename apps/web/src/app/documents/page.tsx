"use client";

import Link from "next/link";
import {
  useEffect,
  useMemo,
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
  listCompanies,
  listDocuments,
} from "@/lib/api";
import type {
  CompanyRead,
  DocumentRead,
  DocumentSummaryRead,
} from "@/lib/api";


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


export default function DocumentsPage() {
  const [companies, setCompanies] =
    useState<CompanyRead[]>([]);

  const [documents, setDocuments] =
    useState<DocumentSummaryRead[]>([]);

  const [selectedDocument, setSelectedDocument] =
    useState<DocumentRead | null>(null);

  const [selectedCompanyId, setSelectedCompanyId] =
    useState<string>("all");

  const [isLoading, setIsLoading] =
    useState<boolean>(true);

  const [isLoadingDocument, setIsLoadingDocument] =
    useState<boolean>(false);

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadPageData(): Promise<void> {
      try {
        setIsLoading(true);
        setErrorMessage(null);

        const [
          companiesData,
          documentsData,
        ] = await Promise.all([
          listCompanies(),
          listDocuments(),
        ]);

        setCompanies(companiesData);
        setDocuments(documentsData);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Failed to load documents.";

        setErrorMessage(message);
      } finally {
        setIsLoading(false);
      }
    }

    void loadPageData();
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

  const filteredDocuments = useMemo(() => {
    if (selectedCompanyId === "all") {
      return documents;
    }

    const companyId = Number(selectedCompanyId);

    return documents.filter((documentRecord) => {
      return documentRecord.company_id === companyId;
    });
  }, [
    documents,
    selectedCompanyId,
  ]);

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
      <main className="p-6">
        <p className="text-sm text-muted-foreground">
          Loading documents...
        </p>
      </main>
    );
  }

  return (
    <main className="space-y-8 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Internal Documents
          </h1>

          <p className="text-muted-foreground">
            Mock Egnyte documents used as internal
            evidence for target monitoring and future
            RAG retrieval.
          </p>
        </div>

        <div className="w-full md:w-72">
          <label
            htmlFor="document-company-filter"
            className="mb-2 block text-sm font-medium"
          >
            Filter by company
          </label>

          <select
            id="document-company-filter"
            value={selectedCompanyId}
            onChange={(event) => {
              setSelectedCompanyId(
                event.target.value
              );

              setSelectedDocument(null);
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

      {errorMessage !== null ? (
        <p className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {errorMessage}
        </p>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Document Library</CardTitle>

          <CardDescription>
            The list endpoint returns document metadata.
            Full extracted text is loaded only when a
            document is opened.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {filteredDocuments.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No documents found.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Document</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead className="text-right">
                    Action
                  </TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {filteredDocuments.map(
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
                        <Link
                          href={
                            `/companies/${documentRecord.company_id}`
                          }
                          className="hover:underline"
                        >
                          {companyNameById.get(
                            documentRecord.company_id
                          )
                            ?? `Company ${documentRecord.company_id}`}
                        </Link>
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
    </main>
  );
}