#!/usr/bin/python

import os
import pyrax
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-f', '--fqdn', help='FQDN of record to add', required=True)
    parser.add_argument ('-i', '--ip', help='IP Address of FQDN record', required=True)
    parser.add_argument ('-e', '--email', help='IP Address of FQDN record', required=True)


    args = parser.parse_args()

    pyrax.set_credential_file("./PathtoCreds")
    dns = pyrax.cloud_dns
        
    dom = dns.create(name=args.fqdn, emailAddress=args.email)
    
    recs = [{
            "type": "A",
            "name": args.fqdn,
            "data": args.ip,
            "ttl": 6000,
            }]
            
    print dom.add_records(recs)


if __name__ == '__main__':
    main()
