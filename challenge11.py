#!/usr/bin/python

import os
import time
import pyrax
import argparse
import re

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-d', '--fqdn', default= 'rackerchallenge11.com', help='FQDN of Load Balancer')
    parser.add_argument ('-i', '--image', default='5cebb13a-f783-4f8c-8058-c4182c724ccd', help='Image ID to build server with. Default is Ubuntu 12.04')
    parser.add_argument ('-f', '--flavor', type=int, default=2, help='Flavor ID to build server with' )
    parser.add_argument ('-r', '--region', default='DFW', help='Datacenter/Region to build servers in', choices=['DFW', 'ORD', 'LON'])
    parser.add_argument ('-e', '--email', default="test@challenge11.com", help='Email Address of DNS Record')

    args = parser.parse_args()

    pyrax.set_credential_file("/Users/drizzle/Desktop/corpcreds")
    cs = pyrax.cloudservers
    clb = pyrax.cloud_loadbalancers
    dns = pyrax.cloud_dns
    cbs = pyrax.cloud_blockstorage

    content = """from="trusted.eng.cam.ac.uk",no-port-forwarding,no-pty ssh-rsa AAAAB
    3NzaC1yc2EAAAABIwAAAQEAybmcqaU/Xos/GhYCzkV+kDsK8+A5OjaK5WgLMqmu38aPo
    56Od10RQ3EiB42DjRVY8trXS1NH4jbURQPERr2LHCCYq6tHJYfJNhUX/COwHs+ozNPE8
    3CYDhK4AhabahnltFE5ZbefwXW4FoKOO+n8AdDfSXOazpPas8jXi5bEwNf7heZT++a/Q
    xbu9JHF1huThuDuxOtIWl07G+tKqzggFVknM5CoJCFxaik91lNGgu2OTKfY94c/ieETO
    XE5L+fVrbtOh7DTFMjIYAWNxy4tlMR/59UVw5dapAxH9J2lZglkj0w0LwFI+7hZu9XvN
    fMKMKg+ERAz9XHYH3608RL1RQ== This comment describes key #1"""

    ssh_key = {"/root/.ssh/authorized_keys": content}

    server1 = cs.servers.create("server1", args.image, args.flavor, files=ssh_key)
    s1_id = server1.id
    server2 = cs.servers.create("server2", args.image, args.flavor, files=ssh_key)
    s2_id = server2.id
    server3 = cs.servers.create("server3", args.image, args.flavor, files=ssh_key)
    s3_id = server3.id    

    print "Building servers."
    
    while not (server1.networks and server2.networks and server3.networks):
        print "Waiting for networks to be provisioned."
        time.sleep(15)
        server1 = cs.servers.get(s1_id)
        server2 = cs.servers.get(s2_id)
        server3 = cs.servers.get(s3_id)        

    print "Networks are ready."

    server1_ip = server1.networks["private"][0]
    server2_ip = server2.networks["private"][0]
    server3_ip = server3.networks["private"][0]    

    # Use the IPs to create the nodes
    node1 = clb.Node(address=server1_ip, port=80, condition="ENABLED")
    node2 = clb.Node(address=server2_ip, port=80, condition="ENABLED")
    node3 = clb.Node(address=server3_ip, port=80, condition="ENABLED")    

    # Create the Virtual IP
    print "Creating load balancer."
    vip = clb.VirtualIP(type="PUBLIC")
 
    # Create Load Balancer
    lb = clb.create(args.fqdn, port=80, protocol="HTTP", nodes=[node1, node2, node3], virtual_ips=[vip])

    print "Created Load Balancer: %s" % [(lb.name, lb.id) for lb in clb.list()]

    lb = clb.get(lb.id)
    lb_virt_ips = ""
    lb_virt_ips = str(lb.virtual_ips)
            
    vip_ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', lb_virt_ips)
    print "IP of Load Balancer: %s" % (vip_ip[0])
                  
    dom = dns.create(name=args.fqdn, emailAddress=args.email)
            
    recs = [{
            "type": "A",
            "name": args.fqdn,
            "data": vip_ip[0],
            "ttl": 6000,
            }]
                    
    print "Added Domain Record: %s" % (dom.add_records(recs))
    
    lb_status = lb.status
    while lb_status != 'ACTIVE':
        print "Waiting for load balancer build to complete."
        time.sleep(15)
        lb = clb.get(lb.id)
        lb_status = lb.status
    
    print "Load Balancer ready."
    
    cert = "-----BEGIN CERTIFICATE-----MIIDEzCCAfugAwIBAgIJAOAIcn7VKEHkMA0GCSqGSIb3DQEBBQUAMCAxHjAcBgNVBAMMFXJhY2tlcmNoYWxsZW5nZTExLmNvbTAeFw0xMzA0MjkwMzU2MDRaFw0yMzA0MjcwMzU2MDRaMCAxHjAcBgNVBAMMFXJhY2tlcmNoYWxsZW5nZTExLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMx3+FWd4C9ta/xQahgo1YWYDdGoO0xstGb8VgxsrckQnG4DRPXcrVGITMW9hLEs7hIwWcB2htpKgPcO9/WT3IiOi+855weF6vuq2a3khItThCRe5JnKkHYW4R1+kV8y7xM31nr2fivYvyobMFyMaibiiwmpXvYPTPe2Oo5krkcL80rvNFFRIir8JGnSgSlO0ivq8ZDZIhqXjQ/LEQHIGehOdpo4jC3EazSmKT/6+Zs+TEwZJvDvLNrOXljvB3ry5bq2IuLI2JBNv0A2D2ytIYQqfpIwVxV9hi6HqOLoxYOiVTvsY4Xf+CSQ06NEVCj14et6HpVFHtYolcoK6uadSW8CAwEAAaNQME4wHQYDVR0OBBYEFMuHzwc21wG0sNOJWngQfTwmNVQ6MB8GA1UdIwQYMBaAFMuHzwc21wG0sNOJWngQfTwmNVQ6MAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADggEBALC94E2M/nNq7LIFfONvnz1AE1vNP+jgfj+rTG0t4kiiMvMDs7jMB9G7MZC6SBkh2t9GjPIVwjhsr/616Ztfo+Id0D/+lk0HtODyOJh1PBO3YE4dYaQ/37Jt1FBbACau0XAzmOIXnQaIAbet+glcX4gzXrK8VHKJgq/RmxllkZ2y4rhwFH7S30LT9h3dnYzI0dBebMKQoQQiP+SLyuo2QlXbQ3a7g/M2MYNjvB9RaIiZbNTHq2IdxmhzTg/z4OXp/QU5ifnlwDSgWHTW7b0JP5sHULVQLx/cQ49quLvo9i4fZUWdv9qov8NPUF45Xp3NJOEjUFiecATe9mxyHfswJeI=-----END CERTIFICATE-----"
    pkey = "-----BEGIN RSA PRIVATE KEY-----MIIEowIBAAKCAQEAzHf4VZ3gL21r/FBqGCjVhZgN0ag7TGy0ZvxWDGytyRCcbgNE9dytUYhMxb2EsSzuEjBZwHaG2kqA9w739ZPciI6L7znnB4Xq+6rZreSEi1OEJF7kmcqQdhbhHX6RXzLvEzfWevZ+K9i/KhswXIxqJuKLCale9g9M97Y6jmSuRwvzSu80UVEiKvwkadKBKU7SK+rxkNkiGpeND8sRAcgZ6E52mjiMLcRrNKYpP/r5mz5MTBkm8O8s2s5eWO8HevLlurYi4sjYkE2/QDYPbK0hhCp+kjBXFX2GLoeo4ujFg6JVO+xjhd/4JJDTo0RUKPXh63oelUUe1iiVygrq5p1JbwIDAQABAoIBAE4PTyOAjmIM6Dj/ikGG9V13W287Rsg6h/T5SPCdXQtx6AaoAN/MS+7glk63t7zcZldTVjCAD6Ou5eVsNYXv2TXZFdtSw7y/h6Jk643TvDZkwAISqDt+dgBfY7oa4+zwSQ2RN7Th/fFHYlP05VWv1abavjIGE1blKIE5dMl/7nj4jD3xL7WnYnmpBpc2P3ttfcM2yFY/xeqFbXa9cH4ZJwf2WdDoPduYrp4ZYKhInwQ6/PqDhEofIa1vyokQHo1HFFVmBd50hMMIEX7Rac6mHaMfy+OyxrC6CkVN05gNAQEr1pNgRvHvpTSs25HvdfhiHUUR4RejBV7xICL2BAVLCKECgYEA6riiWTtTBGrVQv/pzJBbQMHjkX/8aw+pLT1/j0FvexdllK3nGdb5O78xPr2YmxbROWg9ZFNHnbVZkfmXHAF/o/sXfO2JaTO1qFyJZmGB4B67uGHBlKHpgovu6aJYzC94QFNBPTwy4pFKhyQTz/vyqcuUqaJc7owHe9jeygEIW50CgYEA3wE9SVsWTYr+Es97XHbEaFtfC8k9A+FwCDHKGkq+zd75exScRjiatHGmiFlHu5PA1uqQwLdnWKqT3MaI6eemkCkGM6Sts3ghMLnRKTonfLpiDk7lbJdXVE86Erl/D2hARE+HzjsJ4AoGPsHzqI/PY28ZaY45iq2EHSIuY9HnyXsCgYAtszUo2nwXaBWNrfX/djvOJ/H+6kRjM/FkdYzYf40NEkkc4Z8VUN3F3DviU1fbGl4yJzGMzwoqkpyV51qcgU4wxzqTgEw4x3CfDyVRYbq/wDwcciwWnE+yszwZERro5nUrUQpqucXOhytTlJqm7A8bMCAJxysA5xKt8lOuUPUnoQKBgBBr7PFr7baEF7WW5cSnUktE/zjE9uNERJW15OYOvwI1+zUfDWr2XB4RiGvd9zRO6xJob4RhfRDAbucBD6/5yQAwpS5EYC4pGHiYFljs2V+L8hCPqsFWW63vr50VX8/oo2LkYGHFYzLGSjNw4Np2zJTL55koSgB2SpZCoBvlpyXlAoGBAIpSSWBAIYu4EU/hagvcjHDHAjXmdpEaUmjKbRSvA2Oeh4i/bj2GIpfoDWBWSRGdeEZgy5978Fpe9pKhfKug+6Z2HJdmYaeNJ6UZdvSzaqfdy0NqCYzoF/5kksnm+Wy1+bHlduw2Jm/IqCWiesjOP55Bx2XLEWRJ4Qfj1N5f9bKc-----END RSA PRIVATE KEY-----"
    
    lb.add_ssl_termination(securePort=443, secureTrafficOnly=False,
                certificate=cert, privatekey=pkey)
                
    print "Load Balancer SSL Termination Active"
    
    server1vol = cbs.create(name="server1-vol", size=100, volume_type="SATA")
    server2vol = cbs.create(name="server1-vol", size=100, volume_type="SATA")
    server3vol = cbs.create(name="server1-vol", size=100, volume_type="SATA")
    
    pyrax.utils.wait_until(server1, "status", "ACTIVE", attempts=0, verbose=True)
    pyrax.utils.wait_until(server2, "status", "ACTIVE", attempts=0, verbose=True)
    pyrax.utils.wait_until(server3, "status", "ACTIVE", attempts=0, verbose=True)    
    
    server1vol.attach_to_instance(server1, mountpoint="/dev/xvdd")
    pyrax.utils.wait_until(server1vol, "status", "in-use", interval=3, attempts=0,
            verbose=True)
    
    print "Volume attached to server 1"
    
    server2vol.attach_to_instance(server2, mountpoint="/dev/xvdd")
    pyrax.utils.wait_until(server2vol, "status", "in-use", interval=3, attempts=0,
            verbose=True)
    
    print "Volume attached to server 2"
    
    server3vol.attach_to_instance(server3, mountpoint="/dev/xvdd")
    pyrax.utils.wait_until(server3vol, "status", "in-use", interval=3, attempts=0,
            verbose=True)
    
    print "Volume attached to server 3"
    
    snum = 1
    while snum < 4:
        s_name = str(server) + str(snum)
        s_id = str(s) + str(snum) + str(_id)
        s_name = cs.servers.get(s_id)
        print "### Server " + s_name.name + " details ###"
        print "Name:", s_name.name
        print "Status:", s_name.status
        print "Admin Password:", s_name.adminPass
        print "Networks:", s_name.networks
        print                      
        snum += 1
if __name__ == '__main__':
    main()
   

        
