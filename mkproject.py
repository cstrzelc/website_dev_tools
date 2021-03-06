#!/usr/bin/python3
#
# Created on/for Ubuntu 18.04

import argparse
import configparser
import MySQLdb
import os
import platform
import pycurl
import re
import sys
import subprocess

# figure out the operating system early and place in Global namespace
linux_dist_info = platform.dist()
supported_os = [ 'Ubuntu' ]

#Verify operating system is supported
os_verified = [linux_dist_info[0] for supported in supported_os if supported == linux_dist_info[0]]
if not os_verified:
    print("The {0} operating system is not supported.".format(linux_dist_info))
    os_distro = False
else:
    os_distro = os_verified[0]

""" Global Variables """
# TODO these will have to move a more manageable location
wpcli_curl_filename = '/tmp/wp-cli.phar'
wpcli_remote_url = 'https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar'

""" Argument Handling """
parser = argparse.ArgumentParser(description='Make Noble Technology Project')
parser.add_argument('-n', '--name', metavar='XXX', required=True, nargs='+', help='Specify the name of the project')
parser.add_argument('-d', '--domain', metavar='XXX', required=True, nargs='+', help='Specify domain name for project')
parser.add_argument('--hostfile', action='store_true', help='add project to the hosts file')
parser.add_argument('--webserver', action='store_true', help='build webserver config file.')
parser.add_argument('-c', '--configfile', metavar='XXX', nargs='+', help='Specify alternate configuration file')
parser.add_argument('-r', '--database', action='store_true', help='Enable database creation.')
parser.add_argument('--install_wpcli', action="store_true", help="Download and install wpcli")
parser.add_argument('--wpcli', action='store_true', help='initiate wpcli configuration')
parser.add_argument('--install_all', action='store_true', help='Install all needed software.')
parser.add_argument('--configure_all', action='store_true', help='Configure all software')
args = parser.parse_args()

name = args.name[0].strip()
domain = args.domain[0]
# validate domain name matches common convention
validate_domain = re.match(r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$', domain)
try:
    validate_domain.group(0)
except:
    print("The domain name {0} is not valid.".format(domain))
    sys.exit()

# validate configuration file;default is /root/.mkproject
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

install_wpcli = args.install_wpcli
enable_hostfile = args.hostfile
enable_webserver = args.webserver
enable_wpcli = args.wpcli
enable_database = args.database

install_all = args.install_all
configure_all = args.configure_all

if install_all:
    install_wpcli = True

if configure_all:
    enable_hostfile = True
    enable_webserver = True
    enable_wpcli = True
    enable_database = True

""" End Argument Handling """

""" Define Object Classes """
"""
 - mkp_webserver() : detects webserver and performs various webserver configuration functions
 - mkp_database()  : detects database and performs various database configurations
 - mkp_os_actions(): performs various actions on the filesystem required to create project
"""
class mkp_webserver:

    # Constructor
    def __init__(self, config):

        # pull webserver settings from configfile
        try:
            config['webserver']['vsite_conf_dir']
            self.vsite_conf_dir = config['webserver'].get('vsite_conf_dir')
        except:
            # vsite_conf_dir is required
            print("Unable to find vsite_conf_dir configuration.")
            sys.exit()
        try:
            config['webserver']['vsite_conf_numeric_prefix']
            self.vsite_conf_numeric_prefix = config['webserver']['vsite_conf_numeric_prefix']
        except:
            # default numeric prefix is '00'
            self.vsite_conf_numeric_prefix = '00'

        self.vsite_conf_filename = self.vsite_conf_numeric_prefix + '-' + name + '.conf'
        self.vsite_conf_file_fullpath = self.vsite_conf_dir + '/' + self.vsite_conf_numeric_prefix + '-' + name + '.conf'
        # TODO wrap docroot and log_dir in try/except
        self.vsite_default_docroot = '/var/www'  # default documentroot
        self.vsite_default_log_dir = '/var/log'  # default log directory
        self.linux_dist_info = linux_dist_info
        self.supported_os = supported_os
        self.os_distro = os_distro
        self.supported_webservers = []

        # settings destined for the webserver configuration file
        self.vsite_settings = {'serveradmin': 'webmaster@localhost', \
                               'documentroot': self.vsite_default_docroot + '/default_name', \
                               'errorlog': self.vsite_default_log_dir + '/default_error_log', \
                               'accesslog': self.vsite_default_log_dir + 'default_access_log',
                               }
        self.vsite_settings['errorlog'] = self.vsite_default_log_dir + '/' + name + '-error.log'
        self.vsite_settings['accesslog'] = self.vsite_default_log_dir + '/' + name + '-access.log'

        # define tools specific to os flavor or webserver
        self.pkg_mngr = None

        self.set_webserver_tools()


        """ Verification checks"""
        #TODO this verification check for the site file needs to be a warning
        # Exit if the vhost configuration already exists
        #if os.path.isfile(self.vsite_conf_file_fullpath):
        #    print("The file {0} already exists".format(self.vsite_conf_file_fullpath))
        #    sys.exit()

    def set_webserver_tools(self):
        if self.os_distro == "Ubuntu":
            # set pkg_mngr
            self.pkg_mngr = 'apt'
            #supported webservers on Ubuntu
            self.supported_webservers = ['apache2']  # TODO need to add nginx

    # build vhost configuration file
    def build_vsite_file(self, name, domain):
        self.vsite_settings['documentroot'] = self.vsite_default_docroot + "/" + name

        with open(self.vsite_conf_file_fullpath, 'w+') as vsite_avail_file:
            vsite_avail_file.write("<VirtualHost *:80>\n")
            vsite_avail_file.write("ServerAdmin " + self.vsite_settings['serveradmin'] + "\n")
            vsite_avail_file.write("ServerName " + domain + "\n")
            vsite_avail_file.write("ServerAlias www." + domain + "\n")
            vsite_avail_file.write("DocumentRoot " + self.vsite_settings['documentroot'] + "\n")
            vsite_avail_file.write("ErrorLog " + self.vsite_settings['errorlog'] + "\n")
            vsite_avail_file.write("CustomLog " + self.vsite_settings['accesslog'] + " common\n")
            vsite_avail_file.write("</VirtualHost>\n")

    # enable configuration file
    def enable_vhost(self):
        if self.os_distro == 'Ubuntu':
            try:
                result = subprocess.run(['a2ensite', '-q', self.vsite_conf_filename])
            except:
                print("Unable to enable the site for the Apache webserver")

    # return webserver settings
    def get_webserver_settings(self):
        return self.vsite_settings

    def run_pkgmngr_webserver_check(self, webserver, pkg_mngr):
        if pkg_mngr == 'apt':
            return ['dpkg', '-l', webserver]
        elif pkg_mngr == 'yum':
            return ['rpm', '-q', webserver]

    # verify the existenct of a webserver for this OS
    def verify_webserver(self):
        # define all supported tools for os flavor in set_webserver_tools()
        for webserver in self.supported_webservers:
            cmnd = self.run_pkgmngr_webserver_check(webserver, self.pkg_mngr)
            self.p = subprocess.run(cmnd)
            if self.p.returncode == 0:
                return
            else:
                continue

        if self.p.returncode != 0:
            print("Supported webserver not found.  Supported webserver should be one of these {0}".format(self.supported_webservers))
            sys.exit()
    def get_documentroot(self):
        return self.vsite_default_docroot + "/" + name

class mkp_database:

    def __init__(self, config):

        self.os_distro = os_distro
        self.domain = domain
        self.name = name
        self.dbtype = "mysql" #TODO: this will be dynamic in the future
        #use the prefix name if it is populated
        if config['general']['prefix']:
            self.prefix_name = config['general']['prefix'] + "_" + name
        else:
            self.prefix_name = name

        self.db_project_pass = config['database'].get('db_project_pass')


        #Pull in configuration from config file
        try:
            self.dbpass = config['database'].get('dbpass')
        except:
            print("Unable determine database root password.")
            sys.exit()
        try:
            self.dbadmin = config['database'].get('dbadmin')
        except:
            print("Unable determine database admin user.")
            sys.exit()

        self.dbhost_string = "localhost"
        self.dbadmin_string = self.dbadmin
        self.dbpass_string = self.dbpass


        try:
            self.db = MySQLdb.connect(self.dbhost_string, self.dbadmin_string, self.dbpass_string )
        except:
            print("Unable to create database connection.")
            sys.exit()

        self.set_database_tools()

    def set_database_tools(self):
        if self.os_distro == "Ubuntu":
            # set pkg_mngr
            self.pkg_mngr = 'apt'
            #supported webservers on Ubuntu
            self.supported_database_servers = [ 'mariadb-server' ]  # TODO need to add nginx

    def verify_database_server(self):
        pass
        #Needed to install mariadb-server, python3-mysqldb
        #Needed to run /usr/bin/mysql_secure_installation after installation

    #TODO: By default the database will be prefix_projectname and same for the user.
    #These will be made into configuratble options in the future
    def create_database(self) :
        # Create a Cursor object to execute queries.
        self.cur = self.db.cursor()

        #Create database
        try:
            self.cur.execute("CREATE DATABASE " + self.prefix_name + ";")
        except:
            print("database not created.  Check if database already exists.")

    #create database user and grant full permissions to this database.
    def create_user(self):
        stmt="CREATE USER '" + self.prefix_name + "'@'localhost' IDENTIFIED BY '" + self.db_project_pass + "';"
        try:
            self.cur.execute(stmt)
        except:
            print("database user not created.  Check if the user already exists.")

    def grant_all_privs_to_project_db(self):
        stmt="GRANT ALL PRIVILEGES ON " + self.prefix_name + ".* TO '" + self.prefix_name + "'@'localhost';"
        try:
            self.cur.execute(stmt)
        except:
            print("database permissions not applied. Check your database configuration.")

        try:
            self.cur.execute("FLUSH PRIVILEGES;")
        except:
            print("Failed to flush privileges.")

    def get_db_name(self):
        return self.prefix_name

    def get_db_credentials(self):
        return { "dbadmin" : self.dbadmin_string, "dbpass" : self.dbpass_string, "db_project_pass" : self.db_project_pass }

    def close_database(self):
        self.db.close()

class mkp_wpcli:

    def __init__(self, config):
        #Defaults
        self.wpcli_continue_execution = True
        self.wpcli_curl_filename = '/tmp/wp-cli.phar'
        self.wpcli_remote_url = 'https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar'
        self.wpcli_install_location = '/usr/local/bin/wp'
        self.wpcli_admin_user = 'mkp'
        self.wpcli_admin_email = 'mkp@example.com'
        self.wpcli_admin_pass = 'mkpenter!' #incase these are not defined in the config file

        #get configuration file parameters
        if config['wpcli'].get('wpcli_curl_filename'):
            self.wpcli_curl_filename = config['wpcli'].get('wpcli_curl_filename')
        if config['wpcli'].get(wpcli_remote_url):
            self.wpcli_remote_url = config['wpcli'].get('wpcli_remote_url')
        if config['wpcli'].get('wpcli_install_location'):
            self.wpcli_install_location = config['wpcli'].get('wpcli_install_location')
        if config['wpcli'].get('wpcli_admin_user'):
            self.wpcli_admin_user = config['wpcli'].get('wpcli_admin_user')
        if config['wpcli'].get('wpcli_admin_email'):
            self.wpcli_admin_email = config['wpcli'].get('wpcli_admin_email')
        if config['wpcli'].get('wpcli_admin_pass'):
            self.wpcli_admin_pass = config['wpcli'].get('wpcli_admin_pass')


    def verify_php_install(self):
        pass

    def verify_wpcli_install(self):
        pass

    def get_wpcli_info(self):
        pass
        # php wp-cli.phar --info

    def install_wpcli(self, database, webserver):
        document_root = webserver.get_documentroot()

        # As long as the file is opened in binary mode, both Python 2 and Python 3
        # can write response body to it without decoding.
        try:
            with open(self.wpcli_curl_filename, 'wb') as f:
                c = pycurl.Curl()
                c.setopt(c.URL, self.wpcli_remote_url)
                c.setopt(c.WRITEDATA, f)
                c.perform()
                c.close()
        except:
            print("Unable to open file for writing {0}".format(self.wpcli_curl_filename))
            return False

        #mv the wpcli phar file to perm location
        run_args = ['mv', self.wpcli_curl_filename, self.wpcli_install_location ]
        try:
            p = subprocess.Popen(run_args)
            p.wait()
        except:
            print("Unable to cp wpcli command to {0}".format(self.wpcli_install_location))
            return False

        #fix permissions on wpcli installatino
        run_args = ['chmod', '0755', self.wpcli_install_location]
        try:
            p = subprocess.Popen(run_args)
            p.wait()
        except:
            print("Unable to chmod on {0}".format(self.wpcli_install_location))
            return False

        dbname = database.get_db_name()
        dbcredentials = database.get_db_credentials()
        dbadmin = dbname
        db_project_pass = dbcredentials.get('db_project_pass')

        #download latest wordpress
        run_args = ['wp', 'core', 'download', '--path='+document_root, '--allow-root']
        try:
            p = subprocess.Popen(run_args)
            p.wait()
        except:
            print("Unable to download/install Wordpress with wpcli.")
            return False

        #create configuration file wp-config.php
        run_args = [ 'wp', 'config', 'create', '--dbname='+dbname, '--dbuser='+dbadmin, '--dbpass='+db_project_pass, '--allow-root', '--path='+document_root]
        try:
            p = subprocess.Popen(run_args)
            p.wait()
        except:
            print("Unable to create wp_config file with wpcli.")
            return False

        #install wordpress
        run_args = ['wp', 'core', 'install', '--url='+domain, '--title='+dbname, '--admin_user='+self.wpcli_admin_user, '--admin_password='+self.wpcli_admin_pass, '--admin_email='+self.wpcli_admin_email, '--allow-root', '--path='+document_root]
        try:
            p = subprocess.Popen(run_args)
            p.wait()
        except:
            print("Unable to configure project {0} with wpcli.".format(dbname))
            return False



class mkp_os_actions():

    def __init__(self):
        pass

    """ Serverside Actions """

    # create documentroot directory
    def create_docroot(self, docroot_dir):
        if not os.path.isdir(docroot_dir):
            os.mkdir(docroot_dir)

    # host file entry
    def enable_in_hostfile(self, domain):

        print("Adding {0} Host File Entry".format(domain))
        if domain not in open('/etc/hosts').read():
            with open('/etc/hosts', 'a') as hosts:
                hosts.write("127.0.0.1 " + domain + "\n")
        else:
            return True


# execute main
def main():
    config = configparser.ConfigParser()  # create config parser object
    config.read(configfile)  # read in project options

    os = mkp_os_actions()
    webserver = mkp_webserver(config)
    database = mkp_database(config)
    wpcli = mkp_wpcli(config)

    """ Webserver Operations """
    if enable_webserver:
        webserver.verify_webserver()
        webserver.build_vsite_file(name, domain)
        vsite_settings = webserver.get_webserver_settings()
        os.create_docroot(vsite_settings['documentroot'])
        webserver.enable_vhost()

    if enable_hostfile:
        os.enable_in_hostfile(domain)

    """ Database Operations """
    if enable_database:
        database.create_database()
        database.create_user()
        database.grant_all_privs_to_project_db()
        database.close_database()

    """ WP CLI Operations """
    if install_wpcli:
        wpcli.install_wpcli(database, webserver)
    if enable_wpcli:
        pass


if __name__ == '__main__':
    main()
