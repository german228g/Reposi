"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FAQ_ITEMS } from "@/data/products";
import { Reveal } from "./Reveal";

export function Faq() {
  const [openId, setOpenId] = useState<string | null>(FAQ_ITEMS[0]?.id ?? null);

  return (
    <section id="faq" aria-labelledby="faq-heading" className="border-t border-line bg-bone py-24 sm:py-32">
      <div className="container-edit grid grid-cols-1 gap-10 lg:grid-cols-12">
        <Reveal className="lg:col-span-4">
          <span className="eyebrow text-ink/60">FAQ</span>
          <h2 id="faq-heading" className="mt-4 text-balance text-4xl font-medium tracking-tight">
            Частые вопросы.
          </h2>
        </Reveal>

        <div className="divide-y divide-line border-y border-line lg:col-span-8">
          {FAQ_ITEMS.map((item) => {
            const open = openId === item.id;
            return (
              <div key={item.id}>
                <button
                  type="button"
                  onClick={() => setOpenId(open ? null : item.id)}
                  aria-expanded={open}
                  className="focus-ring flex w-full items-center justify-between gap-6 py-6 text-left"
                >
                  <span className="text-lg font-medium tracking-tight">{item.question}</span>
                  <motion.span
                    animate={{ rotate: open ? 45 : 0 }}
                    transition={{ duration: 0.25 }}
                    className="shrink-0 text-2xl font-light text-ink/60"
                  >
                    +
                  </motion.span>
                </button>
                <AnimatePresence initial={false}>
                  {open && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                      className="overflow-hidden"
                    >
                      <p className="max-w-2xl pb-6 text-sm leading-relaxed text-ink/60">
                        {item.answer}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
