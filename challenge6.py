#!/usr/bin/python

import os
import time
import pyrax
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-c', '--container', help='Name of container to be created.', required=True)
    
    args = parser.parse_args()

    pyrax.set_credential_file("/Users/drizzle/Desktop/corpcreds")
    cf = pyrax.cloudfiles

    cont = cf.create_container(args.container)
    print "Creating container named: %s" % (cont.name)
    cf.make_container_public(args.container, ttl=900)
    print "CDN Enabled."
    
if __name__ == '__main__':
    main()
