// import * as vscode from 'vscode';

// export function activate(context: vscode.ExtensionContext) {
//     const provider = vscode.languages.registerOnTypeFormattingEditProvider('tpy', {
//         provideOnTypeFormattingEdits(document, position, ch, options) {
//             if (ch === ':') {
//                 const config = vscode.workspace.getConfiguration('editor');
//                 const indent = config.get<boolean>('insertSpaces') 
//                     ? ' '.repeat(config.get<number>('tabSize', 4))
//                     : '\t';
                
//                 return [vscode.TextEdit.insert(
//                     new vscode.Position(position.line + 1, 0),
//                     indent
//                 )];
//             }
//             return [];
//         }
//     }, ':', '\n');

//     context.subscriptions.push(provider);
// }