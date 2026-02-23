from pathlib import Path
from types import SimpleNamespace

from tabletop.logging.round_csv import write_round_log
from tabletop.state.controller import TabletopController, TabletopState


class _App(SimpleNamespace):
    def format_signal_choice(self, value):
        return value

    def format_decision_choice(self, value):
        return value

    def get_current_plan(self):
        return None


def _build_app(tmp_path: Path, start_mode: str, block_index: int) -> _App:
    state = TabletopState(start_mode=start_mode)
    controller = TabletopController(state)
    return _App(
        controller=controller,
        start_mode=start_mode,
        round_log_path=tmp_path / "round.csv",
        current_round_has_stake=False,
        current_block_info={"index": block_index},
        round_in_block=1,
        next_block_preview=None,
        role_by_physical={1: 1, 2: 2},
        first_player=1,
        session_id="s1",
    )


def test_round_log_condition_for_start_mode_c(tmp_path: Path):
    app = _build_app(tmp_path, "C", 1)
    write_round_log(app, "P1", "start_click", {}, 1)
    assert app.round_log_buffer[-1]["Bedingung"] == "unmasked"



def test_round_log_condition_for_start_mode_t(tmp_path: Path):
    app = _build_app(tmp_path, "T", 1)
    write_round_log(app, "P1", "start_click", {}, 1)
    assert app.round_log_buffer[-1]["Bedingung"] == "masked"
