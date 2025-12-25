"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { type UserSettings } from "@/lib/schemas/settings";

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [companyName, setCompanyName] = useState("");
  const [incomeType, setIncomeType] = useState<"services" | "goods">("services");

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        const response = await fetch("http://localhost:8000/api/settings");
        if (!response.ok) {
          throw new Error("Failed to fetch settings");
        }
        const data: UserSettings = await response.json();
        setSettings(data);
        setCompanyName(data.company_name || "");
        setIncomeType(data.income_type);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      const response = await fetch("http://localhost:8000/api/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: companyName || null,
          income_type: incomeType,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save settings");
      }

      const data: UserSettings = await response.json();
      setSettings(data);
      setSuccessMessage("Settings saved successfully!");

      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-8">
        <p>Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-8 max-w-2xl">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <Image
            src="/tevildo-logo.svg"
            alt="Tevildo"
            width={36}
            height={36}
            className="dark:invert"
          />
          <div>
            <h1 className="text-3xl font-bold">Settings</h1>
            <p className="text-muted-foreground">
              Configure your Tevildo preferences
            </p>
          </div>
        </div>
        <Link href="/">
          <Button variant="outline">Back to Dashboard</Button>
        </Link>
      </div>

      {/* Success message */}
      {successMessage && (
        <div className="mb-4 p-3 bg-green-50 dark:bg-green-950 text-green-900 dark:text-green-100 rounded-md text-sm">
          {successMessage}
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-950 text-red-900 dark:text-red-100 rounded-md text-sm">
          {error}
        </div>
      )}

      {/* Company Settings */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Company Information</CardTitle>
          <CardDescription>
            This name will appear in the dashboard header and future reports
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="company_name">Company Name</Label>
              <Input
                id="company_name"
                type="text"
                placeholder="Your company or name"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="mt-1"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Monotributo Settings */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Monotributo Configuration</CardTitle>
          <CardDescription>
            Configure how category limits are calculated
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label>Income Type</Label>
              <p className="text-sm text-muted-foreground mb-3">
                Select whether you primarily provide services or sell goods. This affects which category limits apply to you.
              </p>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="income_type"
                    value="services"
                    checked={incomeType === "services"}
                    onChange={() => setIncomeType("services")}
                    className="w-4 h-4"
                  />
                  <span>Services (Locaciones y/o prestaciones)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="income_type"
                    value="goods"
                    checked={incomeType === "goods"}
                    onChange={() => setIncomeType("goods")}
                    className="w-4 h-4"
                  />
                  <span>Goods (Venta de bienes)</span>
                </label>
              </div>
            </div>

            {settings?.current_category && (
              <div className="pt-4 border-t">
                <Label>Current Category</Label>
                <p className="text-sm text-muted-foreground">
                  Category <strong>{settings.current_category}</strong> - Change this from the dashboard by clicking on a category row.
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : "Save Settings"}
        </Button>
      </div>

      {/* Export & Backup */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Export & Backup</CardTitle>
          <CardDescription>
            Download reports and backups of your data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex flex-col gap-3">
              <div>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => window.open("http://localhost:8000/api/reports/excel", "_blank")}
                >
                  Download Excel Report
                </Button>
                <p className="text-xs text-muted-foreground mt-1">
                  Summary spreadsheet with invoices and monthly breakdown (last 12 months, locked only)
                </p>
              </div>

              <div>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => window.open("http://localhost:8000/api/reports/zip", "_blank")}
                >
                  Download ZIP with PDFs
                </Button>
                <p className="text-xs text-muted-foreground mt-1">
                  Invoice PDFs grouped by month + Excel report (last 12 months, locked only)
                </p>
              </div>

              <div className="pt-2 border-t">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => window.open("http://localhost:8000/api/reports/backup", "_blank")}
                >
                  Download Full Backup
                </Button>
                <p className="text-xs text-muted-foreground mt-1">
                  Complete backup with all PDFs and data (all invoices, all statuses)
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
