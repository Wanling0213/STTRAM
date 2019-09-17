import json
def read_ini(filename):
    with open(filename,'r')as inifile:
        data=inifile.read()
    obj=json.loads(data)
    return obj

    
# obj=read_ini('init.json')
# for i in obj.keys():
#     for j in obj[i]:
#         print(obj[i].value)
#     print("---")
# addrBits=(obj["L1Cache"]["addrBits"])
# print(addrBits)
# class A():
#     def method1(self):
#         print('A.method1')
        
#     def method2(self):
#         print('A.method2')
        
# class B(A):
#     def method3(self):
#         print('B.method3')

# test=B()
# test.method1()
class counter:
    def __init__(self):
        self.wr_cnt=0
        self.wr_cnt=0
        self.wr_cnt=0


# import os
# path=os.path.join(os.getcwd() ,"trace")
# files= os.listdir(path) 
# print(files)
# for i in range(2):
#     print('Hello', 'World', 2+3, file=open('file.txt', 'a+'))
#     print('Hello', 'World', 2+3, file=open('file.txt', 'a+'))
#     print('Hello', 'World', 2+3, file=open('file.txt', 'a+'))
def fun(a):
    if(a==0):
        print (98)
        return 'ok'#执行到该return语句时，函数终止，后边的语句不再执行
    if(a==1):
        print (98)
        return 'ok'#执行到该return语句时，函数终止，后边的语句不再执行
    if(a==2):
        print (98)
        return 'ok'#执行到该return语句时，函数终止，后边的语句不再执行
    if(a==3):
        print ("hi")
        return 'ok'#执行到该return语句时，函数终止，后边的语句不再执行
fun(3)
