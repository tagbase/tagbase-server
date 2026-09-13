# Bake first-party and wrapper images for GHCR.
#   VERSION=v0.0.0 docker buildx bake -f docker-bake.hcl --print
variable "REGISTRY" {
  default = "ghcr.io/tagbase"
}

variable "VERSION" {
  default = "latest"
}

group "default" {
  targets = [
    "tagbase-server",
    "tagbase-nginx",
    "tagbase-fswatch",
    "tagbase-docker-cron",
    "tagbase-lego",
    "tagbase-postgis",
    "tagbase-alloy",
    "tagbase-prometheus",
    "tagbase-loki",
    "tagbase-tempo",
    "tagbase-grafana",
  ]
}

target "tagbase-server" {
  context   = "./tagbase_server"
  tags      = ["${REGISTRY}/tagbase-server:${VERSION}"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "tagbase-nginx" {
  context   = "./services/nginx"
  tags      = ["${REGISTRY}/tagbase-nginx:${VERSION}"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "tagbase-fswatch" {
  context   = "./services/fswatch"
  tags      = ["${REGISTRY}/tagbase-fswatch:${VERSION}"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "tagbase-docker-cron" {
  context   = "./services/docker-cron"
  tags      = ["${REGISTRY}/tagbase-docker-cron:${VERSION}"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "tagbase-lego" {
  context   = "./services/lego"
  tags      = ["${REGISTRY}/tagbase-lego:${VERSION}"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "tagbase-postgis" {
  context   = "./services/postgis"
  tags      = ["${REGISTRY}/tagbase-postgis:${VERSION}"]
  platforms = ["linux/amd64"]
}

target "tagbase-alloy" {
  context    = "./services/observability"
  dockerfile = "alloy.Dockerfile"
  tags       = ["${REGISTRY}/tagbase-alloy:${VERSION}"]
  platforms  = ["linux/amd64", "linux/arm64"]
}

target "tagbase-prometheus" {
  context    = "./services/observability"
  dockerfile = "prometheus.Dockerfile"
  tags       = ["${REGISTRY}/tagbase-prometheus:${VERSION}"]
  platforms  = ["linux/amd64", "linux/arm64"]
}

target "tagbase-loki" {
  context    = "./services/observability"
  dockerfile = "loki.Dockerfile"
  tags       = ["${REGISTRY}/tagbase-loki:${VERSION}"]
  platforms  = ["linux/amd64", "linux/arm64"]
}

target "tagbase-tempo" {
  context    = "./services/observability"
  dockerfile = "tempo.Dockerfile"
  tags       = ["${REGISTRY}/tagbase-tempo:${VERSION}"]
  platforms  = ["linux/amd64", "linux/arm64"]
}

target "tagbase-grafana" {
  context    = "./services/observability"
  dockerfile = "grafana.Dockerfile"
  tags       = ["${REGISTRY}/tagbase-grafana:${VERSION}"]
  platforms  = ["linux/amd64", "linux/arm64"]
}
