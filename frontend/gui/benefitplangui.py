import os
import customtkinter as ctk
from tkinter import messagebox as msgbox
from tkinter import W, E, NORMAL, DISABLED

from models import Company, BenefitPlan, Employee
from database.mongo import benefit_repo, employee_repo
from frontend.helpers_gui import *
from frontend.helpers_gui.global_styling import *

the_company = Company()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

Width = 1024
Height = 768


class BenefitPlanGui(ctk.CTk):
    def __init__(self, master=None):
        super().__init__()
        self.title("Benefit Plan Management")
        self.geometry(f"{Width}x{Height}")
        self.resizable(True, True)

        self.left_frame = ctk.CTkFrame(master=self, corner_radius=10)
        self.left_frame.pack(side=ctk.LEFT)
        self.left_frame.pack_propagate(False)
        self.left_frame.configure(width=320, height=760)

        self.right_frame = ctk.CTkFrame(master=self)
        self.right_frame.pack(side=ctk.RIGHT, expand=True)
        self.right_frame.pack_propagate(False)

        self.admin() if the_company.logged_in_employee.is_admin else self.employee()

    def admin(self):
        menu_buttons = MenuButtons(
            self.left_frame,
            self.right_frame,
            {
                "Add/remove/modify": self.__admin_add_rm_modify,
                "Apply/remove": self.__admin_apply_rm,
                "Request to enroll": self.__request,
                "Resolve requests": self.__admin_resolve,
                "View details": self.__view_details,
                "List empls w/o benefit": self.__admin_empls_w_o_benefit,
                "Back": self.__back_to_homepage,
            },
        )
        menu_buttons.create()

    def employee(self):
        menu_buttons = MenuButtons(
            self.left_frame,
            self.right_frame,
            {
                "View benefit plans": self.__view_details,
                "Request to enroll": self.__request,
                "Back": self.__back_to_homepage,
            },
        )
        menu_buttons.create()

    def __destroy_all_frames(self):
        for widget in self.right_frame.winfo_children():
            widget.destroy()

    def __back_to_homepage(self):
        from .homepage import Homepage

        self.destroy()
        Homepage().mainloop()

    def __admin_add_rm_modify(self, default_submenu: int = 1):
        # 0: 3 buttons: 1. add, 2. remove, 3. modify
        # 1: Table to choose bnf if modify or remove, "Creating..." if add
        # 2: Input name
        # 3: Input desc
        # 4: Input cost
        # 5: Button to submit

        main_frame = ctk.CTkFrame(master=self.right_frame)
        main_frame.grid(row=0, column=0)

        # region: initialize widgets and variables
        input_name = ctk.CTkEntry(master=main_frame, **input_box_style)
        input_desc = ctk.CTkEntry(master=main_frame, **input_box_style)
        input_cost = ctk.CTkEntry(master=main_frame, **input_box_style)

        benefit_idx_select = ctk.IntVar()
        first_row = ctk.CTkFrame(master=main_frame)
        first_row.grid(row=1, column=0, columnspan=3, pady=10)

        btn_add = ctk.CTkButton(master=main_frame, text="Add", **btn_action_style)
        btn_remove = ctk.CTkButton(master=main_frame, text="Remove", **btn_action_style)
        btn_modify = ctk.CTkButton(master=main_frame, text="Modify", **btn_action_style)
        # endregion

        # region: 3 button representing 3 options: 1. add, 2. remove, 3. modify
        def _add():
            nonlocal input_name, input_desc, input_cost, current_submenu, btn_modify, btn_remove, btn_add
            for widget in first_row.winfo_children():
                widget.destroy()
            ctk.CTkLabel(master=first_row, text="Adding new benefit...", **label_desc_style).grid(
                row=0, column=0, columnspan=3, padx=10, pady=10
            )

            current_submenu = 1

            # enable input boxes, <remove> and <modify> buttons
            # disable <add> button (already clicked)
            for elem in (input_name, input_desc, input_cost, btn_modify, btn_remove):
                elem.configure(state=NORMAL)
            btn_add.configure(state=DISABLED)

        btn_add.grid(row=0, column=0, padx=10, pady=(20, 10))
        btn_add.configure(command=_add)

        def _remove():
            nonlocal input_name, input_desc, input_cost, benefit_idx_select, current_submenu, btn_modify, btn_remove, btn_add
            for widget in first_row.winfo_children():
                widget.destroy()
            display_list(
                _master=first_row,
                options=tuple(f"{b.name} - {b.cost}" for b in the_company.benefits),
                returned_idx=[benefit_idx_select],
                place_row=0,
                colspan=1,
                err_msg="No benefit plan to remove",
            )
            current_submenu = 2

            # disable input boxes, <delete> btn (clicked)
            # enable <add> and <modify> buttons
            for elem in (input_name, input_desc, input_cost, btn_remove):
                elem.configure(state=DISABLED)
            for elem in (btn_add, btn_modify):
                elem.configure(state=NORMAL)

        btn_remove.grid(row=0, column=1, padx=10, pady=(20, 10))
        btn_remove.configure(command=_remove)

        def _modify():
            nonlocal input_name, input_desc, input_cost, benefit_idx_select, current_submenu, btn_modify, btn_remove, btn_add
            for widget in first_row.winfo_children():
                widget.destroy()
            display_list(
                _master=first_row,
                options=tuple(f"{b.name} - {b.cost}" for b in the_company.benefits),
                returned_idx=[benefit_idx_select],
                place_row=0,
                colspan=1,
            )
            current_submenu = 3

            # enable input boxes, <add> and <remove> buttons
            # disable <modify> button (clicked)
            for elem in (input_name, input_desc, input_cost, btn_add, btn_remove):
                elem.configure(state=NORMAL)
            btn_modify.configure(state=DISABLED)

        btn_modify.grid(row=0, column=2, padx=10, pady=(20, 10))
        btn_modify.configure(command=_modify)
        # endregion

        # region: initializing the default menu
        match default_submenu:
            case 1:
                _add()
                current_submenu = 1
            case 2:
                _remove()
                current_submenu = 2
            case 3:
                _modify()
                current_submenu = 3
        # endregion

        # region: input boxes
        ctk.CTkLabel(master=main_frame, text="Name: ", **label_desc_style).grid(
            row=2, column=0, sticky=W, padx=(20, 0), pady=10
        )
        input_name.grid(row=2, column=1, columnspan=2, padx=20, sticky=E)
        ctk.CTkLabel(master=main_frame, text="Description: ", **label_desc_style).grid(
            row=3, column=0, sticky=W, padx=(20, 0)
        )
        input_desc.grid(row=3, column=1, columnspan=2, padx=20, sticky=E)
        ctk.CTkLabel(master=main_frame, text="Cost: ", **label_desc_style).grid(
            row=4, column=0, sticky=W, padx=(20, 0), pady=10
        )
        input_cost.grid(row=4, column=1, columnspan=2, padx=20, sticky=E)
        # endregion

        # region: submit button
        def _submit_handler():
            nonlocal input_name, input_desc, input_cost, benefit_idx_select, current_submenu
            name, desc, cost = input_name.get(), input_desc.get(), input_cost.get()
            benefit_idx_select = benefit_idx_select.get()
            benefits = the_company.benefits
            match current_submenu:
                case 1:  # add
                    new_benefit = BenefitPlan()
                    new_benefit.set_name(name)
                    new_benefit.set_description(desc)
                    new_benefit.set_cost(float(cost))
                    if (not name) and (not desc) and (not cost):
                        msgbox.showerror("Error", "Please fill in all fields")

                    the_company.benefits.append(new_benefit)
                    if os.getenv("HRMGR_DB") == "TRUE":
                        benefit_repo.insert_one(new_benefit.dict(by_alias=True))

                    msgbox.showinfo("Success", f"Benefit plan {name} added")

                case 2:  # remove
                    _bnf = benefits[benefit_idx_select]
                    _bnf_name = _bnf.name

                    if benefit_idx_select is None:
                        msgbox.showerror("Error", "Please select a benefit plan to remove")
                        return

                    # remove the benefit from the company
                    the_company.benefits.remove(the_company.benefits[benefit_idx_select])
                    if os.getenv("HRMGR_DB") == "TRUE":
                        benefit_repo.delete_one({"_id": _bnf.id})

                    # remove the benefit from employees
                    for empl in the_company.employees:
                        if _bnf.name not in empl.benefits:
                            continue
                        empl.benefits.remove(_bnf.name)
                        if os.getenv("HRMGR_DB") == "TRUE":
                            employee_repo.update_one(
                                {"_id": empl.id}, {"$set": empl.dict(include={"benefits"})}, upsert=True
                            )
                    msgbox.showinfo("Success", f"Benefit plan {_bnf_name} removed")

                case 3:  # modify
                    if benefit_idx_select is None:
                        msgbox.showerror("Error", "Please select a benefit plan to modify")
                        return
                    if (not name) and (not desc) and (not cost):
                        msgbox.showerror("Error", "Please fill in at least one field")
                        return
                    _bnf = the_company.benefits[benefit_idx_select]
                    _bnf.set_name(name) if name else None
                    _bnf.set_description(desc) if desc else None
                    _bnf.set_cost(float(cost)) if cost else None

                    if os.getenv("HRMGR_DB") == "TRUE":
                        benefit_repo.update_one({"_id": _bnf.id}, {"$set": _bnf.dict(by_alias=True)}, upsert=True)

                    msgbox.showinfo("Success", "Benefit plan modified")

            self.__destroy_all_frames()
            self.__admin_add_rm_modify(current_submenu)

        ctk.CTkButton(master=main_frame, text="Submit", command=_submit_handler, **btn_action_style).grid(
            row=5, column=0, columnspan=3, pady=20
        )
        # endregion

    def __admin_apply_rm(self, default_submenu: int = 1):
        # 0: 2 buttons: apply, remove
        # 1: Table to choose employee | Table to choose benefit
        # 2: - if in apply: Apply button
        #    - if in remove: Benefits of this employee | Remove button
        main_frame = ctk.CTkFrame(master=self.right_frame)
        main_frame.grid(row=0, column=0)

        # region: variables
        first_row = ctk.CTkFrame(master=main_frame)
        first_row.grid(row=1, column=0, columnspan=2, padx=20)

        empl_idx_select = ctk.IntVar()
        bnf_idx_select = ctk.IntVar()
        # because later we will have index of benefits (in empl || not in empl), not the list of benefits in the company
        custom_bnfs: list[BenefitPlan] = []
        # a list of strings representing each benefit
        custom_bnf_items = tuple()
        # to store the frame of the benefits list, so we can refresh it each time another employee is selected
        bnf_list_frame = (True, ctk.CTkFrame(master=main_frame))

        current_submenu = 1
        # endregion

        # region: when user select an employee, update the benefits list
        def _update_bnf_list():
            nonlocal bnf_idx_select, empl_idx_select, current_submenu, custom_bnf_items, bnf_list_frame, custom_bnfs

            # get the employee
            _empl = the_company.employees[empl_idx_select.get()]

            # get the benefits (in/not in) the employee's benefits
            if current_submenu == 1:
                custom_bnf_items = tuple(
                    [f"{bnf.name} - {bnf.cost}" for bnf in the_company.benefits if bnf.name not in _empl.benefits]
                )
                custom_bnfs = [bnf for bnf in the_company.benefits if bnf.name not in _empl.benefits]
            if current_submenu == 2:
                custom_bnf_items = tuple()
                for bnf in _empl.benefits:
                    for _bnf in the_company.benefits:
                        if _bnf.name == bnf:
                            custom_bnf_items += (f"{_bnf.name} - {_bnf.cost}",)
                            break
                custom_bnfs = [bnf for bnf in the_company.benefits if bnf.name in _empl.benefits]

            # this list will be refreshed every time user select an employee
            bnf_list_frame[1].destroy()
            bnf_list_frame = display_list(
                _master=first_row,
                options=custom_bnf_items,
                returned_idx=[bnf_idx_select],
                err_msg="No benefits",
                place_row=1,
                place_col=1,
                colspan=1,
            )

        # this list is persistent so we can leave it out here
        display_list(
            _master=first_row,
            options=tuple([f"{empl.employee_id} - {empl.name}" for empl in the_company.employees]),
            returned_idx=[empl_idx_select],
            err_msg="No employees",
            place_row=1,
            place_col=0,
            colspan=1,
            cmd=_update_bnf_list,
        )
        # endregion

        # region: 2 buttons to switch between apply and remove submenu
        btn_apply = ctk.CTkButton(master=main_frame, text="Add benefit to employee", **btn_action_style)
        btn_remove = ctk.CTkButton(master=main_frame, text="Remove benefit from employee", **btn_action_style)
        btn_apply.grid(row=0, column=0, padx=10, pady=20)
        btn_remove.grid(row=0, column=1, padx=10, pady=20)

        def _apply():
            nonlocal btn_apply, btn_remove, current_submenu, bnf_list_frame, _update_bnf_list
            btn_apply.configure(state=DISABLED)
            btn_remove.configure(state=NORMAL)
            current_submenu = 1
            bnf_list_frame[1].destroy()
            _update_bnf_list()

        def _remove():
            nonlocal btn_apply, btn_remove, current_submenu, bnf_list_frame, _update_bnf_list
            btn_apply.configure(state=NORMAL)
            btn_remove.configure(state=DISABLED)
            current_submenu = 2
            bnf_list_frame[1].destroy()
            _update_bnf_list()

        btn_apply.configure(command=_apply)
        btn_remove.configure(command=_remove)

        match default_submenu:
            case 1:
                _apply()
            case 2:
                _remove()
        # endregion

        # region: submit button
        def _submit_handler():
            nonlocal empl_idx_select, bnf_idx_select, current_submenu
            _empl = the_company.employees[empl_idx_select.get()]
            _bnf = custom_bnfs[bnf_idx_select.get()]

            if current_submenu == 1:  # apply
                if not the_company.can_modify("benefits", _empl):
                    msgbox.showerror("Error", "Cannot modify benefits")
                    self.__destroy_all_frames()
                    self.__admin_apply_rm(current_submenu)
                    return
                _empl.benefits.append(_bnf.name)
                if os.getenv("HRMGR_DB") == "TRUE":
                    employee_repo.update_one({"_id": _empl.id}, {"$set": _empl.dict(include={"benefits"})}, upsert=True)
                msgbox.showinfo("Success", f"Benefit plan {_bnf.name} applied to {_empl.name}")
            elif current_submenu == 2:  # remove
                _empl.benefits.remove(_bnf.name)
                if os.getenv("HRMGR_DB") == "TRUE":
                    employee_repo.update_one({"_id": _empl.id}, {"$set": _empl.dict(include={"benefits"})}, upsert=True)
                msgbox.showinfo("Success", f"Benefit plan {_bnf.name} removed from {_empl.name}")

            self.__destroy_all_frames()
            self.__admin_apply_rm(current_submenu)

        ctk.CTkButton(master=main_frame, text="Submit", command=_submit_handler, **btn_action_style).grid(
            row=2, column=0, columnspan=2, pady=20
        )
        # endregion

    def __request(self):
        # 0: Table to choose benefit
        # 1: Request button

        main_frame = ctk.CTkFrame(master=self.right_frame)
        main_frame.grid(row=0, column=0)
        zero_row = ctk.CTkFrame(master=main_frame)
        zero_row.grid(row=0, column=0, padx=20, pady=(20, 0))

        # region: variables
        bnf_idx_select = ctk.IntVar()
        bnfs_empl_not_in = tuple(
            bnf for bnf in the_company.benefits if bnf.name not in the_company.logged_in_employee.benefits
        )
        bnf_items = tuple(f"{bnf.name} - {bnf.cost}" for bnf in bnfs_empl_not_in)
        # endregion

        # region: table to choose benefit
        display_list(
            _master=zero_row,
            options=bnf_items,
            returned_idx=[bnf_idx_select],
            err_msg="No benefits",
            place_row=1,
            place_col=0,
            colspan=1,
        )
        # endregion

        # region: request button
        def _request_handler():
            nonlocal bnf_idx_select
            _bnf = bnfs_empl_not_in[bnf_idx_select.get()]

            if the_company.logged_in_employee in _bnf.pending_requests:
                msgbox.showinfo("Error", "You have already requested this benefit")
                return

            _bnf.pending_requests.append(the_company.logged_in_employee)

            if os.getenv("HRMGR_DB") == "TRUE":
                benefit_repo.update_one({"_id": _bnf.id}, {"$set": _bnf.dict(include={"pending_requests"})}, upsert=True)
            msgbox.showinfo("Success", f"Benefit plan {_bnf.name} requested")
            merge_callable(self.__destroy_all_frames, self.__request)()

        ctk.CTkButton(master=main_frame, text="Request", command=_request_handler, **btn_action_style).grid(
            row=1, column=0, pady=20
        )
        # endregion

    def __admin_resolve(self):
        # 0: Table to choose benefit | Table to choose employee
        # 1: Approve button | Reject button

        main_frame = ctk.CTkFrame(master=self.right_frame)
        main_frame.grid(row=0, column=0)

        # region: variables
        bnf_idx_select = ctk.IntVar()
        empl_idx_select = ctk.IntVar()

        bnfs_have_pending: list[BenefitPlan] = []
        bnf_item_have_pending: tuple[str] = tuple()

        # this changes every time the user select a benefit
        pending_empls: list[Employee] = []

        zero_row = ctk.CTkFrame(master=main_frame)
        zero_row.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 0))
        empl_list_frame = (True, ctk.CTkFrame(master=main_frame))
        # endregion

        # region: when user select a benefit, update the employee list
        def _update_empl_list():
            nonlocal empl_idx_select, bnfs_have_pending, bnf_item_have_pending, pending_empls, empl_list_frame
            bnfs_have_pending = [bnf for bnf in the_company.benefits if bnf.pending_requests]

            if len(bnfs_have_pending) == 0:
                return

            bnf_item_have_pending = tuple(f"{bnf.name} - {bnf.cost}" for bnf in bnfs_have_pending)
            pending_empls = bnfs_have_pending[bnf_idx_select.get()].pending_requests

            empl_list_frame[1].destroy()
            empl_list_frame = display_list(
                _master=zero_row,
                options=tuple(f"{empl.name} - {empl.employee_id}" for empl in pending_empls),
                returned_idx=[empl_idx_select],
                err_msg="No pending requests",
                place_row=1,
                place_col=1,
                colspan=1,
            )

        _update_empl_list()
        display_list(
            _master=zero_row,
            options=bnf_item_have_pending,
            returned_idx=[bnf_idx_select],
            err_msg="No benefits",
            place_row=1,
            place_col=0,
            colspan=1,
            cmd=_update_empl_list,
        ) if len(bnfs_have_pending) > 0 else None
        # endregion

        # region: approve button | reject button
        btn_approve = ctk.CTkButton(master=main_frame, text="Approve", **btn_action_style)
        btn_approve.grid(row=1, column=0, pady=20)
        btn_reject = ctk.CTkButton(master=main_frame, text="Reject", **btn_action_style)
        btn_reject.grid(row=1, column=1, pady=20)

        def _approve_handler():
            nonlocal bnf_idx_select, empl_idx_select, bnfs_have_pending, pending_empls
            _bnf = bnfs_have_pending[bnf_idx_select.get()]
            _empl = pending_empls[empl_idx_select.get()]

            if not the_company.can_modify("benefits", _empl):
                msgbox.showinfo("Error", "You do not have permission to modify this employee")
                return

            _bnf.pending_requests.remove(_empl)
            _bnf.enrolled_employees.append(_empl)
            if os.getenv("HRMGR_DB") == "TRUE":
                benefit_repo.update_one(
                    {"_id": _bnf.id}, {"$set": _bnf.dict(include={"pending_requests", "enrolled_employees"})}, upsert=True
                )
            msgbox.showinfo("Success", f"Benefit plan {_bnf.name} approved for {_empl.name}")
            merge_callable(self.__destroy_all_frames, self.__admin_resolve)()

        def _reject_handler():
            nonlocal bnf_idx_select, empl_idx_select, bnfs_have_pending, pending_empls
            _bnf = bnfs_have_pending[bnf_idx_select.get()]
            _empl = pending_empls[empl_idx_select.get()]

            _bnf.pending_requests.remove(_empl)
            if os.getenv("HRMGR_DB") == "TRUE":
                benefit_repo.update_one({"_id": _bnf.id}, {"$set": _bnf.dict(include={"pending_requests"})}, upsert=True)
            msgbox.showinfo("Success", f"Benefit plan {_bnf.name} rejected for {_empl.name}")
            merge_callable(self.__destroy_all_frames, self.__admin_resolve)()

        btn_approve.configure(command=_approve_handler)
        btn_reject.configure(command=_reject_handler)
        # endregion

        # region: if no pending requests, show message
        if len(bnfs_have_pending) == 0:
            for widget in zero_row.winfo_children():
                widget.destroy()
            ctk.CTkLabel(master=zero_row, text="No pending requests", **label_desc_style).grid(
                row=0, column=0, pady=20, padx=20
            )
            btn_approve.configure(state=DISABLED)
            btn_reject.configure(state=DISABLED)
        # endregion

    def __view_details(self):
        # 0: List of benefits | List of employees enrolled in that benefit
        # 1: Description of benefit

        main_frame = ctk.CTkFrame(master=self.right_frame)
        main_frame.grid(row=0, column=0)

        # region: variables
        zero_row = ctk.CTkFrame(master=main_frame)
        zero_row.grid(row=0, column=0, columnspan=2)
        bnf_idx_select = ctk.IntVar()
        empl_list_frame = (True, ctk.CTkFrame(master=zero_row))
        bnf_detail_widget = ctk.CTkLabel(master=main_frame)
        # endregion

        # region: when user select a benefit, update the employee list
        bnfs_items = tuple(f"{bnf.name} - {bnf.cost}" for bnf in the_company.benefits)

        def bnf_select_handler():
            nonlocal bnf_idx_select, bnfs_items, zero_row, bnf_detail_widget, empl_list_frame
            _bnf = the_company.benefits[bnf_idx_select.get()]
            _empls_in_bnf = _bnf.enrolled_employees
            _empl_items = tuple(f"{empl.name} - {empl.employee_id}" for empl in _empls_in_bnf)
            empl_list_frame[1].destroy()
            empl_list_frame = display_list(
                _master=zero_row,
                options=_empl_items,
                err_msg="No employees enrolled",
                place_row=1,
                place_col=1,
                colspan=1,
                selectable=False,
            )

            # update description
            bnf_detail_widget.destroy()
            bnf_detail_widget = ctk.CTkLabel(master=main_frame, text=_bnf.description)
            bnf_detail_widget.grid(row=1, column=0, columnspan=2, pady=20, padx=20)

        display_list(
            _master=zero_row,
            options=bnfs_items,
            returned_idx=[bnf_idx_select],
            err_msg="No benefits",
            place_row=1,
            place_col=0,
            colspan=1,
            cmd=bnf_select_handler,
        ) if len(bnfs_items) > 0 else None
        # endregion

        # if there's no benefit, display err msg instead of `display_list`
        if len(bnfs_items) == 0:
            for widget in zero_row.winfo_children():
                widget.destroy()
            zero_row.destroy()
            zero_row = ctk.CTkLabel(master=main_frame, text="No benefits", **label_desc_style)
            zero_row.grid(row=0, column=0, pady=20, padx=20, columnspan=2)

    def __admin_empls_w_o_benefit(self):
        main_frame = ctk.CTkFrame(master=self.right_frame)
        main_frame.grid(row=0, column=0)

        # empls_w_o_bnf = tuple(empl for empl in the_company.employees if len(empl.benefits) == 0)
        empls_w_o_bnf = tuple(
            f"{empl.name} - {empl.employee_id}" for empl in the_company.employees if len(empl.benefits) == 0
        )
        display_list(
            _master=main_frame,
            options=empls_w_o_bnf,
            err_msg="No employees",
            place_row=1,
            place_col=0,
            colspan=1,
            selectable=False,
        )
