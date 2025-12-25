
"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function UploadPage() {
  const [uploading, setUploading] = useState(false);
  const [uploadedInvoice, setUploadedInvoice] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (file.type !== "application/pdf") {
      setError("Only PDF files are accepted");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://localhost:8000/api/invoices/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setUploadedInvoice(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="container mx-auto py-10 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Upload Invoice</h1>
        <p className="text-muted-foreground">
          Upload invoice PDFs to track your Monotributo income
        </p>
        <div className="mt-4">
          <Link
            href="/"
            className="text-sm text-primary hover:underline"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Upload Invoice</CardTitle>
          <CardDescription>
            Select a PDF invoice to upload to the system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileUpload}
                disabled={uploading}
                className="block w-full text-sm text-slate-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-semibold
                  file:bg-primary file:text-primary-foreground
                  hover:file:bg-primary/90
                  file:cursor-pointer
                  disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>

            {uploading && (
              <p className="text-sm text-muted-foreground">Uploading...</p>
            )}

            {error && (
              <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                {error}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {uploadedInvoice && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Upload Successful
              <Badge variant="secondary">{uploadedInvoice.status}</Badge>
            </CardTitle>
            <CardDescription>Invoice has been stored in the system</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="font-medium">Invoice ID:</div>
              <div className="font-mono text-xs">{uploadedInvoice.id}</div>

              <div className="font-medium">File Path:</div>
              <div className="font-mono text-xs">{uploadedInvoice.file.path}</div>

              <div className="font-medium">File Size:</div>
              <div>{(uploadedInvoice.file.size / 1024).toFixed(2)} KB</div>

              <div className="font-medium">Uploaded:</div>
              <div>{new Date(uploadedInvoice.uploaded_at).toLocaleString()}</div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
