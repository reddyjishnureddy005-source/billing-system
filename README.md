# Intelligent GST Billing & Management System
### Developed for Jai Mata Dhi Poly Packs

A modern, high-performance desktop application designed to automate the manual invoicing process for a manufacturing firm. This system handles everything from real-time database lookups to professional A4 PDF bill generation.

---

## Key Features
- **Smart Auto-Fill:** Implemented a real-time SQLite lookup engine that automatically maps GSTINs to customer names, reducing data entry time by ~50%.
- **Automated Tax Engine:** Custom logic to detect and switch between **CGST/SGST** and **IGST** based on the 33-prefix or State Code.
- **Financial Accuracy:** Automated "Number-to-Words" conversion for Grand Totals to ensure zero errors in professional accounting.
- **Persistent Storage:** Full transaction history management using a local SQLite database with the ability to edit or delete past bills.
- **A4 PDF Invoicing:** Dynamic coordinate-based PDF generation using the ReportLab engine, optimized for A4 portrait printing.
- **Audit Reporting:** One-click export to Excel for monthly tax filings and sales analysis.

##  Technical Stack
- **Language:** Python 3.11+
- **Frontend:** CustomTkinter (Modern Dark Mode UI)
- **Database:** SQLite3
- **Reporting:** Pandas, OpenPyXL
- **PDF Engine:** ReportLab
- **Build Tool:** PyInstaller


##  Build Instructions
To build the standalone executable yourself:
1. Clone the repo: `git clone https://github.com/reddyjishnureddy005-source/billing-system.git
2. Install requirements: `pip install customtkinter reportlab pandas tkcalendar num2words openpyxl`
3. Run build command:
   ```bash
   python -m PyInstaller --noconsole --onefile --add-data "logo.png;." billing.py