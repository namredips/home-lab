#!/bin/bash
# This script adds an encrypted variable to the specified key vault.

set -o errexit -o pipefail -o noclobber -o nounset

Help()
{
   # Display Help
   echo "Function to encrypt variable and append to var file. "
   echo 
   echo "Syntax: test [-n|f|h]"
   echo "options:"
   echo "n     Name of the variable to append ."
   echo "f     Path to file to append the variable."
   echo "s     The string to encrypt."
   echo "h     Print this Help."
   echo
}

# Get the options
OPTIONS=n:f:s:h
LONGOPTS=var_name:,var_file:,string:,help
VALID_OPTIONS=$(getopt --options=$OPTIONS --longoptions=$LONGOPTS --name "$0" -- "$@")
eval set -- "$VALID_OPTIONS"

while [ : ]; do
   case "$1" in
      -h|--help) # display Help
         Help
         shift
         exit
         ;;
      -n|--var_name) # Enter a variable name for encrypted variable
         VAR_NAME=$2
         shift 2
         ;;
      -f|--var_file) # Enter file path for where to append the encrypted variable
         FILE_PATH=$2
         shift 2
         ;;
      -s|--string) # Enter file path for where to append the encrypted variable
         STRING=$2
         shift 2
         ;;
      --) # arguments
         shift
         break
         ;;
      *) # set defaults
         ;;
   esac
done

VAR_NAME=${VAR_NAME:-$1}
FILE_PATH=${FILE_PATH:-"inventory/group_vars/all/all.yml"}
STRING=${STRING:-$3}


ansible-vault encrypt_string --vault-password-file ~/.vault_pass.txt --n $VAR_NAME $STRING >> $FILE_PATH
