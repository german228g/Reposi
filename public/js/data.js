// Дані по областях України.
// pop2021 — оцінка населення на початок 2022 (Укрстат, до повномасштабного вторгнення).
// status — стилізація DeepState: occupied (червоний), contested (помаранчевий), liberated (зелений).
// occupiedPct — орієнтовна частка території області, окупована РФ (станом на 2026, наближено).
// factor — коефіцієнт зниження населення до 2026 (війна, біженці, мобілізація).
// pop2026 = Math.round(pop2021 * factor) — ПРИКЛАДНЕ населення, оцінка.

window.OBLAST_DATA = {
  "Автономна Республіка Крим":   { pop2021: 2413000, status: "occupied",   occupiedPct: 100, factor: 0.62 },
  "Вінницька область":          { pop2021: 1548000, status: "liberated",  occupiedPct: 0,   factor: 0.80 },
  "Волинська область":           { pop2021: 1028000, status: "liberated",  occupiedPct: 0,   factor: 0.92 },
  "Дніпропетровська область":   { pop2021: 3166000, status: "liberated",  occupiedPct: 0,   factor: 0.80 },
  "Донецька область":            { pop2021: 4067000, status: "occupied",   occupiedPct: 90,  factor: 0.55 },
  "Житомирська область":         { pop2021: 1196000, status: "liberated",  occupiedPct: 0,   factor: 0.82 },
  "Закарпатська область":        { pop2021: 1250000, status: "liberated",  occupiedPct: 0,   factor: 0.93 },
  "Запорізька область":          { pop2021: 1633000, status: "occupied",   occupiedPct: 70,  factor: 0.62 },
  "Івано-Франківська область":   { pop2021: 1359000, status: "liberated",  occupiedPct: 0,   factor: 0.93 },
  "Кіровоградська область":      { pop2021: 921000,  status: "liberated",  occupiedPct: 0,   factor: 0.82 },
  "Луганська область":           { pop2021: 2102000, status: "occupied",   occupiedPct: 95,  factor: 0.55 },
  "Львівська область":           { pop2021: 2478000, status: "liberated",  occupiedPct: 0,   factor: 0.95 },
  "Миколаївська область":        { pop2021: 1118000, status: "contested",  occupiedPct: 5,   factor: 0.72 },
  "Одеська область":             { pop2021: 2368000, status: "liberated",  occupiedPct: 0,   factor: 0.85 },
  "Полтавська область":          { pop2021: 1371000, status: "liberated",  occupiedPct: 0,   factor: 0.82 },
  "Рівненська область":          { pop2021: 1148000, status: "liberated",  occupiedPct: 0,   factor: 0.93 },
  "Сумська область":             { pop2021: 1059000, status: "contested",  occupiedPct: 0,   factor: 0.72 },
  "Тернопільська область":       { pop2021: 1029000, status: "liberated",  occupiedPct: 0,   factor: 0.93 },
  "Харківська область":          { pop2021: 2633000, status: "contested",  occupiedPct: 5,   factor: 0.70 },
  "Хмельницька область":         { pop2021: 1246000, status: "liberated",  occupiedPct: 0,   factor: 0.90 },
  "Черкаська область":           { pop2021: 1178000, status: "liberated",  occupiedPct: 0,   factor: 0.82 },
  "Чернівецька область":         { pop2021: 897000,  status: "liberated",  occupiedPct: 0,   factor: 0.93 },
  "Чернігівська область":        { pop2021: 968000,  status: "liberated",  occupiedPct: 0,   factor: 0.80 },
  "Херсонська область":          { pop2021: 1019000, status: "occupied",   occupiedPct: 85,  factor: 0.55 },
  "Київська область":            { pop2021: 1789000, status: "liberated",  occupiedPct: 0,   factor: 0.82 },
  "Севастополь":                 { pop2021: 510000,  status: "occupied",   occupiedPct: 100, factor: 0.62 },
};

// Найбільші міста (точки на карті). pop2026 — оцінка.
window.CITY_DATA = [
  { name: "Київ",        lat: 50.4501, lng: 30.5234, pop2026: 3000000, status: "liberated" },
  { name: "Харків",      lat: 49.9935, lng: 36.2304, pop2026: 1200000, status: "contested" },
  { name: "Одеса",       lat: 46.4825, lng: 30.7233, pop2026: 1010000, status: "liberated" },
  { name: "Дніпро",      lat: 48.4647, lng: 35.0462, pop2026: 980000,  status: "liberated" },
  { name: "Львів",       lat: 49.8397, lng: 24.0297, pop2026: 720000,  status: "liberated" },
  { name: "Запоріжжя",   lat: 47.8388, lng: 35.1396, pop2026: 700000,  status: "occupied"  },
  { name: "Кривий Ріг",  lat: 47.9100, lng: 33.3500, pop2026: 600000,  status: "liberated" },
  { name: "Миколаїв",    lat: 46.9750, lng: 32.0000, pop2026: 450000,  status: "contested" },
  { name: "Полтава",     lat: 49.5937, lng: 34.5407, pop2026: 280000,  status: "liberated" },
  { name: "Вінниця",     lat: 49.2331, lng: 28.4806, pop2026: 370000,  status: "liberated" },
  { name: "Івано-Франківськ", lat: 48.9226, lng: 24.7111, pop2026: 230000, status: "liberated" },
  { name: "Чернівці",    lat: 48.2916, lng: 25.9350, pop2026: 260000,  status: "liberated" },
];

window.STATUS_META = {
  occupied:  { label: "Окуповано РФ",     color: "#d32f2f", fill: "#d32f2f" },
  contested: { label: "Зона бойових дій", color: "#f57c00", fill: "#f59e0b" },
  liberated: { label: "Під контролем України", color: "#2e7d32", fill: "#388e3c" },
};

window.pop2026 = (oblast) => Math.round(oblast.pop2021 * oblast.factor);

window.fmt = (n) => n.toLocaleString("uk-UA");
