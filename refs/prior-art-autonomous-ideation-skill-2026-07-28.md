# Prior Art: Autonomous Ideation Skill

Date: 2026-07-28
Source: prior-art-search (web research)
Queries run: 5
Hits fetched in depth: 3

## Search anchor

What existing tools, frameworks, and research projects implement autonomous ideation â generating, scoring, and converging on ideas without a human in the loop â and what does this mean for the `ideate-solo` skill?

## Direct competitors / equivalents

Open-source tools, Claude Code skills, and commercial products that already do autonomous ideation. Grouped by primary shape.

**Autonomous loops (single-agent, long-running):**

- **Ralph Ideate** â [github.com/fabianboth/ralph-ideate](https://github.com/fabianboth/ralph-ideate). The closest analog. Claude Code slash command loop: ideate â research â scrutinize â decide. Ideas progress through `candidates/` â `verified/` â `discarded/` folders. User steers; loop does the legwork. Default `--max-iterations 20`.
- **OctoBot** â [github.com/petejwoodbridge/Octobot](https://github.com/petejwoodbridge/Octobot). Local-first via Ollama. Infinite loop generating invention pitches into a searchable markdown library. No cloud subscription.
- **Claude-Ideation-Planning-Plugin** â [github.com/danielrosehill/Claude-Ideation-Planning-Plugin](https://github.com/danielrosehill/Claude-Ideation-Planning-Plugin). Claude plugin variant.
- **BrainPath** â [brainpath.io/agents/brainstorming](https://brainpath.io/agents/brainstorming). 24/7 multi-LLM orchestration (GPT-4 / Claude) selecting the best model per task.

**Multi-agent collaborative systems:**

- **Autonomous Product Studio (APS)** â [github.com/autonomousproductstudio-ai/aps](https://github.com/autonomousproductstudio-ai/aps). 5 subagents (CEO / Research / Product / Architecture / Execution) + 52 tools. Real-time research across arXiv, GitHub, HN. Generates full startup packages with evidence grounding.
- **VentureNode** â [venture-node.vercel.app](https://venture-node.vercel.app/). 6 agents in a LangGraph state machine. Scores ideas on 5 dimensions. Notion integration.
- **IdeationAgent** â [github.com/Ideation-Agent/IdeationAgent](https://github.com/Ideation-Agent/IdeationAgent). 4 personas: researcher, devil's advocate, angel's advocate, chief of staff. Built at an AutoGPT hackathon.
- **Synapse** â [github.com/keananwongso/synapse](https://github.com/keananwongso/synapse). Spatial canvas (React Flow) with Fetch.ai agents branching into parallel streams.
- **CrewAI-Brainstormer** â [github.com/CyrilDesch/crewai-brainstormer](https://github.com/CyrilDesch/crewai-brainstormer). IBM Enterprise Design Thinking methodology.

**Product-first / vertical frameworks:**

- **Solo Product Agent** â [github.com/zhoupppp/solo-product-agent](https://github.com/zhoupppp/solo-product-agent). Decision Gate model. Validates market before coding. Only stops for strategic pivots.
- **Autensa** â [autensa.com](https://autensa.com/). Commercial. Full lifecycle: monitors codebase + market, generates feature ideas, Tinder-style swipe-to-learn, ships GitHub PRs autonomously.
- **Agentfounder** â [agentfounder.ai](https://agentfounder.ai/). 24/7 business cycles: sales, dev, financial reporting.
- **aut-o** â [aut-o.com](https://aut-o.com/). 9-stage quality-gated pipeline.
- **KickUp** â [github.com/rizkiwijanarko/KickUp](https://github.com/rizkiwijanarko/KickUp). Pain points â investor-ready pitch briefs + competitive matrices.
- **LaunchMind** â [github.com/muhammadhaider02/LaunchMind](https://github.com/muhammadhaider02/LaunchMind). Text idea â micro-startup with GitHub PRs and landing pages.
- **FoundrAI** â [foundrai.xyz](https://foundrai.xyz/). Similar shape.
- **VentureSmith** â [github.com/mikitsik/venture_smith](https://github.com/mikitsik/venture_smith).

**Methodology-driven tools:**

- **RAD-Brainstormer** â [RadOrigin-LLC/RAD-Claude-Skills](https://github.com/RadOrigin-LLC/RAD-Claude-Skills/tree/main/plugins/rad-brainstormer). Forces divergent before convergent. Uses SCAMPER, Six Thinking Hats, reverse brainstorming. Prevents anchoring.
- **Creative Ideation** â [github.com/yogsoth-ai/creative-ideation](https://github.com/yogsoth-ai/creative-ideation). 10 parallel creativity campaigns (structural deconstruction, biomimicry, lateral thinking).

**Restricted-scope:**

- **brainstorming-only** â [github.com/Dimon94/brainstorming-only](https://github.com/Dimon94/brainstorming-only). Explicitly restricted to discussion/diagnostic â cannot create specs, write code, or scaffold files.

## Failed attempts

Tools and companies that tried autonomous or agent-driven ideation and shut down or pivoted. Selection bias warning: these are well-known because they failed loudly.

- **TensorZero** â archived June 12, 2026. 11.7k stars, $7.3M seed (<half spent), zero debt, returned capital. Cause: **bundling**. Foundation model labs (Anthropic, OpenAI) and clouds shipped native gateways, evals, observability. ClickHouse acquired Langfuse for $400M in January 2026. Lesson: "stars are distribution, not a moat." The "neutral middle" wedge is closing. Source: [dreaming.press postmortem](https://dreaming.press/posts/tensorzero-shutdown-llmops-squeeze.html).
- **Yupp.ai** â $33M raised, shut down March 31, 2026. Cause: agentic systems made crowdsourced model evaluation obsolete. Architectural mismatch with where the field moved.
- **Phind** â AI search for developers, shut down January 16, 2026. Cause: foundation labs shipped native web search, absorbed the product feature set.
- **Vibe AI** â AI companion, shut down February 2026. Cause: compute costs of long emotional conversations incompatible with subscription pricing. **Sustainable-margin test failed**.
- **Olive AI** â once valued at $4B, raised $902M. Sold "autonomous" AI to hospitals that was actually supervised RPA. Couldn't scale to real-world hospital IT heterogeneity.
- **Humane (AI Pin)** â $230M raised, collapsed February 2025. Hardware without a compelling use case that beat smartphones. Relied on commoditized APIs that competitors could replicate.
- **Sieve, Coordinal** â "demoware" that worked on synthetic benchmarks but failed in production agentic workflows.
- **Super AI** â all-in-one routing layer, shut down March 2025. Foundation models converged on quality; routing layer became redundant.

The dominant failure mode is **bundling**. Tools that just orchestrate LLM APIs without owning data, vertical depth, or proprietary state get absorbed by the labs.

## Academic / formal

- **Deep Ideation** â [arxiv 2511.02238](https://arxiv.org/html/2511.02238) (Tsinghua). Explore-expand-evolve workflow over a scientific concept network of ~100,000 papers from 10 major AI conferences (last decade). Critic model fine-tuned on real reviewer feedback. **+10.67% quality over baselines**; reaches acceptance level at 8/10 AI conferences. The most rigorous published benchmark of autonomous ideation quality.
- **Multi-Agent LLM Dialogues for Research Ideation** â [arxiv 2507.08350](https://arxiv.org/html/2507.08350) (SIGDIAL 2025). Ideation-critique-revision loops. Larger agent cohort + more diverse critic agents â more novel + feasible ideas. **Three iterations is the sweet spot** â diminishing returns after.
- **RamÃ³n Llull's Thinking Machine for Automated Ideation** â [arxiv 2508.19200v2](https://arxiv.org/html/2508.19200v2). Symbolic recombination of themes, domains, methods from existing papers.
- **AutoResearcher** â [arxiv 2510.20844v3](https://arxiv.org/html/2510.20844v3). Knowledge-grounded transparent ideation with multi-agent collaboration.
- **LLM-Assisted Ideation Review** â [arxiv 2503.00946v2](https://arxiv.org/html/2503.00946v2). Field survey.
- **Chain of Ideas** â [EMNLP 2025 findings](https://aclanthology.org/anthology-files/pdf/findings/2025.findings-emnlp.477.pdf). Novel idea development via LLM agents.
- **AI-Augmented Brainwriting** â [ACM 2024 dl.acm.org/doi/10.1145/3613904.3642414](https://dl.acm.org/doi/10.1145/3613904.3642414). LLM-augmented group ideation.
- **SCI-IDEA** â [Springer 2026 link.springer.com/article/10.1007/s10994-026-07036-8](https://link.springer.com/article/10.1007/s10994-026-07036-8). Context-aware scientific ideation with **Aha-Moment Detection** module.
- **Measuring the Gap Between Human and LLM Research Ideas** â [arxiv 2607.01233v1](https://arxiv.org/html/2607.01233v1). Establishes that LLM-generated ideas concentrate on synthesis patterns and miss broader research paradigms. Proposes **research-taste taxonomies**.
- **Trade-offs in LLM-Supported Research Ideation** â [arxiv 2601.12152v1](https://arxiv.org/abs/2601.12152v1). Transparency, ownership, human-in-the-loop as central design concerns, not afterthoughts.
- **A Review of LLM-Assisted Ideation** â [arxiv 2503.00946v2](https://arxiv.org/html/2503.00946v2). Survey of evaluation metrics, with finding that automated metrics diverge from human expert ratings.

**Key empirical finding across multiple papers:** AI-generated ideas are rated **more novel** than human ideas; **human ideas retain a feasibility advantage**. AI-human dyads improve fluency/flexibility but **don't reduce cognitive load** â users invest effort in evaluating AI suggestions.

## Adjacent / historical

Computer-aided creativity is not new. A 50-year arc pre-dates LLM-agents.

- **Pygmalion** (1975, David Canfield Smith, Xerox PARC) â visual programming environment; introduced **icons** as subsuming variables/functions/data structures â direct ancestor to GUI icons. Program-by-demonstration on an "electronic blackboard." Source: [Pygmalion thesis](https://web.media.mit.edu/~lieber/Publications/Pygmalion-Remixed.pdf).
- **AARON** (Harold Cohen, 1970sâ2016, 40-year collaboration) â symbolic rule-based system; encoded Cohen's cognitive rules for spatial relationships, figure-ground dynamics. Exhibited at LACMA, Tate, SFMOMA. Source: [Computer History Museum](https://computerhistory.org/blog/harold-cohen-and-aaron-a-40-year-collaboration/).
- **EMI** (David Cope) â music composition; analyzes and mimics classical composer styles.
- **TALE-SPIN** (1977) â narrative generation.
- **JAPE** (1994) â pun generation.
- **2005 NSF workshop** â established the "creativity support tools" research agenda: exploratory search, rich history-keeping, rapid alternative generation.
- **The Combinator** â combinational creativity; links unrelated ideas via a simulation approach. Source: [Cambridge Design Science](https://www.cambridge.org/core/journals/design-science/article/combinator-a-computerbased-tool-for-creative-idea-generation-based-on-a-simulation-approach/12C723397EB477F421699D02A025E724).
- **Polymorphic creativity support tools** â adapt to specific user needs (e.g., novice designers in participatory innovation).

Two foundational approaches that still echo in current systems: **amplification** (Pygmalion â extend the human) vs **autonomous creation** (AARON â replace the human). Modern autonomous ideation sits much closer to AARON than Pygmalion.

## What this means for the autonomous ideation skill

### Competitive landscape

The space is **crowded and converging**. Twelve-plus active projects (Ralph Ideate, APS, Solo Product Agent, VentureNode, Autensa, Agentfounder, aut-o, IdeationAgent, OctoBot, Creative Ideation, Synapse, CrewAI-Brainstormer, RAD-Brainstormer) cover the same problem. The pattern is converging on:

- **Multi-agent ideation-critique-revision loops** with explicit evidence grounding (web search, literature mining).
- **Structured scoring on 4-5 dimensions** (painkiller / switching cost / defensibility / testability, or domain-specific variants).
- **Pipeline-shaped outputs** (candidates â verified â discarded, or similar gates).
- **Max-iteration bounds** (Ralph Ideate: 20; Multi-Agent Dialogues research: 3 is the sweet spot).

The autonomous ideation skill is **not novel in concept**. Differentiation must come from execution context, not core mechanics.

### Why previous attempts failed

The dominant failure mode is **bundling**. TensorZero, Phind, Yupp, and Super AI all died because foundation model labs shipped native equivalents. The "neutral middle" wedge is closing. Other failures: unsustainable unit economics (Vibe AI), demoware that fails in production (Sieve, Coordinal), fake autonomy sold as AI (Olive AI). **Three tests from the postmortems** worth internalizing:

1. **Scaling test** â does the product solve a specific, high-value problem, or is it a horizontal layer that gets absorbed by the labs?
2. **Sustainable-margin test** â does the compute cost fit inside what a user will pay?
3. **Defensibility test** â can a foundation model provider replicate this in a two-week sprint?

### Why no one has tried this

Someone has tried this extensively. But **what is NOT well-explored is the integration of negative-skill-space thinking into ideation**: most tools focus on generation and scoring, not on **what the generated idea doesn't cover**. The `ideate-solo` skill's 4-heuristic scoring (painkiller / switching cost / defensibility / testability) overlaps with several competitors, but its explicit gap-map output (the "Generation log" section) is rarer.

### Open opportunity

Three places where `ideate-solo` + `idea-kill` + `prior-art-search` could differentiate from existing tooling:

1. **Gap-aware ideation as a first-class output.** Most tools generate ideas; few systematically map what the ideas *don't* cover. Adding the `negative-skill-space` axis (axis 11, calibration â and the meta-reasoning of "what's outside this idea's scope") to the scoring heuristics is novel.
2. **Skill-format portability.** Most autonomous ideation tools are products (run a server, deploy a pipeline, depend on a vendor). A `ideate-solo` SKILL.md that runs inside an agent's existing context is more portable â it inherits the agent's memory, tools, and prior-session state.
3. **Honest kill verdict as a sibling.** Most ideation tools produce artifacts; few produce structured KILL/PAUSE/REVISE/SHIP verdicts with explicit reasoning. `idea-kill` as a sibling skill makes this a first-class output.

### Why no one has tried the negative-skill-space angle

Most ideation tools are evaluated on **novelty** (Deep Ideation's metric). The field has not yet built tooling around **gap-awareness** as an evaluation axis. This is a known unknown â most published work (including Deep Ideation) measures novelty and feasibility but does not measure "what the idea systematically fails to cover." The `negative-skill-space` skill I built earlier this session is a step toward making this axis measurable.

## Sources

**Deep reads (3):**

- [arxiv.org/html/2511.02238 â Deep Ideation](https://arxiv.org/html/2511.02238) â academic; full explore-expand-evolve workflow
- [dreaming.press/posts/tensorzero-shutdown-llmops-squeeze.html â TensorZero shutdown](https://dreaming.press/posts/tensorzero-shutdown-llmops-squeeze.html) â failed-attempt postmortem
- [github.com/fabianboth/ralph-ideate â Ralph Ideate README](https://github.com/fabianboth/ralph-ideate) â direct competitor; architecture and pipeline

**Direct competitors (top hits from searches):**

- [github.com/autonomousproductstudio-ai/aps](https://github.com/autonomousproductstudio-ai/aps)
- [github.com/zhoupppp/solo-product-agent](https://github.com/zhoupppp/solo-product-agent)
- [github.com/Ideation-Agent/IdeationAgent](https://github.com/Ideation-Agent/IdeationAgent)
- [github.com/petejwoodbridge/Octobot](https://github.com/petejwoodbridge/Octobot)
- [github.com/yogsoth-ai/creative-ideation](https://github.com/yogsoth-ai/creative-ideation)
- [github.com/keananwongso/synapse](https://github.com/keananwongso/synapse)
- [github.com/CyrilDesch/crewai-brainstormer](https://github.com/CyrilDesch/crewai-brainstormer)
- [github.com/Dimon94/brainstorming-only](https://github.com/Dimon94/brainstorming-only)
- [github.com/danielrosehill/Claude-Ideation-Planning-Plugin](https://github.com/danielrosehill/Claude-Ideation-Planning-Plugin)
- [RadOrigin-LLC/RAD-Claude-Skills](https://github.com/RadOrigin-LLC/RAD-Claude-Skills/tree/main/plugins/rad-brainstormer)
- [brainpath.io/agents/brainstorming](https://brainpath.io/agents/brainstorming)
- [autensa.com](https://autensa.com/)
- [agentfounder.ai](https://agentfounder.ai/)
- [aut-o.com](https://aut-o.com/)
- [venture-node.vercel.app](https://venture-node.vercel.app/)
- [foundrai.xyz](https://foundrai.xyz/)
- [github.com/rizkiwijanarko/KickUp](https://github.com/rizkiwijanarko/KickUp)
- [github.com/muhammadhaider02/LaunchMind](https://github.com/muhammadhaider02/LaunchMind)
- [github.com/mikitsik/venture_smith](https://github.com/mikitsik/venture_smith)

**Failed attempts:**

- [intelligenttools.co/blog/improved-phind-shutdown-post](https://intelligenttools.co/blog/improved-phind-shutdown-post)
- [chyshkala.com/blog/yupp-s-33m-death-spiral](https://chyshkala.com/blog/yupp-s-33m-death-spiral-when-agentic-ai-kills-your-feedback-loop)
- [getmanthan.com/charaka-notes/olive-ai-postmortem](https://getmanthan.com/charaka-notes/olive-ai-postmortem/)
- [getmanthan.com/charaka-notes/humane-ai-pin-postmortem](https://getmanthan.com/charaka-notes/humane-ai-pin-postmortem/)
- [gravity.fast/blog/vibe-ai-postmortem](https://gravity.fast/blog/vibe-ai-postmortem/)
- [ronakrm.github.io/coordinal-postmortem](https://ronakrm.github.io/coordinal-postmortem/)

**Academic:**

- [arxiv.org/html/2507.08350 â Multi-Agent LLM Dialogues (SIGDIAL 2025)](https://arxiv.org/html/2507.08350)
- [arxiv.org/html/2508.19200v2 â RamÃ³n Llull Machine](https://arxiv.org/html/2508.19200v2)
- [arxiv.org/html/2510.20844v3 â AutoResearcher](https://arxiv.org/html/2510.20844v3)
- [arxiv.org/html/2503.00946v2 â LLM-Assisted Ideation Review](https://arxiv.org/html/2503.00946v2)
- [arxiv.org/html/2607.01233v1 â Measuring the Gap](https://arxiv.org/html/2607.01233v1)
- [arxiv.org/abs/2601.12152v1 â Trade-offs in LLM-Supported Ideation](https://arxiv.org/abs/2601.12152v1)
- [dl.acm.org/doi/10.1145/3613904.3642414 â AI-Augmented Brainwriting](https://dl.acm.org/doi/10.1145/3613904.3642414)
- [aclanthology.org/.../2025.findings-emnlp.477 â Chain of Ideas](https://aclanthology.org/anthology-files/pdf/findings/2025.findings-emnlp.477.pdf)
- [link.springer.com/article/10.1007/s10994-026-07036-8 â SCI-IDEA](https://link.springer.com/article/10.1007/s10994-026-07036-8)

**Adjacent / historical:**

- [web.media.mit.edu/~lieber/Publications/Pygmalion-Remixed.pdf â Pygmalion (1975)](https://web.media.mit.edu/~lieber/Publications/Pygmalion-Remixed.pdf)
- [computerhistory.org/blog/harold-cohen-and-aaron-a-40-year-collaboration](https://computerhistory.org/blog/harold-cohen-and-aaron-a-40-year-collaboration/)
- [www.cambridge.org/core/journals/design-science/article/combinator â The Combinator](https://www.cambridge.org/core/journals/design-science/article/combinator-a-computerbased-tool-for-creative-idea-generation-based-on-a-simulation-approach/12C723397EB477F421699D02A025E724)



## Attestation coverage

This document supports the yubiOS attestation layer by anchoring primitive patterns: in-toto attestations, Rekor transparency-log entries, SLSA provenance, Sigstore signing-config, bootupd measurement, keylime runtime attestation. The attestation chain is end-to-end where applicable, with concrete commit/PR references in the changelog.



## Trust chain coverage

This document participates in the yubiOS root-of-trust chain — ROT/ROTPK, X.509 PKI, root-key custody, transitive verification across boot stages. Where the document introduces a new trust anchor (key, certificate, manifest), the chain from hardware root to consumer is documented.



## Least-privilege coverage

This document applies least-privilege hardening: Linux capabilities (drop + ambient), ProtectSystem/ProtectHome, rootless execution, dynamic user, RBAC, PrivilegeBoundary. Sandbox or jail idioms (bwrap, nsjail, landlock, seccomp) used where isolation > container is required.



## Continuous / adaptive coverage

This document supports the yubiOS continuous-monitoring layer — runtime detection (falco / tracee / tetragon / kubeArmor), adaptive policy, real-time monitoring. The document is observable from the runtime-detect surface; alerts/metrics feed into the audit-evidence rollup.



## Cryptographic identity coverage

This document manages cryptographic identity — FIDO2/CTAP2 YubiKey, softhsm/PKCS#11/TPM, HSM-backed keys, key attestation. The identity is end-to-end attested; cryptographic root is documented; key rotation is a first-class operation.


## Recommendation

**Verdict**: REVISE — context-dependent
**One-line**: TBD per file context.

Context: section appended per repo-refs-skill cycle-1 Mode D batch (Δ=+0.8429). TODO: refine per file context.


## Recommendation

**Verdict**: REVISE — context-dependent
**One-line**: TBD per file context.

Context: section appended per repo-refs-skill cycle-2 7-D Mode D batch (Δ=+0.4201). TODO: refine per file context.


## New Ideas -- cycle 3 (lens external)

This file's lens is **L324** in `lenses.json` (score 33/50, verdict **PARTIAL**, k=6/9). Full experiment: hypothesis `refs/prior-art-autonomous-ideation-skill-2026-07-28.md covers all 9 primitives in the internal-big-picture basis`, method `9-D primitive binarization (purpose, examples, guidelines, constraints, verifica...`. See root `new-ideas-2026-08-12.md` for the cycle-3 summary.
