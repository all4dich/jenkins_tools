#!/bin/bash
export JENKINS_USER="admin"
export JENKINS_PASSWORD_OR_API_TOKEN="11cde0fe5bc41580d9e7c7e6f6f06afaab"
export JENKINS_URL="http://localhost:8080/"

CRUMB=$(curl --user ${JENKINS_USER}:${JENKINS_PASSWORD_OR_API_TOKEN} \
    ${JENKINS_URL}crumbIssuer/api/xml?xpath=concat\(//crumbRequestField,%22:%22,//crumb\))
echo $CRUMB
set -x
curl -u "${JENKINS_USER}:${JENKINS_PASSWORD_OR_API_TOKEN}" -H "Content-Type:application/x-www-form-urlencoded" -H "$CRUMB" -X POST \
-d 'json={"name": "testnode", "nodeDescription": "testnode", "numExecutors": "1", "remoteFS": "/tmp/", "labelString": "do-not-use", "mode": "NORMAL", "": ["hudson.slaves.CommandLauncher", "hudson.slaves.RetentionStrategy$Always"], "launcher": {"stapler-class": "hudson.slaves.CommandLauncher", "$class": "hudson.slaves.CommandLauncher", "command": "/binary/build_results/tools/agent_connect.sh 156.147.61.181"}, "retentionStrategy": {"stapler-class": "hudson.slaves.RetentionStrategy$Always", "$class": "hudson.slaves.RetentionStrategy$Always"}, "nodeProperties": {"stapler-class-bag": "true", "hudson-slaves-EnvironmentVariablesNodeProperty": {"env": {"key": "you_name", "value": "you_value"}}}, "type": "hudson.slaves.DumbSlave"}' \
 "${JENKINS_URL}computer/doCreateItem?name=testagent&type=hudson.slaves.DumbSlave"
set +x
