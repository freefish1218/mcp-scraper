"""
补丁模块
包含对第三方库的补丁，用于扩展或修改其功能。
"""

# 自动应用补丁
from .playwright_patch import apply_playwright_patch
from .scrapling_patch import apply_patch


__all__ = ["apply_playwright_patch", "apply_patch"]
