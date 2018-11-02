# protocc

[![Build Status](https://circleci.com/gh/windmilleng/protocc/tree/master.svg?style=shield)](https://circleci.com/gh/windmilleng/protocc)

Stop worrying about how to install the right protoc version and managing protoc plugins!

Compile protobufs (protoc) inside a container (protocc)!

## Usage

In a directory with `.proto` files, run:

```
python protocc.py --out go
```

protocc will generate all the `.pb.go` files inside the container, then copy them
to your local filesystem, printing where it puts each file.

## Requirements

- [Docker](https://docs.docker.com/install/)
- Python

We've manually tested on Python 2 and 3.

## Future Work

Currently this only generates Go protobufs, but could be easily modified to
support other target languages. We welcome your feature requests, or even better,
contributions!

## License

Copyright 2018 Windmill Engineering

Licensed under [the Apache License, Version 2.0](LICENSE)