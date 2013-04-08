#!/usr/bin/python

import os
import time
import pyrax
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-d', '--fqdn', help='FQDN of record to add', required=True)
    parser.add_argument ('-i', '--image', default='5cebb13a-f783-4f8c-8058-c4182c724ccd', help='Image ID to build server with. Default is Ubuntu 12.04')
    parser.add_argument ('-f', '--flavor', type=int, default=2, help='Flavor ID to build server with' )
    parser.add_argument ('-r', '--region', default='DFW', help='Datacenter/Region to build servers in', choices=['DFW', 'ORD', 'LON'])
    parser.add_argument ('-e', '--email', default="test@challenge9.com", help='Email Address of DNS Record')

    args = parser.parse_args()

    pyrax.set_credential_file(".PathtoCreds")
    cs = pyrax.cloudservers
    dns = pyrax.cloud_dns

    server1 = cs.servers.create(args.fqdn, args.image, args.flavor)
    s1_id = server1.id

    print "Building server: %s" % (args.fqdn)
    
    while not (server1.networks):
        print "Waiting for networks to be provisioned."
        time.sleep(15)
        server1 = cs.servers.get(s1_id)

    print "Networks are ready."

    server1_ip = server1.networks["public"][1]
    print server1_ip
    
    dom = dns.create(name=args.fqdn, emailAddress=args.email)
            
    recs = [{
            "type": "A",
            "name": args.fqdn,
            "data": server1_ip,
            "ttl": 6000,
            }]
                    
    print dom.add_records(recs)
    
if __name__ == '__main__':
    main()
