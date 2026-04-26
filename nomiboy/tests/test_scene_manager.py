from dataclasses import dataclass, field
from nomiboy.core.scene_manager import SceneManager


@dataclass
class FakeScene:
    name: str
    enter_calls: list = field(default_factory=list)
    exit_calls: int = 0
    events: list = field(default_factory=list)
    updates: list = field(default_factory=list)
    draws: int = 0

    def on_enter(self, ctx):
        self.enter_calls.append(ctx)
    def on_exit(self):
        self.exit_calls += 1
    def handle_event(self, e):
        self.events.append(e)
    def update(self, dt):
        self.updates.append(dt)
    def draw(self, surf):
        self.draws += 1


def test_push_calls_on_enter():
    sm = SceneManager(ctx="ctx")
    s = FakeScene("a")
    sm.push(s)
    assert s.enter_calls == ["ctx"]
    assert sm.current is s


def test_push_calls_on_exit_for_previous():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b")
    sm.push(a); sm.push(b)
    assert a.exit_calls == 1
    assert sm.current is b


def test_pop_returns_to_previous():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b")
    sm.push(a); sm.push(b)
    sm.pop()
    assert sm.current is a
    assert b.exit_calls == 1


def test_replace_swaps_top():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b")
    sm.push(a); sm.replace(b)
    assert sm.current is b
    assert a.exit_calls == 1
    assert sm.depth == 1


def test_reset_to_clears_stack():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b"); c = FakeScene("c")
    sm.push(a); sm.push(b); sm.reset_to(c)
    assert sm.current is c
    assert sm.depth == 1
    assert a.exit_calls == 1 and b.exit_calls == 1


def test_event_routes_to_top():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b")
    sm.push(a); sm.push(b)
    sm.handle_event("e")
    assert b.events == ["e"]
    assert a.events == []


def test_pop_does_not_reenter_previous():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b")
    sm.push(a); sm.push(b)
    a.enter_calls.clear()  # push 時の enter を一度クリア
    sm.pop()
    assert a.enter_calls == []  # 再入場なし
