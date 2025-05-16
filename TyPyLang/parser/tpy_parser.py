import ast
from preprocessor import preprocess_source
from transformer import TyPyTransformer

def parse_source(source: str, filename: str = "<string>") -> ast.Module:
    """Töödeldud koodi genereerimine (.py kompilaatorile sobivaks)"""
    processed_source = preprocess_source(source)
    try:
        """Koodi teisendamine AST-puuks (abstraktseks süntaksipuuks)"""
        tree = ast.parse(processed_source, filename=filename)
    except SyntaxError as e:
        """
        Saada töödeldud kood ridade kaupa
        """
        lines = processed_source.splitlines()
        err_line = e.lineno or 0
        """
        Tagasta viga koos kontekstiga (2 rida enne ja 2 rida pärast)
        """
        start = max(0, err_line - 3)
        end = min(len(lines), err_line + 2)
        context = "\n".join(f"{i+1:4}: {lines[i]}" for i in range(start, end))
        """
        Tõsta uus viga lisainfoga (nt. "Vigane rida: {line}")
        """
        raise SyntaxError(
            f"Compilation error in processed code (file '{filename}', line {err_line}):\n{context}"
        ) from e
    check_return_statements(tree)
    transformer = TyPyTransformer()
    tree = transformer.visit(tree)
    ast.fix_missing_locations(tree)
    return tree


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
                    f"Function '{name}' declared with a return statement "
                    f"{ast.unparse(ann)}, but no return statement found in the function body "
                    f"return with value" 
                    f"(line {lineno})."
                )
            self.generic_visit(node)

    ReturnVisitor().visit(tree)
