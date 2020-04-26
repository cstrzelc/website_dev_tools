import csv
import os
from crontab import CronTab

working_directory='/tmp/noble/'
home="/home/"
update_customers_script='update_nobletech_customers.py'
customers_database='/tmp/noble/website_dev_tools/customers.csv'

def install_crontab(cronuser):
    cron = CronTab(user=cronuser)
    job = cron.new(command="/usr/bin/python3 " + working_directory + update_customers_script)
    job.minute.every(30)

    cron.write()

# Provision customer environment based on customers.csv
with open(customers_database, newline='') as csvfile:
    customerfile = csv.reader(csvfile, delimiter=',')
    for customer in customerfile:
        customer_alias = customer[0]
        customer_url = customer[1]
        customer_email = customer[2]
        customer_www_root = home + customer_alias + "/public_html"
        command = "mkdir -p  " + customer_www_root

        # Create customer directory
        os.system(command)

        # Download customer website source
        try:
            os.system("cd " + customer_www_root + ";git clone git@github-nobletech:cstrzelc/" + customer_alias + ".git .")
        except:
            os.system("cd " + customer_www_root + ";git pull origin master")

        # Apache conf.d configuration for customer
        conffile = "/etc/httpd/conf.d/" + customer_alias + ".conf"

        seq1 = [ "< VirtualHost *: 80 >\n", "DocumentRoot " + customer_www_root + "\n", \
                "serverAdmin " + customer_email + "\n", "ServerName " + customer_url + "\n",
                "ErrorLog /var/log/httpd/" + customer_alias + "-error_log\n", \
                "CustomLog /var/log/httpd/" + customer_alias + "-access_log\n", \
                "< / VirtualHost >\n\n"
                ]

        seq2 = [ "<Directory " + customer_www_root + " >\n", "AllowOverride FileInfo AuthConfig Limit Indexes\n", \
                "Options MultiViews Indexes SymLinksIfOwnerMatch IncludesNoExec\n", \
                "Require method GET POST OPTIONS\n", \
                "</Directory>\n" ]

        # write configuration to Apache conf file
        with open(conffile, "w") as conf:
            conf.writelines( seq1 )
            conf.writelines( seq2 )

#run_git_update="/usr/bin/python3 " + working_directory + update_customers_script
#os.system(run_git_update)

#Create crontab for doing regular github pulls
install_crontab('root')





