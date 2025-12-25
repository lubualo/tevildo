"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";

interface NavHeaderProps {
  title?: string;
  subtitle?: string;
}

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/invoices", label: "Invoices" },
  { href: "/upload", label: "Upload" },
  { href: "/monotributo", label: "Categories" },
  { href: "/settings", label: "Settings" },
];

export function NavHeader({ title, subtitle }: NavHeaderProps) {
  const pathname = usePathname();

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-8 py-4">
        <div className="flex justify-between items-center">
          {/* Logo and Title */}
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <Image
                src="/tevildo-logo.svg"
                alt="Tevildo"
                width={40}
                height={40}
                className="dark:invert"
              />
              <span className="text-xl font-bold hidden sm:inline">Tevildo</span>
            </Link>
            {title && (
              <>
                <span className="text-muted-foreground hidden sm:inline">/</span>
                <div>
                  <h1 className="text-xl font-semibold">{title}</h1>
                  {subtitle && (
                    <p className="text-sm text-muted-foreground">{subtitle}</p>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link key={item.href} href={item.href}>
                  <Button
                    variant={isActive ? "secondary" : "ghost"}
                    size="sm"
                    className={isActive ? "font-medium" : ""}
                  >
                    {item.label}
                  </Button>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
