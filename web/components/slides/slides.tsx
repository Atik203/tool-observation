import type { ReactElement } from "react";
import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  Braces,
  CalendarDays,
  CheckCircle2,
  FileText,
  Gauge,
  GitBranch,
  Layers,
  ListChecks,
  Presentation,
  RefreshCw,
  Scale,
  ScanSearch,
  Search,
  ShieldCheck,
  Target,
  Timer,
  XCircle,
} from "lucide-react";
import {
  ACCENT,
  AMBER,
  Bullet,
  Card,
  Chip,
  DEEP_INK,
  KpiStrip,
  NEAR_BLACK,
  PipelineStrip,
  ROSE,
  SLATE,
  SlideFrame,
  SlideTable,
  TEAL,
} from "@/components/slides/primitives";
import { gates, outcomes, pilot, pilotTable, planned } from "@/lib/pilot-data";

export interface SlideData {
  pilot: typeof pilot;
  planned: typeof planned;
  outcomes: typeof outcomes;
  gates: typeof gates;
  pilotTable: typeof pilotTable;
}

type SlideProps = { data: SlideData; index: number; total: number };

const BADGE_INTRO = { badge: "Introduction", badgeBg: "#e0e7ff", badgeColor: ACCENT };
const BADGE_MOTIVATION = { badge: "Motivation", badgeBg: "#e0e7ff", badgeColor: ACCENT };
const BADGE_PILOT = { badge: "Pilot evidence", badgeBg: "#ccfbf1", badgeColor: TEAL };
const BADGE_OBJECTIVE = { badge: "Objective", badgeBg: "#e0e7ff", badgeColor: ACCENT };
const BADGE_METHOD = { badge: "Method", badgeBg: "#fef3c7", badgeColor: AMBER };
const BADGE_DATASET = { badge: "Dataset", badgeBg: "#ccfbf1", badgeColor: TEAL };
const BADGE_RESULTS = { badge: "Analysis", badgeBg: "#fee2e2", badgeColor: ROSE };
const BADGE_END = { badge: "Conclusion", badgeBg: "#ccfbf1", badgeColor: TEAL };

/* ───────────────────────────── 1 · Title ─────────────────────────── */

function TitleSlide({ index }: SlideProps) {
  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden bg-white px-[6.5cqw] pb-[2.2cqh] pt-[3.6cqh]">
      <div
        className="pointer-events-none absolute right-[-12cqw] top-[-20cqh] h-[56cqh] w-[56cqh] rounded-full"
        style={{ background: ACCENT, opacity: 0.07 }}
      />
      <div
        className="pointer-events-none absolute bottom-[-24cqh] left-[-10cqw] h-[44cqh] w-[44cqh] rounded-full"
        style={{ background: TEAL, opacity: 0.06 }}
      />
      <div className="relative flex items-center gap-[1.2cqw]">
        <span
          className="flex items-center justify-center rounded-xl text-white shadow-lg"
          style={{ width: "7cqh", height: "7cqh", background: ACCENT }}
        >
          <ScanSearch size="4cqh" />
        </span>
        <div>
          <div className="text-[2.1cqh] font-extrabold uppercase tracking-[0.18em]" style={{ color: ACCENT }}>
            ToolResult-800
          </div>
          <div className="text-[1.8cqh] font-semibold" style={{ color: SLATE }}>
            Fixed-prefix causal study
          </div>
        </div>
      </div>

      <div className="relative mt-[7cqh] max-w-[78cqw]">
        <h1 className="text-[6.8cqh] font-extrabold leading-[1.04]" style={{ color: NEAR_BLACK }}>
          Tool-Result Errors in Language-Model Agents
        </h1>
        <div className="mt-[2.2cqh] text-[3.2cqh] font-semibold" style={{ color: DEEP_INK }}>
          A Controlled Study of Detection, Reliance, and Recovery
        </div>
        <p className="mt-[2.2cqh] max-w-[62cqw] text-[2.25cqh] font-medium leading-snug" style={{ color: SLATE }}>
          Pilot evidence and a proposed confirmatory study across 800 real τ-bench prefixes,
          three open-weight model families, and four recovery steps.
        </p>
      </div>

      <div className="relative mt-[4cqh] flex flex-wrap gap-[1.2cqw]">
        <Chip color={ACCENT} bg="#e0e7ff">N=60 pilot · screening only</Chip>
        <Chip color={TEAL} bg="#ccfbf1">800 + 80 prefixes</Chip>
        <Chip color={AMBER} bg="#fef3c7">3 model families</Chip>
      </div>

      <div className="relative mt-auto flex items-end justify-between border-t-2 pt-[1.4cqh]" style={{ borderColor: "#e2e8f0" }}>
        <div className="text-[1.8cqh] font-semibold" style={{ color: SLATE }}>
          Supervisor meeting · November 2026
        </div>
        <div className="tnum text-[1.8cqh] font-bold" style={{ color: SLATE }}>
          {index + 1}
        </div>
      </div>
    </div>
  );
}

/* ───────────────────────────── 2 · The question ───────────────────── */

function QuestionSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_INTRO} title="One tool result. One next decision." subtitle="Does changing only the observation content change what the agent does next?" index={index} total={total}>
      <div className="grid min-h-0 flex-1 grid-cols-[1.05fr_0.95fr] gap-[2cqw]">
        <Card icon={<Braces size="2.8cqh" />} title="Tool observation" color={ACCENT} fill="#eef2ff">
          <div className="rounded-lg bg-[#0b1020] p-[1.6cqw] font-mono text-[2.05cqh] leading-relaxed text-slate-200">
            <div className="text-slate-500">{"// frozen prefix · after tool call"}</div>
            <div>{"{"}</div>
            <div className="pl-[1.2cqw]">&quot;order_status&quot;: &quot;delivered&quot;,</div>
            <div className="pl-[1.2cqw]">
              &quot;refund_amount&quot;: <span className="text-rose-400">48.50</span>,
            </div>
            <div className="pl-[1.2cqw]">
              &quot;return_window_open&quot;: <span className="text-rose-400">false</span>
            </div>
            <div>{"}"}</div>
          </div>
          <div className="mt-[1.4cqh] flex items-center gap-[0.8cqw] text-[1.95cqh] font-semibold" style={{ color: ROSE }}>
            <AlertTriangle size="2.2cqh" /> True refund is $84.50; the window is open.
          </div>
        </Card>

        <div className="flex min-h-0 flex-col gap-[1.4cqh]">
          <Card icon={<ShieldCheck size="2.8cqh" />} title="Trust the value" color={ROSE} fill="#fff1f2" className="flex-1">
            <div className="flex h-full flex-col justify-center">
              <div className="text-[2.3cqh] font-bold" style={{ color: NEAR_BLACK }}>
                &quot;Your refund is $48.50.&quot;
              </div>
              <div className="mt-[1cqh] text-[1.95cqh] font-semibold" style={{ color: SLATE }}>
                No flag. No re-query. The wrong value enters the answer.
              </div>
              <div className="mt-[1.4cqh]">
                <Chip color={ROSE} bg="#ffe4e6">silent propagation</Chip>
              </div>
            </div>
          </Card>
          <Card icon={<Search size="2.8cqh" />} title="Check the value" color={TEAL} fill="#f0fdfa" className="flex-1">
            <div className="flex h-full flex-col justify-center">
              <div className="text-[2.3cqh] font-bold" style={{ color: NEAR_BLACK }}>
                &quot;The window says closed, but it arrived three days ago. Let me verify.&quot;
              </div>
              <div className="mt-[1.4cqh]">
                <Chip color={TEAL} bg="#ccfbf1">detection / action switch</Chip>
              </div>
            </div>
          </Card>
        </div>
      </div>
      <div className="mt-[1.6cqh] rounded-lg bg-[#f1f5f9] px-[1.6cqw] py-[1.1cqh] text-center text-[2.05cqh] font-bold" style={{ color: DEEP_INK }}>
        Same prefix · same history · same policy · only the observation content changes
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 3 · Why it matters ─────────────────── */

function WhySlide({ index, total }: SlideProps) {
  const items = [
    { icon: <AlertTriangle size="2.8cqh" />, title: "Wrong refund", body: "The agent tells the customer $48.50 instead of $84.50.", color: ROSE, fill: "#fff1f2" },
    { icon: <CalendarDays size="2.8cqh" />, title: "Wrong date or policy", body: "A booking, return, or cancellation decision is made on a false premise.", color: AMBER, fill: "#fffbeb" },
    { icon: <BarChart3 size="2.8cqh" />, title: "Aggregate score", body: "The episode may still be marked completed because the transcript is fluent.", color: ACCENT, fill: "#eef2ff" },
  ];
  return (
    <SlideFrame {...BADGE_MOTIVATION} title="A fluent transcript can hide a wrong value." subtitle="The failure is not a wrong tool call or a planning error. It is a failure to notice that the observation conflicts with the context." index={index} total={total}>
      <div className="grid min-h-0 flex-1 grid-cols-3 gap-[1.6cqw]">
        {items.map((item) => (
          <Card key={item.title} icon={item.icon} title={item.title} color={item.color} fill={item.fill}>
            <div className="flex h-full flex-col justify-center">
              <p className="text-[2.35cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
                {item.body}
              </p>
            </div>
          </Card>
        ))}
      </div>
      <div className="mt-[1.6cqh] rounded-lg px-[1.6cqw] py-[1.2cqh] text-center text-[2.2cqh] font-bold" style={{ background: "#f1f5f9", color: DEEP_INK }}>
        End-to-end success does not tell us whether the agent noticed.
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 4 · What benchmarks miss ───────────── */

function BenchmarksSlide({ index, total }: SlideProps) {
  const cols = [
    { title: "End-to-end", examples: "τ-bench · AgentBench · WebArena", body: "Score the final state or task success. Usually one realization per observation.", color: ACCENT, fill: "#eef2ff" },
    { title: "Tool use", examples: "ToolLLM · MINT · BFCL", body: "Measure tool selection, arguments, and multi-turn feedback. Not observation content.", color: TEAL, fill: "#f0fdfa" },
    { title: "Safety", examples: "AgentDojo · InjecAgent · ToolEmu", body: "Study adversarial instructions. Not plausible factual errors or recovery.", color: AMBER, fill: "#fffbeb" },
  ];
  return (
    <SlideFrame {...BADGE_MOTIVATION} title="Benchmarks score the episode, not the observation." subtitle="Each family answers a different question. None isolates the content of a real tool result inside a frozen prefix." index={index} total={total}>
      <div className="grid min-h-0 flex-1 grid-cols-3 gap-[1.6cqw]">
        {cols.map((col) => (
          <div key={col.title} className="flex h-full min-h-0 flex-col rounded-xl border-2 px-[1.8cqw] py-[1.6cqh]" style={{ borderColor: col.color, background: col.fill }}>
            <div className="text-[2.8cqh] font-extrabold uppercase tracking-wide" style={{ color: col.color }}>{col.title}</div>
            <div className="mt-[0.8cqh] text-[1.95cqh] font-bold" style={{ color: SLATE }}>{col.examples}</div>
            <div className="mt-[1.2cqh] flex-1 text-[2.2cqh] font-medium leading-snug" style={{ color: NEAR_BLACK }}>{col.body}</div>
          </div>
        ))}
      </div>
      <div className="mt-[1.6cqh] rounded-lg px-[1.6cqw] py-[1.2cqh] text-center text-[2.2cqh] font-bold" style={{ background: "#eef2ff", color: ACCENT }}>
        Gap: no controlled, within-prefix estimate of content sensitivity and recovery.
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 5 · Pilot setup ────────────────────── */

function PilotSetupSlide({ data, index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_PILOT} title="A 60-prefix pilot tested whether the manipulation is runnable." subtitle="Synthetic WebArena-lite / τ-style prefixes · screening only" index={index} total={total}>
      <KpiStrip
        items={[
          { value: `${data.pilot.n}`, label: "prefixes", color: ACCENT, sub: "synthetic" },
          { value: "4B", label: "qwen3.5:4b", color: TEAL, sub: "greedy decoding" },
          { value: "3", label: "action codes", color: AMBER, sub: "trust / re-call / flag" },
          { value: "0", label: "recovery steps", color: ROSE, sub: "pilot limitation" },
        ]}
      />
      <div className="mt-[2cqh] grid min-h-0 flex-1 grid-cols-3 gap-[1.6cqw]">
        <Card icon={<Layers size="2.8cqh" />} title="Prefixes" color={ACCENT} fill="#eef2ff">
          <p className="text-[2.25cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
            Synthetic WebArena-lite / τ-style conversations, frozen immediately after a tool result.
          </p>
        </Card>
        <Card icon={<GitBranch size="2.8cqh" />} title="Arms" color={TEAL} fill="#f0fdfa">
          <p className="text-[2.25cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
            Truthful (T), placebo (P), and error (E). The pilot asked whether the error arm moves the next action.
          </p>
        </Card>
        <Card icon={<ListChecks size="2.8cqh" />} title="Coding" color={AMBER} fill="#fffbeb">
          <p className="text-[2.25cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
            Three collapsed codes: trust the value, re-call the tool, or flag the observation.
          </p>
        </Card>
      </div>
      <div className="mt-[1.4cqh] text-[1.9cqh] font-semibold" style={{ color: SLATE }}>
        This is a kill-gate, not an estimate of the confirmatory slope.
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 6 · Pilot results ──────────────────── */

function PilotResultsSlide({ data, index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_PILOT} title="The pilot moved the next action, but the estimate is marginal." subtitle="Recorded results · N=60 · screening only" index={index} total={total}>
      <div className="grid min-h-0 flex-1 grid-cols-[1.15fr_0.85fr] gap-[2cqw]">
        <SlideTable
          head={["Quantity", "Result"]}
          rows={data.pilotTable.map((row) => [row.quantity, row.value])}
          color={TEAL}
          headerBg="#ccfbf1"
          widths={["56%", "44%"]}
        />
        <div className="flex flex-col gap-[1.4cqh]">
          <Card icon={<Target size="2.8cqh" />} title="Read this carefully" color={ROSE} fill="#fff1f2" className="flex-1">
            <ul className="text-[2.05cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
              <Bullet>McNemar p=.0625 is marginal.</Bullet>
              <Bullet>The 95% interval includes a 1.3 pp effect.</Bullet>
              <Bullet>Letter coding missed some silent propagation.</Bullet>
            </ul>
          </Card>
          <div className="rounded-lg px-[1.4cqw] py-[1.1cqh] text-[1.95cqh] font-bold" style={{ background: "#f1f5f9", color: DEEP_INK }}>
            The pilot is a screening signal, not a dose-response estimate.
          </div>
        </div>
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 7 · What pilot establishes ─────────── */

function PilotLimitsSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_PILOT} title="What the pilot establishes — and what it cannot." subtitle="The result is useful as a kill-gate, not as the confirmatory claim." index={index} total={total}>
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[2cqw]">
        <Card icon={<CheckCircle2 size="2.8cqh" />} title="Establishes" color={TEAL} fill="#f0fdfa">
          <ul className="text-[2.2cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
            <Bullet>The manipulation is runnable.</Bullet>
            <Bullet>The model consults observations.</Bullet>
            <Bullet>Placebo jitter was 0/60.</Bullet>
            <Bullet>Error content can move the next action.</Bullet>
            <Bullet>12/12 human spot-check labels agree.</Bullet>
          </ul>
        </Card>
        <Card icon={<XCircle size="2.8cqh" />} title="Cannot establish" color={ROSE} fill="#fff1f2">
          <ul className="text-[2.2cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
            <Bullet>A dose-response slope.</Bullet>
            <Bullet>Recovery over four steps.</Bullet>
            <Bullet>Behaviour on real τ-bench prefixes.</Bullet>
            <Bullet>Other models or content-level sensitivity.</Bullet>
            <Bullet>A precise effect; p=.0625 is marginal.</Bullet>
          </ul>
        </Card>
      </div>
      <div className="mt-[1.6cqh] rounded-lg px-[1.6cqw] py-[1.2cqh] text-center text-[2.2cqh] font-bold" style={{ background: "#f1f5f9", color: DEEP_INK }}>
        The pilot is not pooled with the confirmatory sample.
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 8 · Objective ──────────────────────── */

function ObjectiveSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_OBJECTIVE} title="Estimate the causal effect of observation content." subtitle="Does content change the next decision, and is the change ordered by severity?" index={index} total={total}>
      <div className="grid min-h-0 flex-1 grid-cols-[0.95fr_1.05fr] gap-[2cqw]">
        <Card icon={<Target size="2.8cqh" />} title="Primary question" color={ACCENT} fill="#eef2ff">
          <div className="flex h-full flex-col justify-center">
            <p className="text-[2.6cqh] font-extrabold leading-snug" style={{ color: NEAR_BLACK }}>
              Conditional on a real tool observation inside a frozen prefix, does changing the
              observation&apos;s content change the agent&apos;s next decision?
            </p>
            <div className="mt-[1.6cqh] text-[2.05cqh] font-semibold" style={{ color: SLATE }}>
              Secondary: silent propagation, detection, action switch, and four-step recovery.
            </div>
          </div>
        </Card>
        <Card icon={<ListChecks size="2.8cqh" />} title="Pre-registered hypotheses" color={AMBER} fill="#fffbeb">
          <ul className="text-[2.05cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
            <Bullet><b>H1 (primary):</b> pooled slope β &gt; 0.</Bullet>
            <Bullet><b>H2:</b> positive in at least 2 of 3 models, same sign.</Bullet>
            <Bullet><b>H3:</b> silent propagation is a non-zero share at s=2 and s=3.</Bullet>
            <Bullet><b>H4:</b> at least 50% of the s=3 risk set recovers by H=4.</Bullet>
            <Bullet><b>H5:</b> the s=3 switch rate exceeds s=1.</Bullet>
          </ul>
        </Card>
      </div>
      <div className="mt-[1.4cqh] text-[1.9cqh] font-semibold" style={{ color: SLATE }}>
        H2 is a replication gate, not a model ranking. H4 is an estimation target, not a significance gate.
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 9 · Design ─────────────────────────── */

function DesignSlide({ data, index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_METHOD} title="Freeze the prefix. Change only the observation." subtitle="Every arm shares the same prefix, so task difficulty, domain, and donor style cancel out." index={index} total={total}>
      <PipelineStrip steps={["freeze prefix", "render arm", "query model", "code decision", "follow recovery"]} color={AMBER} bg="#fffbeb" />
      <div className="mt-[2cqh] grid min-h-0 flex-1 grid-cols-5 gap-[1cqw]">
        {data.planned.arms.map((arm) => (
          <div key={arm.id} className="flex h-full flex-col rounded-xl border-2 px-[1.2cqw] py-[1.4cqh]" style={{ borderColor: arm.id === "V" ? SLATE : arm.id === "s=0" ? TEAL : arm.id === "s=1" ? "#0e7490" : arm.id === "s=2" ? AMBER : ROSE, background: "#ffffff" }}>
            <div className="text-[3cqh] font-extrabold" style={{ color: arm.id === "V" ? SLATE : arm.id === "s=0" ? TEAL : arm.id === "s=1" ? "#0e7490" : arm.id === "s=2" ? AMBER : ROSE }}>{arm.id}</div>
            <div className="mt-[0.4cqh] text-[1.7cqh] font-bold uppercase tracking-wide" style={{ color: SLATE }}>level {arm.level}</div>
            <div className="mt-[0.9cqh] flex-1 text-[1.9cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>{arm.change}</div>
            <div className="mt-[0.8cqh] text-[1.75cqh] font-bold" style={{ color: SLATE }}>{arm.role}</div>
          </div>
        ))}
      </div>
      <div className="mt-[1.4cqh] rounded-lg px-[1.6cqw] py-[1.1cqh] text-[2.05cqh] font-bold" style={{ background: "#f1f5f9", color: DEEP_INK }}>
        V is excluded from the primary slope: it differs in format as well as content. s=0 is the placebo.
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 10 · ToolResult-800 ─────────────────── */

function DatasetSlide({ data, index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_DATASET} title="ToolResult-800: 800 real τ-bench prefixes, frozen before outcomes." subtitle="400 airline + 400 retail, plus 80 reserve. Target models never generate the prefix." index={index} total={total}>
      <KpiStrip
        items={[
          { value: `${data.planned.prefixes}`, label: "primary prefixes", color: TEAL, sub: "400 / 400" },
          { value: `${data.planned.reserve}`, label: "reserve", color: ACCENT, sub: "40 / 40" },
          { value: "3", label: "model families", color: AMBER, sub: "7–8B, AWQ" },
          { value: "98%", label: "replay match", color: ROSE, sub: "not relaxed" },
        ]}
      />
      <div className="mt-[2cqh] grid min-h-0 flex-1 grid-cols-[1.1fr_0.9fr] gap-[2cqw]">
        <SlideTable
          head={["Stage", "Count"]}
          rows={[
            ["Source trajectories", "1,980"],
            ["Post-tool candidates", "13,605"],
            ["JSON-parseable", "11,318"],
            ["Eligible value-used", "6,554"],
            ["Selected (primary + reserve)", "880"],
            ["Primary (airline / retail)", "800 (400 / 400)"],
          ]}
          color={TEAL}
          headerBg="#ccfbf1"
          widths={["62%", "38%"]}
        />
        <Card icon={<ShieldCheck size="2.8cqh" />} title="Freeze rules" color={ACCENT} fill="#eef2ff">
          <ul className="text-[2.05cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
            <Bullet>PII scrub; profile tools excluded.</Bullet>
            <Bullet>Replay ≥98%; mismatch taxonomy.</Bullet>
            <Bullet>Stratify by domain, donor, step, tool.</Bullet>
            <Bullet>Seed 20261108; no target outcomes before freeze.</Bullet>
          </ul>
        </Card>
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 11 · Manipulation ──────────────────── */

function ManipulationSlide({ data, index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_METHOD} title="Five arms, one deterministic renderer." subtitle="No LLM paraphrase enters the manipulation. s=0 preserves the full value set of V." index={index} total={total}>
      <SlideTable
        head={["Arm", "Level", "What changes", "Role"]}
        rows={data.planned.arms.map((arm) => [arm.id, arm.level, arm.change, arm.role])}
        color={AMBER}
        headerBg="#fef3c7"
        widths={["10%", "10%", "54%", "26%"]}
        compact
      />
      <div className="mt-[2cqh] grid grid-cols-[1fr_1fr] gap-[1.4cqw]">
        <div className="rounded-lg border-2 border-slate-200 bg-[#f8fafc] px-[1.4cqw] py-[1.2cqh]">
          <div className="text-[1.8cqh] font-bold uppercase tracking-wide" style={{ color: SLATE }}>s=2 example</div>
          <div className="mt-[0.6cqh] font-mono text-[2.05cqh] font-bold" style={{ color: NEAR_BLACK }}>
            refund $84.50 → <span style={{ color: ROSE }}>$48.50</span>
          </div>
        </div>
        <div className="rounded-lg border-2 border-slate-200 bg-[#fff1f2] px-[1.4cqw] py-[1.2cqh]">
          <div className="text-[1.8cqh] font-bold uppercase tracking-wide" style={{ color: ROSE }}>s=3 example</div>
          <div className="mt-[0.6cqh] font-mono text-[2.05cqh] font-bold" style={{ color: NEAR_BLACK }}>
            $48.50 + <span style={{ color: ROSE }}>window closed</span> while delivered 3 days ago
          </div>
        </div>
      </div>
      <div className="mt-[1.4cqh] text-[1.9cqh] font-semibold" style={{ color: SLATE }}>
        PII fields are never perturbed. Every record stores the JSON path, true value, false value, criticality, and renderer version.
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 12 · Outcomes and recovery ─────────── */

function OutcomesSlide({ data, index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_METHOD} title="Code the decision, then follow four steps." subtitle="The decision signature is the tool name plus canonicalized arguments, or the final answer action plus key slots." index={index} total={total}>
      <div className="grid grid-cols-4 gap-[1.2cqw]">
        {data.outcomes.map((outcome) => (
          <div key={outcome.id} className="rounded-xl border-2 border-slate-200 bg-white px-[1.2cqw] py-[1.2cqh]">
            <div className="font-mono text-[2.6cqh] font-extrabold" style={{ color: ACCENT }}>{outcome.id}</div>
            <div className="mt-[0.3cqh] text-[1.95cqh] font-bold" style={{ color: NEAR_BLACK }}>{outcome.label}</div>
            <div className="mt-[0.5cqh] text-[1.75cqh] font-semibold leading-snug" style={{ color: SLATE }}>{outcome.body}</div>
          </div>
        ))}
      </div>
      <div className="mt-[2cqh] grid min-h-0 flex-1 grid-cols-[1.05fr_0.95fr] gap-[2cqw]">
        <Card icon={<RefreshCw size="2.8cqh" />} title="Recovery" color={TEAL} fill="#f0fdfa">
          <div className="flex h-full flex-col justify-center">
            <PipelineStrip steps={["inject", "h=1", "h=2", "h=3", "h=4"]} color={TEAL} bg="#ccfbf1" />
            <div className="mt-[1.4cqh] text-[2.05cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
              R1 = signature first matches V. R2 = explicit flag. Neither by H=4 = censored.
            </div>
          </div>
        </Card>
        <Card icon={<Gauge size="2.8cqh" />} title="Decomposition" color={ROSE} fill="#fff1f2">
          <div className="flex h-full flex-col justify-center">
            <div className="font-mono text-[2.8cqh] font-extrabold" style={{ color: NEAR_BLACK }}>
              Y = Y^A ∨ Y^F ∨ Y^U
            </div>
            <div className="mt-[1.2cqh] text-[2.05cqh] font-semibold leading-snug" style={{ color: SLATE }}>
              Strict silent propagation = Y^U ∧ ¬Y^A ∧ ¬Y^F. A flag at injection is detection, not recovery.
            </div>
          </div>
        </Card>
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 13 · Analysis and gates ────────────── */

function AnalysisSlide({ data, index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_RESULTS} title="A pre-registered, gated analysis." subtitle="Pooled slope first, then per-model slopes with Holm. No model ranking is a confirmatory claim." index={index} total={total}>
      <div className="grid min-h-0 flex-1 grid-cols-[0.9fr_1.1fr] gap-[2cqw]">
        <div className="flex flex-col gap-[1.2cqh]">
          <Card icon={<BarChart3 size="2.8cqh" />} title="Primary model" color={ROSE} fill="#fff1f2">
            <div className="font-mono text-[2.5cqh] font-extrabold" style={{ color: NEAR_BLACK }}>
              logit P(Y=1) = α<sub>p,m</sub> + β<sub>m</sub>s
            </div>
            <div className="mt-[0.8cqh] text-[1.9cqh] font-semibold" style={{ color: SLATE }}>
              Conditional logistic, stratified by prefix; cluster-robust SE by prefix.
            </div>
          </Card>
          <Card icon={<Timer size="2.8cqh" />} title="Recovery model" color={TEAL} fill="#f0fdfa">
            <div className="font-mono text-[2.2cqh] font-extrabold" style={{ color: NEAR_BLACK }}>
              P(recover at h | not yet) = 1 − e<sup>−μ</sup>
            </div>
            <div className="mt-[0.6cqh] font-mono text-[2.2cqh] font-extrabold" style={{ color: NEAR_BLACK }}>
              t<sub>1/2</sub> = ln 2 / μ
            </div>
            <div className="mt-[0.8cqh] text-[1.9cqh] font-semibold" style={{ color: SLATE }}>
              Kaplan–Meier and RMST reported regardless; Weibull shape LRT at p&lt;.01.
            </div>
          </Card>
        </div>
        <SlideTable
          head={["Gate", "Pass criterion"]}
          rows={data.gates.map((gate) => [gate.id, `${gate.when}: ${gate.criterion}`])}
          color={ACCENT}
          headerBg="#e0e7ff"
          widths={["12%", "88%"]}
          compact
        />
      </div>
      <div className="mt-[1.4cqh] rounded-lg px-[1.6cqw] py-[1.1cqh] text-[2.05cqh] font-bold" style={{ background: "#f1f5f9", color: DEEP_INK }}>
        A null or flat slope is a measurement result. It is not reframed as a positive law.
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 14 · Expected outcome and limits ───── */

function ConclusionSlide({ index, total }: SlideProps) {
  return (
    <SlideFrame {...BADGE_END} title="A bounded result — or a well-powered null." subtitle="The claim is limited by the sample, the renderer, the rubric, and the four-step horizon." index={index} total={total}>
      <div className="grid min-h-0 flex-1 grid-cols-2 gap-[2cqw]">
        <Card icon={<CheckCircle2 size="2.8cqh" />} title="If the gates pass" color={TEAL} fill="#f0fdfa">
          <ul className="text-[2.1cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
            <Bullet>A positive pooled slope, graded by severity.</Bullet>
            <Bullet>A silent-propagation share, not just a task score.</Bullet>
            <Bullet>A recovery curve with a pooled half-life where identifiable.</Bullet>
            <Bullet>Bounded to 3 families, 2 domains, one renderer, H=4.</Bullet>
          </ul>
        </Card>
        <Card icon={<Scale size="2.8cqh" />} title="If the result is null" color={ROSE} fill="#fff1f2">
          <ul className="text-[2.1cqh] font-semibold leading-snug" style={{ color: NEAR_BLACK }}>
            <Bullet>A measurement result at a known precision.</Bullet>
            <Bullet>A released dataset and a replicable protocol.</Bullet>
            <Bullet>No post-hoc reframing as a positive law.</Bullet>
            <Bullet>No model ranking, frontier transfer, or end-to-end claim.</Bullet>
          </ul>
        </Card>
      </div>
      <div className="mt-[1.6cqh] grid grid-cols-3 gap-[1.2cqw]">
        {[
          "Public tasks may be memorized; donor prefixes are off-policy.",
          "Severity is constructed; s=1 is a negative control.",
          "Deterministic tools, two domains, four-step horizon.",
        ].map((text) => (
          <div key={text} className="rounded-lg border border-slate-200 bg-[#f8fafc] px-[1.2cqw] py-[1.1cqh] text-[1.85cqh] font-semibold leading-snug" style={{ color: SLATE }}>
            {text}
          </div>
        ))}
      </div>
    </SlideFrame>
  );
}

/* ───────────────────────────── 15 · Thank you ─────────────────────── */

function ThankYouSlide({ index }: SlideProps) {
  return (
    <div className="relative flex h-full w-full flex-col overflow-hidden bg-white px-[6.5cqw] pb-[2.2cqh] pt-[3.6cqh]">
      <div
        className="pointer-events-none absolute right-[-12cqw] top-[-20cqh] h-[56cqh] w-[56cqh] rounded-full"
        style={{ background: ACCENT, opacity: 0.07 }}
      />
      <div
        className="pointer-events-none absolute bottom-[-24cqh] left-[-10cqw] h-[44cqh] w-[44cqh] rounded-full"
        style={{ background: TEAL, opacity: 0.06 }}
      />
      <div className="relative flex items-center gap-[1.2cqw]">
        <span className="flex items-center justify-center rounded-xl text-white shadow-lg" style={{ width: "7cqh", height: "7cqh", background: ACCENT }}>
          <ScanSearch size="4cqh" />
        </span>
        <div className="text-[2.1cqh] font-extrabold uppercase tracking-[0.18em]" style={{ color: ACCENT }}>
          ToolResult-800
        </div>
      </div>
      <div className="relative mt-[10cqh] max-w-[70cqw]">
        <h1 className="text-[8cqh] font-extrabold leading-none" style={{ color: NEAR_BLACK }}>
          Thank you.
        </h1>
        <p className="mt-[2cqh] text-[3cqh] font-semibold" style={{ color: DEEP_INK }}>
          Questions and discussion.
        </p>
        <div className="mt-[3cqh] flex flex-wrap gap-[1.2cqw]">
          <Chip color={ACCENT} bg="#e0e7ff">Pilot N=60 · screening only</Chip>
          <Chip color={TEAL} bg="#ccfbf1">Confirmatory 800 + 80</Chip>
        </div>
      </div>
      <div className="relative mt-auto flex flex-wrap items-center gap-x-[2.4cqw] gap-y-[0.8cqh] border-t-2 pt-[1.4cqh] text-[1.8cqh] font-semibold" style={{ borderColor: "#e2e8f0", color: SLATE }}>
        <span className="inline-flex items-center gap-[0.6cqw]"><Presentation size="2.1cqh" /> Slides: /slide</span>
        <span className="inline-flex items-center gap-[0.6cqw]"><FileText size="2.1cqh" /> Proposal: /proposal.pdf</span>
        <span className="inline-flex items-center gap-[0.6cqw]"><BookOpen size="2.1cqh" /> Repository: Atik203/tool-observation</span>
        <span className="ml-auto tnum">{index + 1}</span>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */

export const SLIDES: Array<(props: SlideProps) => ReactElement> = [
  TitleSlide,
  QuestionSlide,
  WhySlide,
  BenchmarksSlide,
  PilotSetupSlide,
  PilotResultsSlide,
  PilotLimitsSlide,
  ObjectiveSlide,
  DesignSlide,
  DatasetSlide,
  ManipulationSlide,
  OutcomesSlide,
  AnalysisSlide,
  ConclusionSlide,
  ThankYouSlide,
];
