---
name: Cirrus Onboarding Request
about: Request new cirrus client configuration
title: "[Cirrus Onboarding] "
labels: ''
assignees: ''

---

**What is the name of the app that will be using Cirrus? This will be used as a prefix in your Cirrus request path, ex. `/monitor/v2/features/`**

Ex. experimenter

**Where is the nimbus feature manifest?**

Ex. https://github.com/mozilla/experimenter/blob/main/experimenter/experimenter/features/manifests/experimenter/nimbus.fml.yaml

**Is the above location in a public repo or private?**

Ex. public

**Weekly average requests per second?**

This is used to determine how many cirrus instances should be deployed for your service

**Is Cirrus being added to the backend or the frontend?**

This determines whether your cirrus URL will be public or limited to an internal GCP load balancer, Ex. backend-only

**Additional context**

Add any other context here.

**Instructions for Nimbus Team**
- add new application support to the experimenter and notify the Nimbus team in #ask-experimenter on Slack.
- add new clientApplication to cirrus helm chart for **stage** https://github.com/mozilla/webservices-infra/blob/605d520030d4e76da6978ad612de3702f57bb002/cirrus/k8s/cirrus/values-stage.yaml#L10
- add new clientApplication to cirrus helm chart for **prod** https://github.com/mozilla/webservices-infra/blob/605d520030d4e76da6978ad612de3702f57bb002/cirrus/k8s/cirrus/values-prod.yaml#L15
   - based on the given weekly average req/s, configure the minimum autoscaling for the client application in prod based on 10req/s per container for weekly avg req/s (Note: containers handle ~20req/s, so this puts our min at 50% capacity)
   - Ensure that `CIRRUS_REMOTE_SETTING_REFRESH_RATE_IN_SECONDS` is appropriately configured at `.clientApplications.<app>.env.refreshRate`. The stage default is 100 and the prod default is 180.
   - Ensure that `CIRRUS_GLEAN_MAX_EVENTS_BUFFER` is appropriately configured at `.clientApplications.<app>.env.gleanMaxEventsBuffer`. This value represents the max events buffer size for glean. The default for stage is 1 so that QA can test it easily, for the prod the default is 100.
- if necessary, increase tenant resource limits for **stage** https://github.com/mozilla/global-platform-admin/blob/9fea42667d1ed1126284795df9f5f5b330cdffac/tenants/cirrus.yaml#L35-L36
- if necessary, increase tenant resource limits for **prod** https://github.com/mozilla/global-platform-admin/blob/9fea42667d1ed1126284795df9f5f5b330cdffac/tenants/cirrus.yaml#L47-L48
- add cirrus application to probe scraper like in: https://github.com/mozilla/probe-scraper/pulls/617
   - File a DO (Data org) ticket
   - File a bug following the Glean docs
   - Make sure app_name ends with `_cirrus`
   - Have the Glean app depend on "glean-core" and "nimbus-cirrus" (to be noted in the dependencies section when filing a bug).
   - Don't add any metrics or ping files, as this is not required for the this service (the right dependencies are already included)
- add cirrus glean application name like in https://github.com/mozilla/bigquery-etl/pulls/7268 
- sync FML to the experimenter and notify the Nimbus team in #ask-experimenter on Slack.
