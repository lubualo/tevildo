"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
Table,
TableBody,
TableCell,
TableHead,
TableHeader,
TableRow,
} from "@/components/ui/table";
import {
AlertDialog,
AlertDialogAction,
AlertDialogCancel,
AlertDialogContent,
AlertDialogDescription,
AlertDialogFooter,
AlertDialogHeader,
AlertDialogTitle,
AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

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

interface InvoiceListResponse {
invoices: Invoice[];
total: number;
skip: number;
limit: number;
}

export default function InvoicesPage() {
const [invoices, setInvoices] = useState<Invoice[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const router = useRouter();

const fetchInvoices = async () => {
    try {
    setLoading(true);
    const response = await fetch("http://localhost:8000/api/invoices");
    if (!response.ok) {
        throw new Error("Failed to fetch invoices");
    }
    const data: InvoiceListResponse = await response.json();
    setInvoices(data.invoices);
    } catch (err) {
    setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
    setLoading(false);
    }
};

useEffect(() => {
    fetchInvoices();
}, []);

const handleDelete = async (invoiceId: string) => {
    try {
    const response = await fetch(`http://localhost:8000/api/invoices/${invoiceId}`, {
        method: "DELETE",
    });

    if (!response.ok) {
        throw new Error("Failed to delete invoice");
    }

    // Refresh the invoice list
    await fetchInvoices();
    } catch (err) {
    setError(err instanceof Error ? err.message : "Failed to delete invoice");
    }
};

const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive"> = {
    UPLOADED: "secondary",
    PARSED: "default",
    NEEDS_REVIEW: "destructive",
    };
    return <Badge variant={variants[status] || "default"}>{status}</Badge>;
};

const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
};

if (loading) {
    return (
    <div className="container mx-auto p-8">
        <p>Loading invoices...</p>
    </div>
    );
}

if (error) {
    return (
    <div className="container mx-auto p-8">
        <p className="text-red-500">Error: {error}</p>
    </div>
    );
}

return (
    <div className="container mx-auto p-8">
    <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Invoices</h1>
        <Link href="/">
        <Button variant="outline">Upload New Invoice</Button>
        </Link>
    </div>

    <div className="rounded-md border">
        <Table>
        <TableHeader>
            <TableRow>
            <TableHead>Status</TableHead>
            <TableHead>Uploaded At</TableHead>
            <TableHead>Invoice Number</TableHead>
            <TableHead>Client</TableHead>
            <TableHead>Total (ARS)</TableHead>
            <TableHead className="text-right">Actions</TableHead>
            </TableRow>
        </TableHeader>
        <TableBody>
            {invoices.length === 0 ? (
            <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground">
                No invoices found
                </TableCell>
            </TableRow>
            ) : (
            invoices.map((invoice) => (
                <TableRow
                key={invoice.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => router.push(`/invoices/${invoice.id}`)}
                >
                <TableCell>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(invoice.status)}
                    {invoice.locked_at && (
                      <Badge variant="outline" className="text-xs">
                        🔒 Locked
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>{formatDate(invoice.uploaded_at)}</TableCell>
                <TableCell>{invoice.invoice_number || "—"}</TableCell>
                <TableCell>{invoice.client_name || "—"}</TableCell>
                <TableCell>
                    {invoice.total_ars
                    ? invoice.total_ars.toLocaleString("es-AR", {
                        style: "currency",
                        currency: "ARS",
                        })
                    : "—"}
                </TableCell>
                <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                    <AlertDialog>
                    <AlertDialogTrigger asChild>
                        <Button variant="destructive" size="sm">
                        Delete
                        </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                        <AlertDialogTitle>Delete Invoice</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete this invoice? This will
                            permanently remove the invoice and its PDF file from the
                            system. This action cannot be undone.
                        </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={() => handleDelete(invoice.id)}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                            Delete
                        </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                    </AlertDialog>
                </TableCell>
                </TableRow>
            ))
            )}
        </TableBody>
        </Table>
    </div>
    </div>
);
}
