import { Clapperboard, Moon, Sun } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { useTheme } from "../lib/useTheme";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { theme, toggle } = useTheme();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-20 border-b border-border bg-bg/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link
            to="/"
            className="focus-ring flex items-center gap-2 rounded-btn font-bold text-lg"
          >
            <Clapperboard className="text-primary" size={22} />
            <span>
              Seven<span className="text-primary">2U</span>
            </span>
          </Link>
          <button
            type="button"
            onClick={toggle}
            aria-label="Toggle theme"
            className="focus-ring rounded-btn p-2 text-text-secondary hover:bg-elevated hover:text-text-primary transition"
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </header>
      <main className="page-enter mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        {children}
      </main>
      <footer className="border-t border-border py-4 text-center text-xs text-text-muted">
        Data by TVMaze · Seven2U
      </footer>
    </div>
  );
}
