import type { Metadata } from "next";
import { SlideDeck } from "@/components/slides/deck";
import { gates, outcomes, pilot, pilotTable, planned } from "@/lib/pilot-data";

export const metadata: Metadata = {
  title: "Slides",
  robots: { index: false },
};

export default function SlidePage() {
  return <SlideDeck data={{ pilot, planned, outcomes, gates, pilotTable }} />;
}
