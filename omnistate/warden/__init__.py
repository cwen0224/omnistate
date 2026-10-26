# -*- coding: utf-8 -*-
"""
OMNISTATE Warden Package
"""

from omnistate.warden.warden import OmniStateWarden
from omnistate.warden.hooks import install_git_hooks

__all__ = ["OmniStateWarden", "install_git_hooks"]
