kubectl apply -f deploy/env-configmap.yaml

cat deploy/redis/redis-deployment.yaml | linkerd inject - | kubectl apply -f -
kubectl apply -f deploy/redis/redis-service.yaml

kubectl apply -f deploy/db/pgdata-persistentvolumeclaim.yaml
cat deploy/db/db-deployment.yaml | linkerd inject - | kubectl apply -f -
kubectl apply -f deploy/db/db-service.yaml

cat deploy/stream-breeder/stream-breeder-job.yaml | linkerd inject - | kubectl apply -f -

cat deploy/api/api-deployment.yaml | linkerd inject - | kubectl apply -f -
kubectl apply -f deploy/api/api-service.yaml

cat deploy/history-distributor/history-distributor-deployment.yaml | linkerd inject - | kubectl apply -f -
cat deploy/history-ingester/history-ingester-deployment.yaml | linkerd inject - | kubectl apply -f -
cat deploy/scraper-distributor/scraper-distributor-deployment.yaml | linkerd inject - | kubectl apply -f -
cat deploy/scraper/scraper-deployment.yaml | linkerd inject - | kubectl apply -f -
