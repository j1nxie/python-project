import os
import customtkinter as ctk
from tkinter import messagebox as msgbox

from models import Company
from database.mongo import employee_repo
from frontend.helpers_gui import *
from frontend.helpers_gui.global_styling import *

the_company = Company()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

Width = 1024
Height = 768


class PayrollGui(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Payroll Management")
        self.geometry(f"{Width}x{Height}")
        self.resizable(False, False)

        self.left_frame = ctk.CTkFrame(master=self, corner_radius=10)
        self.left_frame.pack(side=ctk.LEFT)
        self.left_frame.pack_propagate(False)
        self.left_frame.configure(width=320, height=760)

        self.right_frame = ctk.CTkFrame(master=self)
        self.right_frame.pack(side=ctk.RIGHT, expand=True)
        self.right_frame.pack_propagate(False)

        menu_buttons = MenuButtons(
            self.left_frame, self.right_frame, self.admin() if the_company.logged_in_employee.is_admin else self.employee()
        )
        menu_buttons.create()

    def admin(self):
        return {
            "Create/update Payroll": self.__admin_create_update_payroll,
            "View Payroll": self.__admin_view_payroll,
            "Back": self.__back_to_homepage,
        }

    def employee(self):
        return {"View Payroll": self.__employee_view_payroll, "Back": self.__back_to_homepage}

    def __back_to_homepage(self):
        from .homepage import Homepage

        self.destroy()
        Homepage().mainloop()

    # region: admin functions

    def __admin_create_update_payroll(self):
        # 0: select employee from a list
        # input: 1: salary
        #        2: bonus
        #        3: tax
        #        4: penalty
        # 5: "Create"/"Update" button depending on whether payroll exists

        main_frame = ctk.CTkFrame(master=self.right_frame)
        main_frame.grid(row=0, column=0)
        empl_idx_select: ctk.Variable = ctk.IntVar(value=0)

        # change btn_label to "Update" if payroll exists
        btn_label: str = "Create"
        submit_btn = ctk.CTkButton(master=main_frame, text=btn_label, **btn_action_style)
        submit_btn.grid(row=5, column=0, columnspan=2, pady=20)

        def _update_btn_label():
            nonlocal btn_label, submit_btn, empl_idx_select
            empl_payroll = the_company.employees[empl_idx_select.get()].payroll
            if any([empl_payroll.salary, empl_payroll.bonus, empl_payroll.tax, empl_payroll.punish, empl_payroll.total]):
                btn_label = "Update"
                submit_btn.configure(text=btn_label)
            else:
                btn_label = "Create"
                submit_btn.configure(text=btn_label)

        _update_btn_label()

        # Select employee from a list to create payroll for
        empl_select_frame = display_list(
            _master=main_frame,
            options=tuple(f"{empl.employee_id} - {empl.name}" for empl in the_company.employees),
            returned_idx=[empl_idx_select],
            selectable=True,
            place_col=0,
            place_row=0,
            colspan=2,
            cmd=_update_btn_label,
        )
        if empl_select_frame[0] is False:
            ctk.CTkLabel(master=main_frame, text="No employee found", **label_desc_style).grid(
                row=1, column=0, columnspan=2, pady=20, padx=20
            )

        # region: input boxes
        entries = [ctk.CTkEntry(master=main_frame) for _ in range(1, 5)]
        labels = ("Salary", "Bonus", "Tax", "Penalty")
        placeholders = ("100", "10", "5", "0")
        for row, entry, label, placeholder in zip(range(1, 5), entries, labels, placeholders):
            ctk.CTkLabel(master=main_frame, text=label, **label_desc_style).grid(
                row=row, column=0, padx=20, pady=(20, 0), sticky="w"
            )
            entry.configure(placeholder_text=placeholder, **input_box_style)
            entry.grid(row=row, column=1, padx=(0, 20), pady=(20, 0))
        # endregion

        # region: submit button

        def _create_update_payroll_handler():
            nonlocal entries, btn_label
            values = [entry.get() for entry in entries]
            selected_empl = the_company.employees[empl_idx_select.get()]
            empl_payroll = selected_empl.payroll

            if not all(values):
                msgbox.showerror("Error", "Please fill in all fields")
                return

            for setter, value in zip(
                (empl_payroll.set_salary, empl_payroll.set_bonus, empl_payroll.set_tax, empl_payroll.set_punish), values
            ):
                setter(value).unwrap()
            selected_empl.set_payroll(empl_payroll).unwrap()
            if os.getenv("HRMGR_DB") == "TRUE":
                employee_repo.update_one(
                    {"_id": selected_empl.id}, {"$set": selected_empl.dict(include={"payroll"})}, upsert=True
                )
            msgbox.showinfo("Success", f"Payroll {btn_label.lower()} successfully")

        submit_btn.configure(command=_create_update_payroll_handler)
        # endregion

    def __admin_view_payroll(self):
        # 0: select employee from a list
        # 1: payroll table

        main_frame = ctk.CTkFrame(master=self.right_frame)
        main_frame.grid(row=0, column=0)

        payrol_table_frame = ctk.CTkFrame(None)

        # Select employee from a list to view payroll
        empl_idx_select: ctk.Variable = ctk.IntVar(value=0)

        def update_payroll_table():
            nonlocal empl_idx_select, payrol_table_frame, main_frame
            selected_empl = the_company.employees[empl_idx_select.get()]
            payroll = selected_empl.payroll

            payrol_table_frame.destroy()
            payrol_table_frame = ctk.CTkFrame(master=main_frame)
            payrol_table_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15), padx=20)

            titles = ("Salary", "Bonus", "Tax", "Penalty", "Total")
            values = (payroll.salary, payroll.bonus, payroll.tax, payroll.punish, payroll.total)
            for row, title, value in zip(range(5), titles, values):
                ctk.CTkLabel(master=payrol_table_frame, text=title).grid(row=row, column=0, padx=20, sticky="w")
                ctk.CTkLabel(master=payrol_table_frame, text=str(value)).grid(row=row, column=1, padx=(0, 20), sticky="e")

        update_payroll_table()

        empl_select_frame = display_list(
            _master=main_frame,
            options=tuple(f"{empl.employee_id} - {empl.name}" for empl in the_company.employees),
            returned_idx=[empl_idx_select],
            selectable=True,
            place_col=0,
            place_row=0,
            colspan=1,
            cmd=update_payroll_table,
        )

        if empl_select_frame[0] is False:
            ctk.CTkLabel(master=main_frame, text="No employee found", **label_desc_style).grid(
                row=1, column=0, columnspan=2, pady=20, padx=20
            )

    # endregion

    # region: employee functions

    def __employee_view_payroll(self):
        main_frame = ctk.CTkFrame(master=self.right_frame)
        main_frame.grid(row=0, column=0)
        empl = the_company.logged_in_employee

        labels = ("Salary", "Bonus", "Tax", "Penalty", "Total")
        values = (empl.payroll.salary, empl.payroll.bonus, empl.payroll.tax, empl.payroll.punish, empl.payroll.total)
        for row, label, value in zip(range(5), labels, values):
            ctk.CTkLabel(master=main_frame, text=label).grid(row=row, column=0, padx=20, sticky="w")
            ctk.CTkLabel(master=main_frame, text=str(value)).grid(row=row, column=1, padx=(0, 20), sticky="e")

    # endregion
