"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { MagneticButton } from "./MagneticButton";

const NAV_LINKS = [
  { href: "#catalog", label: "Каталог" },
  { href: "#kits", label: "Наборы" },
  { href: "#about", label: "О бренде" },
  { href: "#how-to-order", label: "Доставка" },
  { href: "#contacts", label: "Контакты" },
];

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  function handleNavClick(href: string) {
    setMenuOpen(false);
    document.querySelector(href)?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-colors duration-300 ${
        scrolled ? "bg-bone/85 backdrop-blur-sm" : "bg-transparent"
      }`}
    >
      <div
        className={`container-edit flex items-center justify-between py-5 transition-[border-color] duration-300 ${
          scrolled ? "border-b border-line" : "border-b border-transparent"
        }`}
      >
        <a
          href="#hero"
          onClick={(e) => {
            e.preventDefault();
            handleNavClick("#hero");
          }}
          className="focus-ring inline-block py-2 text-lg font-semibold tracking-[0.14em]"
        >
          VOLTENZA
        </a>

        <nav className="hidden items-center gap-9 lg:flex" aria-label="Основная навигация">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={(e) => {
                e.preventDefault();
                handleNavClick(link.href);
              }}
              className="focus-ring inline-block py-2 text-sm uppercase tracking-[0.06em] text-ink/70 transition-colors hover:text-ink"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="hidden lg:block">
          <MagneticButton
            className="focus-ring rounded-full bg-ink px-6 py-3 text-xs font-medium uppercase tracking-[0.1em] text-bone"
            onClick={() => handleNavClick("#catalog")}
          >
            Выбрать аксессуар
          </MagneticButton>
        </div>

        <button
          type="button"
          aria-label={menuOpen ? "Закрыть меню" : "Открыть меню"}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((v) => !v)}
          className="focus-ring flex h-10 w-10 flex-col items-center justify-center gap-1.5 lg:hidden"
        >
          <motion.span
            animate={{ rotate: menuOpen ? 45 : 0, y: menuOpen ? 5 : 0 }}
            className="block h-px w-6 bg-ink"
          />
          <motion.span
            animate={{ opacity: menuOpen ? 0 : 1 }}
            className="block h-px w-6 bg-ink"
          />
          <motion.span
            animate={{ rotate: menuOpen ? -45 : 0, y: menuOpen ? -7 : 0 }}
            className="block h-px w-6 bg-ink"
          />
        </button>
      </div>

      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden border-b border-line bg-bone lg:hidden"
          >
            <nav className="container-edit flex flex-col gap-1 py-4" aria-label="Мобильная навигация">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavClick(link.href);
                  }}
                  className="focus-ring border-b border-line/60 py-4 text-base uppercase tracking-[0.04em] last:border-none"
                >
                  {link.label}
                </a>
              ))}
              <MagneticButton
                className="focus-ring mt-4 rounded-full bg-ink px-6 py-4 text-center text-xs font-medium uppercase tracking-[0.1em] text-bone"
                onClick={() => handleNavClick("#catalog")}
              >
                Выбрать аксессуар
              </MagneticButton>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
