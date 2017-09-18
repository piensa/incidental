FROM mesosphere/kafka-client

# Install pandas
RUN \
    apt-get update && \
    apt-get install -y python-pip python-pandas && \
    rm -rf /var/lib/apt/lists/*

# Install Faker, Click, Fastavro
# FIXME: Use of pip and requirements.txt was abandandoned due to a weird crypto error.
RUN easy_install Faker click fastavro

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Define environment variable
ENV KAFKA_BROKER_LIST 127.0.0.1:1025
ENV KAFKA_TOPIC_NAME topic1

# Run app.py when the container launches
CMD ["python", "incidents.py", "|", "/bin/kafka-console-producer.sh", "--broker-list $KAFKA_BROKER_LIST", "--topic $KAFKA_TOPIC_NAME"]

