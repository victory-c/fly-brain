# Jobs

Every Slurm job run from this repo on the OCF cluster (node `corruption`), newest last. Generated
by `python3 tools/jobs_ledger.py` from `sacct`; do not edit by hand, add context to `NOTES` there.
Commands run from the job's working directory (`.` = repo root, `fly_brain/` for most `srun` jobs).

| Job | Started | State | Time | Resources | What | Command | Logs / outputs |
|---|---|---|---|---|---|---|---|
| 38024 | 2026-11-05 17:16 | FAILED | 00:00:01 | 2 cpu, 2000M, 1 gpu |  | `srun -p ocf-hpc --gres=gpu:1 -c 1 --time=3 bash -c  ⏎ echo "== modules"; grep -i nvidia /proc/modules ⏎ echo "== dev"; ls -l /dev/nvidia* 2>&1 ⏎ echo "== driver"; cat /proc/driver/nvidia/version 2>&1 ¦ head -3 ⏎ echo ...` |  |
| 38025 | 2026-11-05 17:16 | COMPLETED | 00:00:00 | 2 cpu, 2000M, 1 gpu |  | `srun -p ocf-hpc --gres=gpu:1 -n 1 -c 1 --time=2 bash -c  ⏎ echo "== /etc/modprobe.d/nvidia.conf"; cat /etc/modprobe.d/nvidia.conf ⏎ echo "== /etc/nvidia/nvidia-modprobe.conf"; cat /etc/nvidia/nvidia-modprobe.conf 2>&1...` |  |

## Full command lines

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
