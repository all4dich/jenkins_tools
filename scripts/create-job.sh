#!/bin/bash
export JENKINS_USER="admin"
export JENKINS_PASSWORD_OR_API_TOKEN="11cde0fe5bc41580d9e7c7e6f6f06afaab"
export JENKINS_URL="http://localhost:8080/"
CRUMB=$(curl --user ${JENKINS_USER}:${JENKINS_PASSWORD_OR_API_TOKEN} \
    ${JENKINS_URL}crumbIssuer/api/xml?xpath=concat\(//crumbRequestField,%22:%22,//crumb\))
echo $CRUMB
set -x
curl -s -XPOST "${JENKINS_URL}createItem?name=yourJobName" -u ${JENKINS_USER}:${JENKINS_PASSWORD_OR_API_TOKEN} --data-binary @config.xml -H "Content-Type:text/xml"
set +x
