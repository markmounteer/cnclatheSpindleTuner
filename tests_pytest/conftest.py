"""Shared pytest fixtures for unit-style tests."""

import sys
from pathlib import Path

import pytest

# Ensure repository root is on the import path when running pytest directly
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hal_interface import HalInterface


@pytest.fixture
def mock_hal() -> HalInterface:
    """Provide a HAL interface forced into mock mode for deterministic testing."""
    return HalInterface(mock=True)
