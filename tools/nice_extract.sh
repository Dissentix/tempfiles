#!/bin/bash

# Check if a file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

# Check if the file exists
if [ ! -f "$1" ]; then
    echo "Error: File '$1' not found."
    exit 1
fi

# Extract domain name from the file name (removing the last extension)
domain_name=$(echo "$1" | sed 's/\.[^.]*$//')

# Notify user about extraction start
echo "Processing file: $1"
echo "Extracted domain name: $domain_name"

# Extract parameters (without values)
echo "Extracting parameters..."
grep -oP '([?&])(\w+)(?==)' "$1" | sed 's/[&?]//g' | sort -u > "${domain_name}.parameters"
echo "Parameters saved to ${domain_name}.parameters"

# Extract domains (removing protocol and ports)
echo "Extracting unique domains..."
grep -oP 'https?://([^/]+)' "$1" | sed 's|https\?://||' | sed 's|:.*||' | sort -u > "${domain_name}.urls"
echo "Domains saved to ${domain_name}.urls"

# Notify user about completion
echo "Extraction complete!"
