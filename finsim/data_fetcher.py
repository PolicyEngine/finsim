"""Data fetching utilities for FinSim."""

import json
import requests
from bs4 import BeautifulSoup
import re
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SSAMortalityFetcher:
    """Fetches SSA mortality tables from official sources."""
    
    SSA_URL = "https://www.ssa.gov/oact/STATS/table4c6.html"
    
    # Fallback data for when fetching fails
    FALLBACK_MALE = {
        65: 0.01604, 66: 0.01753, 67: 0.01912, 68: 0.02084, 69: 0.02271,
        70: 0.02476, 71: 0.02700, 72: 0.02946, 73: 0.03217, 74: 0.03515,
        75: 0.03843, 76: 0.04204, 77: 0.04603, 78: 0.05043, 79: 0.05530,
        80: 0.06069, 81: 0.06665, 82: 0.07326, 83: 0.08058, 84: 0.08868,
        85: 0.09764, 86: 0.10753, 87: 0.11845, 88: 0.13048, 89: 0.14373,
        90: 0.15829, 91: 0.17427, 92: 0.19178, 93: 0.21093, 94: 0.23182,
        95: 0.25457, 96: 0.27930, 97: 0.30612, 98: 0.33515, 99: 0.36651,
        100: 0.40032
    }
    
    FALLBACK_FEMALE = {
        65: 0.01052, 66: 0.01146, 67: 0.01251, 68: 0.01368, 69: 0.01498,
        70: 0.01642, 71: 0.01803, 72: 0.01983, 73: 0.02183, 74: 0.02406,
        75: 0.02653, 76: 0.02927, 77: 0.03232, 78: 0.03570, 79: 0.03947,
        80: 0.04365, 81: 0.04830, 82: 0.05345, 83: 0.05916, 84: 0.06548,
        85: 0.07247, 86: 0.08019, 87: 0.08872, 88: 0.09812, 89: 0.10849,
        90: 0.11991, 91: 0.13247, 92: 0.14627, 93: 0.16142, 94: 0.17802,
        95: 0.19620, 96: 0.21605, 97: 0.23770, 98: 0.26127, 99: 0.28689,
        100: 0.31467
    }
    
    def fetch_tables(self) -> Tuple[Dict[int, float], Dict[int, float]]:
        """Fetch mortality tables from SSA website.
        
        Returns:
            Tuple of (male_mortality, female_mortality) dictionaries
        """
        try:
            response = requests.get(self.SSA_URL, timeout=10)
            response.raise_for_status()
            
            male_mortality, female_mortality = self._parse_ssa_page(response.text)
            
            if not male_mortality:
                logger.warning("Could not parse SSA data, using fallback")
                return self.FALLBACK_MALE.copy(), self.FALLBACK_FEMALE.copy()
            
            return male_mortality, female_mortality
            
        except Exception as e:
            logger.error(f"Error fetching SSA data: {e}")
            return self.FALLBACK_MALE.copy(), self.FALLBACK_FEMALE.copy()
    
    def _parse_ssa_page(self, html: str) -> Tuple[Dict[int, float], Dict[int, float]]:
        """Parse SSA HTML page to extract mortality tables.
        
        Args:
            html: Raw HTML from SSA website
            
        Returns:
            Tuple of (male_mortality, female_mortality) dictionaries
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        male_mortality = {}
        female_mortality = {}
        
        # Find tables containing mortality data
        tables = soup.find_all('table')
        
        for table in tables:
            headers = table.find_all('th')
            header_text = ' '.join([h.get_text().strip() for h in headers])
            
            # Look for the period life table
            if 'Male' in header_text and 'Female' in header_text:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        try:
                            # Parse age
                            age_text = cells[0].get_text().strip()
                            age_match = re.search(r'\d+', age_text)
                            if not age_match:
                                continue
                            age = int(age_match.group())
                            
                            # Parse male mortality rate
                            male_text = cells[1].get_text().strip()
                            male_text = re.sub(r'[^\d.]', '', male_text)
                            if male_text:
                                male_rate = float(male_text)
                                if 0 < male_rate < 1:  # Sanity check
                                    male_mortality[age] = male_rate
                            
                            # Parse female mortality rate
                            female_text = cells[2].get_text().strip()
                            female_text = re.sub(r'[^\d.]', '', female_text)
                            if female_text:
                                female_rate = float(female_text)
                                if 0 < female_rate < 1:  # Sanity check
                                    female_mortality[age] = female_rate
                                    
                        except (ValueError, IndexError):
                            continue
        
        return male_mortality, female_mortality
    
    def save_to_json(self, output_path: Optional[Path] = None) -> Path:
        """Fetch and save mortality data to JSON file.
        
        Args:
            output_path: Path to save JSON file (defaults to package data dir)
            
        Returns:
            Path to saved file
        """
        if output_path is None:
            output_path = Path(__file__).parent / "data" / "ssa_mortality.json"
        
        male_mortality, female_mortality = self.fetch_tables()
        
        data = {
            "source": self.SSA_URL,
            "description": "SSA Period Life Table 2021",
            "male": {str(k): v for k, v in male_mortality.items()},
            "female": {str(k): v for k, v in female_mortality.items()}
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved mortality data to {output_path}")
        return output_path