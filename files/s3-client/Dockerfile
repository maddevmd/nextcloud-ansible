FROM golang:1.24.8-bookworm AS builder

ENV CGO_ENABLED=0
ENV GOAMD64=v1
ENV GOMAXPROCS=2

RUN go install -p 2 \
    github.com/minio/mc@RELEASE.2025-08-13T08-35-41Z


FROM python:3.12-slim

RUN pip install --no-cache-dir boto3==1.40.0

COPY --from=builder /go/bin/mc /usr/local/bin/mc

WORKDIR /work

CMD ["python", "--version"]
