// Types pour les catégories

export interface Category {
  id: number;
  name: string;
  color: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
  contact_count?: number;
}

export interface CategoryCreate {
  name: string;
  color?: string;
}

export interface CategoryUpdate {
  name?: string;
  color?: string;
}

export interface CategoryWithContacts extends Category {
  contacts: CategoryContact[];
}

export interface CategoryContact {
  id: number;
  phone_number: string;
  country_code: string;
  full_number: string;
  first_name: string | null;
  last_name: string | null;
  whatsapp_verified: boolean | null;
}

export interface AddContactsToCategory {
  contact_ids: number[];
}
