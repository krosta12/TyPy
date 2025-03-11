import ast

class TyPyTransformer(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        # Если функция имеет аннотации параметров type_checked
        has_annotation = (node.returns is not None) or any(arg.annotation is not None for arg in node.args.args)
        if has_annotation:
            decorator = ast.Name(id='type_checked', ctx=ast.Load())
            node.decorator_list.insert(0, decorator)
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node):
        # Преобразуем присваивание с аннотацией
        if node.value is not None and isinstance(node.target, ast.Name):
            var_name = node.target.id
            check_call = ast.Call(
                func=ast.Name(id='__type_check__', ctx=ast.Load()),
                args=[
                    ast.Constant(value=var_name),
                    node.value,
                    node.annotation
                ],
                keywords=[]
            )
            new_node = ast.Assign(
                targets=[node.target],
                value=check_call
            )
            return ast.copy_location(new_node, node)
        return node
