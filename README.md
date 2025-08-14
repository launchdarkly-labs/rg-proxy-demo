# Release Guardian Proxy Demo

This is a demo for how you can use feature flags with an nginx proxy to do a
Guarded Rollout between different versions of a backend service. This can be
helpful if you're trying to guard a change that isn't easily able to be flagged
in application code, such as when you're changing dependency versions.


## Architecture

The project uses two Docker containers, one running as an nginx proxy and one
running as demo Python app.

We run two copies of the Python app container, one `blue` container representing
the currently deployed copy of the app, and one `green` container representing
the candidate version of the app. The blue version is configured to serve errors
at a 1% error rate, and the green version is configured to serve errors at a 90%
error rate. The containers use the LaunchDarkly SDK to report metrics which can
be used to evaluate service health when performing the Guarded Rollout. (If you
want to adjust the error rates, you can do so by editing the `blue.yaml` and
`green.yaml` files in the app container directory.)

The nginx container is set up to use a LaunchDarkly feature flag to determine
which version (blue or green) of the app container it should send requests to.
The traffic split between the two different versions of the application will be
managed by the Guarded Rollout.


## Running Locally

Prerequisites:

1. Clone this git repo.
1. In your LD project, create the following resources:
    1. `request` context kind.
    1. `http-errors` metric. The metric must be enabled for experiments if you
       want to use it for a Guarded Rollout.
    1. `service-proxy-host` feature flag. This should be a multivariate feature
       flag and its values should be the hostnames of the two containers. If
       you're using the default settings here, they should be `service-blue` and
       `service-green`. Set the flag to serve the `service-blue` variation to
       start.
1. Create a file in the root directory of this project named `sdk-key.txt` which
   contains only your sdk key. (E.g. `cat sdk-key.txt` should output something
   like this:)
```
$ cat sdk-key.txt
sdk-(uuid)
```
1. Follow the steps below to start the containers (currently only
   `docker-compose` is supported).
1. Start a Guarded Rollout in the UI from the `service-blue` flag variation to
   the `service-green` flag variation. For testing purposes, it's probably
   easiest to do a custom rollout with only a 50% traffic split. Enable
   auto-rollback if you want to see that in action.
1. Send traffic to the nginx proxy, e.g. by repeatedly `curl`ing it:
```
while true; do curl http://localhost:8080; echo ""; done
```
1. You should see traffic going to the blue service only before you start the
   rollout, then a mix of traffic to the blue and green services, then only blue
   again after the rollout is rolled back (if you selected auto-rollback).


### docker-compose

1. Run `docker compose` to create the containers:
```
docker-compose up -d --build --force-recreate
```
