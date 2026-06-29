FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV COPPER_ENVIRONMENT=docker

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    clang \
    cmake \
    curl \
    g++ \
    gcc \
    git \
    iverilog \
    latexmk \
    make \
    python3 \
    python3-pip \
    python3-venv \
    tar \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-publishers \
    texlive-bibtex-extra \
    texlive-latex-recommended \
    xz-utils \
    biber \
    verilator \
    yosys \
    && (apt-get install -y --no-install-recommends nextpnr-ice40 || true) \
    && (apt-get install -y --no-install-recommends nextpnr-ecp5 || true) \
    && (apt-get install -y --no-install-recommends openroad || true) \
    && rm -rf /var/lib/apt/lists/*

ARG INSTALL_OSS_CAD_SUITE=0
RUN if [ "$INSTALL_OSS_CAD_SUITE" = "1" ]; then \
      mkdir -p /opt/oss-cad-suite && \
      curl -L https://github.com/YosysHQ/oss-cad-suite-build/releases/latest/download/oss-cad-suite-linux-x64.tgz \
        | tar -xz -C /opt/oss-cad-suite --strip-components=1; \
    fi

ENV PATH="/opt/oss-cad-suite/bin:${PATH}"

WORKDIR /workspace
COPY requirements.txt /workspace/requirements.txt
RUN python3 -m pip install --break-system-packages -r /workspace/requirements.txt pytest numpy pandas

COPY . /workspace

CMD ["make", "readiness"]
