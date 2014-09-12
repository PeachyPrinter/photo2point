from Tkinter import *
import sys
import os
import tkMessageBox
import tkFileDialog
from PIL import Image, ImageTk
from photopointapi import PhotoPointApi

class PhotoPoint(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self.path = path 
        self.geometry("1200x975")
        self.title('Photo Point')
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.rowconfigure(80, weight=1)
          
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.folder_opt = {}
        self.folder_opt['initialdir'] = '~/Desktop'
        self.folder_opt['parent'] = self
        self.folder_opt['title'] = 'Select folder containing images'

        self.point_cloud_file_opt = {}
        self.point_cloud_file_opt['initialdir'] = '~/Desktop'
        self.point_cloud_file_opt['parent'] = self
        self.point_cloud_file_opt['title'] = 'Select output file'
        self.point_cloud_file_opt['filetypes'] = [('all files', '.*'), ('ply files', '.ply')]
        self.point_cloud_file_opt['initialfile'] = ['output.ply']
        self.point_cloud_file_opt['defaultextension'] = '.ply'

        self.video_file_opt = {}
        self.video_file_opt['initialdir'] = '~/Desktop'
        self.video_file_opt['parent'] = self
        self.video_file_opt['title'] = 'Select output file'
        self.video_file_opt['filetypes'] = [('all files', '.*'), ('movie files', '.avi')]
        self.video_file_opt['initialfile'] = ['output.avi']
        self.video_file_opt['defaultextension'] = '.avi'


        self.folder_name = StringVar()
        self.folder_name.set('')

        self.point_could_output_file = StringVar()
        self.point_could_output_file.set('')

        self.video_output_file = StringVar()
        self.video_output_file.set('')

        self.image_count = IntVar()
        self.image_count.set(0)

        self.selected_image = IntVar()
        self.selected_image.set(0)
        self.crop = IntVar()
        self.crop.set(100)
        self.x_offset = IntVar()
        self.x_offset.set(0)
        self.y_offset = IntVar()
        self.y_offset.set(0)

        self.z_space = IntVar()
        self.z_space.set(5)
        self.scale = DoubleVar()
        self.scale.set(0.001)
        self.simplifcation = IntVar()
        self.simplifcation.set(20)

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


        Label( text = "Folder to process").grid(padx=2,column=0, row=10, sticky = E)
        Entry( textvariable = self.folder_name).grid(padx=2,column=1, row=10, columnspan=2,sticky=E+W)
        Button( text = "Select", command= self._get_folder).grid(padx=2,column=3, row=10,sticky=W)
        Label( text = "Number of images process:").grid(padx=2,column=4, row=10)
        Label( textvariable = self.image_count).grid(padx=2,column=5, row=10, sticky=W)

        Label( text = "Point file").grid(padx=2,column=0, row=17, sticky = E)
        Entry( textvariable = self.point_could_output_file).grid(padx=2,column=1, row=17, columnspan=2,sticky=E+W)
        Button(text = "Save as...", command= self._points_save_as).grid(padx=2,column=3, row=17,sticky=W)

        Label( text = "Video file").grid(padx=2,column=0, row=18, sticky = E)
        Entry( textvariable = self.video_output_file).grid(padx=2,column=1, row=18, columnspan=2,sticky=E+W)
        Button(text = "Save as...", command= self._video_save_as).grid(padx=2,column=3, row=18,sticky=W)

        Button(text = "Genetate Points", command= self.process_points).grid(padx=2,column=4, columnspan=2, row=17, sticky=E)
        Button(text = "Generate Video", command= self.process_video).grid(padx=2,column=4, columnspan=2, row=18, sticky=E)

        Label( text = "Z spacing (pixels)").grid(padx=2,column=0, row=20, sticky = E)
        Entry( textvariable = self.z_space,width = 10).grid(padx=2,column=1, row=20,sticky=W)
        Label( text = "Scale [0.001]").grid(padx=2,column=0, row=22, sticky = E)
        Entry( textvariable = self.scale,width = 10).grid(padx=2,column=1, row=22,sticky=W)
        Label( text = "Simplifcation [1]").grid(padx=2,column=0, row=25, sticky = E)
        Entry( textvariable = self.simplifcation,width = 10).grid(padx=2,column=1, row=25,sticky=W)

        Label(text ="Red Threshold").grid(padx=2,column=0, row=30, sticky=E+S)
        Label(text ="Green Threshold").grid(padx=2,column=0, row=40, sticky=E+S)
        Label(text ="Blue Threshold").grid(padx=2,column=0, row=50, sticky=E+S)

        Scale(variable = self.red_threshold,   command= self.update_required,to =  255, from_ = 0, orient=HORIZONTAL, ).grid(padx=2,column=1, row=30, sticky=E+W)
        Scale(variable = self.green_threshold, command= self.update_required,to =  255, from_ = 0, orient=HORIZONTAL, ).grid(padx=2,column=1, row=40, sticky=E+W)
        Scale(variable = self.blue_threshold,  command= self.update_required,to =  255, from_ = 0, orient=HORIZONTAL, ).grid(padx=2,column=1, row=50, sticky=E+W)

        Scale(variable = self.x_offset, command= self.update_required,to =  50, from_ = -50,  orient=HORIZONTAL, ).grid(padx=2,column=3, row=40, sticky=E+W)
        Scale(variable = self.y_offset, command= self.update_required,to =  50, from_ = -50,                     ).grid(padx=2,column=2, rowspan = 30, row=30, sticky=N+S)
    
        Label(textvariable = self.call_back_message).grid(padx=2,column=4, row=60)

        self.image_slider = Scale(to =  1, from_ = 1, command= self.update_required, length=500,  variable = self.selected_image )
        self.image_slider.grid(padx=2,column=5, row=80, sticky=N+S+E)
        Label(background='black').grid(padx=2,column=0, columnspan = 5, row=80,sticky=N+E+S+W)
        Scale(to =  100, from_ = 0, command= self.update_required, orient=HORIZONTAL, variable = self.crop ).grid(padx=2,column=0, columnspan = 5, row=85, sticky=N+E+S+W)

        self.after(1000 / 2 , self._show_image)
        self.update = True

    def _points_save_as(self):
        filename = tkFileDialog.asksaveasfilename(**self.point_cloud_file_opt)
        if filename:
            self.point_could_output_file.set(filename)

    def _video_save_as(self):
        filename = tkFileDialog.asksaveasfilename(**self.video_file_opt)
        if filename:
            self.video_output_file.set(filename)

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
        self.image_slider.grid(padx=2,)
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
            image, filename = self.api.test_image(
                                self.folder_name.get(),
                                (1067,600), 
                                self.rgb_threshold, 
                                self.selected_image.get(), 
                                crop = self.crop.get(), 
                                offset = (self.x_offset.get(), self.y_offset.get())
                                )
            photo = ImageTk.PhotoImage(image)
            self.photo = photo
            self.image_label = Label(image = photo).grid(padx=2,column=0, columnspan = 5, row=80,sticky=N+E+S+W)
        self.after(1000 / 2 , self._show_image)

    def process_points(self):
        self.api.process(
            self.folder_name.get(), 
            self.point_could_output_file.get(), 
            self.rgb_threshold,
            self.z_space.get(), 
            float(self.scale.get()),
            self.simplifcation.get(),
            self.call_back ,
            self.crop.get(),
            (self.x_offset.get(), self.y_offset.get())
            )

    def process_video(self):
        self.api.process_video(
            self.folder_name.get(), 
            self.video_output_file.get(), 
            self.rgb_threshold,
            crop = self.crop.get(), 
            offset = (self.x_offset.get(), self.y_offset.get()),
            callback = self.call_back 
            )


    def close(self):
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(os.path.realpath(__file__))

    app = PhotoPoint()
    app.title('Photo Point')
    app.mainloop()