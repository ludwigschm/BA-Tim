import os
import sys
from pathlib import Path

os.environ.setdefault("KIVY_WINDOW", "mock")
os.environ.setdefault("KIVY_GRAPHICS", "mock")
os.environ.setdefault("KIVY_AUDIO", "mock")
os.environ.setdefault("KIVY_TEXT", "mock")

import pytest
pytest.importorskip("kivy")
from kivy.properties import BooleanProperty
from kivy.uix.floatlayout import FloatLayout

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tabletop.data.blocks import load_blocks
from tabletop.state.controller import TabletopController, TabletopState
import tabletop.tabletop_view as tabletop_view
from tabletop.tabletop_view import TabletopRoot


class DummyPauseCover(FloatLayout):
    disabled = BooleanProperty(True)


def _make_practice_state(blocks):
    practice_block = blocks[0]
    practice_rounds = practice_block.get("rounds") or []
    state = TabletopState(blocks=blocks)
    state.current_block_idx = 0
    state.current_block_info = practice_block
    if practice_rounds:
        state.current_round_idx = len(practice_rounds) - 1
        state.current_block_total_rounds = len(practice_rounds)
        state.round_in_block = len(practice_rounds)
    state.in_block_pause = False
    state.pause_message = ""
    state.session_finished = False
    return state


def test_practice_block_transition_triggers_visible_pause(monkeypatch):
    blocks = load_blocks()
    assert blocks, "expected block configuration to be available"
    assert blocks[0].get("practice"), "first block should be the practice block"
    practice_rounds = blocks[0].get("rounds") or []
    assert practice_rounds, "practice block must contain rounds"

    state = _make_practice_state(blocks)
    controller = TabletopController(state)

    original_prepare = TabletopController.prepare_next_round
    captured = {}

    def patched_prepare(self, *, start_immediately: bool = False):
        result = original_prepare(self, start_immediately=start_immediately)
        captured["result"] = result
        self.state.pause_message = ""
        return result

    monkeypatch.setattr(TabletopController, "prepare_next_round", patched_prepare)
    monkeypatch.setattr(tabletop_view, "resolve_background_texture", lambda: None)

    view = TabletopRoot(controller=controller, state=state)
    pause_cover = DummyPauseCover()
    pause_cover.opacity = 0
    pause_cover.disabled = True
    view.pause_cover = pause_cover
    view.ids["pause_cover"] = pause_cover

    view.prepare_next_round(start_immediately=True)

    assert "result" in captured, "controller result should be captured"
    result = captured["result"]
    assert result.in_block_pause is True
    assert view.in_block_pause is True
    assert pause_cover.opacity == 1
    assert pause_cover.disabled is False
    assert pause_cover.parent is view
    expected_message = (
        "Dieser Block ist vorbei. Nehmen Sie sich einen Moment zum Durchatmen.\n"
        "Wenn Sie bereit sind, klicken Sie auf Weiter."
    )
    assert view.pause_message == expected_message


def test_pause_overlay_remains_attached_after_multiple_toggles(monkeypatch):
    blocks = load_blocks()
    state = _make_practice_state(blocks)
    controller = TabletopController(state)
    monkeypatch.setattr(tabletop_view, "resolve_background_texture", lambda: None)

    view = TabletopRoot(controller=controller, state=state)
    pause_cover = DummyPauseCover()
    pause_cover.opacity = 0
    pause_cover.disabled = True
    view.pause_cover = pause_cover
    view.ids["pause_cover"] = pause_cover
    view.add_widget(pause_cover)

    for _ in range(3):
        view.in_block_pause = True
        view.session_finished = False
        view.pause_message = "Pause"
        view.update_pause_overlay()
        assert pause_cover.opacity == 1
        assert pause_cover.disabled is False
        assert pause_cover.parent is view

        view.in_block_pause = False
        view.session_finished = False
        view.update_pause_overlay()
        assert pause_cover.opacity == 0
        assert pause_cover.disabled is True
        assert pause_cover.parent is view


def test_pause_overlay_uses_object_property_when_id_proxy_is_invalid(monkeypatch):
    blocks = load_blocks()
    state = _make_practice_state(blocks)
    controller = TabletopController(state)
    monkeypatch.setattr(tabletop_view, "resolve_background_texture", lambda: None)

    view = TabletopRoot(controller=controller, state=state)
    pause_cover = DummyPauseCover()
    pause_cover.opacity = 0
    pause_cover.disabled = True
    view.pause_cover = pause_cover
    view.add_widget(pause_cover)

    class BrokenProxy:
        @property
        def opacity(self):
            raise ReferenceError("dangling weak proxy")

    view.ids["pause_cover"] = BrokenProxy()
    view.in_block_pause = True
    view.session_finished = False
    view.pause_message = "Pause"

    view.update_pause_overlay()

    assert pause_cover.opacity == 1
    assert pause_cover.disabled is False
    assert pause_cover.parent is view


def test_pause_overlay_inactive_state_has_no_hitbox_and_cancels_zorder_events(monkeypatch):
    blocks = load_blocks()
    state = _make_practice_state(blocks)
    controller = TabletopController(state)
    monkeypatch.setattr(tabletop_view, "resolve_background_texture", lambda: None)

    view = TabletopRoot(controller=controller, state=state)
    pause_cover = DummyPauseCover()
    pause_cover.opacity = 0
    pause_cover.disabled = True
    view.pause_cover = pause_cover
    view.ids["pause_cover"] = pause_cover
    view.add_widget(pause_cover)

    view.in_block_pause = True
    view.pause_message = "Pause"
    view.update_pause_overlay()
    assert view._pause_zorder_ev0 is not None
    assert view._pause_zorder_ev1 is not None

    view.in_block_pause = False
    view.session_finished = False
    view.update_pause_overlay()

    assert pause_cover.opacity == 0
    assert pause_cover.disabled is True
    assert pause_cover.size_hint == (None, None)
    assert tuple(pause_cover.size) == (0, 0)
    assert tuple(pause_cover.pos) == (-100000, -100000)
    assert view._pause_zorder_ev0 is None
    assert view._pause_zorder_ev1 is None
