import sys
import re
import os
from PyQt5.QtWidgets import (QTextEdit, QApplication, QMainWindow, QVBoxLayout, QLabel, QSplitter,
                             QWidget, QAction, QHBoxLayout, QCheckBox, QFileDialog, QMessageBox)
from PyQt5.QtGui import QTextCharFormat, QFont, QSyntaxHighlighter, QIcon, QTextCursor
from PyQt5.QtCore import Qt, QRegExp


class JavaSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlightingRules = []
        self.current_block_level = 0
        self.class_parsing_state = False

        # Keyword Formatting
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(Qt.blue)
        keywordFormat.setFontWeight(QFont.Bold)

        keywords = [
            "public", "private", "protected", "class", "interface", "static",
            "void", "int", "String", "boolean", "double", "float", "long",
            "if", "else", "while", "for", "return", "new",
            "System.out.println", "System", "out", "println",
            "main", "throws", "try", "catch", "final"
        ]

        self.keywordPatterns = [f"\\b{keyword}\\b" for keyword in keywords]

        for pattern in self.keywordPatterns:
            rule = (QRegExp(pattern), keywordFormat)
            self.highlightingRules.append(rule)

        # Comment Formatting
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(Qt.green)
        commentRules = [
            (QRegExp("//[^\n]*"), commentFormat),  # Single-line comments
            (QRegExp("/\\*.*\\*/"), commentFormat)  # Multi-line comments
        ]
        self.highlightingRules.extend(commentRules)

        # Error Formatting
        self.errorFormat = QTextCharFormat()
        self.errorFormat.setForeground(Qt.red)
        self.errorFormat.setUnderlineColor(Qt.red)
        self.errorFormat.setUnderlineStyle(QTextCharFormat.WaveUnderline)

    def highlightBlock(self, text):
        # Apply syntax highlighting rules
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        # Validate entire text
        error_range, correct_option = self._validate_text(text)
        if error_range:
            self.setFormat(error_range[0], error_range[1] - error_range[0], self.errorFormat)

    def _validate_text(self, text):
        # Remove comments and trim
        text_clean = re.sub(r'//.*$|/\*.*\*/', '', text).strip()

        # Ignore empty lines
        if not text_clean:
            return None, None

        # Class and Method Patterns
        class_pattern = r'^(public|private|protected)?\s*class\s+\w+\s*(\{)?$'
        method_pattern = r'^(public|private|protected)?\s*(static)?\s*(void|int|String|boolean)\s+\w+\s*\([^)]*\)\s*\{?$'
        main_method_pattern = r'^public\s+static\s+void\s+main\s*\(\s*String\s*\[\]\s*\w+\s*\)\s*\{?$'

        # Control Structure Patterns
        control_patterns = [
            r'^(if|while|for)\s*\(\s*[^)]+\s*\)\s*\{?$',
            r'^(System\.out\.println\s*\(\s*("[^"]*"|\w+)\s*\);)$'
        ]

        # Variable Declaration Patterns
        variable_patterns = [
            r'^(int|String|boolean|double|float|long)\s+\w+\s*(=\s*[^;]+)?;$',
            r'^[a-zA-Z_]\w*\s*=\s*[^;]+;$'  # Assignment for existing variables
        ]

        # Handle opening and closing braces
        if text_clean == '{':
            self.current_block_level += 1
            return None, None

        if text_clean == '}':
            self.current_block_level = max(0, self.current_block_level - 1)
            return None, None

        # Validate different contexts
        if re.match(class_pattern, text_clean):
            self.class_parsing_state = True
            return None, None

        if re.match(main_method_pattern, text_clean) or re.match(method_pattern, text_clean):
            return None, None

        # Validate inside control structures and methods
        if self.current_block_level > 0:
            if any(re.match(pattern, text_clean) for pattern in control_patterns + variable_patterns):
                return None, None

        # Additional comprehensive error detection
        if not any([
            re.match(class_pattern, text_clean),
            re.match(method_pattern, text_clean),
            re.match(main_method_pattern, text_clean),
            any(re.match(pattern, text_clean) for pattern in control_patterns + variable_patterns)
        ]):
            return (0, len(text)), "Expected a valid Java statement"

        return None, None


class CodeEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_block_level = 0
        self.current_file_path = None  # Store current file path

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_BraceLeft:
            # Insert '{' and a new block
            self.insertPlainText('{')
            self.current_block_level += 1
            cursor = self.textCursor()
            cursor.insertText('\n\t//metodos\n}\n')
            cursor.movePosition(QTextCursor.Up, QTextCursor.MoveAnchor, 2)
            self.setTextCursor(cursor)
            return
        super().keyPressEvent(event)


class JavaSyntaxCheckerIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Java Syntax Checker IDE')
        self.setGeometry(100, 100, 1000, 600)

        # Create main layout
        layout = QVBoxLayout()

        # Create text area with syntax highlighting
        self.textEdit = CodeEditor()
        self.textEdit.setMouseTracking(True)

        # Set larger font
        font = QFont()
        font.setPointSize(14)
        self.textEdit.setFont(font)

        self.highlighter = JavaSyntaxHighlighter(self.textEdit.document())

        # Create error display area
        self.errorDisplay = QTextEdit()
        self.errorDisplay.setReadOnly(True)
        self.errorDisplay.setFont(font)

        # Create label for error display
        errorLabel = QLabel("Syntax Errors")
        font.setPointSize(10)
        errorLabel.setFont(font)

        # Create splitter to hold both text areas
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.textEdit)
        splitter.addWidget(errorLabel)
        splitter.addWidget(self.errorDisplay)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(2, 3)

        layout.addWidget(splitter)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Create menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        editMenu = menubar.addMenu('Edit')
        viewMenu = menubar.addMenu('View')
        helpMenu = menubar.addMenu('Help')

        # Create toolbars
        fileToolbar = self.addToolBar('File')
        editToolbar = self.addToolBar('Edit')
        debugToolbar = self.addToolBar('Debug')

        # Add actions to file menu and toolbar
        newAction = QAction('New', self)
        openAction = QAction('Open', self)
        saveAction = QAction('Save', self)
        saveAsAction = QAction('Save As', self)
        exitAction = QAction('Exit', self)

        fileMenu.addAction(newAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(exitAction)

        fileToolbar.addAction(newAction)
        fileToolbar.addAction(openAction)
        fileToolbar.addAction(saveAction)

        # Add actions to edit menu and toolbar
        cutAction = QAction('Cut', self)
        copyAction = QAction('Copy', self)
        pasteAction = QAction('Paste', self)

        editMenu.addAction(cutAction)
        editMenu.addAction(copyAction)
        editMenu.addAction(pasteAction)

        editToolbar.addAction(cutAction)
        editToolbar.addAction(copyAction)
        editToolbar.addAction(pasteAction)

        # Add debug action to debug toolbar
        runAction = QAction(QIcon('img/run_icon.png'), 'Run', self)
        debugToolbar.addAction(runAction)

        # Create status bar
        self.statusBar().showMessage('Ready')

        # Create night mode checkbox and add it to the menu bar
        self.nightModeCheckBox = QCheckBox("Night Mode")
        self.nightModeCheckBox.stateChanged.connect(self.toggleNightMode)
        nightModeWidget = QWidget()
        nightModeLayout = QHBoxLayout()
        nightModeLayout.addWidget(self.nightModeCheckBox)
        nightModeLayout.setAlignment(Qt.AlignRight)
        nightModeLayout.setContentsMargins(0, 0, 10, 0)
        nightModeWidget.setLayout(nightModeLayout)
        menubar.setCornerWidget(nightModeWidget, Qt.TopRightCorner)

        # Connect actions
        newAction.triggered.connect(self.newFile)
        openAction.triggered.connect(self.openFile)
        saveAction.triggered.connect(self.saveFile)
        saveAsAction.triggered.connect(self.saveFileAs)
        exitAction.triggered.connect(self.close)
        cutAction.triggered.connect(self.textEdit.cut)
        copyAction.triggered.connect(self.textEdit.copy)
        pasteAction.triggered.connect(self.textEdit.paste)
        runAction.triggered.connect(self.runCode)

    def newFile(self):
        # Check if current file has unsaved changes
        if self.textEdit.document().isModified():
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'Do you want to save current file?',
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                self.saveFile()

        self.textEdit.clear()
        self.errorDisplay.clear()
        self.textEdit.current_file_path = None
        self.statusBar().showMessage('New file created')

    def openFile(self):
        # Get filename to open
        filename, _ = QFileDialog.getOpenFileName(self, 'Open File',
                                                  os.path.expanduser('~'),
                                                  'Java Files (*.java);;All Files (*)')
        if filename:
            try:
                with open(filename, 'r') as file:
                    self.textEdit.setPlainText(file.read())
                    self.textEdit.current_file_path = filename
                    self.statusBar().showMessage(f'Opened: {filename}')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Could not open file: {str(e)}')

    def saveFile(self):
        # If no previous file path, call save as
        if not self.textEdit.current_file_path:
            return self.saveFileAs()

        try:
            with open(self.textEdit.current_file_path, 'w') as file:
                file.write(self.textEdit.toPlainText())
            self.textEdit.document().setModified(False)
            self.statusBar().showMessage(f'Saved: {self.textEdit.current_file_path}')
            return True
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Could not save file: {str(e)}')
            return False

    def saveFileAs(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save File',
                                                  os.path.expanduser('~'),
                                                  'Java Files (*.java);;All Files (*)')
        if filename:
            try:
                # Ensure filename has .java extension
                if not filename.endswith('.java'):
                    filename += '.java'

                with open(filename, 'w') as file:
                    file.write(self.textEdit.toPlainText())

                self.textEdit.current_file_path = filename
                self.textEdit.document().setModified(False)
                self.statusBar().showMessage(f'Saved: {filename}')
                return True
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Could not save file: {str(e)}')
                return False
        return False

    def runCode(self):
        self.errorDisplay.clear()
        text = self.textEdit.toPlainText()
        lines = text.split('\n')
        error_count = 0

        for i, line in enumerate(lines):
            error_range, correct_option = self.highlighter._validate_text(line)
            if error_range:
                error_count += 1
                self.errorDisplay.append(f'Error {error_count} on line {i + 1}: {line}')
                if correct_option:
                    self.errorDisplay.append(f'Suggestion: {correct_option}\n')

        if error_count == 0:
            self.errorDisplay.append('No syntax errors detected. Code looks good!')
            self.statusBar().showMessage('Code syntax check completed successfully')
        else:
            self.statusBar().showMessage(f'Found {error_count} syntax errors')

    def toggleNightMode(self, state):
        if state == Qt.Checked:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTextEdit {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QCheckBox {
                    color: #ffffff;
                }
            """)
        else:
            self.setStyleSheet("")


def main():
    app = QApplication(sys.argv)
    ide = JavaSyntaxCheckerIDE()
    ide.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
