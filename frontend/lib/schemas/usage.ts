/**
 * Monotributo usage tracking types
 */

export interface CategoryUsage {
  category_letter: string;
  limit: number;
  used: number;
  percentage: number;
  remaining: number;
  status: "safe" | "warning" | "danger";
  is_current: boolean;
}

export interface UsageResponse {
  rolling_12mo_total_ars: number;
  date_range: {
    from: string;
    to: string;
  };
  invoice_count: number;
  current_category: string | null;
  company_name: string | null;
  income_type: "services" | "goods";
  categories: CategoryUsage[];
}
