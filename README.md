# K8s Proxy Spike

This investigates how we might use Release Guardian to proxy traffic to service
versions running in Kubernetes.


## Running Locally

Prerequisites:

1. Clone this git repo.
1. In your LD project, create the following resources (see the `drewinglis-test`
   project in public prod for how to set them up):
    1. `request` context kind.
    1. `http-errors` metric.
    1. `service-proxy-host` feature flag.
1. Create a file in the root directory of this project named `sdk-key.txt` which
   contains only your sdk key.

### docker-compose

1. Run `docker compose` to create the containers:
```
docker-compose up -d --build --force-recreate
```

### Kubernetes

1. Create the secret in kubernetes:
```
kubectl create secret generic sdk-key --from-file=sdk-key=./sdk-key.txt
```
1. Add the nginx ingress controller:
```
kubectl apply -f https://kind.sigs.k8s.io/examples/ingress/deploy-ingress-nginx.yaml
```
