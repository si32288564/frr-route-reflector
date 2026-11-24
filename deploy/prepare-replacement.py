#!/usr/bin/env python3
"""Generate two reviewed RR snapshots from kubectl JSON; never contact a cluster."""
import json
from pathlib import Path
import sys


def prepare(source):
    text = source.read_text().lstrip()
    decoder = json.JSONDecoder()
    items = []
    while text:
        obj, end = decoder.raw_decode(text)
        items.extend(obj['items'] if obj.get('kind') == 'List' else [obj])
        text = text[end:].lstrip()
    priority = {'ConfigMap': 0, 'NetworkAttachmentDefinition': 1, 'Pod': 2}
    snapshots = []
    for rr in ['rr01', 'rr02']:
        name = 'rr-' + rr
        selected = [o for o in items if o['metadata']['name'] in [name, name + '-net1']]
        if sorted(o['kind'] for o in selected) != sorted(priority):
            raise ValueError(f'{name}: expected exactly one ConfigMap, NAD and Pod')
        for o in selected:
            metadata = o['metadata']
            metadata['namespace'] = 'frr-route-reflector'
            metadata.setdefault('labels', {})['app.kubernetes.io/managed-by'] = 'Helm'
            metadata.setdefault('annotations', {}).update({
                'meta.helm.sh/release-name': 'rr',
                'meta.helm.sh/release-namespace': 'frr-route-reflector'})
        selected.sort(key=lambda o: priority[o['kind']])
        snapshots.append((source.with_name(rr + '-replacement.json'),
                          {'apiVersion': 'v1', 'kind': 'List', 'items': selected}))
    # Validate both snapshots before writing either. This does not apply them.
    for destination, snapshot in snapshots:
        destination.write_text(json.dumps(snapshot, indent=2) + '\n')
        destination.chmod(0o600)
        print(f'Created {destination}')


if __name__ == '__main__':
    prepare(Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/rr-new.json'))
