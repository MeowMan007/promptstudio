FROM golang:1.24-alpine AS source
RUN apk add --no-cache git

FROM source AS minio-build
ARG MINIO_VERSION=RELEASE.2025-10-15T17-29-55Z
RUN GOBIN=/out go install -trimpath -ldflags="-s -w" "github.com/minio/minio@${MINIO_VERSION}"

FROM source AS mc-build
ARG MC_VERSION=RELEASE.2025-08-13T08-35-41Z
RUN GOBIN=/out go install -trimpath -ldflags="-s -w" "github.com/minio/mc@${MC_VERSION}"

FROM alpine:3.22 AS server
RUN apk add --no-cache ca-certificates \
    && addgroup -S minio \
    && adduser -S -G minio minio \
    && mkdir -p /data \
    && chown minio:minio /data
COPY --from=minio-build /out/minio /usr/local/bin/minio
USER minio
EXPOSE 9000 9001
ENTRYPOINT ["minio"]

FROM alpine:3.22 AS mc
RUN apk add --no-cache ca-certificates
COPY --from=mc-build /out/mc /usr/local/bin/mc
ENTRYPOINT ["mc"]
