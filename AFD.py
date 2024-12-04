
import re
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QToolTip, QAction, QMessageBox, QSplitter, QLabel, QCheckBox, QHBoxLayout)
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QIcon, QTextCursor
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
        error_range = self._validate_text(text)
        if error_range:
            self.setFormat(error_range[0], error_range[1] - error_range[0], self.errorFormat)

    def _validate_text(self, text):
        # Remove comments and trim
        text_clean = re.sub(r'//.*$|/\*.*\*/', '', text).strip()

        # Ignore empty lines
        if not text_clean:
            return None

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
            return None

        if text_clean == '}':
            self.current_block_level = max(0, self.current_block_level - 1)
            return None

        # Validate different contexts
        if re.match(class_pattern, text_clean):
            self.class_parsing_state = True
            return None

        if re.match(main_method_pattern, text_clean) or re.match(method_pattern, text_clean):
            return None

        # Validate inside control structures and methods
        if self.current_block_level > 0:
            if any(re.match(pattern, text_clean) for pattern in control_patterns + variable_patterns):
                return None

        # Additional comprehensive error detection
        if not any([
            re.match(class_pattern, text_clean),
            re.match(method_pattern, text_clean),
            re.match(main_method_pattern, text_clean),
            any(re.match(pattern, text_clean) for pattern in control_patterns + variable_patterns)
        ]):
            return (0, len(text))

        return None

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
        self.textEdit = QTextEdit()
        self.textEdit.setMouseTracking(True)
        self.textEdit.viewport().installEventFilter(self)

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
        splitter.setStretchFactor(0,7)
        splitter.setStretchFactor(2,3)

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
        exitAction = QAction('Exit', self)
        fileMenu.addAction(newAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
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
        debugAction = QAction(QIcon('img/debug_icon.png'), 'Debug', self)
        debugToolbar.addAction(debugAction)

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
        exitAction.triggered.connect(self.close)
        cutAction.triggered.connect(self.textEdit.cut)
        copyAction.triggered.connect(self.textEdit.copy)
        pasteAction.triggered.connect(self.textEdit.paste)
        debugAction.triggered.connect(self.debugCode)

    def newFile(self):
        self.textEdit.clear()
        self.errorDisplay.clear()
        self.statusBar().showMessage('New file created')

    def openFile(self):
        # Implement file open logic here
        self.statusBar().showMessage('File opened')

    def saveFile(self):
        # Implement file save logic here
        self.statusBar().showMessage('File saved')

    def debugCode(self):
        self.errorDisplay.clear()
        text = self.textEdit.toPlainText()
        lines = text.split('\n')
        for i, line in enumerate(lines):
            error_range = self.highlighter._validate_text(line)
            if error_range:
                self.textEdit.moveCursor(QTextCursor.Start)
                for _ in range(i):
                    self.textEdit.moveCursor(QTextCursor.Down)
                self.textEdit.moveCursor(QTextCursor.Right, QTextCursor.MoveAnchor, error_range[0])
                self.textEdit.moveCursor(QTextCursor.Right, QTextCursor.KeepAnchor, error_range[1] - error_range[0])
                self.textEdit.setTextCursor(self.textEdit.textCursor())
                self.errorDisplay.append(f'Error detected on line {i + 1}: {line}')
                break

    def eventFilter(self, source, event):
        if event.type() == event.MouseMove and source is self.textEdit.viewport():
            cursor = self.textEdit.cursorForPosition(event.pos())
            cursor.select(cursor.WordUnderCursor)
            text = cursor.selectedText()
            if text and self.is_error(text):
                QToolTip.showText(event.globalPos(), "Syntax error detected")
            else:
                QToolTip.hideText()
        return super().eventFilter(source, event)

    def is_error(self, text):
        # Simple error detection logic
        return text.endswith("!") or text.endswith("System.out.println(\"Hello, World!\")")

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