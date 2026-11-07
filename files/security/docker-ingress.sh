#!/bin/sh
set -eu

external_interface="${1:?Укажи внешний сетевой интерфейс}"
chain="NEXTCLOUD-INGRESS"

test -d "/sys/class/net/$external_interface"

for firewall in iptables ip6tables; do
    "$firewall" -w -S DOCKER-USER >/dev/null

    if ! "$firewall" -w -S "$chain" >/dev/null 2>&1; then
        "$firewall" -w -N "$chain"
    fi

    "$firewall" -w -F "$chain"

    "$firewall" -w -A "$chain" \
        -m conntrack --ctstate ESTABLISHED,RELATED \
        -j RETURN

    for port in 80 443; do
        "$firewall" -w -A "$chain" \
            -p tcp \
            -m conntrack --ctdir ORIGINAL --ctorigdstport "$port" \
            -j RETURN
    done

    "$firewall" -w -A "$chain" -j DROP

    if ! "$firewall" -w -C DOCKER-USER \
        -i "$external_interface" -j "$chain" 2>/dev/null; then
        "$firewall" -w -I DOCKER-USER 1 \
            -i "$external_interface" -j "$chain"
    fi
done
