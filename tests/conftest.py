"""Pytest configuration and fixtures."""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock policyengine_us if not available
try:
    import policyengine_us
except ImportError:
    sys.modules['policyengine_us'] = MagicMock()
    sys.modules['policyengine_core'] = MagicMock()
    sys.modules['policyengine_core.taxbenefitsystems'] = MagicMock()
    sys.modules['policyengine_core.api'] = MagicMock()
    sys.modules['policyengine_core.api.microsimulation'] = MagicMock()
    sys.modules['openfisca_core'] = MagicMock()
    sys.modules['openfisca_core.entities'] = MagicMock()
    sys.modules['openfisca_core.entities.entity'] = MagicMock()

# Mock Microsimulation class
mock_microsim = MagicMock()
mock_microsim.return_value.calculate.return_value = [5000.0]
sys.modules['policyengine_us'].Microsimulation = mock_microsim