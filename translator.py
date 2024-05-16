import argparse
from processor.isa import Opcode, MachineCode, write_code, INPUT_MAP, OUTPUT_MAP


# input и output замена на адрес 1 0


# удаление пробелов и комментариев из строки
def get_meaningful_token(line: str) -> str:
    return line.split(";", 1)[0].strip()


# перевод секции данных из ассемблерного кода в словарь переменных
def translate_data_part(lines: list):
    variables = {}
    data_tokens = [
        MachineCode(0, "NUMBER", [1234]),
        MachineCode(1, "NUMBER", [1234]),
    ]  # длина + input + output
    for line in lines:
        opcode, name, value = line.split(" ", 2)

        variables[name] = len(data_tokens)
        if opcode == "STRING":
            value = value.strip('"')
            for c in value:
                data_tokens.append(MachineCode(len(data_tokens), opcode, [ord(c)]))
            data_tokens.append(MachineCode(len(data_tokens), opcode, [0]))
        elif opcode == "BUFFER":
            for i in range(int(value)):
                data_tokens.append(MachineCode(len(data_tokens), opcode, [0]))
        elif opcode == "NUMBER":
            data_tokens.append(MachineCode(len(data_tokens), opcode, [0]))
        else:
            raise ValueError("No data opcode")
    data_tokens = [len(data_tokens)] + data_tokens
    return variables, data_tokens


# перевод инструкций в MachineCode
def translate_code_part(lines: list):
    tokens = []
    labels = {}

    registers = {"r1": 0, "r2": 1, "r3": 2, "r4": 3}

    for line in lines:
        if line.endswith(":"):
            line = line.strip(":")
            labels[line] = len(tokens)
            continue

        parts = line.split()
        opcode = parts[0].upper()
        args = parts[1:]

        for ind, arg in enumerate(args):
            if isinstance(arg, int):
                continue
            elif arg.isnumeric():
                args[ind] = int(arg)
            elif arg in registers:
                args[ind] = registers[arg]

        if opcode == "INPUT":
            opcode = "LOAD_V"
            args.append(INPUT_MAP)
        elif opcode == "OUTPUT":
            opcode = "STORE_V"
            args.insert(0, OUTPUT_MAP)
        elif opcode == "LINEAR":  # multiple machine words
            first_arg = args[0]
            assert len(args) % 2 == 1 and len(args) >= 3, "Incorrect args amount"
            tokens.append(MachineCode(len(tokens), "LINEAR", args[:3]))
            args = args[3:]
            while args:
                tokens.append(
                    MachineCode(len(tokens), "LINEAR_CONT", [first_arg] + args[:2])
                )
                args = args[2:]
            continue

        tokens.append(MachineCode(len(tokens), opcode, args))

    return labels, tokens


def translate_stage_1(code: str):
    lines = code.split("\n")

    tokens = []

    data_lines = []
    code_lines = []

    data_section = False
    code_section = False

    for line in lines:
        line = get_meaningful_token(line)
        if not line:
            continue
        if line.startswith(".data"):
            data_section = True
            code_section = False
            continue
        elif line.startswith(".code"):
            data_section = False
            code_section = True
            continue

        if data_section:
            data_lines.append(line)
        elif code_section:
            code_lines.append(line)
        else:
            raise ValueError("Incorrect section type!!")

    # Переводим часть данных
    variables, data_tokens = translate_data_part(data_lines)
    tokens.extend(data_tokens)

    # Переводим часть кода
    labels, code_tokens = translate_code_part(code_lines)

    # Объединяем токены
    tokens.extend(code_tokens)

    return labels, variables, tokens


# Генерация машинного кода.
def translate_stage_2(labels: dict, variables: dict, tokens: list):
    code = []
    for token in tokens:
        if isinstance(token, int):
            code.append(token)
            continue

        # token is MachineCode
        # преобразование в Opcode
        token.opcode = Opcode[token.opcode]
        args = token.args

        # обработка аргументов
        for ind, arg in enumerate(args):
            if isinstance(arg, int):
                continue
            if arg in labels:
                # замена метки на соответствующий индекс
                args[ind] = labels[arg]
            elif arg in variables:
                # обработка переменных
                args[ind] = variables[arg]
            else:
                raise ValueError(f"Incorrect argument!!: {args}: {arg}")
        token.args = args
        code.append(token)

    return code


# полная трансляция кода
def translate(code: str):
    labels, variables, code_tokens = translate_stage_1(code)
    code = translate_stage_2(labels, variables, code_tokens)
    return code


def main(source: str, target: str):
    with open(source, "r") as f:
        text = f.read()

    code = translate(text)
    write_code(target, code)
    print("LoC:", len(text.split("\n")), "Instr:", len(code))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Трансляция кода")
    parser.add_argument("source_file", help="Имя файла с кодом")
    parser.add_argument("target_file", help="Имя выходного файла")

    args = parser.parse_args()

    main(args.source_file, args.target_file)
