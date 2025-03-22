import os
import pytest
import re


class CodeQualityChecker:
    def __init__(self, directory):
        self.directory = directory
        self.total_lines = 0
        self.total_errors = 0

    def count_lines(self, file_path):
        """Zählt die Zeilen einer Datei, ohne Leerzeilen und Kommentare."""
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            code_lines = [
                line
                for line in lines
                if line.strip() and not line.strip().startswith("#")
            ]
            return len(code_lines)

    def check_syntax_errors(self, file_path):
        """Überprüft eine Datei auf Syntaxfehler."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                compile(content, file_path, "exec")
        except SyntaxError as e:
            print(f"Syntaxfehler in {file_path}: {e}")
            return 1
        return 0

    def analyze_directory(self):
        """Analysiert alle Python-Dateien im angegebenen Verzeichnis."""
        self.total_lines = 0
        self.total_errors = 0
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    file_lines = self.count_lines(file_path)
                    self.total_lines += file_lines
                    self.total_errors += self.check_syntax_errors(file_path)
                    print(f"{file_path}: {file_lines} Codezeilen")

    def calculate_error_density(self):
        """Berechnet die Fehlerdichte (Fehler pro KLOC)."""
        kloc = self.total_lines / 1000 if self.total_lines > 0 else 1
        error_density = self.total_errors / kloc
        return error_density


# Testfälle für pytest


def test_error_density():
    checker = CodeQualityChecker(".")  # Aktuelles Verzeichnis durchsuchen
    checker.analyze_directory()
    error_density = checker.calculate_error_density()
    assert error_density < 0.5, f"Fehlerdichte zu hoch: {error_density:.2f} Fehler/KLOC"


def test_syntax_errors():
    checker = CodeQualityChecker(".")
    checker.analyze_directory()
    assert (
        checker.total_errors == 0
    ), f"Es wurden {checker.total_errors} Syntaxfehler gefunden!"


def test_calculate_error_density():
    checker = CodeQualityChecker(".")
    checker.analyze_directory()
    error_density = checker.calculate_error_density()
    assert (
        0.0 <= error_density <= 0.5
    ), f"Fehlerdichte außerhalb des zulässigen Bereichs! Gemessene Fehlerdichte: {error_density:.2f} Fehler/KLOC"


if __name__ == "__main__":
    pytest.main(["-v"])
