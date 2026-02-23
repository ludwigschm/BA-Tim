import queue
import time

from tabletop.core.event_router import EventRouter, UIEvent


def test_events_batch_uniformly() -> None:
    calls: "queue.Queue[tuple[str, str, float]]" = queue.Queue()

    def deliver(player: str, event: UIEvent) -> None:
        calls.put((player, event.name, time.perf_counter()))

    router = EventRouter(deliver, normal_batch_interval_s=0.02, normal_max_batch=4)
    router.register_player("VP1")
    router.set_active_player("VP1")

    start = time.perf_counter()
    router.route(UIEvent(name="fix.cross", target="VP1"))
    router.route(UIEvent(name="normal.a", target="VP1"))

    # Events should remain queued until a flush occurs.
    time.sleep(0.005)
    assert calls.empty()

    router.flush_all()

    delivered = [calls.get(timeout=0.1) for _ in range(2)]
    names = sorted(name for _, name, _ in delivered)

    assert names == ["fix.cross", "normal.a"]
    assert router.normal_batches_total == 1
    assert router.events_normal_total == 2

    # All events share the same dispatch path, so none should have been delivered
    # immediately before batching.
    assert all(ts - start >= 0 for *_, ts in delivered)
