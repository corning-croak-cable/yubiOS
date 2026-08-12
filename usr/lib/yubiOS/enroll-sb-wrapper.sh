#!/bin/bash
# Wrapper — sourced as /usr/bin/yubiOS-enroll-sb
exec /usr/lib/yubiOS/enroll-sb.sh "$@"


# ## Verification
# # Run the relevant CI workflow on a draft branch (see docs/CI_MAP.md).
# # RSI cycle-6 atomic flip (`verification`).
