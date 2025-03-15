# MOTO Analysis Tool Extension

## Installation

This extension requires a working MOTO installation.

```bash
pip install moto-analysis-tool
```

## Quick Setup

1. Add "analysis_tool" to your INSTALLED_APPS setting (after setting up main_app in settings.py):

```python
INSTALLED_APPS = [
    ...
    'main_app',  # The main MOTO app must be listed first
    'analysis_tool',  # Our extension
    ...
]
```

2. Include the extension URLs in your project urls.py (a Prefix like at/ is not nessesary, but recommended to prevent conflicts):

```python
path('at/', include('analysis_tool.urls')),
```

3. Run migrations to create the analysis tables (if not used Docker):

```bash
python manage.py migrate analysis_tool
```

4. Access the analytics features through the MOTO interface.

## Integration Features

This extension integrates with MOTO by adding:

- A "Detailanalyse" button in student profiles
- New navigation menu items for analytics
- Heatmap visualization for room utilization
- Advanced student and AG category analytics

## Requirements

- MOTO application (main_app)
- Django >= 4.2.0
- pandas >= 1.5.0
- numpy >= 1.21.0
- scikit-learn >= 1.0.0
- mlxtend >= 0.21.0

## License

GNU Affero General Public License v3.0 (AGPL-3.0)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.