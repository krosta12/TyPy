import re

def preprocess_source(source):
    # use strict создание переменной флага и удаления из кода как мусор
    if "use strict" in source:
        source = re.sub(r'^\s*use strict\s*$', '', source, flags=re.MULTILINE)
        source = "__strict_mode__ = True\n" + source

    # Удаение видимой типизации
    source = re.sub(r'(def\s+\w+)<[^>]+>\s*\(', lambda m: m.group(1) + "(", source)

    # удалекние типизации по инициализации
    source = re.sub(r'^\s*type\s+(\w+)\s*=\s*(.+)$', r'\1 = \2', source, flags=re.MULTILINE)

    # Обработка optional: переменная делает или null или underfined
    source = re.sub(r'(\w+)\?\s*:\s*([^\s=]+)', r'\1: Optional[\2]', source)

    # Обработка readonly-переменных: const 
    source = re.sub(
        r'^\s*readonly\s+(\w+)\s*:\s*([^=]+)=\s*(.+)$',
        lambda m: f"{m.group(1)}: {m.group(2)}= __readonly_check__(\"{m.group(1)}\", {m.group(3)}, {m.group(2).strip()})",
        source, flags=re.MULTILINE
    )

    # Видимые методы для будующей инкапсуляции
    # private: "__var"
    source = re.sub(r'^(\s*)private\s+(\w+)', lambda m: f"{m.group(1)}__{m.group(2)}", source, flags=re.MULTILINE)
    # protected: "_var"
    source = re.sub(r'^(\s*)protected\s+(\w+)', lambda m: f"{m.group(1)}_{m.group(2)}", source, flags=re.MULTILINE)
    # public: default
    source = re.sub(r'^(\s*)public\s+(\w+)', lambda m: f"{m.group(1)}{m.group(2)}", source, flags=re.MULTILINE)

    # Обработка интерфейсов: создание флага интерфейса
    def interface_repl(match):
        name = match.group(1)
        return f"class {name}:\n    __is_interface__ = True"
    source = re.sub(r'^interface\s+(\w+)\s*:', interface_repl, source, flags=re.MULTILINE)

    # Обработка implements: добавляем декораторы @implements для интерфеса 
    def implements_repl(match):
        indent = match.group(1)
        class_name = match.group(2)
        interfaces = match.group(3)
        interfaces_list = [iface.strip() for iface in interfaces.split(',')]
        decorators = "".join([f"{indent}@implements({iface})\n" for iface in interfaces_list])
        return f"{decorators}{indent}class {class_name}:"
    source = re.sub(r'^(\s*)class\s+(\w+)\s+implements\s+([\w\s,]+)\s*:', implements_repl, source, flags=re.MULTILINE)

    # Enum: преобразование в класс
    def enum_repl(match):
        enum_name = match.group(1)
        body = match.group(2)
        lines = body.splitlines()
        enum_lines = []
        value = 1
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.endswith(','):
                line = line[:-1]
            enum_lines.append(f"    {line} = {value}")
            value += 1
        enum_body = "\n".join(enum_lines)
        return f"from enum import Enum\nclass {enum_name}(Enum):\n{enum_body}"
    source = re.sub(r'enum\s+(\w+)\s*:\s*(.*?)\n(?=\S)', enum_repl, source, flags=re.DOTALL)

    # изменение типа данных
    source = re.sub(r'(\S+)\s+as\s+(\w+)', r'__assert_type__(\1, \2)', source)
    
    return source
