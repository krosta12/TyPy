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
        extends_part = match.group(2)
        if extends_part:
            bases = ','.join([base.strip() for base in extends_part.split(',')])
            return f"class {name}({bases}):\n    __is_interface__ = True"
        else:
            return f"class {name}:\n    __is_interface__ = True"
    source = re.sub(r'^(?!\s*#)interface\s+(\w+)(?:\s+extends\s+([\w\s,]+))?\s*:', interface_repl, source, flags=re.MULTILINE)

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

    # Обработка приведения типов (assertion): "expr as Type" -> "__assert_type__(expr, Type)"
    source = re.sub(r'(?<!#)(\S+)\s+as\s+(\w+)', r'__assert_type__(\1, \2)', source)
    
    # Проверка корректности определения методов в интерфейсах
    source = check_interface_methods(source)
    
    return source

def check_interface_methods(source):
    #проверка наличия тела методав  в интерфейсе
    lines = source.splitlines()
    for i, line in enumerate(lines):
        # Если строка определяет интерфейс
        m = re.match(r'^(?!\s*#)\s*class\s+(\w+)\s*(?:\([^)]*\))?:\s*$', line)
        if m:
            interface_name = m.group(1)
            j = i + 1
            while j < len(lines):
                current_line = lines[j]
                # Если пустая строка или строка с меньшим отступом — конец блока
                if not current_line.strip() or (current_line and not current_line.startswith("    ")):
                    break
                # Если строка определяет метод (начинается с def) и не содержит "pass" или не имеет хотя бы одной последующей строки с большим отступом
                method_match = re.match(r'^\s*def\s+(\w+)\(.*\):\s*$', current_line)
                if method_match:
                    method_indent = len(re.match(r'^(\s*)', current_line).group(1))
                    # Если следующая строка отсутствует или имеет отступ не больше, чем у заголовка метода, считаем, что тело метода отсутствует
                    if j + 1 >= len(lines) or (lines[j+1].strip() == '' or len(re.match(r'^(\s*)', lines[j+1]).group(1)) <= method_indent):
                        raise SyntaxError(f"Интерфейс {interface_name}: метод {method_match.group(1)} не имеет тела. Проверьте отступы (например, добавьте 'pass').")
                j += 1
    return "\n".join(lines)
