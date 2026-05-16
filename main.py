"""
Система учёта посещаемости образовательных курсов.
Логин по умолчанию: admin / admin123
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import calendar as _cal

from database import Database
from prediction import linear_regression, predict

import os

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LOGO_PATH = os.path.join(_BASE_DIR, "logo_greenstreet.webp")


# ── Цветовая палитра ──────────────────────────────────────
CLR_PRIMARY     = "#2E7D32"   # тёмно-зелёный
CLR_PRIMARY_DK  = "#1B5E20"   # очень темно-зеленый
CLR_ACCENT      = "#3BC337"   # яркий зелёный для выделения
CLR_ACCENT_DK   = "#2EA32A"   # немного темнее для выделения
CLR_BG          = "#EFF5EF"   # фон
CLR_WHITE       = "#FFFFFF"
CLR_TEXT        = "#1A1A1A"


# ═══════════════════════════════════════════════════════════
#  Главное окно приложения
# ═══════════════════════════════════════════════════════════

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Система учёта посещаемости")
        self._setup_theme()
        self.db = Database()
        if not self.db.connect():
            messagebox.showerror(
                "Ошибка",
                "Не удалось подключиться к MySQL.\n"
                "Убедитесь, что сервер запущен, и проверьте\n"
                "настройки DB_CONFIG в database.py.",
            )
            self.destroy()
            return
        self.user = None
        self._show_login()

    # ── Тема ──────────────────────────────────────────────
    def _setup_theme(self):
        self.configure(bg=CLR_BG)
        s = ttk.Style(self)
        s.theme_use("clam")

        # база
        s.configure(".", background=CLR_BG, foreground=CLR_TEXT,
                    font=("Segoe UI", 10))
        s.configure("TFrame", background=CLR_BG)
        s.configure("TLabel", background=CLR_BG, foreground=CLR_TEXT)

        # кнопки
        s.configure("TButton", background=CLR_ACCENT, foreground=CLR_WHITE,
                    padding=(12, 4), font=("Segoe UI", 10, "bold"),
                    borderwidth=0)
        s.map("TButton",
              background=[("active", CLR_ACCENT_DK), ("pressed", "#259022")])

        # вкладки Notebook
        s.configure("TNotebook", background=CLR_BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=CLR_PRIMARY,
                    foreground=CLR_WHITE, padding=(16, 6),
                    font=("Segoe UI", 10, "bold"))
        s.map("TNotebook.Tab",
              background=[("selected", CLR_ACCENT)],
              foreground=[("selected", CLR_WHITE)])

        # Treeview
        s.configure("Treeview", background=CLR_WHITE, foreground=CLR_TEXT,
                    rowheight=26, fieldbackground=CLR_WHITE,
                    font=("Segoe UI", 10))
        s.configure("Treeview.Heading", background=CLR_PRIMARY,
                    foreground=CLR_WHITE, font=("Segoe UI", 10, "bold"),
                    borderwidth=0)
        s.map("Treeview.Heading",
              background=[("active", CLR_PRIMARY_DK)])
        s.map("Treeview",
              background=[("selected", CLR_ACCENT)],
              foreground=[("selected", CLR_WHITE)])

        # LabelFrame
        s.configure("TLabelframe", background=CLR_BG,
                    bordercolor=CLR_PRIMARY, borderwidth=2)
        s.configure("TLabelframe.Label", background=CLR_BG,
                    foreground=CLR_PRIMARY, font=("Segoe UI", 10, "bold"))

        # поля ввода
        s.configure("TEntry", fieldbackground=CLR_WHITE)
        s.configure("TCombobox", fieldbackground=CLR_WHITE)
        s.map("TCombobox",
              fieldbackground=[("readonly", CLR_WHITE)])

        # чекбоксы
        s.configure("TCheckbutton", background=CLR_BG)

        # полоса прокрутки
        s.configure("Vertical.TScrollbar",
                    background=CLR_PRIMARY, troughcolor="#D4E8D4",
                    borderwidth=0, arrowcolor=CLR_WHITE)
        s.map("Vertical.TScrollbar",
              background=[("active", CLR_PRIMARY_DK)])

        # ── именованные стили ──
        s.configure("Header.TFrame", background=CLR_PRIMARY)
        s.configure("Header.TLabel", background=CLR_PRIMARY,
                    foreground=CLR_WHITE, font=("Segoe UI", 11))
        s.configure("Header.TButton", background=CLR_ACCENT,
                    foreground=CLR_WHITE, font=("Segoe UI", 10, "bold"),
                    borderwidth=0, padding=(14, 4))
        s.map("Header.TButton",
              background=[("active", CLR_ACCENT_DK)])

        s.configure("Title.TLabel", background=CLR_BG,
                    foreground=CLR_PRIMARY, font=("Segoe UI", 16, "bold"))

        # экран входа
        s.configure("Login.TFrame", background=CLR_WHITE)
        s.configure("Login.TLabel", background=CLR_WHITE, foreground=CLR_TEXT)
        s.configure("LoginTitle.TLabel", background=CLR_WHITE,
                    foreground=CLR_PRIMARY, font=("Segoe UI", 16, "bold"))

        # кнопки календаря
        s.configure("Nav.TButton", padding=(4, 1), font=("Segoe UI", 9, "bold"))

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    # ── Экран входа ────────────────────────────────────────
    def _show_login(self):
        self._clear()
        self.geometry("420x340")
        self.resizable(False, False)
        self.configure(bg=CLR_WHITE)

        fr = ttk.Frame(self, padding=30, style="Login.TFrame")
        fr.place(relx=0.5, rely=0.5, anchor="center")

        # картинка логотипа
        if HAS_PIL and os.path.exists(_LOGO_PATH):
            img = Image.open(_LOGO_PATH)
            img.thumbnail((64, 64), Image.LANCZOS)
            self._logo_img = ImageTk.PhotoImage(img)
            ttk.Label(fr, image=self._logo_img, background=CLR_WHITE).grid(
                row=0, column=0, columnspan=2, pady=(0, 6))
            title_row = 1
        else:
            title_row = 0

        ttk.Label(
            fr, text="Система учёта посещаемости",
            style="LoginTitle.TLabel",
        ).grid(row=title_row, column=0, columnspan=2, pady=(0, 20))

        r = title_row + 1
        ttk.Label(fr, text="Логин:", style="Login.TLabel").grid(row=r, column=0, sticky="e", padx=5, pady=5)
        self._le = ttk.Entry(fr, width=22)
        self._le.grid(row=r, column=1, padx=5, pady=5)

        ttk.Label(fr, text="Пароль:", style="Login.TLabel").grid(row=r+1, column=0, sticky="e", padx=5, pady=5)
        self._pe = ttk.Entry(fr, width=22, show="•")
        self._pe.grid(row=r+1, column=1, padx=5, pady=5)

        ttk.Button(fr, text="Войти", command=self._do_login).grid(
            row=r+2, column=0, columnspan=2, pady=15,
        )
        self._le.focus_set()
        self.bind("<Return>", lambda _: self._do_login())

    def _do_login(self):
        u = self.db.authenticate(self._le.get().strip(), self._pe.get())
        if not u:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
            return
        self.user = u
        self.configure(bg=CLR_BG)
        self._show_main()

    # ── Главный экран ─────────────────────────────────────
    def _show_main(self):
        self._clear()
        self.geometry("1060x700")
        self.resizable(True, True)
        self.unbind("<Return>")

        hdr = ttk.Frame(self, style="Header.TFrame")
        hdr.pack(fill="x")
        role_ru = "администратор" if self.user["role"] == "admin" else "учитель"
        ttk.Label(
            hdr,
            text=f'   {self.user["full_name"]}  ({role_ru})',
            style="Header.TLabel",
        ).pack(side="left", pady=8)
        ttk.Button(hdr, text="Выйти", style="Header.TButton",
                   command=self._show_login).pack(side="right", padx=10, pady=6)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._tabs = []
        for TabClass, label, args in [
            (AttendanceTab, "  Посещаемость  ", (nb, self.db, self.user)),
            (PredictionTab, "  Прогноз  ",       (nb, self.db, self.user)),
            (StudentsTab,   "  Ученики  ",      (nb, self.db, self.user)),
        ]:
            tab = TabClass(*args)
            nb.add(tab, text=label)
            self._tabs.append(tab)

        if self.user["role"] == "admin":
            for TabClass, label, args in [
                (SubjectsTab, "  Предметы  ", (nb, self.db)),
                (TeachersTab, "  Учителя  ",  (nb, self.db)),
            ]:
                tab = TabClass(*args)
                nb.add(tab, text=label)
                self._tabs.append(tab)

        nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, _event=None):
        """Auto-refresh data when switching tabs."""
        nb = _event.widget
        tab = nb.nametowidget(nb.select())
        if hasattr(tab, "on_show"):
            tab.on_show()


# ═══════════════════════════════════════════════════════════
#  Виджет-календарь
# ═══════════════════════════════════════════════════════════

class CalendarWidget(ttk.Frame):
    """Компактный календарь с подсветкой дат занятий."""

    _DAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
    _MONTHS = (
        "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
    )

    def __init__(self, master, on_click=None, **kw):
        super().__init__(master, **kw)
        self._cb = on_click
        self._hl = set()            
        today = date.today()
        self._y, self._m = today.year, today.month

        # навигация
        nav = ttk.Frame(self)
        nav.pack(fill="x")
        ttk.Button(nav, text="\u25c4", width=3, style="Nav.TButton",
                   command=self._prev).pack(side="left")
        self._title = ttk.Label(nav, anchor="center",
                                font=("Segoe UI", 10, "bold"))
        self._title.pack(side="left", fill="x", expand=True)
        ttk.Button(nav, text="\u25ba", width=3, style="Nav.TButton",
                   command=self._next).pack(side="right")

        # сетка
        g = tk.Frame(self, bg=CLR_BG)
        g.pack(fill="x", pady=(4, 0))
        for i, d in enumerate(self._DAYS):
            tk.Label(g, text=d, width=3, font=("Segoe UI", 8, "bold"),
                     bg=CLR_PRIMARY, fg=CLR_WHITE).grid(
                row=0, column=i, padx=1, pady=(0, 1))

        self._cells = []
        for r in range(6):
            row_cells = []
            for c in range(7):
                lbl = tk.Label(g, text="", width=3, font=("Segoe UI", 9),
                               bg=CLR_WHITE, relief="flat", cursor="hand2")
                lbl.grid(row=r + 1, column=c, padx=1, pady=1)
                lbl.bind("<Button-1>", self._click)
                row_cells.append(lbl)
            self._cells.append(row_cells)

        self._draw()

    def set_highlighted(self, dates):
        self._hl = set(dates)
        self._draw()

    # ── внутренние ──
    def _draw(self):
        self._title.config(text=f"{self._MONTHS[self._m]} {self._y}")
        weeks = _cal.monthcalendar(self._y, self._m)
        today = date.today()
        for r in range(6):
            for c in range(7):
                cell = self._cells[r][c]
                if r < len(weeks) and weeks[r][c]:
                    day = weeks[r][c]
                    d = date(self._y, self._m, day)
                    cell.config(text=str(day))
                    if d in self._hl:
                        cell.config(bg=CLR_ACCENT, fg=CLR_WHITE)
                    elif d == today:
                        cell.config(bg=CLR_PRIMARY_DK, fg=CLR_WHITE)
                    else:
                        cell.config(bg=CLR_WHITE, fg=CLR_TEXT)
                    cell._date = d
                else:
                    cell.config(text="", bg=CLR_BG, fg=CLR_BG)
                    cell._date = None

    def _click(self, event):
        d = getattr(event.widget, "_date", None)
        if d and self._cb:
            self._cb(d)

    def _prev(self):
        self._m -= 1
        if self._m < 1:
            self._m, self._y = 12, self._y - 1
        self._draw()

    def _next(self):
        self._m += 1
        if self._m > 12:
            self._m, self._y = 1, self._y + 1
        self._draw()


# ═══════════════════════════════════════════════════════════
#  Вкладка «Посещаемость»
# ═══════════════════════════════════════════════════════════

class AttendanceTab(ttk.Frame):

    def __init__(self, master, db, user):
        super().__init__(master, padding=10)
        self.db, self.user = db, user
        self.subjects = []
        self.rows = []          

        # ── строка 1: предмет ──
        r1 = ttk.Frame(self)
        r1.pack(fill="x", pady=2)
        ttk.Label(r1, text="Предмет:").pack(side="left")
        self.subj = ttk.Combobox(r1, state="readonly", width=35)
        self.subj.pack(side="left", padx=5)
        self.subj.bind("<<ComboboxSelected>>", lambda _: self._load_dates())

        # ── строка 2: дата ──
        r2 = ttk.Frame(self)
        r2.pack(fill="x", pady=2)
        ttk.Label(r2, text="Дата (ДД.ММ.ГГГГ):").pack(side="left")
        self.date_e = ttk.Entry(r2, width=12)
        self.date_e.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.date_e.pack(side="left", padx=5)
        ttk.Button(r2, text="Загрузить", command=self._load).pack(side="left", padx=5)

        ttk.Label(r2, text="Прошлые занятия:").pack(side="left", padx=(15, 0))
        self.dates_cb = ttk.Combobox(r2, state="readonly", width=12)
        self.dates_cb.pack(side="left", padx=5)
        self.dates_cb.bind("<<ComboboxSelected>>", self._pick_date)

        # ── содержимое: календарь + таблица ──
        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, pady=5)

        cal_fr = ttk.LabelFrame(content, text=" Календарь ", padding=4)
        cal_fr.pack(side="left", fill="y", padx=(0, 8))
        self.cal = CalendarWidget(cal_fr, on_click=self._on_cal_click)
        self.cal.pack()

        tf = ttk.Frame(content)
        tf.pack(side="left", fill="both", expand=True)

        cols = ("name", "present", "score")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=14)
        for c, h, w in zip(
            cols,
            ("Ученик", "Присутствие", "Балл (0-100)"),
            (300, 120, 120),
        ):
            self.tree.heading(c, text=h)
            self.tree.column(
                c, width=w, anchor="center" if c != "name" else "w",
            )
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self._edit)

        # ── кнопки ──
        bf = ttk.Frame(self)
        bf.pack(fill="x")
        ttk.Button(bf, text="Отметить всех присутствующими",
                   command=self._mark_all).pack(side="left")
        self.status = ttk.Label(bf, text="")
        self.status.pack(side="left", padx=15)
        ttk.Button(bf, text="Сохранить", command=self._save).pack(side="right")

        self._load_subjects()

    # ── внутренние важные методы ──

    def _sid(self):
        i = self.subj.current()
        return self.subjects[i]["id"] if i >= 0 else None

    def _parse_date(self):
        try:
            return datetime.strptime(self.date_e.get().strip(), "%d.%m.%Y").date()
        except ValueError:
            messagebox.showerror("Ошибка", "Формат даты: ДД.ММ.ГГГГ")
            return None

    def on_show(self):
        """Called when tab becomes visible — reload subjects list."""
        prev = self.subj.get()
        self._load_subjects()
        # restore previous selection if still exists
        vals = list(self.subj["values"])
        if prev in vals:
            self.subj.current(vals.index(prev))

    def _load_subjects(self):
        if self.user["role"] == "admin":
            self.subjects = self.db.get_subjects()
        else:
            self.subjects = self.db.get_subjects_for(self.user["id"])
        self.subj["values"] = [s["name"] for s in self.subjects]
        if self.subjects:
            self.subj.current(0)
            self._load_dates()

    def _load_dates(self):
        sid = self._sid()
        if not sid:
            return
        dates = self.db.lesson_dates(sid)
        self.dates_cb["values"] = [
            d["lesson_date"].strftime("%d.%m.%Y") for d in dates
        ]
        self.cal.set_highlighted({d["lesson_date"] for d in dates})

    def _pick_date(self, v):
        v = self.dates_cb.get()
        if v:
            self.date_e.delete(0, "end")
            self.date_e.insert(0, v)
            self._load()

    def _on_cal_click(self, d):
        self.date_e.delete(0, "end")
        self.date_e.insert(0, d.strftime("%d.%m.%Y"))
        self._load()

    def _load(self):
        sid = self._sid()
        dt = self._parse_date()
        if not sid or not dt:
            return
        self.tree.delete(*self.tree.get_children())
        self.rows.clear()

        records = self.db.get_attendance(sid, dt)
        if records:
            for r in records:
                pr = "Да" if r["present"] else "Нет"
                sc = str(r["score"]) if r["score"] is not None else "—"
                iid = self.tree.insert("", "end", values=(r["full_name"], pr, sc))
                self.rows.append(dict(
                    item=iid, student_id=r["student_id"],
                    name=r["full_name"],
                    present=int(r["present"]), score=r["score"],
                ))
            self.status.config(text=f"Загружено записей: {len(records)}")
        else:
            students = self.db.enrolled(sid)
            if not students:
                self.status.config(text="Нет записанных учеников")
                return
            for s in students:
                iid = self.tree.insert("", "end",
                                       values=(s["full_name"], "Нет", "—"))
                self.rows.append(dict(
                    item=iid, student_id=s["id"],
                    name=s["full_name"], present=0, score=None,
                ))
            self.status.config(text=f"Новое занятие ({len(students)} учеников)")

    def _mark_all(self):
        for r in self.rows:
            r["present"] = 1
            sc = str(r["score"]) if r["score"] is not None else "—"
            self.tree.item(r["item"], values=(r["name"], "Да", sc))

    def _edit(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        row = next((r for r in self.rows if r["item"] == item), None)
        if not row:
            return

        dlg = tk.Toplevel(self)
        dlg.title("Редактирование")
        dlg.geometry("340x200")
        dlg.resizable(False, False)
        dlg.configure(bg=CLR_BG)
        dlg.transient(self)
        dlg.grab_set()

        f = ttk.Frame(dlg, padding=15)
        f.pack(fill="both", expand=True)
        ttk.Label(f, text=row["name"],
                  foreground=CLR_PRIMARY,
                  font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 10))

        pvar = tk.BooleanVar(value=bool(row["present"]))
        ttk.Checkbutton(f, text="Присутствовал", variable=pvar).grid(
            row=1, column=0, columnspan=2, pady=5)

        ttk.Label(f, text="Балл (0–100):").grid(
            row=2, column=0, sticky="e", padx=5, pady=5)
        se = ttk.Entry(f, width=8)
        if row["score"] is not None:
            se.insert(0, str(row["score"]))
        se.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        def ok():
            row["present"] = int(pvar.get())
            txt = se.get().strip()
            if txt:
                try:
                    v = int(txt)
                    if not 0 <= v <= 100:
                        raise ValueError
                    row["score"] = v
                except ValueError:
                    messagebox.showerror("Ошибка", "Балл — целое число от 0 до 100")
                    return
            else:
                row["score"] = None
            pr = "Да" if row["present"] else "Нет"
            sc = str(row["score"]) if row["score"] is not None else "—"
            self.tree.item(item, values=(row["name"], pr, sc))
            dlg.destroy()

        ttk.Button(f, text="OK", command=ok).grid(
            row=3, column=0, columnspan=2, pady=12)
        se.focus_set()

    def _save(self):
        sid = self._sid()
        dt = self._parse_date()
        if not sid or not dt or not self.rows:
            return
        for r in self.rows:
            self.db.save_att(r["student_id"], sid, dt, r["present"], r["score"])
        self._load_dates()
        messagebox.showinfo("Готово", "Данные посещаемости сохранены")


# ═══════════════════════════════════════════════════════════
#  Вкладка «Прогноз»
# ═══════════════════════════════════════════════════════════

class PredictionTab(ttk.Frame):

    def __init__(self, master, db, user):
        super().__init__(master, padding=10)
        self.db, self.user = db, user
        self.subjects = []

        # ── управление ──
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 5))
        ttk.Label(top, text="Предмет:").pack(side="left")
        self.subj = ttk.Combobox(top, state="readonly", width=35)
        self.subj.pack(side="left", padx=5)
        ttk.Button(top, text="Рассчитать", command=self._calc).pack(
            side="left", padx=5)
        ttk.Button(top, text="Внести результат экзамена",
                   command=self._add_exam).pack(side="left", padx=5)

        # ── тело: таблица (лево) + график (право) ──
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # таблица
        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        cols = ("name", "avg", "exam", "pred")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=13)
        for c, h, w in zip(
            cols,
            ("Ученик", "Ср. балл", "Экзамен", "Прогноз"),
            (200, 80, 80, 80),
        ):
            self.tree.heading(c, text=h)
            self.tree.column(
                c, width=w, anchor="center" if c != "name" else "w",
            )
        sb = ttk.Scrollbar(left, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # информация
        self.info = ttk.Label(body, text="", font=("Segoe UI", 9))
        self.info.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

        # график
        self.chart_fr = ttk.Frame(body)
        self.chart_fr.grid(row=0, column=1, sticky="nsew")

        self._load_subjects()

    def _sid(self):
        i = self.subj.current()
        return self.subjects[i]["id"] if i >= 0 else None

    def on_show(self):
        """Called when tab becomes visible — reload subjects list."""
        prev = self.subj.get()
        self._load_subjects()
        vals = list(self.subj["values"])
        if prev in vals:
            self.subj.current(vals.index(prev))

    def _load_subjects(self):
        if self.user["role"] == "admin":
            self.subjects = self.db.get_subjects()
        else:
            self.subjects = self.db.get_subjects_for(self.user["id"])
        self.subj["values"] = [s["name"] for s in self.subjects]
        if self.subjects:
            self.subj.current(0)

    def _calc(self):
        sid = self._sid()
        if not sid:
            return
        self.tree.delete(*self.tree.get_children())

        data = self.db.prediction_data(sid)
        train_x, train_y = [], []
        all_rows = []

        for d in data:
            avg = float(d["avg_score"]) if d["avg_score"] is not None else None
            exam = int(d["exam_score"]) if d["exam_score"] is not None else None
            if avg is not None and exam is not None:
                train_x.append(avg)
                train_y.append(exam)
            all_rows.append(dict(
                name=d["full_name"], avg=avg, exam=exam,
            ))

        slope, intercept, r_sq = linear_regression(train_x, train_y)

        for d in all_rows:
            avg_t = f"{d['avg']:.1f}" if d["avg"] is not None else "—"
            exam_t = str(d["exam"]) if d["exam"] is not None else "—"
            if d["avg"] is not None and slope is not None:
                pred_t = f"{predict(slope, intercept, d['avg']):.1f}"
            else:
                pred_t = "—"
            self.tree.insert("", "end", values=(d["name"], avg_t, exam_t, pred_t))

        if slope is not None:
            self.info.config(
                text=f"Уравнение: y = {slope:.2f}·x + {intercept:.2f}     "
                     f"R² = {r_sq:.4f}",
            )
        else:
            self.info.config(
                text="Недостаточно данных для регрессии "
                     "(нужны результаты экзамена минимум у 2 учеников)",
            )

        self._draw_chart(train_x, train_y, slope, intercept, all_rows)

    # ── график ──
    def _draw_chart(self, tx, ty, slope, intercept, rows):
        for w in self.chart_fr.winfo_children():
            w.destroy()

        if not HAS_MPL:
            ttk.Label(
                self.chart_fr,
                text="Для графика установите matplotlib:\n"
                     "pip install matplotlib",
            ).pack(padx=10, pady=30)
            return

        fig = Figure(figsize=(4.2, 3.5), dpi=96)
        ax = fig.add_subplot(111)

        fig.patch.set_facecolor(CLR_BG)
        ax.set_facecolor(CLR_WHITE)

        if tx:
            ax.scatter(tx, ty, color=CLR_PRIMARY, s=40, zorder=5,
                       label="Факт (экзамен)")

        if slope is not None:
            x0, x1 = 0, 100
            ax.plot(
                [x0, x1],
                [slope * x0 + intercept, slope * x1 + intercept],
                color=CLR_ACCENT, linewidth=2,
                label=f"y = {slope:.2f}x + {intercept:.2f}",
            )

            pred_x = [
                d["avg"] for d in rows
                if d["avg"] is not None and d["exam"] is None
            ]
            if pred_x:
                pred_y = [predict(slope, intercept, x) for x in pred_x]
                ax.scatter(pred_x, pred_y, color=CLR_ACCENT, marker="^",
                           s=50, zorder=5, label="Прогноз")

        ax.set_xlabel("Средний балл за занятия")
        ax.set_ylabel("Балл экзамена")
        ax.set_title("Линейная регрессия", fontsize=10)
        ax.set_xlim(0, 105)
        ax.set_ylim(0, 105)
        ax.legend(fontsize=8)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_fr)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── добавить экзамен ──
    def _add_exam(self):
        sid = self._sid()
        if not sid:
            return
        students = self.db.enrolled(sid)
        if not students:
            messagebox.showinfo("Информация", "Нет записанных учеников")
            return

        dlg = tk.Toplevel(self)
        dlg.title("Результат экзамена")
        dlg.geometry("380x200")
        dlg.resizable(False, False)
        dlg.configure(bg=CLR_BG)
        dlg.transient(self)
        dlg.grab_set()

        f = ttk.Frame(dlg, padding=15)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Ученик:").grid(
            row=0, column=0, sticky="e", padx=5, pady=5)
        sc = ttk.Combobox(f, state="readonly", width=28)
        sc["values"] = [s["full_name"] for s in students]
        sc.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(f, text="Балл (0–100):").grid(
            row=1, column=0, sticky="e", padx=5, pady=5)
        se = ttk.Entry(f, width=8)
        se.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        def save():
            idx = sc.current()
            if idx < 0:
                return
            try:
                v = int(se.get().strip())
                if not 0 <= v <= 100:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Балл — целое число от 0 до 100")
                return
            self.db.save_exam(students[idx]["id"], sid, v)
            messagebox.showinfo("Готово", "Результат экзамена сохранён")
            dlg.destroy()
            self._calc()

        ttk.Button(f, text="Сохранить", command=save).grid(
            row=2, column=0, columnspan=2, pady=12)


# ═══════════════════════════════════════════════════════════
#  Вкладка «Ученики» 
# ═══════════════════════════════════════════════════════════

class StudentsTab(ttk.Frame):

    def __init__(self, master, db, user):
        super().__init__(master, padding=10)
        self.db, self.user = db, user

        # ── добавить ученика ──
        add_fr = ttk.LabelFrame(self, text=" Добавить ученика ", padding=8)
        add_fr.pack(fill="x", pady=(0, 10))

        ttk.Label(add_fr, text="ФИО:").grid(row=0, column=0, sticky="e", padx=3)
        self.s_name = ttk.Entry(add_fr, width=50)
        self.s_name.grid(row=0, column=1, padx=3)

        ttk.Label(add_fr, text="Телефон:").grid(row=0, column=2, sticky="e", padx=3)
        self.s_phone = ttk.Entry(add_fr, width=15)
        self.s_phone.grid(row=0, column=3, padx=3)

        ttk.Label(add_fr, text="Email:").grid(row=0, column=4, sticky="e", padx=3)
        self.s_email = ttk.Entry(add_fr, width=18)
        self.s_email.grid(row=0, column=5, padx=3)

        ttk.Button(add_fr, text="Добавить", command=self._add).grid(
            row=0, column=6, padx=8)

        # ── таблица учеников ──
        tf = ttk.Frame(self)
        tf.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("name", "phone", "email")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=10)
        for c, h, w in zip(
            cols, ("ФИО", "Телефон", "Email"), (250, 140, 200),
        ):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # редактировать / удалить
        btn_fr = ttk.Frame(self)
        btn_fr.pack(fill="x", pady=(0, 10))
        ttk.Button(btn_fr, text="Редактировать", command=self._edit).pack(side="left", padx=(0, 5))
        ttk.Button(btn_fr, text="Удалить", command=self._delete).pack(side="left")

        # ── записать на предмет ──
        enr_fr = ttk.LabelFrame(self, text=" Записать на предмет ", padding=8)
        enr_fr.pack(fill="x")

        ttk.Label(enr_fr, text="Ученик:").grid(row=0, column=0, sticky="e", padx=3)
        self.en_student = ttk.Combobox(enr_fr, state="readonly", width=28)
        self.en_student.grid(row=0, column=1, padx=3)

        ttk.Label(enr_fr, text="Предмет:").grid(row=0, column=2, sticky="e", padx=3)
        self.en_subject = ttk.Combobox(enr_fr, state="readonly", width=28)
        self.en_subject.grid(row=0, column=3, padx=3)

        ttk.Button(enr_fr, text="Записать", command=self._enroll).grid(
            row=0, column=4, padx=8)

        self._refresh()

    def on_show(self):
        """Called when tab becomes visible — reload everything."""
        self._refresh()

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if sel:
            idx = self.tree.index(sel[0])
            self.en_student.current(idx)

    def _refresh(self):
        # таблица
        self.students = self.db.get_students()
        self.tree.delete(*self.tree.get_children())
        for s in self.students:
            self.tree.insert("", "end",
                             values=(s["full_name"], s["phone"], s["email"]))
        # запись
        self.en_student["values"] = [s["full_name"] for s in self.students]
        if self.user["role"] == "admin":
            self.subjects = self.db.get_subjects()
        else:
            self.subjects = self.db.get_subjects_for(self.user["id"])
        self.en_subject["values"] = [s["name"] for s in self.subjects]

    def _add(self):
        name = self.s_name.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите ФИО ученика")
            return
        self.db.add_student(name, self.s_phone.get().strip(),
                            self.s_email.get().strip())
        self.s_name.delete(0, "end")
        self.s_phone.delete(0, "end")
        self.s_email.delete(0, "end")
        self._refresh()

    def _enroll(self):
        si = self.en_student.current()
        sj = self.en_subject.current()
        if si < 0 or sj < 0:
            messagebox.showerror("Ошибка", "Выберите ученика и предмет")
            return
        self.db.enroll(self.students[si]["id"], self.subjects[sj]["id"])
        messagebox.showinfo("Готово", "Ученик записан на предмет")

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Информация", "Выберите ученика в таблице")
            return
        idx = self.tree.index(sel[0])
        s = self.students[idx]

        dlg = tk.Toplevel(self)
        dlg.title("Редактирование ученика")
        dlg.geometry("400x200")
        dlg.resizable(False, False)
        dlg.configure(bg=CLR_BG)
        dlg.transient(self)
        dlg.grab_set()

        f = ttk.Frame(dlg, padding=15)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="ФИО:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        e_name = ttk.Entry(f, width=30)
        e_name.insert(0, s["full_name"])
        e_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(f, text="Телефон:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        e_phone = ttk.Entry(f, width=20)
        e_phone.insert(0, s["phone"])
        e_phone.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(f, text="Email:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        e_email = ttk.Entry(f, width=25)
        e_email.insert(0, s["email"])
        e_email.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        def save():
            name = e_name.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите ФИО")
                return
            self.db.update_student(s["id"], name,
                                   e_phone.get().strip(), e_email.get().strip())
            dlg.destroy()
            self._refresh()

        ttk.Button(f, text="Сохранить", command=save).grid(
            row=3, column=0, columnspan=2, pady=12)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Информация", "Выберите ученика в таблице")
            return
        idx = self.tree.index(sel[0])
        s = self.students[idx]
        if messagebox.askyesno("Подтверждение",
                               f"Удалить ученика «{s['full_name']}»?\n"
                               "Все его данные будут удалены."):
            self.db.delete_student(s["id"])
            self._refresh()


# ═══════════════════════════════════════════════════════════
#  Вкладка «Предметы»
# ═══════════════════════════════════════════════════════════

class SubjectsTab(ttk.Frame):

    def __init__(self, master, db):
        super().__init__(master, padding=10)
        self.db = db

        # ── добавить предмет ──
        add_fr = ttk.LabelFrame(self, text=" Добавить предмет ", padding=8)
        add_fr.pack(fill="x", pady=(0, 10))

        ttk.Label(add_fr, text="Название:").grid(
            row=0, column=0, sticky="e", padx=3)
        self.sname = ttk.Entry(add_fr, width=30)
        self.sname.grid(row=0, column=1, padx=3)

        ttk.Label(add_fr, text="Учитель:").grid(
            row=0, column=2, sticky="e", padx=3)
        self.tcb = ttk.Combobox(add_fr, state="readonly", width=25)
        self.tcb.grid(row=0, column=3, padx=3)

        ttk.Button(add_fr, text="Добавить", command=self._add).grid(
            row=0, column=4, padx=8)

        # ── таблица ──
        tf = ttk.Frame(self)
        tf.pack(fill="both", expand=True)

        cols = ("name", "teacher")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=14)
        self.tree.heading("name", text="Предмет")
        self.tree.heading("teacher", text="Учитель")
        self.tree.column("name", width=300)
        self.tree.column("teacher", width=250)
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # редактировать / удалить
        btn_fr = ttk.Frame(self)
        btn_fr.pack(fill="x", pady=(5, 0))
        ttk.Button(btn_fr, text="Редактировать", command=self._edit).pack(side="left", padx=(0, 5))
        ttk.Button(btn_fr, text="Удалить", command=self._delete).pack(side="left")

        self._refresh()

    def on_show(self):
        self._refresh()

    def _refresh(self):
        self.teachers = self.db.get_users()
        self.tcb["values"] = [u["full_name"] for u in self.teachers]

        self.subjects_list = self.db.get_subjects()
        self.tree.delete(*self.tree.get_children())
        for s in self.subjects_list:
            self.tree.insert("", "end", values=(s["name"], s["teacher"]))

    def _add(self):
        name = self.sname.get().strip()
        ti = self.tcb.current()
        if not name:
            messagebox.showerror("Ошибка", "Введите название предмета")
            return
        if ti < 0:
            messagebox.showerror("Ошибка", "Выберите учителя")
            return
        self.db.add_subject(name, self.teachers[ti]["id"])
        self.sname.delete(0, "end")
        self._refresh()

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Информация", "Выберите предмет в таблице")
            return
        idx = self.tree.index(sel[0])
        s = self.subjects_list[idx]

        dlg = tk.Toplevel(self)
        dlg.title("Редактирование предмета")
        dlg.geometry("400x180")
        dlg.resizable(False, False)
        dlg.configure(bg=CLR_BG)
        dlg.transient(self)
        dlg.grab_set()

        f = ttk.Frame(dlg, padding=15)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Название:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        e_name = ttk.Entry(f, width=30)
        e_name.insert(0, s["name"])
        e_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(f, text="Учитель:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        tcb = ttk.Combobox(f, state="readonly", width=27)
        tcb["values"] = [u["full_name"] for u in self.teachers]
        # выбрать текущего учителя
        for i, t in enumerate(self.teachers):
            if t["id"] == s["teacher_id"]:
                tcb.current(i)
                break
        tcb.grid(row=1, column=1, padx=5, pady=5)

        def save():
            name = e_name.get().strip()
            ti = tcb.current()
            if not name:
                messagebox.showerror("Ошибка", "Введите название")
                return
            if ti < 0:
                messagebox.showerror("Ошибка", "Выберите учителя")
                return
            self.db.update_subject(s["id"], name, self.teachers[ti]["id"])
            dlg.destroy()
            self._refresh()

        ttk.Button(f, text="Сохранить", command=save).grid(
            row=2, column=0, columnspan=2, pady=12)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Информация", "Выберите предмет в таблице")
            return
        idx = self.tree.index(sel[0])
        s = self.subjects_list[idx]
        if messagebox.askyesno("Подтверждение",
                               f"Удалить предмет «{s['name']}»?\n"
                               "Все связанные данные будут удалены."):
            self.db.delete_subject(s["id"])
            self._refresh()


# ═══════════════════════════════════════════════════════════
#  Вкладка «Учителя»
# ═══════════════════════════════════════════════════════════

class TeachersTab(ttk.Frame):

    def __init__(self, master, db):
        super().__init__(master, padding=10)
        self.db = db

        # ── добавить учителя ──
        add_fr = ttk.LabelFrame(self, text=" Добавить учителя ", padding=8)
        add_fr.pack(fill="x", pady=(0, 10))

        ttk.Label(add_fr, text="ФИО:").grid(
            row=0, column=0, sticky="e", padx=3)
        self.t_name = ttk.Entry(add_fr, width=44)
        self.t_name.grid(row=0, column=1, padx=3)

        ttk.Label(add_fr, text="Логин:").grid(
            row=0, column=2, sticky="e", padx=3)
        self.t_login = ttk.Entry(add_fr, width=15)
        self.t_login.grid(row=0, column=3, padx=3)

        ttk.Label(add_fr, text="Пароль:").grid(
            row=0, column=4, sticky="e", padx=3)
        self.t_pwd = ttk.Entry(add_fr, width=15, show="•")
        self.t_pwd.grid(row=0, column=5, padx=3)

        ttk.Button(add_fr, text="Добавить", command=self._add).grid(
            row=0, column=6, padx=8)

        # ── таблица ──
        tf = ttk.Frame(self)
        tf.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("name", "login", "role")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=12)
        for c, h, w in zip(
            cols, ("ФИО", "Логин", "Роль"), (250, 150, 120),
        ):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ── кнопки ──
        btn_fr = ttk.Frame(self)
        btn_fr.pack(fill="x")
        ttk.Button(btn_fr, text="Повысить до администратора",
                   command=self._promote).pack(side="left", padx=(0, 5))
        ttk.Button(btn_fr, text="Редактировать",
                   command=self._edit).pack(side="left", padx=5)
        ttk.Button(btn_fr, text="Удалить",
                   command=self._delete).pack(side="left", padx=5)

        self._refresh()

    def on_show(self):
        self._refresh()

    def _refresh(self):
        self.users = self.db.get_users()
        self.tree.delete(*self.tree.get_children())
        for u in self.users:
            role_ru = "администратор" if u["role"] == "admin" else "учитель"
            self.tree.insert("", "end", iid=str(u["id"]),
                             values=(u["full_name"], u["login"], role_ru))

    def _add(self):
        name = self.t_name.get().strip()
        login = self.t_login.get().strip()
        pwd = self.t_pwd.get().strip()
        if not all([name, login, pwd]):
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        try:
            self.db.add_user(login, pwd, name)
        except Exception:
            messagebox.showerror("Ошибка", "Логин уже занят")
            return
        self.t_name.delete(0, "end")
        self.t_login.delete(0, "end")
        self.t_pwd.delete(0, "end")
        self._refresh()

    def _promote(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Информация", "Выберите учителя в таблице")
            return
        uid = int(sel[0])
        self.db.promote(uid)
        self._refresh()
        messagebox.showinfo("Готово", "Роль изменена на администратор")

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Информация", "Выберите учителя в таблице")
            return
        uid = int(sel[0])
        u = next(x for x in self.users if x["id"] == uid)

        dlg = tk.Toplevel(self)
        dlg.title("Редактирование учителя")
        dlg.geometry("380x170")
        dlg.resizable(False, False)
        dlg.configure(bg=CLR_BG)
        dlg.transient(self)
        dlg.grab_set()

        f = ttk.Frame(dlg, padding=15)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="ФИО:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        e_name = ttk.Entry(f, width=28)
        e_name.insert(0, u["full_name"])
        e_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(f, text="Логин:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        e_login = ttk.Entry(f, width=20)
        e_login.insert(0, u["login"])
        e_login.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        def save():
            name = e_name.get().strip()
            login = e_login.get().strip()
            if not name or not login:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return
            try:
                self.db.update_user(uid, name, login)
            except Exception:
                messagebox.showerror("Ошибка", "Логин уже занят")
                return
            dlg.destroy()
            self._refresh()

        ttk.Button(f, text="Сохранить", command=save).grid(
            row=2, column=0, columnspan=2, pady=12)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Информация", "Выберите учителя в таблице")
            return
        uid = int(sel[0])
        u = next(x for x in self.users if x["id"] == uid)
        if messagebox.askyesno("Подтверждение",
                               f"Удалить пользователя «{u['full_name']}»?"):
            self.db.delete_user(uid)
            self._refresh()


# ═══════════════════════════════════════════════════════════
#                Главный цикл
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = App()
    app.mainloop()
