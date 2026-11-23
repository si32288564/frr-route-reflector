# ADR 0012 — Derive each RR Cluster ID from its own loopback

Status: **Owner-approved on 2026-11-24 JST; recorded on main before the
implementation commit.** The Owner requested per-RR loopback-derived Cluster IDs
and explicitly directed main-only updates without PRs for this work. This is an
explicit workflow exception to the usual PR process, not permission to publish
an image or change a running environment. Approval is not a successful runtime
test or deployment.

## Decision and authority

Replace the shared-ID part of ADR 0001. Requirements R-032 and Architecture I-02
define the policy; the Implementation Contract defines the input projection and
Acceptance Criteria A-001 defines evidence. Other routing/topology/security and
lifecycle obligations are unchanged, including no RR-to-RR BGP peer.

Each logical RR uses the IPv4 address of its own configured loopback /32 as its
explicit FRR `bgp cluster-id`, removing the suffix. Router ID remains a separate
input; do not use it as a fallback or assume it always equals the loopback.
Distinct valid RR loopbacks therefore produce distinct Cluster IDs.

Documentation-only example:

| RR | Loopback source | Derived Cluster ID |
|---|---|---|
| RR-01 | 192.0.2.1/32 | 192.0.2.1 |
| RR-02 | 192.0.2.2/32 | 192.0.2.2 |

## Rationale and limits

The Owner selected per-RR loopback-based identities for the intended deployment.
Derivation avoids a redundant input that can disagree with its source. This is
not a statement that shared IDs are invalid BGP: [RFC 4456 section 7](https://www.rfc-editor.org/rfc/rfc4456.html#section-7)
describes common IDs for redundant RRs in one cluster; section 8 describes local
Cluster ID use in CLUSTER_LIST loop prevention. Distinct IDs change that identity
policy and require routing/attribute evidence, not merely two established peers.
They do not add RR peering, synchronization, NEXT_HOP rewriting or IP transit.

The default four-Client design and any separately accepted development topology
must use the same per-RR derivation. This ADR does not merge the closed Home PR
or expand topology scope. One Client cannot prove reflection between Clients.

## Implementation handoff after acceptance

1. Remove `cluster.clusterId` from schema and maintained example/private values;
   retain strict unknown-field rejection. Per-RR `clusterId` is not an alternative
   input. Explicitly reject obsolete shared-ID input; do not silently ignore it.
2. Generate each RR's `bgp cluster-id` from its own loopback, without `/32`.
   Existing distinct-loopback validation remains required. No new runtime
   configuration scheme, environment variable, capability or supervisor is needed.
3. Add the derivation, Router-ID-different-from-loopback, old-input rejection,
   uniqueness and one-RR-change isolation tests in A-001. Update relevant fixtures
   without editing historical evidence. Run lint/template and FRR checks as
   available; mark absent live reflection/attribute/packet evidence NOT RUN.
4. Record code/test results in a subsequent implementation commit on main under
   the Owner's explicit main-only instruction. This design commit leaves Chart, container, examples and tests as
   the accepted shared-ID implementation; it is not a working-code migration.

## Migration and operations

Removing the legacy input is a breaking values-schema change. Existing users
must migrate deliberately; no compatibility option or silent default retains
the old shared value. Generated FRR boot bytes/checksums will change.

For any running release, save the previous values/render/config/image snapshot.
Use the existing reviewed one-RR-at-a-time bare-Pod replacement/cleanup procedure,
after confirming the surviving RR; do not assume a ConfigMap edit or `helm
upgrade` live-reloads FRR. Changing a loopback later also changes its Cluster ID
and remains a reviewed identity change. Verify attributes/routes after change;
do not claim convergence or rolling recovery without measured evidence.
Rollback uses the previous compatible Chart/schema, values and boot snapshot,
with the same controlled replacement. Never feed old shared-ID values to the
new schema and assume rollback. The Owner authorized the direct main source
update, not any live migration.

## Validation status

The initial design commit was documentation only. The subsequent implementation
removes the legacy schema input and derives Cluster ID in the Helm renderer.
[Static execution evidence](../evidence/cluster-id-loopback-static-20261124.txt)
records lint/template, derivation, Router ID independence, per-RR isolation and
40 rejected input cases. FRR CLI configuration/runtime, live BGP attributes,
Kubernetes and migration/rollback tests for this policy are **NOT RUN**.
