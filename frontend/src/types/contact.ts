// Types pour les contacts

export interface Contact {
  id: number;
  phone_number: string;
  country_code: string;
  full_number: string;
  first_name: string | null;
  last_name: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
  categories?: ContactCategory[];
  whatsapp_verified: boolean | null;
  verified_at: string | null;
}

export interface ContactCategory {
  id: number;
  name: string;
  color: string | null;
}

export interface ContactCreate {
  phone_number: string;
  country_code: string;
  first_name?: string;
  last_name?: string;
  category_ids?: number[];
}

export interface ContactUpdate {
  phone_number?: string;
  country_code?: string;
  first_name?: string;
  last_name?: string;
  category_ids?: number[];
}

export interface ContactImportResult {
  total: number;
  success: number;
  failed: number;
  skipped: number;
  errors: string[];
}

export interface ContactImportError {
  row: number;
  phone_number: string;
  error: string;
}

// WhatsApp verification status type
export type WhatsAppStatus = 'verified' | 'not_whatsapp' | 'pending' | null;

export interface ContactFilters {
  search?: string;
  category_id?: number;
  page?: number;
  size?: number;
  whatsapp_status?: WhatsAppStatus;
}

// WhatsApp verification result from API
export interface WhatsAppVerificationResult {
  contact_id: number;
  whatsapp_verified: boolean | null;
  verified_at: string | null;
  error_message: string | null;
}

// Bulk verification response from API
export interface BulkVerificationResponse {
  queued_count: number;
  message: string;
}
