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
  NewsArticleRead,
  listNewsArticles,
} from "@/lib/api";

function formatDate(value: string | null): string {
  if (value === null) {
    return "N/A";
  }

  return new Date(value).toLocaleString();
}

export default function NewsArticlesPage() {
  const [newsArticles, setNewsArticles] = useState<NewsArticleRead[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadNewsArticles(): Promise<void> {
      try {
        setIsLoading(true);
        setErrorMessage(null);

        const data = await listNewsArticles();

        setNewsArticles(data);
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "Failed to load news articles.";

        setErrorMessage(message);
      } finally {
        setIsLoading(false);
      }
    }

    void loadNewsArticles();
  }, []);

  return (
    <main className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          News Articles
        </h1>
        <p className="text-muted-foreground">
          Mock company news used as input signals for trigger extraction.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>News Signal Feed</CardTitle>
          <CardDescription>
            These articles are seeded demo records that represent external
            company signals.
          </CardDescription>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">
              Loading news articles...
            </p>
          ) : errorMessage !== null ? (
            <p className="text-sm text-red-500">{errorMessage}</p>
          ) : newsArticles.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No news articles found.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Company ID</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Published</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {newsArticles.map((article) => (
                  <TableRow key={article.id}>
                    <TableCell className="font-medium">
                      {article.id}
                    </TableCell>

                    <TableCell>{article.company_id}</TableCell>

                    <TableCell>
                      <div className="space-y-1">
                        <p className="font-medium">{article.title}</p>
                        <p className="max-w-2xl text-sm text-muted-foreground">
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
                      {formatDate(article.published_at)}
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