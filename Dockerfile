# syntax=docker/dockerfile:1

########################
# Stage 1 – build base #
########################
FROM rocker/r-ver:4.4.2 AS base

ARG UBUNTU_CODENAME=jammy
ENV DEBIAN_FRONTEND=noninteractive \
    RSPM="https://packagemanager.posit.co/cran/__linux__/ubuntu/${UBUNTU_CODENAME}/latest" \
    MAKEFLAGS="-j$(nproc)" \
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
    # Set JAVA_HOME after JDK installation based on detected architecture
    ARCH=$(dpkg --print-architecture) && \
    echo "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-${ARCH}" >> /etc/environment && \
    echo "Detected architecture: ${ARCH}" && \
    rm -rf /var/lib/apt/lists/*

##############################
# Stage 2 – install R pkgs   #
##############################
FROM base AS r-dependencies
COPY install_r_packages.R /tmp/install_r_packages.R
RUN . /etc/environment && R CMD javareconf && Rscript /tmp/install_r_packages.R

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
    rm -rf /var/lib/apt/lists/*

# Copy R and Python artifacts from build stages
COPY --from=r-dependencies   /usr/local/lib/R /usr/local/lib/R
COPY --from=r-dependencies   /usr/local/bin/R* /usr/local/bin/

# Configure Java and R library paths after copying R
RUN ARCH=$(dpkg --print-architecture) && \
    echo "Configuring for architecture: ${ARCH}" && \
    echo "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-${ARCH}" >> /etc/environment && \
    echo "export LD_LIBRARY_PATH=/usr/lib/jvm/java-17-openjdk-${ARCH}/lib/server:/usr/local/lib/R/lib:\${LD_LIBRARY_PATH}" >> /etc/environment && \
    # Configure ldconfig for both Java and R libraries
    echo "/usr/lib/jvm/java-17-openjdk-${ARCH}/lib/server" > /etc/ld.so.conf.d/java.conf && \
    echo "/usr/local/lib/R/lib" > /etc/ld.so.conf.d/R.conf && \
    ldconfig && \
    # Verify R libraries are accessible
    echo "R library path contents:" && \
    ls -la /usr/local/lib/R/lib/ || echo "R lib directory not found"

COPY --from=python-dependencies /opt/venv /opt/venv

# Set up environment variables for the runtime
RUN echo '. /etc/environment' >> /etc/bash.bashrc && \
    echo '. /etc/environment' >> /etc/profile && \
    # Add R library path to environment
    echo "export R_HOME=/usr/local/lib/R" >> /etc/environment && \
    echo "export R_LIBS_SITE=/usr/local/lib/R/site-library" >> /etc/environment && \
    echo "export R_LIBS_USER=/usr/local/lib/R/site-library" >> /etc/environment

# Optional sanity checks with architecture info
RUN . /etc/environment && \
    echo "=== Architecture Information ===" && \
    echo "Architecture: $(dpkg --print-architecture)" && \
    echo "JAVA_HOME: ${JAVA_HOME}" && \
    echo "R_HOME: ${R_HOME}" && \
    echo "LD_LIBRARY_PATH: ${LD_LIBRARY_PATH}" && \
    echo "=== Library Path Verification ===" && \
    echo "Contents of /usr/local/lib/R/lib:" && \
    ls -la /usr/local/lib/R/lib/ 2>/dev/null || echo "R lib directory not accessible" && \
    echo "Checking for libR.so:" && \
    find /usr/local/lib -name "libR.so*" 2>/dev/null || echo "libR.so not found" && \
    echo "Current ldconfig cache:" && \
    ldconfig -p | grep -E "(libR|java)" || echo "No R or Java libraries in ldconfig cache" && \
    if [ -d "${JAVA_HOME}" ]; then \
        echo "JAVA_HOME directory exists: ${JAVA_HOME}"; \
        ls -la "${JAVA_HOME}/" | head -5; \
    else \
        echo "JAVA_HOME directory not found: ${JAVA_HOME}"; \
    fi && \
    echo "=== Java Version Check ===" && \
    java -version 2>&1 || echo "Java not in PATH" && \
    echo "=== R Basic Test ===" && \
    R --version 2>&1 | head -3 || echo "R not working" && \
    echo "=== R Library Test ===" && \
    R --slave -e "cat('R is working. Base packages loaded successfully.\n')" 2>&1 || echo "R base packages failed to load" && \
    echo "=== Python Environment Check ===" && \
    python3.9 -c "import sys, platform; print('Python', sys.version); print('OS', platform.platform()); print('Architecture:', platform.machine())" && \
    if python3.9 -c "import rpy2" 2>/dev/null; then \
        python3.9 -c "import rpy2; print('rpy2 version:', rpy2.__version__)"; \
    else \
        echo "rpy2 not available or not installed"; \
    fi

WORKDIR /app
COPY . .

# Source environment variables and run the application
CMD ["/bin/bash", "-c", "source /etc/environment && python3.9 main.py"]