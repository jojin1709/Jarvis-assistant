from __future__ import annotations

import subprocess


def gpu_metrics() -> dict:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.total,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
        if result.returncode != 0:
            return {"available": False, "gpus": [], "error": result.stderr.strip()}
        gpus = []
        for line in result.stdout.splitlines():
            name, util, total, used = [part.strip() for part in line.split(",")]
            gpus.append({"name": name, "utilizationPercent": float(util), "memoryTotalMb": float(total), "memoryUsedMb": float(used)})
        return {"available": bool(gpus), "gpus": gpus}
    except Exception as error:
        return {"available": False, "gpus": [], "error": str(error)}
