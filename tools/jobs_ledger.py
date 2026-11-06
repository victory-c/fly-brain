"""Write JOBS.md: every Slurm job run from this repo, with its exact command line, from sacct.

usage: python3 tools/jobs_ledger.py [--since 2026-09-26]

Slurm keeps each job's submit line (sbatch ... / srun ...), so srun jobs that left no log file are
recorded too. Jobs that fed Python on stdin (`python -`) have their script in logs/inline/<jobid>.py
when it could be recovered. NOTES below adds one line of context where the command does not say it.
"""
import argparse
import getpass
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["JobID", "JobName", "State", "Start", "Elapsed", "AllocTRES", "WorkDir", "SubmitLine"]

NOTES = {
    "36053": "probe: node, GPU, python and torch on the cluster",
    "36059": "probe: CPU affinity and torch threads",
    "36073": "probe: GPU name and driver",
    "36074": "probe: CUDA version",
    "36075": "build venv-cuda (torch cu121) and check the GPU",
    "36076": "failed: started in the repo root, where there is no brain package",
    "36077": "tests.test_sim on CPU after the GPU port",
    "36078": "CPU vs GPU benchmark -> results/bench_gpu.json",
    "36079": "probe: GPU memory (failed)",
    "36080": "failed: relative venv path",
    "36081": "failed: relative venv path",
    "36082": "512-trial GPU batch -> results/bench_gpu_512.json",
    "36083": "bike + closed-loop sanity tests",
    "36084": "interface smoke test: senses, readout, decoder on a toy peloton",
    "36085": "open loop: brain in the loop, prior decoder, no steering",
    "36086": "PD rider without a brain (oracle)",
    "36087": "passenger screen, pilot",
    "36088": "which sensory population saturates the brain (odour goal diagnosis)",
    "36089": "passenger screen -> results/screen.json, screen_samples.npz",
    "36090": "failed: wrong path to screen_samples.npz",
    "36091": "CEM learning, sigma0 0.3 -> results/ride.json",
    "36092": "CEM learning, sigma0 0.1 -> results/ride_b.json (the best decoder)",
    "36093": "cancelled, rerun on CPU as 36094",
    "36094": "replay of ride.json -> results/ride_trace.json",
    "36095": "replay of the best decoder -> results/ride_b_trace.json (the /ride/ demo)",
    "36101": "cancelled: is a weak odour goal stable?",
    "36102": "cancelled: HS lane cue check",
    "36103": "lane keeping: screen with HS lane cue -> CEM -> replay",
    "36487": "hands-off on the road (5.5 m/s, 5 Nm), GPU copy queued while the GPUs were busy",
    "36488": "PD rider on the road (5.5 m/s, 5 Nm) -> results/ride_oracle_trace.json (/ride/oracle)",
    "36490": "hands-off on the road (5.5 m/s, 5 Nm), CPU -> results/ride_pilot_road_trace.json (/ride/open-loop)",
    "36492": "replay on the road with the whole brain recorded, CPU -> results/ride_road_trace.json + ride_road_brain.npz (/ride/)",
    "36493": "lane keeping round 2 (lane-next.sbatch): batch centring + look-ahead/gain replays, operating-point CEM, held-out seed 59 -> results/lane/",
    "36494": "/ride/ page replays with the brain recorded: round-2 decoder and hands-off (ride-page.sbatch)",
    "36521": "learning to ride from a blank decoder, every attempt recorded (ride-attempts.sbatch) -> results/attempts/ (the attempts page)",
    "36533": "rewrite: build brain.npz with brain/connectome.py (identical edges and weights to the old build)",
    "36535": "rewrite: old engine vs new engine on sugar/bitter, same seed -> identical spikes",
    "36538": "rewrite: w_syn scale sweep vs Shiu's FlyWire feeding curve, first grid (superseded by 36539)",
    "36539": "rewrite: w_syn scale sweep vs Shiu's FlyWire feeding curve -> results/calibrate_wsyn.json, scale 0.47",
    "36540": "rewrite: replay of the 3D-page decoder (results/lane/cem_mu.json) on the new engine: 10.0 s upright (old 18.1 s)",
    "36541": "rewrite: Fly Brain Live data, Shiu's 10 stimulation experiments (export_dashboard + pack_dashboard)",
    "36542": "rewrite: same replay at scale 0.45: 12.1 s upright, so the Brian2 rule fixes, not the scale, break the old decoder",
    "36543": "rewrite: the bike relearned on the new engine (ride-relearn.sbatch): 37 generations, 1,776 attempts -> results/relearn/ (the /ride/ page)",
    "36546": "cancelled: wrong decoder path",
    "36547": "rewrite: /ride/ page replays of the relearned decoder (results/relearn/cem_mu.json) and hands-off, brains recorded",
    "36554": "rewrite: graph engine benchmark, stopped (buffers sized too large)",
    "36555": "rewrite: the bike relearned again with the new display regions recorded (ride-relearn.sbatch, search only) -> results/relearn/",
    "36626": "rewrite: /ride/ page replays of the relearned decoder and hands-off, brains recorded",
    "36627": "rewrite: dashboard export, all tests on GPU, graph engine benchmark",
    "37926": "after the Debian 13 upgrade: re-run of balance-gate generation 0; ran on CPU because CUDA does not initialise (nvidia_uvm not loaded), timed out",
    "37927": "30-brain pre-test ladder for R3.5/R4/R5, on CPU with a GPU allocated; cancelled and resubmitted per rung without the GPU",
    "37928": "30-brain pre-test of R0, R2, R3 at 0.47 (CPU) -> results/rungs/pretest_*_b30_w0.47.json",
    "37929": "per-brain passenger screens; cancelled, wait for the GPU",
    "37936": "30-brain pre-test of R4 at 1.5 and 2.0 (CPU); cancelled during the 2.0 haltere probe (8 million spikes/s)",
    "37937": "30-brain pre-test of R3.5 at 0.6 to 2.0 (CPU)",
    "37938": "pilot ride on R3 (balance gate unchanged, 4.5 m/s, seed 201) on CPU, 48 threads -> results/rungs/r3_s1_cpu/; generations 0 to 13, then cancelled so the search continues on the C kernel",
    "37939": "per-brain passenger screens on CPU; held, then cancelled to leave the cores to the rides",
    "37940": "30-brain pre-test of R5 at 0.47 to 2.0 (CPU): passes at 2.0",
    "37941": "fine scan of R4 above 1.5 (CPU): runaway at 1.6; 1.7 and 1.8 cancelled",
    "37942": "fine scan of R3.5 between 0.47 and 0.6 (CPU): no signal where the rate matches the real brain's",
    "37943": "pilot ride on R4 at scale 1.5; cancelled, the network runs away within 0.4 s of riding (4 million spikes/s per brain)",
    "37944": "R4 closed-loop stability: the reference replay at scales 1.0 to 1.4 -> riding rate matches the real brain's at 1.2",
    "37945": "pilot ride on R4 at scale 1.2 (balance gate unchanged, 4.5 m/s, seed 201) on CPU, 40 threads -> results/rungs/r4_s1_w1.2_cpu/",
    "37946": "continuation of 37938 (runs/ride.py --resume), the first job on the C kernel: generations 14 and 15 in 681 s and 705 s; cancelled to hand over to 37949, which stops at 60 generations",
    "37947": "30-brain pre-test of R4 at 1.2, 1.3 and the rest of the ladder (CPU)",
    "37948": "pilot ride on R3, second CEM seed (202), on CPU, 32 threads -> results/rungs/r3_s1_cpu/v4.5_s202/; generations 0 to 8, then cancelled so the search continues on the C kernel",
    "37949": "second continuation of the R3 pilot ride, seed 201: generations 16 and 17 on 48 threads (2,802 s and 1,064 s, sharing the node with the screens); replaced by 38043 on 32 threads",
    "37950": "continuation of the R4 pilot ride at scale 1.2 (stops at 60 generations)",
    "37951": "second continuation of the R4 pilot ride at scale 1.2",
    "37952": "continuation of the R3 pilot ride, seed 202: generations 9 to 59 at 507 to 1,502 s each; the search ends at 60 generations with 11.14 s upright and 52% finishing in the last one",
    "37953": "second continuation of the R3 pilot ride, seed 202: found the 60 generations done and stopped after 7 s",
    "38035": "per-brain passenger screens of R0, R1, R2, R3 on CPU with the C kernel -> results/rungs/screens/",
    "38043": "last continuation of the R3 pilot ride, seed 201, on 32 threads: generations 18 to 59 at 436 to 504 s each; the search ends at 60 generations with 11.48 s upright and 42% finishing in the last one",
    "38036": "pilot of the Track A readout on the real wiring: top-8 screened descending neurons, 4.5 m/s, seed 201, 30 generations (CPU, 32 threads); ends at 7.21 s upright with 6% finishing, most rides ending off the road",
    "38077": "replay of the top-8 pilot's final CEM mean, 48 riders x 15 s, seed 201: 9.04 s upright, 7 finish, 41 leave the road, none falls -> results/rungs/r0/top8/v4.5_s201/replay_mu_summary.json",
    "38078": "pilot of the Track A readout on the real wiring: top-32 screened descending neurons, 4.5 m/s, seed 201, 30 generations (CPU, 32 threads); ends at 6.24 s upright with no rider finishing (5.34 to 7.66 s from generation 4 on), most rides ending off the road",
    "38079": "pilot of the random-k control on the real wiring: 8 descending neurons drawn at random from the screen's pool (readout seed 0), 4.5 m/s, seed 201, 30 generations (CPU, 32 threads); ends at 4.06 s upright with no rider finishing, below the hands-off bike",
    "38037": "pilot of the sensory-bypass readout on the real wiring, 4.5 m/s, seed 201, 30 generations (CPU, 32 threads); ends at 13.92 s upright with 77% finishing",
    "38082": "hands-off replay (blank steering) without the off-road rule, 48 riders x 15 s, seed 201: 8.65 s upright, 46 fall, 2 still upright at 15 s -> results/rungs/r0/handsoff/v4.5_s201/replay_noroad_summary.json",
    "38083": "replay of the top-8 pilot's final CEM mean without the off-road rule, 48 riders x 15 s, seed 201: all 48 upright for 15 s, 34 of them more than 3.5 m from the center line at the end -> results/rungs/r0/top8/v4.5_s201/replay_mu_noroad_summary.json",
    "38084": "hands-off replay (blank steering) with the off-road rule, 48 riders x 15 s, seed 201: 5.38 s upright, 41 leave the road, 7 fall, none finishes -> results/rungs/r0/handsoff/v4.5_s201/replay_road_summary.json",
    "38085": "bypass search at synapse scale 0, meant as a bypass with no brain; cancelled after a minute: scale 0 also zeroes the Poisson kick (w_syn x f_poi), so the driven neurons were silent. Replaced by the bypass0 readout (--no-synapses)",
    "38086": "the bypass pilot repeated with every synapse switched off (bypass0, runs/ride.py --no-synapses), 4.5 m/s, seed 201, 30 generations (CPU, 16 threads): ends at 13.91 s upright with 81% finishing, never more than 0.085 s from the bypass pilot (38037) in any generation -> results/rungs/r0/bypass_nosyn/",
    "38081": "replay of the bypass pilot's final CEM mean, 48 riders x 15 s, seed 201: all 48 ride the full 15 s, none leaves the road -> results/rungs/r0/bypass/v4.5_s201/replay_mu_summary.json",
    "38038": "pilot ride on R1 (balance gate unchanged, 4.5 m/s, seed 201, 60 generations) on CPU, 91 to 565 s a generation; ends at 7.01 s upright with 8% finishing (R0: 13.71 and 11.89 s) -> results/rungs/r1_s1_cpu/",
    "38039": "pilot ride on R2 (balance gate unchanged, 4.5 m/s, seed 201, 60 generations) on CPU -> results/rungs/r2_s1_cpu/",
    "38087": "first try of the sign-flip count of the R1 draw (srun): the script was in the login VM's /tmp, which the node does not see",
    "38088": "sign-flip count, second try: bike package not on the path",
    "38089": "sign-flip count, third try: stopped on a missing type name",
    "38090": "sign-flip count, fourth try: wrong side column",
    "38091": "sign-flip count of the R1 draw (scratch script; redone as tools/r1_flips.py in job 38102)",
    "38092": "replay of the R1 pilot's final CEM mean, 48 riders x 15 s, seed 201: 10.12 s upright, 10 finish, 37 leave the road, 1 falls -> results/rungs/r1_s1_cpu/v4.5_s201/replay_mu_summary.json",
    "38093": "replay of the gate's final CEM mean (R0, seed 201) on CPU, 48 riders x 15 s, seed 201: 14.79 s upright, 46 finish, 2 leave the road, none falls -> results/gate/v4.5_s201/replay_mu_summary.json",
    "38094": "replay of the R3 pilot's final CEM mean (seed 201), 48 riders x 15 s, seed 201: 12.25 s upright, 22 finish, 26 leave the road, none falls -> results/rungs/r3_s1_cpu/v4.5_s201/replay_mu_summary.json",
    "38095": "replay of the gate's final CEM mean (R0, seed 202) on CPU, 48 riders x 15 s, seed 201: 14.52 s upright, 44 finish, 4 leave the road, none falls -> results/gate/v4.5_s202/replay_mu_summary.json",
    "38096": "replay of the R3 pilot's final CEM mean (seed 202), 48 riders x 15 s, seed 201: 12.73 s upright, 28 finish, 17 leave the road, 3 fall -> results/rungs/r3_s1_cpu/v4.5_s202/replay_mu_summary.json",
    "38097": "replay of the R1 pilot's final CEM mean without the off-road rule: 47 of 48 upright for 15 s, 35 of them more than 3.5 m from the center line, 1 falls -> results/rungs/r1_s1_cpu/v4.5_s201/replay_mu_noroad_summary.json",
    "38098": "replay of the gate's final CEM mean (R0, seed 201) without the off-road rule: all 48 upright for 15 s, 1 more than 3.5 m from the center line -> results/gate/v4.5_s201/replay_mu_noroad_summary.json",
    "38099": "replay of the R3 pilot's final CEM mean (seed 201) without the off-road rule: all 48 upright for 15 s, 18 more than 3.5 m from the center line -> results/rungs/r3_s1_cpu/v4.5_s201/replay_mu_noroad_summary.json",
    "38100": "replay of the gate's final CEM mean (R0, seed 202) without the off-road rule: all 48 upright for 15 s, 3 more than 3.5 m from the center line -> results/gate/v4.5_s202/replay_mu_noroad_summary.json",
    "38101": "replay of the R3 pilot's final CEM mean (seed 202) without the off-road rule: 44 of 48 upright for 15 s, 10 of them more than 3.5 m from the center line, 4 fall -> results/rungs/r3_s1_cpu/v4.5_s202/replay_mu_noroad_summary.json",
    "38102": "tools/r1_flips.py on the R1 draw (srun, 2 threads): where the sign flips fall -> results/rungs/r1_s1_cpu/sign_flips.json",
    "38106": "second R1 rewiring draw (brain/variants.py r1 --seed 2, srun) -> results/variants/r1_s2.npz",
    "38107": "pilot ride on R1, rewiring draw 2 (balance gate unchanged, 4.5 m/s, seed 201, 60 generations) on CPU, started when the random-8 pilot (38079) ended -> results/rungs/r1_s2_cpu/",
    "38108": "pilot ride on R1, draw 1, second CEM seed (202; balance gate unchanged, 4.5 m/s, 60 generations) on CPU, queued after the R2 ride (38039) -> results/rungs/r1_s1_cpu/v4.5_s202",
    "38109": "tools/r1_flips.py on R1 draw 2 (srun) -> results/rungs/r1_s2_cpu/sign_flips.json",
    "38110": "scratch look at the r0 screen (srun; script outside the repo): the pool's top 8 neurons by correlation with roll rate, lateral offset, heading, yaw rate, lean and handlebar angle, and the screen rows of the hand-picked lane types; prints only",
    "38111": "replay of the random-8 pilot's final CEM mean, 48 riders x 15 s, seed 201: 5.51 s upright, none finishes, 38 leave the road, 10 fall -> results/rungs/r0/rand8_r0/v4.5_s201/replay_mu_summary.json",
    "38112": "replay of the random-8 pilot's final CEM mean without the off-road rule: all 48 fall, 7.82 s upright on average -> results/rungs/r0/rand8_r0/v4.5_s201/replay_mu_noroad_summary.json",
    "38104": "replay of the top-32 pilot's final CEM mean, 48 riders x 15 s, seed 201: 8.88 s upright, 2 finish, 46 leave the road, none falls -> results/rungs/r0/top32/v4.5_s201/replay_mu_summary.json",
    "38105": "replay of the top-32 pilot's final CEM mean without the off-road rule: all 48 upright for 15 s, 44 of them more than 3.5 m from the center line -> results/rungs/r0/top32/v4.5_s201/replay_mu_noroad_summary.json",
}

LEFT_OUT = {"36054", "36055", "36056", "36057", "36062", "36064"}  # Fly Bar jobs, not part of this repo


def sacct(since):
    out = subprocess.run(
        ["sacct", "-u", getpass.getuser(), "-S", since, "-X", "--parsable2", "--format=" + ",".join(FIELDS)],
        capture_output=True, text=True, check=True).stdout
    # a submit line may span several lines (python -c "..."); a record starts with "<jobid>|"
    records, cur = [], None
    for line in out.splitlines()[1:]:
        if re.match(r"^\d+(_\d+)?\|", line):
            if cur is not None:
                records.append(cur)
            cur = line
        elif cur is not None:
            cur += "\n" + line
    if cur is not None:
        records.append(cur)
    jobs = []
    for r in records:
        parts = r.split("|", len(FIELDS) - 1)
        jobs.append(dict(zip(FIELDS, parts)))
    return jobs


def uses_gpu(job):
    """AllocTRES here has no gres/gpu, so read it from the srun flags or the sbatch script."""
    cmd = job["SubmitLine"]
    if "--gres=gpu" in cmd:
        return True
    m = re.match(r"sbatch\s+(\S+\.sbatch)", cmd)
    script = Path(job["WorkDir"]) / m.group(1) if m else None
    return bool(script and script.exists() and re.search(r"#SBATCH\s+--gres=gpu", script.read_text()))


def resources(job):
    t = dict(kv.split("=", 1) for kv in job["AllocTRES"].split(",") if "=" in kv)
    s = f"{t.get('cpu', '?')} cpu, {t.get('mem', '?')}" if t else ""
    return ", ".join(x for x in (s, "1 gpu" if uses_gpu(job) else "") if x)


def outputs(job):
    cmd, jid, name = job["SubmitLine"], job["JobID"], job["JobName"]
    found = [f"`{m}`" for m in re.findall(r"--(?:out|trace)\s+(\S+)", cmd)]
    found += [f"[{p.name}](logs/{p.name})" for p in sorted((ROOT / "logs").glob(f"*-{jid}.*")) if p.stat().st_size]
    inline = ROOT / "logs" / "inline" / f"{jid}.py"
    if inline.exists():
        found.append(f"[inline script](logs/inline/{jid}.py)")
    return ", ".join(found)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-09-26")
    a = ap.parse_args()
    jobs = [j for j in sacct(a.since) if j["WorkDir"].startswith(str(ROOT)) and j["JobID"] not in LEFT_OUT]
    lines = [
        "# Jobs",
        "",
        "Every Slurm job run from this repo on the OCF cluster (node `corruption`), newest last. Generated",
        "by `python3 tools/jobs_ledger.py` from `sacct`; do not edit by hand, add context to `NOTES` there.",
        "Commands run from the job's working directory (`.` = repo root, `fly_brain/` for most `srun` jobs).",
        "",
        "| Job | Started | State | Time | Resources | What | Command | Logs / outputs |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for j in jobs:
        cmd = j["SubmitLine"].strip()
        short = cmd.replace("\n", " ⏎ ")
        short = re.sub(r"(srun|sbatch)\s", r"\1 ", short)
        if len(short) > 220:
            short = short[:217] + "..."
        wd = j["WorkDir"].replace(str(ROOT), ".") or "."
        cell = f"`{short.replace('|', '¦')}`" + (f" (in `{wd}`)" if wd != "." else "")
        lines.append(f"| {j['JobID']} | {j['Start'].replace('T', ' ')[:16]} | {j['State'].split(' ')[0]} | {j['Elapsed']} "
                     f"| {resources(j)} | {NOTES.get(j['JobID'], '')} | {cell} | {outputs(j)} |")
    long = [j for j in jobs if len(j["SubmitLine"]) > 220 or "\n" in j["SubmitLine"]]
    if long:
        lines += ["", "## Full command lines", ""]
        for j in long:
            lines += [f"**{j['JobID']}** ({j['JobName']})", "", "```bash", j["SubmitLine"].strip(), "```", ""]
    (ROOT / "JOBS.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"JOBS.md: {len(jobs)} jobs")


if __name__ == "__main__":
    main()
