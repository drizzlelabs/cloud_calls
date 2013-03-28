import pyrax
import time

# Pull username and api key from a file, that follows the following format: 
"""
[rackspace_cloud]
username = #### 
api_key =  #### 
"""
pyrax.set_credential_file("/Users/drizzle/Desktop/corpcreds")

cs = pyrax.cloudservers

# Function that invokes another function (cs.servers.create), after taking user generated input
def serverCreator(s_prefix, s_image, s_flavor, s_quantity):
  i = 0
	serverDetails = {}
	while (i < int(s_quantity)):
		i = i + 1
		s_name = str(s_prefix) + str(i)
		print "Preparing Server: " + str(s_name)
		serverDetails[s_name] = cs.servers.create(s_name, s_image, s_flavor)

	print
					
	print "Waiting on Networking Information (60 Seconds)..."
	time.sleep(60)
	
	print 
	print 
	
	for s_name in serverDetails:
		serverDetails[s_name].get()
		print "### Server " + str(s_name) + " details ###"
		print "Name:", serverDetails[s_name].name
		print "Status:", serverDetails[s_name].status
		print "Admin Password:", serverDetails[s_name].adminPass
		print "Networks:", serverDetails[s_name].networks
		print
		
# Prompt to ask if the user would like to see a list of servers, in the US region.
server_list_input = raw_input("Would you like to see a list of the existing servers? (yes or no) ")
if server_list_input.lower() == "yes" or server_list_input.lower() == "y":
	cs_dfw = pyrax.connect_to_cloudservers(region="DFW")
	cs_ord= pyrax.connect_to_cloudservers(region="ORD")
	dfw_servers = cs_dfw.servers.list()
	ord_servers = cs_ord.servers.list()
	all_servers = dfw_servers + ord_servers
	print all_servers
elif server_list_input.lower() == "no" or server_list_input.lower() == "n":
	print "Skipping server list."
else:
	print "Please enter a yes or no."	

print
print

# Prompt to ask if image list should be shown
image_list_input = raw_input("Would you like to see a list of buildable images? (yes or no) ")
if image_list_input.lower() == "yes" or image_list_input.lower() == "y":
	imgs = cs.images.list()
	for img in imgs:
	    print "Image Name: %s\n ID: %s" % (img.name, img.id)
elif image_list_input.lower() == "no" or image_list_input.lower() == "n":
	print "Skipping image list."
else:
	print "Please enter a yes or no."

print
print

# Prompt to ask if the flavor list should be shown
flavor_list_input = raw_input("Would you like to see a list of flavors? (yes or no) ")
if flavor_list_input.lower() == "yes" or flavor_list_input.lower() == "y":
	flvs = cs.flavors.list()
	for flv in flvs:
	    print "Name:", flv.name
	    print " ID:", flv.id
	    print " RAM:", flv.ram
	    print " Disk:", flv.disk
	    print " VCPUs:", flv.vcpus
	    print
elif flavor_list_input.lower() == "no" or flavor_list_input.lower() == "n":
	print "Skipping flavor list."
else:
	print "Please enter a yes or no."
	
print
print

# Prompt to determine which image should be used
server_image_input = raw_input("What image would you like to build? (Image Name) ")
server_image = [img for img in cs.images.list()
if str(server_image_input) in img.name][0]
print "%s\n ID: %s" % (server_image, server_image.id)

print
print

# Prompt to see which flavor should the servers be built from
server_flavor_input = raw_input("How much RAM should the image have? (Note: Please answer in #GB) ")
server_flavor = [flavor for flavor in cs.flavors.list()
if str(server_flavor_input) in flavor.name][0]
print "Flavor name: %s" % (server_flavor)

print
print

# Prompt to get number of servers to build
quantity_input = raw_input("How many servers would you like to build? (Enter numeric number) ")
if quantity_input.isalnum() and quantity_input > 0:
	quantity = quantity_input
	print quantity_input
else:
	print "Enter a numeric value."

print
print

# Prompt to determine what the beginning part of the server to be called
server_prefix_input = raw_input("What would you like the server's prefix name labled? ")
if len(server_prefix_input) > 0:
	server_prefix = server_prefix_input
	print server_prefix
else:
	print "Enter more than one character."

print
print

# Executes the serverCreator function
serverCreator(server_prefix, server_image.id, server_flavor.id, quantity_input)
