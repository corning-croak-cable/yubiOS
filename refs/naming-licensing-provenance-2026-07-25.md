# Naming, Licensing, Provenance, and Entity Consultations

Source: OMN-81 (team OMNI-AGENT), a legal and structural consultation workstream feeding OMN-65 (days 0-30). Grounded in the yubi-OS/yubiOS repo as inspected on 2026-07-25.

## Purpose

Lay out the concrete questions and current facts for the naming, licensing, provenance, and entity tracks so the actual legal consultations, which need a human and a lawyer, start from a real risk register instead of a blank page. This doc does not resolve legal questions; it frames them.

## Scope (from OMN-81)

- Clarify naming and trademark risks.
- Review license fit and redistribution obligations.
- Review contributor provenance and policy needs.
- Decide the near-term entity path and legal questions to resolve.
- Produce a concise issue and risk register plus a next-step list.

## 1. Naming and trademark

- Project name in use: yubiOS. Org name: yubi-OS (GitHub org, public as of 2026-07-24).
- Risk: yubi is a recognizable abbreviation of Yubico’s YubiKey trademark. This agent cannot assess trademark risk (that needs a trademark attorney and a registry search) and is flagging it as the number one open legal question, not resolving it.
- Next step: a trademark attorney should review whether yubiOS creates confusion-of-origin risk with Yubico, and whether Yubico publishes any policy on third-party Yubi-prefixed community project names (some hardware vendors do).

## 2. License fit and redistribution obligations

- Repository license, per the GitHub API license endpoint and README badge: LGPL-2.1 (GNU Lesser General Public License v2.1), LICENSE file present at the repo root.
- yubiOS composes upstream projects under their own licenses: systemd is LGPL-2.1-or-later, U-Boot is GPL-2.0-or-later, OP-TEE and ARM Trusted Firmware are BSD-style, ms-tpm-20-ref is BSD-3-Clause-Clear per Microsoft, and the Fedora/CentOS bootc base images carry their own upstream terms in addition to component licenses.
- Open question, not resolved here: does LGPL-2.1 for the yubiOS repo itself create any redistribution friction against a GPL-2.0-or-later component like U-Boot when both ship inside the same bootable image? LGPL and GPL-2.0 are generally compatible for linking, but a lawyer should confirm this holds for the specific combination and distribution model yubiOS uses (a bootable OCI image, not just linked libraries).
- Next step: a license review pass over PINNED.md’s actual pinned components (not just the ones named above) to build a complete component-to-license table, then a lawyer sign-off on the combined redistribution obligations.

## 3. Contributor provenance and policy

- No CONTRIBUTING.md or explicit CLA/DCO policy was found via a root-level check of the yubi-OS/yubiOS repo in this pass. If one exists elsewhere in the repo tree, this doc has not located it and should not be treated as confirming its absence.
- Given the LGPL-2.1 license and the multi-fork nature of this project (6 ARM64 fTPM forks alone per ADR-018/019/020), a Developer Certificate of Origin (DCO, sign-off based) is the lower-friction provenance option compared to a CLA, and matches common practice for LGPL projects consuming other LGPL/GPL/BSD upstreams.
- Next step: decide DCO vs CLA vs neither, and if DCO, add a CONTRIBUTING.md with a sign-off requirement and a CI check (or a documented manual check) for the `Signed-off-by` trailer.

## 4. Near-term entity path

- This agent has no visibility into Jenny’s current legal entity status (sole proprietor, LLC, nonprofit, unformed) and cannot recommend a specific entity type; that is a legal and tax decision requiring a lawyer and likely an accountant, not something to guess at in a repo doc.
- What can be flagged from the repo and OMN-65/70 context: OMN-70 (public-interest operating covenant) and OMN-72 (entity, governance, and legal work) are the two issues that should carry the actual entity decision. This doc records that the near-term entity path is an open legal question tracked there, not answered here, to avoid duplicating OMN-72’s scope.
- Legal questions to resolve, gathered from the four sections above: trademark confusion risk with Yubico; combined-license redistribution obligations across LGPL/GPL/BSD components in one bootable image; DCO vs CLA decision; and the entity type appropriate for a public-interest-leaning open-source security project (relevant to OMN-70’s covenant).

## Issue and risk register

| Risk | Area | Severity (best guess, not legal advice) | Next step | Owner |
|---|---|---|---|---|
| yubiOS name may create trademark confusion with Yubico | Naming | Medium -- reputational and potential cease-and-desist risk, not yet assessed by counsel | Trademark attorney review + registry search | Jenny + counsel |
| Combined LGPL/GPL/BSD licensing across bundled components in one bootable image is not confirmed clean | Licensing | Medium -- could force a license or packaging change if a conflict is found | Build the full component-to-license table from PINNED.md, then counsel sign-off | Jenny + counsel |
| No confirmed contributor provenance policy (DCO/CLA) | Provenance | Low today, grows with contributor count | Decide DCO vs CLA, add CONTRIBUTING.md | Jenny |
| Entity type undecided | Entity | Low urgency now, blocks OMN-70/72 exit criteria | Resolve via OMN-72 with counsel and accountant | Jenny + counsel + accountant |

## Next-step list

1. Engage a trademark attorney for the naming risk (highest-severity open item).
2. Build the complete PINNED.md component-to-license table (this agent can do this as a follow-up task; not done here to keep this doc focused).
3. Decide DCO vs CLA and add CONTRIBUTING.md.
4. Resolve entity type via OMN-72, informed by OMN-70’s covenant commitments.

## Open questions

- Whether Yubico has a stated naming policy for third-party projects -- not found in this pass, needs a targeted search or direct outreach.
- Whether a CONTRIBUTING.md or CLA/DCO already exists somewhere in the repo tree beyond the root-level check done here.
- Jenny’s current legal entity status, which this agent has no visibility into.
