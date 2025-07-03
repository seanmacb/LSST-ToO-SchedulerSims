#!/usr/bin/env python3

from adc.errors import KafkaException
import argparse
from confluent_kafka import KafkaError
from datetime import timedelta
import hop
import time

def messages_outstanding(producer):
	c = 0;
	for trecord in producer.topics.values():
		c += len(trecord.producer._producer)
	return c

parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--format",
    choices=hop.io.Deserializer.__members__,
    default=hop.io.Deserializer.AVRO.name,
    help="Specify the message format. Defaults to BLOB for an unstructured message.",
)
parser.add_argument("url", type=str)
parser.add_argument("message", metavar="MESSAGE", nargs="*")

args = parser.parse_args()
loader = hop.io.Deserializer[args.format]
stream = hop.io.Stream()
#, produce_backoff_time=timedelta(seconds=1)
with stream.open(args.url, "w", compression_type="gzip", produce_timeout=timedelta(seconds=300)) as s:
	print("publishing messages to stream")
	in_flight=0
	total_queued=0
	for message_file in args.message:
		message = loader.load_file(message_file)
		time.sleep(.01)
		s.write(message)
		in_flight+=1
		total_queued+=1
		if total_queued%10 == 0:
			in_flight = messages_outstanding(s)
		elif in_flight>=100:
			in_flight = messages_outstanding(s)
		if total_queued%100 == 0:
			print(f"{total_queued} messages queued, {in_flight} in queue")
		while in_flight>=100:
			print(f"Queued {total_queued} messages, {in_flight} in queue")
			#time.sleep(1)
			try:
				in_flight = s.flush()
			except KafkaException as ex:
				if ex.error.code() == KafkaError._MSG_TIMED_OUT:
					in_flight = messages_outstanding(s)
				else:
					raise
			print(f"  Now {in_flight} in queue")
	while in_flight>0:
		try:
			in_flight = s.flush()
		except KafkaException as ex:
			if ex.error.code() == KafkaError._MSG_TIMED_OUT:
				in_flight = messages_outstanding(s)
			else:
				raise
		print(f"  Now {in_flight} in queue")
		if in_flight>0:
			time.sleep(1)
