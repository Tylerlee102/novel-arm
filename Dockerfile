FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV COPPER_ENVIRONMENT=docker

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    clang \
    cmake \
    g++ \
    gcc \
    git \
    iverilog \
    latexmk \
    make \
    python3 \
    python3-pip \
    python3-venv \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-publishers \
    texlive-bibtex-extra \
    texlive-latex-recommended \
    biber \
    verilator \
    yosys \
    && (apt-get install -y --no-install-recommends nextpnr-ice40 nextpnr-ecp5 || true) \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
COPY requirements.txt /workspace/requirements.txt
RUN python3 -m pip install --break-system-packages -r /workspace/requirements.txt pytest numpy pandas

COPY . /workspace

CMD ["make", "readiness"]
