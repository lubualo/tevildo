
"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import {
Table,
TableBody,
TableCell,
TableHead,
TableHeader,
TableRow,
} from "@/components/ui/table";

interface Invoice {
id: string;
status: string;
uploaded_at: string;
issue_date: string | null;
invoice_type: string | null;
invoice_number: string | null;
client_name: string | null;
currency: string | null;
total_ars: number | null;
locked_at: string | null;
}

export default function InvoicesPage() {
const [invoices, setInvoices] = useState<Invoice[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
    async function fetchInvoices() {
    try {
        const response = await fetch("http://localhost:8000/api/invoices");
        if (!response.ok) {
        throw new Error("Failed to fetch invoices");
        }
        const data = await response.json();
        setInvoices(data.invoices);
    } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load invoices");
    } finally {
        setLoading(false);
    }
    }

    fetchInvoices();
}, []);

const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    UPLOADED: "secondary",
    PARSED: "default",
    NEEDS_REVIEW: "destructive",
    };
    return <Badge variant={variants[status] || "outline"}>{status}</Badge>;
};

if (loading) {
    return (
    <div className="container mx-auto py-10 max-w-6xl">
        <p>Loading invoices...</p>
    </div>
    );
}

if (error) {
    return (
    <div className="container mx-auto py-10 max-w-6xl">
        <div className="p-3 bg-destructive/10 text-destructive rounded-md">
        {error}
        </div>
    </div>
    );
}

return (
    <div className="container mx-auto py-10 max-w-6xl">
    <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Invoices</h1>
        <p className="text-muted-foreground">
        View and manage all uploaded invoices
        </p>
        <div className="mt-4">
        <Link
            href="/"
            className="text-sm text-primary hover:underline"
        >
            ← Back to upload
        </Link>
        </div>
    </div>

    <Card>
        <CardHeader>
        <CardTitle>All Invoices</CardTitle>
        <CardDescription>
            {invoices.length} invoice{invoices.length !== 1 ? "s" : ""} total
        </CardDescription>
        </CardHeader>
        <CardContent>
        <Table>
            <TableHeader>
            <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>Uploaded</TableHead>
                <TableHead>Issue Date</TableHead>
                <TableHead>Invoice #</TableHead>
                <TableHead>Client</TableHead>
                <TableHead>Currency</TableHead>
                <TableHead className="text-right">Total (ARS)</TableHead>
            </TableRow>
            </TableHeader>
            <TableBody>
            {invoices.length === 0 ? (
                <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground">
                    No invoices uploaded yet
                </TableCell>
                </TableRow>
            ) : (
                invoices.map((invoice) => (
                <TableRow key={invoice.id}>
                    <TableCell>{getStatusBadge(invoice.status)}</TableCell>
                    <TableCell>
                    {new Date(invoice.uploaded_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>{invoice.issue_date || "-"}</TableCell>
                    <TableCell className="font-mono text-sm">
                    {invoice.invoice_number || "-"}
                    </TableCell>
                    <TableCell>{invoice.client_name || "-"}</TableCell>
                    <TableCell>{invoice.currency || "-"}</TableCell>
                    <TableCell className="text-right font-mono">
                    {invoice.total_ars
                        ? invoice.total_ars.toLocaleString("es-AR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                        })
                        : "-"}
                    </TableCell>
                </TableRow>
                ))
            )}
            </TableBody>
        </Table>
        </CardContent>
    </Card>
    </div>
);
}