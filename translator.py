import argparse
import re
from typing import Tuple, List, Dict
from processor.isa import Opcode, MachineCode, write_code

# обработка скобок квадратных
# input и output замена на адрес 1 0

# удаление комментариев из строки (заменить)
def get_meaningful_token(line: str) -> str:
    return line.split(";", 1)[0].strip()

# перевод секции данных из ассемблерного кода в словарь переменных
def translate_data_part(lines: List[str]) -> Tuple[Dict[str, List[int]], List[int]]:
    variables = {}
    data_tokens = [0,0]
    for line in lines:
        line = get_meaningful_token(line)

        name, opcode, value = line.split(" ", 2)

        variables[name] = [len(data_tokens)]
        if opcode == 'STRING':
            data_tokens += [ord(c) for c in value]
            data_tokens.append(0)
        elif opcode == 'BUFFER':
            data_tokens += [0] * int(value)
        elif opcode == 'NUMBER':
            data_tokens.append(int(value))
        else:
            raise ValueError("No data opcode")

    data_tokens = [len(data_tokens)] + data_tokens

    return variables, data_tokens


# перевод инструкций в MachineCode
def translate_code_part(lines: List[str]) -> List[MachineCode]:
    tokens = []
    labels = {}

    for line in lines:
        line = get_meaningful_token(line)

        label_match = re.match(r'(\w+):', line)
        if label_match:
            label_name = label_match.group(1)
            labels[label_name] = len(tokens)
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

    return tokens, labels


def translate_stage_1(code: str) -> Tuple[Dict[str, int], Dict[str, List], List]:
    lines = code.split('\n')

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
    code_tokens, labels = translate_code_part(code_lines)

    # Объединяем токены
    tokens.extend(code_tokens)

    return labels, variables, tokens

def translate_stage_1(code: str) -> Tuple[Dict[str, int], Dict[str, List], List]:
    lines = code.split('\n')

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
    code_tokens, labels = translate_code_part(code_lines)

    # Объединяем токены
    tokens.extend(code_tokens)

    return labels, variables, tokens
# Генерация машинного кода.
def translate_stage_2(labels: Dict[str, int], variables: Dict[str, List], tokens: List) -> Tuple[List[int], List[str]]:
    data = []
    code = []
    print(variables)
    for token in tokens:
        print(token)
        if isinstance(token, int):
            data.append(token)


        else:
            # token is MachineCode
            # преобразование мнемоники в индекс
            # opcode_index = list(Opcode).index(Opcode[opcode.upper()])
            # code.append(opcode_index)
            print(token)
            command = token.to_dict()

            args = command["args"]
            new_args = []

            # обработка аргументов
            for arg in args:
                if isinstance(arg, int) or arg.isnumeric():
                    # обработка числовых аргументов
                    new_args.append(int(arg))
                    continue
                arg = arg.strip(',')


                if arg in labels:
                    # замена метки на соответствующий индекс
                    new_args.append(labels[arg])

                elif arg in variables:
                    # обработка переменных
                    new_args.append(variables[arg])
                elif isinstance(arg, str) and arg.startswith('r'):
                    # обработка регистров
                    new_args.append(int(arg[1:]))

                else:
                    # обработка других случаев
                    new_args.append(arg)
            command['args'] = new_args
            code.append(command)

    total_code = [data] + code

    return total_code



# полная трансляция кода
def translate(code: str) -> Tuple[List[int], List[str]]:
    labels, variables, code_tokens = translate_stage_1(code)
    code = translate_stage_2(labels, variables, code_tokens)
    return code


def main(source: str, target: str):
    with open(source, "r") as f:
        text = f.read()

    code = translate(text)
    write_code(target, code)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Трансляция кода")
    parser.add_argument("source_file", help="Имя файла с кодом")
    parser.add_argument("target_file", help="Имя выходного файла")

    args = parser.parse_args()


    main(args.source_file, args.target_file)
