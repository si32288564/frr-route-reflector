# ADR 0009 — Controlled Bare Pod update and recovery

**Status:** Proposed; becomes accepted only when merged to `main`.

## Context

Two distinct RR logical identities are pinned to two distinct Worker Nodes and attached to node-specific VLAN CNI resources. A directly managed Kubernetes `Pod` is not reconciled like a Deployment. A blind Helm update or Pod deletion is not an accepted rolling-upgrade strategy.

## Decision

- Preserve two fixed Bare Pods; `restartPolicy: Always` applies only to **containers within an existing Pod**.
- Changes to the **effective boot config or image** require an explicit operator-controlled Pod replacement, one RR at a time, after confirming the other RR remains operational. Avoid simultaneous replacements.
- The old incarnation must be fully stopped, and its Multus/VLAN attachment released, before the new same-identity Pod is started. Never relocate the missing RR to the other Worker.
- No implicit automation, temporary standby controller or on-the-fly reconciler is introduced. A finite **runbook** provides initial install, upgrade, recovery and rollback instructions.
- A failed interface cleanup or replacement **blocks new same-identity activation** until reconciled. Do not hide dangling network state by replacing with another Pod in parallel.
- A change to a ConfigMap or Pod annotation does not imply running FRR has adopted the change. Do not claim normal `helm upgrade` provides rolling mutation of immutable Pod fields.

## Operational consequences and open binding

The concrete delete/recreate and Helm command ordering remains an **implementation/runbook validation obligation**. The runbook must be proven with live Kubernetes; it may not assume that a missing Helm-owned Bare Pod is silently recreated by the release manager. On Worker failure, an operator restores the original Node and verifies safe CNI cleanup before reactivation.

**Required evidence:** one-sided replacement keeps the other RR available; interrupted replacement fails closed and can be recovered; rollback restores the previous reviewed snapshot; Pod deletion alone does not trigger a new Pod; no duplicate router identity or VLAN attachment appears.

Reference: [Kubernetes Pod concepts](https://kubernetes.io/docs/concepts/workloads/pods/).

Authority: [implementation-contract.md](../implementation-contract.md).
