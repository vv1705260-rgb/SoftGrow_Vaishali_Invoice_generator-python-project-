import json
import datetime
import os
from typing import List, Dict

try:
    from fpdf import FPDF
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False
    print("⚠️ Install fpdf to enable PDF export: pip install fpdf")

class Item:
    def __init__(self, name: str, qty: int, price: float):
        self.name = name
        self.qty = qty
        self.price = price
        self.amount = round(qty * price, 2)

    def to_dict(self):
        return {"name": self.name, "qty": self.qty, "price": self.price, "amount": self.amount}

class Customer:
    def __init__(self, name: str, phone: str, email: str = ""):
        self.name = name
        self.phone = phone
        self.email = email

    def to_dict(self):
        return {"name": self.name, "phone": self.phone, "email": self.email}

class InvoiceSystem:
    def __init__(self, db_file="invoices.json"):
        self.db_file = db_file
        self.invoices = self.load_invoices()
        self.company = "SoftGrowTech Solutions"
        self.gst_rate = 0.18

    def load_invoices(self) -> List[Dict]:
        if not os.path.exists(self.db_file):
            return []
        try:
            with open(self.db_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def save_invoices(self):
        with open(self.db_file, "w") as f:
            json.dump(self.invoices, f, indent=4)

    def generate_invoice_no(self) -> str:
        year = datetime.datetime.now().year
        count = len(self.invoices) + 1
        return f"INV-{year}-{count:04d}"

    def calculate_tax(self, subtotal: float) -> Dict:
        gst_total = round(subtotal * self.gst_rate, 2)
        cgst = round(gst_total / 2, 2)
        sgst = round(gst_total / 2, 2)
        return {"cgst": cgst, "sgst": sgst, "total_gst": gst_total}

    def create_invoice(self):
        print("\n" + "="*50)
        print(" CREATE NEW INVOICE")
        print("="*50)

        c_name = input("Customer Name: ").strip()
        c_phone = input("Phone: ").strip()
        c_email = input("Email (optional): ").strip()
        customer = Customer(c_name, c_phone, c_email)

        items = []
        while True:
            name = input("\nItem name or 'done' to finish: ").strip()
            if name.lower() == 'done':
                if not items:
                    print("❌ Add at least 1 item")
                    continue
                break
            try:
                qty = int(input("Quantity: "))
                price = float(input("Rate ₹: "))
                if qty <= 0 or price <= 0:
                    print("❌ Qty and Rate must be positive")
                    continue
                items.append(Item(name, qty, price))
            except ValueError:
                print("❌ Enter valid numbers")

        discount_percent = 0
        try:
            discount_percent = float(input("\nDiscount % or 0: "))
        except ValueError:
            discount_percent = 0

        subtotal = sum(item.amount for item in items)
        discount_amt = round(subtotal * (discount_percent / 100), 2)
        taxable = subtotal - discount_amt
        tax = self.calculate_tax(taxable)
        grand_total = round(taxable + tax["total_gst"], 2)

        invoice = {
            "invoice_no": self.generate_invoice_no(),
            "date": str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M")),
            "company": self.company,
            "customer": customer.to_dict(),
            "items": [item.to_dict() for item in items],
            "subtotal": round(subtotal, 2),
            "discount_percent": discount_percent,
            "discount_amt": discount_amt,
            "tax": tax,
            "grand_total": grand_total
        }

        self.invoices.append(invoice)
        self.save_invoices()
        self.display_invoice(invoice)

        if PDF_ENABLED:
            choice = input("\nExport to PDF? y/n: ").lower()
            if choice == 'y':
                self.export_pdf(invoice)

    def display_invoice(self, inv: Dict):
        print("\n" + "="*60)
        print(f" {inv['company']} - TAX INVOICE")
        print("="*60)
        print(f"Invoice No: {inv['invoice_no']} Date: {inv['date']}")
        print(f"Customer: {inv['customer']['name']} | {inv['customer']['phone']}")
        print("-"*60)
        print(f"{'Item':<20} {'Qty':<6} {'Rate':<10} {'Amount':<10}")
        print("-"*60)
        for item in inv['items']:
            print(f"{item['name']:<20} {item['qty']:<6} ₹{item['price']:<9.2f} ₹{item['amount']:<9.2f}")
        print("-"*60)
        print(f"{'Subtotal:':<40} ₹{inv['subtotal']:.2f}")
        print(f"{'Discount ' + str(inv['discount_percent'])+'%:':<40} -₹{inv['discount_amt']:.2f}")
        print(f"{'CGST 9%:':<40} +₹{inv['tax']['cgst']:.2f}")
        print(f"{'SGST 9%:':<40} +₹{inv['tax']['sgst']:.2f}")
        print("-"*60)
        print(f"{'GRAND TOTAL:':<40} ₹{inv['grand_total']:.2f}")
        print("="*60)

    def export_pdf(self, inv: Dict):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, inv['company'], ln=True, align='C')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "TAX INVOICE", ln=True, align='C')
        pdf.ln(5)

        pdf.set_font("Arial", '', 10)
        pdf.cell(95, 6, f"Invoice No: {inv['invoice_no']}", ln=0)
        pdf.cell(95, 6, f"Date: {inv['date']}", ln=1)
        pdf.cell(0, 6, f"Bill To: {inv['customer']['name']} | {inv['customer']['phone']}", ln=1)
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 10)
        pdf.cell(80, 8, "Item", 1)
        pdf.cell(20, 8, "Qty", 1)
        pdf.cell(40, 8, "Rate", 1)
        pdf.cell(40, 8, "Amount", 1, ln=1)

        pdf.set_font("Arial", '', 10)
        for item in inv['items']:
            pdf.cell(80, 8, item['name'], 1)
            pdf.cell(20, 8, str(item['qty']), 1)
            pdf.cell(40, 8, f"Rs {item['price']:.2f}", 1)
            pdf.cell(40, 8, f"Rs {item['amount']:.2f}", 1, ln=1)

        pdf.ln(5)
        pdf.cell(140, 6, "Subtotal:", align='R')
        pdf.cell(40, 6, f"Rs {inv['subtotal']:.2f}", ln=1)
        pdf.cell(140, 6, f"Discount {inv['discount_percent']}%:", align='R')
        pdf.cell(40, 6, f"-Rs {inv['discount_amt']:.2f}", ln=1)
        pdf.cell(140, 6, "CGST 9%:", align='R')
        pdf.cell(40, 6, f"+Rs {inv['tax']['cgst']:.2f}", ln=1)
        pdf.cell(140, 6, "SGST 9%:", align='R')
        pdf.cell(40, 6, f"+Rs {inv['tax']['sgst']:.2f}", ln=1)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(140, 8, "GRAND TOTAL:", align='R')
        pdf.cell(40, 8, f"Rs {inv['grand_total']:.2f}", ln=1)

        filename = f"{inv['invoice_no']}.pdf"
        pdf.output(filename)
        print(f"✅ PDF saved as {filename}")

    def view_all_invoices(self):
        print("\n--- ALL INVOICES ---")
        if not self.invoices:
            print("No invoices found")
            return
        print(f"{'No.':<4} {'Invoice No':<15} {'Customer':<20} {'Date':<18} {'Total'}")
        print("-" * 70)
        for i, inv in enumerate(self.invoices, 1):
            print(f"{i:<4} {inv['invoice_no']:<15} {inv['customer']['name']:<20} {inv['date']:<18} ₹{inv['grand_total']:.2f}")

    def search_invoice(self):
        query = input("\nEnter Invoice No or Customer Name: ").strip().lower()
        found = [inv for inv in self.invoices if query in inv['invoice_no'].lower() or query in inv['customer']['name'].lower()]

        if not found:
            print("❌ No invoice found")
            return
        for inv in found:
            self.display_invoice(inv)

    def run(self):
        while True:
            print("\n" + "="*50)
            print(" SoftGrowTech - Invoice Generator v2.0")
            print("="*50)
            choice = input("1. Create Invoice\n2. View All Invoices\n3. Search Invoice\n4. Exit\nChoose: ")
            try:
                if choice == "1": self.create_invoice()
                elif choice == "2": self.view_all_invoices()
                elif choice == "3": self.search_invoice()
                elif choice == "4":
                    print("Exiting. All data saved.")
                    break
                else: print("❌ Invalid choice")
            except KeyboardInterrupt:
                print("\n⚠️ Operation cancelled")
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    system = InvoiceSystem()
    system.run()
