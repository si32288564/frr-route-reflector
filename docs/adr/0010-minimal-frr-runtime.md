# ADR 0010 — Build a dedicated minimal FRR runtime image

**Status:** Proposed; becomes accepted only when reviewed by Owner and merged into `main`.

## Context

Codex Task 0001 stopped while probing the pinned upstream image `quay.io/frrouting/frr:10.3.1`. The reproduced `zebra` initialization requested `CAP_SYS_ADMIN`; a Docker run without the capability failed with exit code 1. Draft [PR #6](https://github.com/si32288564/frr-route-reflector/pull/6) contains the exact evidence. The reproduction proves the behavior of that candidate binary, **not** that all FRR builds or all routing functions require `SYS_ADMIN`.

The project's actual goal is a maintainable, secure **RR CNF**, not a custom FRRouting fork. Simply creating `FROM quay.io/frrouting/frr` does not change the inherited binary's capability requests. Image footprint and effective kernel privilege are independent security properties.

## Decision

1. **Develop the project's own runtime container image.** The first candidate uses an official **Alpine Linux 3.24** base pinned to an immutable digest, with the Alpine `v3.24/community` **FRRouting package**, initially identified as `frr 10.6.1-r0`. Pin the actual package revision and capture exact dependency versions/available architecture at build time. This is a **candidate**, not a prevalidated working runtime.
2. Consume **upstream FRR binaries/packages**, not a maintained custom FRR source fork or project-specific FRR patches. Add only the required configuration, runtime directories, account/capability handling, entrypoint and checks for this CNF. Use standard FRR process management instead of a custom supervisor.
3. Prefer installation of **distribution-signed packages**. Do not assume that all unused FRR daemon binaries can be excluded by an Alpine package install; evaluate the resulting package/file inventory, dependency tree, CVE state and container size. Minimize optional runtime tools and development packages without breaking supportability or diagnostics.
4. **Keep Debian Slim** (with a pinned supported FRR package and architecture) as **a single finite alternative** if the Alpine candidate cannot meet runtime/privilege/security requirements. Distroless, Wolfi and source rebuilds are not required for Task 0001.
5. The build identity is **base image digest + FRR package version/revision + resolved dependencies + build recipe + resulting image digest**. A mutable Alpine repository, a version-pinned `apk add` alone or the word "slim" does **not** demonstrate bit-for-bit repeatability; record package provenance, availability/retention and SBOM. Use a reproducible snapshot/archival mechanism for published builds when necessary, not an unbounded custom build system.

## Capability policy

- **Do not declare `CAP_SYS_ADMIN` categorically forbidden or categorically required.** Determine actual required capabilities for `zebra`, `ospfd`, `bgpd` (and the distribution's necessary helpers) with the pinned runtime.
- First attempt the minimal capability set. If `CAP_SYS_ADMIN` is requested, inspect the version/build capability configuration, distinguish capability-initialization needs from observed functional kernel operations, and assess whether a **disposable, isolated test** with the additional capability is justified.
- A diagnostic exception, if specifically authorized for the disposable lab execution, must retain `privileged: false`, `hostNetwork: false`, no host mount/socket, no host PID/IPC namespace, and no Worker-host sysctl mutation. Record seccomp/admission profile, capability list, and precisely observed process/network behavior. **Permitting a test does not approve a default release manifest or production-like permission grant.**
- Any proposal to ship a Pod manifest with `SYS_ADMIN`, to build FRR with altered privilege management (`--disable-capabilities`) or to require a privileged Pod is a **separate, explicit Owner security decision** based on concrete evidence and mitigations. Codex must not silently add it. Do not loosen other security requirements as a workaround.
- Independent invariant: the RR **must not transit IP packets**. Verify `net.ipv4.ip_forward=0` inside the Pod namespace and enforce fail closed even if a capability exception is eventually accepted. A small image or `bgp no-rib` does not substitute for this invariant.

## Evaluation gates (finite)

| Gate | Evidence required | Stop/continue |
|---|---|---|
| C-1 Package provenance | Alpine 3.24 base digest, FRR package version/repo/signature, architecture, package/dependency inventory | If package cannot be pinned/retrieved or cannot supply required binaries, compare Debian Slim |
| C-2 Limited-capability startup | Exact rootless/nonprivileged settings, `zebra`/`ospfd`/`bgpd` startup output and exit codes, requested/available capabilities | Record BLOCKED if request exceeds approved profile |
| C-3 Functional feasibility | FRR integrated config, OSPFv2 and iBGP mechanics, `bgp no-rib`, loopback, Pod-local forwarding guard in bounded test | Not a claim of full Kubernetes integration |
| C-4 Security/runtime profile | File/daemon inventory, container image size, package vulnerability review, seccomp/capability profile, immutable digest | If unacceptable, return options to Chat/Owner |

Only **Alpine 3.24** and, if necessary, **Debian Slim** are baseline candidates. Do not browse endless versions/tags or introduce permanent custom patch machinery to satisfy a single observed startup failure.

## Important lifecycle caveat

Alpine's `main` and `community` repositories have different support policies; a distro branch's 2028 support date **must not be interpreted as a guarantee of support for the FRR community package until then**. Document the actual package maintenance/update policy and identify how the project will receive supported FRR security fixes.

## Consequences / authority

- The implementation target remains **our own Dockerfile/runtime**, not a forked FRR codebase. The original official FRR image can remain a diagnostic comparator.
- This ADR **replaces the previous preference for using the upstream prebuilt FRR image as the runtime base**; it does not modify BGP/OSPF architecture, 2 Pods, 8 NADs, or no-IP-transit.
- [Implementation contract](../implementation-contract.md) owns the runtime projection and [Task 0001](../tasks/0001-bootstrap-container-chart.md) owns the finite execution/evidence scope. A pending permissions exception must not silently become a new Architecture state.

## References

- [Alpine 3.24 FRR package index](https://pkgs.alpinelinux.org/packages?branch=v3.24&name=frr)
- [Alpine release/support policy](https://alpinelinux.org/releases/)
- [Alpine apk version constraints / repository retention](https://wiki.alpinelinux.org/wiki/Apk)
- [FRR 10.3.1 upstream Zebra capability declarations](https://github.com/FRRouting/frr/blob/frr-10.3.1/zebra/main.c)
- [Kubernetes Linux capabilities](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
