import pyrax
import time

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
			
serverCreator("web", "5cebb13a-f783-4f8c-8058-c4182c724ccd", 2, 3)
