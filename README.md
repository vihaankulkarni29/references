# Dubai Whale Hunter

## Overview
Automated lead discovery tool targeted at companies in Dubai ("Whales"). It identifies leads based on hiring signals (e.g. Jira usage) and technical analysis.

## Structure
- `src/`: Core source code modules.
    - `job_discovery.py`: Finds companies hiring for specific roles.
    - `tech_checker.py`: Analyzes websites for tech stack/localization.
    - `linkedin_pivot.py`: Stealth X-Ray search for Decision Makers.
- `scripts/`: Helper scripts for testing and debugging.
- `docs/`: Documentation.
- `main.py`: Entry point for the pipeline.
- `leads.csv`: Output file.

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m playwright install chromium
   ```
2. Run the pipeline:
   ```bash
   python main.py
   ```

## Development
To run individual module tests:
```bash
python scripts/test_discovery.py
python scripts/test_pivot.py
```
