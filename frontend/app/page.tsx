"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { type UsageResponse } from "@/lib/schemas/usage";

export default function DashboardPage() {
  const [data, setData] = useState<UsageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsage = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/api/monotributo/usage");
      if (!response.ok) {
        throw new Error("Failed to fetch usage data");
      }
      const result: UsageResponse = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsage();
  }, []);

  const formatCurrency = (value: number) => {
    return value.toLocaleString("es-AR", {
      style: "currency",
      currency: "ARS",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("es-AR", {
      month: "short",
      year: "numeric",
    });
  };

  const getStatusIndicator = (status: string) => {
    switch (status) {
      case "safe":
        return <span className="text-2xl">🟢</span>;
      case "warning":
        return <span className="text-2xl">🟡</span>;
      case "danger":
        return <span className="text-2xl">🔴</span>;
      default:
        return <span className="text-2xl">⚪</span>;
    }
  };

  const getProgressBar = (percentage: number) => {
    const clamped = Math.min(Math.max(percentage, 0), 100);
    let colorClass = "bg-green-500";
    if (percentage >= 90) {
      colorClass = "bg-red-500";
    } else if (percentage >= 70) {
      colorClass = "bg-yellow-500";
    }

    return (
      <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClass} transition-all`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    );
  };

  const handleCategoryClick = async (category: string) => {
    try {
      await fetch("http://localhost:8000/api/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_category: category }),
      });
      await fetchUsage(); // Refresh to show new selection
    } catch (err) {
      console.error("Failed to update category:", err);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-8">
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-8">
        <p className="text-red-500">Error: {error}</p>
        <p className="text-sm text-muted-foreground mt-2">
          Make sure you've updated categories from ARCA on the{" "}
          <Link href="/monotributo" className="text-primary hover:underline">
            categories page
          </Link>
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container mx-auto p-8">
        <p className="text-muted-foreground">No data available</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-8">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold">
          {data.company_name || "Welcome to Tevildo"}
        </h1>
        <p className="text-muted-foreground">
          Monotributo income tracking dashboard
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-1">
            Rolling 12-Month Total
          </div>
          <div className="text-3xl font-bold">
            {formatCurrency(data.rolling_12mo_total_ars)}
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            {formatDate(data.date_range.from)} - {formatDate(data.date_range.to)}
          </div>
        </Card>

        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-1">Current Category</div>
          {data.current_category ? (
            <>
              <div className="text-3xl font-bold">Category {data.current_category}</div>
              <div className="text-xs text-muted-foreground mt-2">
                Click any row below to change
              </div>
            </>
          ) : (
            <>
              <div className="text-2xl font-bold text-muted-foreground">Not Set</div>
              <div className="text-xs text-muted-foreground mt-2">
                Click a category below to select
              </div>
            </>
          )}
        </Card>

        <Card className="p-6">
          <div className="text-sm text-muted-foreground mb-1">Invoices (12mo)</div>
          <div className="text-3xl font-bold">{data.invoice_count}</div>
          <div className="text-xs text-muted-foreground mt-2">
            Only locked invoices counted
          </div>
        </Card>
      </div>

      {/* Category Usage Table */}
      <div>
        <h2 className="text-2xl font-semibold mb-4">Category Usage</h2>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[80px]">Category</TableHead>
                <TableHead className="text-right">Annual Limit</TableHead>
                <TableHead className="text-right">Your Total</TableHead>
                <TableHead className="w-[200px]">Usage</TableHead>
                <TableHead className="text-right">Remaining</TableHead>
                <TableHead className="w-[60px] text-center">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.categories.slice().reverse().map((cat) => (
                <TableRow
                  key={cat.category_letter}
                  className={`cursor-pointer hover:bg-muted/50 ${
                    cat.is_current ? "bg-primary/5" : ""
                  }`}
                  onClick={() => handleCategoryClick(cat.category_letter)}
                >
                  <TableCell className="font-bold text-lg">
                    {cat.is_current && (
                      <Badge variant="default" className="mr-2">
                        ✓
                      </Badge>
                    )}
                    {cat.category_letter}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatCurrency(cat.limit)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatCurrency(cat.used)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getProgressBar(cat.percentage)}
                      <span className="text-sm font-medium w-16 text-right">
                        {cat.percentage.toFixed(1)}%
                      </span>
                    </div>
                  </TableCell>
                  <TableCell
                    className={`text-right font-mono ${
                      cat.remaining < 0 ? "text-red-500" : ""
                    }`}
                  >
                    {formatCurrency(cat.remaining)}
                  </TableCell>
                  <TableCell className="text-center">
                    {getStatusIndicator(cat.status)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="mt-4 text-sm text-muted-foreground">
          <p>
            <strong>Income type:</strong> {data.income_type === "services" ? "Services (Locaciones)" : "Goods (Venta de bienes)"}
          </p>
          <p className="mt-1">
            Click any category row to set it as your current category. Only locked invoices from the last 12 months are included in calculations.
          </p>
        </div>
      </div>
    </div>
  );
}
