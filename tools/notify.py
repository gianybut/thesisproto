"""Windows notification from the training queue:  py tools/notify.py <message words...>"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from watch_training import notify  # noqa: E402

msg = ' '.join(sys.argv[1:]) or 'Training queue'
print(f'Notification: {msg}', flush=True)
notify('OcuLubak training', msg)
