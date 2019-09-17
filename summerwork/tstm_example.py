from .. import config
from .. import eva

class TSTM:

    Config = None
    Eva = None
    num_segment = 0
    num_cell = 384
    table = None
    coding_table =  [['000'],
                     ['001', '010', '100'],
                     ['110', '101', '011'],
                     ['111']]
    state_table = None

    def __init__(self, config, eva):
        self.Config = config
        self.Eva = eva
        self.Eva.cl_bit = int(config.l2_cahce_line_size * 1.5)
        self.num_segment = int(config.l2_cahce_line_size / 4)
        self.table = self.set_decision_table()

    def encode(self, original_data, w_data):
        o = format(original_data, '0768b')
        w = format(w_data, '0512b')
        coded_data = ''
        for num in range(self.num_segment):
            original = int(o[num*6 : num*6+6], 2)
            target = int(w[num*4 : num*4+4], 2)
            coded_data += self.table[original][target]
            self.Eva.write(self.state_table[original][target])
        w_data = int(coded_data, 2)
        return w_data

    def decode(self, r_data):
        r = format(r_data, '0768b')
        data = ''
        for num in range(self.num_segment * 2):
            segment = r[num*3 : num*3+3]
            sum = 0
            for char in segment:
                sum += int(char)
            data += format(sum, '02b')
        r_data = int(data, 2)
        self.Eva.read(self.num_cell)
        return r_data

    def __combine(self, target):
        candidate = []
        first = int(target[0:2], 2)
        second = int(target[2:4], 2)
        for n in range(len(self.coding_table[first])):
            for m in range(len(self.coding_table[second])):
                candidate.append(self.coding_table[first][n] + self.coding_table[second][m])
        return candidate

    def __count(self, original, candidate):
        candidate_state = []
        for num in range(len(candidate)):
            zt = 0
            st = 0
            ht = 0
            tt = 0
            for cell in range(3):
                bit = cell * 2
                if original[bit : bit+2] == candidate[num][bit : bit+2]:                                #ZT
                    zt += 1
                elif original[bit] == candidate[num][bit] and original[bit+1] != candidate[num][bit+1]: #ST
                    st += 1
                elif candidate[num][bit] == candidate[num][bit+1]:                                      #HT
                    ht += 1
                else:                                                                                   #TT
                    tt += 1
            candidate_state.append([zt, st, ht, tt])
        return candidate_state

    def __select(self, candidate):
        best = None
        state = None
        for num in range(len(candidate)):
            if state is None:
                best = num
                state = candidate[num]
            else:
                for n in range(3, -1, -1):      # TT < HT < ST < ZT
                    if candidate[num][n] > state[n]:
                        break
                    elif candidate[num][n] < state[n]:
                        best = num
                        state = candidate[num]
                        break
        return best

    def set_decision_table(self):
        table = [[0 for t in range(16)] for o in range(64)]
        self.state_table = [[[] for t in range(16)] for o in range(64)]
        for o in range(64):
            for t in range(16):
                original = format(o, '06b')
                target = format(t, '04b')
                candidate = self.__combine(target)
                candidate_state = self.__count(original, candidate)
                best = self.__select(candidate_state)
                table[o][t] = candidate[best]
                self.state_table[o][t] = candidate_state[best]
        return table
