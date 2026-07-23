> **Archived research snapshot** synced from the assistant knowledge base (`documents/github-yubios-KS9n5GAT/knowledge/`) on 2026-07-23. May predate current specs — treat `PINNED.md` and the dated `refs/*` notes as the live source of truth; this is background research context only.

---

# systemd Reference: exec/unit/service/directives
_Refreshed: June 23, 2026 — Sources: man7.org systemd v260_

## Man Page Map

| What you need | Man page |
|---|---|
| Common unit options ([Unit], [Install]) | `systemd.unit(5)` |
| Service-specific ([Service]) | `systemd.service(5)` |
| Execution environment (ExecStart=, sandbox, caps) | `systemd.exec(5)` |
| Resource limits (CPU, memory, cgroups) | `systemd.resource-control(5)` |
| Kill behavior | `systemd.kill(5)` |
| Full directive index | `systemd.directives(7)` |

---

## Service Types (Type=)

| Type | Behavior |
|---|---|
| `simple` | Default. Started immediately after fork. Main process = ExecStart= process. |
| `exec` | Like simple but waits for execve() to succeed. Preferred for most long-running services. |
| `forking` | Daemon forks; parent exits. Use `PIDFile=` to track. Discouraged; use notify instead. |
| `oneshot` | Short-lived. Multiple `ExecStart=` run serially. Use `RemainAfterExit=yes` to stay active. |
| `notify` | Waits for `sd_notify("READY=1")` before considering started. Preferred for daemons. |
| `notify-reload` | Like notify; reload sends RELOADING=1 then READY=1. Replaces ExecReload= signal pattern. |
| `idle` | Delays ExecStart= ~5s until other jobs quiet. Avoids stdout mixing. |
| `dbus` | Waits for `BusName=` to appear on D-Bus. |

---

## Execution Commands

| Directive | Section | Notes |
|---|---|---|
| `ExecStart=` | [Service] | Main command. Multiple lines for oneshot only. Prefix `-` ignores failure. |
| `ExecStartPre=` | [Service] | Runs before ExecStart=. Serial. Fail stops start (unless `-` prefixed). Not for long-running processes. |
| `ExecStartPost=` | [Service] | Runs after ExecStart=. `$MAINPID` available. |
| `ExecCondition=` | [Service] | Before ExecStartPre=. Exit 1-254 = skip rest (not fail). Exit 255 or abnormal = fail. |
| `ExecStop=` | [Service] | Runs on stop. Only if start succeeded. KillMode= applies after. |
| `ExecStopPost=` | [Service] | Always runs on stop (even on failure). |
| `ExecReload=` | [Service] | Handles `systemctl reload`. Prefer `Type=notify-reload` instead. |
| `ExecReloadPost=` | [Service] | v259+. Runs after successful reload. |

---

## Dependencies and Ordering ([Unit])

| Directive | Meaning |
|---|---|
| `Requires=` | Hard dep. Failure fails this unit. |
| `Wants=` | Soft dep. Failure doesn't fail this unit. |
| `BindsTo=` | Strongest binding. Stop/failure propagates both ways. |
| `PartOf=` | Weak coupling. Stop/restart together; no failure propagation. |
| `After=` | Ordering only (no dep). Start after listed units. |
| `Before=` | Ordering only. Start before listed units. |
| `WantedBy=` | [Install] — symlink target for `systemctl enable`. Usually `multi-user.target`. |
| `RequiredBy=` | [Install] — reverse of Requires=. |
| `Upholds=` | Like Wants= but continuously re-activates if target stops. v250+. |

---

## Security and Sandboxing (systemd.exec(5))

| Directive | Effect |
|---|---|
| `DynamicUser=yes` | Transient UID (no /etc/passwd). Implies StateDirectory=, RuntimeDirectory=. |
| `PrivateTmp=yes` | tmpfs on /tmp and /var/tmp for this service. |
| `PrivateTmp=disconnected` | v255+. Disconnected tmpfs (no shared /tmp). |
| `ProtectSystem=strict` | /usr, /boot, /efi read-only. Use `ReadWritePaths=` for exceptions. |
| `ProtectSystem=full` | + /etc read-only. |
| `ProtectHome=yes` | /home, /root, /run/user hidden or tmpfs. |
| `NoNewPrivileges=yes` | No privilege escalation (setuid, setresuid, caps drop). |
| `SystemCallFilter=` | seccomp BPF. Use `~@clock` to blacklist groups. Failure kills process. |
| `CapabilityBoundingSet=` | Mask capabilities (e.g., `~CAP_SYS_ADMIN` to remove, or `CAP_NET_BIND_SERVICE` to allow only). |
| `AmbientCapabilities=` | Grant caps to main process (e.g., `CAP_NET_BIND_SERVICE`). |
| `ReadOnlyPaths=` | Bind-mount paths as read-only. |
| `ReadWritePaths=` | Bind-mount paths as read-write (use with ProtectSystem=strict). |
| `StateDirectory=` | Creates `/var/lib/<name>/` owned by service. |
| `RuntimeDirectory=` | Creates `/run/<name>/`; cleaned on stop. |
| `CacheDirectory=` | Creates `/var/cache/<name>/`. |
| `LogsDirectory=` | Creates `/var/log/<name>/`. |
| `ConfigurationDirectory=` | Creates `/etc/<name>/`. |
| `NotifyAccess=` | Who can call sd_notify: `none` / `mainpid` / `all`. |
| `ProtectKernelModules=yes` | Deny CAP_SYS_MODULE. |
| `ProtectKernelTunables=yes` | /proc/sys, /sys read-only. |
| `ProtectControlGroups=yes` | /sys/fs/cgroup read-only. |
| `LockPersonality=yes` | Prevent ABI personality change. |
| `RestrictRealtime=yes` | Deny real-time scheduling. |
| `RestrictNamespaces=yes` | Deny namespace creation (or restrict by type). |
| `RestrictAddressFamilies=` | Allowlist socket families (e.g., `AF_UNIX AF_INET AF_INET6`). |
| `MemoryDenyWriteExecute=yes` | Deny W+X memory mappings. |
| `PrivateDevices=yes` | Minimal /dev (no physical devices). |
| `PrivateNetwork=yes` | Private network namespace (loopback only). |
| `PrivateUsers=yes` | User namespace. `PrivateUsers=full` (v258) = complete isolation. `PrivateUsers=managed` (v260) = automatic UID management. |
| `ProtectProc=invisible` | Hide other users' /proc/<pid> entries. |
| `ProcSubset=pid` | Only show process-related /proc entries. |
| `RootImage=` | Run service from disk image (DDI). Verity-protected. |
| `RootMStack=` | v260+. overlayfs-based mount stack for root filesystem. |
| `RootEphemeral=yes` | v254+. Ephemeral copy of RootDirectory= per service invocation. |
| `BindNetworkInterface=` | v260+. Restrict service to specific network interface. |
| `RefreshOnReload=yes` | v260+. Re-read credentials when service is reloaded. |

**Hardened baseline combo (yubiOS services):**
```ini
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
DynamicUser=yes
NoNewPrivileges=yes
SystemCallFilter=~@mount @reboot @debug
CapabilityBoundingSet=
ProtectKernelModules=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes
LockPersonality=yes
RestrictRealtime=yes
MemoryDenyWriteExecute=yes
RestrictAddressFamilies=AF_UNIX AF_NETLINK
```

---

## Resource Control (systemd.resource-control(5), cgroups v2)

| Directive | Notes |
|---|---|
| `MemoryMax=` | Hard limit. OOM kill if exceeded. |
| `MemoryHigh=` | Soft limit. Throttle + reclaim. |
| `CPUQuota=` | Percentage of CPU (e.g., `50%`). |
| `CPUWeight=` | Relative CPU weight (default 100). |
| `IOWeight=` | Relative IO weight. |
| `TasksMax=` | Max pids in cgroup. |

---

## Restart / Watchdog

| Directive | Values / Notes |
|---|---|
| `Restart=` | `no` / `on-success` / `on-failure` / `on-abnormal` / `on-watchdog` / `on-abort` / `always` |
| `RestartSec=` | Delay before restart (default 100ms). |
| `RestartSteps=` | v255+. Exponential backoff step count. |
| `RestartMaxDelaySec=` | v255+. Cap for exponential backoff. |
| `WatchdogSec=` | Heartbeat interval. Process must call `sd_notify("WATCHDOG=1")`. |

---

## Unit File Specifiers (common)

| Specifier | Expands to |
|---|---|
| `%n` | Unit name |
| `%p` | Unit name prefix (before @) |
| `%i` | Instance name (after @) |
| `%H` | Hostname |
| `%v` | Kernel release |
| `%u` | User name |
| `%h` | Home directory |
| `%t` | Runtime directory ($XDG_RUNTIME_DIR or /run) |

---

## Drop-In Pattern

```
/etc/systemd/system/myservice.service.d/
    10-override.conf    # loaded after main unit
    20-hardening.conf
```

For type-wide drops: `/etc/systemd/system/service.d/99-sandbox.conf` applies to ALL `.service` units.

---

## systemd.unit(5) Key Sections

### [Unit]
- `Description=` — human-readable name
- `Documentation=` — man pages, URLs
- `After=`, `Before=`, `Requires=`, `Wants=`, `BindsTo=`, `PartOf=`, `Upholds=`
- `ConditionPathExists=`, `ConditionFileIsExecutable=`, `AssertPathExists=`
- `DefaultDependencies=no` — opt out of automatic sysinit/shutdown deps

### [Install]
- `WantedBy=`, `RequiredBy=` — `systemctl enable` symlink targets
- `Alias=` — alternative unit name symlinks
- `Also=` — additional units to enable/disable together

### Unit File Search Path (system mode, precedence order)
1. `/etc/systemd/system.control/` (API-managed)
2. `/run/systemd/system.control/` (API-managed)
3. `/etc/systemd/system/` (admin)
4. `/run/systemd/system/` (runtime)
5. `/usr/local/lib/systemd/system/` (local admin)
6. `/usr/lib/systemd/system/` (packages)

---

## Credentials (systemd v254+)

```ini
[Service]
LoadCredential=fido2-token:/etc/yubikey/slot-config
LoadCredentialEncrypted=api-key:/etc/credentials/api.cred
SetCredential=mode:production
```

Access via `$CREDENTIALS_DIRECTORY/fido2-token`.

---

## yubiOS-specific Patterns

### YubiKey auth service unit
```ini
[Unit]
Description=YubiKey FIDO2 Enrollment Service
After=systemd-udevd.service
Requires=systemd-udevd.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/lib/yubiOS/enroll-fido2.sh
DynamicUser=no
User=root
PrivateDevices=no
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
NoNewPrivileges=yes
CapabilityBoundingSet=CAP_SYS_ADMIN CAP_DAC_READ_SEARCH
ReadWritePaths=/etc/crypttab /var/lib/systemd/

[Install]
WantedBy=multi-user.target
```

### systemd-homed drop-in (FIDO2 enrollment)
```ini
# /etc/systemd/system/systemd-homed.service.d/99-yubikey.conf
[Service]
PrivateDevices=no
BindReadOnlyPaths=/dev/hidraw0 /dev/hidraw1 /dev/hidraw2
```
