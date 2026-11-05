"""Checks that run without pytest, so the CLI can prove itself anywhere."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

from . import cli as cli_module
from . import demo, plan
from .audit import causality_breaks, coverage, disagreements, monotone, order_by_wall
from .clock import ClockError, HybridClock, ManualWall
from .stamp import Stamp, StampError, parse_stamp
from .world import World, WorldError

CHECKS = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global CHECKS, FAILED
    CHECKS += 1
    if condition:
        return
    FAILED += 1
    print(f"FAIL {name}" + (f": {detail}" if detail else ""))


def refuses(name: str, kind, action) -> None:
    try:
        action()
    except kind as error:
        check(name, True)
        check(f"{name} explains itself", len(str(error)) > 10, str(error))
    except Exception as error:
        check(name, False, f"raised {type(error).__name__}: {error}")
    else:
        check(name, False, "nothing was raised")


def quiet(argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli_module.main(argv)
    except SystemExit as exited:
        code = int(exited.code or 0)
    return code, out.getvalue()


def run() -> None:
    stamp = Stamp(1_700_000_000_000, 3, "a")
    check("a stamp round trips through its text", parse_stamp(stamp.text()) == stamp)
    check("text sorts with the stamp",
          Stamp(10, 1, "a").text() < Stamp(10, 2, "a").text())
    check("the node breaks a tie", Stamp(1, 0, "a") < Stamp(1, 0, "b"))
    check("the key is physical, logical, node", Stamp(1, 2, "c").key() == (1, 2, "c"))
    refuses("a negative physical time is refused", StampError, lambda: Stamp(-1))
    refuses("a boolean is not a stamp", StampError, lambda: Stamp(True))
    refuses("a node name cannot hold a pipe", StampError, lambda: Stamp(1, 0, "a|b"))
    refuses("unparsable text is refused", StampError, lambda: parse_stamp("nope"))

    wall = ManualWall(1_000)
    clock = HybridClock("a", wall_ms=wall.now)
    first = clock.now()
    second = clock.now()
    check("two events in one millisecond differ", first < second)
    check("the counter did the work", second.logical == first.logical + 1)
    wall.set(600)
    third = clock.now()
    check("a wall that steps back does not move the stamp", third > second)
    check("the stamp kept the old physical time", third.physical_ms == second.physical_ms)
    later_wall = ManualWall(1_000)
    later = HybridClock("c", wall_ms=later_wall.now)
    later.now()
    later_wall.advance(5)
    fourth = later.now()
    check("an advancing wall makes a new millisecond", fourth.physical_ms == 1_005)
    check("a new millisecond resets the counter", fourth.logical == 0)

    remote = Stamp(5_000, 0, "b")
    received = clock.receive(remote)
    check("a receipt is later than the send", received > remote)
    check("the receipt adopts the remote millisecond", received.physical_ms == 5_000)
    check("skew is measured against the wall", clock.skew_ms() == 5_000 - wall.now())
    check("a clock that needed help is drifting", clock.is_drifting())
    strict = HybridClock("d", wall_ms=lambda: 1_000, max_skew_ms=10)
    strict.receive(Stamp(5_000, 0, "a"))
    refuses("a bound refuses too much skew", ClockError, strict.check_skew)
    bounded = HybridClock("b", wall_ms=lambda: 1_000, max_skew_ms=10_000)
    bounded.receive(Stamp(5_000, 0, "a"))
    bounded.check_skew()
    check("a bound that is wide enough says nothing", True)
    refuses("a clock needs a node name", ClockError, lambda: HybridClock("", wall_ms=lambda: 0))
    refuses("receiving a non-stamp is refused", ClockError, lambda: clock.receive(5))
    refuses("the wall cannot advance backwards", ClockError, lambda: wall.advance(-1))

    world = World({"a": 500, "b": 0}, start_ms=1_700_000_000_000)
    world.tick(0)
    sent, got = world.send("a", "b", "ping")
    check("the world stamps a message later on receipt", sent < got)
    check("the world records no violation", world.violations() == [])
    check("the world counts one message", len(world.messages) == 1)
    check("the fast node runs 500 ms ahead", world.clock("a").physical_ms
          - world.wall("a").now() >= 0)
    check("the slow node is skewed by the receipt", world.clock("b").skew_ms() == 500)
    check("as_dict carries the nodes", world.as_dict()["nodes"]["b"]["receives"] == 1)
    check("the report names the columns",
          world.reports()[0].split() == ["node", "physical_ms", "logical", "wall_ms", "skew_ms"])
    refuses("an unknown node is refused", WorldError, lambda: world.clock("z"))
    refuses("a world needs a node", WorldError, lambda: World({}))
    refuses("time does not run backwards", WorldError, lambda: world.tick(-1))
    refuses("a step back must be positive", WorldError, lambda: world.step_back("a", 0))

    naive = demo.stories()[2]
    check("the wall order disagrees with the stamp order", naive.held)
    check("the demo counts its inversions",
          any(line.startswith("inversions between the two orders:")
              and not line.endswith(": 0") for line in naive.lines))
    world2 = World({"a": 0, "b": 0}, start_ms=1_000)
    world2.tick(0)
    world2.local("a")
    world2.tick(10)
    world2.local("b")
    check("a consistent world has no inversions", disagreements(world2.entries) == [])
    check("a consistent world is monotone", monotone(world2.entries))
    check("causality breaks are found", causality_breaks([(Stamp(2_000, 0, "a"),
                                                           Stamp(1_000, 0, "b"))]) != [])
    check("no break when the receipt is later",
          causality_breaks([(Stamp(2_000, 0, "a"), Stamp(2_000, 1, "b"))]) == [])
    check("coverage names every node", set(coverage(world2)) == {"a", "b"})
    check("the wall order sorts by wall time",
          next(entry.node for entry in order_by_wall(world2.entries)) == "a")

    for story in demo.stories():
        check(f"demo story holds: {story.title}", story.held)
    rendered = demo.render()
    check("the demo prints every story", rendered.count("-> holds") == len(demo.stories()))
    check("the demo claims nothing broken", "BROKEN" not in rendered)

    events = plan.load(Path(__file__).resolve().parent.parent.parent / "fixtures" / "handoff.jsonl")
    check("a plan file loads", len(events) == 6)
    built = plan.execute(events, start_ms=1_700_000_000_000)
    check("a plan runs", len(built.messages) == 1)
    code, out = quiet(["plan", "--plan", str(
        Path(__file__).resolve().parent.parent.parent / "fixtures" / "handoff.jsonl")])
    check("the plan command exits zero", code == 0, out)
    check("the plan command reports no breaks", "causal breaks 0" in out)
    code, out = quiet(["plan", "--plan", str(
        Path(__file__).resolve().parent.parent.parent / "fixtures" / "handoff.jsonl"),
        "--max-skew", "100"])
    check("a skew past the bound exits one", code == 1, str(code))
    code, _ = quiet(["stamp", "000001700000000000:0000003@a"])
    check("the stamp command exits zero", code == 0)
    code, _ = quiet(["stamp", "nope"])
    check("a broken stamp exits two", code == 2, str(code))
    code, out = quiet(["demo"])
    check("the demo command exits zero", code == 0, str(code))




def main() -> int:
    run()
    if FAILED:
        print(f"selftest: {FAILED} check(s) failed out of {CHECKS}")
        return 1
    print(f"selftest: {CHECKS} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
