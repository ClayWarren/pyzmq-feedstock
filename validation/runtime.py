import json
import os
from pathlib import Path
import platform
import struct
import subprocess
import sys

import zmq
from zmq.backend.cython import _zmq

arm = os.environ['PYZMQ_PLATFORM'] == 'win-arm64'
expected = 0xAA64 if arm else 0x8664
prefix = Path(sys.prefix)
binaries = [Path(sys.executable), Path(_zmq.__file__)]
for pattern in ['*zmq*.dll', '*sodium*.dll']:
    matches = list((prefix / 'Library/bin').glob(pattern))
    assert matches, pattern
    binaries.extend(matches)
for binary in binaries:
    data = binary.read_bytes()
    offset = struct.unpack_from('<I', data, 0x3C)[0]
    assert data[offset:offset + 4] == b'PE\0\0', binary
    machine = struct.unpack_from('<H', data, offset + 4)[0]
    assert machine == expected, (binary, hex(machine))
    print(binary.name, hex(machine))
assert zmq.has('curve') and zmq.has('ipc')
assert not zmq.has('draft')
server_public, server_secret = zmq.curve_keypair()
client_public, client_secret = zmq.curve_keypair()
with zmq.Context() as context:
    with context.socket(zmq.PAIR) as server, context.socket(zmq.PAIR) as client:
        server.linger = client.linger = 0
        server.sndtimeo = server.rcvtimeo = 5000
        client.sndtimeo = client.rcvtimeo = 5000
        server.curve_secretkey = server_secret
        server.curve_publickey = server_public
        server.curve_server = True
        client.curve_publickey = client_public
        client.curve_secretkey = client_secret
        client.curve_serverkey = server_public
        port = server.bind_to_random_port('tcp://127.0.0.1')
        client.connect(f'tcp://127.0.0.1:{port}')
        client.send_multipart([b'arm64', b'encrypted request'])
        assert server.recv_multipart() == [b'arm64', b'encrypted request']
        server.send(b'ack')
        assert client.recv() == b'ack'
if arm:
    for name in ['zeromq', 'libsodium']:
        records = list((prefix / 'conda-meta').glob(f'{name}-*.json'))
        assert len(records) == 1, records
        record = json.loads(records[0].read_text())
        assert 'pyzmq-prerequisite' in record['url'], record['url']
        print(name, record['url'], record.get('sha256'))
print(platform.machine(), sys.version, 'GIL enabled:', sys._is_gil_enabled())
if os.environ['PYZMQ_ABI3'] == 'false':
    assert not sys._is_gil_enabled()
else:
    baseline = '3.14' if arm else '3.12'
    subprocess.run(['abi3audit', '-s', '-v', '--assume-minimum-abi3', baseline, _zmq.__file__], check=True)
print('Architecture, native dependency provenance, CURVE round-trip, and ABI checks passed')
