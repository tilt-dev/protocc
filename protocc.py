#!/usr/bin/env python

import argparse
import os
import os.path
import subprocess

PROTOC_VERSION = '3.6.1'
PROTOC_GEN_GO_VERSION = 'v1.2.0'
GO_VERSION = '1.11'

def protoc_install_cmds():
  return [
    "RUN apt update && apt install unzip",
    "ENV PROTOC_VERSION {0}".format(PROTOC_VERSION),
    " && \\\t\n".join([
      ("RUN wget https://github.com/google/protobuf/releases/download/" +
       "v${PROTOC_VERSION}/protoc-${PROTOC_VERSION}-linux-x86_64.zip"),
      "unzip protoc-${PROTOC_VERSION}-linux-x86_64.zip -d protoc",
      "mv protoc/bin/protoc /usr/bin/protoc",
    ])
  ]

def golang_base_cmds():
  return [
    "FROM golang:{0}".format(GO_VERSION),
  ]

def golang_install_cmds():
  gopath = subprocess.check_output(["go", "env", "GOPATH"]).decode('utf-8').strip()
  return [
    "ENV GOPATH {0}".format(gopath),
    "ENV PATH=\"{0}/bin:${{PATH}}\"".format(gopath),
    "ENV PROTOC_GEN_GO_VERSION {0}".format(PROTOC_GEN_GO_VERSION),
    " && \\\t\n".join([
      "RUN GOPATH=${GOPATH} mkdir -p ${GOPATH}/src/github.com/golang",
      "cd ${GOPATH}/src/github.com/golang",
      "git clone https://github.com/golang/protobuf",
      "cd protobuf",
      "git checkout ${PROTOC_GEN_GO_VERSION}",
      "go get ./protoc-gen-go",
    ])
  ]

def dirs_with_protos():
  dirs = []
  for dirpath, _, fnames in os.walk("./"):
    contains_protos = False
    for fname in fnames:
      if fname.endswith(".proto"):
        contains_protos = True
        break

    if contains_protos:
      dirs.append(dirpath)

  return dirs

def golang_dirs_with_protos():
  dirs = dirs_with_protos()
  return [d for d in dirs if "/vendor/" not in d]

def workdir_cmds():
  return ["WORKDIR {0}".format(os.getcwd())]

def add_cmds(dirs):
  cmds = []
  for dirname in dirs:
    cmds.append("ADD {0}/*.proto {0}/".format(dirname))
  return cmds

def golang_run_cmds(dirs):
  cmds = []
  for dirname in dirs:
    cmds.append(("RUN protoc --go_out=plugins=grpc:${{GOPATH}}/src " +
                 "-I${{GOPATH}}/src {0}/*.proto").format(abspath(dirname)))
  return cmds

def entrypoint_cmd(pattern):
  return "ENTRYPOINT find {0} -name '{1}'".format(os.getcwd(), pattern)

def go_cmds(dirs):
  return (
    golang_base_cmds() +
    protoc_install_cmds() +
    golang_install_cmds() +
    workdir_cmds() +
    add_cmds(dirs) +
    golang_run_cmds(dirs) +
    [entrypoint_cmd("*.pb.go")]
    )

def check_call_with_stdin(script, stdin):
  print('$ {0}'.format(script))
  proc = subprocess.Popen(script, shell=True, stdin=subprocess.PIPE)
  proc.communicate(input=stdin.encode())
  if proc.returncode:
    raise Exception("Failed: " + script)

def call(script):
  print('$ {0}'.format(script))
  return subprocess.call(script, shell=True)

def check_call(script):
  print('$ {0}'.format(script))
  return subprocess.check_call(script, shell=True)

def check_output(script):
  print('$ {0}'.format(script))
  return subprocess.check_output(script, shell=True)

def abspath(path):
  return os.path.normpath(os.path.join(os.getcwd(), path))

def run_cmds(cmds):
  check_call_with_stdin("docker build -t tmp/protocc -f - .", stdin="\n".join(cmds))
  call("docker rm protocc")

  output = check_output("docker run --name protocc tmp/protocc").decode('utf-8').strip()
  print(output)

  files = [f.strip() for f in output.split("\n") if f.strip()]
  for file in files:
    check_call("docker cp protocc:{0} {0}".format(file))

  check_call("docker rm protocc")

def main():
  args = parse_args()
  outs = args.out
  if not outs:
    print("Must choose an output language with --out")
    exit(1)

  for lang in outs:
    if lang == "go":
      dirs = golang_dirs_with_protos()
      cmds = go_cmds(dirs)
      run_cmds(cmds)

  exit(0)

def parse_args():
  parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Compile protobufs (protoc) inside a container (protocc)!')
  parser.add_argument('--out',
                      type=str,
                      nargs='+',
                      choices=['go'],
                      help='list of languages to output. Example: `--out go`')
  return parser.parse_args()

if __name__ == "__main__":
  main()
