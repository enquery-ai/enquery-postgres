# Use the official PostgreSQL image as a base
FROM postgres:15

# Install build dependencies and required packages
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-15 \
    libicu-dev \
    cmake \
    libkrb5-dev \
    libssl-dev \
    flex \
    bison \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install pgvector
RUN git clone https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make \
    && make install

# Install Apache AGE
RUN git clone https://github.com/apache/age.git \
    && cd age \
    && git checkout PG15 \
    && make \
    && make install

# Install TimescaleDB
RUN git clone https://github.com/timescale/timescaledb.git \
    && cd timescaledb \
    && git checkout 2.10.1 \
    && ./bootstrap \
    && cd build && make \
    && make install

# Add extensions to postgresql.conf
RUN echo "shared_preload_libraries = 'timescaledb,vector,age'" >> /usr/share/postgresql/postgresql.conf.sample

# Copy initialization script
COPY init.sql /docker-entrypoint-initdb.d/