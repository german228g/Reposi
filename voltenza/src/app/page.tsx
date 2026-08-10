import { Header } from "@/components/Header";
import { Hero } from "@/components/Hero";
import { Categories } from "@/components/Categories";
import { Catalog } from "@/components/Catalog";
import { ProductStory } from "@/components/ProductStory";
import { Kits } from "@/components/Kits";
import { HowToOrder } from "@/components/HowToOrder";
import { Testimonials } from "@/components/Testimonials";
import { Faq } from "@/components/Faq";
import { Footer } from "@/components/Footer";
import { OrderModalProvider } from "@/context/OrderModalContext";

export default function Home() {
  return (
    <OrderModalProvider>
      <Header />
      <main>
        <Hero />
        <Categories />
        <Catalog />
        <ProductStory />
        <Kits />
        <HowToOrder />
        <Testimonials />
        <Faq />
      </main>
      <Footer />
    </OrderModalProvider>
  );
}
