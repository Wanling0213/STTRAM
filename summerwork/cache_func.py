import math
import tstm  as mytstm
tstm=mytstm.TSTM()
tstm_table=tstm.table
import copy
def write(Cache,line_hit_idx,addr,data,method): 
    """ write func pop out cacheline then insert to index 0 (put the newest data) 
        param line_hit_idx cacheline hit index in setXX
        param addr address
        param data data to be writen to cacheline
        param method design to do "TSTM" or "CMLC"
        return none
    """
    tag,set_idx,offset=splitAddr(Cache,addr)
    if (line_hit_idx==None):###找出cache中valid bit=False的cacheline index
        for line in Cache.cache_table[set_idx]:
            if line.valid==False:
                line_hit_idx=Cache.cache_table[set_idx].index(line)
                break

    line_hit=Cache.cache_table[set_idx].pop(line_hit_idx)
    CLreplacement(line_hit,tag,True,True)
    updateData(Cache,line_hit,line_hit.data,data,method)
    Cache.cache_table[set_idx].insert(0,line_hit) #updata LRU,改完再塞回去
def read(Cache,line_hit_idx,addr,data,method): 
    """ read func pop out cacheline then insert to index 0 (put the newest data) 
        param line_hit_idx cacheline hit index in setXX
        param addr address
        param data data to be writen to cacheline
        return copy_line_hit
    """
    tag,set_idx,offset=splitAddr(Cache,addr)
    if (line_hit_idx==None):###找出cache中valid bit=False的cacheline index
        for line in Cache.cache_table[set_idx]:
            if line.valid==False:
                line_hit_idx=Cache.cache_table[set_idx].index(line)
                break
    line_hit=Cache.cache_table[set_idx].pop(line_hit_idx)
    
    CLreplacement(line_hit,tag,True,True)
    if(line_hit_idx!=None):#if read hit, keep original cacheline.data
        # data=line_hit.data
        if method=="SLC":
            Cache.i_r_energy_cnt_per_cell+=len(line_hit.data)
            Cache.i_r_lat_cnt_per_CL+=1
        else:
            Cache.i_r_energy_cnt_per_cell+=int(len(line_hit.data)/2)
            Cache.i_r_lat_cnt_per_CL+=1
        pass
    else:
        updateData(Cache,line_hit,line_hit.data,data,method)
            
    Cache.cache_table[set_idx].insert(0,line_hit) #updata LRU
    copy_line_hit=copy.deepcopy(line_hit)
    ori_addr=comAddr(Cache,line_hit.tag,set_idx,offset)
    return copy_line_hit,ori_addr
def CLreplacement(cacheline,tag,valid=True,dirty=True):
    """ CLreplacement func cacheline(CL) replacement\n
        param tag new tag\n
        param dirty set dirty if data be modified \n
        return none 
    """
    cacheline.valid=valid
    cacheline.dirty=dirty
    cacheline.tag=tag
def get_line_hit_idx(Cache,addr):
    """檢查set中有沒有發生hit\n
        param addr address\n
        return line_hit_idx line_hit_idx會回傳被pop出來的cacheline 在哪一個位置(ex: 4-ways return 0/1/2/3),若miss會回傳None
    """
    tag,set_idx,offset=splitAddr(Cache,addr)
    line_hit_idx=None
    for line in Cache.cache_table[set_idx]:
        if (line.tag==tag and line.valid==True):
            line_hit_idx=Cache.cache_table[set_idx].index(line)
    return line_hit_idx
def updateData(Cache,cacheline,original_data,target_data,method="CMLC"):
    """ updateData func update data of hit cacheline\n
        param original_data original data place in cacheline\n 
        param target_data data to be written to cacheline\n 
        param method decide to use CMLC or TSTM\n 
    「"""
    encoded_data=""
    has_TT=False
    if method=="TSTM":
        # print("!!!")
        # print("original data %d" %len(original_data))
        # print("target_data%d" %len(target_data))
        i_targetdata_bit=4 
        i_originaldata_bit=int(i_targetdata_bit*1.5)   
        for num in range(Cache.num_segment):
            target=target_data[num*i_targetdata_bit:num*i_targetdata_bit+i_targetdata_bit]
            original=original_data[num*i_originaldata_bit:num*i_originaldata_bit+i_originaldata_bit]
            candidate_data=tstm_table.loc[original,target]
            encoded_data+=candidate_data 
            translist=tstm.getTransType(original,candidate_data)
            if 'TT' in translist:
                has_TT=True
            cal_TT_ST_HT_cnt_per_cell(Cache,translist)
        cacheline.data=encoded_data
        Cache.i_r_energy_cnt_per_cell+=int(len(original_data)/2)
        Cache.i_r_lat_cnt_per_CL+=1
        if has_TT==True:
            Cache.i_w_lat_TT_cnt_per_CL+=1
        else:
            Cache.i_w_lat_NonTT_cnt_per_CL+=1
        Cache.i_TSTMencode_cnt_per_CL+=1
        # print("encoded_data%d" %len(encoded_data))
        # print("----")
    elif(method=="CMLC"):
        tt_cnt_per_CL=convert(Cache,target_data)
        if tt_cnt_per_CL > 0 :
            has_TT= True
        encoded_data=target_data 
        cacheline.data=encoded_data
        if has_TT==True:
            Cache.i_w_lat_TT_cnt_per_CL+=1
        else:
            Cache.i_w_lat_NonTT_cnt_per_CL+=1
    else:
        cacheline.data=target_data 
        Cache.i_w_energy_cnt_per_cell+=len(target_data)
        Cache.i_w_lat_cnt_per_CL+=1  
def cal_w_energy_cnt(Cache,data):
    """專門給SLC用的計算寫入能量"""    
    Cache.i_w_energy_cnt_per_cell+=len(data)
def cal_TT_ST_HT_cnt_per_cell(Cache,translist):
    """專門給TSTM用的計算寫入能量""" 
    #first cell
    if (translist[0]=="TT"):
        Cache.i_first_cell[0]+=1
    elif (translist[0]=="ST"):
        Cache.i_first_cell[1]+=1
    elif (translist[0]=="HT"):
        Cache.i_first_cell[2]+=1
    elif (translist[0]=="ZT"):
        Cache.i_first_cell[3]+=1
    #middle cell
    if (translist[1]=="TT"):
        Cache.i_mid_cell[0]+=1
    elif (translist[1]=="ST"):
        Cache.i_mid_cell[1]+=1
    elif (translist[1]=="HT"):
        Cache.i_mid_cell[2]+=1
    elif (translist[1]=="ZT"):
        Cache.i_mid_cell[3]+=1
    #last cell
    if (translist[2]=="TT"):
        Cache.i_last_cell[0]+=1
    elif (translist[2]=="ST"):
        Cache.i_last_cell[1]+=1
    elif (translist[2]=="HT"):
        Cache.i_last_cell[2]+=1
    elif (translist[2]=="ZT"):
        Cache.i_last_cell[3]+=1

def cal_total_TT_ST_HT_cnt(Cache):
    Cache.TT_cnt=Cache.i_first_cell[0]+Cache.i_mid_cell[0]+Cache.i_last_cell[0]*(2/3)
    Cache.ST_cnt=Cache.i_first_cell[1]+Cache.i_mid_cell[1]+Cache.i_last_cell[1]*(2/3)
    Cache.HT_cnt=Cache.i_first_cell[2]+Cache.i_mid_cell[2]+Cache.i_last_cell[2]*(2/3)
    Cache.ZT_cnt=Cache.i_first_cell[3]+Cache.i_mid_cell[3]+Cache.i_last_cell[3]*(2/3)
def convert(Cache,translist):
    tt_cnt_in_CL=0
    for i in range(0,len(translist),2):
        if translist[i] != translist[i+1]:
            Cache.TT_cnt+=1
            tt_cnt_in_CL+=1
        else:
            Cache.HT_cnt+=1
    return tt_cnt_in_CL    
def isFull(Cache,addr):
    """ 檢查set中cacheline的valid bit 確認setXX 還有沒有空間\n
        param addr address\n
        return True-> if set is Full else  return False
    """
    valid_cnt=0
    tag,set_idx,offset=splitAddr(Cache,addr)
    for line in Cache.cache_table[set_idx]:
        if line.valid==True:
            valid_cnt+=1
    result= True if valid_cnt==Cache.ways else False
    return result
def evict(Cache,addr):
    """
    evict func do cache eviction\n
    param addr address\n
    /* 機制:被選到的cacheline valid bit設為false\n
        回傳\n
        (1)copy_line_least_used 複製一份被evict的cacheline info\n
        (2)ori_addr original address
    */
    """
    tag,set_idx,offset=splitAddr(Cache,addr)
    ###被evict的cacheline valid bit設為false        
    Cache.cache_table[set_idx][Cache.ways-1].valid=False
    copy_line_least_used=copy.deepcopy(Cache.cache_table[set_idx][Cache.ways-1])#line_least_used -> list最後面最少被使用到的
    ori_addr=comAddr(Cache,copy_line_least_used.tag,set_idx,offset)#重新算addr
    return copy_line_least_used,ori_addr
###address
def checkBackInvalid(Cache,addr):
    """ checkBackInvalid func 檢查被L2 cache evict掉的有沒有在L1裡面\n
        如果存在的話\n
        (1)檢查dirty如果是True就要寫回memory L1的資訊\n
            但如果是False就直接evict\n
        (2)valid bit 設為false\n
        return copy_line_hit 如果copy_line_hit!=None表示被L2 evict掉的cacheline存在L1cache 中
    """
    #print(Cache)
    ###檢查被L2 cache evict掉的有沒有在L1裡面
    tag,set_idx,offset=splitAddr(Cache,addr)
    line_hit_idx=get_line_hit_idx(Cache,addr)#L1 cache hit
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
        Cache.cache_table[set_idx][line_hit_idx].valid=False
    else:#不在L1裡面
        pass
    return copy_line_hit
def splitAddr(Cache,addr):
    """ splitAddr func split address\n
        param Cache give setting of cache\n
        param addr address\n
        return tag,set index,offset
    """
    offset_len = 6
    set_idx = int(addr[Cache.addrBits-int(math.log(Cache.sets,2))-offset_len:Cache.addrBits-offset_len],2)#int(addr[11:26],2)
    tag = addr[:Cache.addrBits-int(math.log(Cache.sets,2))-offset_len]#addr[0:11]
    offset =addr[-offset_len:]
    return tag,set_idx,offset
def comAddr(Cache,tag,set_idx,offset):
    """ ComAddr func recombine address\n
        param tag tag\n
        param set_idx set index\n
        param offset data offset\n
        return addr address
    """
    set_idx=bin(set_idx)[2:].zfill(int(math.log(Cache.sets,2)))
    addr = tag + set_idx + offset
    return addr
def TSTMdecode(data):
    decode_data=tstm.TSTM_Decoding(data)
    return decode_data
if __name__ == '__main__': 
    tstm=mytstm.TSTM()
    tstm_table=tstm.table
    print(tstm_table.loc['111111','0000'])