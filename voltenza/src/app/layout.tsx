import type { Metadata, Viewport } from "next";
import { Inter_Tight } from "next/font/google";
import "./globals.css";

const interTight = Inter_Tight({
  variable: "--font-inter-tight",
  subsets: ["latin", "latin-ext"],
  display: "swap",
  weight: ["400", "500", "600", "700", "800", "900"],
});

const siteUrl = "https://voltenza.eu";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "VOLTENZA — Энергия. Притяжение. Движение.",
    template: "%s — VOLTENZA",
  },
  description:
    "VOLTENZA — тщательно отобранные аксессуары для энергии, крепления и повседневного использования смартфона. Магнитные держатели, powerbank и автомобильные крепления. Варна, Болгария.",
  keywords: [
    "VOLTENZA",
    "магнитный держатель телефона",
    "powerbank",
    "автомобильное крепление",
    "аксессуары для смартфона",
    "MagSafe держатель",
    "Варна",
    "Болгария",
  ],
  applicationName: "VOLTENZA",
  authors: [{ name: "VOLTENZA" }],
  openGraph: {
    type: "website",
    locale: "ru_RU",
    url: siteUrl,
    siteName: "VOLTENZA",
    title: "VOLTENZA — Энергия. Притяжение. Движение.",
    description:
      "Тщательно отобранные мобильные аксессуары: магнитные держатели, powerbank и крепления. Строгий дизайн, надёжная функциональность.",
  },
  twitter: {
    card: "summary_large_image",
    title: "VOLTENZA — Энергия. Притяжение. Движение.",
    description:
      "Тщательно отобранные мобильные аксессуары для энергии, крепления и повседневного использования.",
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export const viewport: Viewport = {
  themeColor: "#0a0a0a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className={`${interTight.variable} h-full`}>
      <body className="min-h-full flex flex-col bg-bone text-ink antialiased">
        {children}
      </body>
    </html>
  );
}
