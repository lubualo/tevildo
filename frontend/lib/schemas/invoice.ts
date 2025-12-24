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
