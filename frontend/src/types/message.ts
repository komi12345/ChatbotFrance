// Types pour les messages

export type MessageStatus = "pending" | "sent" | "delivered" | "read" | "failed";
export type MessageType = "message_1" | "message_2";

export interface Message {
  id: number;
  campaign_id: number;
  contact_id: number;
  message_type: MessageType;
  content: string;
  status: MessageStatus;
  whatsapp_message_id: string | null;
  error_message: string | null;
  retry_count: number;
  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
  created_at: string;
  updated_at: string;
  contact?: MessageContact;
  campaign?: MessageCampaign;
}

export interface MessageContact {
  id: number;
  phone_number: string;
  full_number: string;
  first_name: string | null;
  last_name: string | null;
}

export interface MessageCampaign {
  id: number;
  name: string;
}

export interface MessageStats {
  total_messages: number;
  sent_count: number;
  delivered_count: number;
  read_count: number;
  failed_count: number;
  pending_count: number;
  success_rate: number;
  delivery_rate: number;
  read_rate: number;
}

export interface MessageFilters {
  campaign_id?: number;
  contact_id?: number;
  status?: MessageStatus;
  message_type?: MessageType;
  page?: number;
  size?: number;
}

export interface DailyMessageStats {
  date: string;
  sent: number;
  delivered: number;
  read: number;
  failed: number;
}

export interface StatusDistribution {
  status: MessageStatus;
  count: number;
  percentage: number;
}
