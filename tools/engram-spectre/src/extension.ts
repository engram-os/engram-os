import * as vscode from 'vscode';
import axios from 'axios'; 

export function activate(context: vscode.ExtensionContext) {
	console.log('Engram Spectre is active!');

	let disposable = vscode.commands.registerCommand('engram.ask', async () => {
		
		const editor = vscode.window.activeTextEditor;
		if (!editor) {
			vscode.window.showErrorMessage('No active editor found! Spectre cannot see.');
			return;
		}

		const selection = editor.selection;
		const codeText = editor.document.getText(selection);

		if (!codeText) {
			vscode.window.showInformationMessage('Please select some code first.');
			return;
		}

		const instruction = await vscode.window.showInputBox({
			placeHolder: "What should Spectre do? (e.g., 'Explain this', 'Refactor to clean code')",
			prompt: "Ask Engram Spectre"
		});

		if (!instruction) return;

		vscode.window.withProgress({
			location: vscode.ProgressLocation.Notification,
			title: "Spectre is thinking...",
			cancellable: false
		}, async () => {
			
			try {
				const response = await axios.post('http://localhost:8000/api/spectre/chat', {
					code: codeText,
					instruction: instruction
				});

				const answer = response.data.response;

				const doc = await vscode.workspace.openTextDocument({
					content: `// Spectre ANSWER:\n\n${answer}`,
					language: 'markdown'
				});
				await vscode.window.showTextDocument(doc, { viewColumn: vscode.ViewColumn.Beside });

			} catch (error) {
				vscode.window.showErrorMessage(`Ghost died: ${error}`);
			}
		});
	});

	context.subscriptions.push(disposable);
}

export function deactivate() {}