#!/usr/bin/awk -f
BEGIN { FS = ":" }
{ if ($3 >= 1000 && $1 != "nobody") printf "%s\n", $1 }
