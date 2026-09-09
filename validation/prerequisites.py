import hashlib
from pathlib import Path
import tarfile
from compression import zstd

destination = Path('C:/pyzmq-prerequisite/win-arm64')
destination.mkdir(parents=True, exist_ok=True)
sodium = 'libsodium-1.0.22-hb7845dc_3.conda'
raw = Path('C:/pyzmq-download/libsodium.tar.zst')
with raw.open('rb') as stream, zstd.open(stream) as decoded:
    with tarfile.open(fileobj=decoded, mode='r|') as archive:
        for member in archive:
            if Path(member.name).name == sodium and member.isfile():
                (destination / sodium).write_bytes(archive.extractfile(member).read())
expected = {
    sodium: '7d398295dbb2cd046983401cbf6e68998b80a4f413b279ea2ddce6b0f95e9464',
    'zeromq-4.3.5-h3f841bf_11.conda': 'd72baca2b7f86d66865a5917d61e5c023d867e4cd66b603411d09fa89a81eafb',
}
for name, digest in expected.items():
    actual = hashlib.sha256((destination / name).read_bytes()).hexdigest()
    assert actual == digest, (name, actual)
    print(name, actual)
