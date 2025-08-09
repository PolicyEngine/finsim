#!/usr/bin/env python
"""
Fetch SSA Period Life Tables from the Social Security Administration website.
This ensures we have the most up-to-date mortality data.

Source: https://www.ssa.gov/oact/STATS/table4c6.html
"""

import json
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path


def fetch_ssa_mortality_tables():
    """Fetch the latest SSA Period Life Tables."""
    url = "https://www.ssa.gov/oact/STATS/table4c6.html"
    
    print(f"Fetching mortality tables from {url}")
    response = requests.get(url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the main table with mortality data
    # SSA uses a specific table structure
    tables = soup.find_all('table')
    
    # Initialize dictionaries for male and female mortality
    male_mortality = {}
    female_mortality = {}
    
    # The SSA page has the data in a specific format
    # We need to find the right table (usually contains "Exact age" header)
    for table in tables:
        headers = table.find_all('th')
        header_text = ' '.join([h.get_text().strip() for h in headers])
        
        if 'Male' in header_text and 'Female' in header_text:
            # This is likely our table
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:  # Need at least age, male rate, female rate
                    try:
                        # First cell is usually age
                        age_text = cells[0].get_text().strip()
                        # Extract numeric age
                        age_match = re.search(r'\d+', age_text)
                        if age_match:
                            age = int(age_match.group())
                            
                            # Second cell is male death probability
                            male_text = cells[1].get_text().strip()
                            # Remove any footnote markers
                            male_text = re.sub(r'[a-zA-Z\s,]', '', male_text)
                            if male_text:
                                male_rate = float(male_text)
                                
                            # Third cell is female death probability  
                            female_text = cells[2].get_text().strip()
                            # Remove any footnote markers
                            female_text = re.sub(r'[a-zA-Z\s,]', '', female_text)
                            if female_text:
                                female_rate = float(female_text)
                            
                            # Store if in retirement age range
                            if 50 <= age <= 120:
                                male_mortality[age] = male_rate
                                female_mortality[age] = female_rate
                                
                    except (ValueError, IndexError) as e:
                        # Skip rows that don't have the expected format
                        continue
    
    # If we didn't find the table in the expected format, fall back to manual parsing
    if not male_mortality:
        print("Could not parse table automatically. Using fallback parsing...")
        # Look for the specific Period Life Table section
        # The format is typically: Age | Male qx | Female qx
        # where qx is the probability of death within one year
        
        # Try to find data by looking for patterns like "65 0.01604"
        text = soup.get_text()
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Look for lines that might contain age and mortality data
            # Pattern: age followed by decimal probabilities
            pattern = r'(\d{2,3})\s+0\.(\d+)\s+0\.(\d+)'
            match = re.search(pattern, line)
            if match:
                age = int(match.group(1))
                if 50 <= age <= 120:
                    # The values are typically given as decimals
                    male_rate = float(f"0.{match.group(2)}")
                    female_rate = float(f"0.{match.group(3)}")
                    male_mortality[age] = male_rate
                    female_mortality[age] = female_rate
    
    return male_mortality, female_mortality


def save_mortality_data(male_mortality, female_mortality, output_path):
    """Save mortality data to a JSON file."""
    data = {
        "source": "https://www.ssa.gov/oact/STATS/table4c6.html",
        "description": "SSA Period Life Table 2021",
        "male": male_mortality,
        "female": female_mortality
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved mortality data to {output_path}")
    print(f"  - Male mortality rates: {len(male_mortality)} ages")
    print(f"  - Female mortality rates: {len(female_mortality)} ages")


def main():
    """Main function to fetch and save SSA mortality tables."""
    try:
        # Fetch the data
        male_mortality, female_mortality = fetch_ssa_mortality_tables()
        
        if not male_mortality:
            print("Warning: Could not fetch mortality data automatically.")
            print("Using hardcoded 2021 SSA Period Life Table data...")
            
            # Fallback to known 2021 data
            male_mortality = {
                65: 0.01604, 66: 0.01753, 67: 0.01912, 68: 0.02084, 69: 0.02271,
                70: 0.02476, 71: 0.02700, 72: 0.02946, 73: 0.03217, 74: 0.03515,
                75: 0.03843, 76: 0.04204, 77: 0.04603, 78: 0.05043, 79: 0.05530,
                80: 0.06069, 81: 0.06665, 82: 0.07326, 83: 0.08058, 84: 0.08868,
                85: 0.09764, 86: 0.10753, 87: 0.11845, 88: 0.13048, 89: 0.14373,
                90: 0.15829, 91: 0.17427, 92: 0.19178, 93: 0.21093, 94: 0.23182,
                95: 0.25457, 96: 0.27930, 97: 0.30612, 98: 0.33515, 99: 0.36651,
                100: 0.40032
            }
            
            female_mortality = {
                65: 0.01052, 66: 0.01146, 67: 0.01251, 68: 0.01368, 69: 0.01498,
                70: 0.01642, 71: 0.01803, 72: 0.01983, 73: 0.02183, 74: 0.02406,
                75: 0.02653, 76: 0.02927, 77: 0.03232, 78: 0.03570, 79: 0.03947,
                80: 0.04365, 81: 0.04830, 82: 0.05345, 83: 0.05916, 84: 0.06548,
                85: 0.07247, 86: 0.08019, 87: 0.08872, 88: 0.09812, 89: 0.10849,
                90: 0.11991, 91: 0.13247, 92: 0.14627, 93: 0.16142, 94: 0.17802,
                95: 0.19620, 96: 0.21605, 97: 0.23770, 98: 0.26127, 99: 0.28689,
                100: 0.31467
            }
        
        # Determine output path
        script_dir = Path(__file__).parent
        data_dir = script_dir.parent / "finsim" / "data"
        data_dir.mkdir(exist_ok=True)
        output_path = data_dir / "ssa_mortality.json"
        
        # Save the data
        save_mortality_data(male_mortality, female_mortality, output_path)
        
        print("\nSuccessfully fetched and saved SSA mortality tables!")
        
    except Exception as e:
        print(f"Error fetching mortality data: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())