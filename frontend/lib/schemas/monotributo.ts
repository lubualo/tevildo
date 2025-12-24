/**
 * Monotributo category types and schemas
 */

export interface MonotributoVersion {
  id: string;
  name: string;
  valid_from: string;
  valid_to: string | null;
  notes: string | null;
}

export interface MonotributoCategoryLimit {
  category_letter: string;
  annual_income_limit_services: number;
  annual_income_limit_goods: number;
  surface_limit_m2: number | null;
  electricity_limit_kwh: number | null;
  annual_rent_limit_ars: number | null;
  integrated_tax_services: number | null;
  pension_contribution_services: number | null;
  social_security_services: number | null;
  integrated_tax_goods: number | null;
  pension_contribution_goods: number | null;
  social_security_goods: number | null;
  total_monthly_services: number | null;
  total_monthly_goods: number | null;
}

export interface CurrentCategoriesResponse {
  version: MonotributoVersion;
  categories: MonotributoCategoryLimit[];
}
