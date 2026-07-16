import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { DocumentRead } from "@/lib/api";


type DocumentPreviewProps = {
  documentRecord: DocumentRead | null;
  isLoading: boolean;
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


export function DocumentPreview({
  documentRecord,
  isLoading,
}: DocumentPreviewProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Document Preview</CardTitle>
        </CardHeader>

        <CardContent>
          <p className="text-sm text-muted-foreground">
            Loading document content...
          </p>
        </CardContent>
      </Card>
    );
  }

  if (documentRecord === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Document Preview</CardTitle>

          <CardDescription>
            Select a document to inspect its extracted
            text and metadata.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <p className="text-sm text-muted-foreground">
            No document selected.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <CardTitle>
              {documentRecord.title}
            </CardTitle>

            <CardDescription>
              {documentRecord.file_name}
            </CardDescription>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge>
              {formatDocumentType(
                documentRecord.document_type
              )}
            </Badge>

            <Badge variant="secondary">
              {documentRecord.source_system}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <section className="grid gap-4 md:grid-cols-2">
          <MetadataItem
            label="Uploaded"
            value={formatDate(
              documentRecord.uploaded_at
            )}
          />

          <MetadataItem
            label="Ingested"
            value={formatDate(
              documentRecord.ingested_at
            )}
          />

          <MetadataItem
            label="MIME Type"
            value={
              documentRecord.mime_type ?? "N/A"
            }
          />

          <MetadataItem
            label="External ID"
            value={
              documentRecord.external_id ?? "N/A"
            }
          />
        </section>

        <section>
          <p className="mb-2 text-sm font-medium">
            Source Path
          </p>

          <code className="block break-all rounded-md bg-muted p-3 text-xs">
            {documentRecord.source_path ?? "N/A"}
          </code>
        </section>

        <section>
          <p className="mb-2 text-sm font-medium">
            Extracted Content
          </p>

          <div className="max-h-[32rem] overflow-y-auto whitespace-pre-wrap rounded-md border bg-muted/30 p-4 text-sm leading-7">
            {documentRecord.content_text
              ?? "No extracted text is available."}
          </div>
        </section>
      </CardContent>
    </Card>
  );
}


type MetadataItemProps = {
  label: string;
  value: string;
};


function MetadataItem({
  label,
  value,
}: MetadataItemProps) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-sm text-muted-foreground">
        {label}
      </p>

      <p className="mt-1 break-all font-medium">
        {value}
      </p>
    </div>
  );
}