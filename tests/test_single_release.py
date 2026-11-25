"""Helm management-only regression: actual layered values and unchanged runtime."""
import collections
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile

import yaml

chart = 'charts/frr-route-reflector'
common_file = 'deploy/values-common.yaml'
common = yaml.safe_load(Path(common_file).read_text())
profiles = [yaml.safe_load(Path(f'deploy/values-{rr}.yaml').read_text()) for rr in ['rr01', 'rr02']]
legacy = yaml.safe_load(Path('deploy/lab-values.yaml').read_text())
assert [p['routers'][0] for p in profiles] == legacy['routers']
assert common['image'] == legacy['image']
assert common['cluster'] == legacy['cluster']


def helm(files, release='rr', lint=False, extra=(), target=chart):
    args = ['helm', 'lint', target] if lint else ['helm', 'template', release, target]
    for f in files:
        args += ['-f', f]
    return subprocess.run(args + ['-n', 'frr-route-reflector'] + list(extra), text=True, capture_output=True)


def render_value(value, release='rr'):
    with tempfile.NamedTemporaryFile('w', suffix='.json') as f:
        json.dump(value, f)
        f.flush()
        return helm([f.name], release)


def objects(result):
    assert result.returncode == 0, result.stderr
    return [o for o in yaml.safe_load_all(result.stdout) if o]


old_objects = objects(helm(['deploy/lab-values.yaml']))
rendered = []
for i, rr in enumerate(['rr01', 'rr02']):
    files = [common_file, f'deploy/values-{rr}.yaml']
    lint = helm(files, rr, lint=True)
    assert lint.returncode == 0, lint.stdout + lint.stderr
    result = helm(files, rr)
    objs = objects(result)
    assert result.stdout == helm(files, rr).stdout
    assert collections.Counter(o['kind'] for o in objs) == {'Pod': 1, 'ConfigMap': 1, 'NetworkAttachmentDefinition': 1}
    assert {(o['kind'], o['metadata']['name']) for o in objs} == {('Pod', rr), ('ConfigMap', rr), ('NetworkAttachmentDefinition', rr + '-net1')}
    cm = next(o for o in objs if o['kind'] == 'ConfigMap')
    before_cm = next(o for o in old_objects if o['kind'] == 'ConfigMap' and o['metadata']['name'] == 'rr-' + rr)
    assert cm['data'] == before_cm['data'], 'FRR boot configuration changed'
    pod = next(o for o in objs if o['kind'] == 'Pod')
    before_pod = copy.deepcopy(next(o for o in old_objects if o['kind'] == 'Pod' and o['metadata']['name'] == 'rr-' + rr))
    before_pod['spec']['volumes'][0]['configMap']['name'] = rr
    assert pod['spec'] == before_pod['spec'], 'runtime/security/placement changed'
    assert pod['metadata']['annotations']['rr.example.org/boot-sha256'] == before_pod['metadata']['annotations']['rr.example.org/boot-sha256']
    assert json.loads(pod['metadata']['annotations']['k8s.v1.cni.cncf.io/networks']) == [{'name': rr + '-net1', 'namespace': 'frr-route-reflector', 'interface': 'net1'}]
    nad = json.loads(next(o for o in objs if o['kind'] == 'NetworkAttachmentDefinition')['spec']['config'])
    old_nad = json.loads(next(o for o in old_objects if o['kind'] == 'NetworkAttachmentDefinition' and o['metadata']['name'] == 'rr-' + rr + '-net1')['spec']['config'])
    old_nad['name'] = rr + '-net1'
    assert nad == old_nad
    alternate = objects(helm(files, rr + '-alternate'))
    assert {(o['kind'], o['metadata']['name']) for o in alternate} == {
        ('Pod', rr + '-alternate'), ('ConfigMap', rr + '-alternate'),
        ('NetworkAttachmentDefinition', rr + '-alternate-net1')}
    assert next(o for o in alternate if o['kind'] == 'ConfigMap')['data'] == cm['data']
    override = objects(helm(files, rr, extra=['--set', 'cluster.bgpAsn=65000']))
    conf = next(o for o in override if o['kind'] == 'ConfigMap')['data']['frr.conf']
    assert 'router bgp 65000' in conf and conf.count('remote-as 65000') == 6
    rendered.append(objs)
assert {(o['kind'], o['metadata']['name']) for o in rendered[0]}.isdisjoint(
    {(o['kind'], o['metadata']['name']) for o in rendered[1]})
assert {(o['kind'], o['metadata']['name']) for o in old_objects}.isdisjoint(
    {(o['kind'], o['metadata']['name']) for objs in rendered for o in objs})

# The existing finite migration rollback preparation still targets only old
# names and ownership. Verify both List and the actual streamed kubectl shape.
for encoded in [json.dumps({'kind': 'List', 'items': old_objects}),
                '\n'.join(json.dumps(o) for o in old_objects)]:
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / 'old.json'
        source.write_text(encoded)
        prep = subprocess.run(['python3', 'deploy/prepare-replacement.py', str(source)], capture_output=True, text=True)
        assert prep.returncode == 0, prep.stderr
        for rr in ['rr01', 'rr02']:
            saved = json.loads((Path(folder) / (rr + '-replacement.json')).read_text())['items']
            assert [o['kind'] for o in saved] == ['ConfigMap', 'NetworkAttachmentDefinition', 'Pod']
            assert {o['metadata']['name'] for o in saved} == {'rr-' + rr, 'rr-' + rr + '-net1'}
            assert all(o['metadata']['annotations']['meta.helm.sh/release-name'] == 'rr' for o in saved)

# Each standalone input remains locally validated. Pair consistency is checked
# by reusing pair mode, not by querying an unrelated live Helm release.
single = {**common, **profiles[0]}
cases = []


def bad(label, mutate, initial=single):
    value = copy.deepcopy(initial)
    mutate(value)
    cases.append((label, value))


bad('empty-routers', lambda v: v.update(routers=[]))
bad('two-routers', lambda v: v['routers'].append(copy.deepcopy(profiles[1]['routers'][0])))
bad('three-routers', lambda v: v['routers'].extend(copy.deepcopy(legacy['routers'])))
bad('unknown-mode', lambda v: v.update(releaseMode='automatic'))
bad('single-direct-clients', lambda v: v.update(topology='direct-clients'))
bad('single-missing-topology', lambda v: v.pop('topology'))
bad('pair-one-router', lambda v: v.update(releaseMode='pair'))
bad('missing-mode-one-router', lambda v: v.pop('releaseMode'))
bad('self-peer', lambda v: v['routers'][0]['neighbors'][0].update(address='10.240.0.1'))
bad('duplicate-peer', lambda v: v['routers'][0]['neighbors'].append(v['routers'][0]['neighbors'][0]))
bad('overlapping-peer', lambda v: v['routers'][0]['neighbors'][0].update(address='10.240.1.1'))
bad('missing-link', lambda v: v['routers'][0].update(links=[]))
bad('extra-link', lambda v: v['routers'][0]['links'].append(v['routers'][0]['links'][0]))
bad('wrong-remote', lambda v: v['routers'][0]['links'][0].update(remoteAddress='10.240.1.2'))
bad('no-client', lambda v: v['routers'][0].update(neighbors=[{'address': '10.240.0.2', 'routeReflectorClient': False}]))
bad('raw-config', lambda v: v.update(frrConfig='router bgp 1'))
bad('floating-image', lambda v: v.update(image='example.invalid/rr:latest'))

pair = {**common, 'releaseMode': 'pair', 'routers': [copy.deepcopy(p['routers'][0]) for p in profiles]}
assert render_value(pair).returncode == 0
bad('cross-loopback', lambda v: v['routers'][1].update(loopback=v['routers'][0]['loopback']), pair)
bad('cross-router-id', lambda v: v['routers'][1].update(routerId=v['routers'][0]['routerId']), pair)
bad('cross-worker', lambda v: v['routers'][1].update(nodeSelector=v['routers'][0]['nodeSelector']), pair)
bad('cross-vlan', lambda v: v['routers'][1]['links'][0].update(vlanId=501), pair)
bad('cross-subnet', lambda v: v['routers'][1]['links'][0].update(localAddress='10.240.1.0/31', remoteAddress='10.240.1.1'), pair)
bad('cross-RR-as-client', lambda v: v['routers'][0]['neighbors'][-1].update(routeReflectorClient=True), pair)
for label, value in cases:
    assert render_value(value).returncode != 0, label
for files in [[common_file], ['deploy/values-rr01.yaml']]:
    assert helm(files, 'rr01').returncode != 0, 'incomplete layered values accepted'

# Direct invocation of the template preserves compatibility for the old files.
baseline = os.environ.get('FRR_BASELINE_CHART')
if baseline:
    for fixture in ['examples/documentation-values.json', 'examples/core-documentation-values.json', 'deploy/lab-values.yaml']:
        before = helm([fixture], target=baseline)
        after = helm([fixture])
        assert before.returncode == after.returncode == 0
        assert before.stdout == after.stdout, fixture + ': legacy render changed'
    print('Legacy three-fixture byte-identical renders=PASS')
print(f'Single-release layered lint/render/isolation/unchanged runtime/security/config/pair consistency=PASS negatives={len(cases) + 2}')
