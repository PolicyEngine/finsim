#!/usr/bin/env python3
"""Test script to verify syntax without PolicyEngine dependencies."""

import ast
import sys

def check_syntax(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r') as f:
            source = f.read()
        ast.parse(source)
        print(f"✅ {filepath}: Syntax is valid")
        return True
    except SyntaxError as e:
        print(f"❌ {filepath}: {e}")
        return False

# Test the files we modified
files_to_test = [
    'finsim/portfolio_simulation.py',
    'app.py'
]

all_valid = True
for filepath in files_to_test:
    if not check_syntax(filepath):
        all_valid = False

if all_valid:
    print("\n✅ All files have valid syntax!")
else:
    print("\n❌ Some files have syntax errors")
    sys.exit(1)