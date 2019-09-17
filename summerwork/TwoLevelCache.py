# import TSTM_Cache as cache
# import tstm  as mytstm
# import math
main_memory=list()
import tstm  as mytstm
import math
import pandas as pd
import json
import time

class cacheline():
    def __init__(self,valid,tag,dirty,data,trans):
        self.valid = valid
        self.tag = tag
        self.dirty = dirty
        self.data = data
        self.TransType_result=trans
class SRAMCache():
    def __init__(self,addrBits,cachesize,blocksize,ways):
        self.addrBits=addrBits
        self.cachesize=cachesize
        self.blocksize=blocksize
        self.ways=ways
        self.number_of_lines = int(self.cachesize / self.blocksize)
        self.sets = int(self.number_of_lines/ self.ways)
        ###init cache table
        self.data = "1"*self.blocksize*8
        self.cache_table = [[cacheline(False,-1,False,self.data,None) for i in range(0, self.ways)] for i in range(0, self.sets)]
        
        self.write_hit_cnt=0
        self.write_miss_cnt=0
        self.read_hit_cnt=0
        self.read_miss_cnt=0
        self.read_from_next_level_cnt=0

    def write(self,line_hit_idx,addr,data): 
        """ write func pop out cacheline then insert to index 0 (put the newest data) 
            param line_hit_idx cacheline hit index in setXX
            param addr address
            param data data to be writen to cacheline
            return none
        """
        tag,set_idx,offset=L1splitAddr(addr)
        if (line_hit_idx==None):###找出cache中valid bit=False的cacheline index
            for line in self.cache_table[set_idx]:
                if line.valid==False:
                    line_hit_idx=self.cache_table[set_idx].index(line)

        line_hit=self.cache_table[set_idx].pop(line_hit_idx)
        self.CLreplacement(line_hit,tag,True,True)
        self.updateData(line_hit,data)
        self.cache_table[set_idx].insert(0,line_hit) #updata LRU,改完再塞回去
    def CLreplacement(self,cacheline,tag,valid=True,dirty=True):
        """ CLreplacement func cacheline(CL) replacement\n
            param tag new tag\n
            param dirty set dirty if data be modified \n
            return none 
        """
        cacheline.valid=valid
        cacheline.dirty=dirty
        cacheline.tag=tag
    def updateData(self,cacheline,data):
        """ updateData func update data of hit cacheline\n
            param data data to be written\n 
            return none
        """

        cacheline.data=data
    def read(self,line_hit_idx,addr,data): 
        """ read func pop out cacheline then insert to index 0 (put the newest data) 
            param line_hit_idx cacheline hit index in setXX
            param addr address
            param data data to be writen to cacheline
        """
        tag,set_idx,offset=L1splitAddr(addr)
        if (line_hit_idx==None):###找出cache中valid bit=False的cacheline index
            for line in self.cache_table[set_idx]:
                if line.valid==False:
                    line_hit_idx=self.cache_table[set_idx].index(line)
        line_hit=self.cache_table[set_idx].pop(line_hit_idx)
        
        if(line_hit_idx!=None):#if read hit, keep original cacheline.data
            data=line_hit.data

        self.CLreplacement(line_hit,tag,True,True)
        self.updateData(line_hit,data)
        self.cache_table[set_idx].insert(0,line_hit) #updata LRU
    def get_line_hit_idx(self,addr):
        """檢查set中有沒有發生hit\n
            param addr address\n
            return line_hit_idx line_hit_idx會回傳被pop出來的cacheline 在哪一個位置(ex: 4-ways return 0/1/2/3),若miss會回傳None
        """
        tag,set_idx,offset=L1splitAddr(addr)
        line_hit_idx=None
        for line in self.cache_table[set_idx]:
            if (line.tag==tag and line.valid==True):
                line_hit_idx=self.cache_table[set_idx].index(line)
        return line_hit_idx
    def isFull(self,addr):
        """ 檢查set中cacheline的valid bit 確認setXX 還有沒有空間\n
            param addr address\n
            return True-> if set is Full else  return False
        """
        valid_cnt=0
        tag,set_idx,offset=L1splitAddr(addr)
        for line in self.cache_table[set_idx]:
            if line.valid==True:
                valid_cnt+=1
        result= True if valid_cnt==self.ways else False
        return result
    def L1evict(self,addr):
        """
        L1evict func do L1 cache eviction\n
        param addr address\n
        /* 機制:被選到的cacheline valid bit設為false\n
           回傳\n
            (1)copy_line_least_used 複製一份被evict的cacheline info\n
            (2)ori_addr original address
        */
        """
        L1tag,L1set_idx,L1offset=L1splitAddr(addr)
        #print("L1 evict")
        ###被evict的cacheline valid bit設為false        
        self.cache_table[L1set_idx][self.ways-1].valid=False
        copy_line_least_used=self.cache_table[L1set_idx][self.ways-1]#line_least_used -> list最後面最少被使用到的
        ori_addr=reComAddr(copy_line_least_used.tag,L1set_idx,L1offset)#重新算addr
        return copy_line_least_used,ori_addr


class Cache():
    def __init__(self,addrBits,cachesize,blocksize,ways):
        self.addrBits=addrBits
        self.cachesize=cachesize
        self.blocksize=blocksize
        self.ways=ways
        self.number_of_lines = int(self.cachesize / self.blocksize)
        self.sets = int(self.number_of_lines/ self.ways)
        self.num_segment=int(self.blocksize*8/6)
        ###init cache table
        self.data = "1"*self.blocksize*8 
        self.cache_table = [[cacheline(False,-1,False,self.data,None) for i in range(0, self.ways)] for i in range(0, self.sets)]
        
        self.write_hit_cnt=0
        self.write_miss_cnt=0
        self.read_hit_cnt=0
        self.read_miss_cnt=0
        self.read_from_next_level_cnt=0

        ###TSTM setting
        self.TT_occur_first_cell=0
        self.TT_occur_mid_cell=0
        self.TT_occur_last_cell=0
        self.TT_cnt=0
        self.ST_cnt=0
        self.ZT_cnt=0
        self.HT_cnt=0
        self.TransType_result_tb=list()

    
        self.i_w_latency_cnt_per_cell=0
        self.i_r_latency_cnt_per_cell=0
        self.i_r_energy_cnt_per_cell=0
        self.i_w_energy_cnt_per_cell=0 #SLC
        #TSTM need extra record
        self.i_encode_cnt=0 
    def write(self,line_hit_idx,addr,data,method): 
        """ write func pop out cacheline then insert to index 0 (put the newest data) 
            param line_hit_idx cacheline hit index in setXX
            param addr address
            param data data to be writen to cacheline
            param method design to do "TSTM" or "CMLC"
            return none
        """
        tag,set_idx,offset=L2splitAddr(addr)
        if (line_hit_idx==None):###找出cache中valid bit=False的cacheline index
            for line in self.cache_table[set_idx]:
                if line.valid==False:
                    line_hit_idx=self.cache_table[set_idx].index(line)

        line_hit=self.cache_table[set_idx].pop(line_hit_idx)
        self.CLreplacement(line_hit,tag,True,True)
        line_hit.TransType_result=self.updateData(line_hit,line_hit.data,data,method)
        self.TransType_result_tb.append(line_hit.TransType_result)#把編碼完的結果存在list裡最後轉成excel
        self.cache_table[set_idx].insert(0,line_hit) #updata LRU,改完再塞回去
    def CLreplacement(self,cacheline,tag,valid=True,dirty=True):
        """ CLreplacement func cacheline(CL) replacement\n
            param tag new tag\n
            param dirty set dirty if data be modified \n
            return none 
        """
        cacheline.valid=valid
        cacheline.dirty=dirty
        cacheline.tag=tag
    def updateData(self,cacheline,original_data,target_data,method="CMLC"):
        """ updateData func update data of hit cacheline\n
            param original_data original data place in cacheline\n 
            param target_data data to be written to cacheline\n 
            param method decide to use CMLC or TSTM\n 
            return energy_list \n 
            TSTM : [['TT','ST','ZT'],['TT','ST','ZT'],['TT','ST','ZT']....]\n 
            CMLC : ['TT','ST','ZT','HT',.....]\n 
        """
        encoded_data=""
        energy_list=list()#用來放每個set裡的block發生哪些type
        if method=="TSTM":
            #self.i_r_energy_cnt_per_cell+=int(len(original_data)/2)
            i_targetdata_bit=4 
            i_originaldata_bit=int(i_targetdata_bit*1.5)    
            for num in range(self.num_segment):
                target=target_data[num*i_targetdata_bit:num*i_targetdata_bit+i_targetdata_bit]
                original=original_data[num*i_originaldata_bit:num*i_originaldata_bit+i_originaldata_bit]
                candidate_data=tstm_table.loc[original,target]
                energy_list.append(tstm.getTransType(original,candidate_data))#回傳['TT','ST','ZT']
                encoded_data+=candidate_data 
            cacheline.data=encoded_data
        elif(method=="CMLC"):
            # print("original data length:%d"%(len(original_data)))
            # print("target data length:%d"%(len(target_data)))
            energy_list.append(tstm.getTransType(original_data,target_data))#回傳['TT','ST','ZT']
            encoded_data=target_data 
            cacheline.data=encoded_data
        else:
            energy_list=None
            self.i_w_energy_cnt_per_cell+=len(target_data)
            cacheline.data=target_data
      
        return energy_list #encoded_data回傳編碼後的718 bits data,energy_list是[['TT','ST','ZT']*128]的陣列
    def read(self,line_hit_idx,addr,data,method): 
        """ read func pop out cacheline then insert to index 0 (put the newest data) 
            param line_hit_idx cacheline hit index in setXX
            param addr address
            param data data to be writen to cacheline
            param method design to do "TSTM" or "CMLC"
            return L1addr,copy_line_hit 當L2 cache read hit時要把address組合回去&cacheline的data傳回去
        """
        tag,set_idx,offset=L2splitAddr(addr)
        if (line_hit_idx==None):###找出cache中valid bit=False的cacheline index
            for line in self.cache_table[set_idx]:
                if line.valid==False:
                    line_hit_idx=self.cache_table[set_idx].index(line)
        line_hit=self.cache_table[set_idx].pop(line_hit_idx)
        
        if(line_hit_idx!=None):#if read hit, keep original cacheline.data
            data=line_hit.data
            
        self.CLreplacement(line_hit,tag,True,True)
        line_hit.TransType_result=self.updateData(line_hit,line_hit.data,data,method)
        if method!="SLC":
            self.TransType_result_tb.append(line_hit.TransType_result)#把編碼完的結果存在list裡最後轉成excel
        self.cache_table[set_idx].insert(0,line_hit) #updata LRU
        ori_addr=reComAddr(line_hit.tag,set_idx,offset)
        copy_line_hit=line_hit
        return copy_line_hit,ori_addr
    def get_line_hit_idx(self,addr):
        """檢查set中有沒有發生hit\n
            param addr address\n
            return line_hit_idx line_hit_idx會回傳被pop出來的cacheline 在哪一個位置(ex: 4-ways return 0/1/2/3),若miss會回傳None
        """
        tag,set_idx,offset=L2splitAddr(addr)
        line_hit_idx=None
        for line in self.cache_table[set_idx]:
            if (line.tag==tag and line.valid==True):
                line_hit_idx=self.cache_table[set_idx].index(line)
        return line_hit_idx
    def isFull(self,addr):
        """ 檢查set中cacheline的valid bit 確認setXX 還有沒有空間\n
            param addr address\n
            return True-> if set is Full else  return False
        """
        valid_cnt=0
        tag,set_idx,offset=L2splitAddr(addr)
        for line in self.cache_table[set_idx]:
            if line.valid==True:
                valid_cnt+=1
        result= True if valid_cnt==self.ways else False
        return result
    def L2evict(self,addr):
        """
        L2evict func do L2 cache eviction\n
        param addr address\n
        /* 機制:被選到的cacheline valid bit設為false \n
           回傳\n
            (1)copy_line_least_used 複製一份被evict的cacheline info\n
            (2)ori_addr original address
        */
        """
        L2tag,L2set_idx,L2offset=L2splitAddr(addr)
        #print("L2 evict")
        ###被選到的cacheline valid bit設為false
        
        self.cache_table[L2set_idx][self.ways-1].valid=False
        copy_line_least_used=self.cache_table[L2set_idx][self.ways-1]
        ori_addr=reComAddr(copy_line_least_used.tag,L2set_idx,L2offset)
        return copy_line_least_used,ori_addr
    def TT_occur_cell(self,TransType_list,method): 
        """ 
        TT_occur_cell func 看TT發生在哪個cell(TSTM才需要紀錄)\n 
        param method decide to use CMLC or TSTM\n 
        return TT發生在 first,middle,last cell的次數\n 
        """
        if method=="TSTM":
            for seg in TransType_list:
                if 'TT' == seg[0]:
                    self.TT_occur_first_cell+=1
                if 'TT' == seg[1]:
                    self.TT_occur_mid_cell+=1
                if 'TT' == seg[2]:
                    self.TT_occur_last_cell+=1
    def output_result(self,type_list):
        Trans_df=pd.DataFrame(type_list)
        Trans_df.to_excel("TSTM.xls")
    def count_TT_occur(self,TransType_list,method):
        """
        count_TT_occur func 紀錄ST,TT,HT,ZT發生的次數\n 
        param TransType_list 裡面記錄ZT,HT,TT,ST的資訊\n 
        param method decide to use CMLC or TSTM\n 
        return none
        """
        if(method=="TSTM" or method=="CMLC"):
            tmp=list()
            for seg in TransType_list:
                for cell_status in seg: #cell_status 'HT','ST','ZT','TT'
                    tmp.append(cell_status)
            TransType_list=tmp
            self.TT_cnt+=TransType_list.count('TT')
            self.ST_cnt+=TransType_list.count('ST')
            self.HT_cnt+=TransType_list.count('HT')
            self.ZT_cnt+=TransType_list.count('ZT')
    def count_total_energy(self,i_w_ST_energy_per_cell,i_w_HT_energy_per_cell,i_w_energy_per_cell,i_r_energy_per_cell,method):
        """
        count_total_energy func 計算總耗能\n 
        param i_w_ST_energy_per_cell write data 時ST的耗能(以cell為單位)\n
        param i_w_HT_energy_per_cell write data 時HT的耗能(以cell為單位)\n  
        param i_read_energy_per_cell read data 時的耗能(以cell為單位)\n 
        param method TT/HT/ST/ZT\n 
        return total_energy
        """
        if method=="SLC":
            
            total_energy=self.i_w_energy_cnt_per_cell*i_w_energy_per_cell
        else:
            hard_domain=self.HT_cnt+self.TT_cnt
            soft_domain=self.ST_cnt+self.TT_cnt
            if method=="TSTM":
                total_energy=hard_domain*i_w_HT_energy_per_cell+soft_domain*i_w_ST_energy_per_cell+self.i_r_energy_cnt_per_cell*i_r_energy_per_cell
            else:
                total_energy=hard_domain*i_w_HT_energy_per_cell+soft_domain*i_w_ST_energy_per_cell
        return total_energy

def hex2bin(hex_str,totalBits=0):
    return bin(int(hex_str,16))[2:].zfill(totalBits)
def read_trace(filename,addrBits):
    with open(filename) as f:
        cmd_list = f.readlines()
        cmd_list = [x.split() for x in cmd_list] 
    bin_cmd_list=list() # convert hex to binary
    for cmd in cmd_list:
        if(cmd[0]in['WRITE','W','Write','w','write','READ','R','Read','r','read']):
            #write todo 
            addr=cmd[1]
            bin_addr=hex2bin(addr[2:],addrBits)
            data= ''.join(cmd[2:])
            bin_data=hex2bin(data,512)
            bin_cmd=list()
            bin_cmd.append(cmd[0])
            bin_cmd.append(bin_addr)
            bin_cmd.append(bin_data)
            bin_cmd_list.append(bin_cmd)
    return bin_cmd_list 
def reComAddr(tag,set_idx,offset):
    """ L1reComAddr func recombine address\n
        param tag tag\n
        param set_idx set index\n
        param offset data offset\n
        return addr address
    """
    addr = tag + bin(set_idx)[2:] + bin(offset)[2:]
    return addr
def L1splitAddr(addr):
    """ L1splitAddr func split address\n
        param addr address\n
        return tag,set index,offset
    """
    offset = 6
    set_idx = int(addr[L1Cache.addrBits-int(math.log(L1Cache.sets,2))-offset:L1Cache.addrBits-offset],2)#int(addr[11:26],2)
    tag = addr[:L1Cache.addrBits-int(math.log(L1Cache.sets,2))-offset]#addr[0:11]
    return tag,set_idx,offset
def L2splitAddr(addr):
    """ L2splitAddr func split address\n
        param addr address\n
        return tag,set index,offset
    """
    offset = 6
    set_idx = int(addr[L2Cache.addrBits-int(math.log(L2Cache.sets,2))-offset:L2Cache.addrBits-offset],2)#int(addr[11:26],2)
    tag = addr[:L2Cache.addrBits-int(math.log(L2Cache.sets,2))-offset]#addr[0:11]
    return tag,set_idx,offset
def checkBackInvalid(addr,Cache):
    """ checkBackInvalid func 檢查被L2 cache evict掉的有沒有在L1裡面\n
        如果存在的話\n
        (1)檢查dirty如果是True就要寫回memory L1的資訊\n
            但如果是False就直接evict\n
        (2)valid bit 設為false\n
        return copy_line_hit 如果copy_line_hit!=None表示被L2 evict掉的cacheline存在L1cache 中
    """
    #print(Cache)
    ###檢查被L2 cache evict掉的有沒有在L1裡面
    tag,set_idx,offset=L1splitAddr(addr)
    line_hit_idx=Cache.get_line_hit_idx(addr)#L1 cache hit
    L1_line_hit=None #若L1_line_hit是None表示不在L1 cache中
    copy_line_hit=None #若L1_cache_line有找到,copy_line_hit會複製一份其資訊

    if(line_hit_idx!=None):#在L1裡面
        L1_line_hit=Cache.cache_table[set_idx][line_hit_idx]
        ###(1)檢查dirty如果是True就要寫回memory L1的資訊但如果是False就直接evict
        if L1_line_hit.dirty==True:#write back data from L1 cache 
            copy_line_hit=L1_line_hit 
        else:
            pass
        ###(2)valid bit 設為false
        #print(Cache.cache_table[set_idx][line_hit_idx].valid)
        Cache.cache_table[set_idx][line_hit_idx].valid=False
        #print(Cache.cache_table[set_idx][line_hit_idx].valid)
    else:#不在L1裡面
        pass
    return copy_line_hit
def print_sim(method,Cache,energy):
    # Cache_level="L1" if Cache.__class__.__name__=="SLCCache" else "L2"
    print("【 %s %dKB %dway 2Level 】" %(method,Cache.cachesize/1024,Cache.ways))
    print("block size : %d Byte" %(Cache.blocksize))
    print("Simulation Result:")
    print("hit count:")
    print("    w %d" %(Cache.write_hit_cnt))
    print("    r: %d" %(Cache.read_hit_cnt))
    print("miss count: " )
    print("    w %d" %(Cache.write_miss_cnt))
    print("    r %d" %(Cache.read_miss_cnt))
    print("method=%s" %method)
    if (method=="TSTM" or method=="CMLC"):#Level 2 才需要計算TT
        if (method=="TSTM"):
            print("First cell occur TT %d" %(Cache.TT_occur_first_cell))
            print("Middle cell occur TT %d" %(Cache.TT_occur_mid_cell))
            print("last cell occur TT %d" %(Cache.TT_occur_last_cell))
        print("HT count %d" %(Cache.HT_cnt))
        print("ST count %d" %(Cache.ST_cnt))
        print("ZT count %d" %(Cache.ZT_cnt))
        print("TT count %d" %(Cache.TT_cnt))
        print("energy %.3f",energy)
    elif(method=="SLC") :
        print("energy %.3f",energy)    
def output_txt(method,Cache,energy):
    #Cache_level="L1" if Cache.__class__.__name__=="SLCCache" else "L2"
    f.write("【 %s %dKB %dway 2Level 】\n" %(method,Cache.cachesize/1024,Cache.ways))
    f.write("block size : %d Byte\n" %(Cache.blocksize))
    f.write("Simulation Result:\n")
    f.write("hit count:\n")
    f.write("    w %d\n" %(Cache.write_hit_cnt))
    f.write("    r: %d\n" %(Cache.read_hit_cnt))
    f.write("miss count: \n" )
    f.write("    w %d\n" %(Cache.write_miss_cnt))
    f.write("    r %d\n" %(Cache.read_miss_cnt))
    if (method=="TSTM" or method=="CMLC"):#Level 2 才需要計算TT
        if (method=="TSTM"):
            f.write("First cell occur TT %d\n" %(Cache.TT_occur_first_cell))
            f.write("Middle cell occur TT %d\n" %(Cache.TT_occur_mid_cell))
            f.write("last cell occur TT %d\n" %(Cache.TT_occur_last_cell))
        f.write("HT count %d\n" %(Cache.HT_cnt))
        f.write("ST count %d\n" %(Cache.ST_cnt))
        f.write("ZT count %d\n" %(Cache.ZT_cnt))
        f.write("TT count %d\n" %(Cache.TT_cnt))
        f.write("energy %.3f\n" %(energy))
    else:
        f.write("energy %.3f\n" %(energy))
def read_ini(filename):
    with open(filename,'r')as inifile:
        data=inifile.read()
    obj=json.loads(data)
    return obj
def TranSize(s_cachesize):
    if "MB" in s_cachesize :
        i_cachesize = int(s_cachesize[:-2])*1024*1024
    elif "KB" in s_cachesize :
        i_cachesize= int(s_cachesize[:-2])*1024 
    else:
        i_cachesize=int(s_cachesize[:-1])
    return i_cachesize
class init_setting():
    def __init__(self):
        obj=read_ini('init.json')
        self.L1cachesize=TranSize(obj["LEVEL1"]["CACHESIZE"].upper())
        self.L1cachelinesize=TranSize(obj["LEVEL1"]["CACHELINESZ"].upper())
        self.L1way=obj["LEVEL1"]["WAY"]
        self.L1addrBits=obj["LEVEL1"]["ADDRBITS"]
        self.L2cachesize=TranSize(obj["LEVEL2"]["CACHESIZE"].upper())
        self.L2cachelinesize=TranSize(obj["LEVEL2"]["CACHELINESZ"].upper())
        self.L2way=obj["LEVEL2"]["WAY"]
        self.L2addrBits=obj["LEVEL2"]["ADDRBITS"]
        self.tracefile=obj["GENERAL"]["TRACE_PATH"]+obj["GENERAL"]["TRACE_NAME"]
        self.b_traceall=obj["GENERAL"]["TRACE_ALL_RUN"]

if __name__ == '__main__': 
    start=time.time()
    init=init_setting()
    #for tracefile in ['trace/bitcount_V2.txt','trace/crc_V2.txt','trace/patricia_V2.txt','trace/qsort_V2.txt','trace/susan_V2.txt']:
    L1Cache=SRAMCache(init.L1addrBits,init.L1cachesize,init.L1cachelinesize,init.L1way) 
    tstm=mytstm.TSTM()
    tstm_table=tstm.table
    L1method="SRAM"
    cmd_list=read_trace(init.tracefile,init.L1addrBits)     
    print("tracefile name: %s" %(init.tracefile))
    print("trace file size: %d " %(len(cmd_list)))

    #for method in ["SLC","CMLC","TSTM"]:
    for method in ["CMLC"]:
        L2method=method
        L2Cache=Cache(init.L2addrBits,init.L2cachesize,init.L2cachelinesize,init.L2way)
        flag=1
        write_main_memory_cnt=0
        # tt = open('temp.txt', 'w', encoding = 'UTF-8')
        for cmd in cmd_list:
            #print(flag)
            addr,data=cmd[1:]
            L1_line_hit_idx=L1Cache.get_line_hit_idx(addr)
            if(L1_line_hit_idx!=None):#L1 cache hit
                if cmd[0]in ['WRITE','W','Write','w','write']: #write to L1 cache
                    L1Cache.write_hit_cnt+=1
                    L1Cache.write(L1_line_hit_idx,addr,data)
                    # tt.write("L1 write hit\n")
                elif cmd[0] in ['READ','R','Read','r','read']: #read from L1 cache
                    L1Cache.read_hit_cnt+=1
                    L1Cache.read(L1_line_hit_idx,addr,data)
                    # tt.write("L1 read hit\n")
            else:#L1 cache miss 
                L2_line_hit_idx=L2Cache.get_line_hit_idx(addr)
                if(L2_line_hit_idx!=None):#L2 cache hit
                    if cmd[0]in ['WRITE','W','Write','w','write']: 
                        L1Cache.write_miss_cnt+=1
                        L2Cache.write_hit_cnt+=1
                        # tt.write("write L1 miss L2 hit\n")
                        L2Cache.write(L2_line_hit_idx,addr,data,L2method)#update L2 cache
                        
                        if(L1Cache.isFull(addr)): #check if L1 cache is full
                            ###do L1 eviction start 
                            L1_evicted_line,L1_evicted_line_addr=L1Cache.L1evict(addr)#被evict掉的cacheline資訊&address,update to L2 cache 
                            if L1_evicted_line.dirty==True:#data need to be updated from L1 to L2
                                if(L2Cache.isFull(L1_evicted_line_addr)):#如果L2是滿的做 L2 evict
                                    ###do L2 eviction start
                                    L2_evicted_line,L2_evicted_line_addr=L2Cache.L2evict(L1_evicted_line_addr)
                                    
                                    #check back invalidation-> 找找看有沒有存在L1 cache
                                    exist_line=checkBackInvalid(L2_evicted_line_addr,L1Cache)
                                    if exist_line!=None:#被L2evict掉的cacheline存在L1裡(且L1cacheline的dirty=True)
                                        ###寫回memory L1 cache的data
                                        main_memory.append(exist_line)
                                        #record write_main_memory_cnt???
                                        write_main_memory_cnt+=1
                                    elif(exist_line==None and L2_evicted_line.dirty==True):#被L2evict掉的cacheline不存在L1裡(且L2cacheline的dirty=True)
                                        ###寫回memory L2 cache的data
                                        main_memory.append(L2_evicted_line)
                                        #record write_main_memory_cnt???
                                        write_main_memory_cnt+=1
                                    else:
                                        # 直接evict
                                        pass
                                    ###do L2 eviction end
                                L2Cache.write(None,L1_evicted_line_addr,L1_evicted_line.data,L2method)#被L1 evict 的cacheline update to L2
                            else:#不管他->直接丟掉
                                pass    
                            ###do L1 eviction end                            
                        L1Cache.write(L1_line_hit_idx,addr,data)  #place in L1 cache
                    elif cmd[0] in ['READ','R','Read','r','read']: # L2 cache read hit
                        L1Cache.read_miss_cnt+=1
                        L2Cache.read_hit_cnt+=1
                        # tt.write("read L1 miss L2 hit\n")
                        line_hit,addr=L2Cache.read(L2_line_hit_idx,addr,data,L2method) #read from L2 cache 
                        tstm.TSTM_Decoding(line_hit.data)#從L2讀出來的data要做decode
                        if(L1Cache.isFull(addr)): #check if L1 cache is full
                            ###do L1 eviction start 
                            L1_evicted_line,L1_evicted_line_addr=L1Cache.L1evict(addr)#被evict掉的cacheline資訊&address,update to L2 cache 
                            if L1_evicted_line.dirty==True:#data need to be updated from L1 to L2
                                if(L2Cache.isFull(L1_evicted_line_addr)):#如果L2是滿的做 L2 evict
                                    ###do L2 eviction start
                                    L2_evicted_line,L2_evicted_line_addr=L2Cache.L2evict(L1_evicted_line_addr)
                                    
                                    #check back invalidation-> 找找看有沒有存在L1 cache
                                    exist_line=checkBackInvalid(L2_evicted_line_addr,L1Cache)
                                    if exist_line!=None:#被L2evict掉的cacheline存在L1裡(且L1cacheline的dirty=True)
                                        ###寫回memory L1 cache的data
                                        main_memory.append(exist_line)
                                        #record write_main_memory_cnt???
                                        write_main_memory_cnt+=1
                                    elif(exist_line==None and L2_evicted_line.dirty==True):#被L2evict掉的cacheline不存在L1裡(且L2cacheline的dirty=True)
                                        ###寫回memory L2 cache的data
                                        main_memory.append(L2_evicted_line)
                                        #record write_main_memory_cnt???
                                        write_main_memory_cnt+=1
                                    else:
                                        # 直接evict
                                        pass
                                    ###do L2 eviction end
                                L2Cache.write(None,L1_evicted_line_addr,L1_evicted_line.data,L2method)#update to L2
                            else:#不管他->直接丟掉
                                pass    
                            ###do L1 eviction end     
                        L1Cache.write(L1_line_hit_idx,addr,line_hit.data)#place in L1 
                else:#both L1 and L2 cache miss
                    if cmd[0]in ['WRITE','W','Write','w','write']: 
                        L1Cache.write_miss_cnt+=1
                        L2Cache.write_miss_cnt+=1
                        # tt.write("L1 and L2 write miss\n")
                    elif cmd[0] in ['READ','R','Read','r','read']:
                        L1Cache.read_miss_cnt+=1
                        L2Cache.read_miss_cnt+=1
                        # tt.write("L1 and L2 read miss\n")
                    if(L1Cache.isFull(addr)):
                        ###do L1 eviction start 
                        L1_evicted_line,L1_evicted_line_addr=L1Cache.L1evict(addr)#被evict掉的cacheline資訊&address,update to L2 cache 
                        if L1_evicted_line.dirty==True:#data need to be updated from L1 to L2
                            if(L2Cache.isFull(L1_evicted_line_addr)):#如果L2是滿的做 L2 evict
                                ###do L2 eviction start
                                L2_evicted_line,L2_evicted_line_addr=L2Cache.L2evict(L1_evicted_line_addr)
                                
                                #check back invalidation-> 找找看有沒有存在L1 cache
                                exist_line=checkBackInvalid(L2_evicted_line_addr,L1Cache)
                                if exist_line!=None:#被L2evict掉的cacheline存在L1裡(且L1cacheline的dirty=True)
                                    ###寫回memory L1 cache的data
                                    main_memory.append(exist_line)
                                    #record write_main_memory_cnt???
                                    write_main_memory_cnt+=1
                                elif(exist_line==None and L2_evicted_line.dirty==True):#被L2evict掉的cacheline不存在L1裡(且L2cacheline的dirty=True)
                                    ###寫回memory L2 cache的data
                                    main_memory.append(L2_evicted_line)
                                    #record write_main_memory_cnt???
                                    write_main_memory_cnt+=1
                                else:
                                    # 直接evict
                                    pass
                                ###do L2 eviction end
                            L2Cache.write(None,L1_evicted_line_addr,L1_evicted_line.data,L2method)#update to L2
                        else:#不管他->直接丟掉
                            pass    
                        ###do L1 eviction end     
                    L1Cache.write(L1_line_hit_idx,addr,data)#place in L1
                    if(L2Cache.isFull(addr)):
                        ###do L2 eviction start
                        L2_evicted_line,L2_evicted_line_addr=L2Cache.L2evict(addr)
                                
                        #check back invalidation-> 找找看有沒有存在L1 cache
                        exist_line=checkBackInvalid(L2_evicted_line_addr,L1Cache)
                        if exist_line!=None:#被L2evict掉的cacheline存在L1裡(且L1cacheline的dirty=True)
                            ###寫回memory L1 cache的data
                            main_memory.append(exist_line)
                            #record write_main_memory_cnt???
                            write_main_memory_cnt+=1
                        elif(exist_line==None and L2_evicted_line.dirty==True):#被L2evict掉的cacheline不存在L1裡(且L2cacheline的dirty=True)
                            ###寫回memory L2 cache的data
                            main_memory.append(L2_evicted_line)
                            #record write_main_memory_cnt???
                            write_main_memory_cnt+=1
                        else:
                            # 直接evict
                            pass
                        ###do L2 eviction end
                    L2Cache.write(L2_line_hit_idx,addr,data,L2method)#place in L2

                
            flag+=1
        # tt.close()
        for i in L2Cache.TransType_result_tb:
            L2Cache.TT_occur_cell(i,L2method)
            L2Cache.count_TT_occur(i,L2method)
        L2Cache.output_result(L2Cache.TransType_result_tb)
        total_energy=L2Cache.count_total_energy(1.92,3.192,3,0.9*2,L2method)
        print_sim(L1method,L1Cache,0)
        print_sim(L2method,L2Cache,total_energy)
        f = open('result0823.txt', 'a+', encoding = 'UTF-8')
        f.write("tracefile name: %s \n" %(init.tracefile))
        output_txt(L1method,L1Cache,0)
        output_txt(L2method,L2Cache,total_energy)
        f.close()
        end=time.time()
        print("time cost : %d s" %(end-start))
        
