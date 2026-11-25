# ADR 0015 — One core RR per Helm release

Status: **Owner-approved, 2026-11-26 JST.** The Owner approved separating RR
Helm management after agreeing that routing/container behavior is already
functional and should remain unchanged. Existing main-only development applies.
This task changes source and operating instructions; no live migration is run.

## Decision

- Add explicit `releaseMode: single`, supported for `topology: core` only.
  It accepts exactly one `routers` entry and owns one bare Pod, one ConfigMap,
  and one VLAN NAD. Resource names are the Helm release name (Pod/ConfigMap)
  and `<release>-net1` (NAD). The RR's FRR hostname remains `routers[].name`.
- Keep `releaseMode: pair` as the compatibility default: exactly two routers,
  existing names/counts and byte-identical renders for previous inputs. Both
  core pair and original direct-client pair deployments remain supported.
- Use one common values file for image/security/ASN/area/topology/release mode,
  plus a complete single-router array per RR in its individual file. Helm arrays
  replace rather than merge; individual files must not be layered together.
- Deploy two independent releases in the same operator-selected namespace using
  normal `helm install --create-namespace`; remove each with `helm uninstall`.
  Namespace deletion is a separate explicit command after both releases are
  removed. No Namespace, policy exception, hook, controller or CNI installer
  is added to the Chart. No container rebuild or registry publication is needed.
- Keep the existing FRR configuration source, required interfaces, loopback/
  Cluster ID derivation, NEXT_HOP policy, no-rib, OSPF max-metric, forwarding
  guard, image digest, capabilities and lifecycle model unchanged.

## Validation boundary

Local input/schema validation still applies to the selected RR. A standalone
release cannot know another release's loopback, Router ID, node/VLAN/subnet or
which external peer is another RR. These cross-release invariants are deployment
input responsibilities, not claims made by a single render. Validate the shipped
two profiles together with existing pair-mode checks: distinct identities,
workers/VLANs/subnets and reciprocal non-Client RR peers. Rendered FRR config and
Pod security/runtime specification must equal the paired deployment after only
resource names/references are accounted for. Explicitly test independent naming
and one-release-only changes. Reject absent/extra routers, mixed topology/mode
and existing invalid single-RR fields. Do not introduce cluster lookups.

## Updates and migration

Bare Pods and boot-snapshot configuration remain under ADR 0009. Common values
do not imply a synchronized update: operate one release at a time. A plain
ConfigMap/annotation update is not a running-config reload. For boot-config or
immutable Pod changes, stop/uninstall the selected RR, confirm sandbox/CNI
cleanup, then reinstall it with the saved or new values. Keep the other RR
operational; never use Helm force replacement or duplicate an RR identity.

The existing `rr` release owns names `rr-rr01` and `rr-rr02`. Migrate by stopping
only its first old Pod, confirming cleanup, and installing new `rr01` with new
names. Validate routing before repeating for `rr02`. Old ConfigMaps/NADs remain
inactive until uninstalling the old `rr` release after both new RRs are verified.
Do not upgrade/reconcile old `rr` during migration: it could recreate old Pods
alongside new identities. Keep old per-RR snapshots for selective rollback.
No ownership adoption or manual Helm-secret editing is necessary.

Static checks do not prove live Helm install/uninstall, migration/rollback,
packet behavior or high availability. Report all unexecuted checks NOT RUN.
