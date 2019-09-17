import pandas as pd
import os 
import json
import xlwt
fpath="output"
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
            files.append(f)
    return files
file_list=get_tracepath(fpath)
energy_list_slc=list()
energy_list_cmlc=list()
energy_list_tstm=list()
lat_list_slc=list()
lat_list_cmlc=list()
lat_list_tstm=list()
wearing_list_slc=list()
wearing_list_cmlc_H=list()
wearing_list_cmlc_S=list()
wearing_list_tstm_H=list()
wearing_list_tstm_S=list()
def read_json(filename):
    """ read_ini func 讀進trace並處理\n
        return obj
    """
    with open(filename,'r')as inifile:
        data=inifile.read()
    obj=json.loads(data)
    energy_list_slc.append(obj["SLC"][0])
    lat_list_slc.append(obj["SLC"][1])
    wearing_list_slc.append(obj["SLC"][2])  
    energy_list_cmlc.append(obj["CMLC"][0])
    lat_list_cmlc.append(obj["CMLC"][1])
    wearing_list_cmlc_H.append(obj["CMLC"][2])
    wearing_list_cmlc_S.append(obj["CMLC"][3])
    energy_list_tstm.append(obj["TSTM"][0])
    lat_list_tstm.append(obj["TSTM"][1])
    wearing_list_tstm_H.append(obj["TSTM"][2])
    wearing_list_tstm_S.append(obj["TSTM"][3])
for f in file_list:
    read_json(os.path.join("output",f))
    

energy_dict = {
    "SLC": energy_list_slc,
    "CMLC": energy_list_cmlc,
    "TSTM": energy_list_tstm
}
lat_dict={
    "SLC": lat_list_slc,
    "CMLC": lat_list_cmlc,
    "TSTM": lat_list_tstm
}
wearing_dict={
    "SLC": wearing_list_slc,
    "CMLC_soft": wearing_list_cmlc_S,
    "TSTM_soft": wearing_list_tstm_S,
    "CMLC_hard": wearing_list_cmlc_H,
    "TSTM_hard": wearing_list_tstm_H
}
energy_df = pd.DataFrame(energy_dict,columns = ["SLC", "CMLC","TSTM"],index=file_list)
lat_df=pd.DataFrame(lat_dict,columns = ["SLC", "CMLC","TSTM"],index=file_list)
wearing_df=pd.DataFrame(wearing_dict,columns = ["SLC", "CMLC_soft","TSTM_soft","CMLC_hard","TSTM_hard"],index=file_list)
# print(energy_df)

writer = pd.ExcelWriter('result_0831.xlsx')
energy_df.to_excel(writer,'energy')
lat_df.to_excel(writer,'latency')
wearing_df.to_excel(writer,'wearing times')
writer.save()