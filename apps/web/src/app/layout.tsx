import type { Metadata } from "next";

import { SiteNav } from "@/components/site-nav";
import {
  ThemeProvider,
} from "@/components/theme-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "PE Origination Agent Platform",
  description:
    "A full-stack AI workflow platform for private equity origination.",
};

type RootLayoutProps = Readonly<{
  children: React.ReactNode;
}>;

export default function RootLayout({
  children,
}: RootLayoutProps) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
    >
      <body
        className="min-h-screen bg-background text-foreground antialiased"
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <SiteNav />

          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
