"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { ModeToggle } from "@/components/mode-toggle";
import {
  buttonVariants,
} from "@/components/ui/button";
import { cn } from "@/lib/utils";

const links = [
  {
    href: "/",
    label: "Dashboard",
  },
  {
    href: "/companies",
    label: "Companies",
  },
  {
    href: "/news-articles",
    label: "News",
  },
  {
    href: "/triggers",
    label: "Triggers",
  },
  {
    href: "/crm",
    label: "CRM",
  },
  {
    href: "/documents",
    label: "Documents",
  },
  {
  href: "/rag",
  label: "RAG Explorer",
  },
  {
    href: "/agent-runs",
    label: "Agent Runs",
  },
  {
    href: "/drafts",
    label: "Drafts",
  },
] as const;

function isNavigationItemActive(
  pathname: string,
  href: string
): boolean {
  if (href === "/") {
    return pathname === "/";
  }

  return (
    pathname === href
    || pathname.startsWith(`${href}/`)
  );
}

export function SiteNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="mx-auto flex min-h-16 max-w-7xl items-center gap-6 px-6">
        <Link
          href="/"
          className="shrink-0 font-semibold tracking-tight"
        >
          PE Origination Agent
        </Link>

        <nav
          aria-label="Main navigation"
          className="ml-auto flex items-center gap-1 overflow-x-auto whitespace-nowrap py-2"
        >
          {links.map((link) => {
            const isActive =
              isNavigationItemActive(
                pathname,
                link.href
              );

            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={
                  isActive
                    ? "page"
                    : undefined
                }
                className={cn(
                  buttonVariants({
                    variant: isActive
                      ? "secondary"
                      : "ghost",
                    size: "sm",
                  }),
                  isActive
                    && "font-semibold shadow-sm"
                )}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="shrink-0 border-l pl-2">
          <ModeToggle />
        </div>
      </div>
    </header>
  );
}