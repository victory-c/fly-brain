#!/usr/bin/env python3
"""Per-rider outcome counts of a `runs/ride.py --replay` trace, without the per-step trace.

A rider finished if it stayed upright for the whole ride. A ride that ended early counts as bailed if the bail
rule ended it (giant-fiber spikes; the rule is on unless the replay ran with --no-bail), as left the road if the
rider's final distance from the center line is beyond the off-road limit, and as a fall otherwise. With
--offroad 0 (a replay run without the off-road rule) every early end is a bail or a fall, and the summary also
counts the finishers whose final distance from the center line is beyond --road-m.

The trace does not record the replay's --offroad or --seconds, so pass the values the replay ran with.

    python3 tools/replay_summary.py TRACE.json OUT.json --offroad 3.5 --mode "replay of ..."
    python3 tools/replay_summary.py TRACE.json OUT.json --offroad 0 --mode "replay of ... without the off-road rule"
"""
import argparse
import json
import statistics


def outcome(result, seconds=15.0, offroad=3.5, road_m=3.5):
    up, lat = result["upright"], [abs(y) for y in result["lateral"]]
    bail = [bool(b) for b in result.get("bailed", [False] * len(up))]
    # ride.py adds the 10 ms control step in float32, so a full ride does not sum to exactly `seconds`
    # (15 s gives 15.000248, 60 s gives 59.995937). Half a step of slack still tells a full ride from one
    # that ended a step early.
    done = [u > seconds - 0.005 for u in up]
    out = {"riders": len(up), "finished": sum(done)}
    out["bailed"] = sum(1 for d, b in zip(done, bail) if b and not d)
    if offroad > 0:
        out["left_road"] = sum(1 for d, b, y in zip(done, bail, lat) if not d and not b and y > offroad)
        out["fell"] = len(up) - out["finished"] - out["bailed"] - out["left_road"]
    else:
        out["fell"] = len(up) - out["finished"] - out["bailed"]
        out["finished_beyond_road_m"] = sum(1 for d, y in zip(done, lat) if d and y > road_m)
        out["finished_within_road_m"] = out["finished"] - out["finished_beyond_road_m"]
        out["road_m"] = road_m
        fin = [y for d, y in zip(done, lat) if d]
        if fin:
            out["finished_lateral_median"] = statistics.median(fin)
            out["finished_lateral_max"] = max(fin)
    out["lateral_mean"] = sum(lat) / len(lat)
    out["lateral_median"] = statistics.median(lat)
    out["upright_mean"] = sum(up) / len(up)
    out["upright_max"] = max(up)
    out["offroad_m"] = offroad
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trace")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--seconds", type=float, default=15.0, help="the --seconds the replay ran with")
    ap.add_argument("--offroad", type=float, required=True,
                    help="the --offroad the replay ran with (0: no rule); the trace does not record it")
    ap.add_argument("--road-m", type=float, default=3.5, help="with --offroad 0: the limit to count finishers against")
    ap.add_argument("--mode", default=None, help="one line saying what was replayed (job id, log)")
    a = ap.parse_args()
    t = json.load(open(a.trace))
    s = {k: t[k] for k in ("mode", "state_names", "dn_names", "sense_names", "theta", "theta_names", "result") if k in t}
    if a.mode:
        s["mode"] = a.mode
    s["outcome"] = outcome(t["result"], a.seconds, a.offroad, a.road_m)
    print(json.dumps(s["outcome"]))
    if a.out:
        json.dump(s, open(a.out, "w"))


if __name__ == "__main__":
    main()
