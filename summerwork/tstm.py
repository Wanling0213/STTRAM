import pandas as pd
import itertools
import xlwt

ZT=0
HT=3.192
ST=1.92
TT=HT+ST

class TSTM():
    def __init__(self):
        self.table=self.CreateDecisionTable()
    def getTransType_Energy(self,in_str,out_str ):
        """compare two string type (ST,TT,ZT,HT)
            para in_str original data 
            para out_str encoded data
        """
        type_list=[]#four types: HT ST ZT TT
        
        i_strlen=len(in_str)#input string length
        o_strlen=len(out_str)#output string length
        if ((i_strlen!=o_strlen or i_strlen%2!=0)): #check two string are even & have same length
            print("error Wrong string length!")
            return

        for i in range(0,i_strlen,2):
            if (in_str[i]==out_str[i]):
                if (in_str[i+1]==out_str[i+1]):
                    type_list.append(ZT)
                else:
                    type_list.append(ST)
            else:
                if (out_str[i]==out_str[i+1]):
                    type_list.append(HT)
                else:
                    type_list.append(TT)
        return type_list
    def getTransType(self,in_str,out_str ):
        """compare two string type (ST,TT,ZT,HT)
            para in_str original data 
            para out_str encoded data
        """
        type_list=[]#four types: HT ST ZT TT
        
        i_strlen=len(in_str)#input string length
        o_strlen=len(out_str)#output string length

        if ((i_strlen!=o_strlen or i_strlen%2!=0)): #check two string are even & have same length
            print("error Wrong string length!")
            return

        for i in range(0,i_strlen,2):
            if (in_str[i]==out_str[i]):
                if (in_str[i+1]==out_str[i+1]):
                    type_list.append("ZT")
                else:
                    type_list.append("ST")
            else:
                if (out_str[i]==out_str[i+1]):
                    type_list.append("HT")
                else:
                    type_list.append("TT")
        return type_list
    def TSTM_Encoding(self,data):
        encode_method={
        "00": ["000"],
        "01": ["001","010","100"],
        "10": ["110","101","011"],
        "11": ["111"]
        }
        tmpbuf=itertools.product(encode_method[data[0:2]], encode_method[data[2:]])
        encoded_list=list()
        for i in tmpbuf:
            #print(i)
            encoded_list.append(i[0]+i[1])
        return encoded_list
            
    def CreateDecisionTable(self):
        x = [bin(i)[2:].zfill(4) for i in range(pow(2,4))]#2**2
        #print(x)
        y = [bin(i)[2:].zfill(6) for i in range(pow(2,6))]#2**6
        #print(y)
        DecisionTable_list=list()
        for target in x:
            Tmp_list=list()
            encoded_list=self.TSTM_Encoding(target) #return encoded list
            for original in y:    
                minvalue=999
                minindex=-1
                TransType_list=list()
                for code in encoded_list:
                    #print(getTransType(original,_type))
                    TransType = self.getTransType_Energy(original,code)
                    TransType_list.append(TransType)
                    if ((not TT in TransType) and minvalue>sum(TransType)):
                        minvalue = sum(TransType)
                        minindex = encoded_list.index(code)
                
                #unavoidable TT happen
                if (minindex==-1 and minvalue==999):
                    #print("ori:",original)
                    #for i in encoded_list:
                        #print(i)
                    #print("this is result",encoded_list[TransType_list.index(min(TransType_list,key=sum))])
                    Tmp_list.append(encoded_list[TransType_list.index(min(TransType_list,key=sum))])
                else:
                    #print ("min energy:",encoded_list[minindex])
                    Tmp_list.append(encoded_list[minindex])

            DecisionTable_list.append(Tmp_list)  
        Dict=dict()
        # for key in x:
        #     Dict[key]= DecisionTable_list[x.index(key)]
        for index in range(len(x)):
            Dict[x[index]] = DecisionTable_list[index]     
        
        DecisionTable_df = pd.DataFrame(Dict,index=y)   
        
        #print(DecisionTable_df.loc['111111','0000'])
        #DecisionTable_df.to_excel("DecisionTable.xls")
        return DecisionTable_df
                        
    def TSTM_Decoding(self,data):
        seg_num=int(len(data)/6)
        decode_data=list()
        for i in range(seg_num):
            seg=data[6*i:6*i+6]
            datalist=[seg[:3],seg[3:]]          
            for i in datalist:
                if (i.count("1")==0):
                    decode_data.append("00")
                elif (i.count("1")==1):
                    decode_data.append("01")
                elif (i.count("1")==2):
                    decode_data.append("10")
                else:
                    decode_data.append("11")

        return "".join(decode_data)
        

# list_=TSTM_Encoding("1001")
# for i in list_: 
#     print(i,getTransType("000111",i))

#TSTM_Encoding("1001")
def hex2bin(hex_str,totalBits=0):
    return bin(int(hex_str,16))[2:].zfill(totalBits)
def read_trace(filename):
    with open(filename) as f:
        cmd_list = f.readlines()
        cmd_list = [x.split() for x in cmd_list] 
    bin_cmd_list=list() # convert hex to binary
    for cmd in cmd_list:
        if(cmd[0]in['WRITE','W','Write','w','write','READ','R','Read','r','read']):
            #write todo 
            addr=cmd[1]
            bin_addr=hex2bin(addr[2:],20)
            data= ''.join(cmd[2:])
            bin_data=hex2bin(data,512)
            bin_cmd=list()
            bin_cmd.append(cmd[0])
            bin_cmd.append(bin_addr)
            bin_cmd.append(bin_data)
            bin_cmd_list.append(bin_cmd)
        

    return bin_cmd_list 
if __name__ == '__main__':  
    tstm=TSTM()
    #DecisionTable_df=tstm.table
    a=tstm.TSTM_Decoding("001110111000")     #return 0011
    print(a)
    cmd_list=read_trace("trace/susan_V2.txt")     
    # for cmd in cmd_list:
    #     if cmd[0]in ['WRITE','W','Write','w','write']:
    #         addr,target_data=cmd[1:]
    #         original_data="1"*768
    #         ###練習處理data編碼512bits->768bits
    #         i_targetdata_bit=4
    #         i_originaldata_bit=int(i_targetdata_bit*1.5)
    #         encoded_data=""
    #         energy_list=list()
    #         for num in range(128):
    #             target=target_data[num*i_targetdata_bit:num*i_targetdata_bit+i_targetdata_bit]
    #             print("target " ,(target))
    #             original=original_data[num*i_originaldata_bit:num*i_originaldata_bit+i_originaldata_bit]
    #             print("origianl " ,(original))
    #             w_data=DecisionTable_df.loc[original,target]
    #             energy_list.append(tstm.getTransType(original,w_data))#回傳['TT','ST','ZT']
    #             encoded_data+=w_data
            ###
    #print(DecisionTable_df.loc['111111','0000'])

