# CREATE USER INTERFACE FOR THE LAB MANAGEMENT SYSTEM 
import os 
import tkinter as tk
from tkinter import messagebox 
import customtkinter as ctk
from customtkinter import CTk
from PIL import Image
from ui_main import MainUI
from bitmaps import user_image
from db_initializer import DBInitializer  # Interacts with your refactored backend schema
import time
from utils import resource_path, kill_ollama_process


LOGO = resource_path("images/ub_logo.png")
COLOR_ERROR = "#f08080"
TRANSPARENT = "#FFFFFF"  # Fully transparent color for entry backgrounds

# Component Dimensions & Properties
entry_width = 300
padx = 10
pady = 6
blue_widget = '#3b8cc6'
gray_widget = '#5a5a5a'
title_font = ('helvetica', 14, 'bold')
normal_lbl_font = ('helvetica', 12, 'bold')

class LoginUI(CTk):

    user_loged_in: str
    
    def __init__(self) -> None:
        super().__init__()
        self.geometry('500x520') 
        self.resizable(width=False, height=False)
        self.title('ProjectCare - Iniciar Sesión')
        
        self.db_manager = DBInitializer() # initilize server config

        self.win_segments()
        self._top_segment()
        self._mid_segment()
        self._bottom_segment()
        self._newuser_segment()

    
    def connect_to_default_server(self) -> bool:
        try:
            connection_success = self.db_manager.initialize_auth_system()
            if not connection_success:
                messagebox.showwarning(
                    "Error de Conexión", 
                    "No se pudo establecer conexión con el servidor de la Base de Datos.\n\nPuede entrar al sistema como Invitado."
                )
        except Exception as e:
            print(f"Aviso: El sistema arrancará en modo local desacoplado: {e}")
            messagebox.showerror(
                "Error Crítico", 
                f"Error inesperado al conectar a la Base de Datos:\n{e}\n\nEntrar al sistema como Invitado."
            )
            return False
        else:
            return True


    def win_segments(self) -> None:
        """Sets up persistent container wrappers for standard login flow."""
        self.frames = []
        for _ in range(4):
            frame = ctk.CTkFrame(master=self, fg_color='transparent')
            frame.pack(side='top', anchor='n', expand=True, fill='both', padx=padx, pady=pady)
            self.frames.append(frame)
        self.top, self.mid, self.bottom, self.new_user = self.frames
    
    def _top_segment(self) -> None:
        """Loads and binds organization logos or credentials tracking metadata."""
        if os.path.exists(LOGO):
            leanbio_image = Image.open(LOGO)
            lbsys_image = ctk.CTkImage(light_image=leanbio_image, size=(300, 90))
            image = ctk.CTkButton(
                master=self.top, 
                image=lbsys_image, 
                text='', 
                fg_color='transparent',
                state='disabled'
            )
            image.pack(side='top', pady=(10, 5))
        
        creator_lbl = ctk.CTkLabel(
            master=self.top, 
            text='Software desarrollado por Javier R. Mitogo Nguema\n v 1.0',
            font=('helvetica', 11, 'italic')
        )
        creator_lbl.pack(side='top', pady=5, anchor='n')
    
    def _mid_segment(self) -> None:
        """Constructs input elements for user verification fields."""
        lbl_frame = ctk.CTkFrame(master=self.mid, fg_color='transparent')
        lbl_frame.pack(side='left', fill='y', padx=(30, 10), expand=True)
        entry_frame = ctk.CTkFrame(master=self.mid, fg_color='transparent')
        entry_frame.pack(side='left', fill='y', padx=(10, 30), expand=True)

        login_data_labels = ['Nombre de Usuario:', 'Contraseña:']
        self.entries = []

        for lbl in login_data_labels:
            label = ctk.CTkLabel(master=lbl_frame, text=lbl, font=normal_lbl_font, anchor='w')
            label.pack(side='top', anchor='w', fill='x', pady=8)
            
            if 'Contraseña' in lbl:
                entry = ctk.CTkEntry(master=entry_frame, width=entry_width, show='*')
            else:
                entry = ctk.CTkEntry(master=entry_frame, width=entry_width)
                
            entry.pack(side='top', anchor='w', pady=8)
            self.entries.append(entry)
            
        self.user_entry, self.pwrd_entry = self.entries
        
    def _bottom_segment(self) -> None:
        """Hosts login verification action buttons and Guest access trigger."""
        self.enter_btn = ctk.CTkButton(
            master=self.bottom, 
            text='Iniciar Sesión', 
            font=('helvetica', 12, 'bold'),
            fg_color=blue_widget,
            width=220,
            height=35,
            command=self._check_user_credentials
        )
        self.enter_btn.pack(side='top', anchor='n', pady=(10, 5))

        # NEW: Guest mode button that skips authentication checks entirely
        self.guest_btn = ctk.CTkButton(
            master=self.bottom, 
            text='Entrar como Invitado', 
            font=('helvetica', 12),
            fg_color=gray_widget,
            width=220,
            height=30,
            command=self._enter_as_guest
        )
        self.guest_btn.pack(side='top', anchor='n', pady=5)
    
    def _newuser_segment(self) -> None:
        """Navigates to user registration interface screen."""
        new_user_lbl = ctk.CTkLabel(master=self.new_user, text="¿No tienes cuenta?", font=('helvetica', 11))
        new_user_lbl.pack(side='left', padx=(40, 5), anchor='w')
        
        new_user_btn = ctk.CTkButton(
            master=self.new_user, 
            text='Registrarse', 
            font=('helvetica', 11, 'underline'),
            fg_color='transparent',
            text_color=blue_widget,
            hover=False,
            width=80,
            command=self.switch_to_add_user_ui
        )
        new_user_btn.pack(side='left', anchor='w')

    def entry_error(self) -> None:
        """Flash entries red briefly, then restore transparent background."""
        for entry in self.entries:
            entry.configure(fg_color=COLOR_ERROR)

        self.after(
            100,
            lambda: [
                entry.configure(fg_color=TRANSPARENT)
                for entry in self.entries
            ]
        )

    def _launch_main_workspace(self, username: str) -> None:
        """Internal helper to safely initialize and build the MainUI viewport workspace."""
        self.user_loged_in = username
        self._widthdraw_loggin()

        self.workspace_root = ctk.CTkToplevel(self)
        self.workspace_root.title("ProjectCare - Panel de pacientes")

        screen_w = self.workspace_root.winfo_screenwidth()
        screen_h = self.workspace_root.winfo_screenheight()
        self.workspace_root.geometry(f"{screen_w}x{screen_h}+0+0")

        if os.name == 'nt':
            self.workspace_root.state('zoomed')

        # Instantiate Main Dashboard interface container
        self.main_window = MainUI(
            toplvl=self.workspace_root, 
            user=self.user_loged_in,  # type: ignore
            on_close_func=self._on_workspace_closed
        )

        self.workspace_root.protocol(
            "WM_DELETE_WINDOW",
            self._on_workspace_closed
        )

        self.workspace_root.lift()
        self.workspace_root.focus_set()

    def _check_user_credentials(self) -> None:
        if not self.connect_to_default_server():
            return


        """Processes and queries login inputs against database table entities."""
        self.enter_btn.configure(state='disabled', text='Verificando...')
        username = self.user_entry.get().strip()
        password = self.pwrd_entry.get().strip()

        self.update_idletasks()

        try:
            success, result = self.db_manager.login_user(username, password)
        except Exception as err:
            success, result = False, f"Error de servidor de base de datos:\n{err}"

        if success:
            self.user_entry.delete(0, tk.END)
            self.pwrd_entry.delete(0, tk.END)
            self._launch_main_workspace(username)
            
            self.enter_btn.configure(state='normal', text='Iniciar Sesión')
        else:
            self.entry_error()
            messagebox.showerror("Error de Autenticación", result) # type: ignore
            self.enter_btn.configure(state='normal', text='Iniciar Sesión')

    def _enter_as_guest(self) -> None:
        """Bypasses backend authorization arrays completely to launch local visualization panels."""
        self.user_entry.delete(0, tk.END)
        self.pwrd_entry.delete(0, tk.END)
        # Directly execute layout building using a standalone identity profile
        self._launch_main_workspace("Invitado")

    def _on_workspace_closed(self) -> None:
        """Handles recycling, explicit garbage collection, and window lifecycle cleanups when workspace exits."""
        msg = messagebox.askyesno("Cerrar Sesión", "¿Está seguro de que desea cerrar sesión y salir del espacio de trabajo?")
        if msg:
            try:
                if hasattr(self, 'workspace_root') and self.workspace_root:
                    self.workspace_root.destroy()
            except Exception as e:
                print(f"Handled silent workspace window release exception: {e}")
            finally:
                self.geometry('500x520')
                self.switch_to_login_ui()
                self.deiconify()
                self.lift()
                
                kill_ollama_process()
                
                self.focus_force()

    def switch_to_add_user_ui(self) -> None:
        """Prepares geometry footprints and draws registration layout components."""
        for frame in self.frames:
            frame.pack_forget()

        self.geometry('550x640')
        self.title('ProjectCare - Registro de Nuevo Usuario')

        self.registration_fields = {
            'username': 'Nombre de Usuario:',
            'name': 'Nombre:',
            'surname': 'Apellidos:',
            'date_of_birth': 'Fec. Nacimiento (AAAA-MM-DD):',
            'department': 'Departamento:',
            'password': 'Contraseña:',
            'repeat_password': 'Repetir Contraseña:'
        }
        
        self.registration_entries = {}

        self.reg_title_frame = ctk.CTkLabel(
            master=self, 
            width=550, 
            height=40,
            text='REGISTRO DE NUEVO EMPLEADO', 
            font=title_font, 
            text_color='white',
            fg_color=blue_widget
        )
        self.reg_title_frame.pack(side='top', fill='x', pady=(0, 15))

        self.picture_frame = ctk.CTkFrame(master=self, fg_color='transparent')
        user_default_image = ctk.CTkImage(light_image=user_image, size=(100, 100))
        avatar_lbl = ctk.CTkLabel(master=self.picture_frame, image=user_default_image, text='')
        avatar_lbl.pack(side='top')
        self.picture_frame.pack(side='top', pady=5)

        self.form_frame = ctk.CTkFrame(master=self, fg_color='transparent')
        self.form_frame.pack(side='top', fill='both', expand=True, padx=40, pady=10)

        for idx, (field_key, field_label) in enumerate(self.registration_fields.items()):
            lbl = ctk.CTkLabel(master=self.form_frame, text=field_label, font=normal_lbl_font, anchor='w')
            lbl.grid(row=idx, column=0, padx=10, pady=6, sticky='w')

            if 'password' in field_key:
                entry = ctk.CTkEntry(master=self.form_frame, width=260, show='*')
            else:
                entry = ctk.CTkEntry(master=self.form_frame, width=260)
                
            entry.grid(row=idx, column=1, padx=10, pady=6, sticky='e')
            self.registration_entries[field_key] = entry

        self.reg_cancel_frame = ctk.CTkFrame(master=self, fg_color='transparent')
        self.reg_cancel_frame.pack(side='top', pady=(10, 20))

        self.register_btn = ctk.CTkButton(master=self.reg_cancel_frame, text='Registrar', width=120, fg_color=blue_widget, command=self.register_user)
        self.register_btn.pack(side='left', padx=15)

        self.cancel_btn = ctk.CTkButton(master=self.reg_cancel_frame, text='Cancelar', width=120, fg_color='grey50', command=self.cancel_register)
        self.cancel_btn.pack(side='left', padx=15)

        self.update_idletasks()

    def register_user(self) -> None:
        """Extracts text streams and evaluates inputs through the db initialization pipeline."""
        if not self.connect_to_default_server():
            return 
        
        user_payload = {}
        
        if self.registration_entries['password'].get() != self.registration_entries['repeat_password'].get():
            self.registration_entries['password'].configure(fg_color=COLOR_ERROR)
            self.registration_entries['repeat_password'].configure(fg_color=COLOR_ERROR)

            time.sleep(1)  
            self.registration_entries['password'].configure(fg_color=TRANSPARENT)
            self.registration_entries['repeat_password'].configure(fg_color=TRANSPARENT)    

            messagebox.showerror("Error de Validación", "Las contraseñas no coinciden. Por favor, inténtelo de nuevo.")
            return
        
        for field_key, entry_widget in self.registration_entries.items():
            user_payload[field_key] = entry_widget.get().strip()

        try:
            success, message = self.db_manager.register_user(user_payload)
        except Exception as e:
            success, message = False, f"Servidor inaccesible en este entorno:\n{e}"

        if success:
            messagebox.showinfo("Registro Exitoso", message)
            self.switch_to_login_ui()
        else:
            messagebox.showerror("Error de Validación", message)

    def cancel_register(self) -> None:
        """Aborts registration sequence safely and rolls back geometry layouts."""
        msg = messagebox.askokcancel(title='Confirmación', message='¿Desea cancelar el registro y volver al inicio?')
        if msg:
            self.switch_to_login_ui()

    def switch_to_login_ui(self) -> None:
        """Clears up active registration views and repaints standard login structures."""
        getattr(self, 'reg_title_frame', ctk.CTkFrame(self)).pack_forget()
        getattr(self, 'picture_frame', ctk.CTkFrame(self)).pack_forget()
        getattr(self, 'form_frame', ctk.CTkFrame(self)).pack_forget()
        getattr(self, 'reg_cancel_frame', ctk.CTkFrame(self)).pack_forget()

        self.geometry('500x520')
        self.title('ProjectCare - Iniciar Sesión')

        for frame in self.frames:
            frame.pack(side='top', anchor='n', expand=True, fill='both', padx=padx, pady=pady)
            
        self.update_idletasks()

    def _widthdraw_loggin(self) -> None:
        self.withdraw()

    def run(self) -> None:
        self.mainloop()

if __name__ == '__main__':
    app = LoginUI()
    app.run()