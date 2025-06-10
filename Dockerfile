FROM python:3.11-slim

# Install system packages and R
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    r-base \
    r-base-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    git && \
    rm -rf /var/lib/apt/lists/*

# Ensure a persistent site library for installed R packages
RUN mkdir -p /usr/local/lib/R/site-library
ENV R_LIBS=/usr/local/lib/R/site-library \
    R_LIBS_USER=/usr/local/lib/R/site-library \
    R_HOME=/usr/lib/R

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy code into container
COPY . /app
WORKDIR /app

# Install required R packages
COPY install_r_packages.R /tmp/install_r_packages.R
RUN Rscript /tmp/install_r_packages.R

CMD ["python", "main.py"]
