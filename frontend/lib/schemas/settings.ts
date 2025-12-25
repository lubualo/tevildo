/**
 * User settings types and schemas
 */

export interface UserSettings {
  id: string;
  company_name: string | null;
  current_category: string | null; // A-K
  income_type: "services" | "goods";
  created_at: string;
  updated_at: string;
}

export interface SettingsUpdate {
  company_name?: string | null;
  current_category?: string | null;
  income_type?: "services" | "goods";
}
