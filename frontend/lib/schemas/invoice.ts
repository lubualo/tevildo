import { z } from "zod";

// Form uses strings (HTML inputs), we convert to proper types when submitting
export const invoiceFormSchema = z.object({
  issue_date: z.string().optional(),
  invoice_type: z.string().optional(),
  invoice_number: z.string().optional(),
  client_name: z.string().optional(),
  client_tax_id: z.string().optional(),
  currency: z.string().optional(),
  total_ars: z.string().optional(),
  total_original: z.string().optional(),
  fx_rate: z.string().optional(),
  fx_date: z.string().optional(),
  fx_source: z.string().optional(),
  notes: z.string().optional(),
});

export type InvoiceFormData = z.infer<typeof invoiceFormSchema>;

// API response types
export interface Invoice {
  id: string;
  status: string;
  uploaded_at: string;
  issue_date: string | null;
  invoice_type: string | null;
  invoice_number: string | null;
  client_name: string | null;
  client_tax_id: string | null;
  currency: string | null;
  total_ars: number | null;
  total_original: number | null;
  fx_rate: number | null;
  fx_date: string | null;
  fx_source: string | null;
  notes: string | null;
  locked_at: string | null;
}

export interface ParsedDataAttempt {
  id: string;
  created_at: string;
  parser_name: string;
  confidence: number;
  warnings: string | null;
  extracted_data: {
    invoice_type?: string;
    invoice_number?: string;
    issue_date?: string;
    client_name?: string;
    client_tax_id?: string;
    currency?: string;
    total_original?: number;
    total_ars?: number;
    fx_rate?: number;
    fx_date?: string;
    fx_source?: string;
    cae?: string;
    notes?: string;
  };
}
