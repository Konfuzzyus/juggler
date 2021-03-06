"""
    Juggler - Dirty dependency management and packaging for compiled code
    Copyright (C) 2014  Christian Meyer

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import urllib
from juggler import version
from xml.etree import ElementTree
from semantic_version import Version, Spec

class FileNotFound(Exception):
    pass

class InvalidFile(Exception):
    pass

class InvalidRepository(Exception):
    pass

class PackageInfo():
    def __init__(self, name, root, flavor):
        self.builds = []
        self.__name = name
        self.__root = root
        self.__flavor = flavor
    
    def add_build(self, build_version):
        assert isinstance(build_version, Version)
        if not build_version in self.builds:
            self.builds.append(build_version)
        return PackageEntry(self.__name, self.__root, build_version, self.get_flavor())
    
    def get_entry(self, spec, ignore_local_build):
        best_match = None
        for build in self.builds:
            if ignore_local_build and build.prerelease == (u'local',):
                continue
            if spec.match(build):
                if build > best_match or best_match == None:
                    best_match = build
        if best_match is None:
            return None
        return PackageEntry(self.__name, self.__root, best_match, self.get_flavor())
        
    def get_name(self):
        return self.__name

    def get_flavor(self):
        return self.__flavor

class PackageEntry():
    def __init__(self, name, root, build_version, flavor):
        self.__name = name
        self.__version = build_version
        self.__root = root
        self.__flavor = flavor

    def get_name(self):
        return self.__name
    
    def get_version(self):
        return self.__version
    
    def get_path(self):
        return self.__root
    
    def get_flavor(self):
        return self.__flavor

    def get_filename(self):
        return '%s_%s-%s.tar.gz' % (self.__name, self.__flavor, str(self.__version))

class Listing():
    def __init__(self, root='.'):
        self.__packages = {}
        self.__root = root
    
    def is_empty(self):
        return len(self.__packages) == 0
    
    def add_package(self, name, version_string, flavor='vanilla'):
        key = '%s@%s' % (name, flavor)
        if not key in self.__packages:
            self.__packages[key] = PackageInfo(name, self.__root, flavor)
        return self.__packages[key].add_build(version.parse_version(version_string))
    
    def get_package(self, name, spec=version.parse_spec('*'), ignore_local_build=False, flavor='vanilla'):
        assert isinstance(spec, Spec)
        key = '%s@%s' % (name, flavor)
        if key in self.__packages:
            return self.__packages[key].get_entry(spec, ignore_local_build=ignore_local_build)
        else:
            return None
    
    def get_root(self):
        return self.__root
    
    def store(self, path):
        root = ElementTree.Element('Listing')
        for key in self.__packages:
            pack = ElementTree.SubElement(root, 'Package', {'name': self.__packages[key].get_name(), 'flavor': self.__packages[key].get_flavor()})
            for build in self.__packages[key].builds:
                ElementTree.SubElement(pack, 'Build', {'version': str(build)})
        tree = ElementTree.ElementTree(root)
        tree.write(os.path.join(path, get_listing_filename()), encoding="utf-8")

def get_listing_filename():
    return 'juggler_listing.xml'

def create_empty_listing(path):
    listing_path = os.path.join(path, get_listing_filename())
    with open(listing_path, 'w') as listing_file:
        listing_file.write('<Listing/>')

def load_remote_listing(url):
    remotename = '/'.join([url, get_listing_filename()])
    remotefile = None
    try:
        remotefile = urllib.urlopen(remotename)
    except IOError as error:
        raise FileNotFound('%s could not be accessed: %s' % (remotename, error))
    return load_listing(remotefile, url)

def load_local_listing(path):
    if path is None:
        return

    filename = os.path.join(path, get_listing_filename())
    if not os.path.isfile(filename):
        raise FileNotFound('%s is a directory or missing' % filename)
    
    return load_listing(filename, path)

def load_listing(source, root):
    xmltree = None
    try:
        xmltree = ElementTree.parse(source)
    except ElementTree.ParseError as error:
        raise InvalidFile('parsing error in %s: %s' % (source, error))

    listing = Listing(root)
    package_entries = xmltree.findall('./Package')
    for entry in package_entries:
        for build in entry.findall('./Build'):
            if 'flavor' in entry.attrib:
                listing.add_package(entry.attrib['name'], build.attrib['version'], entry.attrib['flavor'])
            else:
                listing.add_package(entry.attrib['name'], build.attrib['version'])
    return listing

def prepare_local_repository(target_repository):
    if (not os.path.exists(target_repository)):
        os.makedirs(target_repository)
    elif (not os.path.isdir(target_repository)):
        raise InvalidRepository('I can not prepare your local repository %s, the destination is not a directory.' % target_repository)
    elif (not os.path.exists(os.path.join(target_repository, get_listing_filename()))):
        create_empty_listing(target_repository)
