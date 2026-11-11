import type { Metadata, Viewport } from "next";
import Script from "next/script";
import localFont from "next/font/local";
import "./globals.css";

const instrument = localFont({
  src: [
    { path: "./fonts/instrument-sans-latin.woff2", weight: "400 700", style: "normal" },
    { path: "./fonts/instrument-sans-latin-italic.woff2", weight: "400 700", style: "italic" },
  ],
  variable: "--font-instrument",
  display: "swap",
  preload: true,
});

const newsreader = localFont({
  src: [
    { path: "./fonts/newsreader-latin.woff2", weight: "200 800", style: "normal" },
    { path: "./fonts/newsreader-latin-italic.woff2", weight: "200 800", style: "italic" },
  ],
  variable: "--font-newsreader",
  display: "swap",
  preload: false,
});

const jetbrains = localFont({
  src: [
    { path: "./fonts/jetbrains-mono-latin.woff2", weight: "100 800", style: "normal" },
    { path: "./fonts/jetbrains-mono-latin-italic.woff2", weight: "100 800", style: "italic" },
  ],
  variable: "--font-jetbrains",
  display: "swap",
  preload: false,
});

export const metadata: Metadata = {
  title: {
    default: "Tool-Result Errors in Language-Model Agents — ToolResult-800",
    template: "%s — Tool-Result Errors",
  },
  description:
    "A fixed-prefix causal study of detection, reliance, and recovery when language-model agents read wrong tool results.",
  applicationName: "Tool-Result Errors",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#07110f" },
    { media: "(prefers-color-scheme: light)", color: "#faf8f3" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="darkreader-lock" />
      </head>
      <body
        className={`${instrument.variable} ${newsreader.variable} ${jetbrains.variable} font-sans min-h-screen flex flex-col bg-background text-foreground antialiased`}
      >
        <Script id="toolobs-theme-init" strategy="beforeInteractive">
          {`(function(){try{var t=localStorage.getItem("toolobs-theme");if(t==="light"){document.documentElement.classList.remove("dark")}else{document.documentElement.classList.add("dark")}}catch(e){document.documentElement.classList.add("dark")}})();`}
        </Script>
        {children}
      </body>
    </html>
  );
}
