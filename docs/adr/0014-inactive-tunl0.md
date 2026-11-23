# ADR 0014 — Permit only an inactive, unaddressed tunl0 at startup

Status: **Owner-approved, 2026-11-24 JST.** The Owner approved the bounded
inventory change after the lab startup failure was reported. Existing main-only
development and public development-image workflow continue. No lab host, CNI,
Admission, capability or forwarding changes are part of this fix.

## Observation and decision

The lab Pod namespace contains the required lo/eth0/net1 plus tunl0. The observed
tunl0 is DOWN with no addresses. net1 is the correct VLAN with its declared /31,
and IPv4 forwarding reads 0. The previous exact inventory check rejects the
extra name before copying FRR daemon configuration; the EXIT cleanup then emits
a misleading missing-daemons error. The rejection is reproduced using the actual
Bash inventory function, independently of the lab.

Permit **only tunl0** in addition to the declared interface inventory, in both
one-link core and four-link direct-client modes, and only when all startup
readbacks succeed:

- Administrative UP flag is absent, and link state is DOWN.
- No IPv4 addresses and no IPv6 addresses are assigned to tunl0.
- No missing required interface or other extra interface is accepted.

Do not delete, activate, address or use tunl0. It is not an RR attachment, OSPF
interface, BGP source, transit path, or Helm input. This is a startup inventory
exception, not an ongoing tunnel-state monitor. The existing independent
forwarding=0 guard remains active throughout runtime. All routing identities,
required VLAN checks, daemon lifecycle and security boundaries remain unchanged.

## Validation and rollout

Exercise the actual Bash functions with both expected inventories, the extra
inactive tunl0, administrative/operational UP states, IPv4/IPv6 addresses,
failed or malformed readbacks, other extra names, and missing required names.
Where available, validate the gate in Linux with an isolated disposable netns;
distinguish this from native AMD64 daemon and Kubernetes acceptance.

Build a new AMD64/ARM64 image without overwriting the old public tag, pin the
new index in the lab values, and replace one stopped/failed RR incarnation at
a time only after its Pod termination and CNI cleanup are confirmed. Do not
use a blanket Helm force replacement. Preserve the old image/config snapshot
for diagnosis; it remains known to fail in namespaces containing tunl0.
