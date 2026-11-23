# ラボ用設定

Ownerが2026-11-24に機密情報を含まないと確認し、公開を承認した設定は
[lab-values.yaml](lab-values.yaml)です。今回の承認はこの設定に限り、
他の私有ファイル・認証情報・未編集ログの公開は含みません。

2 WorkerにRRを各1台、各RRにCore向けVLANを1本作成します。
Core＋4 ClientをRR Client、相手RRを通常Peerとする設定です。
デプロイ・OSPF/BGP・非転送・復旧の実環境試験は未実施です。

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
