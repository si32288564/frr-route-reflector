# ADR 0013 — Core OSPF attachment and independent iBGP neighbors

Status: **Owner-approved, 2026-11-24 JST.** The Owner clarified the target in
chat: two RRs, one /31 P2P link from each RR to core, OSPF advertisement of each
RR loopback, and multiple loopback-addressed iBGP neighbors reached through core.
The diagram includes a normal RR-to-RR iBGP session. The Owner requested a
configurable neighbor list and directed main-only updates without PRs. Record
the design before implementation; this authorizes source updates, not deployment,
network changes or public image publication.

## Bounded extension

Add explicit `topology: core` while retaining `topology: direct-clients` as the
default existing four-Client/two-Worker topology. No implicit detection from list
length and no generic routing framework. The old requirements' direct RR-to-Client
VLAN cardinality and no-RR-peer rule remain specific to the default topology.

Core topology:

- Exactly two independent RR Pods/ConfigMaps and two VLAN NADs; each RR has one
  `net1` static /31 attachment to core. No VLAN/interface per BGP neighbor.
- OSPFv2 P2P on `net1` only; advertise the RR loopback /32 passively. Core and
  external routers must provide return/remote-loopback reachability. They and the
  actual data-plane fabric remain outside this Chart's lifecycle authority.
- Common iBGP ASN/OSPF area, distinct RR Router IDs/loopbacks; Cluster ID remains
  derived from each RR loopback under ADR 0012. Do not rewrite NEXT_HOP, redistribute
  service prefixes into OSPF or enable RR transit. Preserve `bgp no-rib`, permanent
  administrative max-metric, forwarding=0 guard and existing security profile.
- Default `placement: distinct-workers`. Explicit `placement: single-worker` is
  allowed only with core topology for the Owner-selected home development setup;
  both selectors must then identify the same Worker. No Worker-HA claim.

## Canonical input / validation contract

Keep one Helm values SSOT. In core mode `clients` must be empty: the only BGP
source is each RR's `neighbors` list, independent from its single `links` entry.
Do not accept duplicate or conflicting sources, raw FRR text, per-peer eBGP ASN,
IPv6, next-hop policy overrides or arbitrary interface counts.

- Each core `links` list has one `net1` entry: VLAN ID, local /31 and opposite
  core endpoint `remoteAddress`. No `client` reference. Retain VLAN/subnet
  uniqueness and no loopback/peer endpoint overlap with /31 link subnets.
- Each `neighbors` list has one or more objects with exactly `address` (IPv4
  loopback address, no mask) and `routeReflectorClient` (explicit boolean). At
  least one entry is an RR Client; no arbitrary maximum or four-peer assumption.
- Generate remote-as from common ASN, update-source from the local RR loopback,
  IPv4 activation for every entry, and `route-reflector-client` **only** for true.
- Reject duplicate addresses within an RR, self-peering, invalid/non-unicast
  addresses and /31 endpoint addresses. The other RR's loopback may be explicitly
  listed only with `routeReflectorClient: false`; never infer or auto-add that
  neighbor and never mark it as a Client. Configuring one side does not configure
  the other. No new RR-to-RR VLAN, synchronization or forwarding is introduced.
- Default direct-client mode keeps its four global Clients/four links per RR,
  distinct Worker placement and no independent `neighbors` list. Old valid values
  remain valid. Both modes reject shared/manual Cluster ID inputs.

## Acceptance / migration

Check one/two/several Client peers plus optional non-Client RR peer, deterministic
2/2/2 rendering, role-correct FRR lines, one OSPF interface, and independent VLAN
and peer counts. Reject mixed/unknown fields, duplicate/self/RR-as-Client peers,
invalid /31 relations, identity/placement collisions and unwanted interfaces.
Regression-test the default 2/2/8 fixture with byte-identical output to the previous
main. Runtime requires exactly the declared interfaces (one or four), no phantom
interfaces; standard daemon/config lifecycle and forwarding guard are unchanged.

Apply the mapping to a new or deliberately migrated values snapshot; do not
silently shorten old live attachments. Save the old Chart/image/values and use
the controlled bare-Pod replacement/cleanup procedure. The new single-interface
mode requires an updated entrypoint image; old four-interface images cannot boot
it. No live CNI/Admission/NIC or Pod migration is authorized by this source change.

Actual OSPF Full, BGP Established, reflection/attributes, FIB non-installation,
negative packet transit, failure/recovery remain separate measured acceptance.
A single RR Client is not proof of reflection to another Client. Keep unexecuted
runtime/packet tests NOT RUN; do not equate render or image build with G-3 PASS.
