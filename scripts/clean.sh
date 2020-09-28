kubectl delete -f deploy/env-configmap.yaml

kubectl delete -f deploy/redis/redis-deployment.yaml
kubectl delete -f deploy/redis/redis-service.yaml

kubectl delete -f deploy/db/db-deployment.yaml
kubectl delete -f deploy/db/db-service.yaml

kubectl delete -f deploy/stream-breeder/stream-breeder-job.yaml

kubectl delete -f deploy/api/api-deployment.yaml
kubectl delete -f deploy/api/api-service.yaml

kubectl delete -f deploy/history-distributor/history-distributor-deployment.yaml
kubectl delete -f deploy/history-ingester/history-ingester-deployment.yaml
kubectl delete -f deploy/scraper-distributor/scraper-distributor-deployment.yaml
kubectl delete -f deploy/scraper/scraper-deployment.yaml