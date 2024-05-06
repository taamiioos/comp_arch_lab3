import json
from enum import Enum

class Opcode(Enum):
    LOAD = 'load'
    MOV = 'mov'
    CMP_RN = 'sub'
    MOD = 'mod'
    ADD = 'add'
    INC = 'inc'
    DEC = 'dec'
    JMP = 'jmp'
    JZ = 'jz'
    HLT = 'hlt'
    NUMBER = "number"
    STRING = "string"
    BUFFER = "buffer"



class MachineCode:
    def __init__(self, index, opcode, args=None, arg_type=None):
        self.index = index
        self.opcode = opcode.value if isinstance(opcode, Opcode) else opcode
        self.args = args if args else []
        self.arg_type = arg_type

    def to_dict(self):
        return {
            "index": self.index,
            "opcode": self.opcode,
            "args": self.args,
            "arg_type": self.arg_type
        }



def write_code(filename, code):
    with open(filename, "w") as f:
        json.dump([instr for instr in code], f, indent=4)



def read_code(filename):
    with open(filename) as f:
        data = json.load(f)
        code = []
        for instr in data:
            opcode = Opcode[instr["opcode"]]
            args = instr["args"]
            code.append(MachineCode(instr["index"], opcode, args))
        return code
