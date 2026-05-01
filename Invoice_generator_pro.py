import datetime
import csv
import os

INVOICE_COUNTER_FILE = "invoice_count.txt"
INVOICE_HISTORY = "invoice_history.csv"

def get_next_invoice_no():
    if not os.path.exists(INVOICE_COUNTER_FILE):
        with open(INVOICE_COUNTER_FILE, "w") as f:
            f.write("1")
        return "INV-001"
    
    with open(INVOICE_COUNTER_FILE, "r") as f:
        count = int(f.read().strip())
    
    with open(INVOICE_COUNTER_FILE, "w") as f:
        f.write(str(count + 1))
    
    return f"INV-{count:03d}"

def save_to_csv(invoice_data):
    file_exists = os.path.isfile(INVOICE_HISTORY)
    with open(INVOICE_HISTORY, "a", newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Invoice_No", "Date", "Customer", "Phone", "Total", "GST", "Grand_Total"])
        writer.writerow(invoice_data)

def create_invoice():
    print("="*55)
    print(" SoftGrowTech INVOICE GENERATOR PRO")
    print("="*55)
    
    invoice_no = get_next_invoice_no()
    date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
    
    customer = input("Customer Name: ").strip()
    while not customer:
        customer = input("❌ Name required. Customer Name: ").strip()
    
    phone = input("Phone Number: ").strip()
    
    items = []
    total = 0
    
    print("\n--- ADD ITEMS ---")
    while True:
        name = input("\nItem name or 'done' to finish: ").strip()
        if name.lower() == 'done':
            if not items:
                print("❌ Add at least 1 item")
                continue
            break
            
        try:
            qty = int(input("Quantity: "))
            price = float(input("Price per item ₹: "))
            if qty <= 0 or price <= 0:
                print("❌ Qty and Price must be positive")
                continue
        except ValueError:
            print("❌ Enter valid numbers only")
            continue
            
        amount = round(qty * price, 2)
        items.append({"name": name, "qty": qty, "price": price, "amount": amount})
        total += amount
        print(f"✅ Added: {name} | Total so far: ₹{total:.2f}")
    
    try:
        discount = float(input("\nEnter discount % or 0: "))
        if discount < 0 or discount > 100:
            discount = 0
    except ValueError:
        discount = 0
    
    discount_amt = round(total * (discount / 100), 2)
    subtotal = round(total - discount_amt, 2)
    cgst = sgst = round(subtotal * 0.09, 2)
    gst_total = round(cgst + sgst, 2)
    grand_total = round(subtotal + gst_total, 2)
    
    # Display Invoice
    invoice_text = f"""

           SoftGrowTech - TAX INVOICE

Invoice No: {invoice_no} Date: {date}
Customer: {customer} Phone: {phone}

{'Item':<20} {'Qty':<6} {'Rate':<10} {'Amount':<10}

"""
    for item in items:
        invoice_text += f"{item['name']:<20} {item['qty']:<6} ₹{item['price']:<9.2f} ₹{item['amount']:<9.2f}\n"
    
    invoice_text += f"""--------------------------------------------------------
Subtotal:                               ₹{total:.2f}
Discount {discount}%:                        -₹{discount_amt:.2f}
Taxable Amount:                         ₹{subtotal:.2f}
CGST 9%:                                +₹{cgst:.2f}
SGST 9%:                                +₹{sgst:.2f}

GRAND TOTAL:                            ₹{grand_total:.2f}

        Thank you for your business!

"""
    
    print(invoice_text)
    
    # Save files
    txt_filename = f"{invoice_no}.txt"
    with open(txt_filename, "w", encoding="utf-8") as file:
        file.write(invoice_text)
    
    save_to_csv([invoice_no, date, customer, phone, total, gst_total, grand_total])
    
    print(f"✅ Invoice saved as {txt_filename}")
    print(f"✅ Record added to {INVOICE_HISTORY}")

def view_history():
    print("\n--- INVOICE HISTORY ---")
    if not os.path.exists(INVOICE_HISTORY):
        print("No invoices created yet")
        return
    
    with open(INVOICE_HISTORY, "r") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i == 0:
                print(f"{'No.':<4} {' | '.join(row)}")
                print("-" * 80)
            else:
                print(f"{i:<4} {' | '.join(row)}")

def main():
    while True:
        print("\n" + "="*40)
        print(" INVOICE SYSTEM MENU")
        print("="*40)
        choice = input("1. Create New Invoice\n2. View Invoice History\n3. Exit\nChoose: ")
        
        if choice == "1":
            create_invoice()
        elif choice == "2":
            view_history()
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
