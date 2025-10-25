FROM almalinux:9-minimal

ENV TZ=Asia/Tokyo
WORKDIR /usr/local/bin
RUN microdnf update -y && microdnf clean all
COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /bin/uv
COPY . /murchace/
WORKDIR /murchace
RUN uv sync --frozen

CMD ["uv", "run", "--frozen", "doit", "serve"]
