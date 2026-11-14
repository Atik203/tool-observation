import Link from "next/link";
import {
  AlertTriangle,
  ArrowDown,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  CircleCheck,
  ClipboardList,
  Database,
  FileText,
  Flag,
  Gauge,
  GitBranch,
  Layers,
  ListChecks,
  Presentation,
  RefreshCw,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  Timer,
  Workflow,
  Wrench,
  XCircle,
} from "lucide-react";
import { outcomes, phases, pilot, pilotTable, planned } from "@/lib/pilot-data";

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="max-w-2xl space-y-2">
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="display-title text-3xl md:text-4xl text-balance">{title}</h2>
      {description && <p className="text-base text-muted-foreground leading-relaxed">{description}</p>}
    </div>
  );
}

function Metric({ value, label, sub }: { value: string; label: string; sub: string }) {
  return (
    <div className="p-5 md:p-6 space-y-1.5">
      <div className="text-3xl md:text-4xl font-extrabold font-mono tnum tracking-tight">{value}</div>
      <div className="text-base font-semibold">{label}</div>
      <div className="text-xs text-muted-foreground">{sub}</div>
    </div>
  );
}

function ArmCard({ arm }: { arm: (typeof planned.arms)[number] }) {
  const tone =
    arm.id === "V"
      ? "border-slate-500/30 bg-slate-500/5"
      : arm.id === "s=0"
        ? "border-sky-500/30 bg-sky-500/5"
        : arm.id === "s=1"
          ? "border-teal-500/30 bg-teal-500/5"
          : arm.id === "s=2"
            ? "border-amber-500/30 bg-amber-500/5"
            : "border-rose-500/30 bg-rose-500/5";
  return (
    <article className={`rounded-xl border p-4 space-y-2 ${tone}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-base font-bold">{arm.id}</span>
        <span className="text-xs uppercase tracking-widest text-muted-foreground">{arm.level}</span>
      </div>
      <p className="text-sm leading-relaxed text-muted-foreground">{arm.change}</p>
      <p className="text-xs font-semibold">{arm.role}</p>
    </article>
  );
}

function OutcomeCard({ outcome }: { outcome: (typeof outcomes)[number] }) {
  return (
    <article className="glass-panel rounded-xl p-4 space-y-2">
      <div className="flex items-center gap-2">
        <span className="font-mono text-base font-bold text-teal-700 dark:text-teal-300">{outcome.id}</span>
        <span className="text-sm font-semibold">{outcome.label}</span>
      </div>
      <p className="text-sm leading-relaxed text-muted-foreground">{outcome.body}</p>
    </article>
  );
}

export default function Home() {
  return (
    <div className="space-y-12 md:space-y-16 max-w-6xl mx-auto pb-4">
      {/* Hero */}
      <section id="overview" className="grid lg:grid-cols-[1.05fr_0.95fr] gap-8 lg:gap-12 items-center pt-4 md:pt-10">
        <div className="space-y-6">
          <p className="eyebrow animate-rise flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-teal-700 dark:text-teal-300" aria-hidden />
            Fixed-prefix causal study · ToolResult-800
          </p>
          <h1 className="display-title text-4xl sm:text-5xl leading-[1.04] text-balance animate-rise [animation-delay:60ms]">
            Measure the moment a tool result changes the{" "}
            <span className="gradient-text">next decision</span>.
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-xl leading-relaxed animate-rise [animation-delay:120ms]">
            A controlled study of detection, reliance, and recovery when language-model agents read
            wrong tool results. Same prefix, same history, only the observation content changes.
          </p>
          <div className="flex flex-wrap items-center gap-3 animate-rise [animation-delay:180ms]">
            <Link
              href="/slide"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-teal-700 to-cyan-600 px-5 py-2.5 text-base font-semibold text-white shadow-lg shadow-teal-700/20 transition-all hover:from-teal-600 hover:to-cyan-500"
            >
              <Presentation className="w-4 h-4" aria-hidden /> View the 15-slide deck
            </Link>
            <Link
              href="/proposal.pdf"
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-secondary/60 px-5 py-2.5 text-base font-semibold transition-colors hover:bg-secondary"
            >
              <FileText className="w-4 h-4" aria-hidden /> Read the proposal
            </Link>
            <a
              href="#pilot"
              className="inline-flex items-center gap-1.5 px-2 py-2.5 text-base font-semibold text-muted-foreground transition-colors hover:text-foreground"
            >
              See the pilot <ArrowRight className="w-4 h-4" aria-hidden />
            </a>
          </div>
          <ul className="flex flex-wrap gap-x-5 gap-y-2 text-sm text-muted-foreground animate-rise [animation-delay:240ms]">
            {[
              `${planned.prefixes} real τ-bench prefixes planned`,
              "3 open-weight 7–8B families",
              `Pilot N=${pilot.n} · screening only`,
            ].map((t) => (
              <li key={t} className="inline-flex items-center gap-1.5">
                <CircleCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden /> {t}
              </li>
            ))}
          </ul>
        </div>

        {/* Hero visual — illustrative, not a harvested record */}
        <div className="space-y-3 animate-rise [animation-delay:200ms]">
          <div className="glass-panel rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between gap-3">
              <span className="eyebrow">frozen prefix · after tool call</span>
              <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-0.5 font-mono text-xs text-amber-700 dark:text-amber-300">
                s=2
              </span>
            </div>

            <div className="rounded-xl bg-slate-950 p-4 font-mono text-xs leading-relaxed text-slate-200 shadow-inner">
              <div className="text-slate-500">{"// tool observation"}</div>
              <div>{"{"}</div>
              <div className="pl-4">&quot;order_status&quot;: &quot;delivered&quot;,</div>
              <div className="pl-4">
                &quot;refund_amount&quot;: <span className="text-rose-400">48.50</span>,
              </div>
              <div className="pl-4">
                &quot;return_window_open&quot;: <span className="text-rose-400">false</span>
              </div>
              <div>{"}"}</div>
            </div>

            <div className="flex justify-center">
              <ArrowDown className="w-4 h-4 text-muted-foreground" aria-hidden />
            </div>

            <div className="rounded-xl border border-rose-500/30 bg-rose-500/5 p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm font-semibold text-rose-600 dark:text-rose-400">
                <AlertTriangle className="w-4 h-4" aria-hidden /> next decision
              </div>
              <p className="text-base leading-relaxed">
                &quot;I&apos;ve started the return. Your refund is <strong>$48.50</strong>.&quot;
              </p>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="rounded-full border border-border bg-secondary/60 px-2.5 py-0.5">action unchanged</span>
                <span className="rounded-full border border-border bg-secondary/60 px-2.5 py-0.5">no flag</span>
                <span className="rounded-full border border-rose-500/40 bg-rose-500/10 px-2.5 py-0.5 font-semibold text-rose-600 dark:text-rose-400">
                  silent propagation
                </span>
              </div>
            </div>

            <p className="text-xs text-muted-foreground">
              The true refund is $84.50 and the return window is open. Illustrative construction, not a
              harvested record.
            </p>
          </div>
        </div>
      </section>

      {/* Pilot evidence strip */}
      <section aria-label="Pilot evidence" className="glass-panel rounded-2xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 lg:divide-x divide-border/60 animate-fade">
        <Metric value={`${pilot.consult.pct.toFixed(1)}%`} label="Consult rate" sub={`${pilot.consult.count}/${pilot.consult.total} pilot prefixes`} />
        <Metric value={`${pilot.placeboJitter.pct.toFixed(0)}%`} label="Placebo jitter" sub={`${pilot.placeboJitter.count}/${pilot.placeboJitter.total} · P vs T`} />
        <Metric value={`${pilot.errorSwitch.pct.toFixed(1)}%`} label="Error switch" sub={`${pilot.errorSwitch.count}/${pilot.errorSwitch.total} · E vs T`} />
        <Metric value={`p=${pilot.mcnemar.p.toFixed(4)}`} label="McNemar exact" sub={`b=${pilot.mcnemar.b}, c=${pilot.mcnemar.c}`} />
      </section>
      <p className="-mt-8 text-center text-xs text-muted-foreground">
        Pilot: N={pilot.n} · {pilot.model} · {pilot.prefixType} · screening only
      </p>

      {/* The question */}
      <section id="question" className="space-y-6">
        <SectionHeading
          eyebrow="The question"
          title="One observation, three questions."
          description="The unit is a frozen conversation ending immediately after a real tool result. The target model produces the next decision; it never generates the prefix."
        />
        <div className="grid md:grid-cols-3 gap-4">
          {[
            {
              icon: ScanSearch,
              title: "Does content change the decision?",
              body: "Hold the prefix fixed. Change only the observation content. Measure whether the next decision departs from the verbatim continuation.",
            },
            {
              icon: Layers,
              title: "Is the change graded?",
              body: "s=1 changes one non-critical field. s=2 changes one critical field to a plausible wrong value. s=3 adds a second detectable contradiction.",
            },
            {
              icon: Timer,
              title: "How long does it last?",
              body: "Follow four steps after injection. R1 is a correct decision; R2 is explicit detection. A sequence with neither is censored at H=4.",
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <article key={item.title} className="glass-panel rounded-2xl p-5 space-y-3">
                <div className="w-9 h-9 rounded-xl surface-inset flex items-center justify-center">
                  <Icon className="w-4.5 h-4.5 text-teal-700 dark:text-teal-300" aria-hidden />
                </div>
                <h3 className="text-base font-bold">{item.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{item.body}</p>
              </article>
            );
          })}
        </div>
      </section>

      {/* The design */}
      <section id="design" className="space-y-6">
        <SectionHeading
          eyebrow="The design"
          title="Freeze the prefix. Change only the observation."
          description="Every arm is generated from the same frozen prefix. Task difficulty, domain, donor style, and conversation history cancel out."
        />
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {planned.arms.map((arm) => (
            <ArmCard key={arm.id} arm={arm} />
          ))}
        </div>

        <div className="glass-panel rounded-2xl p-5 md:p-6 space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-sm font-semibold">
            {["freeze prefix", "render arm", "query model", "code decision", "follow recovery"].map((step, i, arr) => (
              <div key={step} className="flex items-center gap-2">
                <span className="rounded-lg border border-border bg-secondary/60 px-3 py-1.5">{step}</span>
                {i < arr.length - 1 && <ArrowRight className="w-3.5 h-3.5 text-muted-foreground" aria-hidden />}
              </div>
            ))}
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
            {[
              { icon: Database, label: "800 + 80", sub: "primary + reserve prefixes" },
              { icon: GitBranch, label: "400 / 400", sub: "airline / retail" },
              { icon: Wrench, label: "3 families", sub: "open-weight 7–8B, AWQ" },
              { icon: Workflow, label: "34,800", sub: "generations in the envelope" },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.label} className="surface-inset rounded-xl p-3 flex items-start gap-3">
                  <Icon className="w-4 h-4 mt-0.5 text-teal-700 dark:text-teal-300" aria-hidden />
                  <div>
                    <div className="font-mono font-bold tnum">{item.label}</div>
                    <div className="text-xs text-muted-foreground">{item.sub}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Pilot */}
      <section id="pilot" className="space-y-6">
        <SectionHeading
          eyebrow="Pilot evidence"
          title="The manipulation is runnable. The estimate is marginal."
          description="The pilot used synthetic WebArena-lite / τ-style prefixes, qwen3.5:4b, greedy decoding, and three collapsed action codes. It is a screening signal, not a dose-response estimate."
        />
        <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-4">
          <div className="glass-panel rounded-2xl p-5 md:p-6">
            <div className="flex items-center justify-between gap-3 mb-4">
              <h3 className="text-base font-bold">Recorded pilot results</h3>
              <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-0.5 text-xs font-semibold uppercase tracking-widest text-amber-700 dark:text-amber-300">
                Screening only
              </span>
            </div>
            <div className="overflow-hidden rounded-xl border border-border">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="bg-secondary/70">
                    <th className="text-left px-3 py-2 font-semibold">Quantity</th>
                    <th className="text-right px-3 py-2 font-semibold">Result</th>
                  </tr>
                </thead>
                <tbody>
                  {pilotTable.map((row) => (
                    <tr key={row.quantity} className="border-t border-border/70">
                      <td className="px-3 py-2 text-muted-foreground">{row.quantity}</td>
                      <td className="px-3 py-2 text-right font-mono tnum font-semibold">{row.value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              The recorded 95% interval is an unpaired Wald interval; the paired McNemar test is the
              design-matched comparison.
            </p>
          </div>

          <div className="space-y-3">
            <div className="glass-panel rounded-2xl p-5 space-y-3">
              <h3 className="text-base font-bold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" aria-hidden /> What it establishes
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex gap-2"><CircleCheck className="w-3.5 h-3.5 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden /> The manipulation is runnable.</li>
                <li className="flex gap-2"><CircleCheck className="w-3.5 h-3.5 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden /> The model consults observations.</li>
                <li className="flex gap-2"><CircleCheck className="w-3.5 h-3.5 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden /> Error content can move the next action.</li>
                <li className="flex gap-2"><CircleCheck className="w-3.5 h-3.5 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden /> 12/12 human spot-check labels agree.</li>
              </ul>
            </div>
            <div className="glass-panel rounded-2xl p-5 space-y-3">
              <h3 className="text-base font-bold flex items-center gap-2">
                <XCircle className="w-4 h-4 text-rose-600 dark:text-rose-400" aria-hidden /> What it cannot establish
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {pilot.caveats.map((c) => (
                  <li key={c} className="flex gap-2"><span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0" aria-hidden /> {c}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Outcomes */}
      <section id="measure" className="space-y-6">
        <SectionHeading
          eyebrow="What we measure"
          title="A decision, not just a task score."
          description="A decision signature is the tool name plus canonicalized arguments, or the final answer action plus decision-critical slots. The verbatim V continuation is the reference."
        />
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {outcomes.map((outcome) => (
            <OutcomeCard key={outcome.id} outcome={outcome} />
          ))}
        </div>
        <div className="glass-panel rounded-2xl p-5 md:p-6 grid lg:grid-cols-[0.9fr_1.1fr] gap-5 items-center">
          <div className="space-y-2">
            <p className="eyebrow">Decomposition</p>
            <p className="font-mono text-base md:text-base font-bold">Y = Y^A ∨ Y^F ∨ Y^U</p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Strict silent propagation is <span className="font-mono">Y^U ∧ ¬Y^A ∧ ¬Y^F</span>. A flag at the
              injection step is detection, not recovery.
            </p>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <RefreshCw className="w-4 h-4 text-teal-700 dark:text-teal-300" aria-hidden /> Recovery over H=4
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              {[
                { label: "R1", title: "Corrected", body: "signature matches V" },
                { label: "R2", title: "Flagged", body: "explicit detection" },
                { label: "H=4", title: "Censored", body: "neither by step 4" },
              ].map((r) => (
                <div key={r.label} className="surface-inset rounded-xl p-3">
                  <div className="font-mono font-bold text-teal-700 dark:text-teal-300">{r.label}</div>
                  <div className="font-semibold mt-1">{r.title}</div>
                  <div className="text-muted-foreground mt-0.5">{r.body}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Roadmap */}
      <section id="roadmap" className="space-y-6">
        <SectionHeading
          eyebrow="What comes next"
          title="A bounded, pre-registered confirmatory study."
          description="The pilot is not pooled with the confirmatory sample. Every gate is sequential and frozen before the main run."
        />
        <div className="grid sm:grid-cols-3 gap-3">
          {[
            { icon: Database, title: "ToolResult-800", body: "800 real τ-bench prefixes, 400 airline + 400 retail, plus 80 reserve. Frozen before any target-model outcome." },
            { icon: Wrench, title: "3 model families", body: "Qwen2.5-7B, Mistral-7B-v0.3, and Llama-3.1-8B, 4-bit AWQ, greedy decoding." },
            { icon: Gauge, title: "34,800 generations", body: "12,000 base + 19,200 transient recovery + 2,400 persistent + 1,200 jitter repeats." },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <article key={item.title} className="glass-panel rounded-2xl p-5 space-y-3">
                <div className="w-9 h-9 rounded-xl surface-inset flex items-center justify-center">
                  <Icon className="w-4.5 h-4.5 text-teal-700 dark:text-teal-300" aria-hidden />
                </div>
                <h3 className="text-base font-bold">{item.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{item.body}</p>
              </article>
            );
          })}
        </div>

        <div className="glass-panel rounded-2xl p-5 md:p-6 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-base font-bold flex items-center gap-2">
              <ListChecks className="w-4 h-4 text-teal-700 dark:text-teal-300" aria-hidden /> Phase plan
            </h3>
            <span className="font-mono text-xs text-muted-foreground">$0 cash · 45 GPU-hour / 200 GB stop</span>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-6 gap-2">
            {phases.map((phase) => (
              <div key={phase.id} className="surface-inset rounded-xl p-3 space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-sm font-bold text-teal-700 dark:text-teal-300">{phase.id}</span>
                  <span className="text-xs text-muted-foreground">{phase.weeks}</span>
                </div>
                <div className="text-xs font-semibold leading-snug">{phase.name}</div>
                <div className="text-xs text-muted-foreground">{phase.gate}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Limits */}
      <section id="limits" className="space-y-6">
        <SectionHeading
          eyebrow="Limits"
          title="What this study will not claim."
          description="The claim is bounded by design. A null or flat slope is a publishable measurement result, not a failure to hide."
        />
        <div className="glass-panel rounded-2xl p-5 md:p-7 grid md:grid-cols-2 gap-6">
          <div className="space-y-3">
            {[
              "τ-bench tasks are public and may be memorized; baseline reliance could be inflated.",
              "Donor prefixes come from gpt-4o and claude-3.5-sonnet; target models continue off-policy histories.",
              "Severity is a constructed ordinal variable; if s=1 moves decisions like s=2, the dose interpretation fails.",
            ].map((text) => (
              <div key={text} className="flex gap-3 text-sm text-muted-foreground leading-relaxed">
                <Flag className="w-4 h-4 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden />
                {text}
              </div>
            ))}
          </div>
          <div className="space-y-3">
            {[
              "Three open-weight 7–8B families, two domains, one renderer, deterministic tools.",
              "Recovery is observed for four steps; longer horizons are censored.",
              "No universal law, model ranking, frontier transfer, or end-to-end task-success claim.",
            ].map((text) => (
              <div key={text} className="flex gap-3 text-sm text-muted-foreground leading-relaxed">
                <ShieldCheck className="w-4 h-4 mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden />
                {text}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="glass-panel rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center gap-6 justify-between">
        <div className="space-y-2 max-w-2xl">
          <h2 className="display-title text-3xl md:text-4xl">See the full story in 15 slides.</h2>
          <p className="text-base text-muted-foreground leading-relaxed">
            The deck covers the question, the pilot evidence, the five-arm design, the planned
            ToolResult-800 sample, the analysis gates, and the limits of the claim.
          </p>
        </div>
        <div className="flex flex-wrap gap-3 shrink-0">
          <Link
            href="/slide"
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-teal-700 to-cyan-600 px-5 py-2.5 text-base font-semibold text-white shadow-lg shadow-teal-700/20 transition-all hover:from-teal-600 hover:to-cyan-500"
          >
            <Presentation className="w-4 h-4" aria-hidden /> Open the deck
          </Link>
          <Link
            href="/proposal.pdf"
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-secondary/60 px-5 py-2.5 text-base font-semibold transition-colors hover:bg-secondary"
          >
            <BookOpen className="w-4 h-4" aria-hidden /> Proposal PDF
          </Link>
        </div>
      </section>

      {/* Small print */}
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5"><ClipboardList className="w-3 h-3" aria-hidden /> ToolResult-800</span>
        <span>·</span>
        <span>Pilot N={pilot.n} · screening only</span>
        <span>·</span>
        <span>Confirmatory design: 800 + 80 prefixes</span>
      </div>
    </div>
  );
}
