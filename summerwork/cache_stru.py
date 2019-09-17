
class cacheline():
    def __init__(self,valid,tag,dirty,data,trans):
        self.valid = valid
        self.tag = tag
        self.dirty = dirty
        self.data = data
        self.TransType_result=trans

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
        self.write_main_memory_cnt=0

        ###TSTM setting
        self.i_first_cell=[0,0,0,0]  # TT_cnt,ST_cnt,HT_cnt,ZT_cnt
        self.i_mid_cell=[0,0,0,0]  # TT_cnt,ST_cnt,HT_cnt,ZT_cnt
        self.i_last_cell=[0,0,0,0] # TT_cnt,ST_cnt,HT_cnt,ZT_cnt
        self.cell_status=[self.i_first_cell,self.i_mid_cell,self.i_last_cell]
        self.HT_cnt=0
        self.TT_cnt=0
        self.ZT_cnt=0
        self.ST_cnt=0

        
        #latency
        self.i_w_lat_cnt_per_CL=0
        self.i_w_lat_NonTT_cnt_per_CL=0
        self.i_w_lat_TT_cnt_per_CL=0
        self.i_TSTMencode_cnt_per_CL=0 #TSTM extra recorded
        self.i_r_lat_cnt_per_CL=0

        #energy
        self.i_w_energy_cnt_per_cell=0 #SLC
        self.i_r_energy_cnt_per_cell=0 #SLC&TSTM&CMLC

        self.i_w_times_cnt_per_cell=0 #SLC
        
        self.total_energy=0
        self.total_lat=0
        self.total_wearing_cnt=0
        self.total_wearing_hard_cnt=0#CMLC&TSTM
        self.total_wearing_soft_cnt=0#CMLC&TSTM