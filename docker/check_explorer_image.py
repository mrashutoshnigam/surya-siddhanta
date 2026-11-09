"""Build output smoke check: nginx, local textures, both models and lesson data."""
import argparse
import json
import subprocess
import time
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', default='suryasiddhanta-explorer:check')
    args = parser.parse_args()
    container = subprocess.check_output(['docker', 'run', '--rm', '-d', '-p', '127.0.0.1::10000',
        '-e', 'PORT=10000', '-e', 'RENDER=true', args.image], text=True).strip()
    try:
        port = subprocess.check_output(['docker', 'port', container, '10000/tcp'], text=True).strip().rsplit(':', 1)[-1]
        base = f'http://127.0.0.1:{port}'
        for _ in range(60):
            try:
                with urlopen(base + '/api/health', timeout=2) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(1)
        else:
            raise RuntimeError('Container did not become healthy')
        with urlopen(base + '/universe') as response:
            assert b'<div id="root"' in response.read()
        with urlopen(base + '/api/explorer/catalog') as response:
            catalog = json.load(response)
        assert catalog['modern_available'], catalog['modern_unavailable_reason']
        texture = catalog['bodies']['Earth']['texture']
        with urlopen(base + texture) as response:
            assert response.headers['Content-Type'].startswith('image/')
        for model in ('historical', 'modern'):
            request = Request(base + '/api/explorer/snapshot', data=json.dumps(dict(model=model, instant='2025-01-01T00:00:00Z')).encode(), headers={'Content-Type': 'application/json'})
            with urlopen(request) as response:
                snapshot = json.load(response)
            assert snapshot['model'] == model and 'Mars' in snapshot['bodies']
        with urlopen(base + '/api/explorer/lessons/mars-retrograde') as response:
            assert len(json.load(response)['samples']) == 183
        print('PASS: container UI, local Earth texture, verified modern kernel, both snapshots and historical Mars lesson')
    finally:
        subprocess.run(['docker', 'logs', '--tail', '20', container], check=False)
        subprocess.run(['docker', 'stop', container], check=True, stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
