"""
并行模块基础测试
"""
import pytest


def test_pool_import():
    from integrations.parallel.pool import ParallelPool
    assert ParallelPool is not None


def test_checkpoint_import():
    from integrations.parallel.checkpoint import CheckpointManager
    assert CheckpointManager is not None
