# syntax=docker/dockerfile:1

########################
# Stage 1 – build base #
########################
FROM rocker/r-ver:4.4.2 AS base

ARG UBUNTU_CODENAME=jammy
ENV DEBIAN_FRONTEND=noninteractive \
    RSPM="https://packagemanager.posit.co/cran/__linux__/ubuntu/${UBUNTU_CODENAME}/latest" \
    MAKEFLAGS="-j$(nproc)" \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    PATH="/opt/venv/bin:${PATH}"

# Python 3.9 tool-chain + JDK for compiling rJava
RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        openjdk-17-jdk-headless \
        libicu-dev \
        python3.9 python3.9-venv python3.9-dev \
        build-essential && \
    python3.9 -m ensurepip --upgrade && \
    rm -rf /var/lib/apt/lists/*

##############################
# Stage 2 – install R pkgs   #
##############################
FROM base AS r-dependencies
COPY install_r_packages.R /tmp/install_r_packages.R
RUN Rscript /tmp/install_r_packages.R

##########################################################
# Stage 3 – create Python venv & install Python packages #
##########################################################
FROM r-dependencies AS python-dependencies
RUN python3.9 -m venv /opt/venv && \
    /opt/venv/bin/python -m pip install --upgrade pip

COPY requirements.txt /tmp/requirements.txt
RUN if [ -s /tmp/requirements.txt ]; then \
        pip install --no-cache-dir -r /tmp/requirements.txt ; \
    fi

##############################################
# Stage 4 – slim runtime with R + Python 3.9 #
##############################################
FROM rocker/r-ver:4.4.2 AS final

ARG UBUNTU_CODENAME=jammy
ENV DEBIAN_FRONTEND=noninteractive \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    LD_LIBRARY_PATH="/usr/lib/jvm/java-17-openjdk-amd64/lib/server:/usr/local/lib/R/lib:${LD_LIBRARY_PATH}" \
    PATH="/opt/venv/bin:${PATH}" \
    R_HOME=/usr/local/lib/R \
    R_LIBS_SITE=/usr/local/lib/R/site-library \
    R_LIBS_USER=/usr/local/lib/R/site-library

# Runtime layer with JDK (contains libjvm.so) + common libs
RUN apt-get update && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        openjdk-17-jdk-headless \                    
        python3.9 python3.9-venv python3.9-dev \
        libblas3 liblapack3 libgfortran5 \
        libcurl4-openssl-dev libssl-dev libxml2 \
        libfontconfig1 libharfbuzz0b libfribidi0 \
        libfreetype6 libpng16-16 libtiff6 libicu-dev \
        libreadline-dev libpcre2-dev libdeflate-dev \
        liblzma-dev libbz2-dev zlib1g-dev && \
    python3.9 -m ensurepip --upgrade && \
    echo "${JAVA_HOME}/lib/server" > /etc/ld.so.conf.d/java.conf && ldconfig && \
    rm -rf /var/lib/apt/lists/*

# Copy R and Python artifacts from build stages
COPY --from=r-dependencies   /usr/local/lib/R /usr/local/lib/R
COPY --from=r-dependencies   /usr/local/bin/R* /usr/local/bin/
COPY --from=python-dependencies /opt/venv /opt/venv

# Optional sanity checks
RUN R --slave -e "cat('Installed R packages:\\n'); cat(rownames(installed.packages()), sep='\\n')" && \
    python3.9 -c "import sys, rpy2, platform; print('Python', sys.version); print('rpy2', rpy2.__version__); print('OS', platform.platform())"

WORKDIR /app
COPY . .

CMD ["python3.9", "main.py"]
