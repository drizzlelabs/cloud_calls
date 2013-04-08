#!/usr/bin/python

import os
import time
import pyrax
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-c', '--container', help='Name of container to be created.', required=True)
    parser.add_argument ('-f', '--fqdn', help='FQDN of record to add', required=True)
    parser.add_argument ('-i', '--ip', help='IP Address of FQDN record')
    parser.add_argument ('-e', '--email', help='IP Address of FQDN record', required=True)
    
    args = parser.parse_args()

    pyrax.set_credential_file(".PathtoCreds")
    cf = pyrax.cloudfiles
    dns = pyrax.cloud_dns

    cont = cf.create_container(args.container)
    print "Creating container named: %s" % (cont.name)
    cf.make_container_public(args.container, ttl=900)
    print "CDN Enabled."
    
    content = "Hello World"
    obj = cf.store_object(cont.name, "index.html", content, content_type="text/html")
    print "Stored Object: %s" % (obj)
    print "CDN URI: %s" % (cont.cdn_uri)
    
    dom = dns.create(name=args.fqdn, emailAddress=args.email)
            
    recs = [{
            "type": "CNAME",
            "name": "test." + str(args.fqdn),
            "data": cont.cdn_uri,
            "ttl": 6000,
            }]
                    
    print dom.add_records(recs)
    
if __name__ == '__main__':
    main()
