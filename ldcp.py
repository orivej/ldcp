#!/usr/bin/env python

import argparse
import os
import shutil
import subprocess

LDLINUX = {
    'elf32-i386': 'ld-linux.so.2',
    'elf64-x86-64': 'ld-linux-x86-64.so.2'
}

def collect(roots):
    paths = {}

    def recur(path):
        filename = os.path.basename(path)
        if filename in paths:
            return
        paths[filename] = path

        try:
            out = subprocess.check_output(['ldd', path])
        except subprocess.CalledProcessError:
            return

        for line in out.splitlines():
            args = line.split()
            if 'linux-vdso.so.1' in args or 'linux-gate.so.1' in args or 'statically' in args:
                continue

            if '=>' in args:
                pos = args.index('=>')
                arg = args[pos + 1]
                recur(arg)

            recur(args[0])

    for root in roots:
        recur(root)

    return paths


def save(paths, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)

    for filename, path in paths.iteritems():
        dstpath = os.path.join(dst, filename)
        if not os.path.exists(dstpath) or not os.path.samefile(path, dstpath):
            shutil.copy(path, dstpath)
        os.chmod(dstpath, 0755)

        if filename in LDLINUX.values():
            continue

        try:
            headers = subprocess.check_output(['objdump', '-h', dstpath]).split()
        except subprocess.CalledProcessError:
            continue

        if 'format' not in headers[:-1]:
            continue

        ldlinux = LDLINUX[headers[headers.index('format') + 1]]
        args = ['patchelf', '--set-rpath', '$ORIGIN']
        if '.interp' in headers:
            args += ['--set-interpreter', './' + ldlinux]
        subprocess.check_call(args + [dstpath])

        if '.so' not in filename:
            os.rename(dstpath, dstpath + '.bin')
            with open(dstpath, 'w') as f:
                f.write('#!/bin/sh\n')
                f.write('d="$(dirname "$(readlink -f "$0")")"\n')
                f.write('exec "$d/{}" "$d/{}" "$@"\n'.format(ldlinux, filename + '.bin'))
            os.chmod(dstpath, 0755)


def main():
    os.environ['LANG'] = 'C'
    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg('dst')
    arg('path', nargs='+')
    args = parser.parse_args()
    paths = collect(args.path)
    save(paths, args.dst)


if __name__ == '__main__':
    main()
