# Task 0001 implementation binding

> Cluster ID generation was updated under the Owner-approved
> [ADR 0012](adr/0012-cluster-id-from-rr-loopback.md). Historical Task 0001 runtime
> evidence used the former shared-ID policy and does not qualify live behavior
> for the new policy.

Accepted sources: Implementation Contract, ADR 0010/0011 and PR #6 review
5526023836. Helm values own all routing identities and mappings. Default values
are deliberately incomplete; the one positive security profile must be selected.
Unknown fields are rejected, including arbitrary FRR text and forwarding policy.
Under [ADR 0015](adr/0015-independent-helm-releases.md), core inputs may explicitly
select `releaseMode: single` for one RR per Helm release. Paired inputs remain
the compatibility default. Common+individual values merge to one validated input;
the independent release changes resource names/ownership, not FRR boot bytes or
the runtime specification. Cross-release invariants are deployment input
responsibilities and are checked together for the supplied profiles.
The default topology uses the fixed global Client list. The explicit `core`
option accepts only structured per-RR `neighbors` under
[ADR 0013](adr/0013-core-ospf-independent-ibgp-neighbors.md), independently of
its one OSPF VLAN attachment. Example values are documentation-only, not an
approved deployment plan.

## Runtime

The image uses digest-pinned Alpine 3.24, official frr=10.6.1-r0 and
tini=0.19.0-r3 packages. No development packages, FRR patches or independent
supervisor. Required daemons are mgmtd/zebra/bgpd/ospfd; distro binaries for other
roles remain installed but disabled. Standard watchfrr runs in foreground,
standard watchfrr.sh/frrcommon.sh manage daemon launch/restart/config application,
and tini reaps children. A small action adapter changes only the UID of the
standard stop command; it does not replace the supervisor or FRR privilege code.

Start as root, primary group frr (101), supplemental frrvty (102). ospfd 10.6.1
explicitly rejects non-root entry before its standard FRR privilege drop; a
non-root launcher was tested and rejected rather than patched. The protocol
daemons drop to FRR UID 100/GID 101. The Chart restores seven caps after ALL:
CHOWN for desired config ownership, SETUID/SETGID for standard daemon account
drop and su-based stop, and NET_ADMIN/NET_RAW/NET_BIND_SERVICE/SYS_ADMIN declared
by the packaged FRR daemons. FOWNER is unnecessary with freshly copied owned
files and group-accessible runtime directories and was removed. No CAP_KILL is
added: stop uses the daemon account, while the root watchfrr is signalled by the
root entrypoint. This is the working task-specific set, not a mathematical proof
of a global capability minimum or a production endorsement.

All daemons share the Pod netns. Runtime `/etc/frr`, `/run/frr`, `/var/tmp/frr`
and `/lib/frr` are Pod-private emptyDirs with fsGroup 101; no host mounts.
`/lib/frr` is the Alpine build's mgmtd/state path. Projected ConfigMap files in
`/config` are read only; accepted bytes are copied into writable runtime config
at every start. Live vtysh changes are not the configuration source.

The entrypoint owns loopback installation. FRR only advertises that address
passively. It requires IPv4 eth0 and exactly the declared inventory: lo/eth0/net1
in core mode, or lo/eth0/net1..net4 in default direct-client mode. Each secondary
is VLAN-type with the expected /31 address. The entrypoint then installs the
stable /32. Missing/extra interfaces or unsupported counts fail before daemons.
Under Owner-approved [ADR 0014](adr/0014-inactive-tunl0.md), only an additional
tunl0 is permitted at startup when its administrative UP flag is absent, link
state is DOWN, and both IPv4/IPv6 address readbacks are empty. Failed readbacks,
an active/addressed tunl0, and every other extra interface still fail closed.
The runtime never changes or uses tunl0; forwarding and required VLAN checks
remain unchanged.

## Forwarding, health and boundaries

Calico owns initialization of forwarding=0. The container independently reads
it after all attachments, before daemon startup, during startup and every
one-second normal guard interval. It never writes/remounts proc. A violation
exits the wrapper, removes the readiness marker, terminates watchfrr and invokes
standard daemon stops as frr. Readiness alone is not the enforcement path.
The interval plus process shutdown is not a zero-window forwarding guarantee;
kernel-capable compromise is residual risk. Real negative packet/failure/drift
acceptance remains necessary, separate from the isolated detector test.

Startup waits for daemon PID/process identity, OSPF CLI responsiveness and
successful `vtysh -b`. Health verifies the guard, boot marker and expected
non-zombie processes; watchfrr independently monitors vty responsiveness.
Health never requires all remote neighbors to be Established/Full.

FRR's `bgp no-rib` is a **global configuration command** in this build, rendered
before `router bgp`, not in its stanza. IPv4 peers share the cluster ASN,
RR loopback update-source and unchanged NEXT_HOP. Each Cluster ID is explicitly
derived from that RR's loopback IPv4 without `/32`, not from its Router ID;
neither shared `cluster.clusterId` nor per-RR `clusterId` is an accepted input.
OSPF is
P2P on secondary links with passive loopback and permanent max-metric. Core
mode OSPF runs only on net1 toward core. Its IPv4 iBGP peers may be numerous;
`route-reflector-client` is rendered only for entries explicitly marked true.
The opposite RR, if explicitly listed, must be a normal non-Client peer. VLANs
are not created for BGP peers. Default mode retains four direct Client links.

Private Worker/namespace binding, Multus/NAD provisioning, admission and a full
secondary chain are Owner-owned and unmodified. Chart checksum is audit metadata,
not an implicit restart controller. See the proposed runbook for bare-Pod
replacement limitations. Formal SBOM/CVE scan, package retention/security-update
policy and OSS licensing remain release gates; no image/Chart was published.
