#!/bin/bash
# this script does not work as expected
export JENKINS_USER="admin"
export JENKINS_PASSWORD_OR_API_TOKEN="11cde0fe5bc41580d9e7c7e6f6f06afaab"
export JENKINS_URL="http://localhost:8080/"
CRUMB=$(curl --user ${JENKINS_USER}:${JENKINS_PASSWORD_OR_API_TOKEN} \
    ${JENKINS_URL}crumbIssuer/api/xml?xpath=concat\(//crumbRequestField,%22:%22,//crumb\))
CRUMB2="\"`echo $CRUMB |sed 's/:/":"/g'`\""
CRUMB3=`echo $CRUMB|awk -F: '{print $2}'`
echo $CRUMB2
set -x
curl -v -s -X POST "${JENKINS_URL}createItem?name=job2" -u ${JENKINS_USER}:${JENKINS_PASSWORD_OR_API_TOKEN} \
    -d "json={'name':'job2','mode':'hudson.model.FreeStyleProject'}" \
    -H "Content-Type:application/x-www-form-urlencoded" \
    -H ".crumb:${CRUMB3}"
#curl -v -s -XPOST "${JENKINS_URL}createItem" -u ${JENKINS_USER}:${JENKINS_PASSWORD_OR_API_TOKEN} -d 'json={"name":"job2","mode":"hudson.model.FreeStyleProject",'${CRUMB2}'}' -H "Content-Type:application/x-www-form-urlencoded" -H "${CRUMB}"
#curl -s -XPOST "${JENKINS_URL}createItem?name=job2" -u ${JENKINS_USER}:${JENKINS_PASSWORD_OR_API_TOKEN} -d 'json={"name":"job2","mode":"hudson.model.FreeStyleProject"}'
set +x
