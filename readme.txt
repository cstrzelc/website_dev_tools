customers.csv column fields
Example: drdutko,drdutko.com,chris@nobletech.net,website,,,,0,12.99,august

Fields defined:
client: alias i.e. drdutko
domain: i.e. example.com
email: i.e. chris@nobletech.net
type: accepted values 'website' or 'wordpress'
database connection host: string value
database name: string value
database username: string value
?
monthly hosting price: i.e. 12.99
renewal date: accepted answers are months in lowercase i.e. august

FLOW OF DATA:
Development:
1) start container locally, container will pull down all new code on start
2) exec into the container and change the project you're working on to the development branch
3) for wordpress, you may have to import the database from production to a local mysql DB - perhaps a container.

Production:
commit to project master -> crontab within container pulls down the update hourly

Generating new images
cd /Users/csaws/Documents/Personal/Noble/Projects/Noble-containers
<edit Docker file>

Pushing new images to ECR