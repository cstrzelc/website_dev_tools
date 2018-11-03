#!/usr/bin/python3
#
# Created on/for Ubuntu 18.04
#
# Create webdesign development project
#     1. create apache vhost
#     2. TODO: create database (mariadb)
#     3. TODO: download and install wordpress site instance (with wpcli)

import argparse
import os
import platform
import re
import sys
import subprocess

""" Globals """
vsite_conf_dir = '/etc/apache2/sites-available'  #default directory for configuration file
vsite_conf_filename = ''                         #default name of sites-available file
vsite_conf_file_fullpath = ''                    #default configuration filename
vsite_conf_numeric_prefix = '00'                 #default numeric prefix
vsite_default_docroot = '/var/www/html'          #default documentroot
vsite_default_log_dir = '/var/log'               #default log directory
                                                 #settings destined for the webserver configuration file
vsite_settings = {'serveradmin':'webmaster@localhost', \
                  'documentroot':vsite_default_docroot + '/default_name', \
                  'errorlog':vsite_default_log_dir + '/default_error_log', \
                  'accesslog':vsite_default_log_dir + 'default_access_log',
                  }
linux_dist_info = platform.dist()                #linux distro version

""" binary locations """
a2ensite = '/usr/sbin/a2ensite'

""" Argument Handling """
parser = argparse.ArgumentParser(description='Make Noble Technology Project')
parser.add_argument('-n', '--name', metavar='N', required=True, nargs='+', help='Specify the name of the project')
parser.add_argument('-d', '--domain', metavar='N', required=True, nargs='+', help='Specify domain name for project')
parser.add_argument('--hostfile', action='store_true', help='Specify domain name for project')
args = parser.parse_args()

name = args.name[0].strip()
domain = args.domain[0]
#validate domain name matches common convention
validate_domain = re.match(r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$', domain)
try:
    validate_domain.group(0)
except:
    print("The domain name {0} is not valid.".format(domain))
    sys.exit()
hostfile = args.hostfile

#create the site name; default standard is 00-name.conf
vsite_conf_filename = vsite_conf_numeric_prefix + '-' + name + '.conf'
vsite_conf_file_fullpath = vsite_conf_dir + '/' + vsite_conf_numeric_prefix + '-' + name + '.conf'
#reconfigure logs
vsite_settings['errorlog'] = vsite_default_log_dir + '/' + name + '-error.log'
vsite_settings['accesslog'] = vsite_default_log_dir + '/' + name + '-access.log'


""" VERIFICATION CHECKS """
#Check for exsitence of same-named webserver configuration file
if os.path.isfile(vsite_conf_file_fullpath):
    print("The file {0} already exists".format(vsite_conf_file_fullpath))
    sys.exit()

""" Building Files """
#build 00-name.conf
def build_vsite_file(name, domain):
    vsite_settings['documentroot'] = vsite_default_docroot + "/" + name

    with open(vsite_conf_file_fullpath, 'w+') as vsite_avail_file:
        vsite_avail_file.write("<VirtualHost " + domain + ":80>\n")
        vsite_avail_file.write("ServerAdmin " + vsite_settings['serveradmin'] + "\n")
        vsite_avail_file.write("DocumentRoot " + vsite_settings['documentroot'] + "\n")
        vsite_avail_file.write("ErrorLog " + vsite_settings['errorlog'] + "\n")
        vsite_avail_file.write("CustomLog " + vsite_settings['accesslog'] + " common\n")
        vsite_avail_file.write("</VirtualHost>\n")


""" Serverside Actions """
#create documentroot directory
def create_docroot(docroot_dir):
    if not os.path.isdir(docroot_dir):
        os.mkdir(docroot_dir)

#enable configuration file
def enable_vhost():
    if linux_dist_info[0] == 'Ubuntu':
        try:
            result = subprocess.run([a2ensite, '-q', vsite_conf_filename])
        except:
            print("Unable to enable the site for the Apache webserver")
            sys.exit()

#host file entry
def enable_in_hostfile(domain):
    domain_pattern = re.compile(domain)

    #check for existing entry
    for i, line in enumerate(open('/etc/hosts')):
        for match in re.finditer(domain_pattern, line):
            print("Found existing entry for {0} in /etc/hosts.".format(domain))
            return True

    
    with open('/etc/hosts', 'a') as hosts:
        hosts.write("127.0.0.1 " + domain + "\n")
    

#execute main
def main():
    build_vsite_file(name, domain)
    create_docroot(vsite_settings['documentroot'])
    enable_vhost()
    if hostfile: 
        enable_in_hostfile(domain)

if __name__ == '__main__':
    main()
