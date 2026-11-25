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
{{- $core := eq $v.topology "core" -}}
{{- if eq $v.releaseMode "single" -}}
{{- if or (not $core) (ne (len $v.routers) 1) }}{{ fail "single release requires core topology and exactly one RR" }}{{ end -}}
{{- else -}}
{{- if ne (len $v.routers) 2 }}{{ fail "pair release requires exactly two RRs" }}{{ end -}}
{{- end -}}
{{- if ne $v.securityProfile "lab-sysadmin" }}{{ fail "explicit lab-sysadmin profile required" }}{{ end -}}
{{- $_ := include "rr.ipnum" $v.cluster.ospfArea -}}
{{- $names := dict -}}{{- $ips := dict -}}{{- $ids := dict -}}{{- $nodes := dict -}}{{- $vlans := dict -}}{{- $nets := dict -}}
{{- $rrloops := dict -}}{{- $peerips := dict -}}
{{- range $v.routers -}}{{- $_ := set $rrloops (trimSuffix "/32" .loopback) true -}}{{- end -}}
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
{{- if and (eq $v.placement "distinct-workers") (hasKey $nodes $node) }}{{ fail "duplicate Worker binding" }}{{ end -}}{{- $_ := set $nodes $node true -}}
{{- $rrip := $ip -}}
{{- $pairs := dict -}}{{- $ifs := dict -}}
{{- range .links -}}
{{- if not $core -}}
{{- if or (not (hasKey $names .client)) (hasKey $pairs .client) }}{{ fail "unknown or duplicate client link" }}{{ end -}}{{- $_ := set $pairs .client true -}}
{{- end -}}
{{- if hasKey $ifs .interface }}{{ fail "duplicate interface" }}{{ end -}}{{- $_ := set $ifs .interface true -}}
{{- $vlan := toString .vlanId -}}{{- if hasKey $vlans $vlan }}{{ fail "duplicate VLAN" }}{{ end -}}{{- $_ := set $vlans $vlan true -}}
{{- $n := int64 (include "rr.ipnum" (trimSuffix "/31" .localAddress)) -}}
{{- $_ := include "rr.unicast" (trimSuffix "/31" .localAddress) -}}
{{- $net := toString (div $n 2) -}}{{- if hasKey $nets $net }}{{ fail "overlapping /31" }}{{ end -}}{{- $_ := set $nets $net true -}}
{{- if .remoteAddress -}}{{- $remote := int64 (include "rr.ipnum" .remoteAddress) -}}
{{- if or (eq $n $remote) (ne (div $n 2) (div $remote 2)) }}{{ fail "remote endpoint must be opposite /31 member" }}{{ end -}}
{{- end -}}
{{- end -}}
{{- if $core -}}
{{- $peers := dict -}}
{{- range .neighbors -}}
{{- $_ := include "rr.unicast" .address -}}
{{- if eq .address $rrip }}{{ fail "self iBGP neighbor" }}{{ end -}}
{{- if hasKey $peers .address }}{{ fail "duplicate iBGP neighbor" }}{{ end -}}
{{- if and (hasKey $rrloops .address) .routeReflectorClient }}{{ fail "RR neighbor must be a non-Client peer" }}{{ end -}}
{{- $_ := set $peers .address true -}}{{- $_ := set $peerips .address true -}}
{{- end -}}
{{- end -}}
{{- end -}}
{{- if and (eq $v.placement "single-worker") (ne (len $nodes) 1) }}{{ fail "single-worker placement requires identical Worker selectors" }}{{ end -}}
{{- range $ip, $_ := $ips -}}{{- if hasKey $nets (toString (div (int64 (include "rr.ipnum" $ip)) 2)) }}{{ fail "loopback overlaps /31" }}{{ end -}}{{- end -}}
{{- range $ip, $_ := $peerips -}}{{- if hasKey $nets (toString (div (int64 (include "rr.ipnum" $ip)) 2)) }}{{ fail "BGP loopback neighbor overlaps /31" }}{{ end -}}{{- end -}}
{{- end -}}
{{- define "rr.peers" -}}
{{- if eq .v.topology "core" -}}{{ toJson .rr.neighbors }}
{{- else -}}
{{- $peers := list -}}
{{- range .v.clients -}}{{- $peers = append $peers (dict "address" (trimSuffix "/32" .loopback) "routeReflectorClient" true) -}}{{- end -}}
{{ toJson $peers }}
{{- end -}}
{{- end -}}
{{- define "rr.resourceName" -}}
{{- if eq .root.Values.releaseMode "single" -}}
{{- .root.Release.Name -}}
{{- else -}}
{{- printf "%s-%s" .root.Release.Name .rr.name -}}
{{- end -}}
{{- end -}}
{{- define "rr.config" -}}
{{- $peers := include "rr.peers" . | fromJsonArray -}}
frr defaults traditional
hostname {{ .rr.name }}
service integrated-vtysh-config
log stdout
interface lo
 ip ospf area {{ .v.cluster.ospfArea }}
 ip ospf passive
!
{{ $interfaces := list }}{{ range .rr.links }}{{ $interfaces = append $interfaces .interface }}{{ end }}{{ range sortAlpha $interfaces }}interface {{ . }}
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
 bgp cluster-id {{ trimSuffix "/32" .rr.loopback }}
 no bgp default ipv4-unicast
{{ range $peers }} neighbor {{ .address }} remote-as {{ $.v.cluster.bgpAsn }}
 neighbor {{ .address }} update-source {{ trimSuffix "/32" $.rr.loopback }}
{{ end }} address-family ipv4 unicast
{{ range $peers }}  neighbor {{ .address }} activate
{{ if .routeReflectorClient }}  neighbor {{ .address }} route-reflector-client
{{ end }}{{ end }} exit-address-family
!
{{- end -}}
