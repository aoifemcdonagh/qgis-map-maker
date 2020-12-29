"""
    GUI for running farm_layout.py
"""
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import threading
import os
import farm_layout

DEFAULT_PROJECT_DIR = 'projects/'

# namespace to hold arguments to pass to farm_layout.py
class QGISArgs:
    def __init__(self, **kwargs):
        # attributes match attributes of argparse namespace in farm_layout.py
        self.file = ""
        self.project_path = ""
        self.layout_name = ""
        self.table_fields = []
        self.colour_code = None
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

        self.data_input = None
        self.processing_screen = None
        self.end_screen = None

        self.btn_start = tk.Button(self, text="Start", command=self.start)
        self.btn_start.pack()

    def set_project_path(self, path):
        self.project_path = path

    def start(self):
        self.data_input = DataInput(self)
        self.data_input.pack()
        self.btn_start.pack_forget()

    def start_processing_screen(self):
        self.data_input.pack_forget()
        self.processing_screen = ProcessingScreen(self)
        self.processing_screen.pack()
        self.update()

    def start_end_screen(self):
        self.processing_screen.pack_forget()
        self.end_screen = EndScreen(self)
        self.end_screen.pack()

    #def start_qgis(self):
    #    start_qgis(self.project_path.get())

    def restart(self):
        self.end_screen.pack_forget()
        self.data_input = DataInput(self)  # clear DataInput
        self.data_input.pack()


class DataInput(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self)
        self.master = master

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

        self.frm_project_name = tk.Frame(master=self.frm_data)
        self.frm_project_name.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)
        self.frm_source_file = tk.Frame(master=self.frm_data)
        self.frm_source_file.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)
        self.frm_layout_name = tk.Frame(master=self.frm_data)
        self.frm_layout_name.pack(fill=tk.X, expand=True, padx=frame_pad, pady=frame_pad)

        # project name
        self.lbl_project_name = tk.Label(text="Project name, path or folder", master=self.frm_project_name)
        self.lbl_project_name.pack(fill=tk.Y, side=tk.LEFT)
        self.ent_project_name = tk.Entry(master=self.frm_project_name)
        self.ent_project_name.pack(fill=tk.Y, side=tk.RIGHT)

        # source file
        self.lbl_source_file = tk.Label(text="Source file", master=self.frm_source_file, textvariable=self.input_source_file)
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

        qgis_args = QGISArgs(file=self.input_source_file.get(),
                             project_path=project_path,
                             layout_name=self.ent_layout_name.get())

        # create thread to run processing script
        th = threading.Thread(target=farm_layout.main, args=(qgis_args,))
        th.start()

        # set project path in MainApplication
        self.master.set_project_path(project_path)

        self.master.start_processing_screen()

        th.join()

    def get_project_path(self, input_string):
        """

        :param input_string:
        :return:
        """

        input_path = Path(input_string)
        project_path = ''

        # if input_string is a path to .qgs file, return input_string
        if input_path.suffix == '.qgs':
            project_path = input_path

        # if input_string is a path to a dir, return path to .qgs file in that dir
        elif input_path.is_dir():
            project_path = input_path / 'project.qgs'

        # if input_string is only a name, return path to 'name'.qgs in default project dir
        elif input_path.suffix == '':
            project_path = DEFAULT_PROJECT_DIR / input_path.with_suffix('.qgs')

        else:
            print("invalid project name/file specified. Most likely a non .qgs file specified")

        return project_path


class ProcessingScreen(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self)
        self.master = master

        self.text_string = tk.StringVar()
        self.text_string.set("Processing...")

        self.text = tk.Label(self,
                             textvariable=self.text_string,
                             width=50,
                             height=5)
        self.text.pack()

        self.btn_next = tk.Button(self, text="next", command=self.start_end_screen)
        self.master.after(2000, self.btn_next.pack())

        """
        num = 3
        for i in range(num):
            self.master.after(1000, command=lambda: self.update_process_icon(i))

            if i == num - 1:
                # on last number go to next screen may not work
                self.btn_next.pack()"""

    def update_process_icon(self, value):
        self.text_string.set("Processing" + str(value))

    def start_end_screen(self):
        self.master.start_end_screen()


class EndScreen(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self)
        self.master = master

        self.text = tk.Label(self, text="Finished",
                            width=50,
                            height=5)
        self.text.pack()

        # todo create commands for both buttons
        # possibly set a flag which is handled by MainApplication?
        # either button triggers self.destroy() and sets corresponding flag
        self.btn_open_qgis = tk.Button(self,
                                       text="Open QGIS project",
                                       command=lambda: start_qgis_project(str(self.master.project_path)))
        self.btn_open_qgis.pack(side=tk.LEFT)

        self.btn_start_over = tk.Button(self, text="Create another project", command=self.restart)
        self.btn_start_over.pack(side=tk.RIGHT)

    def start_qgis(self):
        self.master.start_qgis()

    def restart(self):
        self.master.restart()


def start_qgis_project(path):
    # run qgis project created
    os.startfile(path)


if __name__ == "__main__":
    root = tk.Tk()
    root.maxsize(500, 500)

    heading = tk.Label(root, text="Farmeye QGIS Layout Builder",
                            width=50,
                            height=5)
    heading.pack()

    MainApplication(root).pack(side="top", fill="both", expand=True)

    root.mainloop()
