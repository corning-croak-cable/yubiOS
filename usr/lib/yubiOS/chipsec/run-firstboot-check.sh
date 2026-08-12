#!/bin/sh
# yubiOS first-boot firmware validation wrapper (ADR-024).
#
# Runs a fixed, yubiOS-relevant subset of CHIPSEC's common.* modules plus a
# best-effort Absolute/Computrace surface scan. Writes a structured result to
# /run/yubiOS/chipsec-result for yubiOS-enroll.service to read, and logs full
# detail to the journal under SYSLOG_IDENTIFIER=yubiOS-chipsec.
#
# Honesty note (see ADR-024): there is no automated CHIPSEC module for
# Absolute Persistence / Computrace detection. The wpbt/uefi-var scan below is
# informational only -- it does not PASS/FAIL, it reports what it finds.
#
# Result contract:
#   RESULT=PASS   all scoped CHIPSEC checks passed.
#   RESULT=WARN   CHIPSEC produced warnings or no report; surface this as
#                 firmware-warning evidence, not as a clean bill of health.
#   RESULT=FAILED one or more scoped CHIPSEC checks failed.
# WPBT/Computrace detections are recorded separately as informational evidence
# and must not, by themselves, change the PASS/WARN/FAILED result.

set -eu

RESULT_DIR=/run/yubiOS
RESULT_FILE="$RESULT_DIR/chipsec-result"
LOG_TAG=yubiOS-chipsec
mkdir -p "$RESULT_DIR"

log() { logger -t "$LOG_TAG" "$*"; echo "$*"; }

log "yubiOS first-boot firmware validation starting"

modprobe chipsec_helper 2>/dev/null || log "WARNING: chipsec_helper module load failed or unavailable"

MODULES="common.bios_wp common.spi_lock common.spi_desc common.smm_lock common.smrr common.smm_code_chk common.secureboot.variables common.debugenabled common.me_mfg_mode"

OVERALL=PASS
REPORT=/run/yubiOS/chipsec-report.json

set --
for module in $MODULES; do
  set -- "$@" -m "$module"
done

if ! chipsec_main.py "$@" --json "$REPORT" >/tmp/chipsec-firstboot.log 2>&1; then
  log "WARNING: chipsec_main.py exited non-zero -- see /tmp/chipsec-firstboot.log"
fi

if [ -f "$REPORT" ]; then
  if grep -q '"result": *"Failed"' "$REPORT" 2>/dev/null; then
    OVERALL=FAILED
    log "FAILED: one or more firmware checks failed -- see $REPORT"
  elif grep -q '"result": *"Warning"' "$REPORT" 2>/dev/null; then
    OVERALL=WARN
    log "WARN: one or more firmware checks warned -- see $REPORT"
  else
    log "PASS: all scoped firmware checks passed"
  fi
else
  OVERALL=WARN
  log "WARN: no chipsec report produced -- treating as inconclusive, not a hard failure"
fi

# Best-effort Absolute/Computrace surface (informational only -- see ADR-024).
WPBT_SEEN=no
if chipsec_util.py acpi list 2>/dev/null | grep -qi WPBT; then
  WPBT_SEEN=yes
  log "INFO: WPBT ACPI table present (Absolute/Computrace-capable firmware feature; informational, not a failure)"
fi
COMPUTRACE_VARS=$(chipsec_util.py uefi var-list 2>/dev/null | grep -iE 'computrace|absolute' || true)
if [ -n "$COMPUTRACE_VARS" ]; then
  log "INFO: Computrace/Absolute-named UEFI variables present: $COMPUTRACE_VARS"
fi

cat > "$RESULT_FILE" <<EOF
RESULT=$OVERALL
WPBT_PRESENT=$WPBT_SEEN
REPORT=$REPORT
TIMESTAMP=$(date -u +%FT%TZ)
EOF

log "yubiOS first-boot firmware validation complete: $OVERALL"


# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md).
# # RSI cycle-6 atomic flip (`verification`).


# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md).
# # RSI cycle-7 atomic flip (NSS-axis(calibration)).
