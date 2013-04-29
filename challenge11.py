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
    
    cert = "-----BEGIN CERTIFICATE-----MIIDEzCCAfugAwIBAgIJAJuSFgp/wiKcMA0GCSqGSIb3DQEBBQUAMCAxHjAcBgNVBAMMFXJhY2tlcmNoYWxsZW5nZTExLmNvbTAeFw0xMzA0MjkwNDI1MzNaFw0yMzA0MjcwNDI1MzNaMCAxHjAcBgNVBAMMFXJhY2tlcmNoYWxsZW5nZTExLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMK6UzS7ot4IKNR2f3SjlARGCE35tM9Kwf09g91HxB4v2ND4dvADnVyjCSHwO2knGWChaF0IP0ffVRZd5zxADq4ZmqYTZZVvMb8MryxvKcGyK62VyV/xlIrlN7JnXPK0+xwXBwD+OaKLZdTIPIdMACDCrMyUceTiVBfv+ArUvOzPElj4k7PoKHC8nLdD5KVEaaAHfUECK8KCzGJNzue0KckDv06eXdRXYUA5yrQNDSwyN3vZUSH+P/e93BgQeQmgsDjWgpM8rtvwr0pFZZOVaF6niGXqSbLL40jdgJIMKR/FuZyN7GLklZis6Gt3HhRNH9EdaQefPmeaDeY8mMNG22UCAwEAAaNQME4wHQYDVR0OBBYEFBL2kRsNqXNsOFt5pvlIRetL3jVmMB8GA1UdIwQYMBaAFBL2kRsNqXNsOFt5pvlIRetL3jVmMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADggEBAIl7fLBKQtyaiLxEQpGs7YJaqCUFfAcVpGZPMc3R+H+yOlEMj/mYzPxl/YML1p/PWCD8/R5WWNPWceCn2HCQU5b0hhLPYyNQDZN7mg2Jsii23/rvg7xwuz2wsVcOOvOmYoUhT0LIuQ6M99O+TvXma3YYbOTpmoIGiUlDiOvWWU7aRGfNoQoqjjrtHx4YxdanRO3Tkkbi91iVQgAzuQ+QDxTht2/FlujWEy9n3q9Ha3vDm+l49rIeCc2ntZzeeMtT29YwmIlANxuYxp2rQu3tthcTi7cfXSeBF1yfg49WVHCWEh6hT+j98oJylRf/gghRClLMfyRGuIcxciq99WCoflM=-----END CERTIFICATE-----"
    pkey = "-----BEGIN RSA PRIVATE KEY-----MIIEpQIBAAKCAQEAwrpTNLui3ggo1HZ/dKOUBEYITfm0z0rB/T2D3UfEHi/Y0Ph28AOdXKMJIfA7aScZYKFoXQg/R99VFl3nPEAOrhmaphNllW8xvwyvLG8pwbIrrZXJX/GUiuU3smdc8rT7HBcHAP45ootl1Mg8h0wAIMKszJRx5OJUF+/4CtS87M8SWPiTs+gocLyct0PkpURpoAd9QQIrwoLMYk3O57QpyQO/Tp5d1FdhQDnKtA0NLDI3e9lRIf4/973cGBB5CaCwONaCkzyu2/CvSkVlk5VoXqeIZepJssvjSN2AkgwpH8W5nI3sYuSVmKzoa3ceFE0f0R1pB58+Z5oN5jyYw0bbZQIDAQABAoIBAHXhB2efwts4A0eCqGt6bqsbngFeDUeDUOW1bHLy89T2UAFIt+9ZsNQYWfnyjHR+V814SE4xJOWkW8TbeZSujnR0SXsJuO/6TRoDWrPCY3u/GNPPHgV3n91pHwtfqRO/3VdG1VWTkF5GlpF12bZpmpY6YxLBNiVBoXiQKw6bc/bB4RZCa8cm3hIlq+rGcH2N3TkkZJvqPKe3dz+OL+gMrlHYRfF62nWhbtUSqBP8lTC6z4DdhGUI+FbBZLfRG3rlpRjNT2xHGDYIdNKGW6UYgDFGZ9bXjuruAYh+I87I6NBSZyQg6AxHGEHsrzWmTHiAHkujZF7hHtjfuY1AuATNfaECgYEA6bQgJrTcvjjsoF/olj/zzOjnxy/SiCub26wE0dvDzXaMLQny1sJfGHPaS8eJ43POkDjcEkotQ+FDaiKJZoKizSOnWWMre7L8ff02GX71Hq8cQTEpg1duZnwDFhNo47t4YfOEjOOI1I7NnNoGHmI9NJnFvzgq6wC2jJLJDlY3Z40CgYEA1U5Fo2pCZBMs5gFgvoMpvFwNXh04sevbtnTbnIFoTvYoGcPDxV/1YK08P/kfi1Q6ywS5/J1o/wgzORvnPF3unQkGTPVA45POoCcntpsqQJNs8WpGqh3TZu9gpOlztd5DoMeJ2J7zPel+Ip+OhpxozokHouDcWjQBS3cK/3m+QTkCgYEA0AV8ZNeycUO8JJiaMDtmqKtbvCouLPUcO3GnrKEAbb+q0GA9nrnO6bYdxjwr2aD4admi0kjid7xoRG3PfcakYRLuYBts1iOgqgicgh9G0nQuIz0+ZWGKrICQQrMuNx9k7VNUVhAmeIVQMeDDd4IcVtjVcvrtANdWplP10OQfVvUCgYEAj8CDUAFBov4FSTDuiRYOH4IOBDo/RjEEzm7svgm8SVK9bbewDSmBTdkR/K8g4h4uzTlvOl6/LvjQxJEYgmdvcudtFppGU9j97JLWwcrKa+CvD/emjekx2nJCuIEYWR3kh8tSC+n7VeMw/ZZ4UCHCxEY3Hj7aYfQgV0Jv6AKdBIkCgYEAq6qp4A7ovn0rkZyfOl/OrgQgmFEwcqNAyf/7Qfp6BSkq16UfGXvWImz0tfrR6t9Qvh1b8GEgRY0zzt4TAuzNuHu6zXSLdGZmW4TRh/EPxMe6hhkQdVdgQeRzKHS+CI7v8AMLfl6ZOLo/ReTQClJPHf+WHhkdBzvFDay2UGK2XJ8=-----END RSA PRIVATE KEY-----"
    
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
   

        
