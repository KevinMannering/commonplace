"""Tests for centralized model routing config."""

from __future__ import annotations

import importlib


def test_config_exposes_fast_and_smart_models() -> None:
    from commonplace.config import COMMONPLACE_CONFIG, FAST_MODEL, SMART_MODEL

    assert COMMONPLACE_CONFIG.fast_model == FAST_MODEL
    assert COMMONPLACE_CONFIG.smart_model == SMART_MODEL


def test_config_reads_model_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("FAST_MODEL", "fast-test-model")
    monkeypatch.setenv("SMART_MODEL", "smart-test-model")

    import commonplace.config as config_module

    reloaded = importlib.reload(config_module)

    assert reloaded.FAST_MODEL == "fast-test-model"
    assert reloaded.SMART_MODEL == "smart-test-model"
    assert reloaded.COMMONPLACE_CONFIG.fast_model == "fast-test-model"
    assert reloaded.COMMONPLACE_CONFIG.smart_model == "smart-test-model"

    monkeypatch.delenv("FAST_MODEL", raising=False)
    monkeypatch.delenv("SMART_MODEL", raising=False)
    importlib.reload(config_module)
