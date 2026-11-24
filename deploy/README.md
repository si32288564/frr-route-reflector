# ラボ用設定

Ownerが2026-11-24に機密情報を含まないと確認し、公開を承認した設定は
[lab-values.yaml](lab-values.yaml)です。今回の承認はこの設定に限り、
他の私有ファイル・認証情報・未編集ログの公開は含みません。

2 WorkerにRRを各1台、各RRにCore向けVLANを1本作成します。
Core＋4 ClientをRR Client、相手RRを通常Peerとする設定です。
初回の実環境配備では、追加tunl0を旧イメージが拒否し両PodがCrashLoopに
なりました。現在の固定Digestは[ADR 0014](../docs/adr/0014-inactive-tunl0.md)
の限定修正版（タグ`main-51c49f5`）です。旧タグは変更していません。
修正版のKubernetes起動・OSPF/BGP・パケット非転送・復旧は未実測です。

## 取得・静的確認

リポジトリのルートで実行します。

```sh
git pull --ff-only
helm lint ./charts/frr-route-reflector -f deploy/lab-values.yaml
helm template rr ./charts/frr-route-reflector \
  -n frr-route-reflector -f deploy/lab-values.yaml > /tmp/rr-rendered.yaml
```

出力は2 Pod・2 ConfigMap・2 NADです。生成ファイルを手修正せず、
変更はvaluesへ反映して再生成してください。

## 初回デプロイ

最初に`kubectl config current-context`で対象ラボを確認します。
両Workerのhostnameラベル・eno3のVLAN接続、VLAN/static CNI、Workerの
イメージPull、Calicoの有効delegateの
`container_settings.allow_ip_forwarding:false`を確認してください。
管理端末でのDocker Pull成功はWorkerのcontainerdでのPull成功を意味しません。

専用Namespaceがなければ作成し、Admissionを検査します。

```sh
kubectl get namespace frr-route-reflector
# NotFoundの場合だけ実行:
kubectl create namespace frr-route-reflector
kubectl apply --dry-run=server -n frr-route-reflector -f /tmp/rr-rendered.yaml
```

現行の`lab-sysadmin`はSYS_ADMIN等を必要とし、Baseline/Restricted PSAでは
拒否されます。拒否時は停止し、既存の許可条件を確認してください。
この手順ではAdmission緩和やクラスタ全体のCalico設定変更を行いません。
Pod内forwardingが1なら起動guardが停止します。host sysctlや追加権限で
回避しないでください。dry-runだけではCNIの実行結果は確認できません。

前提とdry-runが成立し、同名releaseがない初回に実行します。

```sh
helm install rr ./charts/frr-route-reflector \
  -n frr-route-reflector -f deploy/lab-values.yaml --wait --timeout 180s
kubectl get pods -n frr-route-reflector -o wide
```

失敗時は再installせず、`helm status rr -n frr-route-reflector`、
Podのdescribe/logで切り分けます。ReadyだけでOSPF/BGP成功とは扱いません。
各Podの`ip_forward=0`、OSPF Full 1隣接、iBGP Established 6ネイバー、
反映先Clientの経路とNEXT_HOP、RR FIBへのBGP経路非登録を別々に実測します。
非転送のパケット試験と停止・再生成・cleanupも別途実測が必要です。

Bare Podは削除しても自動再生成されません。更新・復旧は
[既存runbook](../docs/runbook.md)の片系停止・CNI cleanup確認後の置換方針に従います。

この初回releaseだけを全撤去する場合は以下です。

```sh
helm uninstall rr -n frr-route-reflector --wait --timeout 120s
```

両WorkerでPod sandbox終了とCNI cleanupを確認してから再配備してください。
Namespace・既存bridge・Core/Client設定はこの撤去コマンドの対象外です。

## 旧イメージで初回installが失敗した場合の片系置換

これは両Podが起動失敗している今回の初期復旧用の手順です。
無停止アップグレードの実証ではありません。既存の値・release情報・ログを
保存し、最新のソース一式へ更新します。ZIP展開の場合は`git pull`ではなく
最新ZIPを別ディレクトリへ展開します。Namespaceや既存releaseは作り直しません。

```sh
umask 077
helm get values rr -n frr-route-reflector -a > /tmp/rr-before-values.yaml
helm get manifest rr -n frr-route-reflector > /tmp/rr-before-manifest.yaml
helm lint ./charts/frr-route-reflector -f deploy/lab-values.yaml
helm template rr ./charts/frr-route-reflector \
  -n frr-route-reflector -f deploy/lab-values.yaml > /tmp/rr-new.yaml
kubectl create --dry-run=client -n frr-route-reflector \
  -f /tmp/rr-new.yaml -o json > /tmp/rr-new.json
```

同じHelm生成結果からRR単位のファイルを作ります。Python3標準ライブラリのみを
使用します。Helm所有情報を保ち、ConfigMap→NAD→Podの順に並べます。

```sh
python3 deploy/prepare-replacement.py
```

kubectlの出力が単一Listでも、複数JSONの連続でも処理します。
このコマンドは`/tmp/rr-new.json`を読み、同じディレクトリに
`rr01-replacement.json`と`rr02-replacement.json`を作るだけです。
クラスタへの接続・Pod削除・適用は行いません。PythonコードやREADME抽出の
手入力は不要です。

最初にRR-01だけ停止します。

```sh
kubectl delete pod rr-rr01 -n frr-route-reflector --wait=true --timeout=60s
```

Worker-01が到達可能で、旧Pod sandbox終了とCNI DEL完了を確認してから
次へ進みます。不明なまま再生成・force-deleteしません。

```sh
kubectl apply -n frr-route-reflector -f /tmp/rr01-replacement.json
kubectl wait -n frr-route-reflector --for=condition=Ready pod/rr-rr01 --timeout=120s
kubectl exec -n frr-route-reflector rr-rr01 -- cat /proc/sys/net/ipv4/ip_forward
kubectl exec -n frr-route-reflector rr-rr01 -- vtysh -c 'show ip ospf neighbor'
```

Readyとforwarding=0を確認し、OSPF状態を記録します。起動失敗ならRR-02は
触らず、改善された停止ログを確認します。対向Core未設定のOSPF未確立は
起動成功と区別します。続いてRR-02を同じ順序で置換します。

```sh
kubectl delete pod rr-rr02 -n frr-route-reflector --wait=true --timeout=60s
# Worker-02のsandbox終了/CNI DEL確認後:
kubectl apply -n frr-route-reflector -f /tmp/rr02-replacement.json
kubectl wait -n frr-route-reflector --for=condition=Ready pod/rr-rr02 --timeout=120s
kubectl exec -n frr-route-reflector rr-rr02 -- cat /proc/sys/net/ipv4/ip_forward
```

両Podがレビュー済みrenderと同じ状態になった後、Helmのrelease記録を整合します。
image/配置/設定を再変更せず、`--force`を使用しません。

```sh
helm upgrade rr ./charts/frr-route-reflector \
  -n frr-route-reflector -f deploy/lab-values.yaml --wait --timeout 180s
```

この片系置換・記録整合の実環境手順は未実測です。旧イメージはtunl0環境で
起動しない既知不具合があるため、旧Digestへ戻すことを正常復旧とは扱いません。
