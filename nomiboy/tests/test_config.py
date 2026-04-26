from nomiboy import config


def test_screen_size_is_landscape_480x320():
    assert config.SCREEN_SIZE == (480, 320)


def test_target_fps_is_30():
    assert config.TARGET_FPS == 30


def test_is_pi_can_be_overridden_by_env(monkeypatch):
    monkeypatch.setenv("NOMIBOY_FORCE_PI", "1")
    assert config.detect_is_pi() is True


def test_fullscreen_follows_is_pi(monkeypatch):
    monkeypatch.setenv("NOMIBOY_FORCE_PI", "1")
    monkeypatch.delenv("NOMIBOY_FULLSCREEN", raising=False)
    assert config.detect_fullscreen() is True


def test_fullscreen_can_be_overridden(monkeypatch):
    monkeypatch.setenv("NOMIBOY_FORCE_PI", "1")
    monkeypatch.setenv("NOMIBOY_FULLSCREEN", "0")
    assert config.detect_fullscreen() is False
