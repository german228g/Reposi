import { CONTACTS } from "@/data/products";

const SOCIALS = [
  { label: "Instagram", value: CONTACTS.instagram },
  { label: "TikTok", value: CONTACTS.tiktok },
  { label: "WhatsApp", value: CONTACTS.whatsapp },
  { label: "Email", value: CONTACTS.email },
];

export function Footer() {
  return (
    <footer id="contacts" className="border-t border-line bg-ink py-16 text-bone">
      <div className="container-edit">
        <div className="grid grid-cols-1 gap-12 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <p className="text-2xl font-semibold tracking-[0.14em]">VOLTENZA</p>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-bone/60">
              Тщательно отобранные аксессуары для энергии, крепления и
              повседневного использования смартфона.
            </p>
            <p className="mt-6 text-xs uppercase tracking-[0.14em] text-bone/60">
              {CONTACTS.city}
            </p>
          </div>

          <div className="lg:col-span-3">
            <p className="eyebrow text-bone/60">Контакты</p>
            <ul className="mt-5 flex flex-col gap-3 text-sm">
              {SOCIALS.map((social) => (
                <li key={social.label} className="flex items-center justify-between gap-4 text-bone/70">
                  <span>{social.label}</span>
                  <span className="text-bone/60">{social.value}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-4">
            <p className="eyebrow text-bone/60">Навигация</p>
            <ul className="mt-5 flex flex-col gap-3 text-sm text-bone/70">
              <li><a className="focus-ring inline-block py-1.5 hover:text-bone" href="#catalog">Каталог</a></li>
              <li><a className="focus-ring inline-block py-1.5 hover:text-bone" href="#kits">Наборы</a></li>
              <li><a className="focus-ring inline-block py-1.5 hover:text-bone" href="#how-to-order">Доставка</a></li>
              <li><a className="focus-ring inline-block py-1.5 hover:text-bone" href="#faq">FAQ</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-16 flex flex-col gap-4 border-t border-bone/15 pt-6 text-xs uppercase tracking-[0.08em] text-bone/60 sm:flex-row sm:items-center sm:justify-between">
          <span>© {new Date().getFullYear()} VOLTENZA. Все права защищены.</span>
          <span>Оплата — наложенным платежом через Econt / Speedy</span>
        </div>
      </div>
    </footer>
  );
}
