import json
from enum import Enum

INPUT_MAP = 0
OUTPUT_MAP = 1


class Operation(Enum):
    CMP = 0
    ADD = 1
    MUL = 2
    MOD = 3


class Opcode(Enum):
    # принцип "куда что"
    HLT = "hlt"  # стоп программы
    JMP = "jmp"  # [v] перейти к метке
    JZ = "jz"  # [v] перейти к метке если стоит флаг zero
    JZ_R = "jz_r"  # [v] [r] перейти к метке если в регистре 0

    MOV = "mov"  # [r] [v] записать в регистр значение
    LOAD_V = "load_v"  # [r] [v] считать значение в регистр из памяти по адресу-значению
    LOAD_R = "load_r"  # [r] [r] считать значение в регистр из памяти по адресу-регистру
    STORE_V = "store_v"  # [v] [r] сохранить в память по адресу-значению из регистра
    STORE_R = "store_r"  # [r] [r] сохранить в память по адресу-регистру из регистра
    NEXT = "next"  # [r] [r] загрузить в регистр из памяти по адресу-регистру+1 (инкрементировав регистр)

    CMP = "cmp"  # [r] [v] сравнить регистр со значением, установить zero если true
    INC = "inc"  # [r] увеличить регистр на 1
    ADD_MMR = "add_mmr"  # [v] [v] [r] сохранить в адрес-значение сумму из-адрес-значения и регистра
    MOD_RRV = "mod_rrv"  # [r] [r] [v] записать в регистр результат нахождения остатка от деления значения в регистре на значение

    LINEAR = "linear"  # [r] [v] [r] в регистр записывается произведение значения на значение в регистре + последующие LINEAR_CONT
    LINEAR_CONT = (
        "linear_cont"  # [r] [v] [r] произведение значения на значение в регистре
    )

    # INPUT = "input_r"  # [r] заменяется на LOAD_V
    # OUTPUT = "output_r"  # [r] заменяется на STORE_V

    NUMBER = "number"  # число в памяти
    STRING = "string"  # нул-терминированная строка
    BUFFER = "buffer"  # буфер для записи


class MachineCode:
    def __init__(self, index: int, opcode: Opcode, args: list = None):
        self.index = index
        self.opcode = opcode
        self.args = args if args else []

    def to_dict(self):
        return {
            "index": self.index,
            "opcode": self.opcode.value,
            "args": self.args,
        }

    def __repr__(self):
        return str(self.to_dict())


def write_code(filename: str, code: list):
    with open(filename, "w") as file:
        buf = []
        for instr in code:
            val = instr if isinstance(instr, int) else instr.to_dict()
            buf.append(json.dumps(val))
        file.write("[" + ",\n ".join(buf) + "]")


def read_code(filename: str):
    with open(filename) as f:
        js = json.load(f)
        data_len = js.pop(0)
        data = js[:data_len]
        code = js[data_len:]
        for ind, instr in enumerate(data):
            index = instr["index"]
            opcode = Opcode(instr["opcode"])
            args = instr["args"]
            data[ind] = MachineCode(index, opcode, args)

        for ind, instr in enumerate(code):
            index = instr["index"]
            opcode = Opcode(instr["opcode"])
            args = instr["args"]
            code[ind] = MachineCode(index, opcode, args)
        return data, code
