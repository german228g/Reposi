"use client";

import { Reveal } from "./Reveal";
import { CourierMark } from "./CourierMark";

const STEPS = [
  {
    n: "01",
    title: "Выберите товар",
    text: "Просмотрите каталог или наборы и определитесь с моделью, цветом и комплектацией.",
  },
  {
    n: "02",
    title: "Свяжитесь через указанный канал",
    text: "Заполните форму заказа на сайте — заявка попадает администратору, который свяжется с вами для подтверждения деталей.",
  },
  {
    n: "03",
    title: "Получите через Econt / Speedy",
    text: "Доставка наложенным платежом — вы оплачиваете заказ при получении в офисе курьера или по указанному адресу.",
  },
];

export function HowToOrder() {
  return (
    <section
      id="how-to-order"
      aria-labelledby="order-heading"
      className="border-t border-line bg-bone py-24 sm:py-32"
    >
      <div className="container-edit">
        <Reveal className="max-w-xl">
          <span className="eyebrow text-ink/60">Как заказать</span>
          <h2 id="order-heading" className="mt-4 text-balance text-4xl font-medium tracking-tight sm:text-5xl">
            Просто, без онлайн-оплаты и подписок.
          </h2>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-8 sm:grid-cols-3">
          {STEPS.map((step, i) => (
            <Reveal key={step.n} delay={i * 0.1}>
              <div className="flex h-full flex-col gap-4 border-t border-ink/20 pt-6">
                <span className="text-sm font-medium text-ink/60">{step.n}</span>
                <h3 className="text-xl font-medium tracking-tight">{step.title}</h3>
                <p className="text-sm leading-relaxed text-ink/60">{step.text}</p>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.2} className="mt-16 flex flex-wrap items-center gap-6 border-t border-line pt-10">
          <span className="text-sm uppercase tracking-[0.08em] text-ink/60">
            Доставка наложенным платежом:
          </span>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-2 rounded-full border border-line px-4 py-2 text-sm">
              <CourierMark id="speedy" /> Speedy
            </span>
            <span className="flex items-center gap-2 rounded-full border border-line px-4 py-2 text-sm">
              <CourierMark id="econt" /> Econt
            </span>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
