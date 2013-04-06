#!/usr/bin/python

import os
import time
import pyrax
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-n', '--name', help='Name of database to be created', required=True)
    parser.add_argument ('-u', '--username', help='Username of database to be created', required=True)
    parser.add_argument ('-p', '--password', help='Password of database to be created', required=True)


    args = parser.parse_args()

    pyrax.set_credential_file(".PathToCreds")
    cdb = pyrax.cloud_databases
 
    # Creates the instance
    instance_name = "Default Instance"
    inst = cdb.create(instance_name, flavor="1GB Instance", volume=2)
    print "Instance: %s" % (inst)

    completed_instance = []
    while len(completed_instance) < 1:    
        for instance in cdb.list():
            if str(instance_name) in instance.name and instance.status == 'ACTIVE':
                completed_instance.append(instance_name)
        print "Waiting for instance to be ready. Trying again in 30 seconds."
        time.sleep(30)
    
    print "Instance is ready. Creating database."
    
    # Creates the database   
    db = inst.create_database(args.name)
    print "DB: %s" % (db)    

    # Creates the user    
    user = inst.create_user(name=args.username, password=args.password, database_names=[db])
    print "User: %s" % (user)

    

if __name__ == '__main__':
    main()
