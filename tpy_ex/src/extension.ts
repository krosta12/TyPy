//import * as vscode from 'vscode'
//
//export function activate(context: vscode.ExtensionContext) {
//    const provider = vscode.languages.registerOnTypeFormattingEditProvider('TyPy', {
//        provideOnTypeFormattingEdits(document, position, ch, options) {
//            if (ch === ':') {
//                const indent = options.insertSpaces
//                    ? ' d'.repeat(options.tabSize)
//                    : '\t';
//                return [vscode.TextEdit.insert(
//                    new vscode.Position(position.line + 1, 0),
//                    indent
//                )];
//            }
//            return [];
//        }
//    }, ':');
//    
//    context.subscriptions.push(provider);
//}
