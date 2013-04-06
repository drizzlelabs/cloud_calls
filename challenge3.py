#!/usr/bin/python

import os
import time

import pyrax
import pyrax.exceptions as exc
import pyrax.utils as util
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-d', '--directory', help='Directory containing files to be uploaded', required=True)
    parser.add_argument ('-c', '--container', help='Destination container.', required=True)
    
    args = parser.parse_args()

    pyrax.set_credential_file("./PathtoCreds")
    cf = pyrax.cloudfiles

    folder = args.directory

    print "Uploading folder: %s" % (folder)
    upload_key, total_bytes = cf.upload_folder(folder, container=args.container)
    print "Total bytes to upload: %s" % (total_bytes)
    uploaded = 0
    while uploaded < total_bytes:
        uploaded = cf.get_uploaded(upload_key)
        print "Progress: %4.2f%%" % ((uploaded * 100.0) / total_bytes)
        time.sleep(1)

if __name__ == '__main__':
    main()
    
    
    
