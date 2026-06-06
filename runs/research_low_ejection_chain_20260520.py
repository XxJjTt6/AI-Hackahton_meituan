#!/usr/bin/env python3
import importlib.util, pathlib, itertools, argparse, heapq, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('solver_mod',ROOT/'solver.py')
s=importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

def parse(text):
    lines=text.strip().splitlines(); off=1 if lines and lines[0].startswith('task') else 0
    C=[]; B=set()
    for idx,line in enumerate(lines[off:]):
        p=line.strip().split('\t')
        if len(p)<4: continue
        tk,cid,cost,prob=p[:4]; tasks=tuple(x.strip() for x in tk.split(',') if x.strip())
        try: cost=float(cost); prob=float(prob)
        except: continue
        C.append((tk,tasks,cid,cost,prob,idx)); B.update(tasks)
    return C,B

def rows_cost(sel):
    return sum(s._group_expected_cost(rows,len(rows[0][1])) for rows in sel.values() if rows)

def canonical(sel):
    return tuple(sorted((t,tuple(sorted(r[2] for r in rows))) for t,rows in sel.items()))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('--seconds',type=float,default=20); ap.add_argument('--beam',type=int,default=2000)
    args=ap.parse_args(); deadline=time.monotonic()+args.seconds
    text=open(args.input).read(); C,B=parse(text); row={(r[0],r[2]):r for r in C}
    base=s.solve(text); sel=s._result_to_selected(base,row); basecost=s._solution_expected_cost(base,C,B)
    print('base',basecost,'groups',len(sel),'sig',hash(canonical(sel)))
    tasks=sorted(sel)
    couriers=sorted({r[2] for rows in sel.values() for r in rows})
    # Candidate moves: move one courier from src to dst, allowing src to pull one courier from another task recursively.
    # State is assignment tuple; expand by one courier transfer if both affected task costs decrease chain-wise enough.
    start=canonical(sel); best_cost=basecost; best_state=start
    pq=[(basecost,0,start)]; seen={start:basecost}; iters=0
    def state_to_sel(state):
        return {t:[row[(t,c)] for c in cs if (t,c) in row] for t,cs in state}
    while pq and time.monotonic()<deadline:
        cost,depth,state=heapq.heappop(pq); iters+=1
        if cost>seen.get(state,1e99)+1e-9: continue
        cur=state_to_sel(state)
        if cost<best_cost-1e-9:
            best_cost=cost; best_state=state; print('IMPROVE',best_cost,best_cost-basecost,'depth',depth,'iters',iters,flush=True)
        if depth>=4: continue
        used={c for _,cs in state for c in cs}
        # Try replacing one courier in a high-cost task with a courier from a low-cost task, then leave donor with remaining >=1.
        task_cost=sorted(((s._group_expected_cost(cur[t],len(cur[t][0][1])),t) for t in tasks), reverse=True)
        high=[t for _,t in task_cost[:10]]; donors=[t for _,t in task_cost[-18:]]
        state_map={t:tuple(cs) for t,cs in state}
        for dst in high:
            dst_rows=cur[dst]; old_dst=s._group_expected_cost(dst_rows,len(dst_rows[0][1]))
            for src in donors:
                if src==dst or len(cur[src])<=1: continue
                old_src=s._group_expected_cost(cur[src],len(cur[src][0][1]))
                for moved in state_map[src]:
                    add=row.get((dst,moved))
                    if not add: continue
                    for drop in state_map[dst]:
                        if drop==moved: continue
                        new_dst=[row[(dst,c)] for c in state_map[dst] if c!=drop]+[add]
                        new_src=[row[(src,c)] for c in state_map[src] if c!=moved]
                        if not new_src: continue
                        delta=s._group_expected_cost(new_dst,len(new_dst[0][1]))+s._group_expected_cost(new_src,len(new_src[0][1]))-old_dst-old_src
                        if delta>=2.5: continue
                        ns=[]
                        for t,cs in state:
                            if t==dst: ns.append((t,tuple(sorted([c for c in cs if c!=drop]+[moved]))))
                            elif t==src: ns.append((t,tuple(sorted(c for c in cs if c!=moved))))
                            else: ns.append((t,cs))
                        ns=tuple(sorted(ns))
                        nc=cost+delta
                        if nc<seen.get(ns,1e99)-1e-9:
                            seen[ns]=nc; heapq.heappush(pq,(nc,depth+1,ns))
        if len(pq)>args.beam:
            pq=heapq.nsmallest(args.beam,pq); heapq.heapify(pq)
    print('done best',best_cost,best_cost-basecost,'iters',iters,'seen',len(seen))
    if best_state!=start:
        for t,cs in best_state[:10]: print(t,list(cs))
if __name__=='__main__': main()
