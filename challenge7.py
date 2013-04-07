import time
import pyrax
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-i', '--image', default='5cebb13a-f783-4f8c-8058-c4182c724ccd', help='Image ID to build server with. Default is Ubuntu 12.04')
    parser.add_argument ('-f', '--flavor', type=int, default=2, help='Flavor ID to build server with. Default flavor is 512MB' )
    parser.add_argument ('-p', '--port', type=int, default=80, help='Port the nodes and load balancer should be configured for')

    args = parser.parse_args()
    
    pyrax.set_credential_file(".PathtoCreds")
    cs = pyrax.cloudservers
    clb = pyrax.cloud_loadbalancers

              
    server1 = cs.servers.create("server1", args.image, args.flavor)
    s1_id = server1.id
    server2 = cs.servers.create("server2", args.image, args.flavor)
    s2_id = server2.id

    print "Building servers."
    
    # The servers won't have their networks assigned immediately, so
    # wait until they do.
    while not (server1.networks and server2.networks):
        print "Waiting for networks to be provisioned."
        time.sleep(15)
        server1 = cs.servers.get(s1_id)
        server2 = cs.servers.get(s2_id)
        
    # Get the private network IPs for the servers
    server1_ip = server1.networks["private"][0]
    server2_ip = server2.networks["private"][0]

    # Use the IPs to create the nodes
    node1 = clb.Node(address=server1_ip, port=args.port, condition="ENABLED")
    node2 = clb.Node(address=server2_ip, port=args.port, condition="ENABLED")
    
    # Create the Virtual IP
    vip = clb.VirtualIP(type="PUBLIC")
    
    lb = clb.create("example_lb", port=args.port, protocol="HTTP",
            nodes=[node1, node2], virtual_ips=[vip])
            
    print [(lb.name, lb.id) for lb in clb.list()]
    

if __name__ == '__main__':
    main()
