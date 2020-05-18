
CUSTOMERS DATABASE FILE
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
1) start container locally, container will pull down all new code
    1a) Pulls code from github for each client (github only stores wordpress customer config files, not wordpress core).
    2a) Pulls code from nightly backup for each client
2) exec into the container and change the project you're working on to the development branch
3) for wordpress, you may have to import the database from production to a local mysql DB - perhaps a container.

PRODUCTION:
commit to project master -> crontab within container pulls down the update hourly

Generating new images
cd /Users/csaws/Documents/Personal/Noble/Projects/Noble-containers
<edit Docker file>

Pushing new images to ECR


TL;DR


S3 BUCKET FOR NIGHTLY BACKUPS
a483e7440e01:Noble-containers csaws$ aws s3api create-bucket --bucket nobletech-sharedhosting-nightly-backup --profile sharedhosting --region us-east-1
{
    "Location": "/nobletech-sharedhosting-nightly-backup"
}

CREATE USER
a483e7440e01:Noble-containers csaws$ aws iam create-user --user-name nobletech-sharedhosting --profile sharedhosting
{
    "User": {
        "Path": "/",
        "UserName": "nobletech-sharedhosting",
        "UserId": "AIDAXVOC66YP3PH6IYACS",
        "Arn": "arn:aws:iam::527079241247:user/nobletech-sharedhosting",
        "CreateDate": "2020-05-04T16:01:46+00:00"
    }
}
a483e7440e01:Noble-containers csaws$

GROUP FOR SHARED HOSTING ADMINS
a483e7440e01:Noble-containers csaws$ aws iam create-group --group-name nobletech-sharedhosting-admin --profile sharedhosting
{
    "Group": {
        "Path": "/",
        "GroupName": "nobletech-sharedhosting-admin",
        "GroupId": "AGPAXVOC66YPSPGAGOIZT",
        "Arn": "arn:aws:iam::527079241247:group/nobletech-sharedhosting-admin",
        "CreateDate": "2020-05-04T15:48:18+00:00"
    }
}
a483e7440e01:Noble-containers csaws$

ATTACH POLICY
aws iam attach-group-policy --group-name nobletech-sharedhosting-admin --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --profile sharedhosting
ATTACH USER TO GROUP
a483e7440e01:Noble-containers csaws$ aws iam add-user-to-group --group-name nobletech-sharedhosting-admin --user-name nobletech-sharedhosting --profile sharedhosting


a483e7440e01:Noble-containers csaws$ aws iam create-access-key --user-name nobletech-sharedhosting --profile sharedhosting
{
    "AccessKey": {
        "UserName": "nobletech-sharedhosting",
        "AccessKeyId": "AKIAXVOC66YPW6F6PAMB",
        "Status": "Active",
        "SecretAccessKey": "???",
        "CreateDate": "2020-05-04T16:04:42+00:00"
    }
}
