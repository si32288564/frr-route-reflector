{{- define "rr.ipnum" -}}
{{- $p := splitList "." . -}}
{{- if ne (len $p) 4 }}{{ fail "invalid IPv4" }}{{ end -}}
{{- $n := 0 -}}
{{- range $i, $s := $p -}}
{{- if or (not (regexMatch "^(0|[1-9][0-9]{0,2})$" $s)) (gt (int $s) 255) }}{{ fail "invalid IPv4 octet" }}{{ end -}}
{{- $n = add (mul $n 256) (int $s) -}}
{{- end -}}{{ $n }}
{{- end -}}
{{- define "rr.unicast" -}}
{{- $n := int64 (include "rr.ipnum" .) -}}
{{- $first := div $n 16777216 -}}
{{- if or (eq $first 0) (eq $first 127) (ge $first 224) }}{{ fail "non-unicast identity/address" }}{{ end -}}
{{- end -}}
{{- define "rr.validate" -}}
{{- if gt (len .Release.Name) 30 }}{{ fail "release name maximum is 30" }}{{ end -}}
{{- $v := .Values -}}
{{- if ne $v.securityProfile "lab-sysadmin" }}{{ fail "explicit lab-sysadmin profile required" }}{{ end -}}
{{- $_ := include "rr.ipnum" $v.cluster.clusterId -}}
{{- $_ := include "rr.unicast" $v.cluster.clusterId -}}
{{- $_ := include "rr.ipnum" $v.cluster.ospfArea -}}
{{- $names := dict -}}{{- $ips := dict -}}{{- $ids := dict -}}{{- $nodes := dict -}}{{- $vlans := dict -}}{{- $nets := dict -}}
{{- range $v.clients -}}
{{- if hasKey $names .name }}{{ fail "duplicate client name" }}{{ end -}}{{- $_ := set $names .name true -}}
{{- $ip := trimSuffix "/32" .loopback -}}{{- $_ := include "rr.ipnum" $ip -}}
{{- $_ := include "rr.unicast" $ip -}}
{{- if hasKey $ips $ip }}{{ fail "duplicate loopback" }}{{ end -}}{{- $_ := set $ips $ip true -}}
{{- end -}}
{{- $rrnames := dict -}}
{{- range $v.routers -}}
{{- if hasKey $rrnames .name }}{{ fail "duplicate RR name" }}{{ end -}}{{- $_ := set $rrnames .name true -}}
{{- $_ := include "rr.ipnum" .routerId -}}
{{- $_ := include "rr.unicast" .routerId -}}
{{- if hasKey $ids .routerId }}{{ fail "duplicate router ID" }}{{ end -}}{{- $_ := set $ids .routerId true -}}
{{- $ip := trimSuffix "/32" .loopback -}}{{- $_ := include "rr.ipnum" $ip -}}
{{- $_ := include "rr.unicast" $ip -}}
{{- if hasKey $ips $ip }}{{ fail "duplicate loopback" }}{{ end -}}{{- $_ := set $ips $ip true -}}
{{- $node := index .nodeSelector "kubernetes.io/hostname" -}}
{{- if hasKey $nodes $node }}{{ fail "duplicate Worker binding" }}{{ end -}}{{- $_ := set $nodes $node true -}}
{{- $pairs := dict -}}{{- $ifs := dict -}}
{{- range .links -}}
{{- if or (not (hasKey $names .client)) (hasKey $pairs .client) }}{{ fail "unknown or duplicate client link" }}{{ end -}}{{- $_ := set $pairs .client true -}}
{{- if hasKey $ifs .interface }}{{ fail "duplicate interface" }}{{ end -}}{{- $_ := set $ifs .interface true -}}
{{- $vlan := toString .vlanId -}}{{- if hasKey $vlans $vlan }}{{ fail "duplicate VLAN" }}{{ end -}}{{- $_ := set $vlans $vlan true -}}
{{- $n := int64 (include "rr.ipnum" (trimSuffix "/31" .localAddress)) -}}
{{- $_ := include "rr.unicast" (trimSuffix "/31" .localAddress) -}}
{{- $net := toString (div $n 2) -}}{{- if hasKey $nets $net }}{{ fail "overlapping /31" }}{{ end -}}{{- $_ := set $nets $net true -}}
{{- if .remoteAddress -}}{{- $remote := int64 (include "rr.ipnum" .remoteAddress) -}}
{{- if or (eq $n $remote) (ne (div $n 2) (div $remote 2)) }}{{ fail "remote endpoint must be opposite /31 member" }}{{ end -}}
{{- end -}}
{{- end -}}
{{- end -}}
{{- range $ip, $_ := $ips -}}{{- if hasKey $nets (toString (div (int64 (include "rr.ipnum" $ip)) 2)) }}{{ fail "loopback overlaps /31" }}{{ end -}}{{- end -}}
{{- end -}}
{{- define "rr.config" -}}
frr defaults traditional
hostname {{ .rr.name }}
service integrated-vtysh-config
log stdout
interface lo
 ip ospf area {{ .v.cluster.ospfArea }}
 ip ospf passive
!
{{ range sortAlpha (list "net1" "net2" "net3" "net4") }}interface {{ . }}
 ip ospf network point-to-point
 ip ospf area {{ $.v.cluster.ospfArea }}
!
{{ end }}router ospf
 ospf router-id {{ .rr.routerId }}
 max-metric router-lsa administrative
!
bgp no-rib
router bgp {{ .v.cluster.bgpAsn }}
 bgp router-id {{ .rr.routerId }}
 bgp cluster-id {{ .v.cluster.clusterId }}
 no bgp default ipv4-unicast
{{ range .v.clients }} neighbor {{ trimSuffix "/32" .loopback }} remote-as {{ $.v.cluster.bgpAsn }}
 neighbor {{ trimSuffix "/32" .loopback }} update-source {{ trimSuffix "/32" $.rr.loopback }}
{{ end }} address-family ipv4 unicast
{{ range .v.clients }}  neighbor {{ trimSuffix "/32" .loopback }} activate
  neighbor {{ trimSuffix "/32" .loopback }} route-reflector-client
{{ end }} exit-address-family
!
{{- end -}}
