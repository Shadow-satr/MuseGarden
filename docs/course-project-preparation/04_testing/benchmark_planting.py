import sys,time,statistics,platform,json,datetime
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from application.garden_planting import plan_planting
N=10000
for _ in range(100):plan_planting((22,18),[],prefer_large=True)
t=[]
for _ in range(10):
 start=time.perf_counter()
 for j in range(N):plan_planting((22,18),[],prefer_large=True)
 t.append((time.perf_counter()-start)*1000)
print(json.dumps({'date_local':datetime.datetime.now().astimezone().isoformat(),'python':sys.version,'platform':platform.platform(),'method':'10 batches of 10000 plan_planting calls, empty existing list, prefer_large=True, same legal position; no I/O','batch_ms':t,'mean_us_per_call':statistics.mean(t)*1000/N,'max_batch_us_per_call':sorted(t)[-1]*1000/N,'note':'microbenchmark only; not generation latency or concurrent system performance'},ensure_ascii=False,indent=2))
