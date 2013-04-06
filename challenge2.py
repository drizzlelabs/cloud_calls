import time
import pyrax
import argparse

def main():

    pyrax.set_credential_file("./CredsFile")

    cs = pyrax.cloudservers
    servers = cs.servers.list()
    image_list = cs.images.list()

    srv_dict = {}


    print "Select a server from which an image will be created."
    for pos, srv in enumerate(servers):
        print "%s: %s" % (pos, srv.name)
        srv_dict[str(pos)] = srv.id
    selection = None
    while selection not in srv_dict:
        if selection is not None:
            print " -- Invalid choice"
        selection = raw_input("Enter the number for your choice: ")

    server_id = srv_dict[selection]
    print
    img_name = raw_input("Enter a name for the image: ")

    images = {}
    images[img_name] = cs.servers.create_image(server_id, img_name)
    
    completed_images = []
    while len(completed_images) < 1:    
        for img in cs.images.list():
            if str(img_name) in img.name and img.status == 'ACTIVE':
                completed_images.append(images[img_name])
        print "Waiting for image to be saved. Trying again in 30 seconds."
        time.sleep(30)

    print "\nImage is ready. Creating server."

    servers = {}
    servers[img_name] = cs.servers.create(img_name, images[img_name], 2)
    print "Building server: %s" % img_name
    
    print 
    
    completed_details = []
    while len(completed_details) < 1:
        for img_name in servers:
            servers[img_name].get()
            if len(servers[img_name].networks) > 0:
                completed_details.append(servers[img_name])        
        print "Waiting for details to be ready. Trying again in 30 seconds."
        time.sleep(30)
        
    for img_name in servers:
        servers[img_name].get()
        print "Name: %s" % servers[img_name].name
        print "ID: %s" % servers[img_name].id
        print "Status: %s" % servers[img_name].status
        print "Admin Password: %s" % servers[img_name].adminPass
        print "Networks: %s \n" % servers[img_name].networks

if __name__ == '__main__':
    main()
