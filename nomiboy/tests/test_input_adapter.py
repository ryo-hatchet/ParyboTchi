from types import SimpleNamespace
import pygame
from nomiboy.core.input_adapter import InputAdapter, InputEvent, InputKind


def test_mouse_button_down_becomes_tap():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.MOUSEBUTTONDOWN, pos=(100, 50), button=1)
    out = ia.translate(pg_event)
    assert out == InputEvent(kind=InputKind.TAP, x=100, y=50)


def test_mouse_button_up_becomes_release():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.MOUSEBUTTONUP, pos=(10, 20), button=1)
    out = ia.translate(pg_event)
    assert out.kind == InputKind.RELEASE


def test_mouse_motion_with_button_pressed_becomes_drag():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.MOUSEMOTION, pos=(50, 60), buttons=(1, 0, 0))
    out = ia.translate(pg_event)
    assert out.kind == InputKind.DRAG


def test_mouse_motion_without_button_returns_none():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.MOUSEMOTION, pos=(50, 60), buttons=(0, 0, 0))
    out = ia.translate(pg_event)
    assert out is None


def test_finger_down_normalized_coords_scaled():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.FINGERDOWN, x=0.5, y=0.25)
    out = ia.translate(pg_event)
    assert out == InputEvent(kind=InputKind.TAP, x=240, y=80)


def test_unknown_event_returns_none():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_a)
    assert ia.translate(pg_event) is None
