#!/bin/bash
set -euo pipefail

fatal() {
    echo -e "\n❌ FATAL: $*" >&2
    exit 1
}

jq_required() {
    local json="$1"
    local field="$2"

    local value
    value=$(echo "$json" | jq -r "$field") || \
        fatal "Missing required field: $field"

    [[ -n "$value" && "$value" != "null" ]] || \
        fatal "Required field is empty: $field"

    echo "$value"
}
