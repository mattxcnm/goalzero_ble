"""Goal Zero device definitions and registry."""
from .base import GoalZeroDevice
from .yeti500 import Yeti500Device
from .alta80 import Alta80Device

__all__ = ["GoalZeroDevice", "Yeti500Device", "Alta80Device"]
