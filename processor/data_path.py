import logging

from processor.isa import Opcode, MachineCode, Operation, OUTPUT_MAP, INPUT_MAP


class DataPath:
    data_memory: list = None

    data_address: int = None
    buffer_register: int = None
    registers: list = None

    is_zero: bool = None

    input_buffer: list = None
    output_buffer: list = None

    def __init__(self, data_memory: list, registers_amount: int, input_buffer: list):
        assert registers_amount > 0, "More registers!"
        self.data_memory = data_memory
        self.data_address = 0
        self.buffer_register = 0
        self.registers = [0] * registers_amount
        self.is_zero = False
        self.input_buffer = input_buffer
        self.output_buffer = []

    def signal_latch_data_address(self, instr: MachineCode, step: int = 1):
        opcode = instr.opcode
        if opcode is Opcode.LOAD_V:
            self.data_address = instr.args[1]
        elif opcode in [Opcode.LOAD_R, Opcode.NEXT]:
            self.data_address = self.registers[instr.args[1]]
        elif opcode is Opcode.STORE_V:
            self.data_address = instr.args[0]
        elif opcode is Opcode.STORE_R:
            self.data_address = self.registers[instr.args[0]]
        elif opcode is Opcode.ADD_MMR:
            if step == 1:
                self.data_address = instr.args[1]
            elif step == 2:
                self.data_address = instr.args[0]
            else:
                raise ValueError("Step must be 1 or 2!")
        else:
            raise ValueError(f"Wrong opcode: {opcode}")

    def signal_latch_buffer_register(self, instr: MachineCode, step: int = 1):
        opcode = instr.opcode
        if opcode is Opcode.ADD_MMR:
            self.buffer_register = self.data_memory[self.data_address].args[0]
        elif opcode is Opcode.MOD_RRV:
            self.buffer_register = instr.args[1]
        elif opcode is Opcode.LINEAR:
            self.buffer_register = instr.args[1]
        elif opcode is Opcode.LINEAR_CONT:
            if step == 1:
                self.buffer_register = instr.args[1]
            elif step == 2:
                self.buffer_register = self.alu(
                    Operation.MUL, self.buffer_register, self.registers[instr.args[2]]
                )
            else:
                raise ValueError("Step must be 1 or 2!")
        else:
            raise ValueError(f"Wrong opcode: {opcode}")

    def signal_latch_register(self, instr: MachineCode, step: int = 1):
        opcode = instr.opcode
        if opcode is Opcode.LOAD_V and instr.args[1] == INPUT_MAP:
            self.registers[instr.args[0]] = self._signal_input()
            return

        if opcode is Opcode.MOV:
            self.registers[instr.args[0]] = instr.args[1]
        elif opcode in [Opcode.LOAD_V, Opcode.LOAD_R]:
            self.registers[instr.args[0]] = self.data_memory[self.data_address].args[0]
        elif opcode is Opcode.NEXT:
            if step == 1:
                self.registers[instr.args[1]] = self.alu(
                    Operation.ADD, self.registers[instr.args[1]], 1
                )
            elif step == 2:
                self.registers[instr.args[0]] = self.data_memory[
                    self.data_address
                ].args[0]
            else:
                raise ValueError("Step must be 1 or 2!")
        elif opcode is Opcode.INC:
            self.registers[instr.args[0]] = self.alu(
                Operation.ADD, self.registers[instr.args[0]], 1
            )
        elif opcode is Opcode.MOD_RRV:
            self.registers[instr.args[0]] = self.alu(
                Operation.MOD, self.registers[instr.args[1]], instr.args[2]
            )
        elif opcode is Opcode.LINEAR:
            self.registers[instr.args[0]] = self.alu(
                Operation.MUL, self.buffer_register, self.registers[instr.args[2]]
            )
        elif opcode is Opcode.LINEAR_CONT:
            self.registers[instr.args[0]] = self.alu(
                Operation.ADD, self.buffer_register, self.registers[instr.args[0]]
            )
        else:
            raise ValueError(f"Wrong opcode {opcode}")

    def alu(self, operation: Operation, left: int, right: int):
        if operation is Operation.ADD:
            res = left + right
        elif operation is Operation.MUL:
            res = left * right
        elif operation is Operation.MOD:
            res = left % right
        elif operation is Operation.CMP:
            res = 0 if left == right else 1
        else:
            raise ValueError(f"Wrong operation: {operation}")

        if res == 0:
            self.is_zero = True
        elif res == 1:
            self.is_zero = False
        return res

    def signal_wr(self, instr: MachineCode):
        opcode = instr.opcode
        if opcode is Opcode.STORE_V and instr.args[0] == OUTPUT_MAP:
            self._signal_output(self.registers[instr.args[1]])
            return

        if opcode in [Opcode.STORE_V, Opcode.STORE_R]:
            self.data_memory[self.data_address].args[0] = self.registers[instr.args[1]]
        elif opcode is Opcode.ADD_MMR:
            self.data_memory[self.data_address].args[0] = self.alu(
                Operation.ADD, self.buffer_register, self.registers[instr.args[2]]
            )
        else:
            raise ValueError(f"Wrong opcode: {opcode}")

    def _signal_input(self):
        if len(self.input_buffer) == 0:
            raise EOFError("End of input file")
        str_symbol = self.input_buffer.pop(0)
        val = ord(str_symbol)
        if val == 0:
            str_symbol = ""
        logging.debug(f"input: {str_symbol}")
        return val

    def _signal_output(self, val):
        self.output_buffer.append(val)
        logging.debug(
            f"output: {''.join(map(lambda x: chr(x) if x < 256 else str(x), self.output_buffer))} << {val}"
        )

    def zero(self):
        return self.is_zero
