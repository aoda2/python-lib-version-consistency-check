docker container prune 
docker image rm -f $(docker image ls | grep "^<none>" | awk "{print $3}")