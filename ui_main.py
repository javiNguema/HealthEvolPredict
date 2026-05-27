
import tkinter as tk
from tkinter import font, ttk
from turtle import heading
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import ImageTk
from typing import Callable, Any
from tkinter import messagebox
from tkinter import filedialog
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import threading
import os 
from functools import partial
import time


from bitmaps import images, chatbot_image
from dataLoader import retrieve_data
from db_connection import DBConnectionManager
from pca_analysis import perform_pca
from model_engine import run_pycaret_pipeline, run_custom_scikit_model
from sklearn.metrics import confusion_matrix, PrecisionRecallDisplay, RocCurveDisplay
from ollama_installer import ensure_ollama_setup

# Evita que librerías internas bifurquen hilos inseguros que provoquen el 'abort' en macOS
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

padx = 10
pady = 5
psize = 12
top_action_bar_containerbar_width = 350
treeview_height = 22
ysb_width = 15
xsb_width = 15
image_width = 25
image_height = 25
navbar_frame_width = 900
blue_widget = '#3b8cc6'
row_height = 30
nav_bar_rowheight = 45

heading_width = 1400
project_panel = False
grey_color_rows = '#ececec'
provisional_db = {'Projects': [], 'Suppliers': []}
is_on_transaction = False
tree_table_width_expanded = 900

fig_height = 10
fig_width = 14
fig_ipad = 0.1
h_ipady = 0.1




metric_translations = {
    'count': 'Cantidad', 
    'mean': 'Promedio', 
    'std': 'Desv. Est.', 
    'min': 'Mínimo', 
    "25%": " 25% percentil", 
    "50%": " 50% percentil",
    "75%": " 75% percentil",
    'max': 'Máximo',
    'missing': 'Valores Faltantes',
    'non_null': 'Valores No Nulos',
    'unique': 'Valores Únicos',         
    'top': 'Valor Más Frecuente',        
    'freq': 'Frecuencia de Top'          
}

class MainUI:
    is_on_patient_data_panel: bool = False
    is_on_exploration_panel: bool = False
    is_on_db_config_pannel: bool = False
    is_on_models_panel: bool = False
    is_on_chatbot_panel:bool = False

    model_features: Any | None = None
    model_outputs: Any | None = None
    db_tables_iid: dict = {}

    is_add_patient_collapsed: bool = True
    table_height: float = None # type: ignore
    is_on_navbar: bool = False
    is_row_selected: bool = False
    is_connected: bool = False
    login_win_action: Callable = None # type: ignore
    

    def __init__(self, toplvl: ctk.CTkToplevel, user: list | None = None, on_close_func:Callable|None = None) -> None:

        self.db_manager = DBConnectionManager()
        if hasattr(self, "user_loggged_in"):
            print(f'the sat attribute is {self.user_logged_in}') # type: ignore

        self.toplvl = toplvl
        self.on_close_func = on_close_func
        system_screen_width = toplvl.winfo_screenwidth()
        system_screen_height = toplvl.winfo_screenheight()
        self.trained_model = None    
        self.model_features = []      
        self.model_outputs = None     


        self.log_font =("helvetica", 12, 'bold')
        size_font_all = 15 
        name_font = 'helvetica' 
        font_size_navbar = 18
        font_name_navbar = 'helvetica'
        

        size_font_title = 18
        name_font_title = 'helvetica'

        self.normal_font = (name_font, size_font_all)
        self.font_navbar = (font_name_navbar, font_size_navbar)
        self.title_font = (name_font_title, size_font_title)

        self.main_width = system_screen_width 
        self.main_height = system_screen_height 

        self.tree_table_width = int((4/5)*self.main_width) 
        self.tree_table_height = int((12/14)*self.main_height) 
        self.navbar_width = int((1/5.4)*self.main_width) 
        self.hidden_frame_width = int((1/5)*self.main_width)

        self.toplvl.geometry(f'{self.main_width}x{self.main_height}')
        self.toplvl.title('ProjectCare')
        self.menubar()
        self.win_segments()
        self.navigationBar()
        self.patient_data_panel_segment()
        self.top_action_bar_container()
        self.show_db_config_panel()
        self.show_chatbot_panel()
        self.show_models_panel()
        

        


        cols_placeholder = []
        n = 10
        for i in range(n):
            if i < n-1:
                cols_placeholder.append(f'column {i}')
            else:
                cols_placeholder.append("column...")
                break
        
        self.desc_table_patients = CustomTable(
            master=self.table_frame,
            columns=cols_placeholder,
            row_height=row_height,
            font_data=(self.normal_font[0], 13),
            font_header=(self.normal_font[0], 14, "bold")
        )
        self.desc_table_patients.pack(fill="both", expand=True)

        start_session_logs = partial(ensure_ollama_setup, logs=self.log)

        threading.Thread(target=start_session_logs, daemon=True).start()

        self.log(message='Panel de Datos de Paciente. Datos de paciente no cargados...', username=user) # type: ignore



    def win_segments(self) -> None:
        self.toplvl.grid_rowconfigure(0, weight=1)
        self.toplvl.grid_columnconfigure(0, weight=0)  # Left Navbar frame column
        self.toplvl.grid_columnconfigure(1, weight=1)  # Right main frame content column

        self.navBarFrame = ctk.CTkFrame(master=self.toplvl, width=self.navbar_width, fg_color='transparent')
        self.navBarFrame.grid(row=0, column=0, sticky='nsew', padx=padx, pady=pady)
        self.navBarFrame.grid_propagate(False)

        self.content_frame = ctk.CTkFrame(master=self.toplvl, fg_color='transparent')
        self.content_frame.grid(row=0, column=1, sticky='nsew')
        self.log_frame = ctk.CTkFrame(master=self.content_frame, border_width=1)
        self.log_frame.pack(side='top', pady=pady, anchor='nw', fill='x')

        self.patient_data_panel = ctk.CTkFrame(master=self.content_frame, fg_color='transparent')
        self.project_panel_frame = ctk.CTkFrame(master=self.content_frame, fg_color='transparent')
        self.exploration_panel_frame = ctk.CTkFrame(master=self.content_frame, fg_color='transparent')
        self.db_config_frame = ctk.CTkFrame(master=self.content_frame, fg_color='transparent')
                                                               
        self.patient_data_panel.pack_configure(side='left', anchor='nw', padx=0, expand=True, fill='both')

    def on_tree_select(self, event):
        selected_item = self.navtreeview.focus()
        if not selected_item:
            return

        item_text = self.navtreeview.item(selected_item, "text")
        parent_id = self.navtreeview.parent(selected_item)

        on_click_actions = {
            "Modelos": lambda: self.switch_panel('models'), # Updated from print
            "Datos de Pacientes": lambda: self.switch_panel('Datos de Pacientes'),
            "Exploración": lambda: self.switch_panel('exploration'),
            "BD": lambda: self.switch_panel('db'),
            "Chatbot": lambda: self.switch_panel('chatbot'),
            "Salir": self.on_close_func
        }

        if parent_id == "":
            if isinstance(item_text, tuple):
                item_text = item_text[0]
            action = on_click_actions.get(item_text)
            if action:
                action()
        else:
            parent_text = self.navtreeview.item(parent_id, "text")
            if isinstance(parent_text, tuple):
                parent_text = parent_text[0]
            
            if parent_text == "BD":
                print(f"the item tex is: {item_text}")
                self.load_db_table(item_text)
    
    
        


    def navigationBar(self):
        self.node_ids = {'Modelos': [], 'Datos de Pacientes': [], 'Exploración': [], "BD": [], "Chatbot": [], 'Salir': []}
        self.child_node_ids = {'Modelos': [], 'Datos de Pacientes': [], 'Exploración': [], "BD": [], "Chatbot": [], 'Salir': []}
        self.branched_nodes = {'Modelos': [], 'Datos de Pacientes': [], 'Exploración': [], "BD": [], "Chatbot": [], 'Salir': []}

        self.images_adapted = {}
        for name, image in images.items():
            imgTk = ImageTk.PhotoImage(image)
            self.images_adapted[name] = imgTk

        style_nav = ttk.Style()
        style_nav.configure("TreeviewNav.Treeview", rowheight=nav_bar_rowheight, font=self.font_navbar)  
        style_nav.configure("TreeviewNav.Row", font=self.font_navbar)

        self.navBarFrame.grid_rowconfigure(0, weight=1)
        self.navBarFrame.grid_columnconfigure(0, weight=1)

        self.navtreeview = ttk.Treeview(
            master=self.navBarFrame, 
            selectmode=tk.BROWSE, 
            columns=('status',),
            style="TreeviewNav.Treeview"
        )
        self.navtreeview.configure(show='tree')
        
        status_col_width = 40 
        
        ysb = ctk.CTkScrollbar(
            self.navBarFrame,
            width=ysb_width,
            orientation='vertical',
            cursor='hand2',
            button_color='#3b8cc6',
            button_hover_color='SteelBlue',
            command=self.navtreeview.yview
        )
        
        self.navtreeview.heading(column='#0', text="Browser", anchor="w")
        tree_main_width = self.navbar_width - status_col_width - ysb_width - 10

        self.navtreeview.column(column='#0', width=tree_main_width, stretch=True)
        self.navtreeview.column('status', width=status_col_width, anchor='center', stretch=False)

        self.icons = zip(self.branched_nodes.items(), self.images_adapted.values())
        
        for (key, lst_value), image in self.icons:
            node_id = self.navtreeview.insert('', 'end', text=str(key), image=image, values=("",))  # type: ignore
            self.node_ids[key] = node_id  # type: ignore
            if key == 'BD':
                self.navtreeview.set(node_id, column="status", value='⚠️')
            
            for child in lst_value:
                iid = self.navtreeview.insert(node_id, 'end', text=child, values=("",))
                self.child_node_ids[key].append(iid)

        self.navtreeview.grid(row=0, column=0, sticky='nsew')
        ysb.grid(row=0, column=1, sticky='ns')
        self.navtreeview.configure(yscrollcommand=ysb.set)

        self.navtreeview.bind("<<TreeviewSelect>>", self.on_tree_select)

    def show_db_config_panel(self) -> None:
        """Generates the MySQL connection configuration interface within the main container."""
        self.db_config_frame.configure(width=self.tree_table_width, height=self.tree_table_height)
        
        for widget in self.db_config_frame.winfo_children():
            widget.destroy()

        title_lbl = ctk.CTkLabel(
            master=self.db_config_frame, 
            text="Configuración de Conexión MySQL", 
            font=(self.title_font[0], 18, "bold")
        )
        title_lbl.pack(anchor='nw', pady=(0, 30), padx=0)

        form_frame = ctk.CTkFrame(master=self.db_config_frame)
        form_frame.pack(anchor='nw', pady=(5, 20), padx=0)

        self.db_fields = {}
        fields_setup = [
            ("Host / Servidor:", "host", "s501.sureserver.com"),
            ("Puerto:", "port", "3306"),
            ("Usuario:", "user", "Student"),
            ("Contraseña:", "password", "Barcelona2024*"),
            ("Base de Datos:", "database", "metales_traking")
        ]

        for label_text, key, default_val in fields_setup:
            row = ctk.CTkFrame(master=form_frame, fg_color="transparent")
            row.pack(fill='x', pady=8)

            lbl = ctk.CTkLabel(master=row, text=label_text, font=(self.normal_font[0], 13), width=150, anchor='w')
            lbl.pack(side='left', padx=(5, 10))

            show_mask = "*" if key == "password" else ""
            entry = ctk.CTkEntry(master=row, font=(self.normal_font[0], 13), width=350, show=show_mask)
            entry.insert(0, default_val)
            entry.pack(side='left', expand=True, padx=(0, 5))

            self.db_fields[key] = entry

        actions_row = ctk.CTkFrame(master=self.db_config_frame, fg_color="transparent")
        actions_row.pack(anchor='w', fill='x', pady=20, padx=0)

        self.test_btn = ctk.CTkButton(
            master=actions_row,
            text="Probar Conexión",
            font=(self.normal_font[0], 12, "bold"),
            fg_color="#5a6268",
            width=150,
            command=self.on_test_connection_click
        )
        self.test_btn.pack(side='left', padx=(0, 15))

        self.btn_disconnect_conn = ctk.CTkButton(
            master=actions_row, 
            text="Desconectar", 
            fg_color="#dc3545",      
            hover_color="#bd2130",
            command=self.on_disconnect_connection_click
        )
        self.btn_disconnect_conn.pack(side="left", padx=5, pady=10)

    def on_test_connection_click(self) -> None:
        """Runs the validation logic on an asynchronous background thread to prevent GUI lockups."""
        raw_config = {k: v.get().strip() for k, v in self.db_fields.items()}
        
        # Visually disable buttons during thread lifespan
        self.test_btn.configure(state="disabled", text="Conectando...")
        
        def connection_worker():
            success, message = self.db_manager.test_connection(raw_config)
            # Route response updates back through safely on the Main Thread event loop loop
            self.toplvl.after(0, lambda: self._handle_connection_result(success, message, raw_config))

        threading.Thread(target=connection_worker, daemon=True).start()

    def _handle_connection_result(self, success: bool, message: str, raw_config: dict) -> None:
        """Main Thread UI safe sync callback pipeline."""
        self.test_btn.configure(state="normal", text="Probar Conexión")
        
        if success:
            messagebox.showinfo(title="Éxito", icon='info', message=message)
            node_id = self.node_ids.get("BD")
            if node_id:
                self.navtreeview.set(node_id, column='status', value='🟢')   # type: ignore
            self.db_manager.save_configuration(raw_config)
            
            db_tables = self.db_manager.get_tables()
            
            if node_id:
                for child in self.navtreeview.get_children(node_id):  # type: ignore
                    self.navtreeview.delete(child)
            
            self.branched_nodes['BD'] = []
            max_num_tables = 16

            for t in db_tables:
                if node_id:
                    child_iid = self.navtreeview.insert(parent=node_id, index="end", text=t, values=("",))  # type: ignore
                    self.db_tables_iid[t] = child_iid 
                self.branched_nodes['BD'].append(t)
                
                max_num_tables -= 1
                if max_num_tables <= 0:
                    break
            
            self.is_connected = True
        else:
            messagebox.showerror(title="Error", icon='error', message=message)

    def on_disconnect_connection_click(self) -> None:
        """Closes the active database connection, resets UI tree elements, and updates status."""
        if not self.is_connected:
            messagebox.showinfo(title="Estado de Conexión", message="No existe conexión a base de datos.")
            return
        
        node_id = self.node_ids.get("BD")
        if node_id:
            self.navtreeview.set(node_id, column='status', value='⚠️')   # type: ignore
            for child in self.navtreeview.get_children(node_id):  # type: ignore
                self.navtreeview.delete(child)
        
        self.branched_nodes['BD'] = []
        self.db_manager.close_connection()
        self.is_connected = False
            
        messagebox.showinfo(title="Desconectado", message="La conexión a la base de datos se ha cerrado correctamente.")

    def patient_data_panel_segment(self) -> None:

        self.main_children_holder = ctk.CTkFrame(master=self.patient_data_panel, fg_color='transparent')
        self.main_children_holder.grid(row=0, column=1, sticky="wn", padx=0)

        self.patient_data_panel.grid_rowconfigure(0, weight=1)
        self.patient_data_panel.grid_columnconfigure(1, weight=1)

        
        self.user_log_lbl = ctk.CTkLabel(
            master=self.log_frame, 
            text="User: Not Authenticated", 
            font=self.log_font if hasattr(self, 'log_font') else ("Arial", 10)
        )
        self.user_log_lbl.pack(side='left', padx=15, pady=5)

        self.status_log_lbl = ctk.CTkLabel(
            master=self.log_frame, 
            text="System status: Initialization Idle", 
            font=self.log_font if hasattr(self, 'log_font') else ("Arial", 10, "normal"),
            text_color="gray"
        )
        self.status_log_lbl.pack(side='right', padx=15, pady=5)



        self.main_command_frame = ctk.CTkFrame(master=self.main_children_holder, fg_color='transparent')
        self.main_command_frame.pack(side='top', pady=pady, anchor='nw', fill='x')

        self.table_holder_frame = ctk.CTkFrame(master=self.main_children_holder)
        self.table_holder_frame.pack(side='top', pady=pady, anchor='nw', fill='both', expand=True)
        
        self.table_frame = ctk.CTkFrame(self.table_holder_frame, fg_color='transparent')
        self.table_frame.pack(side='top', fill='both', expand=True, padx=padx, pady=pady)

        self.is_on_patient_data_panel = True 
        self.view.entryconfig(index=self.view_options['Datos de Pacientes'], state='disabled')


    def log(self, message: str = None, username: str = None) -> None: # type: ignore
        """
        Dynamically refreshes runtime operational telemetry and employee 
        identity logs inside the persistent top tracking layout subframe.
        """
        if username is not None:
            if hasattr(self, 'user_log_lbl') and self.user_log_lbl.winfo_exists():
                self.user_log_lbl.configure(text=f"Usuario: {username}")

        if message is not None:
            if hasattr(self, 'status_log_lbl') and self.status_log_lbl.winfo_exists():
                self.status_log_lbl.configure(text=f"Estado: {message}")
                
        self.toplvl.update_idletasks()



    def view_data(self, columns, data) -> None:
        if hasattr(self, 'desc_table_patients'):
            self.desc_table_patients.tree_config(columns=columns, data_list=data)
            


    def load_data(self, event=None) -> None:
        file_path = filedialog.askopenfilename(
            title="Seleccionar Datos (.csv)",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
    
        if file_path:
            # try:
            new_columns, new_raw_data, self.loadedData = retrieve_data(file_path)
            self.view_data(columns=new_columns, data=new_raw_data)
            self.log(message=f'{len(new_raw_data)} datos de Pacientes Cargados con éxito')
            # messagebox.showinfo("Éxito", f"Se han cargado {len(new_raw_data)} registros.")
            threading.Thread(target=time.sleep(1), daemon=True).start()
            
            self.log(message='Panel de Datos de Paciente. Datos de paciente cargados')


    def top_action_bar_container(self) -> None: 
        # search_btn = ctk.CTkButton(master=self.main_command_frame, text='Buscar')
        # search_bar = ctk.CTkEntry(master=self.main_command_frame, width=top_action_bar_containerbar_width, placeholder_text="id de paciente")
        # search_btn.pack_configure(side='left', anchor='nw', padx=padx)
        # search_bar.pack_configure(side='left', anchor='nw', padx=padx)

        upload_btn = ctk.CTkButton(
            master=self.main_command_frame, 
            text='Añadir datos', 
            fg_color="#28a745",  
            hover_color="#218838",
        )

        self.clear_table_btn = ctk.CTkButton(
            master=self.main_command_frame, 
            text='Vaciar tabla',
            command=self.clear_main_table 
        )

        upload_btn.pack(side='left', anchor='w', padx=(0, 5))
        self.clear_table_btn.pack(side='left', anchor='w', padx=(0, 5))
        upload_btn.bind("<Button-1>", self.load_data)

        self.toplvl.update_idletasks()

    def clear_main_table(self) -> None:
        self.log(message=f"Panel de Datos de Paciente: Eliminando tabla...")
        time.sleep(0.5)
        self.clear_table_btn.configure(state='disable', text='Vaciando tabla...')
        self.desc_table_patients.clear()
        self.clear_table_btn.configure(state='normal', text='Vaciar tabla')
        self.log(message=f"Panel de Datos de Paciente. Esperando datos de paciente...")
        

    def _hide_all_panels(self):
        """Hide all panels safely."""
        for panel in [
            self.patient_data_panel,
            self.exploration_panel_frame,
            self.db_config_frame,
            self.models_panel_frame,
            self.chatbot_panel
        ]:
            try:
                panel.pack_forget()
            except:
                pass

    def _reset_flags(self):
        self.is_on_patient_data_panel = False
        self.is_on_exploration_panel = False
        self.is_on_db_config_pannel = False
        self.is_on_models_panel = False
        self.is_on_chatbot_panel = False

    def _update_menu_state(self, active: str):
        states = {
            'Datos de Pacientes': 'normal',
            'Exploración': 'normal',
            'Conectar a BD': 'normal',
            'Modelado ML': 'normal',
            'Chatbot': 'normal'
        }

        if active == 'Datos de Pacientes':
            states['Datos de Pacientes'] = 'disabled'
        elif active == 'exploration':
            states['Exploración'] = 'disabled'
        elif active == 'db':
            states['Conectar a BD'] = 'disabled'
        elif active == 'models':
            states['Modelado ML'] = 'disabled' # Add this
        elif active == 'Chatbot':
            states['Chatbot'] = 'disabled' # Add this

        for key, state in states.items():
            if key in self.view_options:
                self.view.entryconfig(index=self.view_options[key], state=state)


    def switch_panel(self, target: str):
        current = (
            'Datos de Pacientes' if self.is_on_patient_data_panel else
            'exploration' if self.is_on_exploration_panel else
            'db' if self.is_on_db_config_pannel else 
            'models' if self.is_on_models_panel else 
            'chatbot' if self.is_on_chatbot_panel else None
        )

        if current == target:
            return

        self._hide_all_panels()
        self._reset_flags()

        if target == 'Datos de Pacientes':
            self._show_panel(self.patient_data_panel)
            self.is_on_patient_data_panel = True
            if not self.desc_table_patients.is_loaded:
                self.log(message='Panel de Datos de Pacientes: Datos no cargados...')
            else:
                self.log(message='Panel de Datos de Pacientes: Datos cargados...')
        elif target == 'exploration':
            if not self.exploration_panel_frame.winfo_children():
                self.show_exploration_panel()
            self._show_panel(self.exploration_panel_frame)
            self.log(message='Panel de exploración de datos...')
            self.is_on_exploration_panel = True
        
        elif target == 'db':
            if not self.db_config_frame.winfo_children():
                self.show_db_config_panel()
            self._show_panel(self.db_config_frame)
            self.log(message='Panel de conexión a base de datos...')
            self.is_on_db_config_pannel = True
        
        elif target == 'models':
            if not self.models_panel_frame.winfo_children():
                self.show_models_panel()
            self._show_panel(self.models_panel_frame)
            self.log(message='Panel de Modelos...')
            self.is_on_models_panel = True
        

        elif target == 'chatbot':
            if not self.chatbot_panel.winfo_children():
                self.show_chatbot_panel()
            self._show_panel(self.chatbot_panel)
            self.log(message='Panel de Chatbot (consultas BD)...')
            self.is_on_chatbot_panel = True

        self._update_menu_state(target)
        self.toplvl.update_idletasks()
    

    def switch_to_models_panel(self, event=None):
        self.switch_panel('models')
    

    def  show_models_panel(self) -> None:
        """Generates the interactive Machine Learning models workspace."""

        self.models_panel_frame = ctk.CTkFrame(master=self.content_frame, fg_color='transparent')
        self.models_panel_frame.configure(width=self.tree_table_width, height=self.tree_table_height)
        
        config_box = ctk.CTkFrame(master=self.models_panel_frame)
        config_box.pack(side="top", fill="x", padx=0, pady=pady)
        
        title_lbl = ctk.CTkLabel(master=config_box, text="Configuración de Modelos Machine Learning", font=(self.title_font[0], 15, "bold"))
        title_lbl.grid(row=0, column=0, columnspan=4, sticky="w", padx=15, pady=(10, 5))
        
        # Model Selector Dropdown (6 models including PyCaret Auto-Evaluation)
        ctk.CTkLabel(master=config_box, text="Algoritmo:", font=(self.normal_font[0], 12)).grid(row=1, column=0, padx=(20, 5), pady=8, sticky="w")
        self.model_selector = ctk.CTkOptionMenu(
            master=config_box,
            values=[
                "Evaluación Automática (PyCaret)",
                "Regresión Logística", 
                "Bosques Aleatorios (Random Forest)", 
                "Máquinas de Vector de Soporte (SVM)", 
                "Gradiente Aumentado (XGBoost)", 
                "K-Vecinos Cercanos (KNN)"
            ],
            width=260,
            command=self._on_model_algorithm_changed
        )
        self.model_selector.grid(row=1, column=1, padx=5, pady=8, sticky="w")
        
        # Visually Appealing Split Data Control (Slider + Synchronized Label View)
        ctk.CTkLabel(master=config_box, text="División Entrenamiento:", font=(self.normal_font[0], 12)).grid(row=1, column=2, padx=(30, 5), pady=8, sticky="w")
        slider_frame = ctk.CTkFrame(master=config_box, fg_color="transparent")
        slider_frame.grid(row=1, column=3, padx=5, pady=8, sticky="w")
        
        self.split_val_lbl = ctk.CTkLabel(master=slider_frame, text="80% / 20%", font=(self.normal_font[0], 11, "bold"), width=70)
        self.split_slider = ctk.CTkSlider(
            master=slider_frame, 
            from_=0.5,  # type: ignore
            to=0.9,  # type: ignore
            number_of_steps=40,
            command=lambda val: self.split_val_lbl.configure(text=f"{int(val*100)}% / {100-int(val*100)}%")
        )
        self.split_slider.set(0.80)
        self.split_slider.pack(side="left", padx=5)
        self.split_val_lbl.pack(side="left", padx=5)
        
        # Dynamic Model Parameters Area
        self.params_subframe = ctk.CTkFrame(master=config_box, fg_color="transparent")
        self.params_subframe.grid(row=2, column=0, columnspan=4, sticky="ew", padx=20, pady=(5, 10))
        self._on_model_algorithm_changed(self.model_selector.get())
        
        # Action Control Panel Row
        actions_bar = ctk.CTkFrame(master=self.models_panel_frame, fg_color="transparent")
        actions_bar.pack(side="top", fill="x", padx=0, pady=2)
        
        btn_select_vars = ctk.CTkButton(master=actions_bar, text="Definir variables (X/Y)", fg_color="#5a6268", font=(self.normal_font[0], 12, "bold"), command=self.open_variable_selection_modal)
        btn_select_vars.pack(side="left", padx=(5, 15))
        
        self.btn_run_model = ctk.CTkButton(master=actions_bar, text="Entrenar Modelo", fg_color=blue_widget, font=(self.normal_font[0], 12, "bold"), command=self._on_execute_modeling_click)
        self.btn_run_model.pack(side="left", padx=5)

        self.btn_save_model = ctk.CTkButton(
            master=actions_bar, # Ajustar al contenedor de tus botones actuales
            text="💾 Guardar Modelo",
            fg_color="#28a745", # Color verde de persistencia
            hover_color="#218838",
            command=self._on_save_model_as_click
        )
        self.btn_save_model.pack(side ='left', padx=10, pady=10)
        
        
        self.models_output_tabview = ctk.CTkTabview(master=self.models_panel_frame, width=self.tree_table_width)
        self.models_output_tabview.pack(side="top", fill="both", expand=True, padx=0, pady=pady)
        
        self.m_tab_metrics = self.models_output_tabview.add("Métricas y Tablas")
        self.m_tab_plots = self.models_output_tabview.add("Visualizaciones de Modelo")
        
        # Setup clean default previews inside tabs
        self.m_tab_metrics.grid_columnconfigure(0, weight=1)
        self.m_tab_metrics.grid_rowconfigure(0, weight=1)
        self.model_metrics_table = CustomTable(master=self.m_tab_metrics, 
                                               columns=["Métrica de Rendimiento", "Conjunto Entrenamiento", "Conjunto Validación"],
                                               font_data=(self.normal_font[0], 13),
                                               row_height=row_height,
                                                font_header=(self.normal_font[0], 14, "bold"))
        self.model_metrics_table.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.m_tab_plots.grid_columnconfigure(0, weight=1)
        self.m_tab_plots.grid_rowconfigure(0, weight=1)
        self.model_plot_display = ctk.CTkFrame(master=self.m_tab_plots, fg_color="transparent")
        self.model_plot_display.pack(fill="both", expand=True)
        self._render_empty_model_plot()

    

    def _on_model_algorithm_changed(self, selected_model: str) -> None:
        """Dynamically repaints custom parameter options based on chosen pipeline algorithm."""
        for widget in self.params_subframe.winfo_children():
            widget.destroy()
            
        if selected_model.startswith("Evaluación Automática"):
            # Container to keep the metrics label and checkboxes perfectly inline on a single row
            row_container = ctk.CTkFrame(master=self.params_subframe, fg_color="transparent")
            row_container.pack(side="left", fill="x", expand=True)
            
            lbl = ctk.CTkLabel(master=row_container, text="Métricas de Optimización:", font=(self.normal_font[0], 12, "bold"))
            lbl.pack(side="left", padx=(0, 15))
            
            # List of metrics to evaluate in the PyCaret pipeline matrix"
            metrics_list = ["Accuracy", "AUC", "Recall", "Precision", "F1-Score", "Kappa", "MCC", "TT (Sec)"]
            self.metric_checkbox_vars = {} # Dictionary to store Boolean states for runtime evaluation
            
            for metric in metrics_list:
                # Variable tracking frame to read values (.get() checking True/False)
                var = tk.BooleanVar(value=True if metric in metrics_list[:4] else False)
                self.metric_checkbox_vars[metric] = var
                
                chk = ctk.CTkCheckBox(
                    master=row_container, 
                    text=metric, 
                    variable=var,
                    font=(self.normal_font[0], 11),
                    checkbox_width=18,
                    checkbox_height=18,
                    border_width=2
                )
                chk.pack(side="left", padx=10)
            
        elif selected_model.startswith("Bosques Aleatorios"):
            ctk.CTkLabel(master=self.params_subframe, text="Nº Estimadores:", font=(self.normal_font[0], 12)).pack(side="left", padx=5)
            ctk.CTkEntry(master=self.params_subframe, width=70, placeholder_text="100").pack(side="left", padx=5)
            ctk.CTkLabel(master=self.params_subframe, text="Max Profundidad:", font=(self.normal_font[0], 12)).pack(side="left", padx=(15, 5))
            ctk.CTkEntry(master=self.params_subframe, width=70, placeholder_text="None").pack(side="left", padx=5)
            
        elif selected_model.startswith("Máquinas de Vector"):
            ctk.CTkLabel(master=self.params_subframe, text="Kernel Ordinal:", font=(self.normal_font[0], 12)).pack(side="left", padx=5)
            ctk.CTkOptionMenu(master=self.params_subframe, values=["rbf", "linear", "poly", "sigmoid"], width=100).pack(side="left", padx=5)
            
        elif selected_model.startswith("K-Vecinos"):
            ctk.CTkLabel(master=self.params_subframe, text="Vecinos (K):", font=(self.normal_font[0], 12)).pack(side="left", padx=5)
            ctk.CTkEntry(master=self.params_subframe, width=70, placeholder_text="5").pack(side="left", padx=5)
            
        else:
            ctk.CTkLabel(master=self.params_subframe, text="Parámetros controlados automáticamente por regularización nativa.", font=(self.normal_font[0], 11, "italic")).pack(side="left", padx=5)

    def _render_empty_model_plot(self) -> None:
        fig = Figure(figsize=(6, 3.5), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_title("Gráficos de Rendimiento de Clasificación", fontsize=11, fontweight="bold")
        ax.text(0.5, 0.5, "Ejecute el modelo para ver la Matriz de Confusión\no curvas ROC correspondientes.", ha='center', va='center', fontsize=10, style='italic')
        canvas = FigureCanvasTkAgg(fig, master=self.model_plot_display)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        canvas.draw()


    def _on_execute_modeling_click(self) -> None:

        if not hasattr(self, 'loadedData') or self.loadedData is None or self.loadedData.empty:
            messagebox.showwarning("Aviso", "Por favor, cargue un conjunto de datos CSV antes de iniciar el entrenamiento.")
            return
            
        # Capturar X e Y directo de los estados cacheados por tus modales de la interfaz
        features = getattr(self, 'model_features', [])
        target = getattr(self, 'model_outputs', None)
        
        # Si guardas el target como lista en el modal, extraemos el primer elemento string
        if isinstance(target, list) and len(target) > 0:
            target = target[0]

        if not features or not target:
            messagebox.showwarning("Falta Configuración", "Debe configurar las variables de entrada (X) y salida (Y) en 'Seleccionar Variables'.")
            return

        selected_algo = self.model_selector.get()

        def worker():
            self.btn_run_model.configure(state="disabled")

            try:
                
                if selected_algo.startswith("Evaluación Automática"):
                    # 1. Capture user-selected metrics from checkboxes
                    active_checkboxes = [metric for metric, var in self.metric_checkbox_vars.items() if var.get()]
                    
                    self.log(message=f"Ejecutando AutoML con métricas: {', '.join(active_checkboxes)}...")
                    
                    # Ejecución de PyCaret (devuelve datos crudos)
                    best_model, metrics_df, plot_data_dict = run_pycaret_pipeline(
                        self.loadedData, features, target, active_checkboxes # type: ignore
                    )

                    self.log(message=f"Modelado finalizado. Extrayendo métricas filtradas...")
                    self.trained_model = best_model
                    time.sleep(0.5)
                    
                    # 2. Map your UI Checkbox names -> PyCaret's internal column names
                    # This guarantees the mapping logic finds the column even if shorthand is used
                    pycaret_metric_map = {
                        "Accuracy": "Accuracy",
                        "AUC": "AUC",
                        "Recall": "Recall",       # Often 'Recall' or 'Reccl.' depending on version
                        "Precision": "Prec.",     # PyCaret columns frequently use 'Prec.'
                        "F1-Score": "F1"          # PyCaret columns frequently use 'F1'
                    }
                    
                    # Find which internal PyCaret columns match the user's checked preferences
                    target_pycaret_cols = []
                    for cb in active_checkboxes:
                        mapped_name = pycaret_metric_map.get(cb, cb)
                        # Check if it exactly matches or is contained within PyCaret's headers
                        for actual_col in metrics_df.columns:
                            print(actual_col)
                            if actual_col == mapped_name or actual_col == cb:
                                target_pycaret_cols.append(actual_col)
                                break
                    
                    # 3. Build table columns dynamically using the validated PyCaret headers
                    cols = ["Algoritmo"] + target_pycaret_cols
                    
                    # Fallback safely if the intersection was completely empty
                    if len(cols) == 1:
                        cols = ["Algoritmo"] + [str(c) for c in metrics_df.columns if c != 'Model']

                    # 4. Extract row values mapping exactly to our dynamically filtered columns
                    rows = []
                    for index, row in metrics_df.iterrows():
                        row_vals = [row['Model']]  # First column is always the Model name
                        for c in cols[1:]:         # Match remaining active columns
                            val = row.get(c, 0.0)
                            row_vals.append(f"{val:.4f}" if isinstance(val, (float, int, np.number)) else str(val))
                        rows.append(row_vals)
                    
                    self.log(message=f"Generando gráficos individuales de evaluación ({type(best_model).__name__})...")

                    model_figures = self.generate_model_individual_plots(plot_data_dict)
                    time.sleep(0.5)

                    # 5. Push final updates to the main thread UI components
                    self.log(message="Actualizando paneles de visualización y métricas.")
                    self.toplvl.after(0, lambda: self.model_metrics_table.tree_config(cols, rows))
                    self.toplvl.after(0, lambda: self._initialize_model_plots_carousel(model_figures))
                    
                    self.log(message=f"Pipeline listo. Modelo sugerido: {type(best_model).__name__}")
                    messagebox.showinfo("Éxito", f"PyCaret completado.\nModelo sugerido: {type(best_model).__name__}")
                else:
                    # Configuración de modelos manuales
                    
                    params = {}
                    if "Bosques Aleatorios" in selected_algo:
                        for child in self.params_subframe.winfo_children():
                            if isinstance(child, ctk.CTkEntry):
                                if "Estimadores" in getattr(child, '_placeholder_text', ''): params["n_estimators"] = child.get()
                                elif "Profundidad" in getattr(child, '_placeholder_text', ''): params["max_depth"] = child.get()
                    elif "Máquinas de Vector" in selected_algo:
                        for child in self.params_subframe.winfo_children():
                            if isinstance(child, ctk.CTkOptionMenu): params["kernel"] = child.get()
                    elif "K-Vecinos" in selected_algo:
                        for child in self.params_subframe.winfo_children():
                            if isinstance(child, ctk.CTkEntry): params["n_neighbors"] = child.get()
                    
                    
                    self.log(message=f'Entrenando algoritmo seleccionado: {selected_algo}...')

                    metrics, importances, trained_model, X_test, y_test = run_custom_scikit_model(
                        self.loadedData, features, target, selected_algo, params # type: ignore
                    )
                    time.sleep(0.5)
                    self.log(message=f'Entrenamiento finalizado. Obteniendo modelo entrenado...')
                    self.trained_model = trained_model

                    
                    cols = ["Métrica de Rendimiento", "Conjunto de Validación (Test)"]
                    rows = [
                        ["Accuracy", f"{metrics.get('Accuracy', 0.0):.4f}"],
                        ["AUC (Área bajo la curva)", f"{metrics.get('AUC', 0.0):.4f}"],
                        ["Precision", f"{metrics.get('Precision', 0.0):.4f}"],
                        ["Recall (Sensibilidad)", f"{metrics.get('Recall', 0.0):.4f}"],
                        ["F1-Score", f"{metrics.get('F1-Score', 0.0):.4f}"]
                    ]
                    
                    # Adaptar Scikit-Learn al mismo diccionario estructurado de datos puros
                    from sklearn.metrics import roc_curve, precision_recall_curve
                    sk_data = {}
                    sk_data['confusion_matrix'] = (y_test.values, trained_model.predict(X_test)) # type: ignore
                    
                    if hasattr(trained_model, "predict_proba"):
                        probs = trained_model.predict_proba(X_test)[:, 1]
                        fpr, tpr, _ = roc_curve(y_test, probs)
                        sk_data['auc'] = (fpr, tpr)
                        precision, recall, _ = precision_recall_curve(y_test, probs)
                        sk_data['pr'] = (recall, precision)
                        
                    if hasattr(trained_model, "feature_importances_"):
                        sk_data['feature'] = (X_test.columns.tolist(), trained_model.feature_importances_) # type: ignore
                    
                    self.log(message=f'Generando gráficos de evaluación de modelo...')
                    time.sleep(0.5)

                    model_figures = self.generate_model_individual_plots(sk_data)
                    
                    self.toplvl.after(0, lambda: self.model_metrics_table.tree_config(cols, rows)) # type: ignore
                    self.toplvl.after(0, lambda: self._initialize_model_plots_carousel(model_figures))

                    messagebox.showinfo(title="Éxito", message=f"Entrenamiento de {selected_algo} completado con éxito.")
                    self.btn_run_model.configure(state='normal', text='Entrenar Modelo')
                    
            except Exception as e:
                self.toplvl.after(0, lambda: messagebox.showerror("Error de Modelado", str(e)))

            self.log(message=f'Entrenamiento de modelo finalizado con éxito...')


        
        threading.Thread(target=worker, daemon=True).start()
        self.btn_run_model.configure(state="normal")
        
        
    def show_chatbot_panel(self) -> None:
        """
        Dynamically initializes and switches the view context to the 
        split chatbot and notification panel using a matching Treeview style navigation.
        """
        import tkinter as tk
        from tkinter import ttk
        import os

        from chatbot_engine import GenericDataChatbot
        self.chat_engine = GenericDataChatbot()

        # Session tracking storage to hold messages for each child node thread
        # Schema: { iid: {"title": str, "messages": [ {"role": "Tú"/"Asistente", "text": str}, ... ]} }
        self.chat_sessions = {}
        self.current_active_thread_id = None

        self.chatbot_panel = ctk.CTkFrame(master=self.content_frame, fg_color="transparent")
        
        # --- SEGMENT 1: NARROW COLUMN (Conversations) ---
        self.sidebar_nav = ctk.CTkFrame(master=self.chatbot_panel, width=300, corner_radius=8)
        self.sidebar_nav.pack(side="left", fill="both", expand=False, padx=(0, 5))
        self.sidebar_nav.pack_propagate(False) # Secure narrow profile
        
        self.nav_title = ctk.CTkLabel(
            master=self.sidebar_nav, 
            text="Hilos de Consultas", 
            font=self.title_font if hasattr(self, 'title_font') else ("Arial", 14, "bold")
        )
        self.nav_title.pack(side="top", anchor="nw", padx=15, pady=12)
        
        # Grid Configuration for Treeview & Scrollbar placement
        self.tree_container = ctk.CTkFrame(master=self.sidebar_nav, fg_color="transparent")
        self.tree_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree_container.grid_rowconfigure(0, weight=1)
        self.tree_container.grid_columnconfigure(0, weight=1)

        # Apply styles matching your main navigation bar configuration
        style_chat_nav = ttk.Style()
        style_chat_nav.configure(
            "ChatNav.Treeview", 
            rowheight=32, 
            font=self.font_navbar if hasattr(self, 'font_navbar') else ("Arial", 11)
        )
        
        # Instantiate matching structural Treeview element
        self.chat_treeview = ttk.Treeview(
            master=self.tree_container,
            selectmode=tk.BROWSE,
            columns=('unread_flag',),
            style="ChatNav.Treeview"
        )
        self.chat_treeview.configure(show='tree')
        
        # Setup specific status indicator alert column tracking geometry rules
        self.chat_treeview.heading(column='#0', text="Historial", anchor="w")
        self.chat_treeview.column(column='#0', width=220, stretch=True)
        self.chat_treeview.column('unread_flag', width=35, anchor='center', stretch=False)

        # Bind custom scrolling track matching your UI system layout specs
        ysb = ctk.CTkScrollbar(
            master=self.tree_container,
            width=12,
            orientation='vertical',
            cursor='hand2',
            button_color='#3b8cc6',
            button_hover_color='SteelBlue',
            command=self.chat_treeview.yview
        )
        self.chat_treeview.configure(yscrollcommand=ysb.set)

        # Place the UI objects cleanly inside the grid layer mapping frame
        self.chat_treeview.grid(row=0, column=0, sticky='nsew')
        ysb.grid(row=0, column=1, sticky='ns', padx=(2, 0))
        
        # Parent Group: Chat Log Threads
        self.history_parent = self.chat_treeview.insert('', 'end', text="Historial de Consultas", values=("",))
        self.chat_treeview.item(self.history_parent, open=True)

        # Bind selection callbacks to render your chat console dynamically on item click
        self.chat_treeview.bind("<<TreeviewSelect>>", self._on_chat_tree_select)

        # --- SEGMENT 2: WIDER COLUMN (Active Chat Engine) ---
        # Note: We keep this packed immediately now since new chats automatically instantiate a node thread wrapper
        self.chat_console = ctk.CTkFrame(master=self.chatbot_panel, corner_radius=8)
        self.chat_console.pack(side="right", fill="both", expand=True)
        
        self.chat_history = ctk.CTkTextbox(
            master=self.chat_console, 
            font=("Consolas", 12) if os.name == 'nt' else ("Courier", 12),
            border_width=1,
            border_color="#b0b0b0",
            activate_scrollbars=True
        )
        self.chat_history.pack(side="top", fill="both", expand=True, padx=12, pady=(12, 6))
        self.chat_history.configure(state="disabled")

        
        # Message Input Prompter Row Box
        self.prompt_frame = ctk.CTkFrame(master=self.chat_console, fg_color="transparent")
        self.prompt_frame.pack(side="top", fill="x", padx=12, pady=(6, 12))
        
        self.chat_entry = ctk.CTkTextbox(
            master=self.prompt_frame, 
            width=200, 
            font=("Consolas", 12) if os.name == 'nt' else ("Courier", 12),
            border_width=1,
            activate_scrollbars=True
        )
        self.chat_entry.insert("0.0", 'Escribe un mensaje al Asistente...')
        self.chat_entry.pack(side="top", fill="both", expand=True, pady=(12, 6))
        
        self.chat_entry.bind("<Return>", lambda event: self._send_chat_message(event))
        
        self.btn_actions_frame = ctk.CTkFrame(master=self.prompt_frame, fg_color="transparent")
        self.btn_actions_frame.pack(side="top", fill="x")

        self.send_btn = ctk.CTkButton(
            master=self.btn_actions_frame, 
            text="Enviar", 
            width=70,
            command=lambda: self._send_chat_message()
        )
        self.send_btn.pack(side="right", padx=(5, 0))

        # NEW: Clear / New Chat Button
        self.clear_btn = ctk.CTkButton(
            master=self.btn_actions_frame, 
            text="Nuevo Chat", 
            width=90,
            fg_color="#A0A0A0",      # Neutral gray tone to visually differentiate from Enviar
            hover_color="#808080",
            text_color="black",
            command=self._clear_current_chat_session
        )
        self.clear_btn.pack(side="right")

        
        
        self.chatbot_panel.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        if hasattr(self, 'toplvl'):
            self.toplvl.update_idletasks()




    def _clear_current_chat_session(self) -> None:
        """Clears the active viewport screens and breaks the current thread tracking reference link."""
        # 1. Wipe text view consoles completely clean
        self.chat_history.configure(state="normal")
        self.chat_history.delete("0.0", "end")
        self.chat_history.configure(state="disabled")
        
        # 2. Reset input panel box text state
        self.chat_entry.delete("0.0", "end")
        self.chat_entry.insert("0.0", 'Escribe un mensaje al Asistente...')
        
        # 3. Disconnect current pointer reference index mapping
        self.current_active_thread_id = None
        
        # 4. Clear visual Treeview highlight selection bars safely
        existing_selections = self.chat_treeview.selection()
        if existing_selections:
            self.chat_treeview.selection_remove(existing_selections)
            
        # Optional: Bring typing focus straight back to input target text field area
        self.chat_entry.focus_set()




    def _activate_chat_session(self, initial_context: str) -> None:
        """Packs the hidden chat interface element onto screen when clicked."""
        # Check if console is already visible to avoid unnecessary repacking cycles
        if not self.chat_console.winfo_manager():
            self.chat_console.pack(side="right", fill="both", expand=True)
            
        # Unlock history window temporarily to greet the session context change
        self.chat_history.configure(state="normal")
        self.chat_history.delete("0.0", "end") # Clear out older context
        self.chat_history.insert("end", f"--- Iniciada sesión de chat: {initial_context} ---\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")
        
        self.log(message=f"Chat session opened context: {initial_context}")

    def _send_chat_message(self, event=None) -> str:
        """Extracts text, dynamically provisions a Treeview node thread if needed, and streams indicators."""

        raw_text = self.chat_entry.get("0.0", "end").strip()
        
        if not raw_text or raw_text == 'Escribe un mensaje al Asistente...':
            return "break"
            
        # 1. Update text logs immediately for visibility
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"\nTú: {raw_text}\n")
        
        # 2. Dataset availability safe-guard
        try:
            assert hasattr(self, 'loadedData')
        except AssertionError as e:
            self.chat_history.insert("end", f"\nAsistente: No hay datos cargados en el sistema actualmente...\n")
            self.chat_history.configure(state="disabled")
            self.chat_entry.delete("0.0", "end")
            self.chat_history.see("end")
            return 'break'
        else:
            self.chat_history.insert("end", f"\nAsistente: Buscando información en los datos cargados...\n")
            self.chat_history.configure(state="disabled")
    
            # 3. Dynamic Provisioning: Create a thread node if none is active or selected
            str_length = 20
            if self.current_active_thread_id is None:
                # Create truncated version of the prompt string (e.g., first 28 chars...)
                truncated_title = raw_text[:str_length] + "..." if len(raw_text) > str_length else raw_text
                
                # Insert child node leaf directly under our history parent header
                new_iid = self.chat_treeview.insert(self.history_parent, 'end', text=truncated_title.capitalize(), values=("",))
                
                # Allocate session mapping space
                self.chat_sessions[new_iid] = {"title": truncated_title.capitalize(), "messages": []}
                self.current_active_thread_id = new_iid
                
                # Visually highlight and focus selection onto this newly deployed branch node
                self.chat_treeview.selection_set(new_iid)
                self.chat_treeview.focus(new_iid)

            # Save historical user record log to memory context array list
            self.chat_sessions[self.current_active_thread_id]["messages"].append({"role": "Tú", "text": raw_text})
            
            # 4. Clear input field block tracking metrics down
            self.chat_entry.delete("0.0", "end")
            self.chat_history.see("end")
            
            # 5. Dispatch async background calculation loop execution call
            threading.Thread(
                target=self._async_chatbot_worker, 
                args=(raw_text, self.current_active_thread_id), 
                daemon=True
            ).start()

            return "break"



    def _async_chatbot_worker(self, prompt: str, target_thread_id: str) -> None:
        """Background background execution task loop tracking specific thread context."""
        bot_reply = self.chat_engine.execute_and_reply(prompt, self.loadedData)
        # Pass the calculated response text alongside the destination context node identifier
        self.toplvl.after(0, lambda: self._update_chat_ui_with_reply(bot_reply, target_thread_id))


    def _update_chat_ui_with_reply(self, reply: str, target_thread_id: str) -> None:
        """Appends reply data securely to history log cache coordinates."""
        # Commit computed record to the appropriate mapping list inside our dictionary data structure
        if target_thread_id in self.chat_sessions:
            self.chat_sessions[target_thread_id]["messages"].append({"role": "Asistente", "text": reply})
        
        # Only draw onto viewport screen if the user hasn't switched away from this active thread row click target
        if self.current_active_thread_id == target_thread_id:
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", f"\nAsistente:\n{reply}\n")
            self.chat_history.configure(state="disabled")
            self.chat_history.see("end")

    def _on_chat_tree_select(self, event) -> None:
        """Listens to selections, changing context mapping views and loading text histories on click."""
        selected_items = self.chat_treeview.selection()
        if not selected_items:
            return

        selected_iid = selected_items[0]
        
        # Guard: Check if the user selected the structural parent header block itself
        if selected_iid == self.history_parent:
            self.current_active_thread_id = None # Set baseline unlinked entry target focus pointer
            return

        # Update focus variable pointer coordinate state
        self.current_active_thread_id = selected_iid
        
        # Clear console log field container completely and pull cached logs back into scope
        self.chat_history.configure(state="normal")
        self.chat_history.delete("0.0", "end")
        
        if selected_iid in self.chat_sessions:
            # Reconstruct screen dialogue view block iteratively
            for msg in self.chat_sessions[selected_iid]["messages"]:
                if msg["role"] == "Tú":
                    self.chat_history.insert("end", f"\nTú: {msg['text']}\n")
                else:
                    self.chat_history.insert("end", f"\nAsistente:\n{msg['text']}\n")
                    
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")



    def generate_model_individual_plots(self, plot_data: dict) -> list:
        """
        Recibe un diccionario de datos puros y genera páginas independientes de gráficos
        en alta resolución adaptadas al carrusel visual de la UI.
        """
        figures_list = []
        if not plot_data:
            return figures_list

        # --- Página 1: Matriz de Confusión ---
        if 'confusion_matrix' in plot_data:
            from sklearn.metrics import confusion_matrix
            y_real, y_pred = plot_data['confusion_matrix']
            fig = Figure(figsize=(7.2, 4.6), dpi=100)
            ax = fig.add_subplot(111)
            cm = confusion_matrix(y_real, y_pred)
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax, cbar=False)
            ax.set_title("Matriz de Confusión - Evaluación del Modelo", fontsize=12, fontweight="bold")
            ax.set_xlabel("Clase Predicha")
            ax.set_ylabel("Clase Real")
            fig.tight_layout()
            figures_list.append(fig)

        # --- Página 2: Curva ROC (AUC) ---
        if 'auc' in plot_data:
            fpr, tpr = plot_data['auc']
            fig = Figure(figsize=(7.2, 4.6), dpi=100)
            ax = fig.add_subplot(111)
            ax.plot(fpr, tpr, color=blue_widget, lw=2, label="Curva ROC")
            ax.plot([0, 1], [0, 1], color="gray", linestyle="--")
            ax.set_title("Curva Característica Operativa del Receptor (ROC)", fontsize=12, fontweight="bold")
            ax.set_xlabel("Tasa de Falsos Positivos (FPR)")
            ax.set_ylabel("Tasa de Verdaderos Positivos (TPR)")
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            figures_list.append(fig)

        # --- Página 3: Curva Precision-Recall ---
        if 'pr' in plot_data:
            recall, precision = plot_data['pr']
            fig = Figure(figsize=(7.2, 4.6), dpi=100)
            ax = fig.add_subplot(111)
            ax.plot(recall, precision, color="darkorange", lw=2, label="Precision-Recall")
            ax.set_title("Curva Precision-Recall", fontsize=12, fontweight="bold")
            ax.set_xlabel("Recall (Sensibilidad)")
            ax.set_ylabel("Precision")
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            figures_list.append(fig)

        # --- Página 4: Importancia de Variables ---
        if 'feature' in plot_data:
            colnames, importances = plot_data['feature']
            fig = Figure(figsize=(7.2, 4.6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Ordenar las top 10 para visualización limpia
            indices = np.argsort(importances)[-10:]
            sorted_names = [colnames[i] for i in indices]
            sorted_importances = [importances[i] for i in indices]
            
            ax.barh(range(len(indices)), sorted_importances, color="#20c997", align="center")
            ax.set_yticks(range(len(indices)))
            ax.set_yticklabels(sorted_names, fontsize=9)
            ax.set_title("Top Características con Mayor Peso Predictivo", fontsize=12, fontweight="bold")
            ax.set_xlabel("Importancia Relativa")
            fig.tight_layout()
            figures_list.append(fig)

        return figures_list





    def _show_panel(self, panel):
        print("showing chatbot panel")
        panel.pack(side='left', fill='both', anchor='nw', expand=True, pady=pady, padx =0)
        
    def switch_to_patient_data_panel(self, event=None):
        self.switch_panel('Datos de Pacientes')

    def switch_to_exploration_panel(self, event=None):
        self.switch_panel('exploration')

    def switch_to_db_config_pannel(self, event=None):
        self.switch_panel('db')

    def show_exploration_panel(self) -> None:
        self.exploration_panel_frame.configure(width=self.tree_table_width, corner_radius=0, height=self.tree_table_height)
        self.exploration_panel_frame.pack_configure(side='top', anchor='nw', padx=0, pady =0.2, fill='both', expand=True)
        
        self.exploration_panel_frame.pack_propagate(False)
        self.exploration_panel_frame.grid_propagate(False)

        self.desc_tabview = ctk.CTkTabview(master=self.exploration_panel_frame, width=self.tree_table_width, height=self.tree_table_height)
        self.desc_tabview.pack(side='top', anchor='nw', fill='both', expand=True, padx=0, pady=0)
        
        self.tab_tables = self.desc_tabview.add("Tablas")
        self.tab_plots = self.desc_tabview.add("Gráficos")
        
        for tab in [self.tab_tables, self.tab_plots]:
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

        self.setup_exploration_table_tab()
        self.setup_plots_tab()



    def setup_exploration_table_tab(self) -> None:
        """Sets up the table analysis view structure with an explicit execution button."""
        self.table_tab_container = ctk.CTkFrame(master=self.tab_tables, fg_color='transparent')
        self.table_tab_container.pack(fill='both', padx=padx, pady=pady, anchor='nw', expand=True)
        table_options_frame = ctk.CTkFrame(master=self.table_tab_container)
        table_options_frame.pack(side='top', padx=padx, pady=(0, 10), anchor='w', fill='x')

        options_title = ctk.CTkLabel(
            master=table_options_frame, 
            text="Seleccionar métricas de resumen estadístico:", 
            font=(self.title_font[0], 13, "bold")
        )
        options_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(8, 12))

        run_btn = ctk.CTkButton(
            master=table_options_frame,
            text="Calcular Descriptivos",
            font=(self.normal_font[0], 12, "bold"),
            fg_color="#3b8cc6",
            width=140,
            height=28,
            command=self.on_run_describe_click
        )
        run_btn.grid(row=0, column=4, columnspan=2, sticky="e", padx=15, pady=(8, 12)) 

        self.table_metric_switches = {}
        columns_to_show = list(metric_translations.values())
        max_rows = 3

        for index, col_name in enumerate(columns_to_show):
            grid_row = (index % max_rows) + 1
            grid_col_base = (index // max_rows) * 2

            lbl = ctk.CTkLabel(master=table_options_frame, text=f"{col_name}:", font=(self.normal_font[0], 12), anchor="w")
            lbl.grid(row=grid_row, column=grid_col_base, sticky="w", padx=(20, 5), pady=4)

            is_checked = col_name not in ['Valores Únicos', 'Valor Más Frecuente', 'Frecuencia de Top']
            self.table_metric_switches[col_name] = ctk.BooleanVar(value=is_checked)

            chk = ctk.CTkCheckBox(
                master=table_options_frame,
                text="",
                variable=self.table_metric_switches[col_name],
                width=24,
                height=24
            )
            chk.grid(row=grid_row, column=grid_col_base + 1, sticky="w", padx=(0, 20), pady=4)

        placeholder_cols = ['Métrica'] + [f"Columna {i}" for i in range(7)] + ["Columna..."]

        self.tables_display_container = ctk.CTkFrame(master=self.table_tab_container, fg_color='transparent')
        self.tables_display_container.pack(side='top', fill='both', expand=True, padx=padx, pady=padx)
        
        # Table carousel control variables
        self.carousel_tables = []       # Will hold list of dicts: {"title": str, "cols": list, "rows": list}
        self.current_table_index = 0
        
        # Initial empty descriptive table packed inside the new container
        self.desc_table = CustomTable(
            master=self.tables_display_container,
            columns=placeholder_cols,
            row_height=row_height,
            font_data=(self.normal_font[0], 13),
            font_header=(self.normal_font[0], 14, "bold")
        )
        self.desc_table.pack(side='top', fill='both', expand=True)
    
    def display_table_carousel_slice(self) -> None:
        """Clears the table container and renders the active table step with page buttons using a static grid layout."""
        if not self.carousel_tables:
            return
            
        # 1. Clear previous widgets inside the container safely
        for widget in self.tables_display_container.winfo_children():
            widget.destroy()
            
        # Configure weight metrics to make row 1 (the table) scalable, and row 0 & 2 static
        self.tables_display_container.grid_rowconfigure(0, weight=0)
        self.tables_display_container.grid_rowconfigure(1, weight=1)
        self.tables_display_container.grid_rowconfigure(2, weight=0)
        self.tables_display_container.grid_columnconfigure(0, weight=1)

        target_table_data = self.carousel_tables[self.current_table_index]
        
        # 2. Render table description title label (Row 0)
        title_lbl = ctk.CTkLabel(
            master=self.tables_display_container, 
            text=target_table_data["title"], 
            font=(self.title_font[0], 13, "bold") if hasattr(self, 'title_font') else ("Arial", 13, "bold"),
            text_color="#3b8cc6"
        )
        title_lbl.grid(row=0, column=0, sticky="nw", pady=(0, 5))
        
        # 3. Instantiate the CustomTable structure (Row 1 - Scalable window viewport)
        current_table_widget = CustomTable(
            master=self.tables_display_container,
            columns=target_table_data["cols"],
            row_height=22, 
            font_data=(self.normal_font[0], 13) if hasattr(self, 'normal_font') else ("Arial", 13),
            font_header=(self.normal_font[0], 14, "bold") if hasattr(self, 'normal_font') else ("Arial", 14, "bold")
        )
        current_table_widget.grid(row=1, column=0, sticky="nsew")
        current_table_widget.tree_config(target_table_data["cols"], target_table_data["rows"])
        
        # 4. Build lower Navigation Bar (Row 2 - Rigidly anchored at base frame coordinates)
        navigation_bar = ctk.CTkFrame(master=self.tables_display_container, height=45, fg_color="transparent")
        navigation_bar.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        navigation_bar.pack_propagate(False) # Prevent the frame from collapsing vertically

        # 5. Pack subcomponents using side layouts to guarantee spacing alignment
        prev_btn = ctk.CTkButton(
            master=navigation_bar,
            text="<< Previous",
            width=100,
            command=self.slide_table_carousel_left,
            state="normal" if self.current_table_index > 0 else "disabled"
        )
        prev_btn.pack(side="left", padx=20, pady=5)
        
        next_btn = ctk.CTkButton(
            master=navigation_bar,
            text="Next >>",
            width=100,
            command=self.slide_table_carousel_right,
            state="normal" if self.current_table_index < len(self.carousel_tables) - 1 else "disabled"
        )
        next_btn.pack(side="right", padx=20, pady=5)

        counter_lbl = ctk.CTkLabel(
            master=navigation_bar,
            text=f"Table {self.current_table_index + 1} of {len(self.carousel_tables)}",
            font=(self.normal_font[0], 11, "bold") if hasattr(self, 'normal_font') else ("Arial", 11, "bold")
        )
        counter_lbl.pack(side="bottom", expand=True, pady=5)


    def slide_table_carousel_left(self) -> None:
        if self.current_table_index > 0:
            self.current_table_index -= 1
            self.display_table_carousel_slice()

    def slide_table_carousel_right(self) -> None:
        if self.current_table_index < len(self.carousel_tables) - 1:
            self.current_table_index += 1
            self.display_table_carousel_slice()



    def setup_plots_tab(self) -> None:
        """Sets up the plots analysis layout view with controls on top and a horizontal plot carousel below."""
        self.plots_tab_container = ctk.CTkFrame(master=self.tab_plots, fg_color='transparent')
        self.plots_tab_container.pack(fill='both', padx=padx, pady=pady-4, anchor='nw', expand=True)

        self.plots_options_frame = ctk.CTkFrame(master=self.plots_tab_container)
        self.plots_options_frame.pack(side='top', padx=padx, pady=(0, 0), anchor='w', fill='x')

        options_title = ctk.CTkLabel(
            master=self.plots_options_frame, 
            text="Seleccionar análisis gráficos:", 
            font=(self.title_font[0], 13, "bold")
        )
        options_title.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(8, 12))

        run_plots_btn = ctk.CTkButton(
            master=self.plots_options_frame,
            text="Generar gráficos",
            font=(self.normal_font[0], 12, "bold"),
            fg_color="#3b8cc6",
            width=140,
            height=28,
            command=self.on_run_plots_click
        )
        run_plots_btn.grid(row=0, column=4, sticky="e", padx=15, pady=(8, 12))

        self.plot_switches = {
            'Heatmap': ctk.BooleanVar(value=True),
            'PCA': ctk.BooleanVar(value=False),
        }

        for index, (plot_name, var_state) in enumerate(self.plot_switches.items()):
            lbl = ctk.CTkLabel(master=self.plots_options_frame, text=f"{plot_name}:", font=(self.normal_font[0], 12))
            lbl.grid(row=1, column=index*2, sticky="w", padx=(20, 5), pady=4)

            chk = ctk.CTkCheckBox(master=self.plots_options_frame, text="", variable=var_state, width=24, height=24)
            chk.grid(row=1, column=index*2 + 1, sticky="w", padx=(0, 20), pady=4)

        self.heatmap_threshold_frame = ctk.CTkFrame(master=self.plots_options_frame, fg_color="transparent")
        self.heatmap_threshold_frame.grid(row=2, column=0, columnspan=6, sticky="w", padx=20, pady=(8, 5))

        ctk.CTkLabel(master=self.heatmap_threshold_frame, text="Umbral Correlación Heatmap:", font=(self.normal_font[0], 12)).pack(side='left', padx=(0, 5))
        
        self.corr_threshold_var = ctk.DoubleVar(value=0.5)
        self.threshold_entry = ctk.CTkEntry(
            master=self.heatmap_threshold_frame, 
            width=80, 
            textvariable=self.corr_threshold_var
        )
        self.threshold_entry.pack(side='left', padx=5)
        
        ctk.CTkLabel(master=self.heatmap_threshold_frame, text="(0.0 - 1.0)", font=(self.normal_font[0], 11)).pack(side='left', padx=5)

        self.add_more_plots_var = ctk.BooleanVar(value=False)
        add_more_chk = ctk.CTkCheckBox(
            master=self.plots_options_frame,
            text="Añadir más gráficos",
            font=(self.normal_font[0], 12, "bold"),
            variable=self.add_more_plots_var,
            command=self.toggle_custom_plot_options
        )
        add_more_chk.grid(row=3, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 8))

        self.custom_plot_controls_subframe = ctk.CTkFrame(master=self.plots_options_frame, fg_color="transparent")
        available_cols = list(self.loadedData.columns) if hasattr(self, 'loadedData') and self.loadedData is not None else ["Ninguna variable"]

        self.custom_plot_type = ctk.CTkOptionMenu(
            master=self.custom_plot_controls_subframe, 
            values=["Dispersión (Scatter)", "Líneas (Line Plot)", "Barras (Bar Plot)", "Boxplot"]
        )
        self.custom_plot_type.set("Tipo de gráfico")

        self.input_var_menu = ctk.CTkOptionMenu(master=self.custom_plot_controls_subframe, values=available_cols)
        self.input_var_menu.set("Variable Entrada (X)")

        self.output_var_menu = ctk.CTkOptionMenu(master=self.custom_plot_controls_subframe, values=available_cols)
        self.output_var_menu.set("Variable Salida (Y)")

        ctk.CTkLabel(master=self.custom_plot_controls_subframe, text="Gráfico:", font=(self.normal_font[0], 11)).grid(row=0, column=0, padx=5, sticky="w")
        self.custom_plot_type.grid(row=0, column=1, padx=5)
        ctk.CTkLabel(master=self.custom_plot_controls_subframe, text="X:", font=(self.normal_font[0], 11)).grid(row=0, column=2, padx=5, sticky="w")
        self.input_var_menu.grid(row=0, column=3, padx=5)
        ctk.CTkLabel(master=self.custom_plot_controls_subframe, text="Y:", font=(self.normal_font[0], 11)).grid(row=0, column=4, padx=5, sticky="w")
        self.output_var_menu.grid(row=0, column=5, padx=5)

        self.plots_display_container = ctk.CTkFrame(master=self.plots_tab_container, fg_color='transparent')
        self.plots_display_container.pack(side='top', fill='both', expand=True, padx=padx, pady=padx)
        
        self.carousel_figures = []
        self.current_carousel_index = 0

        self.render_default_empty_figure()

    def render_default_empty_figure(self) -> None:
        """Renders a standalone default blank figure container before data calculation triggers."""
        for widget in self.plots_display_container.winfo_children():
            widget.destroy()

        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_title("Vista Previa de Análisis Gráfico", fontsize=12, fontweight="bold")
        ax.text(0.5, 0.5, "Cargue un archivo CSV y haga clic en\n'Generar Gráficos' para activar el carrusel.", 
                ha='center', va='center', fontsize=10, style='italic')
        ax.set_xlabel("Eje X (Muestra)")
        ax.set_ylabel("Eje Y (Muestra)")
        fig.tight_layout(h_pad=fig_ipad)

        canvas = FigureCanvasTkAgg(fig, master=self.plots_display_container)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side="top", fill="both", expand=True)
        canvas.draw()

    def toggle_custom_plot_options(self) -> None:
        if self.add_more_plots_var.get():
            if hasattr(self, 'loadedData') and self.loadedData is not None and not self.loadedData.empty:
                current_cols = list(self.loadedData.columns)
                self.input_var_menu.configure(values=current_cols)
                self.output_var_menu.configure(values=current_cols)
            self.custom_plot_controls_subframe.grid(row=4, column=0, columnspan=6, sticky="w", padx=20, pady=(0, 10))
        else:
            self.custom_plot_controls_subframe.grid_forget()

    def on_run_plots_click(self) -> None:
        is_pca_calculated = False

        if not hasattr(self, 'loadedData') or self.loadedData is None or self.loadedData.empty:
            messagebox.showwarning(
                "Aviso", 
                "No hay datos cargados para modelar gráficos. Por favor, cargue un archivo CSV desde 'Datos de Pacientes'."
            )
            return
        if (self.model_features == None) or (self.model_outputs == None):
            messagebox.showwarning(
                "Aviso", 
                "Variables de entrada(X) y salida(Y) no definidas.\nPulsar Ctrl+Shift+O para definir variables"
            )
            return 

        active_plots = {}
        if self.plot_switches['Heatmap'].get(): 
            active_plots['Heatmap'] = []
        if self.plot_switches['PCA'].get(): 
            active_plots['PCA'] = []
        
        if self.add_more_plots_var.get():
            g_type = self.custom_plot_type.get()
            var_x = self.input_var_menu.get()
            var_y = self.output_var_menu.get()
            
            if g_type != "Tipo de gráfico" and var_x != "Variable Entrada (X)" and var_y != "Variable Salida (Y)":
                active_plots["Custom"] = [g_type, var_x, var_y]

        if not active_plots:
            messagebox.showwarning("Aviso", "Por favor, seleccione al menos una opción de gráfico.")
            return

        self.carousel_figures = []
        
        self.log(message='Trabajando en la generación de gráficos...')
        for plot_name in active_plots.keys():
            if plot_name == "Heatmap":
                self._generate_heatmap_figure()
            elif plot_name == "PCA":
                self._generate_pca_figure()
                self._generate_pca_table()
                self._show_pca_table()
                is_pca_calculated = True
            elif plot_name == "Custom":
                self._generate_custom_plot_figure(list(active_plots['Custom']))
            else:
                fig = Figure(figsize=(7, 3.5), dpi=100)
                ax = fig.add_subplot(111)
                ax.set_title(plot_name, fontsize=11, fontweight="bold")
                ax.text(0.5, 0.5, f"[{plot_name} - Pendiente de implementación]", 
                        ha='center', va='center', fontsize=11, style='italic')
                fig.tight_layout(h_pad=fig_ipad)
                self.carousel_figures.append(fig)

        self.current_carousel_index = 0
        if is_pca_calculated:
            messagebox.showinfo(title="PCA table generated", message="Nueva tabla de PCA generada en el tab de tablas.")
        self.display_carousel_slice()
        self.log(message='Se han generado los gráficos seleccionados con éxito...')

    def _generate_heatmap_figure(self):
        try:
            df = self.loadedData[self.model_features].select_dtypes(include=[np.number])
        except Exception as e:
            df = self.loadedData.select_dtypes(include=[np.number])

        if df.empty:
            fig = Figure(figsize=(7, 6), dpi=100)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No hay columnas numéricas para heatmap", ha='center', va='center')
            self.carousel_figures.append(fig)
            return

        corr_matrix = df.corr()
        threshold = self.corr_threshold_var.get()
        mask = np.abs(corr_matrix) >= threshold
        filtered_corr = corr_matrix.where(mask)

        fig = Figure(figsize=(8, 5.5), dpi=100)
        ax = fig.add_subplot(111)
        
        sns.heatmap(
            filtered_corr, 
            annot=True, 
            cmap='coolwarm', 
            center=0, 
            ax=ax,
            vmin=-1, 
            vmax=1,
            fmt='.2f'
        )
        ax.set_title(f"Heatmap de Correlación (umbral ≥ {threshold})", fontsize=12, fontweight="bold")
        fig.tight_layout(h_pad=fig_ipad)
        self.carousel_figures.append(fig)

    def _generate_pca_figure(self):
        try:
            df = self.loadedData[self.model_features].select_dtypes(include=[np.number])
        except Exception as e:
            df = self.loadedData.select_dtypes(include=[np.number])

        pca_result, pca_model, feature_names = perform_pca(df)

        fig = Figure(figsize=(7, 5), dpi=100)
        ax = fig.add_subplot(111)

        if pca_result is None:
            ax.text(0.5, 0.5, "No hay suficientes columnas numéricas\npara realizar PCA", 
                    ha='center', va='center', fontsize=12)
        else:
            ax.scatter(pca_result[:, 0], pca_result[:, 1], alpha=0.75, edgecolors='w', s=70)
            explained = pca_model.explained_variance_ratio_ # type: ignore
            ax.set_title(f'PCA - Varianza Explicada\n'
                        f'PC1: {explained[0]:.1%} | PC2: {explained[1]:.1%}', 
                        fontsize=12, fontweight='bold')
            ax.set_xlabel('Componente Principal 1')
            ax.set_ylabel('Componente Principal 2')
            ax.grid(True, alpha=0.3)

        fig.tight_layout()
        self.carousel_figures.append(fig)
        self._generate_pca_table()

        if hasattr(self, 'pca_table_data') and self.pca_table_data is not None:
            formatted_pca_rows = []
        
            for row in self.pca_table_data:
                string_row = []
                for val in row:
                    if isinstance(val, (float, np.floating)):
                        string_row.append(f"{val:.4f}")
                    else:
                        string_row.append(str(val))
                formatted_pca_rows.append(string_row)
                
            pca_table_payload = {
                "title": "Matriz de cargas factoriales (PCA)",
                "cols": self.pca_feature_names,
                "rows": formatted_pca_rows
            }
            
            # Remove any previous execution duplicates of PCA table
            self.carousel_tables = [t for t in self.carousel_tables if t["title"] != pca_table_payload["title"]]
            self.carousel_tables.append(pca_table_payload)
            
            # Auto-advance the index view straight to your newly appended PCA Table results
            self.current_table_index = len(self.carousel_tables) - 1
            self.toplvl.after(0, self.display_table_carousel_slice)



    def _generate_pca_table(self):
        try:
            df = self.loadedData[self.model_features].select_dtypes(include=[np.number]) if self.model_features else \
                 self.loadedData.select_dtypes(include=[np.number])
        except:
            df = self.loadedData.select_dtypes(include=[np.number])

        pca_result, pca_model, feature_names = perform_pca(df, npca=4)
        if pca_result is None or pca_model is None:
            self.pca_table_data = None
            return

        explained_var = pca_model.explained_variance_ratio_
        loadings = pca_model.components_.T

        table_data = []
        for i, feature in enumerate(feature_names): # type: ignore
            row = [feature, loadings[i, 0], loadings[i, 1]]
            table_data.append(row)

        table_data.append(["--- Explained Variance ---", explained_var[0], explained_var[1]])
        table_data.append(["Cumulative", explained_var[0] + explained_var[1], ""])

        self.pca_table_data = table_data
        self.pca_feature_names = ["Variable", "PC1", "PC2"]

    def _show_pca_table(self):
        if not hasattr(self, 'pca_table_data') or self.pca_table_data is None:
            return

        if hasattr(self, 'pca_result_table') and self.pca_result_table:
            self.pca_result_table.pack_forget()
            self.pca_result_table.destroy()

        self.pca_result_table = CustomTable(
            master=self.table_tab_container,
            columns=self.pca_feature_names,
            row_height=row_height,
            default_cwidth=180,
            font_data=(self.normal_font[0], 13),
            font_header=(self.normal_font[0], 14, "bold")
        )
        self.pca_result_table.pack(side='top', fill='both', expand=True, padx=padx, pady=(10, 0))


    def _generate_custom_plot_figure(self, plot_info: list):
        try:
            plot_type, x_var, y_var = plot_info
            plot_title = f'{plot_type} - {x_var} vs {y_var}'

            fig = Figure(figsize=(7, 4), dpi=100)
            ax = fig.add_subplot(111)

            if plot_type.startswith("Dispersión"):
                self.loadedData.plot(kind='scatter', x=x_var, y=y_var, ax=ax, alpha=0.7)
            elif plot_type.startswith("Líneas"):
                self.loadedData.plot(kind='line', x=x_var, y=y_var, ax=ax)
            elif plot_type.startswith("Barras"):
                self.loadedData.plot(kind='bar', x=x_var, y=y_var, ax=ax)
            elif plot_type.startswith("Boxplot"):
                self.loadedData.boxplot(column=y_var, by=x_var, ax=ax)
                ax.set_title(plot_title)
            else:
                ax.text(0.5, 0.5, f"Tipo de gráfico no soportado: {plot_type}", ha='center', va='center')

            ax.set_title(plot_title, fontsize=11, fontweight="bold")
            fig.tight_layout(h_pad=fig_ipad)
            self.carousel_figures.append(fig)
        except Exception as e:
            fig = Figure(figsize=(7, 4), dpi=100)
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Error generando gráfico:\n{str(e)}", ha='center', va='center', color='red')
            fig.tight_layout(h_pad=fig_ipad)
            self.carousel_figures.append(fig)

    def display_carousel_slice(self) -> None:
        for widget in self.plots_display_container.winfo_children():
            widget.destroy()

        if not self.carousel_figures:
            self.render_default_empty_figure()
            return

        canvas_frame = ctk.CTkFrame(master=self.plots_display_container, fg_color="transparent")
        canvas_frame.pack(side="top", fill="both", expand=True)

        target_fig = self.carousel_figures[self.current_carousel_index]
        canvas = FigureCanvasTkAgg(target_fig, master=canvas_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side="top", fill="both", expand=True)
        canvas.draw()

        navigation_bar = ctk.CTkFrame(master=self.plots_display_container, height=40, fg_color="transparent")
        navigation_bar.pack(side="bottom", fill="x", pady=(5, 0))

        prev_btn = ctk.CTkButton(
            master=navigation_bar, 
            text="<< Anterior", 
            width=100,
            command=self.slide_carousel_left,
            state="normal" if self.current_carousel_index > 0 else "disabled"
        )
        prev_btn.pack(side="left", padx=50)

        counter_lbl = ctk.CTkLabel(
            master=navigation_bar, 
            text=f"Gráfico {self.current_carousel_index + 1} de {len(self.carousel_figures)}",
            font=(self.normal_font[0], 11, "bold")
        )
        counter_lbl.pack(side="left", expand=True)

        next_btn = ctk.CTkButton(
            master=navigation_bar, 
            text="Siguiente >>", 
            width=100,
            command=self.slide_carousel_right,
            state="normal" if self.current_carousel_index < len(self.carousel_figures) - 1 else "disabled"
        )
        next_btn.pack(side="right", padx=50)

    def slide_carousel_left(self) -> None:
        if self.current_carousel_index > 0:
            self.current_carousel_index -= 1
            self.display_carousel_slice()

    def slide_carousel_right(self) -> None:
        if self.current_carousel_index < len(self.carousel_figures) - 1:
            self.current_carousel_index += 1
            self.display_carousel_slice()
    

    def _initialize_model_plots_carousel(self, figures_list: list) -> None:
        """Inicializa el carrusel paginado de gráficos en la UI de forma segura sin autodestruir componentes."""
        # Limpiar TODO el panel únicamente la primera vez para estructurar el Layout persistente
        for widget in self.model_plot_display.winfo_children():
            widget.destroy()

        if not figures_list:
            self._render_empty_model_plot()
            return

        self.model_carousel_figs = figures_list
        self.model_carousel_index = 0

        # 1. CONTENEDOR EXCLUSIVO PARA EL CANVAS (Aquí se inyectarán y borrarán los gráficos)
        self.model_canvas_container = ctk.CTkFrame(master=self.model_plot_display, fg_color="transparent")
        self.model_canvas_container.pack(side="top", fill="both", expand=True)

        # 2. PANEL DE NAVEGACIÓN INFERIOR (Persistente, nunca se destruye)
        self.model_carousel_nav = ctk.CTkFrame(master=self.model_plot_display, fg_color="transparent")
        self.model_carousel_nav.pack(side="bottom", fill="x", pady=5)

        self.btn_model_prev = ctk.CTkButton(
            master=self.model_carousel_nav, text="<< Anterior", width=100, fg_color="#5a6268",
            command=lambda: self._navigate_model_carousel(-1)
        )
        self.btn_model_prev.pack(side="left", padx=20)

        self.model_carousel_lbl = ctk.CTkLabel(
            master=self.model_carousel_nav, text="Página 1 / 1", 
            font=(self.normal_font[0], 11, "bold") if hasattr(self, 'normal_font') else ("Arial", 11, "bold")
        )
        self.model_carousel_lbl.pack(side="left", expand=True)

        self.btn_model_next = ctk.CTkButton(
            master=self.model_carousel_nav, text="Siguiente >>", width=100, fg_color="#5a6268",
            command=lambda: self._navigate_model_carousel(1)
        )
        self.btn_model_next.pack(side="right", padx=20)

        # Cargar la primera página en el contenedor dedicado
        self._render_model_carousel_page()


    def _render_model_carousel_page(self) -> None:
        """Borra únicamente el canvas anterior e inyecta la nueva página de gráficos."""
        # Limpiar EXCLUSIVAMENTE el contenedor del gráfico, protegiendo los botones y etiquetas
        if hasattr(self, 'model_canvas_container') and self.model_canvas_container.winfo_exists():
            for child in self.model_canvas_container.winfo_children():
                child.destroy()
        else:
            # Fallback defensivo si por algún motivo no existe el contenedor dedicado
            return

        current_fig = self.model_carousel_figs[self.model_carousel_index]
        
        # El master del canvas es estrictamente el contenedor de gráficos
        canvas = FigureCanvasTkAgg(current_fig, master=self.model_canvas_container)
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True, padx=5, pady=5)
        canvas.draw()

        # Actualizar los metadatos de los controles que ahora están sanos y salvos
        total_pages = len(self.model_carousel_figs)
        if self.model_carousel_lbl.winfo_exists():
            self.model_carousel_lbl.configure(text=f"Página {self.model_carousel_index + 1} / {total_pages}")
        
        if self.btn_model_prev.winfo_exists():
            self.btn_model_prev.configure(state="normal" if self.model_carousel_index > 0 else "disabled")
            
        if self.btn_model_next.winfo_exists():
            self.btn_model_next.configure(state="normal" if self.model_carousel_index < total_pages - 1 else "disabled")

    def _navigate_model_carousel(self, direction: int) -> None:
        """Aumenta o disminuye el índice del paginador de gráficos."""
        new_index = self.model_carousel_index + direction
        if 0 <= new_index < len(self.model_carousel_figs):
            self.model_carousel_index = new_index
            self._render_model_carousel_page()

    def generate_scikit_quadrant_figures(self, model, X_test, y_test) -> list:
        """
        Construye una figura maestra dividida en un cuadrante de 2x2 (4 subplots independientes).
        Si necesitas añadir más gráficos a futuro, esta función puede retornar una lista de figuras 
        para activar automáticamente la paginación.
        """
        
        
        # Crear una figura adaptada al espacio del tabview
        fig = Figure(figsize=(8, 5.5), dpi=100)
        
        # --- Subplot 1: Matriz de Confusión ---
        ax1 = fig.add_subplot(221)
        try:
            preds = model.predict(X_test)
            cm = confusion_matrix(y_test, preds)
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1, cbar=False)
            ax1.set_title("Matriz de Confusión", fontsize=10, fontweight="bold")
            ax1.set_xlabel("Predicho")
            ax1.set_ylabel("Real")
        except Exception as e:
            ax1.text(0.5, 0.5, f"No disponible:\n{e}", ha='center', va='center', fontsize=8, style='italic')

        # --- Subplot 2: Curva ROC (AUC) ---
        ax2 = fig.add_subplot(222)
        try:
            RocCurveDisplay.from_estimator(model, X_test, y_test, ax=ax2, color=blue_widget)
            ax2.set_title("Curva ROC", fontsize=10, fontweight="bold")
            ax2.grid(True, alpha=0.3)
            ax2.get_legend().remove() # type: ignore # Reducir ruido visual
        except Exception:
            ax2.text(0.5, 0.5, "Requiere predict_proba()", ha='center', va='center', fontsize=8, style='italic')

        # --- Subplot 3: Curva Precision-Recall ---
        ax3 = fig.add_subplot(223)
        try:
            PrecisionRecallDisplay.from_estimator(model, X_test, y_test, ax=ax3, color="darkorange")
            ax3.set_title("Curva Precision-Recall", fontsize=10, fontweight="bold")
            ax3.grid(True, alpha=0.3)
            if ax3.get_legend(): ax3.get_legend().remove() # type: ignore
        except Exception:
            ax3.text(0.5, 0.5, "No disponible", ha='center', va='center', fontsize=8, style='italic')

        # --- Subplot 4: Importancia de Variables (Feature Importance) ---
        ax4 = fig.add_subplot(224)
        try:
            if hasattr(model, "feature_importances_"):
                importances = model.feature_importances_
                indices = np.argsort(importances)[-5:] # Mostrar las top 5 para no saturar el cuadrante
                features = [X_test.columns[i] for i in indices]
                ax4.barh(range(len(indices)), importances[indices], color="#20c997", align="center")
                ax4.set_yticks(range(len(indices)))
                ax4.set_yticklabels(features, fontsize=8)
                ax4.set_title("Top 5 Importancia de Variables", fontsize=10, fontweight="bold")
            else:
                ax4.text(0.5, 0.5, "Este algoritmo no genera\nimportancia de variables directa", ha='center', va='center', fontsize=8, style='italic')
        except Exception:
            ax4.text(0.5, 0.5, "Error al calcular", ha='center', va='center', fontsize=8, style='italic')

        fig.tight_layout()
        return [fig] # Retorna dentro de una lista por si el carrusel requiere extenderse a más páginas

    def on_run_describe_click(self) -> None:
        if hasattr(self, 'loadedData') and self.loadedData is not None and not self.loadedData.empty:
            desc_summary = self.loadedData.describe(include="all").fillna("N/A")
            
            missing_series = self.loadedData.isna().sum()
            non_null_series = self.loadedData.notna().sum()
            
            desc_summary.loc['missing'] = missing_series
            desc_summary.loc['non_null'] = non_null_series

            desc_cols = ['Métrica'] + list(desc_summary.columns)

            if hasattr(self, 'desc_table') and self.desc_table:
                # 1. First format the row string matrix based on current checkbox configurations
                formatted_matrix = self.update_exploration_table_rows(desc_summary)
                
                self.carousel_tables = [
                {"title": "Resumen basado en análisis descriptivo", "cols": desc_cols, "rows": formatted_matrix}
                    ]
                self.current_table_index = 0
                self.display_table_carousel_slice()
        else:
            messagebox.showwarning(
                "Aviso",
                "No hay datos cargados para calcular. Por favor, cargue un archivo CSV desde Inicio."
            )

    def load_db_table(self, table_name: str):
        """Load database table safely using threading + after()."""

        if not getattr(self, 'is_connected', False):
            messagebox.showwarning("Advertencia", "No hay conexión activa a la base de datos.")
            return

        try:
            data_dicts = self.db_manager.fetch_table_data(table_name, limit=250)
            
            if not data_dicts:
                messagebox.showinfo("Info", f"La tabla '{table_name}' está vacía.")
                return

            df = pd.DataFrame(data_dicts)
            columns = list(df.columns)
            rows = [list(row) for row in df.values.tolist()]   # ensure pure python lists


            try:
                self.switch_panel('Datos de Pacientes')
                self.view_data(columns=columns, data=rows)
                messagebox.showinfo("Éxito", f"Tabla '{table_name}' cargada correctamente\n({len(rows)} registros)")
            
            except Exception as e:
                messagebox.showerror("Error", f"Error actualizando UI:\n{e}")


        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar {table_name}:\n{str(e)}")




    def update_exploration_table_rows(self, desc_summary) -> list:
        formatted_matrix = []
        for metric_name in desc_summary.index:
            display_name = metric_translations.get(metric_name, metric_name)
            
            switch_var = self.table_metric_switches.get(display_name)
            if switch_var and not switch_var.get():
                continue

            raw_values = desc_summary.loc[metric_name].tolist()
            formatted_row = [display_name]
            for v in raw_values:
                if pd.isna(v) or v == "N/A":
                    formatted_row.append("N/A")
                elif isinstance(v, (int, float)):
                    if metric_name in ['count', 'missing', 'non_null', 'unique', 'freq'] or float(v).is_integer():
                        formatted_row.append(str(int(v)))
                    else:
                        formatted_row.append(f"{v:.2f}")
                else:
                    formatted_row.append(str(v))
                    
            formatted_matrix.append(formatted_row)
        
        return formatted_matrix


    def open_variable_selection_modal(self, event = None) -> None:
        if not hasattr(self, 'loadedData') or self.loadedData is None or self.loadedData.empty:
            messagebox.showwarning(
                "Aviso", 
                "No hay datos cargados. Por favor, cargue un archivo CSV desde Inicio antes de Definir variables."
            )
            return

        if not hasattr(self, 'model_features') or self.model_features is None:
            self.model_features = []
        if not hasattr(self, 'model_outputs') or self.model_outputs is None:
            self.model_outputs = []

        modal = ctk.CTkToplevel(self.toplvl)
        modal.title("Definir Variables")
        modal.geometry("550x600")
        modal.transient(self.toplvl)
        modal.grab_set()

        modal.grid_rowconfigure(2, weight=1)
        modal.grid_columnconfigure(0, weight=1)
        modal.grid_columnconfigure(1, weight=1)

        title_lbl = ctk.CTkLabel(master=modal, text="Configuración de Variables para Modelado", font=(self.title_font[0], 14, "bold"))
        title_lbl.grid(row=0, column=0, columnspan=2, pady=(15, 5), padx=15, sticky="w")

        self.selected_features_vars = {}
        self.selected_outputs_vars = {}
        
        feature_checkboxes = {}
        output_checkboxes = {}
        available_columns = list(self.loadedData.columns)

        def on_checkbox_toggle(column_name: str, target_side: str):
            if target_side == "X":
                is_checked = self.selected_features_vars[column_name].get()
                if is_checked:
                    self.selected_outputs_vars[column_name].set(False)
                    output_checkboxes[column_name].configure(state="disabled")
                else:
                    output_checkboxes[column_name].configure(state="normal")
            elif target_side == "Y":
                is_checked = self.selected_outputs_vars[column_name].get()
                if is_checked:
                    self.selected_features_vars[column_name].set(False)
                    feature_checkboxes[column_name].configure(state="disabled")
                else:
                    feature_checkboxes[column_name].configure(state="normal")

        def select_all_features():
            for col in available_columns:
                if not self.selected_outputs_vars[col].get():
                    self.selected_features_vars[col].set(True)
                    on_checkbox_toggle(col, "X")

        def select_all_outputs():
            for col in available_columns:
                if not self.selected_features_vars[col].get():
                    self.selected_outputs_vars[col].set(True)
                    on_checkbox_toggle(col, "Y")

        btn_all_x = ctk.CTkButton(master=modal, text="Seleccionar Todo X", font=(self.normal_font[0], 11), command=select_all_features, height=24)
        btn_all_x.grid(row=1, column=0, padx=15, pady=(5, 5), sticky="w")

        btn_all_y = ctk.CTkButton(master=modal, text="Seleccionar Todo Y", font=(self.normal_font[0], 11), command=select_all_outputs, height=24)
        btn_all_y.grid(row=1, column=1, padx=15, pady=(5, 5), sticky="w")

        features_frame = ctk.CTkScrollableFrame(master=modal, label_text="Características (Variables X)")
        features_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        outputs_frame = ctk.CTkScrollableFrame(master=modal, label_text="Variables de Salida (Y)")
        outputs_frame.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")

        for col in available_columns:
            was_feature = col in self.model_features
            was_output = col in self.model_outputs

            x_var = tk.BooleanVar(value=was_feature)
            self.selected_features_vars[col] = x_var
            chk_x = ctk.CTkCheckBox(
                master=features_frame, text=col, variable=x_var,
                command=lambda c=col: on_checkbox_toggle(c, "X")
            )
            chk_x.pack(anchor="w", pady=4, padx=5)
            feature_checkboxes[col] = chk_x

            y_var = tk.BooleanVar(value=was_output)
            self.selected_outputs_vars[col] = y_var
            chk_y = ctk.CTkCheckBox(
                master=outputs_frame, text=col, variable=y_var,
                command=lambda c=col: on_checkbox_toggle(c, "Y")
            )
            chk_y.pack(anchor="w", pady=4, padx=5)
            output_checkboxes[col] = chk_y

            if was_feature:
                on_checkbox_toggle(col, "X")
            elif was_output:
                on_checkbox_toggle(col, "Y")

        btn_frame = ctk.CTkFrame(master=modal, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=2, pady=15, padx=10, sticky="e")

        def save_and_close():
            features_chosen = [col for col, var in self.selected_features_vars.items() if var.get()]
            outputs_chosen = [col for col, var in self.selected_outputs_vars.items() if var.get()]
            
            self.model_features = features_chosen
            self.model_outputs = outputs_chosen
            
            messagebox.showinfo("Guardado", f"Configuración guardada:\n\nVariables de entrada (Features): {len(features_chosen)}\nVariables de salida (outputs): {len(outputs_chosen)} seleccionadas")
            modal.destroy()

        cancel_btn = ctk.CTkButton(master=btn_frame, text="Cancelar", fg_color="#5a6268", command=modal.destroy, width=100)
        cancel_btn.pack(side="left", padx=5)

        confirm_btn = ctk.CTkButton(master=btn_frame, text="Confirmar", fg_color=blue_widget, command=save_and_close, width=100)
        confirm_btn.pack(side="left", padx=5)


    def _on_import_model(self) -> None:
        """
        Abre un cuadro de diálogo para cargar un pipeline binario (.pkl),
        restaurando el estimador y sus esquemas estructurales en memoria.
        """
        file_path = filedialog.askopenfilename(
            title="Seleccionar Modelo Entrenado Envasado...",
            filetypes=[("Archivos Pickle", "*.pkl"), ("Todos los archivos", "*.*")]
        )
        
        if not file_path:
            return  # El usuario canceló la operación

        import pickle
        try:
            self.log(message=f"importando modelo...")
            
            with open(file_path, 'rb') as f:
                model_artifact = pickle.load(f)
            
            # Validación de consistencia estructural del diccionario guardado
            if not isinstance(model_artifact, dict) or "model" not in model_artifact:
                raise ValueError("La cabecera del archivo no contiene una estructura estructurada de artefacto válida.")

            # Restauración exacta de parámetros de sesión y metadatos
            self.trained_model = model_artifact["model"]
            self.model_features = model_artifact.get("features", [])
            self.model_outputs = model_artifact.get("target", None)
            
            # Actualización del panel de bitácora superior
            model_name = type(self.trained_model).__name__
            self.log(message=f"Modelo '{model_name}' importado con éxito ({len(self.model_features)} features).") # type: ignore
            
            messagebox.showinfo(
                "Éxito", 
                f"Pipeline importado correctamente.\n\n"
                f"Estimador: {model_name}\n"
                f"Variables de entrada: {len(self.model_features)}\n" # type: ignore
                f"Variable objetivo: {self.model_outputs}"
            )
            
        except Exception as e:
            self.log(message="Error crítico al deserializar el artefacto del modelo.")
            messagebox.showerror(
                "Error de Importación", 
                f"No se pudo decodificar el flujo binario del archivo seleccionado:\n{str(e)}"
            )



    def _on_save_model_as_click(self) -> None:
        """Abre un cuadro de diálogo para guardar el modelo actual y sus metadatos en un archivo .pkl"""
        if not hasattr(self, 'trained_model') or self.trained_model is None:
            messagebox.showwarning("Aviso", "No hay ningún modelo entrenado u optimizado disponible para guardar.")
            return

        # Solicitar al usuario la ubicación de memoria persistente
        file_path = filedialog.asksaveasfilename(
            title="Guardar Modelo Entrenado Como...",
            defaultextension=".pkl",
            filetypes=[("Archivos Pickle", "*.pkl"), ("Todos los archivos", "*.*")]
        )
        
        if not file_path:
            return # El usuario canceló la operación

        import pickle
        try:
            # Empaquetamos el modelo junto con las variables requeridas para garantizar consistencia al predecir
            model_artifact = {
                "model": self.trained_model,
                "features": getattr(self, 'model_features', []),
                "target": getattr(self, 'model_outputs', None)
            }
            
            with open(file_path, 'wb') as f:
                pickle.dump(model_artifact, f)
                
            messagebox.showinfo("Éxito", f"Modelo persistido correctamente en memoria:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error de Guardado", f"No se pudo guardar el archivo del modelo:\n{str(e)}")


    def _on_execute_prediction_click(self) -> None:
        """
        Extracts cell vectors from selected rows inside self.desc_table_patients, 
        and executes real-time inference using the active model pipeline.
        """
        # 1. Security Check: Verify model presence
        if not hasattr(self, 'trained_model') or self.trained_model is None:
            messagebox.showwarning(
                "Modelo no encontrado", 
                "Debe algún modelo o cargar un archivo de modelo válido (.pkl) antes de ejecutar la predicción."
            )
            return

        # 2. Dynamic Schema Inspection: Safely retrieve the model's training feature requirements
        if hasattr(self.trained_model, "feature_names_in_"):
            expected_features = list(self.trained_model.feature_names_in_)
        elif hasattr(self.trained_model, "get_booster"):  # Fallback layer for core XGBoost modules
            expected_features = self.trained_model.get_booster().feature_names
        else:
            # Fallback to structural attributes tracking arrays
            expected_features = getattr(self, 'model_features', [])

        target = getattr(self, 'model_outputs', 'Target')

        if not expected_features:
            messagebox.showerror(
                "Model Error", 
                "Could not extract or resolve the input feature specifications from the active model."
            )
            return

        # 3. Extract items using self.desc_table_patients abstract methods API
        try:
            selected_items = self.desc_table_patients.get_selected_items()
            table_columns = self.desc_table_patients.get_columns()
        except AttributeError:
            messagebox.showerror(
                "Interface Error", 
                "Could not access the abstract wrapper methods of self.desc_table_patients."
            )
            return

        if not selected_items:
            messagebox.showwarning(
                "Selection Empty", 
                "Please select one or more rows in the main data view table to execute predictions."
            )
            return

        # 4. Check for feature overlap alignment
        valid_features = [col for col in expected_features if col in table_columns]
        
        if len(valid_features) != len(expected_features):
            missing_from_ui = [col for col in expected_features if col not in table_columns]
            messagebox.showerror(
                "Column Missing Error",
                f"The trained model requires features that are missing from the current table view.\n"
                f"Missing layout requirements: \n{', '.join(missing_from_ui)}"
            )
            return

        try:
            feature_indices = {col: table_columns.index(col) for col in valid_features}
            
            extracted_rows_X = []
            extracted_rows_full = []
            
            for item in selected_items:
                row_values = self.desc_table_patients.get_item_values(item)
                if not row_values:
                    continue
                
                # Build predictive inference arrays mapping token vectors
                x_dict = {}
                for col in valid_features:
                    val_str = row_values[feature_indices[col]]
                    try:
                        x_dict[col] = float(val_str)
                    except ValueError:
                        x_dict[col] = 0.0
                extracted_rows_X.append(x_dict)
                
                # Copy complete row arrays block tokens metadata for audit tracking presentation
                full_row_dict = {table_columns[i]: row_values[i] for i in range(len(table_columns))}
                extracted_rows_full.append(full_row_dict)

            X_infer = pd.DataFrame(extracted_rows_X)
            sliced_df = pd.DataFrame(extracted_rows_full)

            # --- FORCE STRICT SCHEMATIC ALIGNMENT ---
            # Drops unintended metadata columns like 'sex' and enforces the correct order
            X_infer = X_infer[expected_features]

            # 5. Compute matrix tensor calculations
            if hasattr(self.trained_model, "predict"):
                predictions = self.trained_model.predict(X_infer)
            else:
                raise ValueError("The loaded model pipeline does not implement a valid .predict() execution signature.")

            # 6. Render results window cleanly bound to CustomTkinter's root loop context
            pred_window = PredictionWindow(
                master=self.toplvl, 
                dataframe=sliced_df, 
                target_col=target, 
                predictions=predictions
            )
            pred_window.grab_set()
            
        except Exception as err:
            messagebox.showerror(
                "Inference Engine Crash", 
                f"An error occurred while compiling vectors or feeding records into the estimator:\n{str(err)}"
            )



    def menubar(self) -> None:
        active_bg_color = '#3b8cc6'
        menubar = tk.Menu(self.toplvl)
        self.toplvl.config(menu=menubar)

        self.file = tk.Menu(menubar, font=self.normal_font, tearoff=0)
        self.options = tk.Menu(menubar, font=self.normal_font, tearoff=0)
        self.edit = tk.Menu(menubar, font=self.normal_font, tearoff=0)
        self.view = tk.Menu(menubar, font=self.normal_font, tearoff=0)
        self.help = tk.Menu(menubar, font=self.normal_font, tearoff=0)
        self.model_menu = tk.Menu(menubar, font=self.normal_font, tearoff=0)

        menus_and_cascades = {'Archivo': self.file, 
                              'Opciones': self.options, 
                            #   'Editar': self.edit, 
                              'Vista': self.view, 
                              'Ayuda': self.help
                              }
        
        file_options = {
            'Cargar Modelo...':self._on_import_model,
            'Guardar Modelo...':self._on_save_model_as_click,
            'Importar Datos...': self.load_data,
            'Guardar Datos de Análisis': ...,
            'Exportar Datos de Análisis': ..., 
            'Exportar Gráficos': ...,
            'Salir': self.on_close_func
        }
        
        opt_options = {
            'Definir variables': self.open_variable_selection_modal,
            'Ejecutar predicción': self._on_execute_prediction_click, 
            'Guardar result. de pred.': ...,
        } 


        opt_options_shortcuts ={
            'Definir variables': 'Ctrl+Shift+O',
            'Ejecutar predicción': ..., 
            'Guardar result. de pred.': ...,
        }
        file_shortcuts = {
            'Guardar Datos de Análisis': 'Ctrl+Shift+S',
            'Exportar Datos de Análisis': 'Ctrl+Shift+X', 
            'Exportar Gráficos': 'Ctrl+G',
            'Salir': ...
        }
        
        view_options = {
            'Datos de Pacientes': self.switch_to_patient_data_panel,
            'Exploración': self.switch_to_exploration_panel,
            'Modelado ML': self.switch_to_models_panel,
            'Conectar a BD': self.switch_to_db_config_pannel,
        }
        
        view_shortcuts = {
            'Datos de Pacientes': 'Shift+M',
            'Exploración': 'Shift+H',
            'Modelado ML': 'Shift+O'
        }

        help_option = {
            'Acerca del software': ...,
            'Términos de Uso':..., 
            'Licencia de codigo': ...,
            'Visitar repositorio (Github)...': self.open_github_repository,

        }

        for item, func in help_option.items():
            if item == "Visitar repositorio (Github)...":
                self.help.add_command(label=item, font=self.normal_font, activebackground=active_bg_color, command=func, state = 'normal') # type: ignore
            else:
                self.help.add_command(label=item, font=self.normal_font, activebackground=active_bg_color, command=func, state = 'disabled') # type: ignore


        self.view_options = {}

        for item, func in view_options.items():
            if item == 'Colapsar Form. de Paciente':
                if not self.is_on_navbar:
                    self.view.add_command(label=item, font=self.normal_font, activebackground=active_bg_color, command=func, state='disabled')
            else:
                self.view.add_command(label=item, font=self.normal_font, activebackground=active_bg_color, command=func)
            self.view_options[item] = self.view.index(item)
            # if item in ['Exploración', ]:
            #     self.view.add_separator()
            # if item in ['Modelado ML', ]:
            self.view.add_separator()
        
        self.view.entryconfig(index='Datos de Pacientes', accelerator=view_shortcuts['Datos de Pacientes'])
        self.view.entryconfig(index='Exploración', accelerator=view_shortcuts['Exploración'])
        self.view.entryconfig(index='Modelado ML', accelerator=view_shortcuts['Modelado ML'])
        
        self.model_menu.add_command(label="Cargar Modelo (.pkl)", command=self._on_import_model)
        self.model_menu.add_command(label="Guardar Modelo...", command=self._on_save_model_as_click)

        self.toplvl.bind_all("<Shift-H>", self.switch_to_exploration_panel)
        self.toplvl.bind_all("<Shift-M>", self.switch_to_patient_data_panel)
        self.toplvl.bind_all("<Shift-O>", self.switch_to_models_panel)

        for item, func in file_options.items():
            if item in ['Exportar Gráficos', 'Guardar Datos de Análisis', 'Exportar Datos de Análisis']:
                self.file.add_command(label=item, font=self.normal_font, activebackground=active_bg_color, command=func, state = "disabled")

            else:
                self.file.add_command(label=item, font=self.normal_font, activebackground=active_bg_color, command=func)
            self.file.add_separator()


        for item, func in opt_options.items():
            self.options.add_command(label=item, font=self.normal_font, activebackground=active_bg_color, command=func)
            if item == "Definir variables":
                self.options.add_separator()
            
        self.file.entryconfig(index='Guardar Datos de Análisis', accelerator=file_shortcuts['Guardar Datos de Análisis'])
        self.file.entryconfig(index='Exportar Datos de Análisis', accelerator=file_shortcuts['Exportar Datos de Análisis'])
        self.file.entryconfig(index='Exportar Gráficos', accelerator=file_shortcuts['Exportar Gráficos'])


        self.options.entryconfig(index='Definir variables', accelerator=opt_options_shortcuts["Definir variables"])
        self.toplvl.bind_all("<Control-Shift-O>", self.open_variable_selection_modal)


        self.toplvl.bind_all("<Control-Shift-S>", self.saveData)
        self.toplvl.bind_all("<Control-Shift-X>", self.exportData)
        self.toplvl.bind_all("<Control-G>", self.export_grapth)

        for menu, cascade in menus_and_cascades.items():
            menubar.add_cascade(label=menu, menu=cascade)

    def saveData(self, event: tk.Event|None=None) -> None:
        print('file saved')

    def exportData(self, event: tk.Event|None=None) -> None:
        print('excel file exported')

    def export_report(self, event: tk.Event|None=None) -> None:
        print('report exported')
    
    def export_grapth(self, event: tk.Event|None=None) -> None:
        print('grapth exported')
    
    def open_github_repository(self) -> None:
        """
        Safely invokes the operating system's default web browser 
        to open the project source or profile repository link.
        """
        import webbrowser
        
        github_url = "https://github.com/javiNguema/DatahealthProject/blob/3cd5d99a177a6a17293a599dee382631cfa85baa/README.md" 
        
        try:
            # Open the URL in a new browser tab if possible, otherwise a new window
            webbrowser.open_new_tab(github_url)
            self.log(message=f"Successfully directed system browser link context to: {github_url}")
        except Exception as e:
            # Fallback error logger tracking if the OS environment rejects browser execution
            if hasattr(self, 'log'):
                self.log(message=f"Error trying to open browser link: {str(e)}")
            else:
                print(f"Error opening link: {e}")

    

        
class CustomTable(ctk.CTkFrame):
    def __init__(
        self, 
        master, 
        columns: list | tuple = [], 
        default_cwidth: int = 180,
        default_height: int = 35,
        row_height: int = 10, 
        font_data: tuple = ("Arial", 10),
        font_header: tuple = ("Arial", 12, "bold"),
        even_row_color: str = "#ececec",
        odd_row_color: str = "#ffffff",
        use_x_scrollbar: bool = True,
        use_y_scrollbar: bool = True,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        if not (len(columns) > 0):
            self.columns = [f'column {item}' for item in range(7)]
        else:
            self.columns = list(columns)
        self.is_loaded = False
        
        self.default_cwidth = default_cwidth
        self.fontdata = font_data



        self.even_row_color = even_row_color
        self.odd_row_color = odd_row_color

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.style_name = f"CustomTable_{id(self)}.Treeview"
        self.style = ttk.Style()
        self.style.configure(self.style_name, rowheight=row_height, font=font_data)
        self.style.configure(f"{self.style_name}.Heading", font=font_header)

        self.tree = ttk.Treeview(
            master=self,
            selectmode=tk.EXTENDED,
            show='headings',
            columns=self.columns,
            style=self.style_name,
            height=default_height
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        for col in self.columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, anchor=tk.CENTER, width=self.default_cwidth, stretch=False)

        if use_y_scrollbar:
            self.ysb = ctk.CTkScrollbar(master=self, orientation='vertical', command=self.tree.yview)
            self.tree.configure(xscrollcommand=self.ysb.set) # type: ignore (Fix layout fit tracker bind)
            self.tree.configure(yscrollcommand=self.ysb.set)
            self.ysb.grid(row=0, column=1, sticky='ns')

        if use_x_scrollbar:
            self.xsb = ctk.CTkScrollbar(master=self, orientation='horizontal', command=self.tree.xview)
            self.tree.configure(xscrollcommand=self.xsb.set)
            self.xsb.grid(row=1, column=0, sticky='ew')

        self.tree.tag_configure("evenrow", background=self.even_row_color)
        self.tree.tag_configure("oddrow", background=self.odd_row_color)

    # Add these methods directly inside your CustomTable class to expose selection and columns cleanly

    def get_selected_items(self) -> list[str]:
        """
        Returns a list of selected row item IDs (iids) from the underlying Treeview.
        """
        return list(self.tree.selection())

    def get_item_values(self, item_id: str) -> tuple:
        """
        Returns the data values matching a specific row item ID.
        """
        return tuple(self.tree.item(item_id, "values"))

    def get_columns(self) -> list[str]:
        """
        Returns the list of current active columns configured in the table matrix.
        """
        return self.columns

    def clear(self) -> None:
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.columns = [f'column {item}' for item in range(7)]
        
        self.tree.configure(columns=self.columns)
        
        for col in self.columns:
            self.tree.heading(col, text=str(col), anchor=tk.CENTER)
            self.tree.column(col, anchor=tk.CENTER, width=self.default_cwidth, stretch=False)
        self.is_loaded = False
    

    def tree_config(self, columns: list | tuple, data_list: list[tuple | list] = None) -> None: # type: ignore
        """
        Safely updates columns dynamically, forces headings to repaint, 
        and updates table values without destroying the frame.
        """
        
        self.clear()
        self.columns = list(columns)
        self.tree.configure(columns=self.columns, style=self.style_name)

        
        for col in self.columns:
            self.tree.heading(col, text=str(col), anchor=tk.CENTER)
            self.tree.column(col, anchor=tk.CENTER, width=self.default_cwidth, stretch=False)

        if data_list is not None:
            self._insert_rows(data_list)
    
        

    def _insert_rows(self, data_list: list[tuple | list]) -> None:
        list(map(self._insert_single_row, enumerate(data_list)))
        self.is_loaded = True
    
    def _insert_single_row(self, item):
        index, row_values = item
        tag = "evenrow" if index % 2 != 0 else "oddrow"
        self.tree.insert("", "end", values=tuple(row_values), tags=(tag,))

    def get_selected_row(self) -> tuple | None:
        focused_item = self.tree.focus()
        if focused_item:
            return self.tree.item(focused_item, "values") # type: ignore
        return None


class PredictionWindow(ctk.CTkToplevel):

    def __init__(self, master, dataframe: pd.DataFrame, target_col: str, predictions: np.ndarray, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("Resultados de la Predicción")
        self.geometry("900x550")
        self.minsize(800, 450)
        
        self.df = dataframe.copy()
        
        prediction_label = f"PREDICCIÓN ({target_col})" if target_col else "PREDICCIÓN_MODELO"
        self.df[prediction_label] = predictions


        cols = [prediction_label] + [c for c in self.df.columns if c != prediction_label]
        self.df = self.df[cols]

        self.header_frame = ctk.CTkFrame(master=self, fg_color="transparent")
        self.header_frame.pack(side="top", fill="x", padx=15, pady=10)
        
        self.title_lbl = ctk.CTkLabel(
            master=self.header_frame, 
            text="Resultados del Motor de Inferencia", 
            font=(master.normal_font[0], 16, "bold") if hasattr(master, 'normal_font') else ("Arial", 16, "bold")
        )
        self.title_lbl.pack(side="left")


        self.btn_export = ctk.CTkButton(
            master=self.header_frame,
            text="📥 Exportar Resultados (CSV)",
            fg_color="#17a2b8",
            hover_color="#138496",
            width=150,
            command=self._export_predictions_csv
        )
        self.btn_export.pack(side="right", padx=5)


        self.table_container = ctk.CTkFrame(master=self, fg_color="transparent")
        self.table_container.pack(side="top", fill="both", expand=True, padx=15, pady=5)

        
        self.results_table = CustomTable(
            self.table_container,
            columns=list(self.df.columns),
            default_height=treeview_height,  
            default_cwidth=180,             
            font_data = ("Arial", 15),
            row_height= 20,
            font_header = ("Arial", 18, "bold"),
            even_row_color="#ececec",
            odd_row_color="#ffffff",
            use_x_scrollbar=True,
            use_y_scrollbar=True
        )
        self.results_table.pack(fill="both", expand=True)
        
        self.results_table.pack(fill="both", expand=True)

        self._populate_table_data()

    def _populate_table_data(self):
        """Formatea y traslada la matriz de Pandas a la estructura Treeview de la CustomTable."""
        columns = list(self.df.columns)
        
        rows = []
        for _, row in self.df.iterrows():
            row_vals = []
            for col in columns:
                val = row[col]

                if isinstance(val, (float, np.floating)):
                    row_vals.append(f"{val:.4f}")
                else:
                    row_vals.append(str(val))
            rows.append(row_vals)
            

        self.results_table.tree_config(columns, rows)

    def _export_predictions_csv(self):
        """Permite guardar localmente el DataFrame enriquecido con las etiquetas predichas."""
        file_path = filedialog.asksaveasfilename(
            title="Exportar Predicciones",
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")]
        )
        if file_path:
            try:
                self.df.to_csv(file_path, index=False)
                messagebox.showinfo("Éxito", f"Archivo guardado correctamente:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron exportar los datos:\n{str(e)}")



if __name__ == '__main__':
    root = tk.Tk()
    MainUI(root) # type: ignore
    root.mainloop()