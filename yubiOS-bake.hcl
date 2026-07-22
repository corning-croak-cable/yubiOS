# yubiOS Docker Buildx Bake graph
#
# This file is the single source of truth for container-image build settings
# used by the non-ci_fork GitHub Actions workflows dispatched from ci.yml.
# GitHub Actions still owns runner selection, Docker/Buildx installation and
# active-builder selection, host/Podman/KVM tests, source commits, and
# imagetools assembly. Bake owns Dockerfiles, target dependencies, platforms,
# tags, outputs, labels, and Docker Build Policy enforcement.
#
# Docker primary references:
#   https://docs.docker.com/build/bake/reference/
#   https://docs.docker.com/build/bake/contexts/
#   https://docs.docker.com/build/policies/usage/
#   https://docs.docker.com/build/exporters/
#   https://docs.docker.com/reference/cli/docker/buildx/create/

variable "IMAGE" {
  type        = string
  default     = "docker.io/0mniteck/yubios"
  description = "Production Docker Hub repository."
}

variable "GIT_SHA" {
  type        = string
  default     = "local"
  description = "Source revision used by immutable tags and OCI labels."
}

variable "ARCH" {
  type        = string
  default     = "amd64"
  description = "Architecture suffix for native per-arch CI and publish tags."
}

variable "PLATFORM" {
  type        = string
  default     = "linux/amd64"
  description = "Single native platform built by the current runner."
}

variable "PUSH" {
  type        = bool
  default     = false
  description = "Use registry output and immutable publish tags when true."
}

variable "LOCAL_TAG" {
  type        = string
  default     = ""
  description = "Optional prefix for host-loaded local image and artifact tags."
}

variable "SOURCE_DATE_EPOCH" {
  type        = string
  default     = "0"
  description = "Canonical source commit timestamp propagated to supported builders."
}

variable "SOURCE_DATE_ISO8601" {
  type        = string
  default     = "1970-01-01T00:00:00Z"
  description = "RFC3339 form of SOURCE_DATE_EPOCH for OCI creation metadata."
}

variable "REPRO_DEST" {
  type        = string
  default     = "repro.oci"
  description = "Directory destination for the cache-isolated OCI reproduction target."
}

variable "FIRMWARE_CONTEXT" {
  type        = string
  default     = "fw"
  description = "Prepared context containing firmware/ for the scratch artifact."
}

variable "FIRMWARE_BOARD" {
  type        = string
  default     = "qemu-arm64"
  description = "Board identifier used by firmware tags and OCI metadata."
}

variable "FIRMWARE_BOARD_TITLE" {
  type        = string
  default     = "QEMU ARM64 CI baseline"
  description = "Human-readable board description for OCI metadata."
}

variable "FIRMWARE_PUBLISH_ORIGINAL" {
  type        = bool
  default     = false
  description = "Also publish the compatibility firmware and firmware-SHA tags."
}

variable "INSTALLER_CONTEXT" {
  type        = string
  default     = "inst"
  description = "Prepared context containing installer/ for the scratch artifact."
}

function "ref" {
  params = [tag]
  result = "${IMAGE}:${tag}"
}

# Buildx evaluates this explicit policy for every target that can resolve a
# source. cwd:// anchors the shared policy at the Bake invocation directory;
# otherwise filenames resolve inside target contexts such as fw/ or inst/.
# reset+filename preserves the existing CLI contract, while strict fails closed
# when the selected BuildKit daemon cannot evaluate policies.
target "_policy" {
  policy = [
    {
      filename = "cwd://yubiOS.rego"
      reset    = true
      strict   = true
    },
  ]
}

target "_source-metadata" {
  labels = {
    "org.opencontainers.image.created"  = SOURCE_DATE_ISO8601
    "org.opencontainers.image.source"   = "https://github.com/yubi-OS/yubiOS"
    "org.opencontainers.image.revision" = GIT_SHA
  }
}

# BuildKit's Dockerfile frontend consumes SOURCE_DATE_EPOCH and
# BUILDKIT_MULTI_PLATFORM. The former fixes image config/history timestamps;
# exporter rewrite-timestamp below also clamps layer-member mtimes. Export
# targets override multi-platform mode where their format requires it.
target "_reproducible" {
  args = {
    SOURCE_DATE_EPOCH       = SOURCE_DATE_EPOCH
    BUILDKIT_MULTI_PLATFORM = "1"
  }
}

# Exporter selection is shared by every externally visible image. The active
# builder is deliberately not modeled here: each containerized workflow job
# creates a user-scoped `hardened` builder and selects it explicitly on the
# Bake CLI, while this file continues to bind every image target to yubiOS.rego.
target "_image-export" {
  # Attestations are stored as additional manifests in an image index. Keep
  # provenance on registry exports, but disable it for Docker exports because
  # the local Docker image store accepts only a single image manifest.
  attest = [
    {
      type     = "provenance"
      disabled = !PUSH
    },
  ]
  # Even with one requested platform, BUILDKIT_MULTI_PLATFORM=1 returns a
  # manifest-list result that the Docker exporter cannot load. Registry output
  # supports that result and retains the deterministic multi-platform mode.
  args = {
    BUILDKIT_MULTI_PLATFORM = PUSH ? "1" : "0"
  }
  output = PUSH ? [
    {
      type                  = "registry"
      rewrite-timestamp     = true
      compression           = "gzip"
      compression-level     = 6
      force-compression     = true
      oci-mediatypes        = true
      compatibility-version = "20"
    },
  ] : [
    {
      type                  = "docker"
      rewrite-timestamp     = true
      compression           = "gzip"
      compression-level     = 6
      force-compression     = true
      compatibility-version = "20"
    },
  ]
}

target "_repro-export" {
  # OCI layouts support the deterministic manifest-list result used by the
  # isolated two-build comparison, even though those builds never push.
  args = {
    BUILDKIT_MULTI_PLATFORM = "1"
  }
  output = [
    {
      type                  = "oci"
      dest                  = REPRO_DEST
      tar                   = false
      rewrite-timestamp     = true
      compression           = "gzip"
      compression-level     = 6
      force-compression     = true
      oci-mediatypes        = true
      compatibility-version = "20"
    },
  ]
}

# Internal production image node. Keeping the unexported base separate means
# the dev target can consume it through target: context dependency without ever
# inheriting the production target's registry output or production tags.
target "_yubios-base" {
  inherits   = ["_policy", "_source-metadata", "_reproducible"]
  context    = "."
  dockerfile = "Containerfile"
  platforms  = [PLATFORM]
  pull       = true
}

target "yubios" {
  inherits = ["_yubios-base", "_image-export"]
  description = "Build the native production yubiOS bootc image."
  tags = PUSH ? [
    ref("${GIT_SHA}-${ARCH}"),
  ] : concat(
    ["yubios:ci-${ARCH}"],
    LOCAL_TAG != "" ? ["yubios:${LOCAL_TAG}"] : [],
  )
}

target "yubios-smoke" {
  inherits    = ["_policy", "_reproducible"]
  description = "Verify production scripts, symlinks, and PAM wiring in-build."
  context     = "."
  contexts = {
    yubios-base = "target:_yubios-base"
  }
  dockerfile-inline = <<-DOCKERFILE
    FROM yubios-base
    RUN test -x /usr/lib/yubiOS/enroll-sb-wrapper.sh && \
        test -L /usr/bin/yubiOS-enroll-sb && \
        test -L /usr/bin/yubiOS-enroll-luks && \
        test -L /usr/bin/yubiOS-enroll-pam && \
        test -L /usr/bin/yubiOS-enroll-ssh && \
        test -L /usr/bin/yubiOS-enroll-homed && \
        grep -q pam_u2f /etc/pam.d/sudo
  DOCKERFILE
  platforms = [PLATFORM]
  output    = [{ type = "cacheonly" }]
}

group "yubios-ci" {
  description = "Build and smoke-test the native production image."
  targets     = ["yubios", "yubios-smoke"]
}

target "yubios-repro" {
  inherits    = ["yubios", "_repro-export"]
  description = "Export production yubiOS as a canonical OCI layout for two-build comparison."
  tags        = []
}

target "yubios-dev" {
  inherits    = ["_policy", "_source-metadata", "_reproducible", "_image-export"]
  description = "Build the isolated swu2f development/test image."
  context     = "."
  contexts = {
    yubios-base = "target:_yubios-base"
  }
  dockerfile = "Containerfile.dev"
  platforms  = [PLATFORM]
  tags = PUSH ? [
    ref("dev-${GIT_SHA}-${ARCH}"),
  ] : concat(
    ["yubios:dev-${ARCH}"],
    LOCAL_TAG != "" ? ["yubios:${LOCAL_TAG}-dev"] : [],
  )
}

target "yubios-dev-smoke" {
  inherits    = ["_policy", "_reproducible"]
  description = "Fail if the TEST-only passless authenticator is absent."
  context     = "."
  contexts = {
    yubios-dev-base = "target:yubios-dev"
  }
  dockerfile-inline = <<-DOCKERFILE
    FROM yubios-dev-base
    RUN command -v passless && passless --version
  DOCKERFILE
  platforms = [PLATFORM]
  output    = [{ type = "cacheonly" }]
}

group "yubios-dev-ci" {
  description = "Build and smoke-test the isolated swu2f dev image."
  targets     = ["yubios-dev", "yubios-dev-smoke"]
}

target "yubios-dev-repro" {
  inherits    = ["yubios-dev", "_repro-export"]
  description = "Export TEST-only yubiOS dev as a canonical OCI layout for two-build comparison."
  tags        = []
}

target "firmware" {
  inherits    = ["_policy", "_source-metadata", "_reproducible", "_image-export"]
  description = "Package one prepared ARM64 board firmware payload as an OCI image."
  context     = FIRMWARE_CONTEXT
  dockerfile-inline = <<-DOCKERFILE
    FROM scratch
    COPY firmware/ /firmware/
  DOCKERFILE
  platforms = ["linux/arm64"]
  labels = {
    "org.opencontainers.image.title"       = "yubiOS ARM64 firmware bundle (${FIRMWARE_BOARD})"
    "org.opencontainers.image.description" = "Board-specific TF-A + OP-TEE StMM/fTPM + U-Boot firmware for ${FIRMWARE_BOARD_TITLE}"
    "io.yubios.firmware.board"              = FIRMWARE_BOARD
  }
  tags = PUSH ? concat(
    [
      ref("firmware-${FIRMWARE_BOARD}"),
      ref("firmware-${FIRMWARE_BOARD}-${GIT_SHA}"),
    ],
    FIRMWARE_PUBLISH_ORIGINAL ? [
      ref("firmware"),
      ref("firmware-${GIT_SHA}"),
    ] : [],
  ) : concat(
    ["yubios:firmware-${FIRMWARE_BOARD}"],
    LOCAL_TAG != "" ? [
      "yubios:${LOCAL_TAG}-firmware-${FIRMWARE_BOARD}",
    ] : [],
  )
}

target "installer" {
  inherits    = ["_policy", "_source-metadata", "_reproducible", "_image-export"]
  description = "Package the prepared mkosi disk/UKI installer payload as an OCI image."
  context     = INSTALLER_CONTEXT
  dockerfile-inline = <<-DOCKERFILE
    FROM scratch
    COPY installer/ /installer/
  DOCKERFILE
  platforms = [PLATFORM]
  labels = {
    "org.opencontainers.image.title"       = "yubiOS mkosi installer image"
    "org.opencontainers.image.description" = "DPS disk image + PKCS#11-signed UKI (minimal profile); installs the base system that runs the bootc images"
  }
  tags = PUSH ? [
    ref("installer-${GIT_SHA}-${ARCH}"),
  ] : concat(
    ["yubios:installer-${ARCH}"],
    LOCAL_TAG != "" ? ["yubios:${LOCAL_TAG}-installer"] : [],
  )
}

# A live network verification must never be satisfied by an old RUN cache.
target "pq-tls-verify" {
  inherits    = ["_policy", "_reproducible"]
  description = "Verify the OpenSSL 3.5+ PQ hybrid TLS default against the live endpoint."
  context     = "."
  dockerfile-inline = <<-DOCKERFILE
    FROM dhi.io/debian-base@sha256:5c45913e72c90581fc4cca57c3a7cd7dcac2d9fa44fce24fe4cfa342e5ccb7a6
    SHELL ["/bin/bash", "-c"]
    RUN <<'VERIFY'
    set -euo pipefail
    apt-get update -qq
    apt-get install -y -qq curl
    v=$(openssl version | awk '{print $2}')
    echo "openssl version: $v"
    major=$(printf '%s' "$v" | cut -d. -f1)
    minor=$(printf '%s' "$v" | cut -d. -f2)
    if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 5 ]; }; then
      echo "OpenSSL $v is below the 3.5 PQ hybrid floor" >&2
      exit 1
    fi
    group=$(curl -sv https://omniteck.com/ 2>&1 | grep -o 'SSL connection using[^\"]*' || true)
    echo "negotiated: $group"
    case "$group" in
      *MLKEM*) echo "PQ hybrid group confirmed against omniteck.com" ;;
      *) echo "No MLKEM group negotiated against the live TLS endpoint" >&2; exit 1 ;;
    esac
    if command -v go >/dev/null 2>&1; then
      go_version=$(go version | awk '{print $3}' | sed 's/^go//')
      echo "go version: $go_version"
      go_major=$(printf '%s' "$go_version" | cut -d. -f1)
      go_minor=$(printf '%s' "$go_version" | cut -d. -f2)
      if [ "$go_major" -lt 1 ] || { [ "$go_major" -eq 1 ] && [ "$go_minor" -lt 24 ]; }; then
        echo "Go $go_version is below the 1.24 PQ hybrid floor" >&2
        exit 1
      fi
    else
      echo "Go is not installed; reporting the distro candidate for drift visibility."
      apt-cache policy golang-go || true
    fi
    VERIFY
  DOCKERFILE
  no-cache = true
  output   = [{ type = "cacheonly" }]
}
