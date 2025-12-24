"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
Select,
SelectContent,
SelectItem,
SelectTrigger,
SelectValue,
} from "@/components/ui/select";
import {
Card,
CardContent,
CardDescription,
CardHeader,
CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  invoiceFormSchema,
  type InvoiceFormData,
  type Invoice,
  type ParsedDataAttempt
} from "@/lib/schemas/invoice";

export default function InvoiceDetailPage() {
const params = useParams();
const invoiceId = params.id as string;

const [invoice, setInvoice] = useState<Invoice | null>(null);
const [loading, setLoading] = useState(true);
const [saving, setSaving] = useState(false);
const [error, setError] = useState<string | null>(null);
const [parsedData, setParsedData] = useState<ParsedDataAttempt | null>(null);
const [showParsedData, setShowParsedData] = useState(true);

// React Hook Form setup
const form = useForm<InvoiceFormData>({
    resolver: zodResolver(invoiceFormSchema),
    defaultValues: {
    issue_date: "",
    invoice_type: "",
    invoice_number: "",
    client_name: "",
    client_tax_id: "",
    currency: "",
    total_ars: "",
    total_original: "",
    fx_rate: "",
    fx_date: "",
    fx_source: "",
    notes: "",
    },
});

// Track which field was last modified to prevent infinite loops (using ref to avoid re-renders)
const isCalculating = useRef(false);

// Auto-calculation: watch for changes to calculate conversions
useEffect(() => {
  const subscription = form.watch((value, { name }) => {
    // Prevent infinite loops
    if (isCalculating.current) return;

    // Only auto-calculate if not locked
    if (invoice?.locked_at !== null) return;

    const fxRate = value.fx_rate ? parseFloat(value.fx_rate) : null;

    // Only calculate if we have an exchange rate
    if (!fxRate || fxRate <= 0) return;

    // If user changed total_original, calculate total_ars
    if (name === "total_original") {
      const totalOriginal = value.total_original ? parseFloat(value.total_original) : null;
      if (totalOriginal) {
        isCalculating.current = true;
        const calculatedArs = totalOriginal * fxRate;
        form.setValue("total_ars", calculatedArs.toFixed(2), { shouldValidate: false });
        setTimeout(() => { isCalculating.current = false; }, 50);
      }
    }

    // If user changed total_ars, calculate total_original
    if (name === "total_ars") {
      const totalArs = value.total_ars ? parseFloat(value.total_ars) : null;
      if (totalArs) {
        isCalculating.current = true;
        const calculatedOriginal = totalArs / fxRate;
        form.setValue("total_original", calculatedOriginal.toFixed(2), { shouldValidate: false });
        setTimeout(() => { isCalculating.current = false; }, 50);
      }
    }

    // If user changed fx_rate, recalculate based on which field exists
    if (name === "fx_rate") {
      const totalOriginal = value.total_original ? parseFloat(value.total_original) : null;
      const totalArs = value.total_ars ? parseFloat(value.total_ars) : null;

      isCalculating.current = true;
      if (totalOriginal) {
        const calculatedArs = totalOriginal * fxRate;
        form.setValue("total_ars", calculatedArs.toFixed(2), { shouldValidate: false });
      } else if (totalArs) {
        const calculatedOriginal = totalArs / fxRate;
        form.setValue("total_original", calculatedOriginal.toFixed(2), { shouldValidate: false });
      }
      setTimeout(() => { isCalculating.current = false; }, 50);
    }
  });

  return () => subscription.unsubscribe();
}, [form, invoice]);

// Fetch invoice data
useEffect(() => {
    const fetchInvoice = async () => {
    try {
        setLoading(true);
        const response = await fetch(`http://localhost:8000/api/invoices/${invoiceId}`);

        if (!response.ok) {
        throw new Error("Failed to fetch invoice");
        }

        const data: Invoice = await response.json();
        setInvoice(data);

        // Populate form with existing data
        form.reset({
        issue_date: data.issue_date || "",
        invoice_type: data.invoice_type || "",
        invoice_number: data.invoice_number || "",
        client_name: data.client_name || "",
        client_tax_id: data.client_tax_id || "",
        currency: data.currency || "",
        total_ars: data.total_ars?.toString() || "",
        total_original: data.total_original?.toString() || "",
        fx_rate: data.fx_rate?.toString() || "",
        fx_date: data.fx_date || "",
        fx_source: data.fx_source || "",
        notes: data.notes || "",
        });
    } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
        setLoading(false);
    }
    };

    fetchInvoice();
}, [invoiceId, form]);

// Fetch parse attempts
useEffect(() => {
const fetchParseAttempts = async () => {
    if (!invoiceId) return;

    try {
    const response = await fetch(`http://localhost:8000/api/invoices/${invoiceId}/parse-attempts`);

    if (response.ok) {
        const attempts = await response.json();
        if (attempts.length > 0) {
        // Use most recent parse attempt
        setParsedData(attempts[0]);
        }
    }
    } catch (err) {
    console.error("Failed to fetch parse attempts:", err);
    }
};

fetchParseAttempts();
}, [invoiceId]);

// Save invoice
const onSubmit = async (data: InvoiceFormData) => {
    try {
    setSaving(true);
    setError(null);

    // Build update payload (only send non-empty fields)
    const updatePayload: Record<string, string | number> = {};

    if (data.issue_date) updatePayload.issue_date = data.issue_date;
    if (data.invoice_type) updatePayload.invoice_type = data.invoice_type;
    if (data.invoice_number) updatePayload.invoice_number = data.invoice_number;
    if (data.client_name) updatePayload.client_name = data.client_name;
    if (data.client_tax_id) updatePayload.client_tax_id = data.client_tax_id;
    if (data.currency) updatePayload.currency = data.currency;
    if (data.total_ars) updatePayload.total_ars = Number(data.total_ars);
    if (data.total_original) updatePayload.total_original = Number(data.total_original);
    if (data.fx_rate) updatePayload.fx_rate = Number(data.fx_rate);
    if (data.fx_date) updatePayload.fx_date = data.fx_date;
    if (data.fx_source) updatePayload.fx_source = data.fx_source;
    if (data.notes) updatePayload.notes = data.notes;

    const response = await fetch(`http://localhost:8000/api/invoices/${invoiceId}`, {
        method: "PUT",
        headers: {
        "Content-Type": "application/json",
        },
        body: JSON.stringify(updatePayload),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to save invoice");
    }

    const updatedInvoice: Invoice = await response.json();
    setInvoice(updatedInvoice);
    alert("Invoice saved successfully!");
    } catch (err) {
    setError(err instanceof Error ? err.message : "Failed to save invoice");
    } finally {
    setSaving(false);
    }
};

// Lock invoice
const handleLock = async () => {
    if (!confirm("Are you sure you want to lock this invoice? This action cannot be undone.")) {
    return;
    }

    try {
    setSaving(true);
    setError(null);

    const response = await fetch(`http://localhost:8000/api/invoices/${invoiceId}/lock`, {
        method: "POST",
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to lock invoice");
    }

    const lockedInvoice: Invoice = await response.json();
    setInvoice(lockedInvoice);
    alert("Invoice locked successfully!");
    } catch (err) {
    setError(err instanceof Error ? err.message : "Failed to lock invoice");
    } finally {
    setSaving(false);
    }
};

const handleCopyParsedData = () => {
if (!parsedData?.extracted_data) return;

const data = parsedData.extracted_data;

form.reset({
    issue_date: data.issue_date || "",
    invoice_type: data.invoice_type || "",
    invoice_number: data.invoice_number || "",
    client_name: data.client_name || "",
    client_tax_id: data.client_tax_id || "",
    currency: data.currency || "",
    total_ars: data.total_ars?.toString() || "",
    total_original: data.total_original?.toString() || "",
    fx_rate: data.fx_rate?.toString() || "",
    fx_date: data.fx_date || "",
    fx_source: data.fx_source || "",
    notes: data.notes || "",
});

// Manually trigger calculation for USD invoices
// If we have fx_rate and total_original but no total_ars (or vice versa)
const fxRate = data.fx_rate ? parseFloat(data.fx_rate.toString()) : null;
const totalOriginal = data.total_original ? parseFloat(data.total_original.toString()) : null;
const totalArs = data.total_ars ? parseFloat(data.total_ars.toString()) : null;

if (fxRate && fxRate > 0) {
    if (totalOriginal && !totalArs) {
    // Calculate total_ars from total_original
    const calculatedArs = totalOriginal * fxRate;
    form.setValue("total_ars", calculatedArs.toFixed(2), { shouldValidate: false });
    } else if (totalArs && !totalOriginal) {
    // Calculate total_original from total_ars
    const calculatedOriginal = totalArs / fxRate;
    form.setValue("total_original", calculatedOriginal.toFixed(2), { shouldValidate: false });
    }
}

setShowParsedData(false);
alert("Parsed data copied to form!");
};

if (loading) {
    return (
    <div className="container mx-auto p-8">
        <p>Loading invoice...</p>
    </div>
    );
}

if (!invoice) {
    return (
    <div className="container mx-auto p-8">
        <p className="text-red-500">Invoice not found</p>
        <Link href="/invoices">
        <Button variant="outline" className="mt-4">Back to Invoices</Button>
        </Link>
    </div>
    );
}

const isLocked = invoice.locked_at !== null;

return (
    <div className="container mx-auto p-8">
    {/* Header */}
    <div className="flex justify-between items-center mb-6">
        <div>
        <h1 className="text-3xl font-bold">Invoice Details</h1>
        <p className="text-muted-foreground">ID: {invoice.id}</p>
        </div>
        <div className="flex gap-2 items-center">
        <Badge variant={invoice.status === "UPLOADED" ? "secondary" : "default"}>
            {invoice.status}
        </Badge>
        {isLocked && <Badge variant="outline">🔒 Locked</Badge>}
        <Link href="/invoices">
            <Button variant="outline">Back to List</Button>
        </Link>
        </div>
    </div>

    {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-4">
        {error}
        </div>
    )}

    {parsedData && parsedData.extracted_data && showParsedData && !isLocked && (
    <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
        <div className="flex items-start justify-between">
        <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
            <h3 className="font-semibold text-blue-900">
                📋 Parsed Data Available
            </h3>
            <Badge variant="outline" className="text-xs">
                Confidence: {Math.round(parsedData.confidence * 100)}%
            </Badge>
            {parsedData.confidence < 0.7 && (
                <Badge variant="destructive" className="text-xs">
                Needs Review
                </Badge>
            )}
            </div>

            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm text-blue-800 mb-3">
            {parsedData.extracted_data.invoice_number && (
                <div>Invoice: <span className="font-medium">{parsedData.extracted_data.invoice_number}</span></div>
            )}
            {parsedData.extracted_data.issue_date && (
                <div>Date: <span className="font-medium">{parsedData.extracted_data.issue_date}</span></div>
            )}
            {parsedData.extracted_data.client_name && (
                <div>Client: <span className="font-medium">{parsedData.extracted_data.client_name}</span></div>
            )}
            {parsedData.extracted_data.currency && (
                <div>Currency: <span className="font-medium">{parsedData.extracted_data.currency}</span></div>
            )}
            {parsedData.extracted_data.total_ars && (
                <div>Total ARS: <span className="font-medium">{parsedData.extracted_data.total_ars.toLocaleString()}</span></div>
            )}
            {parsedData.extracted_data.total_original && (
                <div>Total USD: <span className="font-medium">{parsedData.extracted_data.total_original}</span></div>
            )}
            {parsedData.extracted_data.fx_rate && (
                <div>FX Rate: <span className="font-medium">{parsedData.extracted_data.fx_rate}</span></div>
            )}
            {parsedData.extracted_data.cae && (
                <div className="col-span-2">CAE: <span className="font-medium font-mono text-xs">{parsedData.extracted_data.cae}</span></div>
            )}
            </div>

            <div className="flex gap-2">
            <Button
                type="button"
                size="sm"
                onClick={handleCopyParsedData}
                className="bg-blue-600 hover:bg-blue-700"
            >
                Copy All to Form
            </Button>
            <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => setShowParsedData(false)}
            >
                Dismiss
            </Button>
            </div>
        </div>
        </div>
    </div>
    )}

    {/* Main Content: PDF + Form */}
    <div className="grid grid-cols-2 gap-6">
        {/* Left: PDF Viewer */}
        <Card>
        <CardHeader>
            <CardTitle>PDF Preview</CardTitle>
        </CardHeader>
        <CardContent>
            <iframe
            src={`http://localhost:8000/api/invoices/${invoiceId}/pdf`}
            className="w-full h-[800px] border rounded"
            title="Invoice PDF"
            />
        </CardContent>
        </Card>

        {/* Right: Form */}
        <Card>
        <CardHeader>
            <CardTitle>Invoice Data</CardTitle>
            <CardDescription>
            {isLocked
                ? "This invoice is locked and cannot be edited"
                : "Fill in the invoice details manually"}
            </CardDescription>
        </CardHeader>
        <CardContent>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            {/* Issue Date */}
            <div>
                <Label htmlFor="issue_date">Issue Date</Label>
                <Input
                id="issue_date"
                type="date"
                {...form.register("issue_date")}
                disabled={isLocked}
                />
                {form.formState.errors.issue_date && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.issue_date.message}
                </p>
                )}
            </div>

            {/* Invoice Type */}
            <div>
                <Label htmlFor="invoice_type">Invoice Type</Label>
                <Select
                value={form.watch("invoice_type")}
                onValueChange={(value) => form.setValue("invoice_type", value)}
                disabled={isLocked}
                >
                <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="A">A</SelectItem>
                    <SelectItem value="B">B</SelectItem>
                    <SelectItem value="C">C</SelectItem>
                    <SelectItem value="E">E</SelectItem>
                    <SelectItem value="M">M</SelectItem>
                </SelectContent>
                </Select>
                {form.formState.errors.invoice_type && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.invoice_type.message}
                </p>
                )}
            </div>

            {/* Invoice Number */}
            <div>
                <Label htmlFor="invoice_number">Invoice Number</Label>
                <Input
                id="invoice_number"
                placeholder="0001-00000123"
                {...form.register("invoice_number")}
                disabled={isLocked}
                />
                {form.formState.errors.invoice_number && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.invoice_number.message}
                </p>
                )}
            </div>

            {/* Client Name */}
            <div>
                <Label htmlFor="client_name">Client Name</Label>
                <Input
                id="client_name"
                placeholder="Acme Corp"
                {...form.register("client_name")}
                disabled={isLocked}
                />
                {form.formState.errors.client_name && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.client_name.message}
                </p>
                )}
            </div>

            {/* Client Tax ID */}
            <div>
                <Label htmlFor="client_tax_id">Client Tax ID (CUIT)</Label>
                <Input
                id="client_tax_id"
                placeholder="20-12345678-9"
                {...form.register("client_tax_id")}
                disabled={isLocked}
                />
                {form.formState.errors.client_tax_id && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.client_tax_id.message}
                </p>
                )}
            </div>

            {/* Currency */}
            <div>
                <Label htmlFor="currency">Currency</Label>
                <Select
                value={form.watch("currency")}
                onValueChange={(value) => form.setValue("currency", value)}
                disabled={isLocked}
                >
                <SelectTrigger>
                    <SelectValue placeholder="Select currency" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="ARS">ARS (Pesos)</SelectItem>
                    <SelectItem value="USD">USD (Dollars)</SelectItem>
                    <SelectItem value="EUR">EUR (Euros)</SelectItem>
                </SelectContent>
                </Select>
                {form.formState.errors.currency && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.currency.message}
                </p>
                )}
            </div>

            {/* Total ARS */}
            <div>
                <Label htmlFor="total_ars">Total (ARS)</Label>
                <Input
                id="total_ars"
                type="number"
                step="0.01"
                placeholder="50000.00"
                {...form.register("total_ars")}
                disabled={isLocked}
                />
                {form.formState.errors.total_ars && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.total_ars.message}
                </p>
                )}
            </div>

            {/* Total USD */}
            <div>
                <Label htmlFor="total_original">Total (USD/EUR) - Optional</Label>
                <Input
                id="total_original"
                type="number"
                step="0.01"
                placeholder="500.00"
                {...form.register("total_original")}
                disabled={isLocked}
                />
                {form.formState.errors.total_original && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.total_original.message}
                </p>
                )}
            </div>

            {/* FX Rate */}
            <div>
                <Label htmlFor="fx_rate">Exchange Rate - Optional</Label>
                <Input
                id="fx_rate"
                type="number"
                step="0.01"
                placeholder="1000.00"
                {...form.register("fx_rate")}
                disabled={isLocked}
                />
                {form.formState.errors.fx_rate && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.fx_rate.message}
                </p>
                )}
            </div>

            {/* FX Date */}
            <div>
                <Label htmlFor="fx_date">Exchange Rate Date - Optional</Label>
                <Input
                id="fx_date"
                type="date"
                {...form.register("fx_date")}
                disabled={isLocked}
                />
                {form.formState.errors.fx_date && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.fx_date.message}
                </p>
                )}
            </div>

            {/* FX Source */}
            <div>
                <Label htmlFor="fx_source">Exchange Rate Source - Optional</Label>
                <Input
                id="fx_source"
                placeholder="Banco Nación"
                {...form.register("fx_source")}
                disabled={isLocked}
                />
                {form.formState.errors.fx_source && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.fx_source.message}
                </p>
                )}
            </div>

            {/* Notes */}
            <div>
                <Label htmlFor="notes">Notes</Label>
                <Textarea
                id="notes"
                placeholder="Additional notes..."
                {...form.register("notes")}
                disabled={isLocked}
                rows={3}
                />
                {form.formState.errors.notes && (
                <p className="text-sm text-red-500 mt-1">
                    {form.formState.errors.notes.message}
                </p>
                )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-4">
                {!isLocked && (
                <>
                    <Button type="submit" disabled={saving}>
                    {saving ? "Saving..." : "Save"}
                    </Button>
                    <Button type="button" onClick={handleLock} variant="destructive" disabled={saving}>
                    Lock Invoice
                    </Button>
                </>
                )}
                {isLocked && (
                <p className="text-sm text-muted-foreground">
                    Locked on: {new Date(invoice.locked_at!).toLocaleString()}
                </p>
                )}
            </div>
            </form>
        </CardContent>
        </Card>
    </div>
    </div>
);
}
