export type DocumentType =
  | 'SPECIFICATION'
  | 'MANUAL'
  | 'DATASHEET'
  | 'DRAWING'
  | 'BOM'
  | 'OTHER';

export type DocumentStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'PROCESSED'
  | 'COMPLETED'
  | 'FAILED';

export type ExtractionMethod = 'text' | 'ocr';

export interface DocumentPage {
  id: string;
  document_id: string;
  page_number: number;
  text: string;
  extraction_method: ExtractionMethod;
  character_count: number;
  word_count: number;
  ocr_used: boolean;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  page_count: number;
  processed_page_count: number;
  ocr_page_count: number;
}

export interface Document {
  id: string;
  filename: string;
  document_type: string;
  part_number?: string;
  revision?: string;
  file_path?: string;
  mime_type?: string;
  file_size_bytes?: number;
  status: DocumentStatus;
  error_message?: string;
  metadata_payload?: Record<string, any>;
  uploaded_at: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentCreateInput {
  filename: string;
  document_type?: string;
  part_number?: string;
  revision?: string;
  file_path?: string;
  mime_type?: string;
  file_size_bytes?: number;
  metadata_payload?: Record<string, any>;
}

export interface CadMetadata {
  id: string;
  document_id: string;
  part_number?: string;
  part_name?: string;
  material?: string;
  mass_kg?: number;
  volume_cm3?: number;
  bounding_box_dimensions?: Record<string, any>;
  attributes?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  document_id: string;
  document_title: string;
  source_type: string;
  page_number?: number;
  section?: string;
  snippet: string;
  score?: number;
}

export interface CadReference {
  cad_id: string;
  part_number: string;
  part_name?: string;
  feature_name?: string;
  bounding_box?: Record<string, any>;
}

export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  citations?: Citation[];
  cad_references?: CadReference[];
  token_count?: number;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data: T;
  errors?: string[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AgentCitation {
  citation_id: string;
  document_id: string;
  filename: string;
  page_number: number;
  chunk_id?: string | null;
  chunk_index?: number;
  part_number?: string | null;
  revision?: string | null;
  section?: string | null;
  snippet?: string | null;
}

export interface ToolExecutionTrace {
  tool_name: string;
  status: 'success' | 'error';
  input_summary?: Record<string, any> | null;
  output_summary?: Record<string, any> | null;
  error?: string | null;
}

export interface AgentQueryRequest {
  query: string;
  top_k?: number;
  filters?: {
    part_number?: string;
    revision?: string;
    document_type?: string;
  };
}

export interface AgentResponseData {
  query: string;
  answer: string;
  citations: AgentCitation[];
  tool_traces: ToolExecutionTrace[];
  tools_used?: string[];
  tools_called?: string[];
  should_abstain: boolean;
  metadata: {
    provider?: string;
    model?: string;
    latency_ms?: number;
  };
}

export interface ConversationTurn {
  id: string;
  query: string;
  timestamp: string;
  response?: AgentResponseData;
  loading?: boolean;
  error?: string;
}

