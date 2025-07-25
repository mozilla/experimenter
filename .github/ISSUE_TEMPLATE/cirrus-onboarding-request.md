---
name: Cirrus Onboarding Request
about: Request new cirrus client configuration
title: "[Cirrus Onboarding] "
labels: ''
assignees: ''

---

**What is the name of the app that will be using Cirrus? This will be used as a prefix in your Cirrus request path, ex. `/monitor/v2/features/`**

Ex. monitor

**Where is the nimbus feature manifest?**

Ex. https://github.com/mozilla/blurts-server/blob/main/config/nimbus.yaml

**Weekly average requests per second?**

This is used to determine how many cirrus instances should be deployed for your service

**Is Cirrus being added to the backend or the frontend?**

This determines whether the cirrus URL will be public or limited to an internal GCP load balancer, Ex. backend-only

**Additional context**

Add any other context here.

**Instructions for Nimbus Team**
- add new application support to the experimenter and notify the Nimbus team in #ask-experimenter on Slack.
- add new clientApplication to cirrus helm chart for **stage** https://github.com/mozilla/webservices-infra/blob/605d520030d4e76da6978ad612de3702f57bb002/cirrus/k8s/cirrus/values-stage.yaml#L10
- add new clientApplication to cirrus helm chart for **prod** https://github.com/mozilla/webservices-infra/blob/605d520030d4e76da6978ad612de3702f57bb002/cirrus/k8s/cirrus/values-prod.yaml#L15
   - based on the given weekly average req/s, configure the minimum autoscaling for the client application in prod based on 100req/s per container for weekly avg req/s (Note: containers handle ~200req/s, so this puts our min at 50% capacity)
- if necessary, increase tenant resource limits for **stage** https://github.com/mozilla/global-platform-admin/blob/9fea42667d1ed1126284795df9f5f5b330cdffac/tenants/cirrus.yaml#L35-L36
- if necessary, increase tenant resource limits for **prod** https://github.com/mozilla/global-platform-admin/blob/9fea42667d1ed1126284795df9f5f5b330cdffac/tenants/cirrus.yaml#L47-L48
- add cirrus application to probe scraper like in: mozilla/probe-scraper#617
- add cirrus glean application name like in mozilla/bigquery-etl#7268 
- sync FML to the experimenter and notify the Nimbus team in #ask-experimenter on Slack.
- Ensure that ` CIRRUS_REMOTE_SETTING_REFRESH_RATE_IN_SECONDS` is appropriately configured.
- Ensure that ` CIRRUS_GLEAN_MAX_EVENTS_BUFFER` is appropriately configured. This value represents the max events buffer size for glean. We recommend for stage to set the value as 1 so that QA can test it easily, for the prod you can set as 100.
