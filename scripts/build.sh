docker build . -t headsrooms/historedge && docker push headsrooms/historedge
docker build -f scraper.Dockerfile . -t headsrooms/historedge-scraper && docker push headsrooms/historedge-scraper