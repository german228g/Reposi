"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { OrderModal } from "@/components/OrderModal";

interface OrderModalContextValue {
  openOrder: (productName: string) => void;
}

const OrderModalContext = createContext<OrderModalContextValue | null>(null);

export function OrderModalProvider({ children }: { children: ReactNode }) {
  const [activeProduct, setActiveProduct] = useState<string | null>(null);

  const openOrder = useCallback((productName: string) => {
    setActiveProduct(productName);
  }, []);

  const close = useCallback(() => setActiveProduct(null), []);

  const value = useMemo(() => ({ openOrder }), [openOrder]);

  return (
    <OrderModalContext.Provider value={value}>
      {children}
      <OrderModal productName={activeProduct} onClose={close} />
    </OrderModalContext.Provider>
  );
}

export function useOrderModal() {
  const ctx = useContext(OrderModalContext);
  if (!ctx) {
    throw new Error("useOrderModal must be used within OrderModalProvider");
  }
  return ctx;
}
