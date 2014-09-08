import os
from os import listdir
from os.path import isfile, join
import PIL
from PIL import Image, ImageTk,ImageOps, ImageChops
import threading
import math
import time
import numpy as np
import cv2

class Photos2Points(threading.Thread):
    def __init__(self, source_files, output_file, rgb_threshold, z_pixels, scale, simplification, call_back, crop, offset):
        super(Photos2Points, self).__init__()

        self.source_files = source_files
        self.output_file = output_file
        self.rgb_threshold = rgb_threshold
        self.z_pixels = z_pixels
        self.scale = scale
        self.simplification = simplification
        self.call_back = call_back
        self.crop = crop
        self.offset = offset

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

    def crop_image(self,image,crop,offset):
        x_dim,y_dim = image.size

        ydiff = int(float(y_dim) * float(crop) / 100.0 / 2.0)
        xdiff = int(float(x_dim) * float(crop) / 100.0 / 2.0)

        off_x = int(float(offset[0]) / 100.0 * float(x_dim))
        off_y = int(float(offset[1]) / 100.0 * float(y_dim))
        if abs(off_x) > xdiff:
            off_x = xdiff * (abs(off_x) / off_x)
        if abs(off_y) > ydiff:
            off_y = ydiff * (abs(off_y) / off_y)
        image = ImageChops.offset(image, off_x,off_y)
        return image.crop((xdiff,ydiff,x_dim - xdiff, y_dim - ydiff))

    def process(self):
        vertexes = np.empty((0,6))
        good_verticies = -1
        z_pos = 0
        file_count = len(self.source_files)
        if file_count < 1:
            raise Exception("Folder is devoid of images, so sad :(")
        ran = 256 - self.rgb_threshold[2]
        mut = 256.0 / ( ran * 1.0 )

        for index, afile in enumerate(self.source_files):
            start = time.time()
            if self.call_back:
                self.call_back("Processing: %s of %s : %s" % (index+1,file_count,afile))
            image_file = Image.open(afile)
            image = self.crop_image(image_file,self.crop,self.offset)
            end = time.time()
            print('1Processing: %.4f' % (end - start))
            start = time.time()
            image_array = np.array(image)
            end = time.time()
            print('2Processing: %.4f' % (end - start))
            start = time.time()
            height,width,c = image_array.shape
            end = time.time()
            print('3Processing: %.4f' % (end - start))
            start = time.time()
            threshold_array =  np.ones((height,width,c)) * self.rgb_threshold
            end = time.time()
            print('4Processing: %.4f' % (end - start))
            start = time.time()
            result = image_array >= threshold_array
            end = time.time()
            print('5Processing: %.4f' % (end - start))
            start = time.time()
            result = np.sum(result, axis = 2)
            end = time.time()
            print('6Processing: %.4f' % (end - start))
            start = time.time()
            y,x = np.where(result)
            end = time.time()
            print('7Processing: %.4f' % (end - start))
            start = time.time()
            z = np.ones(y.shape[0]) * z_pos
            end = time.time()
            print('8Processing: %.4f' % (end - start))
            start = time.time()
            d_c = image_array[(y,x)]
            end = time.time()
            print('9Processing: %.4f' % (end - start))
            start = time.time()
            scaled_x = x * self.scale
            scaled_y = y * self.scale
            scaled_z = z * self.scale
            end = time.time()
            print('aProcessing: %.4f' % (end - start))
            start = time.time()
            points = np.rot90(np.vstack((scaled_x,scaled_y,scaled_z)))
            end = time.time()
            print('bProcessing: %.4f' % (end - start))
            start = time.time()
            coloured = np.hstack((points, d_c))
            end = time.time()
            print('cProcessing: %.4f' % (end - start))
            start = time.time()
            simplified = coloured[::self.simplification]
            end = time.time()
            print('dProcessing: %.4f' % (end - start))
            start = time.time()
            vertexes = np.vstack((vertexes,simplified))
            end = time.time()
            print('eProcessing: %.4f' % (end - start))
            start = time.time()
            z_pos += self.z_pixels
            end = time.time()
            print('fProcessing: %.4f' % (end - start))
            start = time.time()
            print('')

        total_vertexes = len(vertexes)
        written_vertexes = 0
        print("Expected vertexes: %s" % total_vertexes)
        with open(self.output_file, 'w') as out_file:
            out_file.write(self._ply_template % (os.path.dirname(self.source_files[0]), total_vertexes ))
            for index, vertex in enumerate(vertexes):
                out_file.write("%s %s %s %d %d %d\n" % tuple(vertex))
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

        x_dim,y_dim = image.size

        ydiff = int(float(y_dim) * float(crop) / 100.0 / 2.0)
        xdiff = int(float(x_dim) * float(crop) / 100.0 / 2.0)

        off_x = int(float(offset[0]) / 100.0 * float(x_dim))
        off_y = int(float(offset[1]) / 100.0 * float(y_dim))
        if abs(off_x) > xdiff:
            off_x = xdiff * (abs(off_x) / off_x)
        if abs(off_y) > ydiff:
            off_y = ydiff * (abs(off_y) / off_y)
        image = ImageChops.offset(image, off_x,off_y)
        image = image.crop((xdiff,ydiff,x_dim - xdiff, y_dim - ydiff))


        image.thumbnail(size)
        if rgb_threshold:
            R,G,B = image.split()
            mask1 = R.point(lambda i: self._threshold_test(i, rgb_threshold[0], background))
            mask2 = G.point(lambda i: self._threshold_test(i, rgb_threshold[1], background))
            mask3 = B.point(lambda i: self._threshold_test(i, rgb_threshold[2], background))

            image = Image.merge(image.mode,(mask1,mask2,mask3) )
        return (image, test_image_file)


    def process(self, source_folder, output_file, rgb_threshold, z_pixels, scale, simplification, call_back,crop,offset):
        files = self._files(source_folder)
        converter = Photos2Points(files, output_file, rgb_threshold, z_pixels, scale, simplification, call_back,crop,offset)
        converter.start()

    def process_video(self, source_folder, output_file, rgb_threshold, crop = 0, offset = (0,0), callback = None):
        video_size = (1920,1080)
        fourcc = cv2.cv.FOURCC(*'MJPG')
        out = cv2.VideoWriter(output_file,fourcc, 24.0, video_size)
        images = self.count_images_in_folder(source_folder)
        for i in range(0, self.count_images_in_folder(source_folder)):
            print('Processing image: %s of %s' %(i+1,images))
            image,filename = self.test_image(source_folder, video_size, rgb_threshold, i, 0, crop , offset)
            open_cv_image = np.array(image)[:, :, ::-1].copy() 
            out.write(open_cv_image)
        out.release()



