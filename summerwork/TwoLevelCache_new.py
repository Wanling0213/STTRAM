import initial 
import os
run_times=1
traces=initial.get_tracepath("trace_")

for trace in traces:
    print(trace)
    out_tracename=os.path.join("result",trace.split("\\")[1])
    print("trace file %s " %trace)
    print("trace file %s " %trace,file=open( out_tracename , 'w'))
    L1,L2=initial.read_ini("init.json")
    cmd_list=initial.read_trace(trace)
    print("{",end='',file=open( 'output/'+trace.split("\\")[1] , 'w'))
    initial.simulator(L1,L2,cmd_list,run_times,out_tracename)
    print("}",file=open( 'output/'+trace.split("\\")[1] , 'a+'))