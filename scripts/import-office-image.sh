#!/bin/sh
set -eu
image_archive=${1:-build/office-portal.tar}
ssh -o BatchMode=yes office-image-host import-office-image < "$image_archive"
