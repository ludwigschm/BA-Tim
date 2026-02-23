from tabletop.state.controller import TabletopController, TabletopState


def _mk_plan(a, b):
    return {"vp1": a, "vp2": b}


def test_get_current_plan_swaps_hands_for_blocks_2_and_3():
    block1 = {"index": 1, "rounds": [_mk_plan((11, 12), (21, 22))]}
    block2 = {"index": 2, "rounds": [_mk_plan((31, 32), (41, 42))]}
    block3 = {"index": 3, "rounds": [_mk_plan((51, 52), (61, 62))]}
    block4 = {"index": 4, "rounds": [_mk_plan((71, 72), (81, 82))]}
    state = TabletopState(blocks=[block1, block2, block3, block4])
    controller = TabletopController(state)

    _, p1 = controller.get_current_plan()
    assert p1["vp1"] == (11, 12)
    assert p1["vp2"] == (21, 22)

    state.current_block_idx = 1
    _, p2 = controller.get_current_plan()
    assert p2["vp1"] == (41, 42)
    assert p2["vp2"] == (31, 32)

    state.current_block_idx = 2
    _, p3 = controller.get_current_plan()
    assert p3["vp1"] == (61, 62)
    assert p3["vp2"] == (51, 52)

    state.current_block_idx = 3
    _, p4 = controller.get_current_plan()
    assert p4["vp1"] == (71, 72)
    assert p4["vp2"] == (81, 82)


def test_setup_round_sets_block_starter_to_vp2_for_blocks_2_and_3():
    block2 = {"index": 2, "rounds": [_mk_plan((11, 12), (21, 22))]}
    state = TabletopState(blocks=[block2], current_block_idx=0, current_round_idx=0)
    controller = TabletopController(state)

    controller.setup_round()

    assert state.signaler == 2
    assert state.judge == 1
    assert state.first_player == 2
    assert state.second_player == 1
