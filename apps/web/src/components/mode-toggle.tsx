"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";

export function ModeToggle() {
  const {
    resolvedTheme,
    setTheme,
  } = useTheme();

  function handleToggleTheme(): void {
    setTheme(
      resolvedTheme === "dark"
        ? "light"
        : "dark"
    );
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={handleToggleTheme}
      aria-label="Toggle colour theme"
      title="Toggle colour theme"
    >
      <Sun className="hidden size-4 dark:block" />

      <Moon className="block size-4 dark:hidden" />

      <span className="sr-only">
        Toggle colour theme
      </span>
    </Button>
  );
}