#!/usr/bin/python

import os
import time
import pyrax
import argparse
import re

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-d', '--fqdn', help='FQDN of Load Balancer', required=True)
    parser.add_argument ('-i', '--image', default='5cebb13a-f783-4f8c-8058-c4182c724ccd', help='Image ID to build server with. Default is Ubuntu 12.04')
    parser.add_argument ('-f', '--flavor', type=int, default=2, help='Flavor ID to build server with' )
    parser.add_argument ('-r', '--region', default='DFW', help='Datacenter/Region to build servers in', choices=['DFW', 'ORD', 'LON'])
    parser.add_argument ('-e', '--email', default="test@challenge9.com", help='Email Address of DNS Record')
    parser.add_argument ('-c', '--container', help='Name of container to be created.', required=True)

    args = parser.parse_args()

    pyrax.set_credential_file(".PathtoCreds")
    cs = pyrax.cloudservers
    clb = pyrax.cloud_loadbalancers
    dns = pyrax.cloud_dns
    cf = pyrax.cloudfiles

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

    print "Building servers."
    
    while not (server1.networks and server2.networks):
        print "Waiting for networks to be provisioned."
        time.sleep(15)
        server1 = cs.servers.get(s1_id)
        server2 = cs.servers.get(s2_id)

    print "Networks are ready."

    server1_ip = server1.networks["private"][0]
    server2_ip = server2.networks["private"][0]

    # Use the IPs to create the nodes
    node1 = clb.Node(address=server1_ip, port=80, condition="ENABLED")
    node2 = clb.Node(address=server2_ip, port=80, condition="ENABLED")

    # Create the Virtual IP
    print "Creating load balancer."
    vip = clb.VirtualIP(type="PUBLIC")
 
    # Create Load Balancer
    lb = clb.create(args.fqdn, port=80, protocol="HTTP", nodes=[node1, node2], virtual_ips=[vip])

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
    
    # Adding Load Balancer Health Monitor
    lb.add_health_monitor(type="CONNECT", delay=10, timeout=10, attemptsBeforeDeactivation=3)
    
    # Create content for error page
    lb_error_page = "Oops, we have a problem!"

    time.sleep(15)
    # Changing Load Balancer Error Page
    lb.manager.set_error_page(lb, lb_error_page)
    
    # Creating Cloud Files Container
    cont = cf.create_container(args.container)
    print "Creating container named: %s" % (cont.name)
    
    # Enabling CDN on the Container
    cf.make_container_public(args.container, ttl=900)
    print "CDN Enabled."
    
    # Storing the Error Page in Cloud Files
    obj = cf.store_object(cont.name, "error.html", lb_error_page, content_type="text/html")
    print "Stored Object: %s" % (obj)
    print "CDN URI: %s" % (cont.cdn_uri)
    
if __name__ == '__main__':
    main()
   

        
