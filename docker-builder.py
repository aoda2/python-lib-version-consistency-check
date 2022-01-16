import docker
from docker import client
from docker.models.images import Image 

import subprocess
import re

import itertools
import pprint

samples = 30

def get_versions(package):
    err = subprocess.Popen(
        f"pip3 install {package}==", stderr=subprocess.PIPE,
        shell=True).stderr.readlines()
    errMsg = str(err)
    match = re.search("\(from versions:(.*)\)", errMsg)
    if match:
        return [x.strip() for x in match.group(1).split(',')]
    return []

def buildImage():
    image = {}
    client = docker.from_env()
    try:
        image, buildLog = client.images.build(path = "build/",
            quiet=False, tag="test_image:latest")
    except docker.errors.BuildError as e:
        return None, None

    return image, buildLog

def readReqiurements():
    packages = [] # [{name, vFrom, vTo}, ..]
    lines = []
    with open("requirements_tmp.txt") as f:
        lines = f.read().splitlines()
    for line in lines:
        name = line.split("==")[0]
        vFrom = line.split("==")[1].split(",")[0]
        vTo = line.split("==")[1].split(",")[1]
        packages.append({"name": name, "vFrom": vFrom, "vTo": vTo})
    return packages

def make_samples(py_versions, packages, samples):
    n = int(samples/len(py_versions)/len(packages) - 2)
    
    sample_lists =[]

    for package in packages:
        sample_list = []
        versions = get_versions(package["name"])

        iFrom = versions.index(package["vFrom"])
        # add iFrom        
        sample_list.append({"name": package["name"], "version": versions[iFrom]})
        iTo = versions.index(package["vTo"])

        if iFrom == iTo:
            continue

        for i in range(n):
            iTarget = int((iTo - iFrom)/(n + 1) * (i + 1)) + iFrom
            sample_list.append({"name": package["name"], "version": versions[iTarget]})

        # add iTo        
        sample_list.append({"name": package["name"], "version": versions[iTo]})
        sample_lists.append(sample_list)

    pprint.pprint(sample_lists)        

    l = py_versions
    for a in sample_lists:
        l = list(itertools.product(l, a))
    pprint.pprint(l)
    return l

def flatten(l):
    for el in l:
        if isinstance(el, tuple):
            yield from flatten(el)
        else:
            yield el

def main():

    py_versions = []
    with open("py_versions") as f:
        py_versions = f.read().splitlines()
    
    packages = readReqiurements()

    l = make_samples(py_versions, packages, samples)

    dockerfile = ""
    with open("Dockerfile.tmp") as f:
        dockerfile = f.read()

    res = []
    for x in l:
        r = {}
        z = list(flatten(x))
         # z[0] is py_version
        r["python"] = z[0]
        with open("build/Dockerfile", "w") as f:
            f.write(dockerfile.format(z[0]))
        with open("build/requirements.txt", "w") as f:
            for y in z[1:]:
                f.write(f'{y["name"]}=={y["version"]}\n')
                r[y["name"]] = y["version"]
        

        image, buildLog = buildImage()
        result = "Error" if image is None else "Success"
    
        print(str(z) + "\t->\t" + result)
        r["result"] = result
        res.append(r)
    pprint.pprint(res)

if __name__ == "__main__":
    main()