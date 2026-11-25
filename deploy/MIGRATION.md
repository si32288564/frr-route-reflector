# 既存rrペアreleaseからrr01/rr02への移行

既存`rr`が`rr-rr01`/`rr-rr02`を所有するラボ向けの未実施手順です。
新規環境は[通常のinstall](README.md)だけで構いません。
コンテナ・実効FRR設定・Loopback/Worker/VLANは維持し、資源名と所有releaseを
分けます。稼働中の旧RRと同じLoopbackの新Podを同時に作りません。

## 事前保存

対象context、両RRの起動/forwarding/OSPF/iBGPと片系停止の影響を確認します。
移行中に古い`rr`をupgrade/reconcileしないでください。移行済みRRの旧Podを
再生成し、同じLoopbackを重複させる恐れがあります。Namespaceは変更しません。

```sh
umask 077
mkdir -p /tmp/rr-migration
chmod 700 /tmp/rr-migration
helm get values rr -n frr-route-reflector -a > /tmp/rr-migration/old-values.yaml
helm get manifest rr -n frr-route-reflector > /tmp/rr-migration/old-manifest.yaml
```

旧Chartのソースも保存します。実効boot config、イメージDigest、配置・リンク・
Peerが新common＋個別valuesと一致することを確認します。実環境で追加変更が
あれば個別valuesへ反映してから移行します。
部分rollback用に既存ヘルパーで旧RR単位のsnapshotを保存します。
この準備は移行時だけで、通常のinstallには不要です。

```sh
kubectl create --dry-run=client -n frr-route-reflector \
  -f /tmp/rr-migration/old-manifest.yaml -o json > /tmp/rr-migration/old.json
python3 deploy/prepare-replacement.py /tmp/rr-migration/old.json
```

`rr01-replacement.json`/`rr02-replacement.json`は旧`rr`所有のrollback用です。
新releaseのinstallには使いません。

## RR-01を移行

```sh
kubectl delete pod rr-rr01 -n frr-route-reflector --wait=true --timeout=60s
```

Worker-01のsandbox終了・CNI cleanupを確認します。到達不能、削除未完了、
cleanup未確認なら停止し、force-deleteしません。旧RR-01のConfigMap/NADが
残ること自体は正常です。Podなしでは接続を作りません。

```sh
helm install rr01 ./charts/frr-route-reflector \
  -n frr-route-reflector --create-namespace \
  -f deploy/values-common.yaml -f deploy/values-rr01.yaml --wait --timeout 180s
kubectl exec -n frr-route-reflector rr01 -- cat /proc/sys/net/ipv4/ip_forward
kubectl exec -n frr-route-reflector rr01 -- vtysh -c 'show ip ospf neighbor'
kubectl exec -n frr-route-reflector rr01 -- vtysh -c 'show bgp ipv4 unicast summary'
```

起動、forwarding=0、Loopback、OSPF Full、必要なiBGPが元どおりで、
RR-02が運用継続していることを確認します。Readyだけで次へ進みません。

## RR-02を移行

```sh
kubectl delete pod rr-rr02 -n frr-route-reflector --wait=true --timeout=60s
```

Worker-02のsandbox終了/CNI cleanup確認後:

```sh
helm install rr02 ./charts/frr-route-reflector \
  -n frr-route-reflector --create-namespace \
  -f deploy/values-common.yaml -f deploy/values-rr02.yaml --wait --timeout 180s
```

RR-01と同じ項目、および経路反映/NEXT_HOP/FIBを確認します。
両新releaseが確認できたら旧releaseを撤去します。

```sh
helm uninstall rr -n frr-route-reflector --wait --timeout 120s
helm list -n frr-route-reflector
kubectl get pods,configmaps,network-attachment-definitions.k8s.cni.cncf.io -n frr-route-reflector
```

旧名`rr-rr01`/`rr-rr02`/`rr-rr01-net1`/`rr-rr02-net1`だけが撤去対象です。
新名`rr01`/`rr02`/`rr01-net1`/`rr02-net1`とは重複しません。
Helm Secretの編集、所有権adoption、Namespace削除は不要です。

## 移行途中の失敗・rollback

RR-01のinstall/接続確認に失敗したらRR-02は変更せず、次で旧RR-01へ戻します。

```sh
helm uninstall rr01 -n frr-route-reflector --wait --timeout 120s
# 新RR-01の終了/CNI cleanup確認後:
kubectl apply -n frr-route-reflector -f /tmp/rr-migration/rr01-replacement.json
```

新releaseが作られなかった失敗ではuninstallはNotFoundとなるので、残存Podを
確認します。終了・cleanup未確認なら旧Podを作りません。
RR-02の失敗もrr02だけuninstallし、cleanup後に旧rr02 snapshotをapplyします。
正常な新rr01は維持できます。古い`rr`全体をupgradeして戻す方法は使いません。
新旧両RR-01が同時に作成される危険があります。

全て旧構成へ戻す場合も、片系を残し、新RRを1つずつuninstall・cleanup・
旧snapshot再作成して検証します。最後に両旧RRだけになったことを確認します。
旧release撤去後の全体復旧は、両新releaseを片付け、cleanup後に保存済み
旧Chart/valuesで`rr`をinstallする別の停止作業です。
操作・rollbackは未実測で、経路維持時間や無停止を保証するものではありません。
