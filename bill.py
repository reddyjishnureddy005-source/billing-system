import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
import json
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime, date
from num2words import num2words 
import os
import sys
import textwrap

# --- PORTABILITY HELPER ---
def get_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class BillingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("JAIMATHA DHI POLY PACKS - A4 Professional System")
        self.geometry("1200x850")
        self.edit_mode = False  
        self.init_db()

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.billing_tab = self.tabs.add("New/Edit Bill")
        self.records_tab = self.tabs.add("Past Transactions")
        
        self.setup_billing_ui()
        self.setup_records_ui()

    def init_db(self):
        with sqlite3.connect(get_path('billing_data.db')) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS invoices 
                         (bill_no TEXT PRIMARY KEY, customer TEXT, gst TEXT, state TEXT, date TEXT, total REAL, items_json TEXT)''')

    def handle_mutual_exclusion(self, event):
        gst_val = self.ent_gst.get().strip()
        state_val = self.ent_state.get().strip()
        if gst_val:
            self.ent_state.delete(0, 'end'); self.ent_state.configure(state="disabled")
            if len(gst_val) >= 2:
                try:
                    with sqlite3.connect(get_path('billing_data.db')) as conn:
                        res = conn.execute("SELECT customer FROM invoices WHERE gst=? ORDER BY rowid DESC LIMIT 1", (gst_val,)).fetchone()
                        if res and not self.ent_name.get(): self.ent_name.insert(0, res[0])
                except: pass
        elif state_val:
            self.ent_gst.delete(0, 'end'); self.ent_gst.configure(state="disabled")
        else:
            self.ent_gst.configure(state="normal"); self.ent_state.configure(state="normal")
        self.calculate_totals()

    def calculate_totals(self):
        try:
            gross = sum(float(self.tree.item(i)['values'][4]) for i in self.tree.get_children())
            gst_no = self.ent_gst.get().strip()
            state_val = self.ent_state.get().strip().upper()
            is_tn = gst_no.startswith("33") or state_val == "TN"
            self.lbl_gross.configure(text=f"Gross Value: ₹{gross:.2f}")
            self.lbl_grand.configure(text=f"Grand Total (Inc. 18% GST): ₹{round(gross * 1.18, 2):.2f}")
            return is_tn
        except: return False

    def add_item(self):
        try:
            n, p, q = self.cmb_item.get(), float(self.ent_price.get()), float(self.ent_qty.get())
            self.tree.insert("", "end", values=(len(self.tree.get_children())+1, n, f"{p:.2f}", f"{q} kg", f"{p*q:.2f}"))
            self.calculate_totals()
            self.ent_price.delete(0, 'end'); self.ent_qty.delete(0, 'end')
        except: messagebox.showerror("Error", "Invalid Entry")

    def remove_single_item(self):
        sel = self.tree.selection()
        if not sel: return
        for item in sel: self.tree.delete(item)
        for idx, item in enumerate(self.tree.get_children(), start=1):
            v = list(self.tree.item(item)['values']); v[0] = idx
            self.tree.item(item, values=v)
        self.calculate_totals()

    def clear_fields(self):
        self.edit_mode = False
        for entry in [self.ent_bill_no, self.ent_name, self.ent_gst, self.ent_state]:
            entry.configure(state="normal"); entry.delete(0, 'end')
        for i in self.tree.get_children(): self.tree.delete(i)
        self.lbl_gross.configure(text="Gross Value: ₹0.00"); self.lbl_grand.configure(text="Grand Total: ₹0.00")
        self.handle_mutual_exclusion(None)

    def save_and_pdf(self):
        bill_no, name = self.ent_bill_no.get().strip(), self.ent_name.get().strip()
        gst_in, st_code = self.ent_gst.get().strip(), self.ent_state.get().strip().upper()
        d_str = self.date_picker.get_date().strftime("%d-%m-%Y")
        
        if not bill_no or not name:
            messagebox.showwarning("Warning", "Bill No and Customer Name required.")
            return

        gross = sum(float(self.tree.item(i)['values'][4]) for i in self.tree.get_children())
        is_tn = self.calculate_totals()
        total = round(gross * 1.18, 2)
        items_json = json.dumps([self.tree.item(i)['values'] for i in self.tree.get_children()])

        try:
            words = num2words(total, lang='en_IN').title()
            rupees_text = f"Rupees {words} Only"
        except:
            rupees_text = "Rupees Conversion Error"

        try:
            c = canvas.Canvas(get_path(f"Bill_{bill_no}.pdf"), pagesize=A4); w, h = A4
            c.setLineWidth(1.5); c.rect(30, 30, w-60, h-60) 
            logo = get_path("logo.png")
            if os.path.exists(logo):
                c.drawImage(logo, 40, h-135, width=80, height=80, preserveAspectRatio=True, mask='auto')

            # HEADER
            c.setFont("Helvetica-Bold", 14); c.drawCentredString(w/2, h-45, "TAX INVOICE")
            c.setFont("Helvetica-Bold", 9)
            c.drawRightString(w-40, h-45, "Mobile : 94445 74221")
            c.drawRightString(w-40, h-58, "Mobile : 63690 90355")
            c.drawRightString(w-40, h-71, "Home : 94980 42665")

            c.setFont("Helvetica-Bold", 22); c.setFillColorRGB(0, 0.4, 0); c.drawCentredString(w/2, h-90, "JAIMATHA DHI POLY PACKS")
            c.setFillColorRGB(0,0,0); c.setFont("Helvetica-Bold", 10); c.drawCentredString(w/2, h-110, "GSTIN : 33ALEPC3938L1Z5")
            c.setFont("Helvetica-Oblique", 9); c.drawCentredString(w/2, h-125, "Mfr : HM, HD, LD Polythene Tubes, Bags, Sheet Roll")
            c.setFont("Helvetica", 9); c.drawCentredString(w/2, h-140, "No 5/10, S.V. KOIL STREET, MADDUR,"); c.drawCentredString(w/2, h-152, "Thiruvallur District, Pin - 631 206")

            # CUSTOMER INFO
            c.line(30, h-170, w-30, h-170)
            c.setFont("Helvetica-Bold", 12); c.drawString(45, h-200, f"M/s. {name}")
            c.setFont("Helvetica", 10); c.drawString(45, h-250, f"GSTIN : {gst_in if gst_in else st_code}")
            c.line(w-180, h-170, w-180, h-270) 
            c.setFont("Helvetica", 11); c.drawString(w-170, h-200, "Bill No. :"); c.setFont("Helvetica-Bold", 16); c.drawString(w-100, h-200, bill_no)
            c.setFont("Helvetica", 11); c.drawString(w-170, h-240, "Date :"); c.drawString(w-115, h-240, d_str)

            # TABLE
            table_bottom_y = h-580
            c.line(30, h-270, w-30, h-270); c.setFont("Helvetica-Bold", 11)
            c.drawString(45, h-295, "No."); c.drawString(85, h-295, "Description")
            c.drawString(w-160, h-290, "Kg."); c.drawString(w-115, h-290, "Rate"); c.drawString(w-70, h-290, "Amount")
            c.line(30, h-310, w-30, h-310)
            
            c.line(75, h-270, 75, table_bottom_y); c.line(w-175, h-270, w-175, table_bottom_y) 
            c.line(w-125, h-270, w-125, table_bottom_y - 120); c.line(w-80, h-270, w-80, table_bottom_y - 120)

            y = h-335
            c.setFont("Helvetica", 10)
            for item in self.tree.get_children():
                v = self.tree.item(item)['values']
                c.drawString(48, y, str(v[0])); c.drawString(85, y, str(v[1]))
                c.drawString(w-165, y, str(v[3]).replace(" kg","")); c.drawString(w-115, y, str(v[2])); c.drawRightString(w-40, y, str(v[4]))
                y -= 20
            
            c.setFont("Helvetica-Bold", 10); c.drawString(85, table_bottom_y + 15, "Vehicle Number: _________________")

            # TOTALS
            c.line(30, table_bottom_y, w-30, table_bottom_y)
            y_tot = table_bottom_y - 25
            c.setFont("Helvetica-Bold", 10)
            tax_list = [("TOTAL VALUE", gross), ("CGST - 9%", gross*0.09 if is_tn else 0), ("SGST - 9%", gross*0.09 if is_tn else 0), ("IGST - 18%", gross*0.18 if not is_tn else 0), ("GRAND TOTAL", total)]
            for lbl, val in tax_list:
                c.drawRightString(w-130, y_tot, lbl); c.drawRightString(w-40, y_tot, f"{val:.2f}")
                c.line(w-175, y_tot-5, w-30, y_tot-5); y_tot -= 20

            # FOOTER & BANK
            c.setFont("Helvetica-Bold", 9)
            c.drawString(45, table_bottom_y - 140, "A/C: 265711100000089")
            c.drawString(45, table_bottom_y - 155, "IFSC: UBIN0826570")
            c.drawString(45, table_bottom_y - 170, "Bank: UNION BANK, MADDUR")
            
            wrapped = textwrap.wrap(rupees_text, width=80)
            y_r = table_bottom_y - 195
            c.setFont("Helvetica-Bold", 10)
            for line in wrapped:
                c.drawString(45, y_r, line); y_r -= 15
            
            # --- UPDATED: SIGNATURE LINE MOVED DOWN ABOVE THE BORDER ---
            c.drawRightString(w-45, 45, "For JAI MATHA DHI POLY PACKS")
            c.save()

            with sqlite3.connect(get_path('billing_data.db')) as conn:
                if self.edit_mode: conn.execute("UPDATE invoices SET customer=?, gst=?, state=?, date=?, total=?, items_json=? WHERE bill_no=?", (name, gst_in, st_code, d_str, total, items_json, bill_no))
                else: conn.execute("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?)", (bill_no, name, gst_in, st_code, d_str, total, items_json))
            
            messagebox.showinfo("Success", f"Bill {bill_no} saved (A4)."); self.clear_fields(); self.refresh_history()
        except Exception as e: messagebox.showerror("System Error", str(e))

    def export_to_excel(self):
        try:
            with sqlite3.connect(get_path('billing_data.db')) as conn:
                df = pd.read_sql_query("SELECT bill_no, customer, gst, state, date, total FROM invoices", conn)
            fname = get_path(f"Report_{date.today()}.xlsx"); df.to_excel(fname, index=False); os.startfile(fname)
        except Exception as e: messagebox.showerror("Excel Error", str(e))

    def delete_transaction(self):
        sel = self.history_tree.selection()
        if not sel: return
        if messagebox.askyesno("Confirm", "Delete this bill?"):
            bid = self.history_tree.item(sel[0])['values'][0]
            with sqlite3.connect(get_path('billing_data.db')) as conn:
                conn.execute("DELETE FROM invoices WHERE bill_no=?", (str(bid),))
            self.refresh_history()

    def load_bill_for_editing(self):
        try:
            sel = self.history_tree.selection()
            if not sel: return
            bid = self.history_tree.item(sel[0])['values'][0]
            with sqlite3.connect(get_path('billing_data.db')) as conn:
                conn.row_factory = sqlite3.Row
                r = conn.execute("SELECT * FROM invoices WHERE bill_no=?", (str(bid),)).fetchone()
            if r:
                self.clear_fields(); self.edit_mode = True; self.ent_bill_no.configure(state="normal")
                self.ent_bill_no.insert(0, str(r['bill_no'])); self.ent_bill_no.configure(state="disabled") 
                self.ent_name.insert(0, str(r['customer'])); self.ent_gst.insert(0, str(r['gst'] if r['gst'] else ''))
                self.ent_state.insert(0, str(r['state'] if r['state'] else ''))
                items = json.loads(r['items_json'])
                for i in items: self.tree.insert("", "end", values=i)
                self.handle_mutual_exclusion(None); self.calculate_totals(); self.tabs.set("New/Edit Bill")
        except Exception as e: messagebox.showerror("Edit Error", str(e))

    def setup_billing_ui(self):
        sidebar = ctk.CTkFrame(self.billing_tab, width=300); sidebar.pack(side="left", fill="y", padx=10, pady=10)
        self.ent_bill_no = ctk.CTkEntry(sidebar, placeholder_text="Bill Number"); self.ent_bill_no.pack(pady=10, padx=20)
        self.ent_name = ctk.CTkEntry(sidebar, placeholder_text="Customer Name"); self.ent_name.pack(pady=10, padx=20)
        self.ent_gst = ctk.CTkEntry(sidebar, placeholder_text="GST No"); self.ent_gst.pack(pady=10, padx=20); self.ent_gst.bind("<KeyRelease>", self.handle_mutual_exclusion)
        self.ent_state = ctk.CTkEntry(sidebar, placeholder_text="State Code"); self.ent_state.pack(pady=10, padx=20); self.ent_state.bind("<KeyRelease>", self.handle_mutual_exclusion)
        self.date_picker = DateEntry(sidebar, width=15); self.date_picker.pack(pady=20)

        main = ctk.CTkFrame(self.billing_tab); main.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        item_f = ctk.CTkFrame(main); item_f.pack(fill="x", pady=10)
        self.cmb_item = ctk.CTkComboBox(item_f, values=["Bag", "Roll", "Tube"], width=200); self.cmb_item.pack(side="left", padx=5)
        self.ent_price = ctk.CTkEntry(item_f, placeholder_text="Rate", width=80); self.ent_price.pack(side="left", padx=5)
        self.ent_qty = ctk.CTkEntry(item_f, placeholder_text="Kg", width=80); self.ent_qty.pack(side="left", padx=5)
        ctk.CTkButton(item_f, text="ADD ITEM", width=100, command=self.add_item).pack(side="left", padx=5)

        self.tree = ttk.Treeview(main, columns=(1,2,3,4,5), show="headings")
        for i, h in enumerate(["#", "Description", "Rate", "Weight", "Total"], 1): self.tree.heading(i, text=h)
        self.tree.pack(fill="both", expand=True, pady=10)
        
        lbl_f = ctk.CTkFrame(main); lbl_f.pack(fill="x", pady=5)
        self.lbl_gross = ctk.CTkLabel(lbl_f, text="Gross: ₹0.00", font=("Arial", 14)); self.lbl_gross.pack(side="left", padx=20)
        self.lbl_grand = ctk.CTkLabel(lbl_f, text="Total: ₹0.00", font=("Arial", 22, "bold")); self.lbl_grand.pack(side="right", padx=20)
        
        btn_f = ctk.CTkFrame(main); btn_f.pack(fill="x", pady=10)
        ctk.CTkButton(btn_f, text="REMOVE ITEM", fg_color="red", command=self.remove_single_item).pack(side="left", padx=10)
        ctk.CTkButton(btn_f, text="CLEAR BILL", fg_color="gray", command=self.clear_fields).pack(side="left", padx=10)
        ctk.CTkButton(btn_f, text="SAVE & PRINT PDF", height=50, command=self.save_and_pdf).pack(side="right", expand=True, fill="x", padx=10)

    def setup_records_ui(self):
        self.history_tree = ttk.Treeview(self.records_tab, columns=(1,2,3,4,5,6), show="headings")
        for i, h in enumerate(["Bill", "Customer", "GST", "State", "Date", "Total"], 1): self.history_tree.heading(i, text=h)
        self.history_tree.pack(fill="both", expand=True, padx=10, pady=10)
        f = ctk.CTkFrame(self.records_tab); f.pack(fill="x", pady=10)
        ctk.CTkButton(f, text="EDIT TRANSACTION", fg_color="green", command=self.load_bill_for_editing).pack(side="left", padx=20)
        ctk.CTkButton(f, text="EXCEL REPORT", fg_color="#1D6F42", command=self.export_to_excel).pack(side="left", padx=20)
        ctk.CTkButton(f, text="REFRESH", command=self.refresh_history).pack(side="left", padx=20)
        ctk.CTkButton(f, text="DELETE", fg_color="red", command=self.delete_transaction).pack(side="right", padx=20)
        self.refresh_history()

    def refresh_history(self):
        for i in self.history_tree.get_children(): self.history_tree.delete(i)
        with sqlite3.connect(get_path('billing_data.db')) as conn:
            for r in conn.execute("SELECT bill_no, customer, gst, state, date, total FROM invoices ORDER BY rowid DESC"):
                self.history_tree.insert("", "end", values=r)

if __name__ == "__main__":
    app = BillingApp()
    app.mainloop()