// Types pour les campagnes

export type CampaignStatus = "draft" | "sending" | "completed" | "failed" | "stopped";

export interface Campaign {
  id: number;
  name: string;
  message_1: string;
  message_2: string | null;
  template_name: string | null;
  status: CampaignStatus;
  total_recipients: number;
  sent_count: number;
  success_count: number;
  failed_count: number;
  interaction_count: number;
  created_by: number;
  created_at: string;
  updated_at: string;
  categories?: CampaignCategory[];
}

export interface CampaignCategory {
  id: number;
  name: string;
  color: string | null;
}

export interface CampaignCreate {
  name: string;
  message_1: string;
  message_2?: string;
  template_name?: string;
  category_ids: number[];
}

export interface CampaignUpdate {
  name?: string;
  message_1?: string;
  message_2?: string;
  template_name?: string;
}

export interface CampaignStats {
  id?: number;
  campaign_id?: number;
  name?: string;
  status?: CampaignStatus;
  total_recipients: number;
  sent_count: number;
  success_count?: number;
  delivered_count?: number;
  read_count?: number;
  failed_count: number;
  pending_count?: number;
  interaction_count?: number;
  success_rate: number;
  messages?: CampaignMessage[];
}

export interface CampaignMessage {
  id: number;
  contact_id: number;
  contact_phone: string;
  contact_name: string | null;
  message_type: "message_1" | "message_2";
  status: string;
  error_message: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
}

export interface CampaignFilters {
  status?: CampaignStatus;
  page?: number;
  size?: number;
}
