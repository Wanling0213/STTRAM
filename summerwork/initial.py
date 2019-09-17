import os
import json
import cache_stru as struct
import cache_func as func
import sys
import time
from collections import OrderedDict

def get_tracepath(fpath):
    """ read_tracepath func 讀進trace檔\n 
        return files tracey資料夾底下的檔案
    """
    path=os.path.join(os.getcwd() ,fpath)
    files=list()
    for f in os.listdir(path):
        if(f[0] == '.'):#排除隱藏資料夾
            pass  
        else:
            files.append(os.path.join(fpath,f))
    return files
def hex2bin(hex_str,totalBits=0):
    """ hex2bin func 16進位轉2進位\n
        param totalBits 最後回傳的數字長度\n
        return binary data
    """
    return bin(int(hex_str,16))[2:].zfill(totalBits)
# def dec2bin(dec_str,totalBits=0):
#     return bin(int(dec_str).zfill(totalBits)
def read_trace(filename,addrBits=32):
    """ read_trace func 讀進trace並處理\n
        param totalBits 最後回傳的數字長度\n
        return cmd_list    
    """
    with open(filename) as f:
        cmd_list = f.readlines()
        cmd_list = [x.split() for x in cmd_list] 
    bin_cmd_list=list() # convert hex to binary
    for cmd in cmd_list:
        if(cmd[0]in['WRITE','W','Write','w','write','READ','R','Read','r','read']):
            #write todo 
            addr=cmd[1]
            bin_addr=hex2bin(addr[2:],addrBits)
            #bin_addr=dec2bin(addr[2:],addrBits)
            data= ''.join(cmd[2:])
            bin_data=hex2bin(data,512)
            #bin_data=data
            bin_cmd=list()
            bin_cmd.append(cmd[0])
            bin_cmd.append(bin_addr)
            bin_cmd.append(bin_data)
            bin_cmd_list.append(bin_cmd)
    return bin_cmd_list 
def read_ini(filename):
    """ read_ini func 讀進trace並處理\n
        return obj
    """
    with open(filename,'r')as inifile:
        data=inifile.read()
    obj=json.loads(data, object_pairs_hook=OrderedDict)
    L1=obj["TWOLEVEL"]["L1"]
    L2=obj["TWOLEVEL"]["L2"]
    L1Setting=get_setting(L1)
    L2Setting=get_setting(L2)
    return L1Setting,L2Setting
def get_setting(obj):
    tmp=list()
    for key,value in obj.items():
        tmp.append(value)
    return tmp
def transSize(s_cachesize):
    if "MB" in s_cachesize :
        i_cachesize = int(s_cachesize[:-2])*1024*1024
    elif "KB" in s_cachesize :
        i_cachesize= int(s_cachesize[:-2])*1024 
    else:
        i_cachesize=int(s_cachesize[:-1])
    return i_cachesize
def get_cache_info(setting):
    cachesize=transSize(setting[0])
    way=setting[1]
    blocksize=transSize(setting[2])
    replacement=setting[3]
    method=setting[4]
    addrbits=setting[5]
    read_lat=setting[6]
    write_STnHT_lat=setting[7]
    write_TT_lat=setting[8]
    read_energy=setting[9]
    write_ST_energy=setting[10]
    write_TT_energy=setting[11]
    return cachesize,way,blocksize,replacement,method,addrbits,read_lat,write_STnHT_lat,write_TT_lat,read_energy,write_ST_energy,write_TT_energy
def simulator(L1Settings,L2Settings,cmdlist,run_times,tracename,Mode="TWOLEVL"):
    for L1Setting in L1Settings:
        for L2Setting in L2Settings:
            sim_cache(L1Setting,L2Setting,cmdlist,run_times,tracename)
def sim_cache(L1Setting,L2Setting,cmdlist,run_times,tracename):
    L1cachesize,L1way,L1blocksize,L1replacement,L1method,addrbits,L1_r_lat,L1_w_STnHT_lat,L1_w_TT_lat,L1_r_energy,L1_w_ST_energy,L1_w_HT_energy=get_cache_info(L1Setting)
    L2cachesize,L2way,L2blocksize,L2replacement,L2method,addrbits,L2_r_lat,L2_w_STnHT_lat,L2_w_TT_lat,L2_r_energy,L2_w_ST_energy,L2_w_HT_energy=get_cache_info(L2Setting)
    L1Cache=struct.Cache(addrbits,L1cachesize,L1blocksize,L1way)
    L2Cache=struct.Cache(addrbits,L2cachesize,L2blocksize,L2way) 
    main_memory=list()    
    flag=0
    #cnt_cmdlist=len(cmdlist)
    while(run_times>0):
        print(run_times,L2method)
        start=time.time()
        for cmd in cmdlist:
            # percent=idx/cnt_cmdlist
            # sys.stdout.write("\r{0}{1}".format("|"*times , '%.2f%%' % (percent * 100)))
            # sys.stdout.flush()
            addr,data=cmd[1:]
            L1_line_hit_idx=func.get_line_hit_idx(L1Cache,addr)
            if(L1_line_hit_idx!=None):#L1 cache hit
                if cmd[0]in ['WRITE','W','Write','w','write']: #write to L1 cache
                    L1Cache.write_hit_cnt+=1
                    func.write(L1Cache,L1_line_hit_idx,addr,data,L1method)
                elif cmd[0] in ['READ','R','Read','r','read']: #read from L1 cache
                    L1Cache.read_hit_cnt+=1
                    func.read(L1Cache,L1_line_hit_idx,addr,data,L1method)
            else:#L1 cache miss 
                L2_line_hit_idx=func.get_line_hit_idx(L2Cache,addr)
                if(L2_line_hit_idx!=None):#L2 cache hit
                    if cmd[0]in ['WRITE','W','Write','w','write']: 
                        L1Cache.write_miss_cnt+=1
                        L2Cache.write_hit_cnt+=1
                        #print("1 %d" %len(data))
                        func.write(L2Cache,L2_line_hit_idx,addr,data,L2method) #update L2 cache
                        if(func.isFull(L1Cache,addr)):
                            ###do L1 eviction start 
                            L1_evicted_line,L1_evicted_line_addr=func.evict(L1Cache,addr)#被evict掉的cacheline資訊&address,update to L2 cache 
                            if L1_evicted_line.dirty==True:#data need to be updated from L1 to L2
                                if(func.isFull(L2Cache,L1_evicted_line_addr)):#如果L2是滿的做 L2 evict
                                    ###do L2 eviction start
                                    L2_evicted_line,L2_evicted_line_addr=func.evict(L2Cache,L1_evicted_line_addr)
                            
                                    #check back invalidation-> 找找看有沒有存在L1 cache
                                    exist_line=func.checkBackInvalid(L1Cache,L2_evicted_line_addr)
                                    if exist_line!=None:#被L2evict掉的cacheline存在L1裡(且L1cacheline的dirty=True)
                                        ###寫回memory L1 cache的data
                                        main_memory.append(exist_line)
                                        L1Cache.write_main_memory_cnt+=1
                                    elif(exist_line==None and L2_evicted_line.dirty==True):#被L2evict掉的cacheline不存在L1裡(且L2cacheline的dirty=True)
                                        ###寫回memory L2 cache的data
                                        if L2method=="TSTM":
                                            decode_data=func.TSTMdecode(L2_evicted_line.data)
                                            L2_evicted_line.data=decode_data
                                        main_memory.append(L2_evicted_line)
                                        L2Cache.write_main_memory_cnt+=1
                                    else:
                                        # 直接evict
                                        pass
                                    ###do L2 eviction end
                                func.write(L2Cache,None,L1_evicted_line_addr,L1_evicted_line.data,L2method)#被L1 evict 的cacheline update to L2
                                #print("2 %d" %len(L1_evicted_line.data))
                            else:#不管他->直接丟掉
                                pass    
                            ###do L1 eviction end               
                        func.write(L1Cache,L1_line_hit_idx,addr,data,L1method)  #place in L1 cache             
                    elif cmd[0] in ['READ','R','Read','r','read']: # L2 cache read hit
                        L1Cache.read_miss_cnt+=1
                        L2Cache.read_hit_cnt+=1
                        line_hit,addr=func.read(L2Cache,L2_line_hit_idx,addr,data,L2method) #read from L2 cache 
                        if L2method=="TSTM":
                            decode_data=func.TSTMdecode(line_hit.data)#從L2讀出來的data要做decode
                            line_hit.data=decode_data
                        if(func.isFull(L1Cache,addr)): #check if L1 cache is full    
                            ###do L1 eviction start 
                            L1_evicted_line,L1_evicted_line_addr=func.evict(L1Cache,addr)#被evict掉的cacheline資訊&address,update to L2 cache  
                            if L1_evicted_line.dirty==True:#data need to be updated from L1 to L2
                                if(func.isFull(L2Cache,L1_evicted_line_addr)):#如果L2是滿的做 L2 evict
                                    ###do L2 eviction start
                                    L2_evicted_line,L2_evicted_line_addr=func.evict(L2Cache,L1_evicted_line_addr)
                                    
                                    #check back invalidation-> 找找看有沒有存在L1 cache
                                    exist_line=func.checkBackInvalid(L1Cache,L2_evicted_line_addr)
                                    if exist_line!=None:#被L2evict掉的cacheline存在L1裡(且L1cacheline的dirty=True)
                                        ###寫回memory L1 cache的data
                                        main_memory.append(exist_line)
                                        L1Cache.write_main_memory_cnt+=1
                                    elif(exist_line==None and L2_evicted_line.dirty==True):#被L2evict掉的cacheline不存在L1裡(且L2cacheline的dirty=True)
                                        ###寫回memory L2 cache的data
                                        if L2method=="TSTM":
                                            decode_data=func.TSTMdecode(L2_evicted_line.data)
                                            L2_evicted_line.data=decode_data
                                        main_memory.append(L2_evicted_line)
                                        L2Cache.write_main_memory_cnt+=1
                                    else:
                                        # 直接evict
                                        pass
                                    ###do L2 eviction end
                                #print("3 %d" %len(L1_evicted_line.data))
                                func.write(L2Cache,None,L1_evicted_line_addr,L1_evicted_line.data,L2method)#update to L2
                            else:#不管他->直接丟掉
                                pass    
                            ###do L1 eviction end     
                        func.write(L1Cache,L1_line_hit_idx,addr,line_hit.data,L1method)#place in L1 
                else:#both L1 and L2 cache miss
                    if cmd[0]in ['WRITE','W','Write','w','write']: 
                        L1Cache.write_miss_cnt+=1
                        L2Cache.write_miss_cnt+=1
                        # tt.write("L1 and L2 write miss\n")
                    elif cmd[0] in ['READ','R','Read','r','read']:
                        L1Cache.read_miss_cnt+=1
                        L2Cache.read_miss_cnt+=1
                    if(func.isFull(L1Cache,addr)):
                        ###do L1 eviction start 
                        L1_evicted_line,L1_evicted_line_addr=func.evict(L1Cache,addr)#被evict掉的cacheline資訊&address,update to L2 cache 
                        if L1_evicted_line.dirty==True:#data need to be updated from L1 to L2
                            if(func.isFull(L2Cache,L1_evicted_line_addr)):#如果L2是滿的做 L2 evict
                                ###do L2 eviction start
                                L2_evicted_line,L2_evicted_line_addr=func.evict(L2Cache,L1_evicted_line_addr)
                                
                                #check back invalidation-> 找找看有沒有存在L1 cache
                                exist_line=func.checkBackInvalid(L1Cache,L2_evicted_line_addr)
                                if exist_line!=None:#被L2evict掉的cacheline存在L1裡(且L1cacheline的dirty=True)
                                    ###寫回memory L1 cache的data
                                    main_memory.append(exist_line)
                                    L1Cache.write_main_memory_cnt+=1
                                elif(exist_line==None and L2_evicted_line.dirty==True):#被L2evict掉的cacheline不存在L1裡(且L2cacheline的dirty=True)
                                    ###寫回memory L2 cache的data
                                    if L2method=="TSTM":
                                        decode_data=func.TSTMdecode(L2_evicted_line.data)
                                        L2_evicted_line.data=decode_data
                                    main_memory.append(L2_evicted_line)
                                    L2Cache.write_main_memory_cnt+=1
                                else:
                                    # 直接evict
                                    pass
                                ###do L2 eviction end
                            #print("4 %d" %len(L1_evicted_line.data))
                            func.write(L2Cache,None,L1_evicted_line_addr,L1_evicted_line.data,L2method)#update to L2
                        else:#不管他->直接丟掉
                            pass    
                        ###do L1 eviction end     
                    func.write(L1Cache,L1_line_hit_idx,addr,data,L1method)#place in L1
                    if(func.isFull(L2Cache,addr)):
                        ###do L2 eviction start
                        L2_evicted_line,L2_evicted_line_addr=func.evict(L2Cache,addr)
                                
                        #check back invalidation-> 找找看有沒有存在L1 cache
                        exist_line=func.checkBackInvalid(L1Cache,L2_evicted_line_addr)
                        if exist_line!=None:#被L2evict掉的cacheline存在L1裡(且L1cacheline的dirty=True)
                            ###寫回memory L1 cache的data
                            main_memory.append(exist_line)
                            L1Cache.write_main_memory_cnt+=1
                        elif(exist_line==None and L2_evicted_line.dirty==True):#被L2evict掉的cacheline不存在L1裡(且L2cacheline的dirty=True)
                            ###寫回memory L2 cache的data
                            if L2method=="TSTM":
                                decode_data=func.TSTMdecode(L2_evicted_line.data)
                                L2_evicted_line.data=decode_data
                            main_memory.append(L2_evicted_line)
                            L2Cache.write_main_memory_cnt+=1
                        else:
                            # 直接evict
                            pass
                        ###do L2 eviction end
                    #print("5 %d" %len(data))
                    func.write(L2Cache,L2_line_hit_idx,addr,data,L2method)#place in L2
            # time.sleep(0.1)

            flag+=1
        end=time.time()
        duration=end-start
        run_times-=1
        print(duration)
    print("done!")
    cal_total_energy(L1Cache,L1_r_energy,L1_w_ST_energy,L1_w_HT_energy,L1method)
    cal_total_energy(L2Cache,L2_r_energy,L2_w_ST_energy,L2_w_HT_energy,L2method)
    cal_total_lat(L1Cache,L1_r_lat,L1_w_STnHT_lat,L1_w_TT_lat,L1method)
    cal_total_lat(L2Cache,L2_r_lat,L2_w_STnHT_lat,L2_w_TT_lat,L2method)
    cal_total_wearing_times(L1Cache,L1method)
    cal_total_wearing_times(L2Cache,L2method)
    show_sim_cache_result(L1Cache,L1method,tracename) 
    show_sim_cache_result(L2Cache,L2method,tracename)   
    out_tmp_txt(L2Cache,L2method,tracename)
    print("------------------------",file=open( tracename , 'a+'))

def show_sim_cache_result(Cache,method,tracename):
    # Cache_level="L1" if Cache.__class__.__name__=="SLCCache" else "L2"
    print("【 %s %dMB %dway 2Level 】" %(method,Cache.cachesize/1024/1024,Cache.ways),file=open( tracename , 'a+'))
    print("block size : %d Byte" %(Cache.blocksize),file=open( tracename , 'a+'))
    print("Simulation Result:",file=open( tracename , 'a+'))
    print("hit count:",file=open( tracename , 'a+'))
    print("    w %d" %(Cache.write_hit_cnt),file=open( tracename , 'a+'))
    print("    r: %d" %(Cache.read_hit_cnt),file=open( tracename , 'a+'))
    print("miss count: " ,file=open( tracename , 'a+'))
    print("    w %d" %(Cache.write_miss_cnt),file=open( tracename , 'a+'))
    print("    r %d" %(Cache.read_miss_cnt),file=open( tracename , 'a+'))
    print("method=%s" %method,file=open( tracename , 'a+'))
    if (method=="TSTM" or method=="CMLC"):#Level 2 才需要計算TT
        if (method=="TSTM"):
            print("First cell occur TT %d" %(Cache.cell_status[0][0]),file=open( tracename , 'a+'))
            print("Middle cell occur TT %d" %(Cache.cell_status[1][0]),file=open( tracename , 'a+'))
            print("last cell occur TT %d" %(Cache.cell_status[2][0]),file=open( tracename , 'a+'))
        print("HT count %d" %(Cache.HT_cnt),file=open( tracename , 'a+'))
        print("ST count %d" %(Cache.ST_cnt),file=open( tracename , 'a+'))
        print("ZT count %d" %(Cache.ZT_cnt),file=open( tracename , 'a+'))
        print("TT count %d" %(Cache.TT_cnt),file=open( tracename , 'a+'))
        print("energy %f",Cache.total_energy,file=open( tracename , 'a+'))    
        print("latency %d " %Cache.total_lat,file=open( tracename , 'a+'))
        print("wearing times hard-domain %d " %Cache.total_wearing_hard_cnt,file=open( tracename , 'a+'))
        print("wearing times soft-domain %d " %Cache.total_wearing_soft_cnt,file=open( tracename , 'a+'))
    elif(method=="SLC") :
        print("write count %d" %(Cache.i_w_energy_cnt_per_cell),file=open( tracename , 'a+'))
        print("energy %f",Cache.total_energy,file=open( tracename , 'a+'))    
        print("latency %d " %Cache.total_lat,file=open( tracename , 'a+'))
        print("wearing times %d" %Cache.total_wearing_cnt,file=open( tracename , 'a+'))
def cal_total_energy(Cache,r_energy,w_ST_energy,w_HT_energy,method):
    """
    count_total_energy func 計算總耗能\n 
    param i_w_ST_energy_per_cell write data 時ST的耗能(以cell為單位)\n
    param i_w_HT_energy_per_cell write data 時HT的耗能(以cell為單位)\n  
    param i_read_energy_per_cell read data 時的耗能(以cell為單位)\n 
    param method TT/HT/ST/ZT\n 
    return total_energy
    """
    if method=="SLC":
        total_energy=Cache.i_w_energy_cnt_per_cell * w_ST_energy + Cache.i_r_energy_cnt_per_cell*r_energy
    else:
        if method=="TSTM":
            func.cal_total_TT_ST_HT_cnt(Cache)
            total_tt_cnt,total_st_cnt,total_ht_cnt=Cache.TT_cnt,Cache.ST_cnt,Cache.HT_cnt
            total_energy=(total_tt_cnt*(w_ST_energy+w_HT_energy)+total_st_cnt*w_ST_energy+total_ht_cnt*w_HT_energy+Cache.i_r_energy_cnt_per_cell*r_energy)
        else:
            total_tt_cnt,total_st_cnt,total_ht_cnt=Cache.TT_cnt,Cache.ST_cnt,Cache.HT_cnt
            print("CMLC %d " %Cache.i_r_energy_cnt_per_cell)
            total_energy=(total_tt_cnt*(w_ST_energy+w_HT_energy)+total_st_cnt*w_ST_energy+total_ht_cnt*w_HT_energy+Cache.i_r_energy_cnt_per_cell*r_energy)
    Cache.total_energy=total_energy
def cal_total_lat(Cache,r_lat,w_STnHT_lat,w_TT_lat,method):
    if method=="SLC":
        total_lat=(Cache.i_w_lat_cnt_per_CL*w_STnHT_lat + Cache.i_r_lat_cnt_per_CL*r_lat)
    elif method=="TSTM":
        #+ Cache.i_TSTMencode_cnt_per_CL*20
        total_lat=(2/3)*(Cache.i_w_lat_TT_cnt_per_CL*w_TT_lat + Cache.i_w_lat_NonTT_cnt_per_CL*w_STnHT_lat + Cache.i_r_lat_cnt_per_CL*r_lat + Cache.i_TSTMencode_cnt_per_CL*20)
    else:
        total_lat=Cache.i_w_lat_TT_cnt_per_CL*w_TT_lat + Cache.i_w_lat_NonTT_cnt_per_CL*w_STnHT_lat + Cache.i_r_lat_cnt_per_CL*r_lat
    Cache.total_lat=total_lat
def cal_total_wearing_times(Cache,method):
    if method=="SLC":
        Cache.total_wearing_cnt=Cache.i_w_energy_cnt_per_cell
    elif method=="TSTM":
        Cache.total_wearing_hard_cnt=Cache.TT_cnt+Cache.HT_cnt*(2/3)
        Cache.total_wearing_soft_cnt=2*Cache.TT_cnt+Cache.HT_cnt+Cache.ST_cnt*(2/3)
    else:
        Cache.total_wearing_hard_cnt=Cache.TT_cnt+Cache.HT_cnt
        Cache.total_wearing_soft_cnt=2*Cache.TT_cnt+Cache.HT_cnt+Cache.ST_cnt
def out_tmp_txt(Cache,method,tracename):
    tmp=list()
    print(" \"%s\" :" %method,end='',file=open( 'output/'+tracename.split("\\")[1] , 'a+'))
    tmp.append(Cache.total_energy)
    tmp.append(Cache.total_lat)
    if (method=="TSTM" or method=="CMLC"):#Level 2 才需要計算T    
        tmp.append(Cache.total_wearing_hard_cnt)
        tmp.append(Cache.total_wearing_soft_cnt)
    else:#SLC
        tmp.append(Cache.total_wearing_cnt)

    print(tmp,end='',file=open( 'output/'+tracename.split("\\")[1] , 'a+'))
    if method!="TSTM":
        print(",",end='',file=open( 'output/'+tracename.split("\\")[1] , 'a+'))
