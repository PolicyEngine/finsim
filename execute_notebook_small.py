#!/usr/bin/env python3
"""Execute the notebook with fewer simulations for faster execution."""

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
import re

# Read the notebook
with open('personal_injury_settlement_stacked.ipynb', 'r') as f:
    nb = nbformat.read(f, as_version=4)

# Modify to use fewer simulations for faster execution
for cell in nb.cells:
    if cell.cell_type == 'code':
        # Reduce simulations from 2000 to 200 for speed
        cell.source = re.sub(r'n_simulations=2000', 'n_simulations=200', cell.source)
        # Reduce spending levels for speed
        cell.source = re.sub(
            r'spending_levels = list\(range\(30_000, 105_000, 5_000\)\)',
            'spending_levels = list(range(30_000, 105_000, 10_000))',
            cell.source
        )

# Execute the notebook
print("Executing notebook with 200 simulations...")
ep = ExecutePreprocessor(timeout=1200, kernel_name='python3')
ep.preprocess(nb, {'metadata': {'path': '.'}})

# Save the executed notebook
with open('personal_injury_settlement_executed.ipynb', 'w') as f:
    nbformat.write(nb, f)

print("Notebook executed successfully!")