import time
import pyrax
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument ('base', help="Base hostname to use for servers")
    parser.add_argument ('-c', '--count', type=int, default=3, help="Number of servers to build. Default is 3.")
    parser.add_argument ('-i', '--image', default='5cebb13a-f783-4f8c-8058-c4182c724ccd', help='Image ID to build server with. Default is Ubuntu 12.04')
    parser.add_argument ('-f', '--flavor', type=int, default=2, help='Flavor ID to build server with' )
    parser.add_argument ('-r', '--region', default='DFW', help='Datacenter/Region to build servers in', choices=['DFW', 'ORD', 'LON'])
    
    pyrax.set_credential_file("/Users/drizzle/Desktop/corpcreds")
    cs = pyrax.cloudservers
    
    args = parser.parse_args()
    
    servers = {}
    for i in xrange(0, args.count):
        name =  '%s%d' % (args.base, i)
        server_data = {
            "server": {
                "flavorRef": args.flavor,
                "imageRef": args.image,
                "name": name
            }
        }
        servers[name] = cs.servers.create(name, args.image, args.flavor)
        print "Building server: %s" % name
    
    print 
    
    completed_details = []
    while len(completed_details) < args.count:
        for name in servers:
            servers[name].get()
            if len(servers[name].networks) > 0:
                completed_details.append(servers[name])        
        print "Waiting for details to be ready. Trying again in 30 seconds."
        time.sleep(30)
        
    for name in servers:
        servers[name].get()
        print "Name: %s" % servers[name].name
        print "ID: %s" % servers[name].id
        print "Status: %s" % servers[name].status
        print "Admin Password: %s" % servers[name].adminPass
        print "Networks: %s \n" % servers[name].networks

if __name__ == '__main__':
    main()
