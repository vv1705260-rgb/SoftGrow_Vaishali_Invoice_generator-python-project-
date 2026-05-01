# SoftGrow_Vaishali_Invoice_generator-python-project-

# SoftGrowTech - Invoice Generator Pro

Python Task 1 - Project 3 for SoftGrowTech Internship

## 📋 Description
A command-line GST Invoice Generator built with Python. It creates professional tax invoices with automatic calculations, numbering, and record keeping.

This project demonstrates file handling, data validation, CSV operations, and real-world billing logic in Python.

## ✨ Special Features
1. **Auto Invoice Numbering** - Generates unique IDs like INV-001, INV-002 automatically
2. **Date & Time Stamp** - Adds current date/time to every invoice
3. **GST Calculation** - Splits 18% GST into CGST 9% + SGST 9% as per Indian tax rules
4. **Discount System** - Apply percentage-based discounts before tax calculation
5. **Dual File Output** - Saves invoice as `.txt` for printing + `.csv` for Excel records
6. **Invoice History** - View all past invoices from master CSV file
7. **Input Validation** - Handles invalid inputs, empty names, negative numbers gracefully

## 🛠️ Tech Used
- **Language:** Python 3
- **Modules:** `datetime`, `csv`, `os` - all built-in, no installation needed
- **Storage:** `.txt` files for invoices + `.csv` for sales history

## 🚀 How to Run
1. Make sure Python 3 is installed
2. Download `invoice_generator_pro.py`
3. Open terminal in the project folder
4. Run the command:
5. 5. Follow the menu:
   - `1` to Create New Invoice
   - `2` to View Invoice History
   - `3` to Exit

## 📂 Files Created
| File | Description |
| --- | --- |
| `invoice_generator_pro.py` | Main Python program |
| `INV-001.txt`, `INV-002.txt`... | Individual invoice files |
| `invoice_history.csv` | Master record of all sales - opens in Excel |
| `invoice_count.txt` | Tracks next invoice number |
| `README.md` | Project documentation |

## 📸 Screenshots
Add screenshots of your terminal here showing:
1. Creating an invoice with GST calculation
2. Sample `INV-001.txt` output
3. `invoice_history.csv` opened in Excel
4. Invoice History menu output

## 📊 Sample Output
Made by #Vaishali with 💗
