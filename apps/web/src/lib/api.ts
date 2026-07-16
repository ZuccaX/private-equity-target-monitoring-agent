const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function fetchJson<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);

  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const errorBody = await response.json();

      if (typeof errorBody.detail === "string") {
        message = errorBody.detail;
      }
    } catch {
      // Keep default message.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export type CompanyRead = {
  id: number;
  name: string;
  website: string | null;
  domain: string | null;
  sector: string;
  country: string;
  description: string | null;
  status: string;
  source: string | null;
  source_url: string | null;
  external_id: string | null;
  extra_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
};

export type PriorityScoreRead = {
  id: number;
  agent_run_id: number;
  company_id: number;
  overall_score: number;
  score_version: string;
  sector_fit_score: number;
  trigger_score: number;
  relationship_score: number;
  timing_score: number;
  risk_score: number;
  reasons: string[];
  evidence_refs: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
};

export type EmailDraftRead = {
  id: number;
  agent_run_id: number;
  company_id: number;
  subject: string;
  body: string;
  status: string;
  tone: string;
  recipient_name: string | null;
  recipient_email: string | null;
  generated_by: string;
  model_name: string | null;
  prompt_version: string | null;
  evidence_refs: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
};

export type AgentRunRead = {
  id: number;
  company_id: number;
  run_type: string;
  status: string;
  workflow_version: string;
  model_name: string | null;
  prompt_version: string | null;
  input_snapshot: Record<string, unknown>;
  output_summary: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AgentRunSummary = {
  id: number;
  company_id: number;
  company_name: string;
  run_type: string;
  status: string;
  overall_score: number | null;
  email_draft_id: number | null;
  email_draft_status: string | null;
  completed_at: string | null;
  created_at: string;
};

export type AgentRunDetail = {
  agent_run: AgentRunRead;
  priority_score: PriorityScoreRead | null;
  email_draft: EmailDraftRead | null;
};

export type EmailDraftUpdate = {
  subject?: string | null;
  body?: string | null;
  status?: string | null;
  comment?: string | null;
  reviewer_name?: string | null;
  reviewer_role?: string | null;
};

export type NewsArticleRead = {
  id: number;
  company_id: number;
  title: string;
  summary: string | null;
  url: string | null;
  source: string;
  published_at: string | null;
  ingested_at: string;
  raw_payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type TriggerRead = {
  id: number;
  company_id: number;
  news_article_id: number | null;
  trigger_type: string;
  title: string;
  description: string | null;
  confidence_score: number;
  detected_at: string;
  evidence_refs: Record<string, unknown>[];
  created_at: string;
  updated_at: string;
};

export type DashboardSummaryRead = {
  total_companies: number;
  total_news_articles: number;
  total_triggers: number;
  total_agent_runs: number;
  completed_agent_runs: number;
  failed_agent_runs: number;
  pending_drafts: number;
  approved_drafts: number;
  average_priority_score: number | null;
};

export type ContactRead = {
  id: number;
  company_id: number;
  full_name: string;
  job_title: string | null;
  email: string | null;
  phone: string | null;
  relationship_strength: number;
  source: string;
  external_id: string | null;
  created_at: string;
  updated_at: string;
};

export type CRMInteractionRead = {
  id: number;
  company_id: number;
  contact_id: number | null;
  interaction_type: string;
  direction: string;
  summary: string;
  occurred_at: string;
  sentiment_score: number;
  source: string;
  external_id: string | null;
  raw_payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type DocumentSummaryRead = {
  id: number;
  company_id: number;
  title: string;
  file_name: string;
  document_type: string;
  source_system: string;
  source_path: string | null;
  mime_type: string | null;
  uploaded_at: string | null;
  ingested_at: string;
  external_id: string | null;
  extra_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
};

export type DocumentRead = DocumentSummaryRead & {
  content_text: string | null;
};

export type VectorSearchRequest = {
  query: string;
  company_id: number | null;
  top_k: number;
  document_types?: string[];
  minimum_similarity?: number;
  embedding_provider?: string;
  embedding_model?: string;
  embedding_model_version?: string;
};

export type RAGRetrievalRequest = {
  query: string;
  company_id: number;
  top_k: number;
  document_types?: string[];
  minimum_similarity?: number;
};

export type VectorSearchResultRead = {
  chunk_id: number;
  document_id: number;
  company_id: number;

  document_title: string;
  document_type: string;

  source_system: string;
  source_path: string | null;

  chunk_index: number;
  chunk_text: string;
  token_count: number;

  embedding_model: string;
  embedding_provider: string;
  embedding_model_version: string;
  embedding_dimension: number;

  distance: number;
  similarity: number;
};

export type VectorSearchResponse = {
  query: string;
  company_id: number | null;
  top_k: number;
  result_count: number;
  results: VectorSearchResultRead[];
  requested_provider: string;
  effective_provider: string;
  effective_model: string;
  effective_model_version: string;
  fallback_used: boolean;
  warnings: string[];
  requested_embedding: EmbeddingIdentityRead;
  effective_embedding: EmbeddingIdentityRead;
};

export type EmbeddingIdentityRead = {
  provider: string;
  model: string;
  version: string;
  dimension: number;
};

export type RAGCitation = {
  source_number: number;
  chunk_id: number;
  document_id: number;
  document_title: string;
  source_path: string | null;
};

export type RAGRetrievalResponse = {
  query: string;
  company_id: number;
  top_k: number;
  result_count: number;
  context: string;
  sources: VectorSearchResultRead[];
  status: "ok" | "empty";
  minimum_similarity: number | null;
  context_word_budget: number;
  citations: RAGCitation[];
  requested_provider: string;
  effective_provider: string;
  effective_model: string;
  effective_model_version: string;
  fallback_used: boolean;
  fallback_reason: string | null;
  warnings: string[];
  requested_embedding: EmbeddingIdentityRead;
  effective_embedding: EmbeddingIdentityRead;
};

export async function listCompanies(): Promise<CompanyRead[]> {
  return fetchJson<CompanyRead[]>("/api/companies");
}

export async function getCompany(
  companyId: number
): Promise<CompanyRead> {
  return fetchJson<CompanyRead>(`/api/companies/${companyId}`);
}

export async function runAgentForCompany(
  companyId: number
): Promise<AgentRunDetail> {
  return fetchJson<AgentRunDetail>(`/api/agent-runs/${companyId}`, {
    method: "POST",
  });
}

export async function listAgentRuns(): Promise<AgentRunSummary[]> {
  return fetchJson<AgentRunSummary[]>("/api/agent-runs");
}

export async function listDrafts(): Promise<EmailDraftRead[]> {
  return fetchJson<EmailDraftRead[]>("/api/drafts");
}

export async function updateEmailDraft(
  draftId: number,
  payload: EmailDraftUpdate
): Promise<EmailDraftRead> {
  return fetchJson<EmailDraftRead>(`/api/drafts/${draftId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function listNewsArticles(
  companyId?: number
): Promise<NewsArticleRead[]> {
  const query = companyId === undefined ? "" : `?company_id=${companyId}`;

  return fetchJson<NewsArticleRead[]>(`/api/news-articles${query}`);
}

export async function listTriggers(
  companyId?: number
): Promise<TriggerRead[]> {
  const query = companyId === undefined ? "" : `?company_id=${companyId}`;

  return fetchJson<TriggerRead[]>(`/api/triggers${query}`);
}

export async function getDashboardSummary(): Promise<DashboardSummaryRead> {
  return fetchJson<DashboardSummaryRead>("/api/dashboard/summary");
}

export async function listCRMContacts(
  companyId?: number
): Promise<ContactRead[]> {
  const query =
    companyId === undefined
      ? ""
      : `?company_id=${companyId}`;

  return fetchJson<ContactRead[]>(
    `/api/crm/contacts${query}`
  );
}

export async function listCRMInteractions(
  companyId?: number
): Promise<CRMInteractionRead[]> {
  const query =
    companyId === undefined
      ? ""
      : `?company_id=${companyId}`;

  return fetchJson<CRMInteractionRead[]>(
    `/api/crm/interactions${query}`
  );
}

export async function listDocuments(
  companyId?: number
): Promise<DocumentSummaryRead[]> {
  const query =
    companyId === undefined
      ? ""
      : `?company_id=${companyId}`;

  return fetchJson<DocumentSummaryRead[]>(
    `/api/documents${query}`
  );
}

export async function getDocument(
  documentId: number
): Promise<DocumentRead> {
  return fetchJson<DocumentRead>(
    `/api/documents/${documentId}`
  );
}

export async function searchDocumentChunks(
  request: VectorSearchRequest
): Promise<VectorSearchResponse> {
  return fetchJson<VectorSearchResponse>(
    "/api/vector/search",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    }
  );
}

export async function retrieveRAGContext(
  request: RAGRetrievalRequest
): Promise<RAGRetrievalResponse> {
  return fetchJson<RAGRetrievalResponse>(
    "/api/rag/retrieve",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    }
  );
}
