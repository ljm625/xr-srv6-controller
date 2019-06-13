#!/bin/bash
#Launch etcd in global-vrf network
ip netns exec global-vrf "$@"
