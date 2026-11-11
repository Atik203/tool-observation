import Link from "next/link";
import { ScanSearch } from "lucide-react";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/slide", label: "Slides" },
  { href: "/proposal.pdf", label: "Proposal" },
  { href: "https://github.com/Atik203/tool-observation", label: "GitHub", external: true },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-border/40 mt-12">
      <div className="max-w-[88rem] mx-auto w-full px-4 md:px-6 py-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <span className="w-7 h-7 rounded-lg bg-gradient-to-tr from-teal-600 to-cyan-500 flex items-center justify-center text-white">
            <ScanSearch className="w-4 h-4" aria-hidden />
          </span>
          <div>
            <p className="text-base font-semibold leading-none">Tool Observation</p>
            <p className="text-xs text-muted-foreground mt-1">
              Fixed-prefix study of tool-result errors · ToolResult-800
            </p>
          </div>
        </div>

        <nav aria-label="Footer" className="flex flex-wrap items-center gap-x-5 gap-y-2">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              target={link.external ? "_blank" : undefined}
              rel={link.external ? "noreferrer" : undefined}
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
