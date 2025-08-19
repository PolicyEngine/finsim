#!/usr/bin/env python3
"""Execute the notebook with a smaller number of simulations for speed."""

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import re

# Read the notebook
with open('personal_injury_settlement_stacked.ipynb', 'r') as f:
    nb = nbformat.read(f, as_version=4)

# Modify the number of simulations to run faster
for cell in nb.cells:
    if cell.cell_type == 'code':
        # Replace n_simulations=2000 with n_simulations=500 for faster execution
        cell.source = re.sub(r'n_simulations=2000', 'n_simulations=500', cell.source)

# Execute the notebook
ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
ep.preprocess(nb, {'metadata': {'path': '.'}})

# Save the executed notebook
with open('personal_injury_settlement_executed.ipynb', 'w') as f:
    nbformat.write(nb, f)

print("Notebook executed and saved to personal_injury_settlement_executed.ipynb")