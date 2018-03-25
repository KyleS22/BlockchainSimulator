CC = protoc
CFLAGS = --python_out=..

.PHONEY: all clean

all:
	$(CC) $(CFLAGS) ./protos/*.proto

clean:
	rm -f *.py
