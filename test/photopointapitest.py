import unittest
import os
import sys
from PIL import Image, ImageTk
import shutil


sys.path.insert(0,os.path.join(os.path.dirname(__file__), '..','src'))

from photopointapi import PhotoPointApi

class PhotoPointApiTests(unittest.TestCase):
    def setUp(self):
        self.test_folder = os.path.join(os.path.dirname(__file__), 'test_data')
        self.simple_test_folder = os.path.join(os.path.dirname(__file__), 'test_data_simple')
        self.output_folder = os.path.join(os.path.dirname(__file__), 'test_output')
        try:
            os.stat(self.output_folder)
            shutil.rmtree(self.output_folder)
        except:
            pass
        os.mkdir(self.output_folder)
        self.output_file = os.path.join(self.output_folder, 'output.ply')
        
    
    def test_count_images_in_folder_returns_correct_jpg_count(self):
        expected = 5

        ppa = PhotoPointApi()
        actual = ppa.count_images_in_folder(self.test_folder)

        self.assertEquals(expected,actual)

    def test_count_only_images_in_folder_returns_correct_count(self):
        test_folder = os.path.dirname(__file__)
        expected = 0

        ppa = PhotoPointApi()
        actual = ppa.count_images_in_folder(test_folder)

        self.assertEquals(expected,actual)

    def test_test_image_should_return_a_scaled_image_when_given_folder_with_images(self):
        expected_size = 128,72
        ppa = PhotoPointApi()
        (actual, filename) = ppa.test_image(self.test_folder,expected_size, None)

        self.assertEquals(expected_size[0],actual.size[0])
        self.assertEquals(expected_size[1],actual.size[1])

    def test_test_image_should_return_a_altered_image_when_given_threshold(self):
        expected_size = 128,72
        ppa = PhotoPointApi()
        threshold = 255,255,255
        (actual, filename) = ppa.test_image(self.test_folder,expected_size, threshold)
        for pixel in actual.getdata():
            self.assertEquals((217,217,217), pixel)

    def test_test_image_should_use_middle_image(self):
        expected = os.path.join(self.test_folder, 'DSC_6751.JPG')
        expected_size = 128,72
        ppa = PhotoPointApi()
        (actual, filename) = ppa.test_image(self.test_folder,expected_size, None)
        self.assertEquals(expected , filename)

    def test_test_image_should_use_specifed_image(self):
        expected = os.path.join(self.test_folder, 'DSC_6752.JPG')
        expected_size = 128,72
        ppa = PhotoPointApi()
        (actual, filename) = ppa.test_image(self.test_folder,expected_size, None, 4)
        self.assertEquals(expected , filename)

    def test_process_should_fail_if_folder_empty(self):
        test_source = os.path.dirname(__file__)
        test_threshold = (255,255,255)
        test_z_pixels = 1
        ppa = PhotoPointApi()
        with self.assertRaises(Exception):
            ppa.process(test_source,self.output_file,test_threshold, test_z_pixels, 1, 1, None)
        
    def test_process_should_create_specified_ply_file(self):
        test_threshold = (255,255,255)
        test_z_pixels = 1
        ppa = PhotoPointApi()
        self.assertFalse(os.path.isfile(self.output_file))
        ppa.set_options(self.simple_test_folder,self.output_file,test_threshold, test_z_pixels, 1, 1, None)
        ppa.start()
        ppa.join()
        self.assertTrue(os.path.isfile(self.output_file))

    def test_process_should_create_specified_ply_file_and_add_headers(self):
        test_threshold = (255,255,255)
        test_z_pixels = 1
        ppa = PhotoPointApi()
        ppa.set_options(self.simple_test_folder,self.output_file,test_threshold, test_z_pixels, 1, 1, None)
        ppa.start()
        ppa.join()
        expected_headers ='''ply
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
''' % (self.simple_test_folder, 3)
        with open(self.output_file, 'r') as actual:
            data = actual.read()
            self.assertTrue(data.startswith(expected_headers),data )

    def test_process_should_add_points_above_threshold(self):
        test_threshold = (255,255,255)
        test_z_pixels = 1
        ppa = PhotoPointApi()
        ppa.set_options(self.simple_test_folder,self.output_file,test_threshold, test_z_pixels, 1, 1, None)
        ppa.start()
        ppa.join()
        expected_points ='''46 52 0 255 0 0\n46 52 1 255 0 0\n46 52 2 255 0 0\n'''
        with open(self.output_file, 'r') as actual:
            data = actual.read()
            self.assertTrue(data.endswith(expected_points),"Expected: [%s] but was [%s]" % (expected_points, data) )

    def test_process_should_add_points_above_threshold_with_correct_z(self):
        test_threshold = (255,255,255)
        test_z_pixels = 2
        ppa = PhotoPointApi()
        ppa.set_options(self.simple_test_folder,self.output_file,test_threshold, test_z_pixels, 1, 1, None)
        ppa.start()
        ppa.join()
        expected_points ='''46 52 0 255 0 0\n46 52 2 255 0 0\n46 52 4 255 0 0\n'''
        with open(self.output_file, 'r') as actual:
            data = actual.read()
            self.assertTrue(data.endswith(expected_points),"Expected: [%s] but was [%s]" % (expected_points, data) )

    def test_process_should_scale_points(self):
        test_threshold = (255,255,255)
        test_z_pixels = 1
        scale = 10
        ppa = PhotoPointApi()
        ppa.set_options(self.simple_test_folder,self.output_file,test_threshold, test_z_pixels, scale, 1, None)
        ppa.start()
        ppa.join()
        expected_points ='''460 520 0 255 0 0\n460 520 10 255 0 0\n460 520 20 255 0 0\n'''
        with open(self.output_file, 'r') as actual:
            data = actual.read()
            self.assertTrue(data.endswith(expected_points),"Expected: [%s] but was [%s]" % (expected_points, data) )

    def test_process_should_simplify_points(self):
        test_threshold = (255,255,255)
        test_z_pixels = 1
        ppa = PhotoPointApi()
        ppa.set_options(self.simple_test_folder,self.output_file,test_threshold, test_z_pixels, 1, 2, None)
        ppa.start()
        ppa.join()
        expected_points ='''46 52 0 255 0 0\n46 52 2 255 0 0\n'''
        with open(self.output_file, 'r') as actual:
            data = actual.read()
            self.assertTrue(data.endswith(expected_points),"Expected: [%s] but was [%s]" % (expected_points, data) )
            self.assertTrue("element vertex 2\n" in data, data)


if __name__ == '__main__':
    unittest.main()