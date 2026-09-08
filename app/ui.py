from __future__ import annotations

import csv
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from tkinter import filedialog, ttk, messagebox

from app.db import Database
from app.automation import AutomationManager, StudentTask
from app.render_manager import RenderManager


class JazanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("نظام أتمتة طلاب جيزان")
        self.geometry("1200x800")
        self.configure(bg="#f3f6fb")
        self._apply_professional_theme()
        self.db = Database()
        self.automation = AutomationManager()
        self.render_manager = RenderManager()

        self.program_var = tk.StringVar()
        self.section_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.selected_command_id = None

        self.render_status = None
        self.build_ui()
        self.load_render_config()
        self.load_programs()
        self.load_commands()
        self.check_render_status()

    def _apply_professional_theme(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background="#f3f6fb")
        style.configure("TLabel", background="#f3f6fb", foreground="#1f2937", font=("Segoe UI", 10))
        style.configure("TLabelFrame", background="#f3f6fb")
        style.configure("TLabelframe.Label", background="#f3f6fb", foreground="#111827", font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground="#ffffff", foreground="#111827")
        style.configure("TCombobox", fieldbackground="#ffffff", foreground="#111827")
        style.configure("TButton", padding=(10, 8), font=("Segoe UI", 10, "bold"))
        style.configure("Accent.TButton", background="#2563eb", foreground="#ffffff", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.configure("Sidebar.TButton", background="#1f2a44", foreground="#ffffff", padding=(10, 12), font=("Segoe UI", 10, "bold"))
        style.map("TButton", background=[("active", "#dbeafe"), ("pressed", "#bfdbfe")], foreground=[("active", "#111827")])
        style.map("Accent.TButton", background=[("active", "#1d4ed8"), ("pressed", "#1e40af")], foreground=[("active", "#ffffff")])
        style.map("Sidebar.TButton", background=[("active", "#30456e"), ("pressed", "#253754")], foreground=[("active", "#ffffff")])
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#1f2937", rowheight=28)
        style.configure("Treeview.Heading", background="#dfeafc", foreground="#111827", font=("Segoe UI", 10, "bold"))

    def build_ui(self):
        self.sidebar = tk.Frame(self, bg="#1f2a44", width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        self.logo_label = tk.Label(self.sidebar, text="JAZAN\nAutomation", bg="#1f2a44", fg="#ffffff", font=("Segoe UI", 16, "bold"), justify="center", pady=20)
        self.logo_label.pack(fill=tk.X)

        self.sidebar_buttons = []
        sidebar_items = [
            ("الرئيسية", "main"),
            ("الإعدادات", "settings"),
            ("الطلاب", "students"),
            ("Render", "render"),
        ]

        for text, value in sidebar_items:
            btn = tk.Button(
                self.sidebar,
                text=text,
                bg="#1f2a44",
                fg="#ffffff",
                activebackground="#30456e",
                activeforeground="#ffffff",
                bd=0,
                pady=12,
                font=("Segoe UI", 10, "bold"),
                command=lambda v=value: self.switch_section(v),
            )
            btn.pack(fill=tk.X, padx=10, pady=4)
            self.sidebar_buttons.append(btn)

        self.sidebar_footer = tk.Label(
            self.sidebar,
            text="حالة Render\nغير مهيأ",
            bg="#1f2a44",
            fg="#a7d8ff",
            font=("Segoe UI", 9),
            justify="center",
            pady=20,
        )
        self.sidebar_footer.pack(side=tk.BOTTOM, fill=tk.X)

        self.content = tk.Frame(self, bg="#f3f6fb")
        self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(self.content)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="الرئيسية")

        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="الإعدادات")

        ttk.Label(self.main_tab, text="لوحة تحكم نظام طلاب جيزان", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=10, pady=(10, 0))

        left = ttk.Frame(self.main_tab)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        right = ttk.Frame(self.main_tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        left.grid_columnconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ttk.Label(left, text="اسم التخصص:").grid(row=0, column=0, sticky="w")
        self.program_entry = ttk.Entry(left)
        self.program_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(left, text="إضافة تخصص", command=self.add_program).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(left, text="اسم الشعبة:").grid(row=1, column=0, sticky="w")
        self.section_entry = ttk.Entry(left)
        self.section_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(left, text="إضافة شعبة", command=self.add_section).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(left, text="تحديد التخصص:").grid(row=2, column=0, sticky="w")
        self.program_combo = ttk.Combobox(left, textvariable=self.program_var, state="readonly")
        self.program_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.program_combo.bind("<<ComboboxSelected>>", self.on_program_selected)

        ttk.Label(left, text="تحديد الشعبة:").grid(row=3, column=0, sticky="w")
        self.section_combo = ttk.Combobox(left, textvariable=self.section_var, state="readonly")
        self.section_combo.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(left, text="رابط المحاضرة:").grid(row=4, column=0, sticky="w")
        self.url_entry = ttk.Entry(left)
        self.url_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=5)

        ttk.Button(left, text="تشغيل الأتمتة", command=self.run_automation, style="Accent.TButton").grid(row=5, column=1, sticky="ew", padx=5, pady=10)

        ttk.Label(right, text="إضافة طالب").pack(anchor="w")
        self.student_fields = {}
        for index, field in enumerate([("الاسم", "full_name"), ("الرقم الجامعي", "university_id"), ("الهوية", "national_id")]):
            ttk.Label(right, text=field[0]).pack(anchor="w")
            entry = ttk.Entry(right)
            entry.pack(fill=tk.X, padx=5, pady=3)
            self.student_fields[field[1]] = entry

        ttk.Button(right, text="حفظ طالب", command=self.add_student).pack(fill=tk.X, padx=5, pady=10)

        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=8)

        ttk.Label(right, text="إضافة قائمة الطلاب (اسم في سطر)").pack(anchor="w")
        self.bulk_names_text = tk.Text(right, height=8)
        self.bulk_names_text.pack(fill=tk.BOTH, expand=False, padx=5, pady=3)

        ttk.Label(right, text="إضافة قائمة الارقام الجامعية/الهوية (رقم في سطر)").pack(anchor="w")
        self.bulk_ids_text = tk.Text(right, height=8)
        self.bulk_ids_text.pack(fill=tk.BOTH, expand=False, padx=5, pady=3)

        ttk.Button(right, text="إضافة قائمة الطلاب", command=self.add_bulk_students).pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(right, text="تصدير الطلاب إلى CSV", command=self.export_students_to_csv).pack(fill=tk.X, padx=5, pady=3)
        ttk.Button(right, text="استيراد الطلاب من CSV", command=self.import_students_from_csv).pack(fill=tk.X, padx=5, pady=3)

        ttk.Label(right, text="سجل العمليات").pack(anchor="w", pady=(10, 3))
        self.log_text = tk.Text(right, height=6)
        self.log_text.pack(fill=tk.BOTH, expand=False, padx=5, pady=3)

        self.students_tree = ttk.Treeview(right, columns=("name", "university_id", "national_id", "program", "section"), show="headings")
        self.students_tree.heading("name", text="الاسم")
        self.students_tree.heading("university_id", text="الرقم الجامعي")
        self.students_tree.heading("national_id", text="الهوية")
        self.students_tree.heading("program", text="التخصص")
        self.students_tree.heading("section", text="الشعبة")
        self.students_tree.pack(fill=tk.BOTH, expand=True)
        self.load_students()

        ttk.Label(self.settings_tab, text="إدارة أوامر الأتمتة").pack(anchor="w", padx=10, pady=10)
        self.command_frame = ttk.Frame(self.settings_tab)
        self.command_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.command_name = ttk.Entry(self.command_frame)
        self.command_name.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Label(self.command_frame, text="اسم الأمر").grid(row=0, column=1)

        self.command_type = ttk.Combobox(self.command_frame, values=["fill", "click", "wait", "open_url"], state="readonly")
        self.command_type.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Label(self.command_frame, text="نوع الأمر").grid(row=1, column=1)

        self.selector_type = ttk.Combobox(self.command_frame, values=["css", "xpath", "id", "name", "class"], state="readonly")
        self.selector_type.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        ttk.Label(self.command_frame, text="نوع المحدد").grid(row=2, column=1)

        self.selector_value = ttk.Entry(self.command_frame)
        self.selector_value.grid(row=3, column=0, padx=5, pady=5, sticky="ew")
        ttk.Label(self.command_frame, text="قيمة المحدد").grid(row=3, column=1)

        self.value_template = ttk.Entry(self.command_frame)
        self.value_template.grid(row=4, column=0, padx=5, pady=5, sticky="ew")
        ttk.Label(self.command_frame, text="قيمة الإدخال/القالب").grid(row=4, column=1)

        self.wait_seconds = ttk.Entry(self.command_frame)
        self.wait_seconds.grid(row=5, column=0, padx=5, pady=5, sticky="ew")
        ttk.Label(self.command_frame, text="انتظار (ثانية)").grid(row=5, column=1)

        self.order_index = ttk.Entry(self.command_frame)
        self.order_index.grid(row=6, column=0, padx=5, pady=5, sticky="ew")
        ttk.Label(self.command_frame, text="ترتيب التنفيذ").grid(row=6, column=1)

        ttk.Button(self.command_frame, text="حفظ الأمر", command=self.add_command).grid(row=7, column=0, columnspan=2, sticky="ew", padx=5, pady=10)

        self.commands_tree = ttk.Treeview(self.settings_tab, columns=("id", "name", "type", "selector_type", "selector_value", "value_template", "wait", "order"), show="headings")
        self.commands_tree["displaycolumns"] = ("name", "type", "selector_type", "selector_value", "value_template", "wait", "order")
        self.commands_tree.heading("name", text="الاسم")
        self.commands_tree.heading("type", text="النوع")
        self.commands_tree.heading("selector_type", text="نوع المحدد")
        self.commands_tree.heading("selector_value", text="قيمة المحدد")
        self.commands_tree.heading("value_template", text="القيمة")
        self.commands_tree.heading("wait", text="الانتظار")
        self.commands_tree.heading("order", text="الترتيب")
        self.commands_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.commands_tree.bind("<<TreeviewSelect>>", self.on_command_selected)

        ttk.Button(self.settings_tab, text="تحديث الأمر المحدد", command=self.add_command).pack(anchor="e", padx=10, pady=(0, 5))
        ttk.Button(self.settings_tab, text="حذف الأمر المحدد", command=self.delete_command).pack(anchor="e", padx=10, pady=(0, 10))

        self.render_frame = ttk.LabelFrame(self.settings_tab, text="حالة Render")
        self.render_frame.pack(fill=tk.X, padx=10, pady=10)
        self.render_label = ttk.Label(self.render_frame, text="جاري التحقق من حالة Render...", wraplength=700, justify="right")
        self.render_label.pack(fill=tk.X, padx=10, pady=10)

        self.render_config_frame = ttk.LabelFrame(self.settings_tab, text="إعدادات Render")
        self.render_config_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(self.render_config_frame, text="service_id").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.render_service_id_entry = ttk.Entry(self.render_config_frame)
        self.render_service_id_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(self.render_config_frame, text="api_key").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.render_api_key_entry = ttk.Entry(self.render_config_frame, show="*")
        self.render_api_key_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(self.render_config_frame, text="api_base_url").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.render_api_base_url_entry = ttk.Entry(self.render_config_frame)
        self.render_api_base_url_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        self.render_config_frame.columnconfigure(1, weight=1)

        ttk.Button(self.render_config_frame, text="حفظ إعدادات Render", command=self.save_render_config).grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        ttk.Button(self.render_config_frame, text="تحديث حالة Render", command=self.check_render_status).grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def load_render_config(self):
        config = self.render_manager.load_config()
        self.render_service_id_entry.delete(0, tk.END)
        self.render_api_key_entry.delete(0, tk.END)
        self.render_api_base_url_entry.delete(0, tk.END)

        self.render_service_id_entry.insert(0, config.get("service_id", ""))
        self.render_api_key_entry.insert(0, config.get("api_key", ""))
        self.render_api_base_url_entry.insert(0, config.get("api_base_url", "https://api.render.com/v1/services"))

    def save_render_config(self):
        current = self.render_manager.load_config()
        current["service_id"] = self.render_service_id_entry.get().strip()
        current["api_key"] = self.render_api_key_entry.get().strip()
        current["api_base_url"] = self.render_api_base_url_entry.get().strip() or "https://api.render.com/v1/services"
        self.render_manager.save_config(current)
        self.log("تم حفظ إعدادات Render بنجاح")
        self.check_render_status()

    def switch_section(self, section):
        if section == "main":
            self.notebook.select(self.main_tab)
        elif section == "settings":
            self.notebook.select(self.settings_tab)
        elif section == "students":
            self.notebook.select(self.main_tab)
            self.focus_set()
        elif section == "render":
            self.notebook.select(self.settings_tab)
            self.render_config_frame.focus_set()

    def check_render_status(self):
        self.render_status = self.render_manager.get_service_status()
        message = self.render_status.get("message", "")
        self.render_label.config(text=message)
        status_text = "مفعّل" if self.render_status.get("can_start") else "غير مهيأ"
        self.sidebar_footer.config(text=f"حالة Render\n{status_text}")

        if self.render_status.get("can_start") is False:
            self.notebook.tab(0, state="disabled")
            self.notebook.tab(1, state="disabled")
            self.render_label.config(foreground="red")
            self.after(10000, self.check_render_status)
        else:
            self.notebook.tab(0, state="normal")
            self.notebook.tab(1, state="normal")
            self.render_label.config(foreground="green")

    def load_programs(self):
        programs = self.db.list_programs()
        choices = [row[1] for row in programs]
        self.program_combo["values"] = choices
        if choices:
            self.program_var.set(choices[0])
            self.on_program_selected()

    def on_program_selected(self, event=None):
        program_name = self.program_var.get()
        program_id = self._find_program_id(program_name)
        sections = self.db.list_sections(program_id)
        self.section_combo["values"] = [row[2] for row in sections]
        if sections:
            self.section_var.set(sections[0][2])

    def _find_program_id(self, name):
        for row in self.db.list_programs():
            if row[1] == name:
                return row[0]
        return None

    def _find_section_id(self, program_id, name):
        for row in self.db.list_sections(program_id):
            if row[2] == name:
                return row[0]
        return None

    def add_program(self):
        name = self.program_entry.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "يرجى إدخال اسم التخصص")
            return
        self.db.add_program(name)
        self.program_entry.delete(0, tk.END)
        self.load_programs()

    def add_section(self):
        program_name = self.program_var.get()
        section_name = self.section_entry.get().strip()
        if not program_name or not section_name:
            messagebox.showwarning("تنبيه", "يرجى اختيار تخصص وإدخال اسم الشعبة")
            return
        program_id = self._find_program_id(program_name)
        self.db.add_section(program_id, section_name)
        self.section_entry.delete(0, tk.END)
        self.on_program_selected()

    def add_student(self):
        program_name = self.program_var.get()
        section_name = self.section_var.get()
        data = {key: entry.get().strip() for key, entry in self.student_fields.items()}
        if not all([program_name, section_name, data["full_name"]]):
            messagebox.showwarning("تنبيه", "يرجى ملء الحقول الأساسية")
            return
        program_id = self._find_program_id(program_name)
        section_id = self._find_section_id(program_id, section_name)
        self.db.add_student(data["full_name"], data.get("university_id", ""), data.get("national_id", ""), program_id, section_id)
        self.load_students()
        messagebox.showinfo("نجاح", "تم حفظ الطالب بنجاح")

    def add_bulk_students(self):
        program_name = self.program_var.get()
        section_name = self.section_var.get()
        if not program_name or not section_name:
            messagebox.showwarning("تنبيه", "يرجى تحديد التخصص والشعبة أولاً")
            return

        names = self._parse_bulk_names(self.bulk_names_text.get("1.0", tk.END))
        ids = self._parse_bulk_ids(self.bulk_ids_text.get("1.0", tk.END))

        if not names:
            messagebox.showwarning("تنبيه", "يرجى إدخال أسماء الطلاب واحدة في كل سطر")
            return

        if ids and len(ids) != len(names):
            messagebox.showwarning(
                "تنبيه",
                f"عدد الأسماء ({len(names)}) لا يساوي عدد الارقام ({len(ids)}). سيتم حفظ أول {min(len(names), len(ids))} طالب فقط.",
            )

        program_id = self._find_program_id(program_name)
        section_id = self._find_section_id(program_id, section_name)

        saved_count = 0
        max_count = min(len(names), len(ids)) if ids else len(names)

        for index in range(max_count):
            cleaned_name = names[index]
            cleaned_id = ids[index] if ids else ""
            self.db.add_student(cleaned_name, cleaned_id, "", program_id, section_id)
            saved_count += 1

        if not ids:
            messagebox.showwarning("تنبيه", "تم حفظ الأسماء فقط لأن قائمة الارقام كانت فارغة. يمكنك إدخال الأرقام لاحقاً من خلال نموذج الطالب الفردي.")

        self.load_students()
        messagebox.showinfo("نجاح", f"تم حفظ {saved_count} طالب بنجاح")

    def _parse_bulk_names(self, text):
        lines = []
        for raw_line in text.splitlines():
            cleaned = " ".join(raw_line.strip().split())
            if cleaned:
                lines.append(cleaned)
        return lines

    def _parse_bulk_ids(self, text):
        lines = []
        for raw_line in text.splitlines():
            cleaned = "".join(char for char in raw_line.strip() if char.isalnum())
            if cleaned:
                lines.append(cleaned)
        return lines

    def export_students_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        rows = self.db.list_students()
        with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["name", "university_id", "national_id", "program", "section"])
            for row in rows:
                writer.writerow([row[1], row[2], row[3], row[6], row[7]])

        self.log(f"تم تصدير {len(rows)} طالب إلى ملف CSV")
        messagebox.showinfo("نجاح", f"تم تصدير {len(rows)} طالب بنجاح")

    def import_students_from_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        program_name = self.program_var.get()
        section_name = self.section_var.get()
        if not program_name or not section_name:
            messagebox.showwarning("تنبيه", "يرجى تحديد التخصص والشعبة أولاً")
            return

        program_id = self._find_program_id(program_name)
        section_id = self._find_section_id(program_id, section_name)

        imported_count = 0
        with open(file_path, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                name = (row.get("name") or "").strip()
                university_id = (row.get("university_id") or "").strip()
                national_id = (row.get("national_id") or "").strip()
                if not name:
                    continue
                self.db.add_student(name, university_id, national_id, program_id, section_id)
                imported_count += 1

        self.load_students()
        self.log(f"تم استيراد {imported_count} طالب من CSV")
        messagebox.showinfo("نجاح", f"تم استيراد {imported_count} طالب بنجاح")

    def load_students(self):
        self.students_tree.delete(*self.students_tree.get_children())
        rows = self.db.list_students()
        for row in rows:
            self.students_tree.insert("", tk.END, values=(row[1], row[2], row[3], row[6], row[7]))

    def on_command_selected(self, event=None):
        selection = self.commands_tree.selection()
        if not selection:
            return

        values = self.commands_tree.item(selection[0], "values")
        self.selected_command_id = values[0]

        self.command_name.delete(0, tk.END)
        self.command_name.insert(0, values[1])
        self.command_type.set(values[2])
        self.selector_type.set(values[3])
        self.selector_value.delete(0, tk.END)
        self.selector_value.insert(0, values[4])
        self.value_template.delete(0, tk.END)
        self.value_template.insert(0, values[5] or "")
        self.wait_seconds.delete(0, tk.END)
        self.wait_seconds.insert(0, values[6])
        self.order_index.delete(0, tk.END)
        self.order_index.insert(0, values[7])

    def reset_command_form(self):
        self.selected_command_id = None
        for widget in [self.command_name, self.command_type, self.selector_type, self.selector_value, self.value_template, self.wait_seconds, self.order_index]:
            if isinstance(widget, ttk.Combobox):
                widget.set("")
            else:
                widget.delete(0, tk.END)

    def add_command(self):
        data = {
            "name": self.command_name.get().strip(),
            "command_type": self.command_type.get(),
            "selector_type": self.selector_type.get(),
            "selector_value": self.selector_value.get().strip(),
            "value_template": self.value_template.get().strip() or None,
            "wait_seconds": float(self.wait_seconds.get() or 0),
            "order_index": int(self.order_index.get() or 0),
        }
        if not all([data["name"], data["command_type"], data["selector_type"], data["selector_value"]]):
            messagebox.showwarning("تنبيه", "يرجى إكمال جميع الحقول المطلوبة")
            return

        if self.selected_command_id is not None:
            self.db.update_command(self.selected_command_id, **data)
            messagebox.showinfo("نجاح", "تم تحديث الأمر بنجاح")
        else:
            self.db.add_command(**data)
            messagebox.showinfo("نجاح", "تم حفظ الأمر بنجاح")

        self.reset_command_form()
        self.load_commands()

    def delete_command(self):
        if self.selected_command_id is None:
            messagebox.showwarning("تنبيه", "يرجى اختيار الأمر المراد حذفه أولاً")
            return

        result = messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف الأمر المحدد؟")
        if result:
            self.db.delete_command(self.selected_command_id)
            self.reset_command_form()
            self.load_commands()
            messagebox.showinfo("نجاح", "تم حذف الأمر بنجاح")

    def load_commands(self):
        self.commands_tree.delete(*self.commands_tree.get_children())
        rows = self.db.list_commands()
        for row in rows:
            self.commands_tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))

    def run_automation(self):
        program_name = self.program_var.get()
        section_name = self.section_var.get()
        lecture_url = self.url_entry.get().strip()

        if not program_name or not section_name or not lecture_url:
            messagebox.showwarning("تنبيه", "يرجى اختيار التخصص والشعبة وإدخال رابط المحاضرة")
            return

        program_id = self._find_program_id(program_name)
        section_id = self._find_section_id(program_id, section_name)
        students = self.db.list_students(program_id, section_id)

        if not students:
            messagebox.showwarning("تنبيه", "لا يوجد طلاب في هذا التخصص والشعبة")
            return

        commands = self.db.list_commands()
        commands_payload = [
            {
                "name": row[1],
                "command_type": row[2],
                "selector_type": row[3],
                "selector_value": row[4],
                "value_template": row[5],
                "wait_seconds": row[6],
                "order_index": row[7],
            }
            for row in commands
        ]

        def run_student(student_row):
            task = StudentTask(
                full_name=student_row[1],
                university_id=student_row[2],
                national_id=student_row[3],
                program_name=program_name,
                section_name=section_name,
            )
            self.log(f"بدء تنفيذ الأتمتة للطالب: {task.full_name}")
            self.automation.run_commands(task, commands_payload, lecture_url)
            self.log(f"تمت الأتمتة بنجاح للطالب: {task.full_name}")

        max_workers = min(len(students), 5)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            list(executor.map(run_student, students))

        self.log(f"تم تنفيذ الأتمتة على {len(students)} طالب")
        messagebox.showinfo("نجاح", f"تم تنفيذ الأتمتة على {len(students)} طالب")


if __name__ == "__main__":
    app = JazanApp()
    app.mainloop()
