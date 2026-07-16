"use client";

import { useEffect, useState } from "react";

import {
  listDrafts,
  updateEmailDraft,
  type EmailDraftRead,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

type DraftEditState = {
  subject: string;
  body: string;
};

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<EmailDraftRead[]>([]);
  const [draftEdits, setDraftEdits] = useState<Record<number, DraftEditState>>(
    {}
  );
  const [isLoading, setIsLoading] = useState(true);
  const [updatingDraftId, setUpdatingDraftId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadDrafts(): Promise<void> {
    try {
      setIsLoading(true);
      setErrorMessage(null);

      const data = await listDrafts();

      setDrafts(data);

      const initialEdits: Record<number, DraftEditState> = {};

      for (const draft of data) {
        initialEdits[draft.id] = {
          subject: draft.subject,
          body: draft.body,
        };
      }

      setDraftEdits(initialEdits);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to load drafts."
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSaveDraft(draftId: number): Promise<void> {
    const editState = draftEdits[draftId];

    if (editState === undefined) {
      return;
    }

    try {
      setUpdatingDraftId(draftId);
      setErrorMessage(null);

      await updateEmailDraft(draftId, {
        subject: editState.subject,
        body: editState.body,
      });

      await loadDrafts();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to save draft."
      );
    } finally {
      setUpdatingDraftId(null);
    }
  }

  async function handleDecision(
    draftId: number,
    status: "approved" | "rejected" | "revision_requested"
  ): Promise<void> {
    try {
      setUpdatingDraftId(draftId);
      setErrorMessage(null);

      await updateEmailDraft(draftId, {
        status,
        comment: `Draft marked as ${status} from the demo UI.`,
        reviewer_name: "Demo Analyst",
        reviewer_role: "Investment Analyst",
      });

      await loadDrafts();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to update draft status."
      );
    } finally {
      setUpdatingDraftId(null);
    }
  }

  function updateDraftEdit(
    draftId: number,
    field: keyof DraftEditState,
    value: string
  ): void {
    setDraftEdits((current) => ({
      ...current,
      [draftId]: {
        ...current[draftId],
        [field]: value,
      },
    }));
  }

  useEffect(() => {
    let isCancelled = false;

    async function fetchDrafts(): Promise<void> {
      try {
        const draftsData =
          await listDrafts();

        if (isCancelled) {
          return;
        }

        setDrafts(draftsData);
      } catch (error) {
        if (isCancelled) {
          return;
        }

        const message =
          error instanceof Error
            ? error.message
            : "Failed to load drafts.";

        setErrorMessage(message);
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void fetchDrafts();

    return () => {
      isCancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto max-w-7xl p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold">Email Drafts</h1>
        <p className="mt-2 text-muted-foreground">
          Review AI-generated outreach drafts before simulated approval.
        </p>
      </div>

      {errorMessage !== null && (
        <div className="mb-4 rounded-md border p-4 text-sm">
          {errorMessage}
        </div>
      )}

      {isLoading ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Loading drafts...
          </CardContent>
        </Card>
      ) : drafts.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            No drafts yet. Go to Companies and run the agent first.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {drafts.map((draft) => {
            const editState = draftEdits[draft.id];

            return (
              <Card key={draft.id}>
                <CardHeader className="flex flex-row items-start justify-between gap-4">
                  <div>
                    <CardTitle>Draft #{draft.id}</CardTitle>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Company ID: {draft.company_id} · Agent Run ID:{" "}
                      {draft.agent_run_id}
                    </p>
                  </div>

                  <Badge variant="outline">{draft.status}</Badge>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Subject</label>
                    <Input
                      value={editState?.subject ?? draft.subject}
                      onChange={(event) =>
                        updateDraftEdit(
                          draft.id,
                          "subject",
                          event.target.value
                        )
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Body</label>
                    <Textarea
                      className="min-h-40"
                      value={editState?.body ?? draft.body}
                      onChange={(event) =>
                        updateDraftEdit(draft.id, "body", event.target.value)
                      }
                    />
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      onClick={() => void handleSaveDraft(draft.id)}
                      disabled={updatingDraftId === draft.id}
                    >
                      Save Changes
                    </Button>

                    <Button
                      onClick={() => void handleDecision(draft.id, "approved")}
                      disabled={updatingDraftId === draft.id}
                    >
                      Approve
                    </Button>

                    <Button
                      variant="outline"
                      onClick={() => void handleDecision(draft.id, "rejected")}
                      disabled={updatingDraftId === draft.id}
                    >
                      Reject
                    </Button>

                    <Button
                      variant="outline"
                      onClick={() =>
                        void handleDecision(draft.id, "revision_requested")
                      }
                      disabled={updatingDraftId === draft.id}
                    >
                      Request Revision
                    </Button>
                  </div>

                  <div className="text-xs text-muted-foreground">
                    Generated by {draft.generated_by} · Tone: {draft.tone} ·
                    Created: {new Date(draft.created_at).toLocaleString()}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </main>
  );
}