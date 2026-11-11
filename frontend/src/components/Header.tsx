import { motion } from "framer-motion";
import { FileSearch, Moon, Sun } from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";
import { IndexStats } from "@/types";

interface HeaderProps {
  stats: IndexStats | null;
}

export function Header({ stats }: HeaderProps) {
  const { theme, toggleTheme } = useTheme();
  const docCount = stats?.sparse_count ?? 0;

  return (
    <motion.header
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="sticky top-0 z-40 w-full border-b border-line glass"
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-white shadow-glow">
            <FileSearch className="h-4 w-4" />
          </div>
          <div className="flex flex-col leading-none">
            <span className="text-[15px] font-semibold tracking-tight text-ink">
              Zx&nbsp;Lens
            </span>
            <span className="mt-0.5 text-[11px] text-ink-soft">
              Ask your documents
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <motion.div
            layout
            className="flex items-center gap-2 rounded-full border border-line bg-accent-soft px-3 py-1 text-[11px] text-ink-soft"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            <span>{docCount} indexed chunks</span>
          </motion.div>

          <motion.button
            type="button"
            onClick={toggleTheme}
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.92 }}
            aria-label={
              theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
            }
            className="flex h-9 w-9 items-center justify-center rounded-full border border-line bg-accent-soft text-ink transition-colors hover:text-accent"
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </motion.button>
        </div>
      </div>
    </motion.header>
  );
}
