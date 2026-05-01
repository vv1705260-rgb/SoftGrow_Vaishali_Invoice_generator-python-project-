import sqlite3
import datetime
import argparse
import logging
import smtplib
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dataclasses import dataclass
from typing import List, Optional

try:
    from fpdf import FPDF
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

# --- CONFIG ---
DB_NAME = "billing.db"
LOG_FILE = "billing.log"
CONFIG_FILE = "config.json"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config():
    default = {"company_name": "SoftGrowTech Solutions", "gst_number": "29ABCDE1234F1Z5",
               "email": "your_email@gmail.com", "email_pass": "your_app_password"}
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default, f, indent=4)
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

CONFIG = load_config()

@dataclass
class Product:
    id: int
    name: str
    price: float
    stock: int

@dataclass
class InvoiceItem:
    product_id: int
    name: str
    qty: int
    price: float

    @property
    def amount(self) -> float:
        return round(self.qty * self.price, 2)

class BillingDB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS products
                       (id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS invoices
                       (id INTEGER PRIMARY KEY, inv_no TEXT, date TEXT, customer TEXT,
                        phone TEXT, email TEXT, total REAL)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS invoice_items
                       (id INTEGER PRIMARY KEY, invoice_id INTEGER, product TEXT,
                        qty INTEGER, price REAL, amount REAL)''')
        self.conn.commit()

        # Add sample products if empty
        cur.execute("SELECT COUNT(*) FROM products")
        if cur.fetchone()[0] == 0:
            sample = [(1, "Laptop", 55000, 10), (2, "Mouse", 500, 50), (3, "Keyboard", 1200, 30)]
            cur.executemany("INSERT INTO products VALUES (?,?,?,?)", sample)
            self.conn.commit()

    def get_products(self) -> List[Product]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM products WHERE stock > 0")
        return [Product(*row) for row in cur.fetchall()]

    def update_stock(self, product_id: int, qty_sold: int):
        cur = self.conn.cursor()
        cur.execute("UPDATE products SET stock = stock -? WHERE id =?", (qty_sold, product_id))
        self.conn.commit()

    def save_invoice(self, inv_data: dict, items: List[InvoiceItem]) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO invoices (inv_no, date, customer, phone, email, total) VALUES (?,?,?,?,?,?)",
                    (inv_data['inv_no'], inv_data['date'], inv_data['customer'],
                     inv_data['phone'], inv_data['email'], inv_data['total']))
        inv_id = cur.lastrowid
        for item in items:
            cur.execute("INSERT INTO invoice_items (invoice_id, product, qty, price, amount) VALUES (?,?,?,?,?)",
                        (inv_id, item.name, item.qty, item.price, item.amount))
            self.update_stock(item.product_id, item.qty)
        self.conn.commit()
        logging.info(f"Invoice {inv_data['inv_no']} saved for {inv_data['customer']}")
        return inv_id

    def get_monthly_total(self) -> float:
        cur = self.conn.cursor()
        month = datetime.datetime.now().strftime("%m-%Y")
        cur.execute("SELECT SUM(total) FROM invoices WHERE strftime('%m-%Y', date) =?", (month,))
        result = cur.fetchone()[0]
        return result if result else 0.0

class InvoiceService:
    def __init__(self):
        self.db = BillingDB()
        self.gst_rate = 0.18

    def generate_inv_no(self) -> str:
        cur = self.db.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM invoices")
        count = cur.fetchone()[0] + 1
        return f"INV-{datetime.datetime.now().year}-{count:05d}"

    def create_invoice_cli(self):
        print("\n=== CREATE INVOICE ===")
        customer = input("Customer Name: ")
        phone = input("Phone: ")
        email = input("Email for sending invoice: ")

        products = self.db.get_products()
        print("\nAvailable Products:")
        for p in products:
            print(f"{p.id}. {p.name} - Rs{p.price} | Stock: {p.stock}")

        items = []
        while True:
            try:
                pid = int(input("\nEnter Product ID or 0 to finish: "))
                if pid == 0: break
                product = next((p for p in products if p.id == pid), None)
                if not product:
                    print("❌ Invalid ID"); continue
                qty = int(input(f"Qty for {product.name}: "))
                if qty > product.stock:
                    print(f"❌ Only {product.stock} in stock"); continue
                items.append(InvoiceItem(product.id, product.name, qty, product.price))
                print(f"✅ Added {qty} x {product.name}")
            except ValueError:
                print("❌ Enter numbers only")

        if not items:
            print("❌ No items added"); return

        subtotal = sum(item.amount for item in items)
        cgst = sgst = round(subtotal * 0.09, 2)
        total = round(subtotal + cgst + sgst, 2)
        inv_no = self.generate_inv_no()
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        inv_data = {"inv_no": inv_no, "date": date, "customer": customer,
                   "phone": phone, "email": email, "total": total}

        self.db.save_invoice(inv_data, items)
        pdf_file = self.generate_pdf(inv_data, items, cgst, sgst, subtotal)

        print(f"\n✅ Invoice {inv_no} Created. Total: Rs{total:.2f}")
        if email and pdf_file:
            send = input("Send invoice to customer email? y/n: ").lower()
            if send == 'y':
                self.send_email(email, pdf_file, inv_no)

    def generate_pdf(self, inv, items, cgst, sgst, subtotal) -> Optional[str]:
        if not PDF_ENABLED: return None
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, CONFIG['company_name'], ln=1, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, f"GST: {CONFIG['gst_number']}", ln=1, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(95, 8, f"Invoice: {inv['inv_no']}", 0, 0)
        pdf.cell(95, 8, f"Date: {inv['date'][:10]}", 0, 1)
        pdf.cell(0, 8, f"Bill To: {inv['customer']} | {inv['phone']}", 0, 1)
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 10)
        pdf.cell(90, 8, "Item", 1); pdf.cell(20, 8, "Qty", 1)
        pdf.cell(40, 8, "Rate", 1); pdf.cell(40, 8, "Amount", 1, ln=1)
        pdf.set_font("Arial", '', 10)
        for item in items:
            pdf.cell(90, 8, item.name, 1); pdf.cell(20, 8, str(item.qty), 1)
            pdf.cell(40, 8, f"{item.price:.2f}", 1); pdf.cell(40, 8, f"{item.amount:.2f}", 1, ln=1)

        pdf.ln(3)
        pdf.cell(150, 6, "Subtotal:", 0, 0, 'R'); pdf.cell(40, 6, f"{subtotal:.2f}", 0, 1)
        pdf.cell(150, 6, "CGST 9%:", 0, 0, 'R'); pdf.cell(40, 6, f"{cgst:.2f}", 0, 1)
        pdf.cell(150, 6, "SGST 9%:", 0, 0, 'R'); pdf.cell(40, 6, f"{sgst:.2f}", 0, 1)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(150, 8, "TOTAL:", 0, 0, 'R'); pdf.cell(40, 8, f"{inv['total']:.2f}", 0, 1)

        filename = f"{inv['inv_no']}.pdf"
        pdf.output(filename)
        return filename

    def send_email(self, to_email: str, pdf_path: str, inv_no: str):
        try:
            msg = MIMEMultipart()
            msg['From'] = CONFIG['email']
            msg['To'] = to_email
            msg['Subject'] = f"Invoice {inv_no} from {CONFIG['company_name']}"
            msg.attach(MIMEText(f"Dear Customer,\n\nPlease find attached invoice {inv_no}.\n\nThank you,\n{CONFIG['company_name']}", 'plain'))

            with open(pdf_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {pdf_path}')
                msg.attach(part)

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(CONFIG['email'], CONFIG['email_pass'])
            server.send_message(msg)
            server.quit()
            print(f"✅ Email sent to {to_email}")
            logging.info(f"Invoice {inv_no} emailed to {to_email}")
        except Exception as e:
            print(f"❌ Email failed: {e}. Check config.json and use Gmail App Password")
            logging.error(f"Email failed for {inv_no}: {e}")

def main():
    parser = argparse.ArgumentParser(description="SoftGrowTech Billing System")
    parser.add_argument('--report', choices=['monthly'], help='Generate reports')
    args = parser.parse_args()

    service = InvoiceService()

    if args.report == 'monthly':
        total = service.db.get_monthly_total()
        print(f"📊 Monthly Revenue: Rs {total:.2f}")
        return

    while True:
        print("\n" + "="*45)
        print(" SoftGrowTech - Enterprise Billing v3.0")
        print("="*45)
        choice = input("1. New Invoice\n2. View Products\n3. Monthly Report\n4. Exit\nChoose: ")
        if choice == "1": service.create_invoice_cli()
        elif choice == "2":
            for p in service.db.get_products():
                print(f"{p.id}. {p.name} - Rs{p.price} | Stock: {p.stock}")
        elif choice == "3":
            total = service.db.get_monthly_total()
            print(f"📊 This Month: Rs {total:.2f}")
        elif choice == "4": break

if __name__ == "__main__":
    main()
