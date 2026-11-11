"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Maximize2 } from "lucide-react";
import { SLIDES, type SlideData } from "@/components/slides/slides";

/**
 * Projector-safe 16:9 deck for /slide.
 *
 * Keyboard: ← → PageUp/PageDown Space Home End, F fullscreen (Esc exits)
 * Deep link: /slide?slide=7
 */
export function SlideDeck({ data }: { data: SlideData }) {
  const [index, setIndex] = useState(0);
  const [isFs, setIsFs] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const go = useCallback((dir: number) => {
    setIndex((i) => Math.min(SLIDES.length - 1, Math.max(0, i + dir)));
  }, []);

  const toggleFullscreen = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    if (!document.fullscreenElement) {
      el.requestFullscreen?.().catch(() => {});
    } else {
      document.exitFullscreen?.().catch(() => {});
    }
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      switch (e.key) {
        case "ArrowRight":
        case "PageDown":
        case " ":
          e.preventDefault();
          go(1);
          break;
        case "ArrowLeft":
        case "PageUp":
          e.preventDefault();
          go(-1);
          break;
        case "Home":
          e.preventDefault();
          setIndex(0);
          break;
        case "End":
          e.preventDefault();
          setIndex(SLIDES.length - 1);
          break;
        case "f":
        case "F":
          e.preventDefault();
          toggleFullscreen();
          break;
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, toggleFullscreen]);

  useEffect(() => {
    const onFsChange = () => setIsFs(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", onFsChange);
    return () => document.removeEventListener("fullscreenchange", onFsChange);
  }, []);

  useEffect(() => {
    const raw = new URLSearchParams(window.location.search).get("slide");
    if (!raw) return;
    const n = Number.parseInt(raw, 10);
    if (!Number.isFinite(n)) return;
    const next = Math.min(SLIDES.length - 1, Math.max(0, n - 1));
    queueMicrotask(() => setIndex(next));
  }, []);

  const Slide = SLIDES[index];
  const progress = ((index + 1) / SLIDES.length) * 100;

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 z-[100] flex items-center justify-center overflow-hidden"
      style={{ background: "#1e293b" }}
    >
      <div
        className="relative bg-white shadow-2xl"
        style={{
          aspectRatio: "16 / 9",
          width: "min(100vw, calc(100vh * 16 / 9))",
          height: "min(100vh, calc(100vw * 9 / 16))",
          containerType: "size",
        }}
      >
        <div key={index} className="h-full w-full animate-fade">
          <Slide data={data} index={index} total={SLIDES.length} />
        </div>

        <div className="absolute inset-x-0 top-0 h-1 bg-slate-200">
          <div
            className="h-full bg-violet-600 transition-[width] duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {!isFs && (
        <button
          onClick={toggleFullscreen}
          title="Enter fullscreen (F)"
          aria-label="Enter fullscreen"
          className="fixed right-4 top-4 z-[110] flex h-11 w-11 items-center justify-center rounded-lg border-0 text-white/80 transition-colors hover:text-white"
          style={{ background: "rgba(15,23,42,0.6)" }}
        >
          <Maximize2 size={20} />
        </button>
      )}

      <div className="pointer-events-none fixed bottom-4 left-1/2 z-[110] -translate-x-1/2 select-none text-[13px] font-medium text-white/50">
        ← → to navigate · F for fullscreen · {index + 1} / {SLIDES.length}
      </div>
    </div>
  );
}
