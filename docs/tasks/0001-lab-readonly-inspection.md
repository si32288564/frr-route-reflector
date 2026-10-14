# Task 0001 — read-only lab namespace prerequisite inspection

Codexによる報告:

Date: 2026-10-15 JST. Scope: the existing cluster accessible through the
authorized development host's pre-existing kubectl configuration, plus existing
SSH access to its Nodes. No Pod, container, namespace, policy, CNI or host setting
was created or modified. No runtime implementation resumed.

Instruction: [Architecture review of 3a98744](https://github.com/si32288564/frr-route-reflector/pull/6#pullrequestreview-5525966840).
That review accepts the Docker STOP evidence but requires actual lab inspection
instead of inferring Kubernetes state from Docker defaults. This record adds
observations and does not erase the original Docker results.

## Outcome

**An existing Calico namespace initialization mechanism was found.** On two
inspected Worker candidates, the actual installed primary CNI configuration
contains `container_settings.allow_ip_forwarding: false`. One existing READY,
non-host-network Pod sandbox on each candidate read back `net.ipv4.ip_forward=0`.
This is actual Kubernetes workload namespace evidence, without creating a test
Pod or executing a process inside an application container.

The initialization prerequisite is therefore **not proven absent** in this lab.
Calico is an additional existing mechanism beyond the review's two examples;
it does not require installing a tuning chain or changing kubelet settings.
This observation is **not acceptance of an RR Pod**, the final two designated
Workers, a lab admission exception, or four secondary VLAN attachments.

The accessible cluster has one control-plane Node and four Workers. Two Worker
candidates were inspected, not silently declared the Owner-designated RR pair.
The repository contains no accepted binding of the two actual RR Workers or
authorized RR namespace. Owner confirmation of the cluster/pair/namespace is
still necessary before any deployment plan is treated as bound to this lab.

## Read-only observations

| Area | Observed result | Limit |
|---|---|---|
| API access | Existing kubectl reads succeeded; inspected Worker versions v1.35.4, containerd 2.2.2 | Do not infer access failure from a different SSH endpoint |
| Primary CNI desired config | Calico operator-managed cni-config has allow_ip_forwarding=false, plugins ordered calico then portmap | Desired configuration alone is not runtime proof |
| Actual CNI files on both candidates | Only 10-calico.conflist and the Calico credential-file path listed in CNI config directory; conflist matches calico → portmap, allow_ip_forwarding=false | Credential-file contents were not read |
| Installed CNI version | Calico install-cni image v3.31.4; tuning --version reports v3.31.4 on both candidates | No independent binary provenance audit |
| Existing sandbox readback | One READY non-host-network sandbox per candidate: ip_forward=0 | Point-in-time samples, not startup/restart/drift/packet testing |
| NAD | API resource type unavailable; CRD list has no NAD CRD | This is not an empty NAD list or an RBAC denial |
| Multus | No Multus DaemonSet observed and no Multus configuration in either inspected CNI directory | Do not equate every binary inventory with proof of global absence |
| tuning and vlan | Binaries present on both candidates | Binary presence does not prove execution |
| tuning chain | No tuning entry in actual conflist; no NAD mechanism available | No enabled tuning/sysctl ordering established |
| tuning allowlist | /etc/cni/tuning/allowlist.conf not found on either candidate | No inference about compiled defaults or other future paths |
| kubelet configz | Both GET requests succeeded; allowedUnsafeSysctls absent in returned effective config | No unsafe-sysctl authorization established |
| kubelet flags | No unsafe-sysctl CLI flag; kubeadm extra args and /etc/default/kubelet extra args empty on both candidates | No kubelet configuration change performed |
| Existing Pod specs | Returned Pod securityContext.sysctls fields were empty | No existing declared unsafe-sysctl test evidence found in this snapshot |
| Admission objects | No ValidatingAdmissionPolicy/Binding or validating/mutating webhook configurations returned | This is not proof that all admission checks permit the RR profile |
| Namespace PSA labels | Some infrastructure namespaces enforce privileged; others have no explicit PSA enforce label | Not authorization to deploy RR into an infrastructure namespace |
| API server static manifest | Explicit enable-admission-plugins=NodeRestriction; no disable-admission or admission-config-file flag matched | Built-in/default admission still applies; no RR admission test performed |

The earlier management-name SSH timed out; the Node names returned by the
existing API exposed a reachable internal SSH route. That route allowed the
actual CNI file inspection. KVM guest-agent address discovery was unsupported
(agent not configured); lease discovery returned no address. Those failures
did not prevent the later API/Node read-only inspections.

No request returned an RBAC/permission denial for the successful inspection
paths. `not found`, `unreachable`, and `not run` above are not interchangeable.
Private addresses, hostnames, application inventories, credential material and
full internal configuration/log dumps are intentionally not published.

## Evidence method / commands

These are sanitized command forms; placeholders represent private Node names
or existing sandbox IDs. They were not used to create resources.

```sh
kubectl get nodes -o wide --request-timeout=8s
kubectl get network-attachment-definitions.k8s.cni.cncf.io -A --request-timeout=8s
kubectl get crd -o name --request-timeout=8s
kubectl get daemonsets -A --request-timeout=8s
kubectl get configmap cni-config -n calico-system -o jsonpath='{.data}'
kubectl get installation.operator.tigera.io default -o jsonpath='{.spec.cni}'
kubectl get --raw /api/v1/nodes/<candidate>/proxy/configz --request-timeout=8s
kubectl get namespaces --show-labels --request-timeout=8s
kubectl get validatingadmissionpolicies,validatingadmissionpolicybindings
kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations
kubectl get pods -A -o jsonpath='{range .items[*]}{.spec.securityContext.sysctls}{"\n"}{end}'
```

Existing Node SSH with BatchMode and bounded connect timeouts was used for:

```sh
sudo -n cat /etc/cni/net.d/10-calico.conflist
sudo -n ls /etc/cni/net.d /opt/cni/bin
sudo -n ls -l /etc/cni/tuning/allowlist.conf
sudo -n /opt/cni/bin/tuning --version
sudo -n cat /var/lib/kubelet/kubeadm-flags.env
sudo -n cat /etc/default/kubelet
sudo -n cat /proc/<existing-kubelet-pid>/cmdline
sudo -n crictl --runtime-endpoint unix:///run/containerd/containerd.sock pods -o json
sudo -n crictl --runtime-endpoint unix:///run/containerd/containerd.sock inspectp <existing-ready-sandbox>
sudo -n nsenter -t <existing-sandbox-pid> -n cat /proc/sys/net/ipv4/ip_forward
```

A read-only Python wrapper parsed CRI JSON, selected the first READY sandbox
whose network namespace option was not NODE/host, then used its existing PID
for the last read. It printed only candidate index, forwarding value and any
unsafe-sysctl CLI flags. Both candidate reads returned 0, both CLI flag lists
were empty, both wrapper inspections exited 0. nsenter changes only the reader
process's namespace association; no sysctl write, mount, application exec or
namespace configuration change was made. The CRI inventory was not published.

Control-plane static manifest inspection matched only the three admission flag
patterns above. rg was unavailable there; the read was repeated with grep -E.

## Why the Calico setting is relevant

Read-only retrieval of upstream
[Calico v3.31.4 Linux dataplane source](https://github.com/projectcalico/calico/blob/v3.31.4/cni-plugin/pkg/dataplane/linux/dataplane_linux.go)
shows configureContainerSysctls writing `/proc/sys/net/ipv4/ip_forward` to 0 when
an IPv4 address exists and allowIPForwarding is false. DoWorkloadNetnsSetUp calls
it within the workload namespace during CNI setup. This corroborates the
installed configuration and current workload samples; no source was executed
or modified. Installed chain order is observed from configuration, not a trace
of a newly created RR sandbox.

## Minimal proposed binding and separate validation plan

No new tuning/sysctl resource or mount bypass is proposed. A minimal binding
can rely on the **existing Calico initialization** and require the runtime to
read forwarding=0 **after all CNI attachments finish and before FRR starts**.
If it is 1 or unreadable, stop; do not attempt a host fallback. Keep bounded
recurring guard checks and fail-closed daemon shutdown as already contracted.

This binding is a proposal pending confirmation of designated Workers and
lab-owned Multus prerequisites. Multus/NAD provisioning is currently missing
from the observed cluster state and is outside this read-only request. Its
future secondary-plugin sequence must not silently re-enable forwarding.

A separately authorized validation plan should:

1. Confirm Owner-selected cluster, two Workers and dedicated namespace; verify
   its already-approved admission permission for lab-sysadmin, without assuming
   an infrastructure namespace exemption can be reused.
2. After lab-owned Multus/VLAN prerequisites exist, verify actual full-chain
   ordering and initial forwarding state after four secondary attachments.
3. Start reviewed RR Pods under the exact lab profile and prove gate/config/
   loopback/daemon states, then container restart and fail-closed drift behavior.
4. Execute OSPF/BGP/reflection/no-rib/NEXT_HOP, negative transit and lifecycle
   acceptance separately; do not substitute ordinary workload samples for these.

## Status and handoff

Read-only investigation: **PASS / completed to the evidence above**.
Unsafe-sysctl path: **not established** (no allowlist entry or existing Pod
declaration found). Tuning path: **not enabled in observed chains**. Existing
Calico path: **configuration and ordinary namespace readback confirmed**.
RR deployment/admission/full secondary-chain validation: **NOT RUN**.
Integrated Task 0001 runtime acceptance: **BLOCKED pending Owner-owned lab
binding/provisioning evidence and separately authorized validation**.

No Pod creation, policy label edit, CNI installation, remount, host sysctl write,
containerd patch or cluster security change occurred. Old records are preserved.
PR #6 remains Draft; Issue #5 remains Open; main is not merged by Codex.
