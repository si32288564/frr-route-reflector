# RRごとのHelm管理

1 RR＝1 release。同じChartへ共通valuesとRRごとのvaluesを渡します。
FRR設定・コンテナ・VLAN・権限は既存構成と同じです。
稼働中の旧`rr` releaseがある環境では、[移行手順](MIGRATION.md)を先に
確認してください。同じLoopbackを持つ新旧Podを同時に起動しません。

## 設定ファイル

| ファイル | 内容 |
|---|---|
| [values-common.yaml](values-common.yaml) | 固定イメージDigest、ASN、OSPF Area、securityProfile、単体release指定 |
| [values-rr01.yaml](values-rr01.yaml) | RR-01のLoopback、Worker、VLAN501、/31、ネイバー |
| [values-rr02.yaml](values-rr02.yaml) | RR-02のLoopback、Worker、VLAN502、/31、ネイバー |

共通ファイルの後に、対象RRの個別ファイルを1つだけ指定します。
Helmの配列は置換されるため、rr01/rr02の両個別ファイルを同時指定しません。
全体で2 RRですが、各releaseは1 Pod・1 ConfigMap・1 NADだけを所有します。
Pod/ConfigMap名はrelease名、NAD名は`<release>-net1`です。

これらはOwnerが公開可能と確認したラボ設定です。他環境では値を変更し、
認証情報や未承認の社内情報を公開しないでください。

## 初回install

管理端末で対象クラスタのcontextを確認し、リポジトリルートで実行します。
CalicoによるPod内forwarding=0、Multus/VLAN/static CNI、eno3のtrunk、
Admission、WorkerからのイメージPullが成立している環境を前提とします。
Chartはそれらをインストール・変更しません。

```sh
helm install rr01 ./charts/frr-route-reflector \
  -n frr-route-reflector --create-namespace \
  -f deploy/values-common.yaml -f deploy/values-rr01.yaml --wait --timeout 180s

helm install rr02 ./charts/frr-route-reflector \
  -n frr-route-reflector --create-namespace \
  -f deploy/values-common.yaml -f deploy/values-rr02.yaml --wait --timeout 180s
```

手動Namespace作成、manifest出力・分割・kubectl applyは初回installに不要です。
`--create-namespace`はNamespaceを作るだけで、Admissionを緩和しません。
`--wait`の成功はFRR/guardの起動確認で、全ネイバーの接続確認とは別です。

## 状態確認

```sh
helm list -n frr-route-reflector
kubectl get pods -n frr-route-reflector -o wide
kubectl exec -n frr-route-reflector rr01 -- cat /proc/sys/net/ipv4/ip_forward
kubectl exec -n frr-route-reflector rr01 -- vtysh -c 'show ip ospf neighbor'
kubectl exec -n frr-route-reflector rr01 -- vtysh -c 'show bgp ipv4 unicast summary'
```

RR-02はPod名を`rr02`に置き換えます。各RRのforwarding=0、CoreとのOSPF Full
1隣接、Core＋4 Client＋相手RRのiBGP計6セッションを確認します。
NEXT_HOP維持、FIB非登録、パケット非転送は個別の試験結果として扱います。

## 個別撤去・変更

RR-01だけを撤去する例です。RR-02の資源は別releaseなので対象外です。

```sh
helm uninstall rr01 -n frr-route-reflector --wait --timeout 120s
```

設定やイメージを変更する場合も、Bare Pod/boot snapshotの仕様は同じです。
**通常のhelm upgradeだけではFRR設定の再読込を保証しません。** ConfigMapが
更新されても起動済みFRRへ自動反映されず、一部Podフィールドは変更不能です。
片系の旧valuesとイメージを保存し、もう片系の実接続を確認した上で対象releaseを
uninstallし、sandbox終了・CNI cleanup後に新しいvaluesで同じreleaseをinstallします。
共通valuesを変更しても、両方へ同時適用せず片系ずつ実施します。
`--force`、独自hook、Controllerによる再起動は追加していません。
失敗時も対象releaseだけを片付け、cleanup後に保存済みvaluesで再installします。

## 全撤去

```sh
helm uninstall rr01 -n frr-route-reflector --wait --timeout 120s
helm uninstall rr02 -n frr-route-reflector --wait --timeout 120s
# 両releaseとPod/CNIの撤去確認後、専用Namespaceも不要なら:
kubectl delete namespace frr-route-reflector
```

Namespaceは共有するため、片系だけを削除するときは残します。

## 検証・互換構成

```sh
helm lint ./charts/frr-route-reflector \
  -f deploy/values-common.yaml -f deploy/values-rr01.yaml
helm lint ./charts/frr-route-reflector \
  -f deploy/values-common.yaml -f deploy/values-rr02.yaml
```

各releaseの検証範囲はその入力だけです。別releaseとのLoopback/Router ID/
Worker/VLAN/サブネットの重複や、相手RRのClient指定誤りは、2つの入力を
合わせて確認する必要があります。同梱2プロファイルは開発時にpairモードでも
検証します。単独Chartが他releaseを探索する機構はありません。

既存`lab-values.yaml`と従来のサンプルは互換モード`releaseMode: pair`として
そのまま使用できます。[旧手順](legacy-pair.md)は履歴・復旧用に残します。
今回の変更による実環境のinstall/uninstall・移行・rollbackは未実施です。
