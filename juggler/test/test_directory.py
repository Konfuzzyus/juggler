'''
Created on 09.12.2013

@author: Konfuzzyus
'''
import unittest
import os
import tempfile
from juggler import listing

class TestListing(unittest.TestCase):
    
    def setUp(self):
        handle, filename = tempfile.mkstemp()
        os.close(handle)
        self.__tempfilename = filename

    def tearDown(self):
        os.remove(self.__tempfilename)

    def test_AfterInit_ListingIsEmpty(self):
        directory = listing.Listing()
        self.assertTrue(directory.is_empty())

    def test_LoadMissingFile_RaisesFileNotFound(self):
        self.assertRaises(listing.FileNotFound, listing.load_listing_file, 'RandomNonExistentFile')

    def test_LoadDirectory_RaisesFileNotFound(self):
        self.assertRaises(listing.FileNotFound, listing.load_listing_file, '..')

    def test_LoadEmptyFile_RaisesInvalidFile(self):
        self.assertRaises(listing.InvalidFile, listing.load_listing_file, self.__tempfilename)

    def test_LoadUnknownXMLFile_CreatesEmptyListing(self):
        test_listing = self.simulate_xml_load('<Thingy> <Something/> </Thingy>')
        self.assertTrue(test_listing.is_empty())

    def test_LoadEmptyListing_CreatesEmptyListing(self):
        test_listing = self.simulate_xml_load('<Listing/>')
        self.assertTrue(test_listing.is_empty())
    
    def test_RequestNonExistentPackage_GetNone(self):
        test_listing = listing.Listing()
        self.assertEqual(test_listing.get_package('SomePackage'), None)
    
    def test_LoadSinglePacketData_CreatesNonEmptyListing(self):
        test_listing = self.simulate_xml_load('<Listing> <Package name="SomePackage"> <Build version="v1.0.0"/> </Package> </Listing>')
        self.assertFalse(test_listing.is_empty())
        self.assertNotEqual(test_listing.get_package('SomePackage'), None)

    def simulate_xml_load(self, xml_data):
        with open(self.__tempfilename, 'w') as xmlfile:
            xmlfile.write(xml_data)
        test_listing = listing.load_listing_file(self.__tempfilename)
        return test_listing