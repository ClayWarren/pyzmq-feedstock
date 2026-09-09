import os
from pathlib import Path
import sys

import yaml

variant = yaml.safe_load(Path(sys.argv[1]).read_text())
if os.environ['PYZMQ_PLATFORM'] == 'win-arm64':
    variant['channel_sources'] = ['file:///C:/pyzmq-prerequisite,conda-forge']
Path('validation/selected.yaml').write_text(yaml.safe_dump(variant))
print(yaml.safe_dump(variant))
