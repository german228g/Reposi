/**
 * ============================================================================
 * VOLTENZA — ЕДИНЫЙ ФАЙЛ ДАННЫХ КАТАЛОГА
 * ============================================================================
 * Здесь хранятся все товары, наборы, категории, FAQ и плейсхолдеры отзывов.
 * Это единственный файл, который нужно редактировать владельцу магазина:
 *  - подставить реальные цены вместо "— €" плейсхолдеров;
 *  - подставить реальные фото в /public/products/*;
 *  - подставить реальную ссылку/канал заказа вместо "#order";
 *  - подставить контакты в разделе CONTACTS.
 * Ничего из перечисленного ниже не является реальными ценами или ссылками.
 * ============================================================================
 */

export type Badge = "НОВИНКА" | "В НАЛИЧИИ" | "ХИТ" | "ПОД ЗАКАЗ";

export type CategoryId =
  | "magnetic-power"
  | "mobile-mounts"
  | "everyday-carry"
  | "travel-essentials";

export interface Category {
  id: CategoryId;
  title: string;
  subtitle: string;
  description: string;
}

export interface ProductSpec {
  label: string;
  value: string;
}

export interface Product {
  id: string;
  name: string;
  category: CategoryId;
  description: string;
  /** Плейсхолдер цены — заменить на реальную цену владельцем. */
  price: string;
  /** Путь к изображению в /public. Заменить на реальное фото товара. */
  image: string;
  /**
   * Ссылка/якорь заказа. По умолчанию открывает форму заказа на сайте —
   * при отправке формы владельцу приходит уведомление о новом заказе,
   * дальнейшая связь и оплата — наложенным платежом через Econt/Speedy.
   */
  orderUrl: string;
  badge: Badge;
  inStock: boolean;
  specs: ProductSpec[];
}

export interface Kit {
  id: string;
  title: string;
  tagline: string;
  description: string;
  items: string[];
  /** Плейсхолдер цены набора — заменить на реальную цену. */
  price: string;
  orderUrl: string;
  image: string;
}

export interface Testimonial {
  id: string;
  quote: string;
  meta: string;
}

export interface FaqItem {
  id: string;
  question: string;
  answer: string;
}

export const CATEGORIES: Category[] = [
  {
    id: "magnetic-power",
    title: "Magnetic Power",
    subtitle: "Магнитная зарядка и удержание",
    description:
      "Беспроводная зарядка и магнитные держатели с точным притяжением — без проводов и лишних движений.",
  },
  {
    id: "mobile-mounts",
    title: "Mobile Mounts",
    subtitle: "Крепления для авто и дома",
    description:
      "Надёжные крепления на дефлектор, стекло и стол — телефон всегда под правильным углом.",
  },
  {
    id: "everyday-carry",
    title: "Everyday Carry",
    subtitle: "Каждый день с собой",
    description:
      "Кабели, батареи и мелкие аксессуары, которые незаметно решают повседневные задачи.",
  },
  {
    id: "travel-essentials",
    title: "Travel Essentials",
    subtitle: "В дорогу и в командировку",
    description:
      "Компактные решения для зарядки и крепления телефона вне дома — в самолёте, поезде, отеле.",
  },
];

export const PRODUCTS: Product[] = [
  {
    id: "topk-magnetic-vent-mount",
    name: "TOPK Phone Holder",
    category: "magnetic-power",
    description:
      "Powerful Magnetism — Heavy-Duty ABS Construction, Single-Hand Operation, Compatible with MagSafe, крепление на дефлектор кондиционера.",
    price: "15 €",
    image: "/products/topk-magnetic-vent-mount.jpg",
    orderUrl: "#order",
    badge: "ХИТ",
    inStock: true,
    specs: [
      { label: "Материал", value: "ABS + авиационный алюминий (плейсхолдер)" },
      { label: "Сила притяжения", value: "N52 магниты, до — кг (плейсхолдер)" },
      { label: "Крепление", value: "Дефлектор кондиционера, поворот 360°" },
      { label: "Совместимость", value: "MagSafe, большинство смартфонов с чехлом" },
    ],
  },
  {
    id: "voltenza-magsafe-charger-disc",
    name: "VOLTENZA MagCharge Disc",
    category: "magnetic-power",
    description:
      "Беспроводная магнитная зарядная панель — плоский алюминиевый диск с точным центрированием MagSafe.",
    price: "— €",
    image: "/products/magcharge-disc.jpg",
    orderUrl: "#order",
    badge: "НОВИНКА",
    inStock: true,
    specs: [
      { label: "Мощность зарядки", value: "— Вт (плейсхолдер)" },
      { label: "Материал корпуса", value: "Анодированный алюминий" },
      { label: "Кабель", value: "USB-C, — м (плейсхолдер)" },
      { label: "Совместимость", value: "MagSafe-совместимые смартфоны" },
    ],
  },
  {
    id: "voltenza-power-bank-10k",
    name: "VOLTENZA PowerCell 10K",
    category: "magnetic-power",
    description:
      "Магнитный powerbank с быстрой зарядкой — крепится на заднюю панель телефона и заряжает на ходу.",
    price: "— €",
    image: "/products/power-cell-10k.jpg",
    orderUrl: "#order",
    badge: "В НАЛИЧИИ",
    inStock: true,
    specs: [
      { label: "Ёмкость", value: "10 000 мАч (плейсхолдер)" },
      { label: "Выход", value: "— Вт быстрая зарядка (плейсхолдер)" },
      { label: "Крепление", value: "Магнитное, съёмное" },
      { label: "Индикатор заряда", value: "Цифровой дисплей" },
    ],
  },
  {
    id: "voltenza-vent-mount-pro",
    name: "VOLTENZA Vent Mount Pro",
    category: "mobile-mounts",
    description:
      "Крепление на дефлектор с усиленным шарниром и антивибрационной вставкой для устойчивого удержания в движении.",
    price: "— €",
    image: "/products/vent-mount-pro.jpg",
    orderUrl: "#order",
    badge: "В НАЛИЧИИ",
    inStock: true,
    specs: [
      { label: "Материал", value: "Алюминий + силиконовая вставка" },
      { label: "Угол поворота", value: "360° шаровой шарнир" },
      { label: "Совместимость", value: "Стандартные дефлекторы авто" },
      { label: "Установка", value: "Без инструментов, 1 движение" },
    ],
  },
  {
    id: "voltenza-dash-mount",
    name: "VOLTENZA Dash Mount",
    category: "mobile-mounts",
    description:
      "Магнитное крепление на торпедо или стекло с усиленной клеевой площадкой и незаметным профилем.",
    price: "— €",
    image: "/products/dash-mount.jpg",
    orderUrl: "#order",
    badge: "ПОД ЗАКАЗ",
    inStock: false,
    specs: [
      { label: "Материал", value: "Металл + ABS" },
      { label: "Крепление к поверхности", value: "3M-подобная клеевая площадка (плейсхолдер)" },
      { label: "Сила притяжения", value: "N52 магниты" },
      { label: "Совместимость", value: "MagSafe и стандартные смартфоны" },
    ],
  },
  {
    id: "voltenza-desk-stand",
    name: "VOLTENZA Desk Stand",
    category: "mobile-mounts",
    description:
      "Настольная магнитная подставка для звонков и просмотра — устойчивое основание, регулируемый угол.",
    price: "— €",
    image: "/products/desk-stand.jpg",
    orderUrl: "#order",
    badge: "НОВИНКА",
    inStock: true,
    specs: [
      { label: "Материал", value: "Утяжелённое металлическое основание" },
      { label: "Угол обзора", value: "Регулируемый, ландшафт/портрет" },
      { label: "Совместимость", value: "MagSafe-совместимые смартфоны" },
      { label: "Кабель-канал", value: "Скрытая прокладка кабеля" },
    ],
  },
  {
    id: "voltenza-braided-cable",
    name: "VOLTENZA Braided Cable",
    category: "everyday-carry",
    description:
      "Плетёный кабель повышенной прочности для быстрой зарядки — усиленные разъёмы, минимум 10 000 циклов изгиба.",
    price: "— €",
    image: "/products/braided-cable.jpg",
    orderUrl: "#order",
    badge: "В НАЛИЧИИ",
    inStock: true,
    specs: [
      { label: "Длина", value: "— м (плейсхолдер)" },
      { label: "Оплётка", value: "Нейлон, армированные разъёмы" },
      { label: "Скорость зарядки", value: "Fast Charge (плейсхолдер)" },
      { label: "Совместимость", value: "USB-C / Lightning (уточняется)" },
    ],
  },
  {
    id: "voltenza-cable-organizer",
    name: "VOLTENZA Cable Organizer",
    category: "everyday-carry",
    description:
      "Компактный органайзер для кабелей и мелких аксессуаров — держит рабочее место и сумку в порядке.",
    price: "— €",
    image: "/products/cable-organizer.jpg",
    orderUrl: "#order",
    badge: "В НАЛИЧИИ",
    inStock: true,
    specs: [
      { label: "Материал", value: "Силикон / веган-кожа (плейсхолдер)" },
      { label: "Вместимость", value: "До — кабелей (плейсхолдер)" },
      { label: "Крепление", value: "Магнитная застёжка" },
      { label: "Цвет", value: "Чёрный / Bone" },
    ],
  },
  {
    id: "voltenza-travel-pouch",
    name: "VOLTENZA Travel Pouch",
    category: "travel-essentials",
    description:
      "Дорожный чехол для держателя, кабелей и powerbank — компактно помещается в ручную кладь.",
    price: "— €",
    image: "/products/travel-pouch.jpg",
    orderUrl: "#order",
    badge: "НОВИНКА",
    inStock: true,
    specs: [
      { label: "Материал", value: "Водоотталкивающая ткань (плейсхолдер)" },
      { label: "Размер", value: "— × — см (плейсхолдер)" },
      { label: "Отделения", value: "2 внутренних + 1 внешнее" },
      { label: "Вес", value: "— г (плейсхолдер)" },
    ],
  },
  {
    id: "voltenza-mini-powerbank",
    name: "VOLTENZA Mini PowerCell 5K",
    category: "travel-essentials",
    description:
      "Компактный магнитный powerbank для путешествий — помещается в карман, заряжает телефон на ходу.",
    price: "— €",
    image: "/products/mini-power-cell-5k.jpg",
    orderUrl: "#order",
    badge: "ХИТ",
    inStock: true,
    specs: [
      { label: "Ёмкость", value: "5 000 мАч (плейсхолдер)" },
      { label: "Габариты", value: "Карманный формат" },
      { label: "Крепление", value: "Магнитное" },
      { label: "Зарядка самого powerbank", value: "USB-C, — Вт (плейсхолдер)" },
    ],
  },
];

export const KITS: Kit[] = [
  {
    id: "kit-car",
    title: "Для автомобиля",
    tagline: "Magnetic Power + Mobile Mounts",
    description:
      "Комплект для авто: магнитное крепление на дефлектор, зарядный диск и кабель — телефон всегда под рукой в дороге.",
    items: [
      "VOLTENZA Vent Mount Pro",
      "VOLTENZA MagCharge Disc",
      "VOLTENZA Braided Cable",
    ],
    price: "— €",
    orderUrl: "#order",
    image: "/products/kit-car.jpg",
  },
  {
    id: "kit-travel",
    title: "Для путешествий",
    tagline: "Travel Essentials",
    description:
      "Всё для поездки: компактный powerbank, дорожный чехол и универсальный держатель для отеля и транспорта.",
    items: [
      "VOLTENZA Mini PowerCell 5K",
      "VOLTENZA Travel Pouch",
      "TOPK Phone Holder",
    ],
    price: "— €",
    orderUrl: "#order",
    image: "/products/kit-travel.jpg",
  },
  {
    id: "kit-everyday",
    title: "Для повседневного использования",
    tagline: "Everyday Carry",
    description:
      "Базовый набор на каждый день: настольная подставка, плетёный кабель и органайзер для порядка на столе.",
    items: [
      "VOLTENZA Desk Stand",
      "VOLTENZA Braided Cable",
      "VOLTENZA Cable Organizer",
    ],
    price: "— €",
    orderUrl: "#order",
    image: "/products/kit-everyday.jpg",
  },
];

export const TESTIMONIALS: Testimonial[] = [
  {
    id: "t1",
    quote: "Здесь появится отзыв первого покупателя VOLTENZA.",
    meta: "Плейсхолдер отзыва — заменить после первых заказов",
  },
  {
    id: "t2",
    quote: "Место для реального отзыва о качестве и доставке.",
    meta: "Плейсхолдер отзыва — заменить после первых заказов",
  },
  {
    id: "t3",
    quote: "Здесь можно разместить отзыв о работе магнитного крепления.",
    meta: "Плейсхолдер отзыва — заменить после первых заказов",
  },
  {
    id: "t4",
    quote: "Место для отзыва о скорости доставки Econt/Speedy.",
    meta: "Плейсхолдер отзыва — заменить после первых заказов",
  },
  {
    id: "t5",
    quote: "Здесь появится отзыв о качестве повседневных аксессуаров.",
    meta: "Плейсхолдер отзыва — заменить после первых заказов",
  },
  {
    id: "t6",
    quote: "Место для отзыва о наборе для путешествий.",
    meta: "Плейсхолдер отзыва — заменить после первых заказов",
  },
];

export const FAQ_ITEMS: FaqItem[] = [
  {
    id: "faq-compatibility",
    question: "Совместимость: подойдёт ли держатель к моему телефону?",
    answer:
      "Большинство держателей VOLTENZA совместимы с MagSafe и работают со смартфонами через магнитную пластину в чехле. Точную совместимость модели уточняйте в описании товара или у администратора перед заказом.",
  },
  {
    id: "faq-delivery",
    question: "Как происходит доставка?",
    answer:
      "Доставка осуществляется через Econt или Speedy наложенным платежом — вы оплачиваете заказ при получении в офисе курьера или по адресу. Онлайн-оплата и подписки не используются.",
  },
  {
    id: "faq-check",
    question: "Можно ли проверить товар перед оплатой?",
    answer:
      "Да, при получении в офисе Econt/Speedy наложенным платежом вы можете проверить товар перед оплатой согласно правилам курьерской службы.",
  },
  {
    id: "faq-return",
    question: "Какие условия возврата?",
    answer:
      "Условия возврата уточняются индивидуально с администратором при оформлении заказа. Свяжитесь с нами через указанный канал связи для деталей (плейсхолдер политики возврата).",
  },
  {
    id: "faq-order",
    question: "Как оформить заказ?",
    answer:
      "Выберите товар в каталоге, нажмите «Заказать», заполните форму с контактными данными и предпочитаемым способом доставки. Администратор свяжется с вами для подтверждения деталей.",
  },
];

export const CONTACTS = {
  city: "Varna, Bulgaria",
  instagram: "скоро",
  tiktok: "скоро",
  whatsapp: "скоро",
  email: "скоро",
};

export const COURIERS = [
  { id: "speedy", name: "Speedy" },
  { id: "econt", name: "Econt" },
] as const;
