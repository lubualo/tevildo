"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { type CurrentCategoriesResponse } from "@/lib/schemas/monotributo";

export default function MonotributoPage() {
  const [data, setData] = useState<CurrentCategoriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);
  const [updateMessage, setUpdateMessage] = useState<string | null>(null);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/api/monotributo/categories/current");
      if (!response.ok) {
        throw new Error("Failed to fetch category data");
      }
      const result: CurrentCategoriesResponse = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  const handleUpdate = async () => {
    try {
      setUpdating(true);
      setUpdateMessage(null);
      setError(null);

      const response = await fetch("http://localhost:8000/api/monotributo/categories/update", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to update categories");
      }

      const result = await response.json();

      // Set user-friendly message based on status
      if (result.status === "up_to_date") {
        setUpdateMessage("✅ Categories are already up to date with ARCA");
      } else if (result.status === "updated") {
        setUpdateMessage(
          `✅ Updated from ${result.old_version} to ${result.new_version} (${result.categories_count} categories)`
        );
        // Refresh the data to show new version
        await fetchCategories();
      } else if (result.status === "created") {
        setUpdateMessage(`✅ First version created: ${result.version_name} (${result.categories_count} categories)`);
        await fetchCategories();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setUpdating(false);
    }
  };

  const formatCurrency = (value: number | null) => {
    if (value === null) return "—";
    return value.toLocaleString("es-AR", {
      style: "currency",
      currency: "ARS",
      minimumFractionDigits: 2,
    });
  };

  const formatNumber = (value: number | null) => {
    if (value === null) return "—";
    return value.toLocaleString("es-AR");
  };

  if (loading) {
    return (
      <div className="container mx-auto p-8">
        <p>Loading category data...</p>
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

  if (!data) {
    return (
      <div className="container mx-auto p-8">
        <p className="text-muted-foreground">No category data available</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">Monotributo Categories</h1>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="outline">{data.version.name}</Badge>
            <span className="text-sm text-muted-foreground">
              Valid from: {new Date(data.version.valid_from).toLocaleDateString("es-AR")}
            </span>
          </div>
          {data.version.notes && (
            <p className="text-sm text-muted-foreground mt-1">{data.version.notes}</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleUpdate}
            disabled={updating}
            variant="default"
          >
            {updating ? "Updating..." : "Update from ARCA"}
          </Button>
          <Link href="/invoices">
            <Button variant="outline">View Invoices</Button>
          </Link>
        </div>
      </div>

      {/* Update message */}
      {updateMessage && (
        <div className="mb-4 p-3 bg-green-50 dark:bg-green-950 text-green-900 dark:text-green-100 rounded-md text-sm">
          {updateMessage}
        </div>
      )}

      <div className="space-y-8">
        {/* Annual Income Limits */}
        <div>
          <h2 className="text-xl font-semibold mb-3">Annual Income Limits</h2>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Services</TableHead>
                  <TableHead className="text-right">Goods</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.categories.map((cat) => (
                  <TableRow key={cat.category_letter}>
                    <TableCell className="font-medium">{cat.category_letter}</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(cat.annual_income_limit_services)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(cat.annual_income_limit_goods)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>

        {/* Physical Limits */}
        <div>
          <h2 className="text-xl font-semibold mb-3">Physical & Consumption Limits</h2>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Surface (m²)</TableHead>
                  <TableHead className="text-right">Electricity (kWh)</TableHead>
                  <TableHead className="text-right">Annual Rent</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.categories.map((cat) => (
                  <TableRow key={cat.category_letter}>
                    <TableCell className="font-medium">{cat.category_letter}</TableCell>
                    <TableCell className="text-right">
                      {formatNumber(cat.surface_limit_m2)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatNumber(cat.electricity_limit_kwh)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(cat.annual_rent_limit_ars)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>

        {/* Monthly Payments - Services */}
        <div>
          <h2 className="text-xl font-semibold mb-3">Monthly Payments - Services</h2>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Integrated Tax</TableHead>
                  <TableHead className="text-right">Pension</TableHead>
                  <TableHead className="text-right">Social Security</TableHead>
                  <TableHead className="text-right font-bold">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.categories.map((cat) => (
                  <TableRow key={cat.category_letter}>
                    <TableCell className="font-medium">{cat.category_letter}</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(cat.integrated_tax_services)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(cat.pension_contribution_services)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(cat.social_security_services)}
                    </TableCell>
                    <TableCell className="text-right font-bold">
                      {formatCurrency(cat.total_monthly_services)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>

        {/* Monthly Payments - Goods */}
        <div>
          <h2 className="text-xl font-semibold mb-3">Monthly Payments - Goods</h2>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Integrated Tax</TableHead>
                  <TableHead className="text-right">Pension</TableHead>
                  <TableHead className="text-right">Social Security</TableHead>
                  <TableHead className="text-right font-bold">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.categories.map((cat) => (
                  <TableRow key={cat.category_letter}>
                    <TableCell className="font-medium">{cat.category_letter}</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(cat.integrated_tax_goods)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(cat.pension_contribution_goods)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(cat.social_security_goods)}
                    </TableCell>
                    <TableCell className="text-right font-bold">
                      {formatCurrency(cat.total_monthly_goods)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  );
}
