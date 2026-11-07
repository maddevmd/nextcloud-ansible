FROM golang:1.24.8-bookworm AS builder

ARG MINIO_VERSION=RELEASE.2025-10-15T17-29-55Z

WORKDIR /src

RUN git clone --depth 1 --branch "${MINIO_VERSION}" \
    https://github.com/minio/minio.git .

ENV CGO_ENABLED=0
ENV GOAMD64=v1
ENV GOMAXPROCS=2

RUN go build -p 2 -trimpath -o /out/minio .


FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /data \
    && chown 10001:10001 /data

COPY --from=builder /out/minio /usr/local/bin/minio

USER 10001:10001

ENTRYPOINT ["/usr/local/bin/minio"]
CMD ["--version"]
