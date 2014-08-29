import os
from os import listdir
from os.path import isfile, join
import PIL
from PIL import Image, ImageTk,ImageOps, ImageChops
import threading
import math
import time
import numpy as np

class Photos2Points(threading.Thread):
    def __init__(self, source_files, output_file, rgb_threshold, z_pixels, scale, simplification, call_back):
        super(Photos2Points, self).__init__()

        self.source_files = source_files
        self.output_file = output_file
        self.rgb_threshold = rgb_threshold
        self.z_pixels = z_pixels
        self.scale = scale
        self.simplification = simplification
        self.call_back = call_back

        self._ply_template = '''ply
format ascii 1.0
comment object: %s
element vertex %s
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
'''

    def _in_threshold(self,pixel):
        return (pixel[0] >= self.rgb_threshold[0] and pixel[1] >= self.rgb_threshold[1] and pixel[2] >= self.rgb_threshold[2])

    def run(self):
        self.process()

    def process(self):
        vertexes = []
        good_verticies = -1
        z_pos = 0
        file_count = len(self.source_files)
        if file_count < 1:
            raise Exception("Folder is devoid of images, so sad :(")
        ran = 256 - self.rgb_threshold[2]
        mut = 256.0 / ( ran * 1.0 )

        for index, afile in enumerate(self.source_files):
            if self.call_back:
                self.call_back("Processing: %s of %s : %s" % (index+1,file_count,afile))
            image = Image.open(afile)
            width = image.size[0]
            
            for index, pixel in enumerate(image.getdata()):
                if self._in_threshold(pixel) == True:
                    good_verticies += 1
                    if good_verticies % self.simplification == 0:
                        x = (index % width) * self.scale
                        y = (index / width) * self.scale
                        z = z_pos * self.scale
                        r,g,b = pixel
                        b = int((b - self.rgb_threshold[2]) * mut)
                        vertexes.append((x,y,z,255,b,b))
            z_pos += self.z_pixels

        total_vertexes = len(vertexes)
        written_vertexes = 0
        print("Expected vertexes: %s" % total_vertexes)
        with open(self.output_file, 'w') as out_file:
            out_file.write(self._ply_template % (os.path.dirname(self.source_files[0]), total_vertexes ))
            for index, vertex in enumerate(vertexes):
                out_file.write("%s %s %s %s %s %s\n" % vertex)
                written_vertexes += 1
        if self.call_back:
            self.call_back("Complete, wrote %s vertexes" % written_vertexes)

class PhotoPointApi(object):
    def __init__(self):
        self.files_cache = []
        self.folder_cache = ''
        self.rgb_threshold = (255,255,255)
        self.image_types = ['jpg','jpeg']

    def _files(self,folder):
        if self.folder_cache != folder:
            print("Cache Miss")
            self.folder_cache = folder
            self.files_cache = sorted([ os.path.join(folder,f) for f in listdir(folder) if isfile(join(folder,f)) and self._isimage(f)])
        return self.files_cache

    def count_images_in_folder(self, folder):
        return len(self._files(folder))

    def _isimage(self,afile):
        return afile.lower().split('.')[-1] in self.image_types

    def _in_threshold(self,pixel, rgb_threshold):
        return (pixel[0] >= rgb_threshold[0] and pixel[1] >= rgb_threshold[1] and pixel[2] >= rgb_threshold[2])

    def _threshold_test(self, band, threshold, background):
            if (band >= threshold):
                return band
            else:
                return background

    def test_image(self, folder, size, rgb_threshold, image_no = None, background = 0, crop = 0,offset = (0,0)):
        images = self._files(folder)
        if image_no == None:
            image_to_use = len(images) / 2
        else:
            image_to_use = image_no - 1
        test_image_file = images[image_to_use]
        image = Image.open(test_image_file)

        x,y = image.size
        ydiff = int(float(y) * float(crop) / 100.0 / 2.0)
        xdiff = int(float(x) * float(crop) / 100.0 / 2.0)
        off_x = int(float(offset[0]) / 100.0 * float(x))
        off_y = int(float(offset[1]) / 100.0 * float(y))
        if abs(off_x) > xdiff:
            off_x = xdiff * (abs(off_x) / off_x)
        if abs(off_y) > ydiff:
            off_y = ydiff * (abs(off_y) / off_y)
        image = ImageChops.offset(image, off_x,off_y)
        image = image.crop((xdiff,ydiff,x - xdiff, y - ydiff))


        image.thumbnail(size)
        if rgb_threshold:
            R,G,B = image.split()
            mask1 = R.point(lambda i: self._threshold_test(i, rgb_threshold[0], background))
            mask2 = G.point(lambda i: self._threshold_test(i, rgb_threshold[1], background))
            mask3 = B.point(lambda i: self._threshold_test(i, rgb_threshold[2], background))

            image = Image.merge(image.mode,(mask1,mask2,mask3) )
        return (image, test_image_file)

    def process(self, source_folder, output_file, rgb_threshold, z_pixels, scale, simplification, call_back):
        files = self._files(source_folder)
        converter = Photos2Points(files, output_file, rgb_threshold, z_pixels, scale, simplification, call_back)
        converter.start()
        



