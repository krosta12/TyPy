import ast
from preprocessor import preprocess_source
from transformer import TyPyTransformer

def parse_source(source: str, filename: str = "<string>") -> ast.Module:
    """Получение обработанного кода, потдерждиваемого .py компиляторами"""
    processed_source = preprocess_source(source)
    try:
        """перевод кода в дерево AST"""
        tree = ast.parse(processed_source, filename=filename)
    except SyntaxError as e:
        """
        получить обработанный код по строкам
        """
        lines = processed_source.splitlines()
        err_line = e.lineno or 0
        """
        (2 строки до и 2 строки после) вернуть ошибку
        """
        start = max(0, err_line - 3)
        end = min(len(lines), err_line + 2)
        context = "\n".join(f"{i+1:4}: {lines[i]}" for i in range(start, end))
        """
        Поднимаем новую ошибку с дополнительной информацией
        """
        raise SyntaxError(
            f"Ошибка компиляции в обработанном коде (файл {filename}, строка {err_line}):\n{context}"
        ) from e
    check_return_statements(tree)
    transformer = TyPyTransformer()
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    return tree


#java expirement with visitor patern
def check_return_statements(tree):
    class ReturnVisitor(ast.NodeVisitor):
        def __init__(self):
            self._iface_stack = [False]
            super().__init__()

        def visit_ClassDef(self, node: ast.ClassDef):
            is_iface = any(
                isinstance(stmt, ast.Assign) and
                any(isinstance(t, ast.Name) and t.id == '__is_interface__'
                    for t in stmt.targets)
                for stmt in node.body
            )
            self._iface_stack.append(is_iface or self._iface_stack[-1])
            for stmt in node.body:
                self.visit(stmt)
            self._iface_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef):
            if self._iface_stack[-1]:
                return

            ann = node.returns
            is_none_annot = (
                ann is None
                or (isinstance(ann, ast.Constant) and ann.value is None)
                or (isinstance(ann, ast.Name)     and ann.id == 'None')
            )
            if is_none_annot:
                return self.generic_visit(node)

            found = any(
                isinstance(sub, ast.Return) and sub.value is not None
                for sub in ast.walk(node)
            )
            if not found:
                lineno = node.lineno
                name = node.name
                raise SyntaxError(
                    f"Функция '{name}' объявлена как возвращающая "
                    f"{ast.unparse(ann)}, но в её теле нет ни одного "
                    f"return с возвращаемым значением " 
                    f"(строка {lineno})."
                )
            self.generic_visit(node)

    ReturnVisitor().visit(tree)
