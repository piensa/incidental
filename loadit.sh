python incidents.py --count 1000 | /bin/kafka-console-producer.sh --broker-list 10.0.1.155:1025,10.0.2.52:1025,10.0.2.212:1025 --topic fire
