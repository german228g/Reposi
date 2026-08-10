"use client";

import dynamic from "next/dynamic";
import { useRef } from "react";
import {
  motion,
  useMotionValueEvent,
  useScroll,
  useTransform,
  type MotionValue,
} from "framer-motion";
import { useOrderModal } from "@/context/OrderModalContext";
import { LazyMount } from "./LazyMount";

const StoryScene = dynamic(
  () => import("./three/StoryScene").then((mod) => mod.StoryScene),
  { ssr: false, loading: () => null }
);

const STAGES = [
  {
    label: "Материал",
    title: "Авиационный алюминий и усиленный ABS",
    text: "Корпус собран из двух слоёв: жёсткого металлического диска и ударопрочного пластика клипсы. Материалы и толщина — плейсхолдер, уточняются производителем.",
  },
  {
    label: "Сила крепления",
    title: "N52-магниты с точным центрированием",
    text: "Магнитный массив притягивает телефон за секунду и удерживает его при вибрации в движении. Точное значение силы (кг/N) — плейсхолдер под финальные тесты.",
  },
  {
    label: "Вращение",
    title: "Шаровой шарнир на 360°",
    text: "Ball-joint шарнир позволяет выставить экран под любым углом одним движением и зафиксировать положение без люфта.",
  },
  {
    label: "Совместимость",
    title: "MagSafe и большинство смартфонов",
    text: "Работает напрямую с MagSafe-корпусами или через магнитную пластину в чехле. Полный список совместимости — плейсхолдер, уточняется в карточке товара.",
  },
];

export function ProductStory() {
  const containerRef = useRef<HTMLDivElement>(null);
  const explodeRef = useRef(0);
  const { openOrder } = useOrderModal();

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  const explodeMotion = useTransform(scrollYProgress, [0, 0.45, 0.85, 1], [0, 1, 1, 0]);
  useMotionValueEvent(explodeMotion, "change", (v) => {
    explodeRef.current = v;
  });

  const stageIndex = useTransform(scrollYProgress, (v) =>
    Math.min(STAGES.length - 1, Math.floor(v * STAGES.length))
  );

  return (
    <section
      id="product-story"
      ref={containerRef}
      aria-labelledby="story-heading"
      className="relative bg-ink text-bone"
      style={{ height: "320vh" }}
    >
      <div className="sticky top-0 flex h-[100svh] flex-col overflow-hidden">
        <div className="container-edit flex items-center justify-between pt-28 pb-4">
          <span className="eyebrow text-bone/60">Product Story</span>
          <span className="eyebrow text-bone/60">TOPK Phone Holder</span>
        </div>

        <div className="container-edit grid flex-1 grid-cols-1 items-center gap-6 pb-16 lg:grid-cols-12">
          <div className="relative order-2 aspect-square w-full lg:order-1 lg:col-span-6">
            <LazyMount
              className="h-full w-full"
              fallback={
                <div className="flex h-full w-full items-center justify-center">
                  <div className="h-40 w-40 rounded-full border border-bone/15 sm:h-56 sm:w-56" />
                </div>
              }
            >
              <StoryScene explodeRef={explodeRef} />
            </LazyMount>
          </div>

          <div className="order-1 lg:order-2 lg:col-span-6">
            <h2 id="story-heading" className="text-balance text-3xl font-medium tracking-tight sm:text-5xl">
              Разбираем магнитное крепление до последней детали.
            </h2>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-bone/60">
              Прокрутите вниз — деталь за деталью держатель разбирается,
              показывая устройство магнитного притяжения, а затем
              собирается обратно.
            </p>

            <div className="mt-10 flex flex-col gap-6">
              {STAGES.map((stage, i) => (
                <StageRow key={stage.label} index={i} stageIndex={stageIndex} {...stage} />
              ))}
            </div>

            <button
              type="button"
              onClick={() => openOrder("TOPK Phone Holder")}
              className="focus-ring mt-10 w-fit rounded-full bg-bone px-7 py-4 text-xs font-medium uppercase tracking-[0.08em] text-ink transition-opacity hover:opacity-85"
            >
              Заказать этот держатель
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

function StageRow({
  index,
  stageIndex,
  label,
  title,
  text,
}: {
  index: number;
  stageIndex: MotionValue<number>;
  label: string;
  title: string;
  text: string;
}) {
  const opacity = useTransform(stageIndex, (v) => (v === index ? 1 : 0.8));

  return (
    <motion.div
      style={{ opacity }}
      className="border-l-2 border-bone/20 pl-5 transition-[border-color] duration-300"
    >
      <span className="eyebrow text-bone/75">{label}</span>
      <h3 className="mt-2 text-lg font-medium">{title}</h3>
      <p className="mt-1 max-w-md text-sm leading-relaxed text-bone/75">{text}</p>
    </motion.div>
  );
}
