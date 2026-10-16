# Task 0001 implementation binding

Accepted sources: Implementation Contract, ADR 0010/0011 and PR #6 review
5526023836. Helm values own all routing identities and mappings. Default values
are deliberately incomplete; the one positive security profile must be selected.
Unknown fields are rejected, including custom peers, forwarding policy and FRR
text. Example values are documentation-only, not an approved deployment plan.

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
passively. The default `four-client` topology requires IPv4 eth0 and exactly
lo/eth0/net1..net4, four VLAN-type links with the expected /31 addresses, then
installs the stable /32. The explicit `home-single-client` development topology
requires only lo/eth0/net1 and one VLAN /31 per RR. Both reject phantom interfaces.
See [the scoped home binding](tasks/0002-home-single-client.md); this does not
relax the seven-cap profile, forwarding guard or RR-only configuration ownership.

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
before `router bgp`, not in its stanza. Four IPv4 clients share the cluster ASN,
RR loopback update-source, unchanged NEXT_HOP and common cluster ID; OSPF is
P2P on secondary links with passive loopback and permanent max-metric.

Private Worker/namespace binding, Multus/NAD provisioning, admission and a full
secondary chain are Owner-owned and unmodified. Chart checksum is audit metadata,
not an implicit restart controller. See the proposed runbook for bare-Pod
replacement limitations. Formal SBOM/CVE scan, package retention/security-update
policy and OSS licensing remain release gates; no image/Chart was published.
