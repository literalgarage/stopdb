#!/bin/sh

uv pip freeze | grep -v file:/// > requirements.txt