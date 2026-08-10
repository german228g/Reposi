import { NextResponse } from "next/server";

/**
 * ============================================================================
 * Приём заказов — интеграционная точка для владельца магазина.
 * ============================================================================
 * Сейчас заказ только валидируется и логируется на сервере. Чтобы заказы
 * реально попадали "в личный кабинет" администратора, подключите здесь один
 * из вариантов:
 *   1. Отправку письма (Resend / Nodemailer + SMTP) на рабочую почту.
 *   2. Отправку сообщения в Telegram-бота (Bot API, chatId администратора).
 *   3. Запись в базу данных / Google Sheets / CRM для последующей обработки.
 * Плейсхолдеры цены, ссылок и контактов заполняются в src/data/products.ts.
 * ============================================================================
 */

interface OrderPayload {
  productName: string;
  fullName: string;
  phone: string;
  city: string;
  courier: string;
  officeOrAddress: string;
  comment?: string;
}

function isValidPayload(data: unknown): data is OrderPayload {
  if (!data || typeof data !== "object") return false;
  const d = data as Record<string, unknown>;
  return (
    typeof d.productName === "string" &&
    d.productName.trim().length > 0 &&
    typeof d.fullName === "string" &&
    d.fullName.trim().length > 1 &&
    typeof d.phone === "string" &&
    d.phone.trim().length > 5 &&
    typeof d.city === "string" &&
    d.city.trim().length > 1 &&
    typeof d.courier === "string" &&
    d.courier.trim().length > 0 &&
    typeof d.officeOrAddress === "string" &&
    d.officeOrAddress.trim().length > 1
  );
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }

  if (!isValidPayload(body)) {
    return NextResponse.json({ ok: false, error: "invalid_payload" }, { status: 400 });
  }

  // TODO(owner): заменить console.log на реальную отправку уведомления.
  console.log("[VOLTENZA] Новый заказ (наложенный платёж):", {
    ...body,
    receivedAt: new Date().toISOString(),
  });

  return NextResponse.json({ ok: true });
}
