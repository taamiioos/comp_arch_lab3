from processor.data_path import DataPath
from processor.isa import MachineCode, Opcode, Operation


class ControlUnit:
    program_memory: list = None
    program_counter: int = None

    data_path: DataPath = None

    _tick: int = None

    def __init__(self, program_memory: list, data_path: DataPath):
        self.program_memory = program_memory
        self.program_counter = 0
        self.data_path = data_path
        self._tick = 0

    def tick(self):
        self._tick += 1

    def current_tick(self):
        return self._tick

    def signal_latch_program_counter(self, sel_next: bool, val: int = None):
        if sel_next:
            self.program_counter += 1
        else:
            self.program_counter = val

    def decode_and_execute_control_flow_instruction(self, instr: MachineCode):
        opcode = instr.opcode
        if opcode is Opcode.HLT:
            raise StopIteration()

        if opcode is Opcode.JMP:
            addr = instr.args[0]
            self.signal_latch_program_counter(sel_next=False, val=addr)
            self.tick()
            return True

        if opcode is Opcode.JZ:
            addr = instr.args[0]
            if self.data_path.zero():
                self.signal_latch_program_counter(sel_next=False, val=addr)
            else:
                self.signal_latch_program_counter(sel_next=True)
            self.tick()
            return True

        if opcode is Opcode.JZ_R:
            addr = instr.args[0]
            reg = self.data_path.registers[instr.args[1]]
            self.data_path.alu(Operation.CMP, reg, 0)
            self.tick()
            if self.data_path.zero():
                self.signal_latch_program_counter(sel_next=False, val=addr)
            else:
                self.signal_latch_program_counter(sel_next=True)
            self.tick()
            return True
        return False

    def decode_and_execute_instruction(self):
        # print(self.program_memory)
        instr = self.program_memory[self.program_counter]
        opcode = instr.opcode

        if self.decode_and_execute_control_flow_instruction(instr):
            return

        elif opcode is Opcode.MOV:
            self.data_path.signal_latch_register(instr)

        elif opcode in [Opcode.LOAD_V, Opcode.LOAD_R]:
            self.data_path.signal_latch_data_address(instr)
            self.tick()
            self.data_path.signal_latch_register(instr)

        elif opcode in [Opcode.STORE_V, Opcode.STORE_R]:
            self.data_path.signal_latch_data_address(instr)
            self.tick()
            self.data_path.signal_wr(instr)

        elif opcode is Opcode.NEXT:
            self.data_path.signal_latch_register(instr, step=1)
            self.tick()
            self.data_path.signal_latch_data_address(instr)
            self.tick()
            self.data_path.signal_latch_register(instr, step=2)

        elif opcode is Opcode.CMP:
            self.data_path.alu(
                Operation.CMP, self.data_path.registers[instr.args[0]], instr.args[1]
            )

        elif opcode is Opcode.INC:
            self.data_path.signal_latch_register(instr)

        elif opcode is Opcode.ADD_MMR:
            self.data_path.signal_latch_data_address(instr, step=1)
            self.tick()
            self.data_path.signal_latch_buffer_register(instr)
            self.tick()
            self.data_path.signal_latch_data_address(instr, step=2)
            self.tick()
            self.data_path.signal_wr(instr)

        elif opcode is Opcode.MOD_RRV:
            self.data_path.signal_latch_buffer_register(instr)
            self.tick()
            self.data_path.signal_latch_register(instr)

        elif opcode is Opcode.LINEAR:
            self.data_path.signal_latch_buffer_register(instr)
            self.tick()
            self.data_path.signal_latch_register(instr)
        elif opcode is Opcode.LINEAR_CONT:
            self.data_path.signal_latch_buffer_register(instr, step=1)
            self.tick()
            self.data_path.signal_latch_buffer_register(instr, step=2)
            self.tick()
            self.data_path.signal_latch_register(instr)

        else:
            raise ValueError(f"Invalid opcode: {opcode}")

        self.signal_latch_program_counter(sel_next=True)
        self.tick()

    def __repr__(self):
        # print("======")
        # print(self.program_counter, self.program_memory)
        # print(self.data_path.data_address, self.data_path.data_memory)
        instr = self.program_memory[self.program_counter]
        opcode = instr.opcode

        state_repr = (
            f"TICK: {self._tick:4} "
            f"[{self.program_counter:2}: {opcode.name:7}] "
            f"PC: {self.program_counter:2} "
            f"DR: {self.data_path.data_address:2} "
            f"SB: {self.data_path.buffer_register:2} "
            f"RG: {self.data_path.registers} "
        )
        return state_repr
