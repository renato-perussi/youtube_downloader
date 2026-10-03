"""Seleciona settings pelo ENVIRONMENT."""

import os
from pathlib import Path as _Path

from dotenv import load_dotenv

_base = _Path(__file__).resolve().parent.parent.parent
load_dotenv(_base / '.env')

_ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')

if _ENVIRONMENT == 'prd':
    from .prd import *  # noqa: F403
elif _ENVIRONMENT == 'test':
    from .test import *  # noqa: F403
else:
    from .dev import *  # noqa: F403
