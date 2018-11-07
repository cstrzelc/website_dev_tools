#!/usr/bin/python3
#
# Created on/for Ubuntu 18.04
#
# Create webdesign development project
#     1. create apache vhost
#     2. TODO: create database (mariadb)
#     3. TODO: download and install wordpress site instance (with wpcli)

import argparse
import configparser
import os
import platform
import re
import sys
import subprocess

""" binary locations """
#TODO this will go into mkp_webserver()
a2ensite = '/usr/sbin/a2ensite'

""" Argument Handling """
parser = argparse.ArgumentParser(description='Make Noble Technology Project')
parser.add_argument('-n', '--name', metavar='N', required=True, nargs='+', help='Specify the name of the project')
parser.add_argument('-d', '--domain', metavar='N', required=True, nargs='+', help='Specify domain name for project')
parser.add_argument('--hostfile', action='store_true', help='Specify domain name for project')
parser.add_argument('-c', '--configfile', metavar='N', nargs='+', help='Specify alternate configuration file')
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
#validate configuration file;default is /root/.mkproject
try:
    configfile = args.configfile[0]
    if not os.path.isfile(configfile):
        print("The configuration file provided {0} does not exist".format(configfile))
        sys.exit()
except:
    configfile = "/root/.mkproject"
    if not os.path.isfile(configfile):
        print("Configuration not specified and /root/.mkproject configuration does not exist. Exiting...")
        sys.exit()

""" End Argument Handling """

""" Define Object Classes """
"""
 - mkp_webserver() : detects webserver and performs various webserver configuration functions
 - mkp_database()  : detects database and performs various database configurations
 - mkp_os_actions(): performs various actions on the filesystem required to create project
"""

class mkp_webserver:

    #Constructor
    def __init__(self, config):

        #pull webserver settings from configfile
        try:
            config['webserver']['vsite_conf_dir']
            self.vsite_conf_dir = config['webserver'].get('vsite_conf_dir')
        except:
            #vsite_conf_dir is required
            print("Unable to find vsite_conf_dir configuration.")
            sys.exit()
        try:
            config['webserver']['vsite_conf_numeric_prefix']
            self.vsite_conf_numeric_prefix = config['webserver']['vsite_conf_numeric_prefix']
        except:
            #default numeric prefix is '00'
            self.vsite_conf_numeric_prefix = '00'
            
        self.vsite_conf_filename = self.vsite_conf_numeric_prefix + '-' + name + '.conf'
        self.vsite_conf_file_fullpath = self.vsite_conf_dir + '/' + self.vsite_conf_numeric_prefix + '-' + name + '.conf'
        #TODO wrap docroot and log_dir in try/except
        self.vsite_default_docroot = '/var/www'          #default documentroot
        self.vsite_default_log_dir = '/var/log'          #default log directory
        self.linux_dist_info = linux_dist_info

        #settings destined for the webserver configuration file                               
        self.vsite_settings = {'serveradmin':'webmaster@localhost', \
                  'documentroot':self.vsite_default_docroot + '/default_name', \
                  'errorlog':self.vsite_default_log_dir + '/default_error_log', \
                  'accesslog':self.vsite_default_log_dir + 'default_access_log',
                  }
        self.vsite_settings['errorlog'] = self.vsite_default_log_dir + '/' + name + '-error.log'
        self.vsite_settings['accesslog'] = self.vsite_default_log_dir + '/' + name + '-access.log'

        """ Verification checks"""
        #Exit if the vhost configuration already exists
        if os.path.isfile(self.vsite_conf_file_fullpath):
            print("The file {0} already exists".format(self.vsite_conf_file_fullpath))
            sys.exit()

    #build vhost configuration file
    def build_vsite_file(self, name, domain):
        self.vsite_settings['documentroot'] = self.vsite_default_docroot + "/" + name

        with open(self.vsite_conf_file_fullpath, 'w+') as vsite_avail_file:
            vsite_avail_file.write("<VirtualHost " + domain + ":80>\n")
            vsite_avail_file.write("ServerAdmin " + self.vsite_settings['serveradmin'] + "\n")
            vsite_avail_file.write("DocumentRoot " + self.vsite_settings['documentroot'] + "\n")
            vsite_avail_file.write("ErrorLog " + self.vsite_settings['errorlog'] + "\n")
            vsite_avail_file.write("CustomLog " + self.vsite_settings['accesslog'] + " common\n")
            vsite_avail_file.write("</VirtualHost>\n")

    #enable configuration file                                                                                                             
    def enable_vhost(self):
        if self.linux_dist_info[0] == 'Ubuntu':
            try:
                result = subprocess.run([a2ensite, '-q', self.vsite_conf_filename])
            except:
                print("Unable to enable the site for the Apache webserver")
                sys.exit()

    #return webserver settings
    def get_webserver_settings(self):
        return self.vsite_settings

class mkp_database():

    def __init__(self):
        pass

class mkp_os_actions():

    def __init__(self):
        pass

    """ Serverside Actions """
    #create documentroot directory                                                                                                    
    def create_docroot(self, docroot_dir):
        if not os.path.isdir(docroot_dir):
            os.mkdir(docroot_dir)

    #host file entry                                                                                                                       
    def enable_in_hostfile(self, domain):
        domain_pattern = re.compile(r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$')

        #check for existing entry
        for i, line in enumerate(open('/etc/hosts')):

            for match in re.finditer(domain_pattern, line):
                print("Found existing entry for {0} in /etc/hosts.".format(domain))
                return True

        with open('/etc/hosts', 'a') as hosts:
            hosts.write("127.0.0.1 " + domain + "\n")

#in Global namespace
linux_dist_info = platform.dist()

#execute main
def main():
    config = configparser.ConfigParser()             #create config parser object
    config.read(configfile)         #read in project options
    #dbpass=config['webserver']['vsite_conf_dir']            
    
    webserver = mkp_webserver(config)
    os = mkp_os_actions()

    webserver.build_vsite_file(name, domain)

    vsite_settings = webserver.get_webserver_settings()
    os.create_docroot(vsite_settings['documentroot'])
    webserver.enable_vhost()
    if hostfile: 
        os.enable_in_hostfile(domain)

if __name__ == '__main__':
    main()
