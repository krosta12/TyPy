import re

def preprocess_source(source):
    # Если встречается директива "use strict", удаляем
    source = re.sub(r'^(?!\s*#)\s*use strict\s*$', '', source, flags=re.MULTILINE)
    if "use strict" in source:
        source = "__strict_mode__ = True\n" + source

    # Удаляем параметры обобщений в определениях функций
    source = re.sub(r'^(?!\s*#)(def\s+\w+)<[^>]+>\s*\(', lambda m: m.group(1) + "(", source, flags=re.MULTILINE)

    # Обработка type alias: преобразуем "type Alias = SomeType"
    source = re.sub(r'^(?!\s*#)\s*type\s+(\w+)\s*=\s*(.+)$', r'\1 = \2', source, flags=re.MULTILINE)

    # Обработка optional: заменяем "variable?: Type" на "variable: Optional[Type]"
    source = re.sub(r'^(?!\s*#)(\w+)\?\s*:\s*([^\s=]+)', r'\1: Optional[\2]', source, flags=re.MULTILINE)

    # Обработка readonly-переменных: "readonly x: int = expr" => "x: int = __readonly_check__(...)"
    source = re.sub(
        r'^(?!\s*#)\s*readonly\s+(\w+)\s*:\s*([^=]+)=\s*(.+)$',
        lambda m: f"{m.group(1)}: {m.group(2)}= __readonly_check__(\"{m.group(1)}\", {m.group(3)}, {m.group(2).strip()})",
        source, flags=re.MULTILINE
    )

    # Обработка модификаторов доступа (private, protected, public)
    source = re.sub(r'^(?!\s*#)(\s*)private\s+(\w+)', lambda m: f"{m.group(1)}__{m.group(2)}", source, flags=re.MULTILINE)
    source = re.sub(r'^(?!\s*#)(\s*)protected\s+(\w+)', lambda m: f"{m.group(1)}_{m.group(2)}", source, flags=re.MULTILINE)
    source = re.sub(r'^(?!\s*#)(\s*)public\s+(\w+)', lambda m: f"{m.group(1)}{m.group(2)}", source, flags=re.MULTILINE)

    # Обработка интерфейсов: заменяем "interface Name:" на определение класса с меткой __is_interface__
    def interface_repl(match):
        name = match.group(1)
        return f"class {name}:\n    __is_interface__ = True"
    source = re.sub(r'^(?!\s*#)interface\s+(\w+)\s*:', interface_repl, source, flags=re.MULTILINE)

    # Обработка implements: добавляем декораторы @implements(...)
    def implements_repl(match):
        indent = match.group(1)
        class_name = match.group(2)
        interfaces = match.group(3)
        interfaces_list = [iface.strip() for iface in interfaces.split(',')]
        decorators = "".join([f"{indent}@implements({iface})\n" for iface in interfaces_list])
        return f"{decorators}{indent}class {class_name}:"
    source = re.sub(r'^(?!\s*#)(\s*)class\s+(\w+)\s+implements\s+([\w\s,]+)\s*:', implements_repl, source, flags=re.MULTILINE)

    # Обработка перечислений (enum): преобразуем "enum Color:" в определение класса на базе Enum
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
    source = re.sub(r'^(?!\s*#)enum\s+(\w+)\s*:\s*(.*?)\n(?=\S)', enum_repl, source, flags=re.DOTALL | re.MULTILINE)

    # Обработка приведения типов (assertion): "expr as Type" => "__assert_type__(expr, Type)"
    source = re.sub(r'(?<!#)(\S+)\s+as\s+(\w+)', r'__assert_type__(\1, \2)', source)    
    return source
