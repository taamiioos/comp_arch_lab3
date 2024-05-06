import argparse
import re
from typing import Tuple, List, Dict
from processor.isa import Opcode, MachineCode, write_code


# удаление комментариев из строки
def get_meaningful_token(line: str) -> str:
    return line.split(";", 1)[0].strip()

# перевод секции данных из ассемблерного кода в словарь переменных
def translate_data_part(lines: List[str]) -> Tuple[Dict[str, List], List[Tuple]]:
    variables = {}
    data_tokens = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith(';'):
            continue
        # поиск совпадения с шаблоном регулярного выражения, которое соответствует объявлению переменной в секции данных.
        var_match = re.match(r'(\w+)\s+(STRING|BUFFER)\s+(.+)', line)
        if var_match:
            variable_name = var_match.group(1)  # извлекается имя
            var_type = var_match.group(2)  # извлекается тип
            value = var_match.group(3)  # извлекается значение
            if var_type == 'STRING':
                variables[variable_name] = [ord(c) for c in value if c != '"']
                variables[variable_name].append(0)
                data_tokens.append((variable_name, var_type, value))
            elif var_type == 'BUFFER':
                variables[variable_name] = [0] * int(value)
                data_tokens.append((variable_name, var_type, value))

    return variables, data_tokens


# перевод инструкций в MachineCode
def translate_code_part(lines: List[str]) -> List[MachineCode]:
    tokens = []

    for line in lines:
        line = line.strip()

        if not line or line.startswith(';'):
            continue

        parts = line.split()
        opcode = parts[0].upper()

        if opcode in [item.name for item in Opcode]:
            tokens.append(MachineCode(len(tokens), Opcode[opcode]))

            if len(parts) == 1:
                continue
            elif len(parts) == 2:
                arg = parts[1]
                if arg.isnumeric():
                    tokens[-1].args.append(int(arg))
                else:
                    tokens[-1].args.append(arg)
            elif len(parts) == 3:
                arg1, arg2 = parts[1], parts[2]
                if arg1.isnumeric():
                    tokens[-1].args.append(int(arg1))
                else:
                    tokens[-1].args.append(arg1)
                if arg2.isnumeric():
                    tokens[-1].args.append(int(arg2))
                else:
                    tokens[-1].args.append(arg2)
            elif len(parts) == 4:
                arg1, arg2, arg3 = parts[1], parts[2], parts[3]
                if arg1.isnumeric():
                    tokens[-1].args.append(int(arg1))
                else:
                    tokens[-1].args.append(arg1)
                if arg2.isnumeric():
                    tokens[-1].args.append(int(arg2))
                else:
                    tokens[-1].args.append(arg2)
                if arg3.isnumeric():
                    tokens[-1].args.append(int(arg3))
                else:
                    tokens[-1].args.append(arg3)
            else:
                raise ValueError(f"Instruction '{opcode}' has invalid number of arguments")

    return tokens


# Трансляция текста в последовательность операторов языка (токенов).
def translate_stage_1(code: str) -> Tuple[Dict[str, int], Dict[str, List], List]:
    lines = code.split('\n')

    labels = {}
    tokens = []

    data_lines = []
    code_lines = []

    data_section = False
    code_section = False

    for line in lines:
        if line.strip().startswith('.data'):
            data_section = True
            code_section = False
        elif line.strip().startswith('.code'):
            data_section = False
            code_section = True

        if data_section:
            data_lines.append(line)
        elif code_section:
            code_lines.append(line)

    # Переводим часть данных
    variables, data_tokens = translate_data_part(data_lines)
    tokens.extend(data_tokens)

    # Переводим часть кода
    code_tokens = translate_code_part(code_lines)

    # Обрабатываем метки
    for i, line in enumerate(code_lines):
        label_match = re.match(r'(\w+):', line)
        if label_match:
            label_name = label_match.group(1)
            labels[label_name] = len(tokens)
            continue

    # Объединяем токены
    tokens.extend(code_tokens)

    return labels, variables, tokens


# Генерация машинного кода.
def translate_stage_2(labels: Dict[str, int], variables: Dict[str, List], tokens: List) -> Tuple[List[int], List[str]]:
    code = []
    mnemonics = []

    for token in tokens:
        if isinstance(token, tuple):
            opcode, args = token
        else:
            # если токен является числом, добавление его в код
            code.append(token)
            mnemonics.append(str(token))
            continue

        # преобразование мнемоники в индекс
        opcode_index = list(Opcode).index(Opcode[opcode.upper()])
        code.append(opcode_index)
        mnemonics.append(opcode)

        # обработка аргументов
        for arg in args:
            if isinstance(arg, int) or arg.isnumeric():
                # обработка числовых аргументов
                code.append(int(arg))
                mnemonics.append(str(int(arg)))
                if arg in labels:
                    # замена метки на соответствующий индекс
                    code.append(labels[arg])
                    mnemonics.append(f"label:{arg}")

            elif arg in variables:
                # обработка переменных
                code.append(variables[arg][0])
                mnemonics.append(f"variable:{arg}")
            elif isinstance(arg, str) and arg.endswith(','):
                # remove the trailing comma and convert the argument to a register index
                arg = arg.rstrip(',')
                register_index = int(arg[1:])
                code.append(register_index)
                mnemonics.append(arg)
            else:
                # обработка регистров и других случаев
                code.append(arg)
                mnemonics.append(arg)

    return code, mnemonics




# полная трансляция кода
def translate(code: str) -> Tuple[List[int], List[str]]:
    labels, variables, code_tokens = translate_stage_1(code)
    code, mnemonics = translate_stage_2(labels, variables, code_tokens)
    return code, mnemonics


def main(source: str, target: str, target_mnem: str = None):
    with open(source, "r") as f:
        text = f.read()

    code, mnemonics = translate(text)

    if target_mnem is not None:
        with open(target_mnem, "w") as f:
            for line in mnemonics:
                f.write(line + "\n")

    write_code(target, code)
    print("Mnemonics:")
    for line in mnemonics:
        print(line)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Трансляция кода")
    parser.add_argument("source_file", help="Имя файла с кодом")
    parser.add_argument("target_file", help="Имя выходного файла")

    args = parser.parse_args()

    MNEMONIC_FILE = args.target_file + ".mnem"

    main(args.source_file, args.target_file, MNEMONIC_FILE)
