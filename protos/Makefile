CC = protoc
CFLAGS = --python_out=.

.PHONEY: all clean

all: block_pb2.py

%_pb2.py: %.proto
	$(CC) $(CFLAGS) $<

clean:
	rm -f *.py
