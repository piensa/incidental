python incidents.py --count 200 | /bin/kafka-console-producer.sh --broker-list 10.0.2.186:1025,10.0.2.190:1025,10.0.1.47:1025 --topic fire
