import json
from enum import Enum

class Opcode(Enum):
    LOAD = 'loadmr'
    MOV = 'movnr'
    CMP = 'subrn'
    MOD = 'modrrn'
    ADD = 'addmr'
    INC = 'incr'
    JMP = 'jmp'
    JZ = 'jz'
    HLT = 'hlt'
    INPUT = 'loadmr'
    OUTPUT = 'loadrm'
    NUMBER = "number"
    STRING = "string"
    BUFFER = "buffer"


class MachineCode:
    def __init__(self, index, opcode, args=None):
        self.index = index
        self.opcode = opcode.value if isinstance(opcode, Opcode) else opcode
        self.args = args if args else []

    def to_dict(self):
        return {
            "index": self.index,
            "opcode": self.opcode,
            "args": self.args
        }



def write_code(filename, code):
    with open(filename, "w") as f:
        json.dump([instr.to_dict() for instr in code], f, indent=4)



def read_code(filename):
    with open(filename) as f:
        data = json.load(f)
        code = []
        for instr in data:
            opcode = Opcode[instr["opcode"]]
            args = instr["args"]
            code.append(MachineCode(instr["index"], opcode, args))
        return code
