from Tkinter import *
import sys
import os
import tkMessageBox
import tkFileDialog
from PIL import Image, ImageTk
from photopointapi import PhotoPointApi

class MainUI(Frame):
    def __init__(self, parent):
        self.parent = parent
        self.folder_opt = {}
        self.folder_opt['initialdir'] = '~/Desktop'
        self.folder_opt['parent'] = parent
        self.folder_opt['title'] = 'Select folder containing images'

        self.file_opt = {}
        self.file_opt['initialdir'] = '~/Desktop'
        self.file_opt['parent'] = parent
        self.file_opt['title'] = 'Select output file'
        self.file_opt['filetypes'] = [('all files', '.*'), ('ply files', '.ply')]
        self.file_opt['initialfile'] = ['output.ply']
        self.file_opt['defaultextension'] = '.ply'


        self.folder_name = StringVar()
        self.folder_name.set('')

        self.output_file = StringVar()
        self.output_file.set('')

        self.image_count = IntVar()
        self.image_count.set(0)
        self.selected_image = IntVar()
        self.selected_image.set(0)

        self.z_space = IntVar()
        self.z_space.set(2)
        self.scale = DoubleVar()
        self.scale.set(0.001)
        self.simplifcation = IntVar()
        self.simplifcation.set(10)

        self.red_threshold = IntVar()
        self.red_threshold.set(40)
        self.green_threshold = IntVar()
        self.green_threshold.set(40)
        self.blue_threshold = IntVar()
        self.blue_threshold.set(100)

        self.image_available = False
        self.call_back_message = StringVar()
        self.call_back_message.set('')

        self.api = PhotoPointApi()



        Label( text = "Folder to process").grid(column = 0, row = 10, sticky = E)
        Entry( textvariable = self.folder_name,width = 50).grid(column = 1, row = 10)
        Button( text = "Select", command= self._get_folder).grid(column = 2, row = 10)
        Label( text = "Number of images process:").grid(column = 3, row = 10)
        Label( textvariable = self.image_count).grid(column = 4, row = 10, sticky=W)

        Label( text = "Output file").grid(column = 0, row = 17, sticky = E)
        Entry( textvariable = self.output_file,width = 50).grid(column = 1, row = 17)
        Button(text = "Save as...", command= self._save_as).grid(column = 2, row = 17)
        Label().grid(column=0, row = 20)

        Label( text = "Z spacing (pixels)").grid(column = 0, row = 18, sticky = E)
        Entry( textvariable = self.z_space,width = 50).grid(column = 1, row = 18)
        Label( text = "Scale [0.001]").grid(column = 0, row = 19, sticky = E)
        Entry( textvariable = self.scale,width = 50).grid(column = 1, row = 19)
        Label( text = "Simplifcation [1]").grid(column = 0, row = 20, sticky = E)
        Entry( textvariable = self.simplifcation,width = 50).grid(column = 1, row = 20)

        Label(text ="Red Threshold").grid(column=0, row = 30, sticky=E+S)
        Label(text ="Green Threshold").grid(column=0, row = 40, sticky=E+S)
        Label(text ="Blue Threshold").grid(column=0, row = 50, sticky=E+S)

        Scale(to =  255, from_ = 0, command= self.update_required, length=255, orient=HORIZONTAL, variable = self.red_threshold ).grid(column=1, columnspan = 2, row = 30, sticky=W)
        Scale(to =  255, from_ = 0, command= self.update_required, length=255, orient=HORIZONTAL, variable = self.green_threshold ).grid(column=1, columnspan = 2, row = 40, sticky=W)
        Scale(to =  255, from_ = 0, command= self.update_required, length=255, orient=HORIZONTAL, variable = self.blue_threshold ).grid(column=1, columnspan = 2, row = 50, sticky=W)
    
        Button(text = "Giver...", command= self.process).grid(column = 2, row = 60)
        Label(textvariable = self.call_back_message).grid(column = 3, row = 60)

        self.image_slider = Scale(to =  1, from_ = 1, command= self.update_required, length=500,  variable = self.selected_image )
        self.image_slider.grid(column=4, row = 80, sticky=N+S+E)
        self.image_slider.grid_remove()

        self.parent.after(1000 / 15 , self._show_image)
        self.update = True

    def _save_as(self):
        filename = tkFileDialog.asksaveasfilename(**self.file_opt)
        if filename:
            self.output_file.set(filename)

    def update_required(self, event = None):
        self.update = True

    def _get_folder(self):
        foldername = tkFileDialog.askdirectory(**self.folder_opt)
        if foldername:
            self.folder_name.set(foldername)
            self.folder_opt['initialdir'] = foldername
        
        images = self.api.count_images_in_folder(foldername)
        self.image_count.set(images)
        self.selected_image.set(images / 2)
        self.image_slider.config(to = images)
        self.image_slider.grid()
        if images > 0:
            self.image_available = True
            self.update_required()

    def call_back(self, message):
        self.call_back_message.set(message)

    @property
    def rgb_threshold(self):
        return (self.red_threshold.get(),self.green_threshold.get(),self.blue_threshold.get())

    def _show_image(self,event = None):
        if self.image_available and self.update:
            self.update = False
            api = PhotoPointApi()
            image, filename = self.api.test_image(self.folder_name.get(),(1067,600), self.rgb_threshold, self.selected_image.get())
            photo = ImageTk.PhotoImage(image)
            self.photo = photo
            self.image_label = Label(image = photo).grid(column=0, columnspan = 4, row = 80,sticky=N+E+S+W)
        self.parent.after(1000 / 15 , self._show_image)

    def process(self):
        self.api.process(
            self.folder_name.get(), 
            self.output_file.get(), 
            self.rgb_threshold,
            self.z_space.get(), 
            float(self.scale.get()),
            self.simplifcation.get(),
            self.call_back 
            )

class PhotoPoint(Tk):
    def __init__(self,parent, path):
        Tk.__init__(self,parent)
        self.path = path
        self.geometry("1200x900")
        self.title('Photo Point')
          
        self.parent = parent

        self.start_main_window()

        self.protocol("WM_DELETE_WINDOW", self.close)

    def start_main_window(self):
        MainUI(self)

    def close(self):
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(os.path.realpath(__file__))

    app = PhotoPoint(None,path)
    app.title('Photo Point')
    app.mainloop()