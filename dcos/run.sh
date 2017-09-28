aws cloudformation create-stack --stack-name dcos-statengine --template-url=https://s3-us-west-2.amazonaws.com/downloads.dcos.io/dcos/EarlyAccess/commit/a5ecc9af5d9ca903f53fa16f6f0ebd597095652e/cloudformation/multi-master.cloudformation.json --parameters='[{"ParameterKey":"KeyName","ParameterValue":"stat-key-west"},{"ParameterKey":"PublicSlaveInstanceCount","ParameterValue":"1"}, {"ParameterKey":"SlaveInstanceCount","ParameterValue":"5"}, {"ParameterKey":"OAuthEnabled","ParameterValue":"true"},{"ParameterKey":"AdminLocation","ParameterValue":"0.0.0.0/0" }]' --capabilities CAPABILITY_IAM

aws cloudformation list-stacks

aws cloudformation describe-stacks --stack-name dcos-statengine

# Master DNS string, to be used in dcos connection
aws cloudformation describe-stacks --stack-name dcos-statengine | jq '.Stacks | .[1] | .Outputs'

# Connect dcos cluster to local, log in with github oauth for first account
dcos cluster setup dcos-stat-ElasticL-1IDJP528J3LPL-975310574.us-west-1.elb.amazonaws.com

# Install kafka
dcos package install kafka
# When setting up the durable mount volume, number of brokers, deletable topics, etc.
# dcos package install --options=kafka.json kafka

# Create kafka topic
dcos kafka create topic fire

# SSH into service
dcos node ssh --master-proxy --leader

# Spin up custom container

