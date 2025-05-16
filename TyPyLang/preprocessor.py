import re

def preprocess_source(source):
    """Teisendab TyPy laiendatud süntaksi tavalise Python-koodiks."""


    source = re.sub(r'''(?mx)^([ \t]*)([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*(?<![+\-*/=!<>])=(?![=+\-*/])\s*(.+)$''',
        lambda m: f"{m.group(1)}{m.group(3)}: {m.group(2)} = {m.group(4)}",
        source
    )

    source = re.sub(
        r'(\b[A-Za-z_]\w*)\s*:\s*auto\b',
        r'\1: object',
        source
    )

    
    
    readonly_names = re.findall(
            r'^[ \t]*readonly[ \t]+([A-Za-z_]\w*)[ \t]*:', 
            source, 
            flags=re.MULTILINE
        )

    """Töötle koodi direktiiviga 'use strict''"""
    strict_present = bool(re.search(r'^(?!\s*#)\s*use strict\s*$', source, flags=re.MULTILINE))
    
    """
    Kui leitakse "use strict", lisame muutuja __strict_mode__
    """
    source = re.sub(r'^(?!\s*#)\s*use strict\s*$', '', source, flags=re.MULTILINE)
    if strict_present:
        lines = source.splitlines()
        for idx, line in enumerate(lines, start=1):
            if not line.strip() or line.lstrip().startswith('#') \
            or re.match(r'^\s*(class |import |from )', line) \
            or line.lstrip().startswith('readonly ') \
            or re.match(r'^\s*(private|protected|public)\b', line):
                continue

            m = re.match(r'^\s*def\s+(\w+)\s*\((.*)\)\s*(?:->\s*([^:]+))?:', line)
            if m:
                func_name, args_part, ret_part = m.group(1), m.group(2), m.group(3)
                for arg in [a.strip() for a in args_part.split(',') if a.strip()]:
                    name, _, _ = arg.partition(':')
                    name = name.strip()
                    if name in ('self', 'cls'):
                        continue
                    if ':' not in arg:
                        raise SyntaxError(
                            f"Strict mode: argument '{name}' of funtion '{func_name}' "
                            f"(line {idx}) must have annotation"
                        )
                if ret_part is None:
                    raise SyntaxError(
                        f"Strict mode: function '{func_name}' (line {idx}) "
                        f"must have anotation of returned data type"
                    )
                continue

            if re.search(r'==|!=|<=|>=|\+=|-=|\*=|/=', line):
                continue
            if re.match(r'^\s*(if|elif|while|for|assert)\b', line):
                continue

            if re.match(r'^\s*[A-Za-z_]\w*\s*=\s*TypeVar\(', line):
                continue

            if re.match(r'^\s*[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\s*:\s*[^=\s]+\s*=', line):
                continue
            if '=' in line:
                raise SyntaxError(
                    f"Strict mode: all assignments must have a type annotation "
                    f"(line {idx}): {line.strip()}"
                )

    source = "__strict_mode__ = True\n" + source

    """
    Eemaldame "use strict" direktiivi lähtekoodist
    """
    source = re.sub(r'^(?!\s*#)\s*use strict\s*$', '', source, flags=re.MULTILINE)


    if ' as ' in source and 'cast(' not in source:
        source = "from typing import cast\n" + source

        source = re.sub(
            r'^(?P<indent>\s*)return\s+(?P<expr>.+?)\s+as\s+(?P<type>[A-Za-z_]\w*)\b',
            lambda m: f"{m.group('indent')}return cast({m.group('type')}, {m.group('expr')})",
            source,
            flags=re.MULTILINE
        )

        source = re.sub(
            r'(?P<expr>\S(?:.*?\S)?)\s+as\s+(?P<type>[A-Za-z_]\w*)\b',
            lambda m: f"cast({m.group('type')}, {m.group('expr')})",
            source
        )

    """
    Kontrollime iga kohandatud elemendi struktuuri korrektsust
    """
    if re.search(r"interface\s+\w+\s+def", source):
        raise SyntaxError("Invalid interface declaration syntax")

    if re.search(r"enum\s+\w+\s+\w+", source):
        raise SyntaxError("Invalid enum declaration syntax")
    """
    Eemaldame funktsiooni definitsioonidest generikumite parameetrid
    """
    source = re.sub(r'^(?!\s*#)(def\s+\w+)<[^>]+>\s*\(', lambda m: m.group(1) + "(", source, flags=re.MULTILINE)
    source = re.sub(r'<[^>]+>', '', source)
    source = re.sub(r':\s*[A-Z]\b', ': object', source)

    """
    Tüüpialiaside töötlus: teisendame "type Alias = SomeType"
    """
    source = re.sub(r'^(?!\s*#)\s*type\s+(\w+)\s*=\s*(.+)$', r'\1 = \2', source, flags=re.MULTILINE)

    """
    Valikuliste parameetrite töötlus: "variable?: Type" → "variable: Optional[Type] = None"
    """
    source = re.sub(
        r'^(?!\s*#)(\s*)(\w+)\?\s*:\s*([^\s=]+)',
        r'\1\2: Optional[\3] = None',
        source,
        flags=re.MULTILINE
    )

    """
    Teisendame kirjutuskaitstud muutujad: "readonly x: int = expr" → "x: int = __readonly_check__(...)"
    """

    source = re.sub(
        r'^[ \t]*readonly[ \t]+(\w+)[ \t]*:[ \t]*([^=\n]+?)'
        r'(?:=[ \t]*([^\n#]+))?(?:#.*)?$',
        lambda m: (
            f"{m.group(1)}: {m.group(2).strip()} = "
            f"__readonly_check__('{m.group(1)}', {m.group(3).strip() if m.group(3) else 'None'}, {m.group(2).strip()})"
        ),
        source,
        flags=re.MULTILINE
    )

    """    
    Juurdepääsupiirangute töötlus (private, protected, public)
    """
    source = re.sub(r'^(?!\s*#)(\s*)private\s+(\w+)', lambda m: f"{m.group(1)}__{m.group(2)}", source, flags=re.MULTILINE)
    source = re.sub(r'^(?!\s*#)(\s*)protected\s+(\w+)', lambda m: f"{m.group(1)}_{m.group(2)}", source, flags=re.MULTILINE)
    source = re.sub(r'^(?!\s*#)(\s*)public\s+(\w+)', lambda m: f"{m.group(1)}{m.group(2)}", source, flags=re.MULTILINE)

    """
    Liideste töötlus: asendame "interface Name:" klassi definitsiooniga märgiga __is_interface__
    """
    def interface_repl(match):
        name = match.group(1)
        extends_part = match.group(2)
        if extends_part:
            bases = ','.join(base.strip() for base in extends_part.split(','))
            return f"class {name}({bases}):\n    __is_interface__ = True\n"
        else:
            return f"class {name}:\n    __is_interface__ = True\n"
    source = re.sub(r'^\s*interface\s+(\w+)(?:\s+extends\s+([\w\s,]+))?:\s*', interface_repl, source, flags=re.MULTILINE)

    source = re.sub(
        r'^(\s*)(?!@access_controlled)(class\s+\w+(?!.*__is_interface__)(?:\([^)]*\))?:)',
        lambda m: f"{m.group(1)}@access_controlled\n{m.group(1)}{m.group(2)}",
        source, flags=re.MULTILINE
    )
    
    """
    # Enumi töötlus: "enum Name: ..." → "class Name(Enum): ..."
    """
    def enum_repl(match):
        enum_name = match.group(1)
        body = match.group(2)
        
        # split all body to independents strigns
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        enum_lines = []
        value = 0  # try to index all Enums
        
        for line in lines:
            # check, is string contains commas for linear declaration
            if ',' in line:
                # use split with strip to remove spaces
                elements = [elem.strip() for elem in line.split(',') if elem.strip()]
                for elem in elements:
                    if '=' in elem:
                        # process explicit value
                        name_part, val_part = elem.split('=', 1)
                        name_part = name_part.strip()
                        val_part = val_part.strip()
                        enum_lines.append(f"    {name_part} = {val_part}")
                        # update value for erach next elements
                        try:
                            value = int(val_part) + 1
                        except ValueError:
                            # if value is not int, continue with current value
                            value += 1
                    else:
                        # autho increment value bu queue
                        enum_lines.append(f"    {elem} = {value}")
                        value += 1
            else:
                if '=' in line:
                    name_part, val_part = line.split('=', 1)
                    name_part = name_part.strip()
                    val_part = val_part.strip()
                    enum_lines.append(f"    {name_part} = {val_part}")
                    try:
                        value = int(val_part) + 1
                    except ValueError:
                        value += 1
                else:
                    enum_lines.append(f"    {line} = {value}")
                    value += 1
        
        enum_body = "\n".join(enum_lines)

        enum_body += "\n    def __str__(self):\n        return str(self.value)"
        enum_body += "\n    __repr__ = __str__"
        return f"from enum import Enum\nclass {enum_name}(Enum):\n{enum_body}\n"

    source = re.sub(r'^\s*enum\s+(\w+):\s*\n((?:\s+.+\n*)+)', enum_repl, source, flags=re.MULTILINE)

    """
    "Implements" töötlus: lisame dekorraatorid @implements(...)
    """
    def implements_repl(match):
        indent = match.group(1)
        class_name = match.group(2)
        inheritance = match.group(3) if match.group(3) else ""
        interfaces = match.group(4)
        interfaces_list = [iface.strip() for iface in interfaces.split(',')]
        decorators = "".join([f"{indent}@implements({iface})\n" for iface in interfaces_list])
        return f"{decorators}{indent}class {class_name}{inheritance}:"
    
    source = re.sub(
        r'^(?!\s*#)(\s*)class\s+(\w+)(\s*\([^)]*\))?\s+implements\s+([\w\s,]+)\s*:',
        implements_repl,
        source, flags=re.MULTILINE
    )

    """
    Tüübiassertsiooni töötlus: "expr as Type" → "__assert_type__(expr, Type)"
    """
    source = re.sub(
        r'(?<!#)([^\s=][^#\n]*)\s+as\s+([A-Za-z_]\w*)\b',
        r'cast(\2, \1)',
        source
    )

    """
    Liideste meetodite definitsioonide korrektsuse kontroll
    """
    source = check_interface_methods(source)
    
    # fixing tabulations
    source = fix_interface_body(source)

    for name in readonly_names:
        pattern = rf'^(?!\s*#)(?!\s*readonly\s+){name}\s*[:=]'
        matches = list(re.finditer(pattern, source, flags=re.MULTILINE))
        if len(matches) > 1:
            second = matches[1]
            lineno = source.count('\n', 0, second.start()) + 1
            raise SyntaxError(
                f"Attempt to override a readonly variable '{name}' "
                f"in line {lineno}"
            )

    
    return source

def check_interface_methods(source):
    # controll if methods in interface have body
    lines = source.splitlines()
    for i, line in enumerate(lines):
        # find class decloration with __is_interface__
        m = re.match(r'^(?!\s*#)\s*class\s+(\w+)(?:\s*\([^)]*\))?:\s*$', line)
        if m:
            interface_name = m.group(1)
            # If we find a method without body in the next lines until the end of the block - error.
            j = i + 1
            while j < len(lines):
                current_line = lines[j]
                if not current_line.startswith("    "):
                    break
                # If line defines a method
                method_match = re.match(r'^\s*def\s+(\w+)\(.*\):\s*$', current_line)
                if method_match:
                    method_indent = len(re.match(r'^(\s*)', current_line).group(1))
                    # If the next line is empty or has an indent not greater than the method header, we consider that the method body is missing
                    if j + 1 >= len(lines) or (lines[j+1].strip() == '' or len(re.match(r'^(\s*)', lines[j+1]).group(1)) <= method_indent):
                        raise SyntaxError(f"Interface {interface_name}: method {method_match.group(1)} haven't body. Check spaces (example, add 'pass').")
                j += 1
    return "\n".join(lines)

def fix_interface_body(source):
    """
    Funktsioon korrigeerib liideseploki taaneteid
    """
    lines = source.splitlines()
    new_lines = []
    in_interface = False
    for i, line in enumerate(lines):
        if re.match(r'^\s*class\s+\w+(?:\s*\([^)]*\))?:\s*$', line):
            new_lines.append(line)
            in_interface = False
        elif "__is_interface__" in line:
            new_lines.append(line)
            in_interface = True
        elif in_interface:
            if line.strip() != "":
                new_lines.append("    " + line.lstrip())
            else:
                new_lines.append(line)
            if i+1 < len(lines) and not lines[i+1].startswith("    "):
                in_interface = False
        else:
            new_lines.append(line)
    return "\n".join(new_lines)

def preprocess_generic_functions(source: str) -> str:
    """
    Geneeriliste funktsioonide töötlus: def identity<T>(v: T) -> T → teisendame Pythoni TypeVar-kujule."
    """
    pattern = r"def\s+(\w+)<([\w,\s]+)>\s*\("
    
    typevar_set = set()
    new_source_lines = []
    last_pos = 0

    for match in re.finditer(pattern, source):
        start, end = match.span()
        func_name = match.group(1)
        type_vars = match.group(2).replace(' ', '').split(',')

        typevar_set.update(type_vars)

        # use substrings to build new source code
        new_source_lines.append(source[last_pos:start])
        # corretion of function definition without generics
        new_source_lines.append(f"def {func_name}(")
        last_pos = end

    # the second part of the source code
    new_source_lines.append(source[last_pos:])

    new_source = ''.join(new_source_lines)

    # if founds generics - insert them to the top of the file
    if typevar_set:
        insert_block = "from typing import TypeVar\n" + "".join(
            f"{name} = TypeVar('{name}')\n" for name in sorted(typevar_set)
        ) + "\n\n"
        new_source = insert_block + new_source

    return new_source
