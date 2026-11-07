# Jobs

Every Slurm job run from this repo on the OCF cluster (node `corruption`), newest last. Generated
by `python3 tools/jobs_ledger.py` from `sacct`; do not edit by hand, add context to `NOTES` there.
Commands run from the job's working directory (`.` = repo root, `fly_brain/` for most `srun` jobs).

| Job | Started | State | Time | Resources | What | Command | Logs / outputs |
|---|---|---|---|---|---|---|---|
| 36053 | 2026-09-26 21:16 | COMPLETED | 00:00:00 | 4 cpu, 8G, 1 gpu | probe: node, GPU, python and torch on the cluster | `srun -p ocf-hpc --gres=gpu:1 -c 4 --mem=8G -t 5 bash -c hostname; nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv; which python3 conda; python3 --version; ls /opt/conda/bin 2>/dev/nul...` |  |
| 36059 | 2026-09-26 21:43 | COMPLETED | 00:00:01 | 32 cpu, 4G | probe: CPU affinity and torch threads | `srun -p ocf-hpc -w corruption -c 32 --mem=4G -t 3 --quiet env OMP_NUM_THREADS=32 venv/bin/python -c  ⏎ import os, torch; print('affinity', len(os.sched_getaffinity(0)), 'torch threads', torch.get_num_threads(), 'OMP',...` |  |
| 36073 | 2026-09-27 04:54 | COMPLETED | 00:00:00 | 2 cpu, 2G, 1 gpu | probe: GPU name and driver | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 2 --mem=2G -t 3 --quiet nvidia-smi --query-gpu=name,driver_version --format=csv,noheader` |  |
| 36074 | 2026-09-27 04:54 | FAILED | 00:00:00 | 2 cpu, 1G | probe: CUDA version | `srun -p ocf-hpc -w corruption -c 1 --mem=1G -t 2 --quiet bash -c ls /usr/local/cuda*/bin/nvcc 2>/dev/null; nvidia-smi ¦ grep -oE "CUDA Version: [0-9.]+"` |  |
| 36075 | 2026-09-27 04:55 | COMPLETED | 00:03:23 | 4 cpu, 16G, 1 gpu | build venv-cuda (torch cu121) and check the GPU | `sbatch cuda-venv.sbatch` | [cudavenv-36075.out](logs/cudavenv-36075.out) |
| 36076 | 2026-09-27 04:55 | FAILED | 00:00:00 | 8 cpu, 8G | failed: started in the repo root, where there is no brain package | `srun -p ocf-hpc -w corruption -c 8 --mem=8G -t 10 --quiet env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv/bin/python -m tests.test_sim` |  |
| 36077 | 2026-09-27 04:55 | COMPLETED | 00:00:08 | 8 cpu, 8G | tests.test_sim on CPU after the GPU port | `srun -p ocf-hpc -w corruption -c 8 --mem=8G -t 10 --quiet --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv/bin/python -m tests.test_sim` (in `./fly_brain`) |  |
| 36078 | 2026-09-27 04:58 | COMPLETED | 00:03:02 | 32 cpu, 64G, 1 gpu | CPU vs GPU benchmark -> results/bench_gpu.json | `sbatch bench.sbatch --devices cpu cuda --trials 1 8 32 128` | [flybench-36078.out](logs/flybench-36078.out) |
| 36079 | 2026-09-27 05:00 | FAILED | 00:00:00 | 2 cpu, 1G | probe: GPU memory (failed) | `srun -p ocf-hpc -w corruption -c 1 --mem=1G -t 2 --quiet nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv` |  |
| 36080 | 2026-09-27 05:02 | FAILED | 00:00:00 | 8 cpu, 32G, 1 gpu | failed: relative venv path | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 15 --quiet --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 venv-cuda/bin/python -m runs.bench_gpu --devices cuda --trials 512 --out re...` (in `./fly_brain`) | `results/bench_gpu_512.json` |
| 36081 | 2026-09-27 05:02 | FAILED | 00:00:00 | 8 cpu, 32G, 1 gpu | failed: relative venv path | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 15 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 venv-cuda/bin/python -m runs.bench_gpu --devices cuda --trials 512 --out results/be...` (in `./fly_brain`) | `results/bench_gpu_512.json` |
| 36082 | 2026-09-27 05:02 | COMPLETED | 00:02:04 | 8 cpu, 32G, 1 gpu | 512-trial GPU batch -> results/bench_gpu_512.json | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 15 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --devices cuda...` (in `./fly_brain`) | `results/bench_gpu_512.json` |
| 36083 | 2026-09-27 05:11 | COMPLETED | 00:00:07 | 4 cpu, 8G | bike + closed-loop sanity tests | `srun -p ocf-hpc -w corruption -c 4 --mem=8G -t 10 --quiet ../venv/bin/python -m tests.test_ride` (in `./fly_brain`) |  |
| 36084 | 2026-09-27 05:11 | COMPLETED | 00:00:02 | 4 cpu, 8G | interface smoke test: senses, readout, decoder on a toy peloton | `srun -p ocf-hpc -w corruption -c 4 --mem=8G -t 10 --quiet ../venv/bin/python -` (in `./fly_brain`) | [inline script](logs/inline/36084.py) |
| 36085 | 2026-09-27 05:12 | COMPLETED | 00:00:37 | 8 cpu, 40G, 1 gpu | open loop: brain in the loop, prior decoder, no steering | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet ../venv-cuda/bin/python -m runs.ride --open-loop --riders 8 --seconds 3 --trace results/ride_pilot_trace.json` (in `./fly_brain`) | `results/ride_pilot_trace.json` |
| 36086 | 2026-09-27 05:13 | COMPLETED | 00:00:06 | 4 cpu, 8G | PD rider without a brain (oracle) | `srun -p ocf-hpc -w corruption -c 4 --mem=8G -t 10 --quiet ../venv/bin/python -m runs.ride --oracle --riders 32 --seconds 10 --trace results/ride_oracle_trace.json` (in `./fly_brain`) | `results/ride_oracle_trace.json` |
| 36087 | 2026-09-27 05:15 | COMPLETED | 00:01:09 | 8 cpu, 40G, 1 gpu | passenger screen, pilot | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 20 --quiet ../venv-cuda/bin/python -m runs.screen --riders 8 --seconds 6` (in `./fly_brain`) |  |
| 36088 | 2026-09-27 05:18 | COMPLETED | 00:01:05 | 8 cpu, 40G, 1 gpu | which sensory population saturates the brain (odour goal diagnosis) | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet ../venv-cuda/bin/python -` (in `./fly_brain`) | [inline script](logs/inline/36088.py) |
| 36089 | 2026-09-27 05:19 | COMPLETED | 00:01:43 | 8 cpu, 40G, 1 gpu | passenger screen -> results/screen.json, screen_samples.npz | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 25 --quiet ../venv-cuda/bin/python -m runs.screen --riders 16 --seconds 8` (in `./fly_brain`) |  |
| 36090 | 2026-09-27 05:22 | FAILED | 00:00:03 | 8 cpu, 48G, 1 gpu | failed: wrong path to screen_samples.npz | `sbatch ride.sbatch --init fly_brain/results/screen_samples.npz --riders 48 --generations 15 --seconds 10 --out results/ride.json` | `results/ride.json`, [flyride-36090.err](logs/flyride-36090.err), [flyride-36090.out](logs/flyride-36090.out) |
| 36091 | 2026-09-27 05:23 | COMPLETED | 00:50:32 | 8 cpu, 48G, 1 gpu | CEM learning, sigma0 0.3 -> results/ride.json | `sbatch ride.sbatch --init results/screen_samples.npz --riders 48 --generations 15 --seconds 10 --out results/ride.json` | `results/ride.json`, [flyride-36091.out](logs/flyride-36091.out) |
| 36092 | 2026-09-27 06:13 | COMPLETED | 00:51:17 | 8 cpu, 48G, 1 gpu | CEM learning, sigma0 0.1 -> results/ride_b.json (the best decoder) | `sbatch ride.sbatch --init results/screen_samples.npz --riders 48 --generations 15 --seconds 10 --sigma0 0.1 --seed 1 --out results/ride_b.json` | `results/ride_b.json`, [flyride-36092.out](logs/flyride-36092.out) |
| 36093 | None | CANCELLED | 00:00:00 | 1 gpu | cancelled, rerun on CPU as 36094 | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 25 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --replay results/ride.json --riders 16 --seconds 12 --seed 7 --trace results/ride...` (in `./fly_brain`) | `results/ride_trace.json` |
| 36094 | 2026-09-27 06:25 | COMPLETED | 00:08:26 | 32 cpu, 48G | replay of ride.json -> results/ride_trace.json | `srun -p ocf-hpc -w corruption -c 32 --mem=48G -t 40 --quiet env OMP_NUM_THREADS=32 /home/s/st/stevejobs/flybrain/venv/bin/python -m runs.ride --replay results/ride.json --riders 16 --seconds 12 --seed 7 --device cpu -...` (in `./fly_brain`) | `results/ride_trace.json` |
| 36095 | 2026-09-27 07:05 | COMPLETED | 00:03:26 | 8 cpu, 40G, 1 gpu | replay of the best decoder -> results/ride_b_trace.json (the /ride/ demo) | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --replay results/ride_b.json --riders 16 --seconds 15 --seed 7 --trace results/ri...` (in `./fly_brain`) | `results/ride_b_trace.json` |
| 36101 | None | CANCELLED | 00:00:00 | 1 gpu | cancelled: is a weak odour goal stable? | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -` (in `./fly_brain`) | [inline script](logs/inline/36101.py) |
| 36102 | None | CANCELLED | 00:00:00 |  | cancelled: HS lane cue check | `srun -p ocf-hpc -w corruption -c 2 --mem=6G -t 5 --quiet /home/s/st/stevejobs/flybrain/venv/bin/python -` (in `./fly_brain`) | [inline script](logs/inline/36102.py) |
| 36103 | 2026-09-28 08:15 | COMPLETED | 00:56:28 | 8 cpu, 48G, 1 gpu | lane keeping: screen with HS lane cue -> CEM -> replay | `sbatch ride-lane.sbatch` | [flylane-36103.out](logs/flylane-36103.out) |
| 36104 | None | CANCELLED | 00:00:00 |  |  | `srun -p ocf-hpc -w corruption -c 1 --mem=256M -t 1 --quiet bash -c timeout 10 ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -i ~/.ssh/flybrain_play_deploy -o IdentitiesOnly=yes -T git@github.com 2>&1 ¦ head -1` |  |
| 36105 | 2026-09-28 08:52 | FAILED | 00:00:03 | 8 cpu, 40G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --init results/screen_lane_samples.npz --lane hs --dagger 2 --riders 4 --seconds ...` (in `./fly_brain`) | `/tmp/claude-93015/-home-s-st-stevejobs-flybrain/ff3d4c1f-4087-4f88-b1bd-f60320256b54/scratchpad/dagger_smoke.json` |
| 36106 | 2026-09-28 08:52 | COMPLETED | 00:00:27 | 8 cpu, 40G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --init results/screen_lane_samples.npz --lane hs --dagger 2 --riders 4 --seconds ...` (in `./fly_brain`) | `results/dagger_smoke.json` |
| 36107 | 2026-09-28 08:53 | COMPLETED | 00:35:11 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-dagger.sbatch` | [flydagger-36107.out](logs/flydagger-36107.out) |
| 36108 | 2026-09-28 09:12 | COMPLETED | 00:54:16 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-offroad.sbatch results/ride_lane.json results/ride_road.json` | [flyroad-36108.out](logs/flyroad-36108.out) |
| 36109 | 2026-09-28 09:27 | COMPLETED | 00:51:47 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-offroad2.sbatch results/ride_lane.json results/ride_road2.json` | [flyroad2-36109.out](logs/flyroad2-36109.out) |
| 36110 | 2026-09-28 09:33 | COMPLETED | 00:05:10 | 48 cpu, 64G |  | `srun -p ocf-hpc -w corruption -c 48 --mem=64G -t 60 --quiet env OMP_NUM_THREADS=48 /home/s/st/stevejobs/flybrain/venv/bin/python -m runs.screen --riders 16 --seconds 8 --lane hs --device cpu --out results/screen_lane_...` (in `./fly_brain`) | `results/screen_lane_psi.json` |
| 36111 | 2026-09-28 10:08 | COMPLETED | 00:01:41 | 8 cpu, 40G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.screen --riders 16 --seconds 8 --lane hs --polarity physio --out results/screen_physio...` (in `./fly_brain`) | `results/screen_physio.json` |
| 36112 | 2026-09-28 10:11 | COMPLETED | 00:00:45 | 8 cpu, 40G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.probe --pop HS VS HALT --extra 30 --brains 16 --ms 1000 --out results/probe.json` (in `./fly_brain`) | `results/probe.json` |
| 36113 | 2026-09-28 10:13 | CANCELLED | 00:04:13 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-lanedn.sbatch  results/ride_lanedn.json` | [flylanedn-36113.err](logs/flylanedn-36113.err), [flylanedn-36113.out](logs/flylanedn-36113.out) |
| 36114 | 2026-09-28 10:13 | CANCELLED | 00:04:13 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-lanedn.sbatch hs_heading=150,hs_lane=50 results/ride_lanedn_strong.json` | [flylanedn-36114.err](logs/flylanedn-36114.err), [flylanedn-36114.out](logs/flylanedn-36114.out) |
| 36115 | 2026-09-28 10:18 | CANCELLED | 00:04:56 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-lanedn.sbatch  results/ride_lanedn.json` | [flylanedn-36115.err](logs/flylanedn-36115.err), [flylanedn-36115.out](logs/flylanedn-36115.out) |
| 36116 | 2026-09-28 10:18 | CANCELLED | 00:04:56 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-lanedn.sbatch hs_heading=150,hs_lane=50 results/ride_lanedn_strong.json` | [flylanedn-36116.err](logs/flylanedn-36116.err), [flylanedn-36116.out](logs/flylanedn-36116.out) |
| 36117 | 2026-09-28 10:22 | CANCELLED | 00:31:51 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-lanedn.sbatch  results/ride_lanedn_narrow.json 0.25 8` | [flylanedn-36117.err](logs/flylanedn-36117.err), [flylanedn-36117.out](logs/flylanedn-36117.out) |
| 36118 | 2026-09-28 10:23 | CANCELLED | 00:18:53 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-lanedn.sbatch hs_heading=150,hs_lane=50 results/ride_lanedn_strong.json 0.25 9` | [flylanedn-36118.err](logs/flylanedn-36118.err), [flylanedn-36118.out](logs/flylanedn-36118.out) |
| 36119 | 2026-09-28 10:23 | CANCELLED | 00:02:19 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-lanedn.sbatch  results/ride_lanedn_tiny.json 0.1 10` | [flylanedn-36119.err](logs/flylanedn-36119.err), [flylanedn-36119.out](logs/flylanedn-36119.out) |
| 36120 | 2026-09-28 10:25 | CANCELLED | 00:08:06 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-lanefilter.sbatch` | [flyfilter-36120.err](logs/flyfilter-36120.err), [flyfilter-36120.out](logs/flyfilter-36120.out) |
| 36121 | 2026-09-28 10:33 | CANCELLED | 00:08:22 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-fast.sbatch hs_heading=150,hs_lane=50 results/ride_fast.json 0.25 12` | [flyfast-36121.err](logs/flyfast-36121.err), [flyfast-36121.out](logs/flyfast-36121.out) |
| 36122 | 2026-09-28 10:40 | COMPLETED | 00:00:15 | 4 cpu, 8G |  | `srun -p ocf-hpc -w corruption -c 4 --mem=8G -t 5 --quiet /home/s/st/stevejobs/flybrain/venv/bin/python -` (in `./fly_brain`) |  |
| 36123 | 2026-09-28 10:41 | COMPLETED | 00:00:19 | 4 cpu, 8G |  | `srun -p ocf-hpc -w corruption -c 4 --mem=8G -t 5 --quiet /home/s/st/stevejobs/flybrain/venv/bin/python -` (in `./fly_brain`) |  |
| 36124 | 2026-09-28 10:42 | COMPLETED | 01:06:33 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-easy.sbatch results/ride_lane.json results/ride_easy_seeded.json 0.08 0.25 21` | [flyeasy-36124.out](logs/flyeasy-36124.out) |
| 36125 | 2026-09-28 10:42 | CANCELLED | 00:02:55 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-easy.sbatch results/zero_theta.json results/ride_easy_zero.json 0.15 0.15 22` | [flyeasy-36125.err](logs/flyeasy-36125.err), [flyeasy-36125.out](logs/flyeasy-36125.out) |
| 36126 | 2026-09-28 10:44 | COMPLETED | 01:22:42 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-easy-c.sbatch results/zero_theta.json results/ride_easy_zero.json 0.15 0.15 22` | [flyeasyc-36126.out](logs/flyeasyc-36126.out) |
| 36127 | 2026-09-28 10:54 | COMPLETED | 01:24:01 | 8 cpu, 48G, 1 gpu |  | `sbatch ride-slow.sbatch results/ride_lane.json results/ride_slow.json 0.08 0.25 23` | [flyslow-36127.out](logs/flyslow-36127.out) |
| 36128 | 2026-09-28 11:50 | COMPLETED | 00:25:32 | 8 cpu, 48G, 1 gpu |  | `sbatch sweep-gain.sbatch handsoff gain_+0.00 gain_-0.29 gain_-1.00 gain_-2.00 gain_-4.00 gain_-0.50 gain_+1.00` | [flysweep-36128.out](logs/flysweep-36128.out) |
| 36129 | 2026-09-28 12:12 | COMPLETED | 00:04:35 | 8 cpu, 40G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 30 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --replay results/ride_slow_mu.json --tau-lane-ms 300 --lane-filter results/probe....` (in `./fly_brain`) | `results/ride_slow_mu_trace.json` |
| 36134 | 2026-09-28 14:39 | FAILED | 00:00:00 | 8 cpu, 16G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=16G -t 20 --quiet env OMP_NUM_THREADS=8 venv-cuda/bin/python /tmp/claude-93015/-home-s-st-stevejobs-flybrain/7d1c4570-42ca-4595-8821-958931ef7366/scratchpad/stats.py` |  |
| 36135 | 2026-09-28 14:39 | COMPLETED | 00:00:47 | 8 cpu, 16G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=16G -t 20 --quiet env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/flybrain/fly_brain/runs/step_stats.py` |  |
| 36136 | 2026-09-28 14:42 | COMPLETED | 00:01:18 | 8 cpu, 16G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=16G -t 20 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m tests.test_graph` (in `./fly_brain`) |  |
| 36137 | 2026-09-28 14:44 | COMPLETED | 00:00:10 | 8 cpu, 16G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=16G -t 15 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.profile_step --trials 8` (in `./fly_brain`) |  |
| 36138 | 2026-09-28 14:44 | COMPLETED | 00:02:35 | 8 cpu, 32G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 30 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --graph --devi...` (in `./fly_brain`) | `results/bench_graph.json` |
| 36139 | 2026-09-28 14:48 | COMPLETED | 00:00:38 | 8 cpu, 16G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=16G -t 20 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m tests.test_graph` (in `./fly_brain`) |  |
| 36140 | 2026-09-28 14:48 | COMPLETED | 00:02:00 | 8 cpu, 32G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 30 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --graph --devi...` (in `./fly_brain`) | `results/bench_graph2.json` |
| 36141 | 2026-09-28 14:50 | COMPLETED | 00:00:12 | 8 cpu, 16G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=16G -t 15 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.profile_step --trials 128` (in `./fly_brain`) |  |
| 36142 | 2026-09-28 14:53 | COMPLETED | 00:00:40 | 8 cpu, 32G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 40 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m tests.test_graph` (in `./fly_brain`) |  |
| 36143 | 2026-09-28 14:53 | COMPLETED | 00:00:51 | 8 cpu, 32G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 40 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --graph --devi...` (in `./fly_brain`) | `results/bench_graph3.json` |
| 36144 | 2026-09-28 14:54 | COMPLETED | 00:00:11 | 8 cpu, 32G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 40 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.profile_step --trials 128` (in `./fly_brain`) |  |
| 36145 | 2026-09-28 14:55 | COMPLETED | 00:00:39 | 8 cpu, 48G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=48G -t 40 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m tests.test_graph` (in `./fly_brain`) |  |
| 36146 | 2026-09-28 14:56 | COMPLETED | 00:06:15 | 8 cpu, 48G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=48G -t 40 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --graph --devi...` (in `./fly_brain`) | `results/bench_graph4.json` |
| 36147 | 2026-09-28 15:02 | COMPLETED | 00:02:10 | 8 cpu, 48G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=48G -t 40 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bar --device cuda --grap...` (in `./fly_brain`) |  |
| 36487 | 2026-10-03 11:09 | COMPLETED | 00:04:33 | 8 cpu, 40G, 1 gpu | hands-off on the road (5.5 m/s, 5 Nm), GPU copy queued while the GPUs were busy | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 30 --quiet ../venv-cuda/bin/python -m runs.ride --open-loop --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=1...` (in `./fly_brain`) | `results/ride_pilot_trace.json` |
| 36488 | 2026-10-03 02:32 | COMPLETED | 00:00:09 | 4 cpu, 8G | PD rider on the road (5.5 m/s, 5 Nm) -> results/ride_oracle_trace.json (/ride/oracle) | `srun -p ocf-hpc -w corruption -c 4 --mem=8G -t 10 --quiet ../venv/bin/python -m runs.ride --oracle --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5...` (in `./fly_brain`) | `results/ride_oracle_trace.json` |
| 36489 | 2026-10-03 02:33 | COMPLETED | 00:01:56 | 12 cpu, 40G |  | `srun -p ocf-hpc -w corruption -c 12 --mem=40G -t 12 --quiet ../venv-cuda/bin/python -m runs.ride --open-loop --device cpu --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=...` (in `./fly_brain`) | `results/scratch_cpu_test.json` |
| 36490 | 2026-10-03 02:35 | COMPLETED | 00:34:45 | 12 cpu, 40G | hands-off on the road (5.5 m/s, 5 Nm), CPU -> results/ride_pilot_road_trace.json (/ride/open-loop) | `srun -p ocf-hpc -w corruption -c 12 --mem=40G -t 90 --quiet ../venv-cuda/bin/python -m runs.ride --open-loop --device cpu --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=...` (in `./fly_brain`) | `results/ride_pilot_road_trace.json` |
| 36491 | 2026-10-03 02:42 | COMPLETED | 00:00:19 | 4 cpu, 16G |  | `srun -p ocf-hpc -w corruption -c 4 --mem=16G -t 14 --quiet ../venv-cuda/bin/python -m runs.ride --replay results/ride_slow_mu.json --device cpu --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane ...` (in `./fly_brain`) | `results/scratch_t.json` |
| 36492 | 2026-10-03 03:10 | COMPLETED | 00:34:56 | 12 cpu, 48G | replay on the road with the whole brain recorded, CPU -> results/ride_road_trace.json + ride_road_brain.npz (/ride/) | `srun -p ocf-hpc -w corruption -c 12 --mem=48G -t 120 --quiet ../venv-cuda/bin/python -m runs.ride --replay results/ride_slow_mu.json --device cpu --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lan...` (in `./fly_brain`) | `results/ride_road_trace.json` |
| 36493 | 2026-10-03 11:13 | COMPLETED | 02:51:57 | 8 cpu, 48G, 1 gpu | lane keeping round 2 (lane-next.sbatch): batch centring + look-ahead/gain replays, operating-point CEM, held-out seed 59 -> results/lane/ | `sbatch lane-next.sbatch` | [flylane-36493.out](logs/flylane-36493.out) |
| 36494 | 2026-10-03 14:07 | COMPLETED | 00:09:20 | 8 cpu, 48G, 1 gpu | /ride/ page replays with the brain recorded: round-2 decoder and hands-off (ride-page.sbatch) | `sbatch ride-page.sbatch results/lane/cem_mu.json` | [flypage-36494.out](logs/flypage-36494.out) |
| 36519 | 2026-10-03 19:55 | FAILED | 00:00:04 | 4 cpu, 16G |  | `srun -p ocf-hpc -w corruption -c 4 --mem=16G -t 14 --quiet ../venv-cuda/bin/python -m runs.ride --device cpu --readout lane --lane hs --lane-filter results/probe.json --tau-lane-ms 300 --gains hs_heading=150,hs_lane=5...` (in `./fly_brain`) | `/tmp/claude-93015/-home-s-st-stevejobs-flybrain/ff3d4c1f-4087-4f88-b1bd-f60320256b54/scratchpad/att_test/cem.json` |
| 36520 | 2026-10-03 19:56 | COMPLETED | 00:00:52 | 4 cpu, 16G |  | `srun -p ocf-hpc -w corruption -c 4 --mem=16G -t 14 --quiet ../venv-cuda/bin/python -m runs.ride --device cpu --readout lane --lane hs --lane-filter results/probe.json --tau-lane-ms 300 --gains hs_heading=150,hs_lane=5...` (in `./fly_brain`) | `results/attempts_test/cem.json` |
| 36521 | 2026-10-03 19:58 | COMPLETED | 02:45:41 | 8 cpu, 64G, 1 gpu | learning to ride from a blank decoder, every attempt recorded (ride-attempts.sbatch) -> results/attempts/ (the attempts page) | `sbatch ride-attempts.sbatch` | [flyattempt-36521.out](logs/flyattempt-36521.out) |
| 36533 | 2026-10-04 05:35 | COMPLETED | 00:00:30 | 8 cpu, 64G | rewrite: build brain.npz with brain/connectome.py (identical edges and weights to the old build) | `sbatch -p ocf-hpc -w corruption -c 8 --mem=64G -J connectome-build -o ../logs/rewrite/connectome-build-%j.out --wrap cd /home/s/st/stevejobs/flybrain/.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain && ...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36534 | 2026-10-04 05:38 | COMPLETED | 00:00:03 | 4 cpu, 32G |  | `srun -p ocf-hpc -w corruption -c 4 --mem=32G /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36535 | 2026-10-04 05:39 | COMPLETED | 00:05:50 | 8 cpu, 48G, 1 gpu | rewrite: old engine vs new engine on sugar/bitter, same seed -> identical spikes | `sbatch -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -J engine-equiv -o ../logs/rewrite/equiv-%j.out --wrap cd /home/s/st/stevejobs/flybrain/.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain && ~/...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36536 | 2026-10-04 05:49 | COMPLETED | 00:00:23 | 8 cpu, 48G, 1 gpu |  | `srun -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -t 30 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m pytest -q tests/test_engine.py tests/test_graph.py` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36537 | 2026-10-04 05:50 | COMPLETED | 00:01:09 | 8 cpu, 48G, 1 gpu |  | `srun -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -t 30 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m pytest -q -rs tests/test_engine.py tests/test_graph.py` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36538 | 2026-10-04 05:53 | COMPLETED | 00:09:29 | 16 cpu, 96G, 1 gpu | rewrite: w_syn scale sweep vs Shiu's FlyWire feeding curve, first grid (superseded by 36539) | `sbatch calibrate-wsyn.sbatch` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) | [calibrate-wsyn-36538.out](logs/calibrate-wsyn-36538.out) |
| 36539 | 2026-10-04 06:03 | COMPLETED | 00:14:26 | 16 cpu, 96G, 1 gpu | rewrite: w_syn scale sweep vs Shiu's FlyWire feeding curve -> results/calibrate_wsyn.json, scale 0.47 | `sbatch calibrate-wsyn.sbatch` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) | [calibrate-wsyn-36539.out](logs/calibrate-wsyn-36539.out) |
| 36540 | 2026-10-04 06:18 | CANCELLED | 00:04:17 | 8 cpu, 48G, 1 gpu | rewrite: replay of the 3D-page decoder (results/lane/cem_mu.json) on the new engine: 10.0 s upright (old 18.1 s) | `sbatch -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -t 60 -J ride-replay-new -o ../logs/rewrite/ride-replay-%j.out --wrap cd /home/s/st/stevejobs/flybrain/.claude/worktrees/commit-dc73073-investigation-a94327/...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) | `/tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-commit-dc73073-investigation-a94327/429f3982-d7b5-4efc-acd7-32979c1cb3e7/scratchpad/road_trace_new.json`, `/tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-commit-dc73073-investigation-a94327/429f3982-d7b5-4efc-acd7-32979c1cb3e7/scratchpad/pilot_trace_new.json` |
| 36541 | 2026-10-04 06:22 | COMPLETED | 00:01:35 | 8 cpu, 64G, 1 gpu | rewrite: Fly Brain Live data, Shiu's 10 stimulation experiments (export_dashboard + pack_dashboard) | `sbatch -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=64G -t 60 -J dashboard-export -o ../logs/rewrite/dashboard-%j.out --wrap cd /home/s/st/stevejobs/flybrain/.claude/worktrees/commit-dc73073-investigation-a94327/f...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36542 | 2026-10-04 06:24 | COMPLETED | 00:04:00 | 8 cpu, 48G, 1 gpu | rewrite: same replay at scale 0.45: 12.1 s upright, so the Brian2 rule fixes, not the scale, break the old decoder | `sbatch -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -t 60 -J ride-replay-045 -o ../logs/rewrite/ride-replay-045-%j.out --wrap cd /home/s/st/stevejobs/flybrain/.claude/worktrees/commit-dc73073-investigation-a94...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36543 | 2026-10-04 06:29 | COMPLETED | 02:49:05 | 8 cpu, 64G, 1 gpu | rewrite: the bike relearned on the new engine (ride-relearn.sbatch): 37 generations, 1,776 attempts -> results/relearn/ (the /ride/ page) | `sbatch ride-relearn.sbatch` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) | [ride-relearn-36543.out](logs/ride-relearn-36543.out) |
| 36544 | None | CANCELLED | 00:00:00 | 1 gpu |  | `srun -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -t 30 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m pytest -q -rs tests` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36545 | None | CANCELLED | 00:00:00 | 1 gpu |  | `srun -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -t 20 --immediate=60 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m pytest -q -rs tests/test_graph.py tests/test_engine.py` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36546 | 2026-10-04 09:18 | CANCELLED | 00:00:00 | 1 gpu | cancelled: wrong decoder path | `sbatch ride-page.sbatch fly_brain/../fly_brain/results/relearn/cem_mu.json` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) |  |
| 36547 | 2026-10-04 09:19 | COMPLETED | 00:08:11 | 8 cpu, 48G, 1 gpu | rewrite: /ride/ page replays of the relearned decoder (results/relearn/cem_mu.json) and hands-off, brains recorded | `sbatch ride-page.sbatch results/relearn/cem_mu.json results/relearn/probe.json` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) | [flypage-36547.out](logs/flypage-36547.out) |
| 36548 | 2026-10-04 09:19 | COMPLETED | 00:00:37 | 8 cpu, 32G |  | `srun -p ocf-hpc -w corruption -c 8 --mem=32G -t 30 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_attempts results/relearn/attempts results/attempts_page --force` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36549 | 2026-10-04 09:28 | COMPLETED | 00:00:19 | 8 cpu, 48G |  | `srun -p ocf-hpc -w corruption -c 8 --mem=48G -t 30 bash -c /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_road_trace.json results/ride_3d.html && /home/s/st/stevejobs/flybrain/...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36550 | 2026-10-04 09:29 | COMPLETED | 00:01:14 | 8 cpu, 48G, 1 gpu |  | `srun -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -t 20 --immediate=120 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m pytest -q -rs tests` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36551 | 2026-10-04 09:32 | COMPLETED | 00:00:45 | 8 cpu, 64G, 1 gpu |  | `srun -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=64G -t 20 --immediate=120 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --devices cuda --trials 1 128 --out ../logs/rewrite/bench_engine.json` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) | `../logs/rewrite/bench_engine.json` |
| 36552 | 2026-10-04 15:25 | COMPLETED | 00:00:45 | 8 cpu, 64G |  | `srun -p ocf-hpc -w corruption -c 8 --mem=64G -t 20 bash -c ~/flybrain/venv-cuda/bin/python -m brain.connectome 2>&1 ¦ grep -v 'weight rows' && ~/flybrain/venv-cuda/bin/python -m brain.atlas` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36553 | 2026-10-04 15:26 | COMPLETED | 00:03:31 | 8 cpu, 48G, 1 gpu |  | `srun -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -t 25 --immediate=300 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m pytest -q -rs -x tests` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36554 | 2026-10-04 15:30 | CANCELLED | 00:11:38 | 8 cpu, 96G, 1 gpu | rewrite: graph engine benchmark, stopped (buffers sized too large) | `srun -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=96G -t 25 --immediate=300 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --devices cuda --trials 1 128 1024 --graph --out ../logs/rewrite/ben...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) | `../logs/rewrite/bench_graph_engine.json` |
| 36555 | 2026-10-04 15:42 | COMPLETED | 02:45:01 | 8 cpu, 64G, 1 gpu | rewrite: the bike relearned again with the new display regions recorded (ride-relearn.sbatch, search only) -> results/relearn/ | `sbatch ride-relearn.sbatch` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) | [ride-relearn-36555.out](logs/ride-relearn-36555.out) |
| 36626 | 2026-10-04 18:27 | COMPLETED | 00:08:07 | 8 cpu, 48G | rewrite: /ride/ page replays of the relearned decoder and hands-off, brains recorded | `sbatch --parsable ride-page.sbatch results/relearn/cem_mu.json results/relearn/probe.json` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) | [flypage-36626.out](logs/flypage-36626.out) |
| 36627 | 2026-10-04 18:35 | COMPLETED | 00:09:59 | 8 cpu, 96G, 1 gpu | rewrite: dashboard export, all tests on GPU, graph engine benchmark | `sbatch --parsable --dependency=afterany:36626 -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=96G -t 90 -J flybrain-checks -o logs/rewrite/checks-%j.out --wrap cd fly_brain && P=/home/s/st/stevejobs/flybrain/venv-cud...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) | `../logs/rewrite/bench_graph_engine.json` |
| 36628 | 2026-10-04 18:27 | COMPLETED | 00:00:38 | 8 cpu, 32G |  | `srun -p ocf-hpc -w corruption -c 8 --mem=32G -t 45 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_attempts results/relearn/attempts results/attempts_page --force` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36629 | 2026-10-04 18:35 | COMPLETED | 00:00:19 | 8 cpu, 48G |  | `srun -p ocf-hpc -w corruption -c 8 --mem=48G -t 30 bash -c /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_road_trace.json results/ride_3d.html && /home/s/st/stevejobs/flybrain/...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36630 | 2026-10-04 19:26 | COMPLETED | 00:00:31 | 8 cpu, 96G |  | `srun -p ocf-hpc -w corruption -c 8 --mem=96G -t 20 bash -c ~/flybrain/venv-cuda/bin/python -m brain.connectome && ~/flybrain/venv-cuda/bin/python -m brain.atlas` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36631 | 2026-10-04 19:27 | COMPLETED | 00:02:59 | 8 cpu, 64G, 1 gpu |  | `sbatch --parsable -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=64G -t 40 -J flybrain-checks2 -o logs/rewrite/checks2-%j.out --wrap cd fly_brain && P=/home/s/st/stevejobs/flybrain/venv-cuda/bin/python && $P -m pyte...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) |  |
| 36632 | 2026-10-04 19:27 | COMPLETED | 00:00:16 | 8 cpu, 48G |  | `srun -p ocf-hpc -w corruption -c 8 --mem=48G -t 40 bash -c /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_attempts results/relearn/attempts results/attempts_page 2>&1 ¦ tail -1 && /home/s/st/steve...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36633 | 2026-10-04 20:04 | COMPLETED | 00:00:57 | 8 cpu, 48G |  | `srun -p ocf-hpc -w corruption -c 8 --mem=48G -t 30 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36634 | 2026-10-04 20:06 | COMPLETED | 00:00:38 | 8 cpu, 32G |  | `srun -p ocf-hpc -w corruption -c 8 --mem=32G -t 45 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_attempts results/relearn/attempts results/attempts_page --force` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36635 | 2026-10-04 20:06 | COMPLETED | 00:01:34 | 8 cpu, 64G, 1 gpu |  | `sbatch --parsable -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=64G -t 30 -J flydash3 -o logs/rewrite/dashboard3-%j.out --wrap cd fly_brain && P=/home/s/st/stevejobs/flybrain/venv-cuda/bin/python && $P -m export.ex...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) |  |
| 36636 | 2026-10-04 20:07 | COMPLETED | 00:00:21 | 8 cpu, 48G |  | `srun -p ocf-hpc -w corruption -c 8 --mem=48G -t 30 bash -c /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_road_trace.json results/ride_3d.html && /home/s/st/stevejobs/flybrain/...` (in `./.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain`) |  |
| 36637 | 2026-10-04 20:08 | COMPLETED | 00:01:25 | 8 cpu, 64G, 1 gpu |  | `sbatch --parsable -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=64G -t 30 -J flytests -o logs/rewrite/tests3-%j.out --wrap cd fly_brain && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m pytest -q -rs tests` (in `./.claude/worktrees/commit-dc73073-investigation-a94327`) |  |
| 37486 | 2026-10-17 22:26 | COMPLETED | 00:00:06 | 4 cpu, 24G |  | `srun -p ocf-hpc --cpus-per-task=4 --mem=24G --time=00:25:00 --job-name=publish-brain bash tools/publish_brain.sh brain-v1` |  |
| 37487 | 2026-10-17 22:29 | CANCELLED | 00:34:03 | 8 cpu, 16G, 1 gpu |  | `sbatch ride-gate.sbatch 4.0 201` |  |
| 37488 | None | CANCELLED | 00:00:00 | 1 gpu |  | `sbatch ride-gate.sbatch 4.0 202` |  |
| 37489 | None | CANCELLED | 00:00:00 | 1 gpu |  | `sbatch ride-gate.sbatch 4.5 201` |  |
| 37490 | None | CANCELLED | 00:00:00 | 1 gpu |  | `sbatch ride-gate.sbatch 4.5 202` |  |
| 37491 | 2026-10-17 23:04 | COMPLETED | 05:03:25 | 8 cpu, 16G |  | `sbatch --parsable ride-gate.sbatch 4.0 201` | [ride-gate-37491.out](logs/ride-gate-37491.out) |
| 37492 | 2026-10-17 23:49 | COMPLETED | 05:02:33 | 8 cpu, 16G |  | `sbatch --parsable ride-gate.sbatch 4.5 201` | [ride-gate-37492.out](logs/ride-gate-37492.out) |
| 37493 | 2026-10-17 23:49 | COMPLETED | 05:04:38 | 8 cpu, 16G |  | `sbatch --parsable --nice=100 ride-gate.sbatch 4.0 202` | [ride-gate-37493.out](logs/ride-gate-37493.out) |
| 37494 | 2026-10-18 04:07 | COMPLETED | 05:01:16 | 8 cpu, 16G |  | `sbatch --parsable --nice=100 ride-gate.sbatch 4.5 202` | [ride-gate-37494.out](logs/ride-gate-37494.out) |
| 37519 | 2026-10-19 01:51 | FAILED | 00:00:01 | 2 cpu, 4G |  | `srun -p ocf-hpc -w corruption -c 2 --mem=4G -t 5 bash -c which chromium google-chrome ffmpeg; chromium --version; nproc; ls /usr/lib/x86_64-linux-gnu/libEGL_nvidia* 2>/dev/null ¦ head -2; nvidia-smi --query-gpu=name,u...` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37520 | 2026-10-19 02:01 | COMPLETED | 00:00:00 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -c 2 -t 5 bash -c hostname; which chromium ffmpeg; cat /etc/os-release ¦ head -3; curl -sS -m 10 -o /dev/null -w "gfonts %{http_code}\n" "https://fonts.googleapis.com/css2?family=Anton"; ...` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37521 | 2026-10-19 02:01 | FAILED | 00:00:00 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -c 2 -t 5 bash -c ldd ~/opt/chromium/chromium ¦ grep "not found"; ldd ~/opt/chromium/libGLESv2.so ~/opt/chromium/libvk_swiftshader.so ~/opt/chromium/libEGL.so ¦ grep "not found"` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37522 | 2026-10-19 02:01 | FAILED | 00:00:00 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -c 2 -t 5 bash -c export LD_LIBRARY_PATH=$HOME/opt/chromium/lib; ldd ~/opt/chromium/chromium ~/opt/chromium/lib/* ¦ grep "not found"; ~/opt/chromium/chromium --version` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37523 | 2026-10-19 02:01 | COMPLETED | 00:00:00 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -c 2 -t 5 bash -c export LD_LIBRARY_PATH=$HOME/opt/chromium/lib; ldd ~/opt/chromium/chromium ~/opt/chromium/lib/* ¦ grep "not found"; ~/opt/chromium/chromium --version` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37525 | 2026-10-19 02:11 | COMPLETED | 00:02:29 | 4 cpu, 8G |  | `srun -p ocf-hpc -w corruption -c 4 --mem 8G -t 15 bash /home/s/st/stevejobs/tour-de-fly/scratch/film_test/node1.sh` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37526 | 2026-10-19 02:14 | COMPLETED | 00:00:00 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -c 2 -t 2 bash -c lscpu ¦ grep -E "Model name¦Thread¦Core¦Socket¦MHz¦NUMA node"; cat /sys/fs/cgroup/$(cat /proc/self/cgroup ¦ cut -d: -f3)/cpuset.cpus.effective 2>/dev/null; taskset -cp $$` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37546 | 2026-10-19 03:24 | COMPLETED | 00:00:00 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -c 1 -t 2 bash -c ls -d --time-style=+%H:%M -l /tmp/tdf-film-* ¦ awk "{print \$6}" ¦ sort ¦ uniq -c; ls /tmp/tdf-film-yys_udt3` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37547 | 2026-10-19 03:24 | COMPLETED | 00:00:01 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -c 1 -t 2 bash -c echo node TMPDIR=$TMPDIR; df -h /tmp ¦ tail -1; mount ¦ grep " /tmp "` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37548 | 2026-10-19 03:25 | COMPLETED | 00:00:00 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -n 1 -c 1 -t 2 bash -c echo "node $(hostname): $(ls -d /tmp/tdf-film-* 2>/dev/null ¦ wc -l)"` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37550 | 2026-10-19 03:27 | COMPLETED | 00:00:01 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -n 1 -c 1 -t 2 bash -c rm -rf /tmp/tdf-film-* /tmp/tdf-bench-* /tmp/tdf-sb-*; echo "node left: $(ls -d /tmp/tdf-film-* /tmp/tdf-bench-* /tmp/tdf-sb-* 2>/dev/null ¦ wc -l)"` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37558 | 2026-10-19 03:42 | COMPLETED | 00:00:01 | 2 cpu, 1G |  | `srun -p ocf-hpc -w corruption -c 1 --mem=1G -t 00:02:00 -J tdfD-ls bash -c ls -la --time-style=full-iso /tmp/ ¦ grep -i "tdf\¦det-\¦w0" ; for d in /tmp/tdf-film-run-*; do echo "== $d"; find $d -maxdepth 3 ¦ head -30; ...` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37562 | 2026-10-19 03:53 | COMPLETED | 00:00:00 | 2 cpu, 1G |  | `srun -p ocf-hpc -w corruption -c 1 --mem=1G -t 00:01:00 -J tdfD-chk bash -c which setpriv; setpriv --help ¦ grep -i pdeath` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37566 | 2026-10-19 04:44 | COMPLETED | 00:00:00 | 2 cpu, 2G |  | `srun -p ocf-hpc -w corruption -c 2 --mem=2G -t 3 bash -c fc-list ¦ grep -c -i "Droid Sans Fallback"; fc-list ¦ grep -c -i "DejaVu Sans"` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37607 | 2026-10-19 10:47 | COMPLETED | 00:00:09 | 8 cpu, 8000M |  | `srun -p ocf-hpc -w corruption -c 8 -t 30 /home/s/st/stevejobs/tour-de-fly/scratch/sg/shot.sh /home/s/st/stevejobs/tour-de-fly/scratch/sg/out/lab1.png scratch/sg/lab.html?views=1540,0,3,1980,0,25,12;1930,40,10,1980,0,2...` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37608 | 2026-10-19 10:48 | COMPLETED | 00:01:00 | 8 cpu, 8000M |  | `srun -p ocf-hpc -w corruption -c 8 -t 30 /home/s/st/stevejobs/tour-de-fly/scratch/sg/shot.sh /home/s/st/stevejobs/tour-de-fly/scratch/sg/out/film1.png film.html?w=1600&h=900&sheet=114,117,128,130,96.5,98.5,99.3,101,10...` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37609 | 2026-10-19 10:48 | COMPLETED | 00:00:12 | 8 cpu, 8000M |  | `srun -p ocf-hpc -w corruption -c 8 -t 30 /home/s/st/stevejobs/tour-de-fly/scratch/sg/shot.sh /home/s/st/stevejobs/tour-de-fly/scratch/sg/out/lab_chk.png scratch/sg/lab.html?fin=checker&views=1520,0.8,2.6,1470,0,0.6,15...` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37710 | 2026-10-22 23:41 | COMPLETED | 00:00:01 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -c 2 -t 2 bash -c hostname; nproc; ~/flybrain/venv/bin/python -c "import numpy, scipy; print(numpy.__version__)"; ~/tour-de-fly/film/.venv-tts/bin/python -c "import piper; print(\"piper o...` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37753 | 2026-10-23 02:36 | COMPLETED | 00:00:00 | 2 cpu, 2000M |  | `srun -p ocf-hpc -w corruption -c 1 -t 2 bash -c hostname; which ffmpeg ¦¦ echo no-ffmpeg; ls ~/opt 2>/dev/null ¦ head` (in `./.claude/worktrees/tour-de-fly-dce498`) |  |
| 37853 | None | CANCELLED | 00:00:00 |  |  | `srun -p ocf-hpc -w corruption -c 8 --mem=24G -t 20 --quiet --chdir=/home/s/st/stevejobs/flybrain/.claude/worktrees/foresight-ai-science-rfp-b3f525/fly_brain bash -c /home/s/st/stevejobs/flybrain/venv/bin/python -m bra...` (in `./.claude/worktrees/foresight-ai-science-rfp-b3f525/fly_brain`) |  |
| 37854 | None | CANCELLED | 00:00:00 |  |  | `sbatch --parsable handsoff-gate.sbatch` (in `./.claude/worktrees/foresight-ai-science-rfp-b3f525`) |  |
| 37855 | None | CANCELLED | 00:00:00 |  |  | `srun -p ocf-hpc -w corruption -c 8 --mem=16G -t 30 --quiet --chdir=/home/s/st/stevejobs/flybrain/.claude/worktrees/foresight-ai-science-rfp-b3f525/fly_brain bash -c T=/tmp/claude-93015/-home-s-st-stevejobs-flybrain--c...` (in `./.claude/worktrees/foresight-ai-science-rfp-b3f525/fly_brain`) |  |
| 37923 | 2026-11-05 05:07 | FAILED | 00:00:00 | 4 cpu, 8G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 4 --mem=8G -t 5 --quiet bash -c cat /etc/os-release ¦ head -1; uname -r; nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader; ...` (in `./fly_brain`) |  |
| 37924 | 2026-11-05 05:07 | FAILED | 00:00:00 | 4 cpu, 8G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 4 --mem=8G -t 5 --quiet bash -c ls -la /usr/bin/python3.11 && /usr/bin/python3.11 -V && dpkg -l ¦ grep -E "^ii +(python3\.11¦libpython3\.11)" ¦ awk "{print \$2, \$3}"; /us...` (in `./fly_brain`) |  |
| 37925 | 2026-11-05 05:08 | COMPLETED | 00:00:06 | 2 cpu, 2G |  | `srun -p ocf-hpc -w corruption -c 2 --mem=2G -t 3 --quiet bash -c ls /opt/conda/bin/python 2>&1; /opt/conda/bin/python -V 2>&1; ldd --version ¦ head -1; curl -sI -m 5 https://conda.anaconda.org ¦ head -1` (in `./fly_brain`) |  |
| 37926 | 2026-11-05 05:09 | TIMEOUT | 00:15:09 | 8 cpu, 16G, 1 gpu | after the Debian 13 upgrade: re-run of balance-gate generation 0; ran on CPU because CUDA does not initialise (nvidia_uvm not loaded), timed out | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=16G -t 15 --quiet -J env-check env OMP_NUM_THREADS=8 ../venv-cuda/bin/python -m runs.ride --init-theta results/gate/v4.5_s201/init_hold.json --sigma-new 0.1 --sigm...` (in `./fly_brain`) | `/home/s/st/stevejobs/.cache/flybrain-smoke/gate_v4.5_s201_gen0.json` |
| 37927 | 2026-11-05 05:14 | CANCELLED | 00:15:38 | 8 cpu, 24G | 30-brain pre-test ladder for R3.5/R4/R5, on CPU with a GPU allocated; cancelled and resubmitted per rung without the GPU | `sbatch --parsable pretest-rungs.sbatch r35_s1 r4_s1 r5_s1 0.47 0.6 0.8 1 1.5 2` | [pretest-37927.out](logs/pretest-37927.out) |
| 37928 | 2026-11-05 05:14 | COMPLETED | 00:33:44 | 8 cpu, 24G | 30-brain pre-test of R0, R2, R3 at 0.47 (CPU) -> results/rungs/pretest_*_b30_w0.47.json | `sbatch --parsable pretest-rungs.sbatch r0 r2_s1 r3_s1 0.47` | [pretest-37928.out](logs/pretest-37928.out) |
| 37929 | 2026-11-05 05:25 | CANCELLED | 00:03:10 | 8 cpu, 40G | per-brain passenger screens; cancelled, wait for the GPU | `sbatch --parsable screen-rungs.sbatch r0 r1_s1 r2_s1 r3_s1` | [screen-rungs-37929.out](logs/screen-rungs-37929.out) |
| 37933 | None | CANCELLED | 00:00:00 | 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 2 --mem=4G -t 4 --quiet bash -c echo CVD=$CUDA_VISIBLE_DEVICES; ls -la /dev/nvidia* 2>&1 ¦ head -12; echo; lsmod ¦ grep -i nvidia; echo; cat /proc/driver/nvidia/version 2>...` (in `./fly_brain`) |  |
| 37934 | 2026-11-05 05:28 | COMPLETED | 00:00:02 | 2 cpu, 4G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 2 --mem=4G -t 4 --quiet bash -c echo CVD=$CUDA_VISIBLE_DEVICES; ls -la /dev/nvidia* 2>&1 ¦ head -12; echo; lsmod ¦ grep -i nvidia; echo; cat /proc/driver/nvidia/version 2>...` (in `./fly_brain`) |  |
| 37935 | 2026-11-05 05:28 | COMPLETED | 00:00:02 | 2 cpu, 4G, 1 gpu |  | `srun -p ocf-hpc -w corruption --gres=gpu:1 -c 2 --mem=4G -t 4 --quiet bash -c /sbin/modinfo nvidia-uvm 2>&1 ¦ head -3; /sbin/modinfo nvidia-current-uvm 2>&1 ¦ head -3; find /lib/modules/$(uname -r) -name "*uvm*" 2>/de...` (in `./fly_brain`) |  |
| 37936 | 2026-11-05 05:30 | CANCELLED | 00:32:28 | 16 cpu, 24G | 30-brain pre-test of R4 at 1.5 and 2.0 (CPU); cancelled during the 2.0 haltere probe (8 million spikes/s) | `sbatch --parsable --gres=none -c 16 --time=12:00:00 -J pretest-r4 pretest-rungs.sbatch r4_s1 1.5 2 1 0.8 0.6 0.47` | [pretest-37936.out](logs/pretest-37936.out) |
| 37937 | 2026-11-05 05:30 | COMPLETED | 01:25:10 | 12 cpu, 24G | 30-brain pre-test of R3.5 at 0.6 to 2.0 (CPU) | `sbatch --parsable --gres=none -c 12 --time=12:00:00 -J pretest-r35 pretest-rungs.sbatch r35_s1 0.6 0.8 1 1.5 2` | [pretest-37937.out](logs/pretest-37937.out) |
| 37938 | 2026-11-05 05:30 | CANCELLED | 12:30:06 | 48 cpu, 32G | pilot ride on R3 (balance gate unchanged, 4.5 m/s, seed 201) on CPU, 48 threads -> results/rungs/r3_s1_cpu/; generations 0 to 13, then cancelled so the search continues on the C kernel | `sbatch --parsable --gres=none -c 48 --mem=32G --time=1-00:00:00 -J ride-r3-cpu ride-rung.sbatch 4.5 201 results/variants/r3_s1.npz r3_s1_cpu 1320` | [ride-rung-37938.out](logs/ride-rung-37938.out) |
| 37940 | 2026-11-05 05:51 | COMPLETED | 01:05:30 | 8 cpu, 24G | 30-brain pre-test of R5 at 0.47 to 2.0 (CPU): passes at 2.0 | `sbatch --parsable --gres=none -c 8 --time=16:00:00 -J pretest-r5 pretest-rungs.sbatch r5_s1 2 1.5 1 0.8 0.6 0.47` | [pretest-37940.out](logs/pretest-37940.out) |
| 37941 | 2026-11-05 06:02 | CANCELLED | 00:13:29 | 16 cpu, 24G | fine scan of R4 above 1.5 (CPU): runaway at 1.6; 1.7 and 1.8 cancelled | `sbatch --parsable --gres=none -c 16 --time=06:00:00 -J pretest-r4-fine pretest-rungs.sbatch r4_s1 1.6 1.7 1.8` | [pretest-37941.out](logs/pretest-37941.out) |
| 37942 | 2026-11-05 06:02 | COMPLETED | 00:36:22 | 8 cpu, 24G | fine scan of R3.5 between 0.47 and 0.6 (CPU): no signal where the rate matches the real brain's | `sbatch --parsable --gres=none -c 8 --time=06:00:00 -J pretest-r35-fine pretest-rungs.sbatch r35_s1 0.5 0.53 0.56` | [pretest-37942.out](logs/pretest-37942.out) |
| 37943 | 2026-11-05 06:16 | CANCELLED | 00:11:14 | 40 cpu, 32G | pilot ride on R4 at scale 1.5; cancelled, the network runs away within 0.4 s of riding (4 million spikes/s per brain) | `sbatch --parsable --gres=none -c 40 --mem=32G --time=1-00:00:00 -J ride-r4-cpu ride-rung.sbatch 4.5 201 results/variants/r4_s1.npz r4_s1_w1.5_cpu 1320 1.5` | [ride-rung-37943.out](logs/ride-rung-37943.out) |
| 37944 | 2026-11-05 06:27 | COMPLETED | 00:10:32 | 16 cpu, 24G | R4 closed-loop stability: the reference replay at scales 1.0 to 1.4 -> riding rate matches the real brain's at 1.2 | `sbatch --parsable --gres=none -p ocf-hpc -w corruption -c 16 --mem=24G --time=04:00:00 -J r4-stability -o logs/r4-stability-%j.out --wrap set -e; cd fly_brain; export OMP_NUM_THREADS=16; mkdir -p $HOME/.cache/flybrain...` | `$HOME/.cache/flybrain-smoke/r4_w${S}_trace.json`, [r4-stability-37944.out](logs/r4-stability-37944.out) |
| 37945 | 2026-11-05 06:38 | CANCELLED | 07:29:23 | 40 cpu, 32G | pilot ride on R4 at scale 1.2 (balance gate unchanged, 4.5 m/s, seed 201) on CPU, 40 threads -> results/rungs/r4_s1_w1.2_cpu/ | `sbatch --parsable --gres=none -c 40 --mem=32G --time=1-00:00:00 -J ride-r4-cpu ride-rung.sbatch 4.5 201 results/variants/r4_s1.npz r4_s1_w1.2_cpu 1320 1.2` | [ride-rung-37945.out](logs/ride-rung-37945.out) |
| 37946 | 2026-11-05 18:00 | CANCELLED | 00:23:35 | 48 cpu, 32G | continuation of 37938 (runs/ride.py --resume), the first job on the C kernel: generations 14 and 15 in 681 s and 705 s; cancelled to hand over to 37949, which stops at 60 generations | `sbatch --parsable --gres=none -c 48 --mem=32G --time=1-00:00:00 -J ride-r3-cpu --dependency=afterany:37938 ride-rung.sbatch 4.5 201 results/variants/r3_s1.npz r3_s1_cpu 1320` | [ride-rung-37946.out](logs/ride-rung-37946.out) |
| 37947 | 2026-11-05 06:38 | COMPLETED | 01:08:40 | 8 cpu, 24G | 30-brain pre-test of R4 at 1.2, 1.3 and the rest of the ladder (CPU) | `sbatch --parsable --gres=none -c 8 --time=08:00:00 -J pretest-r4 pretest-rungs.sbatch r4_s1 1.2 1.3 1 0.8 0.6 0.47` | [pretest-37947.out](logs/pretest-37947.out) |
| 37948 | 2026-11-05 07:40 | CANCELLED | 10:31:08 | 32 cpu, 32G | pilot ride on R3, second CEM seed (202), on CPU, 32 threads -> results/rungs/r3_s1_cpu/v4.5_s202/; generations 0 to 8, then cancelled so the search continues on the C kernel | `sbatch --parsable --gres=none -c 32 --mem=32G --time=1-00:00:00 -J ride-r3-s202 ride-rung.sbatch 4.5 202 results/variants/r3_s1.npz r3_s1_cpu 1320` | [ride-rung-37948.out](logs/ride-rung-37948.out) |
| 37949 | 2026-11-05 18:23 | CANCELLED | 01:05:16 | 48 cpu, 32G | second continuation of the R3 pilot ride, seed 201: generations 16 and 17 on 48 threads (2,802 s and 1,064 s, sharing the node with the screens); replaced by 38043 on 32 threads | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 --export=ALL,GENS=60 -c 48 -J ride-r3-cpu --dependency=afterany:37946 ride-rung.sbatch 4.5 201 results/variants/r3_s1.npz r3_s1_cpu 1320` | [ride-rung-37949.out](logs/ride-rung-37949.out) |
| 37952 | 2026-11-05 18:11 | COMPLETED | 10:36:55 | 32 cpu, 32G | continuation of the R3 pilot ride, seed 202: generations 9 to 59 at 507 to 1,502 s each; the search ends at 60 generations with 11.14 s upright and 52% finishing in the last one | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 --export=ALL,GENS=60 -c 32 -J ride-r3-s202 --dependency=afterany:37948 ride-rung.sbatch 4.5 202 results/variants/r3_s1.npz r3_s1_cpu 1320` | [ride-rung-37952.out](logs/ride-rung-37952.out) |
| 37953 | 2026-11-06 04:48 | COMPLETED | 00:00:07 | 32 cpu, 32G | second continuation of the R3 pilot ride, seed 202: found the 60 generations done and stopped after 7 s | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 --export=ALL,GENS=60 -c 32 -J ride-r3-s202 --dependency=afterany:37952 ride-rung.sbatch 4.5 202 results/variants/r3_s1.npz r3_s1_cpu 1320` | [ride-rung-37953.out](logs/ride-rung-37953.out) |
| 38024 | 2026-11-05 17:16 | FAILED | 00:00:01 | 2 cpu, 2000M, 1 gpu |  | `srun -p ocf-hpc --gres=gpu:1 -c 1 --time=3 bash -c  ⏎ echo "== modules"; grep -i nvidia /proc/modules ⏎ echo "== dev"; ls -l /dev/nvidia* 2>&1 ⏎ echo "== driver"; cat /proc/driver/nvidia/version 2>&1 ¦ head -3 ⏎ echo ...` (in `./.claude/worktrees/project-pending-items-5ff0c7`) |  |
| 38025 | 2026-11-05 17:16 | COMPLETED | 00:00:00 | 2 cpu, 2000M, 1 gpu |  | `srun -p ocf-hpc --gres=gpu:1 -n 1 -c 1 --time=2 bash -c  ⏎ echo "== /etc/modprobe.d/nvidia.conf"; cat /etc/modprobe.d/nvidia.conf ⏎ echo "== /etc/nvidia/nvidia-modprobe.conf"; cat /etc/nvidia/nvidia-modprobe.conf 2>&1...` (in `./.claude/worktrees/project-pending-items-5ff0c7`) |  |
| 38026 | 2026-11-05 17:23 | FAILED | 00:00:00 | 16 cpu, 24G |  | `srun -p ocf-hpc --gres=none -c 16 --mem=24G --time=12 bash -c  ⏎ set -e; cd fly_brain; export OMP_NUM_THREADS=16 ⏎ lscpu ¦ grep -E 'Model name¦^CPU\(s\)¦NUMA node\(s\)¦Thread'; gcc --version ¦ head -1 ⏎ gcc -O3 -march...` |  |
| 38027 | 2026-11-05 17:23 | COMPLETED | 00:07:16 | 16 cpu, 24G |  | `srun -p ocf-hpc --gres=none -c 16 --mem=24G --time=12 bash -c  ⏎ set -e; cd fly_brain; export OMP_NUM_THREADS=16 ⏎ gcc -O3 -march=native -fopenmp -ffp-contract=off -fPIC -shared -o /home/s/st/stevejobs/flybrain/.claud...` |  |
| 38028 | 2026-11-05 17:31 | COMPLETED | 00:04:29 | 16 cpu, 24G |  | `srun -p ocf-hpc --gres=none -c 16 --mem=24G --time=12 bash -c  ⏎ set -e; cd fly_brain; export OMP_NUM_THREADS=16 ⏎ for cfg in '300 20' '600 30' '1000 40'; do PYTHONPATH=. ../venv/bin/python /home/s/st/stevejobs/flybra...` |  |
| 38029 | 2026-11-05 17:39 | COMPLETED | 00:00:08 | 16 cpu, 32G |  | `srun -p ocf-hpc --gres=none -c 16 --mem=32G --time=12 bash -c  ⏎ set -e; cd /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/fly_brain; export OMP_NUM_THREADS=16 ⏎ for cfg in '300 20' '450 ...` |  |
| 38030 | 2026-11-05 17:39 | COMPLETED | 00:09:06 | 16 cpu, 32G |  | `srun -p ocf-hpc --gres=none -c 16 --mem=32G --time=12 bash -c  ⏎ set -e; cd /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/fly_brain; export OMP_NUM_THREADS=16 ⏎ for cfg in '300 20' '450 ...` |  |
| 38035 | 2026-11-05 18:22 | COMPLETED | 00:48:36 | 16 cpu, 40G | per-brain passenger screens of R0, R1, R2, R3 on CPU with the C kernel -> results/rungs/screens/ | `sbatch --parsable --gres=none -c 16 --mem=40G --time=06:00:00 -J screen-rungs screen-rungs.sbatch r0 r1_s1 r2_s1 r3_s1` | [screen-rungs-38035.out](logs/screen-rungs-38035.out) |
| 38036 | 2026-11-06 00:53 | COMPLETED | 03:27:01 | 32 cpu, 32G | pilot of the Track A readout on the real wiring: top-8 screened descending neurons, 4.5 m/s, seed 201, 30 generations (CPU, 32 threads); ends at 7.21 s upright with 6% finishing, most rides ending off the road | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 -c 48 --export=ALL,GENS=30 -J ride-r0-top8 --dependency=afterany:37949 ride-readout.sbatch 4.5 201 r0 topk 8 1320` | [ride-readout-38036.out](logs/ride-readout-38036.out) |
| 38037 | 2026-11-06 04:48 | COMPLETED | 03:46:55 | 32 cpu, 32G | pilot of the sensory-bypass readout on the real wiring, 4.5 m/s, seed 201, 30 generations (CPU, 32 threads); ends at 13.92 s upright with 77% finishing | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 -c 32 --export=ALL,GENS=30 -J ride-r0-bypass --dependency=afterany:37953 ride-readout.sbatch 4.5 201 r0 bypass 8 1320` | [ride-readout-38037.out](logs/ride-readout-38037.out) |
| 38038 | 2026-11-06 04:20 | COMPLETED | 07:28:19 | 32 cpu, 32G | pilot ride on R1 (balance gate unchanged, 4.5 m/s, seed 201, 60 generations) on CPU, 91 to 565 s a generation; ends at 7.01 s upright with 8% finishing (R0: 13.71 and 11.89 s) -> results/rungs/r1_s1_cpu/ | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 -c 48 --export=ALL,GENS=60 -J ride-r1-cpu --dependency=afterany:38036 ride-rung.sbatch 4.5 201 results/variants/r1_s1.npz r1_s1_cpu 1320` | [ride-rung-38038.out](logs/ride-rung-38038.out) |
| 38039 | 2026-11-06 12:12 | COMPLETED | 07:58:22 | 32 cpu, 32G | pilot ride on R2 (balance gate unchanged, 4.5 m/s, seed 201, 60 generations) on CPU: 13.42 s in the last generation, 69% finishing, at the real wiring's level (13.71 and 11.89 s) -> results/rungs/r2_s1_cpu/ | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 -c 32 --export=ALL,GENS=60 -J ride-r2-cpu --dependency=afterany:38037 ride-rung.sbatch 4.5 201 results/variants/r2_s1.npz r2_s1_cpu 1320` | [ride-rung-38039.out](logs/ride-rung-38039.out) |
| 38043 | 2026-11-05 19:29 | COMPLETED | 05:24:28 | 32 cpu, 32G | last continuation of the R3 pilot ride, seed 201, on 32 threads: generations 18 to 59 at 436 to 504 s each; the search ends at 60 generations with 11.48 s upright and 42% finishing in the last one | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 --export=ALL,GENS=60 -c 32 -J ride-r3-cpu --dependency=afterany:37949 ride-rung.sbatch 4.5 201 results/variants/r3_s1.npz r3_s1_cpu 1320` | [ride-rung-38043.out](logs/ride-rung-38043.out) |
| 38077 | 2026-11-06 04:23 | COMPLETED | 00:14:08 | 16 cpu, 16G | replay of the top-8 pilot's final CEM mean, 48 riders x 15 s, seed 201: 9.04 s upright, 7 finish, 41 leave the road, none falls -> results/rungs/r0/top8/v4.5_s201/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-top8 -o logs/replay-r0-top8-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_bra...` | `/home/s/st/stevejobs/.cache/sb-replay/top8_mu_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused.json`, [replay-r0-top8-38077.out](logs/replay-r0-top8-38077.out) |
| 38078 | 2026-11-06 08:35 | COMPLETED | 03:36:39 | 32 cpu, 32G | pilot of the Track A readout on the real wiring: top-32 screened descending neurons, 4.5 m/s, seed 201, 30 generations (CPU, 32 threads); ends at 6.24 s upright with no rider finishing (5.34 to 7.66 s from generation 4 on), most rides ending off the road | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 -c 32 --export=ALL,GENS=30 -J ride-r0-top32 --dependency=afterany:38037 ride-readout.sbatch 4.5 201 r0 topk 32 1320` | [ride-readout-38078.out](logs/ride-readout-38078.out) |
| 38079 | 2026-11-06 11:48 | COMPLETED | 02:34:28 | 32 cpu, 32G | pilot of the random-k control on the real wiring: 8 descending neurons drawn at random from the screen's pool (readout seed 0), 4.5 m/s, seed 201, 30 generations (CPU, 32 threads); ends at 4.06 s upright with no rider finishing, below the hands-off bike | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 -c 32 --export=ALL,GENS=30 -J ride-r0-rand8 --dependency=afterany:38038 ride-readout.sbatch 4.5 201 r0 randk 8 1320` | [ride-readout-38079.out](logs/ride-readout-38079.out) |
| 38081 | 2026-11-06 08:37 | COMPLETED | 00:14:38 | 16 cpu, 16G | replay of the bypass pilot's final CEM mean, 48 riders x 15 s, seed 201: all 48 ride the full 15 s, none leaves the road -> results/rungs/r0/bypass/v4.5_s201/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-bypass -o logs/replay-r0-bypass-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly...` | `/home/s/st/stevejobs/.cache/sb-replay/bypass_mu_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused.json`, [replay-r0-bypass-38081.out](logs/replay-r0-bypass-38081.out) |
| 38082 | 2026-11-06 08:51 | COMPLETED | 00:13:16 | 16 cpu, 16G | hands-off replay (blank steering) without the off-road rule, 48 riders x 15 s, seed 201: 8.65 s upright, 46 fall, 2 still upright at 15 s -> results/rungs/r0/handsoff/v4.5_s201/replay_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -d afterany:38081 -J replay-r0-handsoff-noroad -o logs/replay-r0-handsoff-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; ...` | `/home/s/st/stevejobs/.cache/sb-replay/handsoff_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused.json`, [replay-r0-handsoff-noroad-38082.out](logs/replay-r0-handsoff-noroad-38082.out) |
| 38083 | 2026-11-06 09:05 | COMPLETED | 00:13:07 | 16 cpu, 16G | replay of the top-8 pilot's final CEM mean without the off-road rule, 48 riders x 15 s, seed 201: all 48 upright for 15 s, 34 of them more than 3.5 m from the center line at the end -> results/rungs/r0/top8/v4.5_s201/replay_mu_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -d afterany:38082 -J replay-r0-top8-noroad -o logs/replay-r0-top8-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home...` | `/home/s/st/stevejobs/.cache/sb-replay/top8_mu_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused.json`, [replay-r0-top8-noroad-38083.out](logs/replay-r0-top8-noroad-38083.out) |
| 38084 | 2026-11-06 09:18 | COMPLETED | 00:07:38 | 16 cpu, 16G | hands-off replay (blank steering) with the off-road rule, 48 riders x 15 s, seed 201: 5.38 s upright, 41 leave the road, 7 fall, none finishes -> results/rungs/r0/handsoff/v4.5_s201/replay_road_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -d afterany:38083 -J replay-r0-handsoff-road -o logs/replay-r0-handsoff-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /...` | `/home/s/st/stevejobs/.cache/sb-replay/handsoff_road_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused.json`, [replay-r0-handsoff-road-38084.out](logs/replay-r0-handsoff-road-38084.out) |
| 38085 | 2026-11-06 09:29 | CANCELLED | 00:01:01 | 16 cpu, 32G | bypass search at synapse scale 0, meant as a bypass with no brain; cancelled after a minute: scale 0 also zeroes the Poisson kick (w_syn x f_poi), so the driven neurons were silent. Replaced by the bypass0 readout (--no-synapses) | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 -c 16 --export=ALL,GENS=30 -J ride-r0-bypass-w0 ride-readout.sbatch 4.5 201 r0 bypass 8 1320 0` | [ride-readout-38085.out](logs/ride-readout-38085.out) |
| 38086 | 2026-11-06 09:31 | COMPLETED | 02:45:49 | 16 cpu, 32G | the bypass pilot repeated with every synapse switched off (bypass0, runs/ride.py --no-synapses), 4.5 m/s, seed 201, 30 generations (CPU, 16 threads): ends at 13.91 s upright with 81% finishing, never more than 0.085 s from the bypass pilot (38037) in any generation -> results/rungs/r0/bypass_nosyn/ | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 -c 16 --export=ALL,GENS=30 -J ride-r0-bypass0 ride-readout.sbatch 4.5 201 r0 bypass0 8 1320` | [ride-readout-38086.out](logs/ride-readout-38086.out) |
| 38087 | 2026-11-06 11:51 | FAILED | 00:00:00 | 2 cpu, 12G | first try of the sign-flip count of the R1 draw (srun): the script was in the login VM's /tmp, which the node does not see | `srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-project-pending-items-5ff0c...` (in `./fly_brain`) |  |
| 38088 | 2026-11-06 11:51 | FAILED | 00:00:00 | 2 cpu, 12G | sign-flip count, second try: bike package not on the path | `srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/.cache/sb-replay/r1_flips.py /home/s/st/stevejobs/.cache/sb-replay/r1_fl...` (in `./fly_brain`) |  |
| 38089 | 2026-11-06 11:51 | FAILED | 00:00:04 | 2 cpu, 12G | sign-flip count, third try: stopped on a missing type name | `srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/.cache/sb-replay/r1_flips.py /home/s/st/stevejobs/.cache/sb...` (in `./fly_brain`) |  |
| 38090 | 2026-11-06 11:51 | FAILED | 00:00:03 | 2 cpu, 12G | sign-flip count, fourth try: wrong side column | `srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/.cache/sb-replay/r1_flips.py /home/s/st/stevejobs/.cache/sb...` (in `./fly_brain`) |  |
| 38091 | 2026-11-06 11:51 | COMPLETED | 00:00:04 | 2 cpu, 12G | sign-flip count of the R1 draw (scratch script; redone as tools/r1_flips.py in job 38102) | `srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/.cache/sb-replay/r1_flips.py /home/s/st/stevejobs/.cache/sb...` (in `./fly_brain`) |  |
| 38092 | 2026-11-06 11:53 | COMPLETED | 00:16:56 | 16 cpu, 16G | replay of the R1 pilot's final CEM mean, 48 riders x 15 s, seed 201: 10.12 s upright, 10 finish, 37 leave the road, 1 falls -> results/rungs/r1_s1_cpu/v4.5_s201/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r1_s201-road -o logs/replay-r1_s201-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybra...` | `/home/s/st/stevejobs/.cache/sb-replay/r1_s201_mu_road_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r1_s201_road.json`, [replay-r1_s201-road-38092.out](logs/replay-r1_s201-road-38092.out) |
| 38093 | 2026-11-06 11:53 | COMPLETED | 00:14:46 | 16 cpu, 16G | replay of the gate's final CEM mean (R0, seed 201) on CPU, 48 riders x 15 s, seed 201: 14.79 s upright, 46 finish, 2 leave the road, none falls -> results/gate/v4.5_s201/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r0_s201-road -o logs/replay-r0_s201-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybra...` | `/home/s/st/stevejobs/.cache/sb-replay/r0_s201_mu_road_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r0_s201_road.json`, [replay-r0_s201-road-38093.out](logs/replay-r0_s201-road-38093.out) |
| 38094 | 2026-11-06 11:53 | COMPLETED | 00:15:36 | 16 cpu, 16G | replay of the R3 pilot's final CEM mean (seed 201), 48 riders x 15 s, seed 201: 12.25 s upright, 22 finish, 26 leave the road, none falls -> results/rungs/r3_s1_cpu/v4.5_s201/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r3_s201-road -o logs/replay-r3_s201-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybra...` | `/home/s/st/stevejobs/.cache/sb-replay/r3_s201_mu_road_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r3_s201_road.json`, [replay-r3_s201-road-38094.out](logs/replay-r3_s201-road-38094.out) |
| 38095 | 2026-11-06 12:08 | COMPLETED | 00:15:08 | 16 cpu, 16G | replay of the gate's final CEM mean (R0, seed 202) on CPU, 48 riders x 15 s, seed 201: 14.52 s upright, 44 finish, 4 leave the road, none falls -> results/gate/v4.5_s202/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r0_s202-road -o logs/replay-r0_s202-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybra...` | `/home/s/st/stevejobs/.cache/sb-replay/r0_s202_mu_road_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r0_s202_road.json`, [replay-r0_s202-road-38095.out](logs/replay-r0_s202-road-38095.out) |
| 38096 | 2026-11-06 12:08 | COMPLETED | 00:15:32 | 16 cpu, 16G | replay of the R3 pilot's final CEM mean (seed 202), 48 riders x 15 s, seed 201: 12.73 s upright, 28 finish, 17 leave the road, 3 fall -> results/rungs/r3_s1_cpu/v4.5_s202/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r3_s202-road -o logs/replay-r3_s202-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybra...` | `/home/s/st/stevejobs/.cache/sb-replay/r3_s202_mu_road_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r3_s202_road.json`, [replay-r3_s202-road-38096.out](logs/replay-r3_s202-road-38096.out) |
| 38097 | 2026-11-06 12:10 | COMPLETED | 00:15:40 | 16 cpu, 16G | replay of the R1 pilot's final CEM mean without the off-road rule: 47 of 48 upright for 15 s, 35 of them more than 3.5 m from the center line, 1 falls -> results/rungs/r1_s1_cpu/v4.5_s201/replay_mu_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r1_s201-noroad -o logs/replay-r1_s201-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/fl...` | `/home/s/st/stevejobs/.cache/sb-replay/r1_s201_mu_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r1_s201_noroad.json`, [replay-r1_s201-noroad-38097.out](logs/replay-r1_s201-noroad-38097.out) |
| 38098 | 2026-11-06 12:17 | COMPLETED | 00:14:23 | 16 cpu, 16G | replay of the gate's final CEM mean (R0, seed 201) without the off-road rule: all 48 upright for 15 s, 1 more than 3.5 m from the center line -> results/gate/v4.5_s201/replay_mu_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r0_s201-noroad -o logs/replay-r0_s201-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/fl...` | `/home/s/st/stevejobs/.cache/sb-replay/r0_s201_mu_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r0_s201_noroad.json`, [replay-r0_s201-noroad-38098.out](logs/replay-r0_s201-noroad-38098.out) |
| 38099 | 2026-11-06 12:23 | COMPLETED | 00:14:14 | 16 cpu, 16G | replay of the R3 pilot's final CEM mean (seed 201) without the off-road rule: all 48 upright for 15 s, 18 more than 3.5 m from the center line -> results/rungs/r3_s1_cpu/v4.5_s201/replay_mu_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r3_s201-noroad -o logs/replay-r3_s201-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/fl...` | `/home/s/st/stevejobs/.cache/sb-replay/r3_s201_mu_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r3_s201_noroad.json`, [replay-r3_s201-noroad-38099.out](logs/replay-r3_s201-noroad-38099.out) |
| 38100 | 2026-11-06 12:24 | COMPLETED | 00:14:31 | 16 cpu, 16G | replay of the gate's final CEM mean (R0, seed 202) without the off-road rule: all 48 upright for 15 s, 3 more than 3.5 m from the center line -> results/gate/v4.5_s202/replay_mu_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r0_s202-noroad -o logs/replay-r0_s202-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/fl...` | `/home/s/st/stevejobs/.cache/sb-replay/r0_s202_mu_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r0_s202_noroad.json`, [replay-r0_s202-noroad-38100.out](logs/replay-r0_s202-noroad-38100.out) |
| 38101 | 2026-11-06 12:25 | COMPLETED | 00:14:51 | 16 cpu, 16G | replay of the R3 pilot's final CEM mean (seed 202) without the off-road rule: 44 of 48 upright for 15 s, 10 of them more than 3.5 m from the center line, 4 fall -> results/rungs/r3_s1_cpu/v4.5_s202/replay_mu_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r3_s202-noroad -o logs/replay-r3_s202-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/fl...` | `/home/s/st/stevejobs/.cache/sb-replay/r3_s202_mu_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r3_s202_noroad.json`, [replay-r3_s202-noroad-38101.out](logs/replay-r3_s202-noroad-38101.out) |
| 38102 | 2026-11-06 12:32 | COMPLETED | 00:00:05 | 2 cpu, 12G | tools/r1_flips.py on the R1 draw (srun, 2 threads): where the sign flips fall -> results/rungs/r1_s1_cpu/sign_flips.json | `srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/too...` (in `./fly_brain`) |  |
| 38104 | 2026-11-06 12:32 | COMPLETED | 00:13:19 | 16 cpu, 16G | replay of the top-32 pilot's final CEM mean, 48 riders x 15 s, seed 201: 8.88 s upright, 2 finish, 46 leave the road, none falls -> results/rungs/r0/top32/v4.5_s201/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-top32-road -o logs/replay-r0-top32-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flyb...` | `/home/s/st/stevejobs/.cache/sb-replay/top32_mu_road_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_top32_road.json`, [replay-r0-top32-road-38104.out](logs/replay-r0-top32-road-38104.out) |
| 38105 | 2026-11-06 12:40 | COMPLETED | 00:13:38 | 16 cpu, 16G | replay of the top-32 pilot's final CEM mean without the off-road rule: all 48 upright for 15 s, 44 of them more than 3.5 m from the center line -> results/rungs/r0/top32/v4.5_s201/replay_mu_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-top32-noroad -o logs/replay-r0-top32-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/...` | `/home/s/st/stevejobs/.cache/sb-replay/top32_mu_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_top32_noroad.json`, [replay-r0-top32-noroad-38105.out](logs/replay-r0-top32-noroad-38105.out) |
| 38106 | 2026-11-06 12:57 | COMPLETED | 00:00:48 | 2 cpu, 12G | second R1 rewiring draw (brain/variants.py r1 --seed 2, srun) -> results/variants/r1_s2.npz | `srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m brain.variants r1 --seed 2` (in `./fly_brain`) |  |
| 38107 | 2026-11-06 14:23 | COMPLETED | 08:04:22 | 32 cpu, 32G | pilot ride on R1, rewiring draw 2 (balance gate unchanged, 4.5 m/s, seed 201, 60 generations) on CPU, started when the random-8 pilot (38079) ended: 11.75 s in the last generation, 40% finishing, 8% below the real wiring (draw 1: 7.01 s) -> results/rungs/r1_s2_cpu/ | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 -c 32 --export=ALL,GENS=60 -J ride-r1s2-cpu --dependency=afterany:38079 ride-rung.sbatch 4.5 201 results/variants/r1_s2.npz r1_s2_cpu 1320` | [ride-rung-38107.out](logs/ride-rung-38107.out) |
| 38108 | 2026-11-06 20:10 | RUNNING | 03:19:15 | 32 cpu, 32G | pilot ride on R1, draw 1, second CEM seed (202; balance gate unchanged, 4.5 m/s, 60 generations) on CPU, queued after the R2 ride (38039) -> results/rungs/r1_s1_cpu/v4.5_s202 | `sbatch --parsable --gres=none --mem=32G --time=1-00:00:00 -c 32 --export=ALL,GENS=60 -J ride-r1-s202-cpu --dependency=afterany:38039 ride-rung.sbatch 4.5 202 results/variants/r1_s1.npz r1_s1_cpu 1320` | [ride-rung-38108.out](logs/ride-rung-38108.out) |
| 38109 | 2026-11-06 12:59 | COMPLETED | 00:00:05 | 2 cpu, 12G | tools/r1_flips.py on R1 draw 2 (srun) -> results/rungs/r1_s2_cpu/sign_flips.json | `srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/too...` (in `./fly_brain`) |  |
| 38110 | 2026-11-06 13:01 | COMPLETED | 00:00:03 | 2 cpu, 8G | scratch look at the r0 screen (srun; script outside the repo): the pool's top 8 neurons by correlation with roll rate, lateral offset, heading, yaw rate, lean and handlebar angle, and the screen rows of the hand-picked lane types; prints only | `srun -p ocf-hpc -w corruption --gres=none --mem=8G --time=00:10:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/.cache/sb-replay/screen_lane.py` (in `./fly_brain`) |  |
| 38111 | 2026-11-06 14:24 | COMPLETED | 00:10:01 | 16 cpu, 16G | replay of the random-8 pilot's final CEM mean, 48 riders x 15 s, seed 201: 5.51 s upright, none finishes, 38 leave the road, 10 fall -> results/rungs/r0/rand8_r0/v4.5_s201/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-rand8-road -o logs/replay-r0-rand8-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flyb...` | `/home/s/st/stevejobs/.cache/sb-replay/rand8_mu_road_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_rand8_road.json`, [replay-r0-rand8-road-38111.out](logs/replay-r0-rand8-road-38111.out) |
| 38112 | 2026-11-06 14:24 | COMPLETED | 00:12:36 | 16 cpu, 16G | replay of the random-8 pilot's final CEM mean without the off-road rule: all 48 fall, 7.82 s upright on average -> results/rungs/r0/rand8_r0/v4.5_s201/replay_mu_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-rand8-noroad -o logs/replay-r0-rand8-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/...` | `/home/s/st/stevejobs/.cache/sb-replay/rand8_mu_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_rand8_noroad.json`, [replay-r0-rand8-noroad-38112.out](logs/replay-r0-rand8-noroad-38112.out) |
| 38118 | 2026-11-06 22:27 | COMPLETED | 00:13:11 | 16 cpu, 16G | replay of the R2 pilot's final CEM mean, 48 riders x 15 s, seed 201, with the off-road rule: 14.68 s upright, 46 finish, 2 leave the road, none falls -> results/rungs/r2_s1_cpu/v4.5_s201/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 --dependency=afterany:38107 -J replay-r2_s201-road -o logs/replay-r2_s201-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd...` | `/home/s/st/stevejobs/.cache/sb-replay/r2_s201_mu_road_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r2_s201_road.json`, [replay-r2_s201-road-38118.out](logs/replay-r2_s201-road-38118.out) |
| 38119 | 2026-11-06 22:27 | COMPLETED | 00:13:05 | 16 cpu, 16G | replay of the R2 pilot's final CEM mean without the off-road rule: all 48 upright for 15 s and all within 3.5 m of the center line (median 0.9 m) -> results/rungs/r2_s1_cpu/v4.5_s201/replay_mu_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 --dependency=afterany:38107 -J replay-r2_s201-noroad -o logs/replay-r2_s201-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16...` | `/home/s/st/stevejobs/.cache/sb-replay/r2_s201_mu_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r2_s201_noroad.json`, [replay-r2_s201-noroad-38119.out](logs/replay-r2_s201-noroad-38119.out) |
| 38120 | 2026-11-06 22:43 | COMPLETED | 00:13:05 | 16 cpu, 16G | replay of the R1 draw-2 pilot's final CEM mean, 48 riders x 15 s, seed 201, with the off-road rule: 13.47 s upright, 29 finish, 15 leave the road, 4 fall -> results/rungs/r1_s2_cpu/v4.5_s201/replay_mu_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r1d2_s201-road -o logs/replay-r1d2_s201-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/fl...` | `/home/s/st/stevejobs/.cache/sb-replay/r1d2_s201_mu_road_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r1d2_s201_road.json`, [replay-r1d2_s201-road-38120.out](logs/replay-r1d2_s201-road-38120.out) |
| 38121 | 2026-11-06 22:43 | COMPLETED | 00:12:46 | 16 cpu, 16G | replay of the R1 draw-2 pilot's final CEM mean without the off-road rule: 39 of 48 upright for 15 s, 9 fall, 7 of the 39 beyond 3.5 m -> results/rungs/r1_s2_cpu/v4.5_s201/replay_mu_noroad_summary.json | `sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r1d2_s201-noroad -o logs/replay-r1d2_s201-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejob...` | `/home/s/st/stevejobs/.cache/sb-replay/r1d2_s201_mu_noroad_trace.json`, `/home/s/st/stevejobs/.cache/sb-replay/unused_r1d2_s201_noroad.json`, [replay-r1d2_s201-noroad-38121.out](logs/replay-r1d2_s201-noroad-38121.out) |

## Full command lines

**36053** (bash)

```bash
srun -p ocf-hpc --gres=gpu:1 -c 4 --mem=8G -t 5 bash -c hostname; nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv; which python3 conda; python3 --version; ls /opt/conda/bin 2>/dev/null | head -3; python3 -c "import torch;print(torch.__version__, torch.cuda.is_available())" 2>&1; df -h /scratch /tmp 2>/dev/null | tail -2
```

**36059** (env)

```bash
srun -p ocf-hpc -w corruption -c 32 --mem=4G -t 3 --quiet env OMP_NUM_THREADS=32 venv/bin/python -c 
import os, torch; print('affinity', len(os.sched_getaffinity(0)), 'torch threads', torch.get_num_threads(), 'OMP', os.environ.get('OMP_NUM_THREADS'))
```

**36080** (env)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 15 --quiet --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 venv-cuda/bin/python -m runs.bench_gpu --devices cuda --trials 512 --out results/bench_gpu_512.json
```

**36081** (env)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 15 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 venv-cuda/bin/python -m runs.bench_gpu --devices cuda --trials 512 --out results/bench_gpu_512.json
```

**36082** (env)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 15 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --devices cuda --trials 512 --out results/bench_gpu_512.json
```

**36093** (python)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 25 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --replay results/ride.json --riders 16 --seconds 12 --seed 7 --trace results/ride_trace.json
```

**36094** (env)

```bash
srun -p ocf-hpc -w corruption -c 32 --mem=48G -t 40 --quiet env OMP_NUM_THREADS=32 /home/s/st/stevejobs/flybrain/venv/bin/python -m runs.ride --replay results/ride.json --riders 16 --seconds 12 --seed 7 --device cpu --trace results/ride_trace.json
```

**36095** (python)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --replay results/ride_b.json --riders 16 --seconds 15 --seed 7 --trace results/ride_b_trace.json
```

**36105** (python)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --init results/screen_lane_samples.npz --lane hs --dagger 2 --riders 4 --seconds 0.5 --out /tmp/claude-93015/-home-s-st-stevejobs-flybrain/ff3d4c1f-4087-4f88-b1bd-f60320256b54/scratchpad/dagger_smoke.json
```

**36106** (python)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --init results/screen_lane_samples.npz --lane hs --dagger 2 --riders 4 --seconds 0.5 --out results/dagger_smoke.json
```

**36110** (env)

```bash
srun -p ocf-hpc -w corruption -c 48 --mem=64G -t 60 --quiet env OMP_NUM_THREADS=48 /home/s/st/stevejobs/flybrain/venv/bin/python -m runs.screen --riders 16 --seconds 8 --lane hs --device cpu --out results/screen_lane_psi.json
```

**36111** (python)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 15 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.screen --riders 16 --seconds 8 --lane hs --polarity physio --out results/screen_physio.json
```

**36129** (python)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 30 --quiet /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --replay results/ride_slow_mu.json --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --riders 16 --seconds 20 --seed 7 --trace results/ride_slow_mu_trace.json
```

**36138** (env)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 30 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --graph --devices cuda --trials 1 8 32 128 --out results/bench_graph.json
```

**36140** (env)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 30 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --graph --devices cuda --trials 1 8 32 128 --out results/bench_graph2.json
```

**36143** (env)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=32G -t 40 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --graph --devices cuda --trials 1 8 32 128 --out results/bench_graph3.json
```

**36146** (env)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=48G -t 40 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --graph --devices cuda --trials 1 8 32 128 512 1024 --out results/bench_graph4.json
```

**36147** (env)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=48G -t 40 --chdir=/home/s/st/stevejobs/flybrain/fly_brain env OMP_NUM_THREADS=8 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bar --device cuda --graph --tag _gpu
```

**36487** (python)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=40G -t 30 --quiet ../venv-cuda/bin/python -m runs.ride --open-loop --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --riders 16 --seconds 20 --seed 7 --trace results/ride_pilot_trace.json
```

**36488** (python)

```bash
srun -p ocf-hpc -w corruption -c 4 --mem=8G -t 10 --quiet ../venv/bin/python -m runs.ride --oracle --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --riders 16 --seconds 20 --seed 7 --trace results/ride_oracle_trace.json
```

**36489** (python)

```bash
srun -p ocf-hpc -w corruption -c 12 --mem=40G -t 12 --quiet ../venv-cuda/bin/python -m runs.ride --open-loop --device cpu --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --riders 16 --seconds 1 --seed 7 --trace results/scratch_cpu_test.json
```

**36490** (python)

```bash
srun -p ocf-hpc -w corruption -c 12 --mem=40G -t 90 --quiet ../venv-cuda/bin/python -m runs.ride --open-loop --device cpu --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --riders 16 --seconds 20 --seed 7 --trace results/ride_pilot_road_trace.json
```

**36491** (python)

```bash
srun -p ocf-hpc -w corruption -c 4 --mem=16G -t 14 --quiet ../venv-cuda/bin/python -m runs.ride --replay results/ride_slow_mu.json --device cpu --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --riders 2 --seconds 0.5 --seed 7 --trace results/scratch_t.json --brain-out results/scratch_brain.npz
```

**36492** (python)

```bash
srun -p ocf-hpc -w corruption -c 12 --mem=48G -t 120 --quiet ../venv-cuda/bin/python -m runs.ride --replay results/ride_slow_mu.json --device cpu --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --riders 16 --seconds 20 --seed 7 --trace results/ride_road_trace.json --brain-out results/ride_road_brain.npz
```

**36519** (python)

```bash
srun -p ocf-hpc -w corruption -c 4 --mem=16G -t 14 --quiet ../venv-cuda/bin/python -m runs.ride --device cpu --readout lane --lane hs --lane-filter results/probe.json --tau-lane-ms 300 --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --offroad 3.5 --center-batch --zbar results/lane/zbar_mu.npy --sigma-pedal 0 --riders 3 --seconds 0.6 --generations 2 --seed 5 --out /tmp/claude-93015/-home-s-st-stevejobs-flybrain/ff3d4c1f-4087-4f88-b1bd-f60320256b54/scratchpad/att_test/cem.json --log-attempts /tmp/claude-93015/-home-s-st-stevejobs-flybrain/ff3d4c1f-4087-4f88-b1bd-f60320256b54/scratchpad/att_test
```

**36520** (python)

```bash
srun -p ocf-hpc -w corruption -c 4 --mem=16G -t 14 --quiet ../venv-cuda/bin/python -m runs.ride --device cpu --readout lane --lane hs --lane-filter results/probe.json --tau-lane-ms 300 --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --offroad 3.5 --center-batch --zbar results/lane/zbar_mu.npy --sigma-pedal 0 --init-theta results/attempts/init_blank.json --sigma-new 0.1 --sigma0 0.3 --riders 3 --seconds 0.6 --generations 2 --seed 5 --out results/attempts_test/cem.json --log-attempts results/attempts_test
```

**36533** (connectome-build)

```bash
sbatch -p ocf-hpc -w corruption -c 8 --mem=64G -J connectome-build -o ../logs/rewrite/connectome-build-%j.out --wrap cd /home/s/st/stevejobs/flybrain/.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain && ~/flybrain/venv-cuda/bin/python -m brain.connectome
```

**36535** (engine-equiv)

```bash
sbatch -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -J engine-equiv -o ../logs/rewrite/equiv-%j.out --wrap cd /home/s/st/stevejobs/flybrain/.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain && ~/flybrain/venv-cuda/bin/python ../logs/rewrite/equiv.py
```

**36540** (ride-replay-new)

```bash
sbatch -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -t 60 -J ride-replay-new -o ../logs/rewrite/ride-replay-%j.out --wrap cd /home/s/st/stevejobs/flybrain/.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain && P=~/flybrain/venv-cuda/bin/python; $P -m runs.ride --replay results/lane/cem_mu.json --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --riders 16 --seconds 20 --seed 7 --center-batch --trace /tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-commit-dc73073-investigation-a94327/429f3982-d7b5-4efc-acd7-32979c1cb3e7/scratchpad/road_trace_new.json 2>&1 | grep -E '^replay|Error|Traceback|error' ; $P -m runs.ride --open-loop --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --riders 16 --seconds 20 --seed 7 --center-batch --trace /tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-commit-dc73073-investigation-a94327/429f3982-d7b5-4efc-acd7-32979c1cb3e7/scratchpad/pilot_trace_new.json 2>&1 | grep -E '^open loop|Error|Traceback|error'
```

**36541** (dashboard-export)

```bash
sbatch -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=64G -t 60 -J dashboard-export -o ../logs/rewrite/dashboard-%j.out --wrap cd /home/s/st/stevejobs/flybrain/.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain && ~/flybrain/venv-cuda/bin/python -m export.export_dashboard && ~/flybrain/venv-cuda/bin/python export/pack_dashboard.py
```

**36542** (ride-replay-045)

```bash
sbatch -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=48G -t 60 -J ride-replay-045 -o ../logs/rewrite/ride-replay-045-%j.out --wrap cd /home/s/st/stevejobs/flybrain/.claude/worktrees/commit-dc73073-investigation-a94327/fly_brain && ~/flybrain/venv-cuda/bin/python -m runs.ride --replay results/lane/cem_mu.json --tau-lane-ms 300 --lane-filter results/probe.json --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 5.5 --gust 5 --riders 16 --seconds 20 --seed 7 --center-batch --w-syn-scale 0.45 2>&1 | grep -E '^replay|Error|Traceback|rror:'
```

**36549** (bash)

```bash
srun -p ocf-hpc -w corruption -c 8 --mem=48G -t 30 bash -c /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_road_trace.json results/ride_3d.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride results/ride_road_trace.json results/ride_view.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_pilot_road_trace.json results/ride_pilot_3d.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride results/ride_pilot_road_trace.json results/ride_pilot_view.html
```

**36554** (python)

```bash
srun -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=96G -t 25 --immediate=300 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.bench_gpu --devices cuda --trials 1 128 1024 --graph --out ../logs/rewrite/bench_graph_engine.json
```

**36627** (flybrain-checks)

```bash
sbatch --parsable --dependency=afterany:36626 -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=96G -t 90 -J flybrain-checks -o logs/rewrite/checks-%j.out --wrap cd fly_brain && P=/home/s/st/stevejobs/flybrain/venv-cuda/bin/python && $P -m export.export_dashboard && $P export/pack_dashboard.py && $P -m pytest -q -rs tests && $P -m runs.bench_gpu --devices cuda --trials 1 128 1024 --graph --out ../logs/rewrite/bench_graph_engine.json
```

**36629** (bash)

```bash
srun -p ocf-hpc -w corruption -c 8 --mem=48G -t 30 bash -c /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_road_trace.json results/ride_3d.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride results/ride_road_trace.json results/ride_view.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_pilot_road_trace.json results/ride_pilot_3d.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride results/ride_pilot_road_trace.json results/ride_pilot_view.html
```

**36631** (flybrain-checks2)

```bash
sbatch --parsable -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=64G -t 40 -J flybrain-checks2 -o logs/rewrite/checks2-%j.out --wrap cd fly_brain && P=/home/s/st/stevejobs/flybrain/venv-cuda/bin/python && $P -m pytest -q -rs tests && $P -m export.export_dashboard && $P export/pack_dashboard.py
```

**36632** (bash)

```bash
srun -p ocf-hpc -w corruption -c 8 --mem=48G -t 40 bash -c /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_attempts results/relearn/attempts results/attempts_page 2>&1 | tail -1 && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_road_trace.json results/ride_3d.html 2>&1 | grep html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_pilot_road_trace.json results/ride_pilot_3d.html 2>&1 | grep html
```

**36635** (flydash3)

```bash
sbatch --parsable -p ocf-hpc -w corruption -c 8 --gres=gpu:1 --mem=64G -t 30 -J flydash3 -o logs/rewrite/dashboard3-%j.out --wrap cd fly_brain && P=/home/s/st/stevejobs/flybrain/venv-cuda/bin/python && $P -m export.export_dashboard && $P export/pack_dashboard.py
```

**36636** (bash)

```bash
srun -p ocf-hpc -w corruption -c 8 --mem=48G -t 30 bash -c /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_road_trace.json results/ride_3d.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride results/ride_road_trace.json results/ride_view.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_pilot_road_trace.json results/ride_pilot_3d.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride results/ride_pilot_road_trace.json results/ride_pilot_view.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride3d results/ride_oracle_trace.json results/ride_oracle_3d.html && /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m export.export_ride results/ride_oracle_trace.json results/ride_oracle_view.html
```

**37519** (bash)

```bash
srun -p ocf-hpc -w corruption -c 2 --mem=4G -t 5 bash -c which chromium google-chrome ffmpeg; chromium --version; nproc; ls /usr/lib/x86_64-linux-gnu/libEGL_nvidia* 2>/dev/null | head -2; nvidia-smi --query-gpu=name,utilization.gpu,memory.used --format=csv
```

**37520** (bash)

```bash
srun -p ocf-hpc -w corruption -c 2 -t 5 bash -c hostname; which chromium ffmpeg; cat /etc/os-release | head -3; curl -sS -m 10 -o /dev/null -w "gfonts %{http_code}\n" "https://fonts.googleapis.com/css2?family=Anton"; curl -sS -m 10 -o /dev/null -w "cdnjs %{http_code}\n" https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js; ldd /usr/lib/chromium/chromium 2>&1 | grep -i "not found"; fc-list | wc -l; fc-match sans; ls /usr/lib/x86_64-linux-gnu | wc -l
```

**37558** (tdfD-ls)

```bash
srun -p ocf-hpc -w corruption -c 1 --mem=1G -t 00:02:00 -J tdfD-ls bash -c ls -la --time-style=full-iso /tmp/ | grep -i "tdf\|det-\|w0" ; for d in /tmp/tdf-film-run-*; do echo "== $d"; find $d -maxdepth 3 | head -30; du -sh $d; done; pgrep -a -u $USER chromium | head
```

**37607** (shot.sh)

```bash
srun -p ocf-hpc -w corruption -c 8 -t 30 /home/s/st/stevejobs/tour-de-fly/scratch/sg/shot.sh /home/s/st/stevejobs/tour-de-fly/scratch/sg/out/lab1.png scratch/sg/lab.html?views=1540,0,3,1980,0,25,12;1930,40,10,1980,0,25,50;1975,0,2,1990,0,30,70;1980,70,20,1980,0,25,45;2040,-50,30,1980,0,20,50;1900,0,1.7,1980,0,25,60;1520,0.8,2.6,1470,0,0.6,15;1500,-7.3,1.15,1500,0,0.5,30;1497,-1,20,1490,0,0,20 --size 1600x900 --timeout 300 --root /home/s/st/stevejobs/tour-de-fly
```

**37608** (shot.sh)

```bash
srun -p ocf-hpc -w corruption -c 8 -t 30 /home/s/st/stevejobs/tour-de-fly/scratch/sg/shot.sh /home/s/st/stevejobs/tour-de-fly/scratch/sg/out/film1.png film.html?w=1600&h=900&sheet=114,117,128,130,96.5,98.5,99.3,101,102.5 --size 1600x900 --timeout 600
```

**37609** (shot.sh)

```bash
srun -p ocf-hpc -w corruption -c 8 -t 30 /home/s/st/stevejobs/tour-de-fly/scratch/sg/shot.sh /home/s/st/stevejobs/tour-de-fly/scratch/sg/out/lab_chk.png scratch/sg/lab.html?fin=checker&views=1520,0.8,2.6,1470,0,0.6,15;1500,-7.3,1.15,1500,0,0.5,30;1497,-1,20,1490,0,0,20;1440,0.5,1.6,1530,0,1,40 /home/s/st/stevejobs/tour-de-fly/scratch/sg/out/lab_line.png scratch/sg/lab.html?fin=line&views=1520,0.8,2.6,1470,0,0.6,15;1500,-7.3,1.15,1500,0,0.5,30;1497,-1,20,1490,0,0,20;1440,0.5,1.6,1530,0,1,40 --size 1600x900 --timeout 300 --root /home/s/st/stevejobs/tour-de-fly
```

**37710** (bash)

```bash
srun -p ocf-hpc -w corruption -c 2 -t 2 bash -c hostname; nproc; ~/flybrain/venv/bin/python -c "import numpy, scipy; print(numpy.__version__)"; ~/tour-de-fly/film/.venv-tts/bin/python -c "import piper; print(\"piper ok\")"; which ffmpeg; ffmpeg -version | head -1
```

**37853** (bash)

```bash
srun -p ocf-hpc -w corruption -c 8 --mem=24G -t 20 --quiet --chdir=/home/s/st/stevejobs/flybrain/.claude/worktrees/foresight-ai-science-rfp-b3f525/fly_brain bash -c /home/s/st/stevejobs/flybrain/venv/bin/python -m brain.variants r4 --seed 1 && /home/s/st/stevejobs/flybrain/venv/bin/python -m brain.variants r5 --seed 1
```

**37855** (bash)

```bash
srun -p ocf-hpc -w corruption -c 8 --mem=16G -t 30 --quiet --chdir=/home/s/st/stevejobs/flybrain/.claude/worktrees/foresight-ai-science-rfp-b3f525/fly_brain bash -c T=/tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-foresight-ai-science-rfp-b3f525/7da3d3dc-7a0e-4830-8813-3da350058c6f/scratchpad/b2; /home/s/st/stevejobs/flybrain/venv/bin/pip install -q --target $T brian2 2>&1 | tail -2; PYTHONPATH=$T /home/s/st/stevejobs/flybrain/venv/bin/python -m pytest tests/test_brian2.py -v -rs 2>&1 | tail -15
```

**37923** (bash)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 4 --mem=8G -t 5 --quiet bash -c cat /etc/os-release | head -1; uname -r; nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader; nvidia-smi | grep -i "driver version"; python3 -V; ../venv-cuda/bin/python -c "
import torch, sys; print(sys.version.split()[0], torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)
x=torch.randn(4000,4000,device=\"cuda\"); print(float((x@x).abs().mean()))"
```

**37924** (bash)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 4 --mem=8G -t 5 --quiet bash -c ls -la /usr/bin/python3.11 && /usr/bin/python3.11 -V && dpkg -l | grep -E "^ii +(python3\.11|libpython3\.11)" | awk "{print \$2, \$3}"; /usr/bin/python3.11 -c "
import sys; sys.path.insert(0, \"/home/s/st/stevejobs/flybrain/venv-cuda/lib/python3.11/site-packages\")
import torch, numpy, pandas; print(torch.__version__, numpy.__version__, pandas.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))
x=torch.randn(4000,4000,device=\"cuda\"); print(\"matmul ok\", float((x@x).abs().mean())>0)"
```

**37926** (env-check)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 8 --mem=16G -t 15 --quiet -J env-check env OMP_NUM_THREADS=8 ../venv-cuda/bin/python -m runs.ride --init-theta results/gate/v4.5_s201/init_hold.json --sigma-new 0.1 --sigma0 0.3 --sigma-lane-filter 1.0 --sigma-min 0.03 --sigma-pedal 0 --center-batch --zbar results/gate/v4.5_s201/zbar_mu.npy --readout lane --lane hs --lane-filter results/gate/v4.5_s201/probe.json --tau-lane-ms 300 --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 --riders 48 --seconds 15 --generations 1 --seed 201 --out /home/s/st/stevejobs/.cache/flybrain-smoke/gate_v4.5_s201_gen0.json
```

**37933** (bash)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 2 --mem=4G -t 4 --quiet bash -c echo CVD=$CUDA_VISIBLE_DEVICES; ls -la /dev/nvidia* 2>&1 | head -12; echo; lsmod | grep -i nvidia; echo; cat /proc/driver/nvidia/version 2>&1 | head -2; ls /dev/nvidia-caps 2>&1 | head -3; ../venv-cuda/bin/python -c "
import torch, ctypes
print(torch.__version__, torch.version.cuda)
try:
    torch.cuda.init(); print(\"init ok\", torch.cuda.device_count())
except Exception as e: print(\"init error:\", repr(e)[:300])
lib = ctypes.CDLL(\"libcuda.so.1\"); print(\"cuInit ->\", lib.cuInit(0))
" 2>&1 | grep -v Warning; ls -la /usr/bin/nvidia-modprobe 2>&1; dmesg 2>/dev/null | grep -i -E "nvidia|uvm" | tail -5
```

**37934** (bash)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 2 --mem=4G -t 4 --quiet bash -c echo CVD=$CUDA_VISIBLE_DEVICES; ls -la /dev/nvidia* 2>&1 | head -12; echo; lsmod | grep -i nvidia; echo; cat /proc/driver/nvidia/version 2>&1 | head -2; ../venv-cuda/bin/python -c "
import torch, ctypes
print(torch.__version__, torch.version.cuda)
try:
    torch.cuda.init(); print(\"init ok\", torch.cuda.device_count())
except Exception as e: print(\"init error:\", repr(e)[:300])
lib = ctypes.CDLL(\"libcuda.so.1\"); print(\"cuInit ->\", lib.cuInit(0))
" 2>&1 | grep -v Warning; ls -la /usr/bin/nvidia-modprobe 2>&1
```

**37935** (bash)

```bash
srun -p ocf-hpc -w corruption --gres=gpu:1 -c 2 --mem=4G -t 4 --quiet bash -c /sbin/modinfo nvidia-uvm 2>&1 | head -3; /sbin/modinfo nvidia-current-uvm 2>&1 | head -3; find /lib/modules/$(uname -r) -name "*uvm*" 2>/dev/null | head; echo "--- nvidia-modprobe -u -c=0"; /usr/bin/nvidia-modprobe -u -c=0; echo "rc=$?"; ls -la /dev/nvidia-uvm* 2>&1; lsmod | grep uvm; ../venv-cuda/bin/python -c "
import torch
print(torch.cuda.is_available(), torch.cuda.device_count())
x=torch.randn(4000,4000,device=\"cuda\"); print(\"matmul ok\", float((x@x).abs().mean())>0, torch.cuda.get_device_name(0))" 2>&1 | grep -v "Warning\|return torch" | tail -4
```

**37944** (r4-stability)

```bash
sbatch --parsable --gres=none -p ocf-hpc -w corruption -c 16 --mem=24G --time=04:00:00 -J r4-stability -o logs/r4-stability-%j.out --wrap set -e; cd fly_brain; export OMP_NUM_THREADS=16; mkdir -p $HOME/.cache/flybrain-smoke; for S in 1.0 1.2 1.3 1.4; do echo "== $(date +%T) R4 closed-loop stability, scale $S"; ../venv-cuda/bin/python -m runs.ride --replay results/ride_slow_mu.json --tau-lane-ms 300 --lane-filter results/rungs/r4_s1_w1.5_cpu/v4.5_s201/probe.json --brain results/variants/r4_s1.npz --w-syn-scale $S --readout lane --lane hs --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --riders 16 --seconds 20 --seed 7 --trace $HOME/.cache/flybrain-smoke/r4_w${S}_trace.json 2>&1 | grep -E "^replay|population|Error"; done; echo "== done $(date)"
```

**38024** (bash)

```bash
srun -p ocf-hpc --gres=gpu:1 -c 1 --time=3 bash -c 
echo "== modules"; grep -i nvidia /proc/modules
echo "== dev"; ls -l /dev/nvidia* 2>&1
echo "== driver"; cat /proc/driver/nvidia/version 2>&1 | head -3
echo "== uvm ko"; find /lib/modules/$(uname -r) -iname "*uvm*" 2>/dev/null
echo "== modprobe cfg"; ls -l /etc/modprobe.d/ 2>&1; grep -rih nvidia /etc/modprobe.d/ /lib/modprobe.d/ /usr/lib/modprobe.d/ 2>/dev/null | head -20
echo "== modprobe -c"; /sbin/modprobe -c 2>/dev/null | grep -i nvidia | head -20
echo "== helper"; ls -l $(command -v nvidia-modprobe) 2>&1
echo "== alternatives"; ls -l /etc/alternatives/ 2>/dev/null | grep -i nvidia | head
echo "== try"; nvidia-modprobe -u -c=0; echo rc=$?
ls -l /dev/nvidia-uvm* 2>&1
```

**38025** (bash)

```bash
srun -p ocf-hpc --gres=gpu:1 -n 1 -c 1 --time=2 bash -c 
echo "== /etc/modprobe.d/nvidia.conf"; cat /etc/modprobe.d/nvidia.conf
echo "== /etc/nvidia/nvidia-modprobe.conf"; cat /etc/nvidia/nvidia-modprobe.conf 2>&1
echo "== nvidia-load"; cat /etc/nvidia/nvidia-load.conf 2>&1; ls /etc/modules-load.d/ 2>&1; cat /etc/modules-load.d/*nvidia* 2>&1
echo "== direct"; /sbin/modprobe -n -v nvidia-uvm 2>&1; /sbin/modprobe -n -v nvidia-current-uvm 2>&1
echo "== id"; id; sudo -n true 2>&1 | head -1
echo "== uptime"; uptime
```

**38026** (bash)

```bash
srun -p ocf-hpc --gres=none -c 16 --mem=24G --time=12 bash -c 
set -e; cd fly_brain; export OMP_NUM_THREADS=16
lscpu | grep -E 'Model name|^CPU\(s\)|NUMA node\(s\)|Thread'; gcc --version | head -1
gcc -O3 -march=native -fopenmp -ffp-contract=off -fPIC -shared -o /tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-project-pending-items-5ff0c7/069ec666-7600-4925-b3b9-cd4883e88da9/scratchpad/kern/lif_dense.so /tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-project-pending-items-5ff0c7/069ec666-7600-4925-b3b9-cd4883e88da9/scratchpad/kern/lif_dense.c
PYTHONPATH=. ../venv/bin/python /tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-project-pending-items-5ff0c7/069ec666-7600-4925-b3b9-cd4883e88da9/scratchpad/kern/bench_cpu.py /tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-project-pending-items-5ff0c7/069ec666-7600-4925-b3b9-cd4883e88da9/scratchpad/kern/lif_dense.so 48 60
```

**38027** (bash)

```bash
srun -p ocf-hpc --gres=none -c 16 --mem=24G --time=12 bash -c 
set -e; cd fly_brain; export OMP_NUM_THREADS=16
gcc -O3 -march=native -fopenmp -ffp-contract=off -fPIC -shared -o /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/notes/kern/lif_dense.so /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/notes/kern/lif_dense.c
PYTHONPATH=. ../venv/bin/python /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/notes/kern/bench_cpu.py /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/notes/kern/lif_dense.so 48 60
```

**38028** (bash)

```bash
srun -p ocf-hpc --gres=none -c 16 --mem=24G --time=12 bash -c 
set -e; cd fly_brain; export OMP_NUM_THREADS=16
for cfg in '300 20' '600 30' '1000 40'; do PYTHONPATH=. ../venv/bin/python /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/notes/kern/bench2.py /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/notes/kern/lif_dense.so 48 $cfg; done
```

**38029** (bash)

```bash
srun -p ocf-hpc --gres=none -c 16 --mem=32G --time=12 bash -c 
set -e; cd /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/fly_brain; export OMP_NUM_THREADS=16
for cfg in '300 20' '450 25' '500 25'; do PYTHONPATH=. ~/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/notes/kern/bench3.py $cfg /home/s/st/stevejobs/flybrain/fly_brain/results/brain.npz 2>&1 | tail -4; done; ls ~/.cache/fly_brain/
```

**38030** (bash)

```bash
srun -p ocf-hpc --gres=none -c 16 --mem=32G --time=12 bash -c 
set -e; cd /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/fly_brain; export OMP_NUM_THREADS=16
for cfg in '300 20' '450 25' '500 25'; do PYTHONPATH=. ~/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/notes/kern/bench3.py $cfg /home/s/st/stevejobs/flybrain/fly_brain/brain.npz 2>&1 | tail -4; done; ls ~/.cache/fly_brain/
```

**38077** (replay-r0-top8)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-top8 -o logs/replay-r0-top8-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --readout topk --screen results/rungs/screens/r0.parquet --k 8 --center-all --center-batch --lane hs --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/top8_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/top8_mu_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused.json
```

**38081** (replay-r0-bypass)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-bypass -o logs/replay-r0-bypass-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --readout bypass --center-all --center-batch --lane hs --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/bypass_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/bypass_mu_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused.json
```

**38082** (replay-r0-handsoff-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -d afterany:38081 -J replay-r0-handsoff-noroad -o logs/replay-r0-handsoff-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --readout topk --screen results/rungs/screens/r0.parquet --k 8 --center-all --center-batch --lane hs --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --offroad 0 --replay /home/s/st/stevejobs/.cache/sb-replay/handsoff.json --trace /home/s/st/stevejobs/.cache/sb-replay/handsoff_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused.json
```

**38083** (replay-r0-top8-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -d afterany:38082 -J replay-r0-top8-noroad -o logs/replay-r0-top8-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --readout topk --screen results/rungs/screens/r0.parquet --k 8 --center-all --center-batch --lane hs --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --offroad 0 --replay /home/s/st/stevejobs/.cache/sb-replay/top8_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/top8_mu_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused.json
```

**38084** (replay-r0-handsoff-road)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -d afterany:38083 -J replay-r0-handsoff-road -o logs/replay-r0-handsoff-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --readout topk --screen results/rungs/screens/r0.parquet --k 8 --center-all --center-batch --lane hs --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --offroad 3.5 --replay /home/s/st/stevejobs/.cache/sb-replay/handsoff.json --trace /home/s/st/stevejobs/.cache/sb-replay/handsoff_road_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused.json
```

**38087** (python)

```bash
srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-project-pending-items-5ff0c7/069ec666-7600-4925-b3b9-cd4883e88da9/scratchpad/r1_flips.py /tmp/claude-93015/-home-s-st-stevejobs-flybrain--claude-worktrees-project-pending-items-5ff0c7/069ec666-7600-4925-b3b9-cd4883e88da9/scratchpad/r1_flips.json
```

**38088** (python)

```bash
srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/.cache/sb-replay/r1_flips.py /home/s/st/stevejobs/.cache/sb-replay/r1_flips.json
```

**38089** (python)

```bash
srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/.cache/sb-replay/r1_flips.py /home/s/st/stevejobs/.cache/sb-replay/r1_flips.json
```

**38090** (python)

```bash
srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/.cache/sb-replay/r1_flips.py /home/s/st/stevejobs/.cache/sb-replay/r1_flips.json
```

**38091** (python)

```bash
srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/.cache/sb-replay/r1_flips.py /home/s/st/stevejobs/.cache/sb-replay/r1_flips.json
```

**38092** (replay-r1_s201-road)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r1_s201-road -o logs/replay-r1_s201-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --brain results/variants/r1_s1.npz --readout lane --lane hs --lane-filter results/rungs/r1_s1_cpu/v4.5_s201/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r1_s201_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r1_s201_mu_road_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r1_s201_road.json
```

**38093** (replay-r0_s201-road)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r0_s201-road -o logs/replay-r0_s201-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride  --readout lane --lane hs --lane-filter results/gate/v4.5_s201/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r0_s201_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r0_s201_mu_road_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r0_s201_road.json
```

**38094** (replay-r3_s201-road)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r3_s201-road -o logs/replay-r3_s201-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --brain results/variants/r3_s1.npz --readout lane --lane hs --lane-filter results/rungs/r3_s1_cpu/v4.5_s201/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r3_s201_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r3_s201_mu_road_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r3_s201_road.json
```

**38095** (replay-r0_s202-road)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r0_s202-road -o logs/replay-r0_s202-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride  --readout lane --lane hs --lane-filter results/gate/v4.5_s202/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r0_s202_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r0_s202_mu_road_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r0_s202_road.json
```

**38096** (replay-r3_s202-road)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r3_s202-road -o logs/replay-r3_s202-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --brain results/variants/r3_s1.npz --readout lane --lane hs --lane-filter results/rungs/r3_s1_cpu/v4.5_s202/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r3_s202_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r3_s202_mu_road_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r3_s202_road.json
```

**38097** (replay-r1_s201-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r1_s201-noroad -o logs/replay-r1_s201-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --brain results/variants/r1_s1.npz --readout lane --lane hs --lane-filter results/rungs/r1_s1_cpu/v4.5_s201/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 0 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r1_s201_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r1_s201_mu_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r1_s201_noroad.json
```

**38098** (replay-r0_s201-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r0_s201-noroad -o logs/replay-r0_s201-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride  --readout lane --lane hs --lane-filter results/gate/v4.5_s201/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 0 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r0_s201_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r0_s201_mu_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r0_s201_noroad.json
```

**38099** (replay-r3_s201-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r3_s201-noroad -o logs/replay-r3_s201-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --brain results/variants/r3_s1.npz --readout lane --lane hs --lane-filter results/rungs/r3_s1_cpu/v4.5_s201/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 0 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r3_s201_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r3_s201_mu_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r3_s201_noroad.json
```

**38100** (replay-r0_s202-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r0_s202-noroad -o logs/replay-r0_s202-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride  --readout lane --lane hs --lane-filter results/gate/v4.5_s202/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 0 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r0_s202_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r0_s202_mu_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r0_s202_noroad.json
```

**38101** (replay-r3_s202-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r3_s202-noroad -o logs/replay-r3_s202-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --brain results/variants/r3_s1.npz --readout lane --lane hs --lane-filter results/rungs/r3_s1_cpu/v4.5_s202/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 0 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r3_s202_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r3_s202_mu_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r3_s202_noroad.json
```

**38102** (python)

```bash
srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/tools/r1_flips.py results/variants/r1_s1.npz results/rungs/r1_s1_cpu/sign_flips.json
```

**38104** (replay-r0-top32-road)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-top32-road -o logs/replay-r0-top32-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --readout topk --screen results/rungs/screens/r0.parquet --k 32 --center-all --center-batch --lane hs --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --offroad 3.5 --replay /home/s/st/stevejobs/.cache/sb-replay/top32_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/top32_mu_road_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_top32_road.json
```

**38105** (replay-r0-top32-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-top32-noroad -o logs/replay-r0-top32-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --readout topk --screen results/rungs/screens/r0.parquet --k 32 --center-all --center-batch --lane hs --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --offroad 0 --replay /home/s/st/stevejobs/.cache/sb-replay/top32_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/top32_mu_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_top32_noroad.json
```

**38109** (python)

```bash
srun -p ocf-hpc -w corruption --gres=none --mem=12G --time=00:15:00 -c 2 --export=ALL /home/s/st/stevejobs/flybrain/venv-cuda/bin/python /home/s/st/stevejobs/flybrain/.claude/worktrees/project-pending-items-5ff0c7/tools/r1_flips.py results/variants/r1_s2.npz results/rungs/r1_s2_cpu/sign_flips.json
```

**38111** (replay-r0-rand8-road)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-rand8-road -o logs/replay-r0-rand8-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --readout randk --screen results/rungs/screens/r0.parquet --k 8 --readout-seed 0 --center-all --center-batch --lane hs --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --offroad 3.5 --replay /home/s/st/stevejobs/.cache/sb-replay/rand8_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/rand8_mu_road_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_rand8_road.json
```

**38112** (replay-r0-rand8-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:00:00 -c 16 -J replay-r0-rand8-noroad -o logs/replay-r0-rand8-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --readout randk --screen results/rungs/screens/r0.parquet --k 8 --readout-seed 0 --center-all --center-batch --lane hs --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --offroad 0 --replay /home/s/st/stevejobs/.cache/sb-replay/rand8_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/rand8_mu_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_rand8_noroad.json
```

**38118** (replay-r2_s201-road)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 --dependency=afterany:38107 -J replay-r2_s201-road -o logs/replay-r2_s201-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --brain results/variants/r2_s1.npz --readout lane --lane hs --lane-filter results/rungs/r2_s1_cpu/v4.5_s201/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r2_s201_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r2_s201_mu_road_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r2_s201_road.json
```

**38119** (replay-r2_s201-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 --dependency=afterany:38107 -J replay-r2_s201-noroad -o logs/replay-r2_s201-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --brain results/variants/r2_s1.npz --readout lane --lane hs --lane-filter results/rungs/r2_s1_cpu/v4.5_s201/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 0 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r2_s201_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r2_s201_mu_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r2_s201_noroad.json
```

**38120** (replay-r1d2_s201-road)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r1d2_s201-road -o logs/replay-r1d2_s201-road-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --brain results/variants/r1_s2.npz --readout lane --lane hs --lane-filter results/rungs/r1_s2_cpu/v4.5_s201/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 3.5 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r1d2_s201_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r1d2_s201_mu_road_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r1d2_s201_road.json
```

**38121** (replay-r1d2_s201-noroad)

```bash
sbatch --parsable -p ocf-hpc -w corruption --gres=none --mem=16G --time=01:30:00 -c 16 -J replay-r1d2_s201-noroad -o logs/replay-r1d2_s201-noroad-%j.out --wrap set -e; export OMP_NUM_THREADS=16; cd /home/s/st/stevejobs/flybrain/fly_brain; /home/s/st/stevejobs/flybrain/venv-cuda/bin/python -m runs.ride --brain results/variants/r1_s2.npz --readout lane --lane hs --lane-filter results/rungs/r1_s2_cpu/v4.5_s201/probe.json --tau-lane-ms 300 --center-batch --gains hs_heading=150,hs_lane=50 --v0 4.5 --gust 5 --offroad 0 --lane-penalty 0.02 --riders 48 --seconds 15 --seed 201 --replay /home/s/st/stevejobs/.cache/sb-replay/r1d2_s201_mu.json --trace /home/s/st/stevejobs/.cache/sb-replay/r1d2_s201_mu_noroad_trace.json --out /home/s/st/stevejobs/.cache/sb-replay/unused_r1d2_s201_noroad.json
```
