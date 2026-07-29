"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState, type FormEvent } from "react";
import { COURIERS } from "@/data/products";
import { CourierMark } from "./CourierMark";

interface OrderModalProps {
  productName: string | null;
  onClose: () => void;
}

type SubmitState = "idle" | "submitting" | "success" | "error";

export function OrderModal({ productName, onClose }: OrderModalProps) {
  const [courier, setCourier] = useState<(typeof COURIERS)[number]["id"]>("speedy");
  const [status, setStatus] = useState<SubmitState>("idle");
  const [lastProduct, setLastProduct] = useState<string | null>(null);

  if (productName && productName !== lastProduct) {
    setLastProduct(productName);
    setStatus("idle");
    setCourier("speedy");
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (productName) {
      document.addEventListener("keydown", onKey);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [productName, onClose]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("submitting");
    const form = new FormData(event.currentTarget);

    try {
      const response = await fetch("/api/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          productName,
          fullName: form.get("fullName"),
          phone: form.get("phone"),
          city: form.get("city"),
          courier,
          officeOrAddress: form.get("officeOrAddress"),
          comment: form.get("comment"),
        }),
      });
      if (!response.ok) throw new Error("request_failed");
      setStatus("success");
    } catch {
      setStatus("error");
    }
  }

  return (
    <AnimatePresence>
      {productName && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-end justify-center bg-ink/50 backdrop-blur-sm sm:items-center sm:p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          role="presentation"
        >
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="order-modal-title"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 24 }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            onClick={(e) => e.stopPropagation()}
            className="max-h-[92svh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-paper p-7 sm:rounded-3xl sm:p-9"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <span className="eyebrow text-ink/60">Оформление заказа</span>
                <h3 id="order-modal-title" className="mt-2 text-2xl font-medium tracking-tight">
                  {productName}
                </h3>
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Закрыть"
                className="focus-ring flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-line text-lg"
              >
                ×
              </button>
            </div>

            {status === "success" ? (
              <div className="mt-8 flex flex-col items-start gap-3 rounded-2xl bg-bone p-6">
                <p className="text-lg font-medium">Заявка отправлена</p>
                <p className="text-sm leading-relaxed text-ink/65">
                  Администратор свяжется с вами для подтверждения заказа.
                  Оплата — наложенным платежом при получении через{" "}
                  {COURIERS.find((c) => c.id === courier)?.name ?? "курьера"}.
                </p>
                <button
                  type="button"
                  onClick={onClose}
                  className="focus-ring mt-2 rounded-full bg-ink px-6 py-3 text-xs font-medium uppercase tracking-[0.1em] text-bone"
                >
                  Закрыть
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="mt-7 flex flex-col gap-5">
                <p className="text-sm leading-relaxed text-ink/60">
                  Оплата не производится онлайн — только наложенным платежом
                  при получении в офисе или по адресу через Econt / Speedy.
                </p>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <label className="flex flex-col gap-2 text-sm">
                    Имя и фамилия
                    <input
                      required
                      name="fullName"
                      autoComplete="name"
                      className="focus-ring rounded-xl border border-line bg-bone px-4 py-3 text-sm outline-none"
                      placeholder="Иван Иванов"
                    />
                  </label>
                  <label className="flex flex-col gap-2 text-sm">
                    Телефон
                    <input
                      required
                      name="phone"
                      type="tel"
                      autoComplete="tel"
                      className="focus-ring rounded-xl border border-line bg-bone px-4 py-3 text-sm outline-none"
                      placeholder="+359 ..."
                    />
                  </label>
                </div>

                <label className="flex flex-col gap-2 text-sm">
                  Город
                  <input
                    required
                    name="city"
                    autoComplete="address-level2"
                    className="focus-ring rounded-xl border border-line bg-bone px-4 py-3 text-sm outline-none"
                    placeholder="Varna"
                  />
                </label>

                <fieldset className="flex flex-col gap-3">
                  <legend className="text-sm">Способ получения</legend>
                  <div className="flex gap-3">
                    {COURIERS.map((c) => (
                      <button
                        type="button"
                        key={c.id}
                        onClick={() => setCourier(c.id)}
                        className={`focus-ring flex flex-1 items-center justify-center gap-2 rounded-xl border px-4 py-3 text-sm transition-colors ${
                          courier === c.id
                            ? "border-ink bg-ink text-bone"
                            : "border-line bg-bone text-ink/70"
                        }`}
                        aria-pressed={courier === c.id}
                      >
                        <CourierMark id={c.id} active={courier === c.id} />
                        {c.name}
                      </button>
                    ))}
                  </div>
                </fieldset>

                <label className="flex flex-col gap-2 text-sm">
                  Офис или адрес доставки
                  <input
                    required
                    name="officeOrAddress"
                    className="focus-ring rounded-xl border border-line bg-bone px-4 py-3 text-sm outline-none"
                    placeholder="Например: офис Speedy — ул. ..., № ..."
                  />
                </label>

                <label className="flex flex-col gap-2 text-sm">
                  Комментарий (необязательно)
                  <textarea
                    name="comment"
                    rows={3}
                    className="focus-ring resize-none rounded-xl border border-line bg-bone px-4 py-3 text-sm outline-none"
                    placeholder="Цвет, вариант, пожелания к доставке"
                  />
                </label>

                {status === "error" && (
                  <p role="alert" className="text-sm text-ink/70">
                    Не удалось отправить заявку. Попробуйте ещё раз или
                    свяжитесь с нами напрямую через контакты в подвале сайта.
                  </p>
                )}

                <button
                  type="submit"
                  disabled={status === "submitting"}
                  className="focus-ring mt-2 rounded-full bg-ink px-6 py-4 text-sm font-medium uppercase tracking-[0.08em] text-bone transition-opacity disabled:opacity-60"
                >
                  {status === "submitting" ? "Отправляем…" : "Отправить заявку"}
                </button>
              </form>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
