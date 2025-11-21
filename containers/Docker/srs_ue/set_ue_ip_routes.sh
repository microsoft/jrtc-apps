#!/bin/bash

# Function to set up 5G UE TUN routing automatically
setup_ue_routing() {
    local TUN_IF="tun_srsue"
    local UE_CIDR UE_IP UE_PREFIX UE_NET UE_GW

    # Extract IP and subnet
    UE_CIDR=$(ip -o -4 addr show dev "$TUN_IF" | awk '{print $4}')
    if [[ -z "$UE_CIDR" ]]; then
        echo "Error: $TUN_IF has no IPv4 address"
        return 1
    fi

    # Split into IP and prefix
    UE_IP=${UE_CIDR%/*}
    UE_PREFIX=${UE_CIDR#*/}

    # Compute network
    if command -v ipcalc >/dev/null 2>&1; then
        UE_NET=$(ipcalc -n "$UE_CIDR" 2>/dev/null | grep -i '^NETWORK=' | cut -d= -f2)
        if [[ -z "$UE_NET" ]]; then
            echo "Error: Could not compute network from $UE_CIDR"
            return 1
        fi
    else
        UE_NET=$(echo "$UE_IP" | awk -F. '{printf "%d.%d.%d.0/24\n",$1,$2,$3}')
        echo "Warning: ipcalc not found, using fallback network $UE_NET"
    fi

    # Default gateway assumed to be .1
    UE_GW="${UE_NET%.*}.1"

    # Create table 100 routes
    set -x
    ip route add "$UE_NET" dev "$TUN_IF" proto kernel scope link src "$UE_IP" table 100 2>/dev/null || {
        echo "Error: Route $UE_NET already exists or failed"
        set +x
        return 1
    }

    ip route add default via "$UE_GW" dev "$TUN_IF" table 100 2>/dev/null || {
        echo "Error: Default route via $UE_GW failed or already exists"
        set +x
        return 1
    }

    ip rule add from "$UE_IP" table 100 2>/dev/null || {
        echo "Error: Rule from $UE_IP failed or already exists"
        set +x
        return 1
    }
    set +x

    echo "Policy routing set for $TUN_IF: $UE_IP/$UE_PREFIX via $UE_GW"
    echo "To test data:   ping 8.8.8.8 -I $UE_IP"
    echo "            :   ping -f -I $UE_IP -M do 8.8.8.8"

    return 0
}

# Run the function and exit with its status
setup_ue_routing
exit $?
