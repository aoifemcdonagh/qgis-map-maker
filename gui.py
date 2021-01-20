"""
    GUI for running farm_layout.py
"""
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import os
import advanced_layout
import layout_utils

DEFAULT_PROJECT_DIR = 'projects/'
Path(DEFAULT_PROJECT_DIR).mkdir(parents=True, exist_ok=True)
UI_TO_JSON_DICT = layout_utils.get_UI_to_JSON()

# namespace to hold arguments to pass to farm_layout.py
class QGISArgs:
    def __init__(self, **kwargs):
        # attributes match attributes of argparse namespace in farm_layout.py
        self.file = ""
        self.project_path = ""
        self.farm_name = ""
        self.layout_name = ""
        self.map_count = None
        self.table_fields = []
        self.color_code = None
        self.label_data = None
        self.area_acres = None
        self.pdf = None
        self.__dict__.update(kwargs)


class MainApplication(tk.Frame):
    # todo include qgis project path here so that it can be opened at end of process
    # todo add code for creating project path here, pass full path to farm_layout.py
    def __init__(self, master):
        tk.Frame.__init__(self)
        self.master = master
        self.project_path = tk.StringVar()
        self.project_path.set("")
        self.qgis_args = None

        self.data_input = None
        self.processing_screen = None
        self.end_screen = None

        #self.btn_start = tk.Button(self, text="Start", command=self.start)
        #self.btn_start.pack()

        self.error_message = tk.StringVar()
        self.error = tk.BooleanVar()
        self.error.set(False)

        self.start()

    def set_project_path(self, path):
        self.project_path.set(path)

    def set_qgis_args(self, a):
        self.qgis_args = a

    def start(self):
        #self.btn_start.pack_forget()
        self.data_input = DataInput(self)
        self.data_input.pack(padx=20, pady=20)
        self.update()

    def start_processing_screen(self):
        self.data_input.pack_forget()
        self.processing_screen = ProcessingScreen(self)
        self.processing_screen.pack(padx=20, pady=20)
        self.update()
        # create thread to run processing script
        #th = threading.Thread(target=farm_layout.main, args=(self.qgis_args,))
        #th.daemon = True
        #th.start()
        #th.join()
        # todo catch errors from running qgis e.g. required args not specified
        # notify and give option to 'restart' another project
        try:
            advanced_layout.main(self.qgis_args)
        except AssertionError:
            self.error_message.set("ERROR: Required information not given. \n (project name or source file) \n\nQGIS project not created")
            self.error.set(True)
        self.start_end_screen()

    def start_end_screen(self):
        self.processing_screen.pack_forget()
        self.end_screen = EndScreen(self)
        self.end_screen.pack(padx=20, pady=20)
        self.update()

    #def start_qgis(self):
    #    start_qgis(self.project_path.get())

    def restart(self):
        self.project_path.set("")
        self.qgis_args = None
        self.error.set(False)
        self.end_screen.pack_forget()
        self.data_input = DataInput(self)  # clear DataInput
        self.data_input.pack(padx=20, pady=20)
        self.update()


class DataInput(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self)
        self.master = master

        # arguments to store
        self.table_fields = None

        self.frm_data = tk.Frame(self, bg="blue")
        self.frm_data.pack(fill=tk.X, expand=True, padx=20, pady=20)

        # initialise global vars
        # self.input_project_name = tk.StringVar()
        # self.input_layout_name = tk.StringVar()
        self.input_source_file = tk.StringVar()
        self.input_source_file.set("Source file")

        # Default sizes
        frame_pad = 10
        entry_pad = 5

        #todo use grid instead of multiple frames??
        self.frm_project_name = tk.Frame(master=self.frm_data, highlightbackground="red", highlightthickness=2)
        self.frm_project_name.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)
        self.frm_source_file = tk.Frame(master=self.frm_data, highlightbackground="red", highlightthickness=2)
        self.frm_source_file.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)
        self.frm_farm_name = tk.Frame(master=self.frm_data)
        self.frm_farm_name.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)
        self.frm_layout_name = tk.Frame(master=self.frm_data)
        self.frm_layout_name.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)
        self.frm_map_count = tk.Frame(master=self.frm_data)
        self.frm_map_count.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)

        # project name
        self.lbl_project_name = tk.Label(text="Project name, path or folder", master=self.frm_project_name)
        self.lbl_project_name.pack(fill=tk.Y, side=tk.LEFT)
        self.ent_project_name = tk.Entry(master=self.frm_project_name)
        self.ent_project_name.pack(fill=tk.Y, side=tk.RIGHT)

        # farm name
        self.lbl_farm_name = tk.Label(text="Farm name", master=self.frm_farm_name)
        self.lbl_farm_name.pack(fill=tk.Y, side=tk.LEFT)
        self.ent_farm_name = tk.Entry(master=self.frm_farm_name)
        self.ent_farm_name.pack(fill=tk.Y, side=tk.RIGHT)

        # source file
        self.lbl_source_file = tk.Label(text="Source file", master=self.frm_source_file,
                                        textvariable=self.input_source_file)
        self.lbl_source_file.pack(fill=tk.Y, side=tk.LEFT)
        self.btn_source_file = tk.Button(master=self.frm_source_file, text="browse", command=self.browse_button)
        self.btn_source_file.pack(side=tk.RIGHT)
        # ent_source_file = tk.Entry(master=frm_source_file)
        # ent_source_file.pack(fill=tk.Y, side=tk.RIGHT)

        # layout name
        self.lbl_layout_name = tk.Label(text="Layout name", master=self.frm_layout_name)
        self.lbl_layout_name.pack(fill=tk.Y, side=tk.LEFT)
        self.ent_layout_name = tk.Entry(master=self.frm_layout_name)
        self.ent_layout_name.pack(fill=tk.Y, side=tk.RIGHT)

        # map count
        self.lbl_map_count = tk.Label(text="Map count", master=self.frm_map_count)
        self.lbl_map_count.pack(fill=tk.Y, side=tk.LEFT)
        self.ent_map_count = tk.Entry(master=self.frm_map_count)
        self.ent_map_count.pack(fill=tk.Y, side=tk.RIGHT)

        #
        # table variables
        #
        self.frm_table_variables = tk.Frame(master=self.frm_data)
        self.frm_table_variables.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)

        self.lbl_table_variables = tk.Label(master=self.frm_table_variables, text="Table variables")
        self.lbl_table_variables.pack(fill=tk.Y, side=tk.LEFT)

        self.btn_table_variables = tk.Menubutton(master=self.frm_table_variables, text="select", relief=tk.RAISED)
        self.btn_table_variables.pack(fill=tk.Y, side=tk.RIGHT)

        self.table_variables_selected = tk.StringVar()
        self.lbl_table_variables_selected = tk.Label(master=self.frm_table_variables,
                                                     textvariable=self.table_variables_selected)
        self.lbl_table_variables_selected.pack(fill=tk.Y, side=tk.RIGHT)

        self.btn_table_variables.menu = tk.Menu(self.btn_table_variables, tearoff=0)
        self.btn_table_variables["menu"] = self.btn_table_variables.menu
        #self.btn_table_variables.menu.add_command(command=self.update_table_variables)

        self.table_field_vars = {}
        for UI_name in UI_TO_JSON_DICT.keys():
            table_var = tk.IntVar()
            self.btn_table_variables.menu.add_checkbutton(label=UI_name, variable=table_var)
            #chk_btn = tk.Checkbutton(self.frm_table_variables, text=option, variable=var)
            #chk_btn.grid()
            self.table_field_vars[UI_name] = table_var

        #
        # colour code variable
        #
        self.frm_color_variables = tk.Frame(master=self.frm_data)
        self.frm_color_variables.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)

        self.lbl_color_variables = tk.Label(master=self.frm_color_variables, text="Color Code variable")
        self.lbl_color_variables.pack(fill=tk.Y, side=tk.LEFT)

        self.btn_color_variables = tk.Menubutton(master=self.frm_color_variables, text="select", relief=tk.RAISED)
        self.btn_color_variables.pack(fill=tk.Y, side=tk.RIGHT)

        self.color_var = tk.StringVar()
        self.lbl_color_variable_selected = tk.Label(master=self.frm_color_variables, textvariable=self.color_var)
        self.lbl_color_variable_selected.pack(fill=tk.Y, side=tk.RIGHT)

        self.btn_color_variables.menu = tk.Menu(self.btn_color_variables, tearoff=0)
        self.btn_color_variables["menu"] = self.btn_color_variables.menu

        for UI_name in UI_TO_JSON_DICT.keys():
            self.btn_color_variables.menu.add_radiobutton(label=UI_name,
                                                          variable=self.color_var,
                                                          value=UI_name)

        #
        # label variable
        #
        self.frm_label_variables = tk.Frame(master=self.frm_data)
        self.frm_label_variables.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)

        self.lbl_label_variables = tk.Label(master=self.frm_label_variables, text="Label variable")
        self.lbl_label_variables.pack(fill=tk.Y, side=tk.LEFT)

        self.btn_label_variables = tk.Menubutton(master=self.frm_label_variables, text="select", relief=tk.RAISED)
        self.btn_label_variables.pack(fill=tk.Y, side=tk.RIGHT)

        self.label_var = tk.StringVar()
        self.lbl_label_variable_selected = tk.Label(master=self.frm_label_variables, textvariable=self.label_var)
        self.lbl_label_variable_selected.pack(fill=tk.Y, side=tk.RIGHT)

        self.btn_label_variables.menu = tk.Menu(self.btn_label_variables, tearoff=0)
        self.btn_label_variables["menu"] = self.btn_label_variables.menu

        for UI_name in UI_TO_JSON_DICT.keys():
            self.btn_label_variables.menu.add_radiobutton(label=UI_name,
                                                          variable=self.label_var,
                                                          value=UI_name)

        # Area unit
        self.frm_area_unit = tk.Frame(master=self.frm_data)
        self.frm_area_unit.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)

        self.lbl_area_unit = tk.Label(master=self.frm_area_unit, text="Area in acres")
        self.lbl_area_unit.pack(fill=tk.Y, side=tk.LEFT)

        self.area_acres = tk.BooleanVar()
        self.chkbtn_area_unit = tk.Checkbutton(master=self.frm_area_unit,
                                               variable=self.area_acres,
                                               onvalue=True,
                                               offvalue=False)
        self.chkbtn_area_unit.pack(side=tk.RIGHT)

        # start processing
        self.btn_create = tk.Button(master=self, text="Create QGIS Layout", command=self.run_processing)
        self.btn_create.pack()

    def browse_button(self):
        filename = filedialog.askopenfilename()
        self.input_source_file.set(filename)

    def run_processing(self):
        """
        Using data gathered by GUI, run farm_layout.py
        :return:
        """

        # create full project path
        project_path = self.get_project_path(self.ent_project_name.get())

        map_count = 1 if self.ent_map_count.get() is "" else int(self.ent_map_count.get())

        table_fields = self.get_fields(self.table_field_vars)
        fields = None if len(table_fields) == 0 else table_fields

        color_code = self.color_var.get()
        color_code = None if color_code is "" else UI_TO_JSON_DICT[color_code]

        label_var = self.label_var.get()
        label_var = None if label_var is "" else UI_TO_JSON_DICT[label_var]

        area_acres = self.area_acres.get()

        qgis_args = QGISArgs(file=self.input_source_file.get(),
                             project_path=project_path,
                             farm_name=self.ent_farm_name.get(),
                             layout_name=self.ent_layout_name.get(),
                             map_count=map_count,
                             table_fields=fields,
                             color_code=color_code,
                             label_data=label_var,
                             area_acres=area_acres)

        self.master.set_qgis_args(qgis_args)

        # set project path in MainApplication
        self.master.set_project_path(project_path)

        self.master.start_processing_screen()

    def get_project_path(self, input_string):
        """

        :param input_string:
        :return:
        """

        input_path = Path(input_string)
        p = ''

        # if input_string is a path to .qgs file, return input_string
        if input_path.suffix == '.qgs':
            p = input_path

        # if input_string is a path to a dir, return path to .qgs file in that dir
        elif input_path.is_dir():
            p = input_path / 'project.qgs'

        # if input_string is only a name, return path to 'name'.qgs in default project dir
        elif input_path.suffix == '':
            p = DEFAULT_PROJECT_DIR / input_path.with_suffix('.qgs')

        else:
            print("invalid project name/file specified. Most likely a non .qgs file specified")

        return str(p)

    def get_fields(self, d):
        """
        return list of selected table fields from checkboxes
        :param d:
        :return:
        """
        fields = [UI_TO_JSON_DICT[name] for name, value in d.items() if value.get() == 1]
        return fields

    def update_table_variables(self):
        """
        Updates string that holds table variables
        :return:
        """
        str_fields = ","
        fields_selected = self.get_fields(self.table_fields)
        str_fields.join(fields_selected)

        self.table_variables_selected.set(str_fields)


class ProcessingScreen(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self)
        self.master = master

        self.text = tk.Label(self, text="Processing...", width=50, height=5)
        self.text.pack()


class EndScreen(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self)
        self.master = master

        self.lbl_finished = tk.Label(self, text="Finished")
        self.lbl_error_message = tk.Label(self, textvariable=self.master.error_message, fg='red')

        self.btn_open_qgis = tk.Button(self,
                                       text="Open QGIS project",
                                       command=lambda: start_qgis_project(self.master.project_path.get()))

        self.btn_start_over = tk.Button(self, text="Create another project", command=self.master.restart)

        if self.master.error.get():  # if error
            self.lbl_error_message.pack(padx=20, pady=20)
            self.btn_start_over.pack()
        else:  # else print finished
            self.lbl_finished.pack(padx=20, pady=20)
            self.btn_open_qgis.pack(side=tk.LEFT, padx=20)
            self.btn_start_over.pack(side=tk.RIGHT, padx=20)




    def start_qgis(self):
        self.master.start_qgis()

    def restart(self):
        self.master.restart()

"""
class DynamicGrid(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.text = tk.Text(self, wrap="char", borderwidth=0, highlightthickness=0,
                            state="disabled")
        self.text.pack(fill="both", expand=True)
        self.boxes = []

    def add_box(self, check_box):
        box = tk.Frame(self.text, bd=1, relief="sunken", width=100, height=100)
        check_box.pack
        self.boxes.append(box)
        self.text.configure(state="normal")
        self.text.window_create("end", window=box)
        self.text.configure(state="disabled")
"""


def start_qgis_project(path):
    # run qgis project created
    os.startfile(path)


def get_form_fields(file):
    """
    todo return a dict with key = column name, value = gui name
    :param file:
    :return:
    """

    names = []

    with open(file, 'r') as data:
        lines = data.read().splitlines()

        for line in lines:
            names.append(line)

    return names

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Layout Builder")

    #root.maxsize(500, 500)

    #heading = tk.Label(root, text="Farmeye QGIS Layout Builder", width=50, height=5)
    #heading.pack()

    MainApplication(root).pack(side="top", fill="both", expand=True)

    root.mainloop()
