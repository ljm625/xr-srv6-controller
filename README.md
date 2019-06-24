# SRv6 controller docker for IOS-XR

This docker is used for：

1. Fetch SID info from ETCD database

2. Calculate Path by calling the XTC Rest API

3. Transform Path calculation result to Segment List

also provide API for application querying the data.

#### Usage:

On IOS XR Bash, exec
```bash
docker pull ljm625/xr-srv6-controller
docker run -itd --cap-add=SYS_ADMIN --cap-add=NET_ADMIN -v /var/run/netns:/var/run/netns ljm625/xr-srv6-controller -u #UserName -p #Password -i #EtcdIP -e #EtcdPort -x #XtcIP
```

replace # Part with the value in your environment：

For Example：
- XTC IP : 172.20.100.150
- XTC Username : cisco
- XTC Password : cisco
- Etcd IP : 172.20.100.150
- Etcd Port :2769

Then the command is:

```
docker run -itd   --cap-add=SYS_ADMIN   --cap-add=NET_ADMIN \
  -v /var/run/netns:/var/run/netns ljm625/xr-srv6-controller \
   -u cisco -p cisco -x 172.20.100.150 -i 172.20.100.150 -e 2769
```


Check the logs by `docker logs -f {container Name}` to check run status.