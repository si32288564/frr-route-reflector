# ADR 0005 — Client transit on one broadcast VLAN

Status: Proposed, subject to Owner review.

The four RR clients share one independent VLAN and IPv4 /29 for data-plane forwarding. The clients run OSPFv2 broadcast on this multiaccess interface, in the same area as their RR-facing P2P links. The RR Pods and Test peers do not attach to this VLAN. The RR-facing eight VLANs remain IPv4 /31 OSPF point-to-point. The Test-to-Client eBGP segments remain independent and outside OSPF.

The client transit VLAN provides the normal forwarding path between clients; it is not managed by the RR Helm Chart. Actual VID, addresses, DR/BDR selection and interface costs remain environment parameters. Loss of this VLAN may cause traffic loss; no claim of client data-plane HA is made.

Authority: docs/network-design.md and docs/requirements.md. Reference: https://docs.frrouting.org/en/latest/ospfd.html
