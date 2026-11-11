"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Github, Menu, ScanSearch, X } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

const NAV_ITEMS = [
  { href: "/#overview", label: "Overview" },
  { href: "/#pilot", label: "Pilot" },
  { href: "/#design", label: "Design" },
  { href: "/slide", label: "Slides" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="border-b border-border/40 bg-background/80 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-[88rem] mx-auto px-4 md:px-6 h-16 flex items-center justify-between">
        <Link
          href="/"
          aria-label="Tool Observation home"
          className="flex items-center gap-2.5 font-bold tracking-tight rounded-xl"
        >
          <span className="w-8 h-8 rounded-lg bg-gradient-to-tr from-teal-600 to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-teal-700/20">
            <ScanSearch className="w-5 h-5" aria-hidden />
          </span>
          <span className="gradient-text display-title text-xl leading-none">Tool Observation</span>
          <span className="hidden sm:inline text-xs uppercase tracking-widest text-muted-foreground bg-secondary/80 px-2 py-0.5 rounded-full border border-border">
            ToolResult-800
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <nav
            aria-label="Main"
            className="hidden md:flex items-center gap-1 bg-secondary/50 p-1 rounded-full border border-border/50"
          >
            {NAV_ITEMS.map((item) => {
              const active = pathname === "/slide" && item.href === "/slide";
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold transition-all duration-200 ${
                    active
                      ? "bg-gradient-to-r from-teal-700 to-cyan-600 text-white shadow-md shadow-teal-700/20"
                      : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <Link
            href="https://github.com/Atik203/tool-observation"
            target="_blank"
            rel="noreferrer"
            aria-label="Open the repository on GitHub"
            className="hidden sm:flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-secondary/50 text-muted-foreground transition-all hover:bg-secondary hover:text-foreground"
          >
            <Github className="h-4 w-4" aria-hidden />
          </Link>
          <ThemeToggle />

          <button
            type="button"
            className="md:hidden inline-flex items-center justify-center w-9 h-9 rounded-xl border border-border/60 text-muted-foreground hover:text-foreground transition-all"
            aria-label={open ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={open}
            aria-controls="mobile-nav"
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="w-5 h-5" aria-hidden /> : <Menu className="w-5 h-5" aria-hidden />}
          </button>
        </div>
      </div>

      {open && (
        <nav
          id="mobile-nav"
          aria-label="Main (mobile)"
          className="md:hidden border-t border-border/40 p-3 space-y-1 animate-fade"
        >
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-base font-semibold text-muted-foreground transition-all hover:text-foreground hover:bg-secondary"
            >
              {item.label}
            </Link>
          ))}
          <Link
            href="https://github.com/Atik203/tool-observation"
            target="_blank"
            rel="noreferrer"
            onClick={() => setOpen(false)}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-base font-semibold text-muted-foreground transition-all hover:text-foreground hover:bg-secondary"
          >
            <Github className="w-4 h-4" aria-hidden /> Repository
          </Link>
        </nav>
      )}
    </header>
  );
}
