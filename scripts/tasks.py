import time

from fabric import Connection, SerialGroup, ThreadingGroup
from invoke import task

def get_gcloud_ips(c, keyword = "prod-"):
    # parse gcloud CLI to get internalIP -> externalIP mapping    
    gcloud_output = c.run("gcloud compute instances list").stdout.splitlines()[1:]
    gcloud_output = map(lambda s: s.split(), gcloud_output)
    ips = [
        # internal ip and external ip are last 2 tokens in each line
        (line[-2],line[-3])
        for line in gcloud_output if line[-1] == "RUNNING" and(keyword is None or keyword in line[0])
    ]
    print("IPs: ", ips)
    return ips

@task
def build(c, setup = False):

    ips = get_gcloud_ips(c)
    ext_ips = [ip[0] for ip in ips]
    group = ThreadingGroup(*ext_ips)

    if setup:
        group.run("sudo apt-get update && sudo apt-get install libssl-dev libuv1-dev ansible cmake rsync -y")
    print("Cloning/building repo...")

    group.run("git clone --recursive https://github.com/Hoooao/libhotstuff.git hotstuff", warn=True)
    group.run("cd hotstuff && git pull && git checkout main &&  cmake -DCMAKE_BUILD_TYPE=Debug -DBUILD_SHARED=ON -DHOTSTUFF_PROTO_LOG=ON -DCMAKE_CXX_FLAGS='-g -DHOTSTUFF_ENABLE_BENCHMARK' && make -j4")

@task
def setup(c):
    ips = get_gcloud_ips(c, keyword="replica")
    with c.cd("deploy"):
        # write each pair in ips to a file in ./scripts/deploy/replica.txt
        with open("./deploy/replicas.txt", "w") as f:
            for ip in ips:
                f.write("    ".join(ip) + "\n")
                
        ips = get_gcloud_ips(c, keyword="client")
        with open("./deploy/clients.txt", "w") as f:
            for ip in ips:
                f.write(ip[0] + "\n")
                f.write(ip[0] + "\n")
                f.write(ip[0] + "\n")
                f.write(ip[0] + "\n")
                f.write(ip[0] + "\n")
                f.write(ip[0] + "\n")
                f.write(ip[0] + "\n")
                f.write(ip[0] + "\n")
        c.run("./gen_all.sh")
    return

@task
def run(c, run_prefix=  "myrun1"):
    with c.cd("deploy"):
        print("Running... ",f"./run.sh new {run_prefix}")
        c.run(f"./run.sh new {run_prefix}")
        print("Running... ",f"./run_cli.sh new {run_prefix}_cli")
        c.run(f"./run_cli.sh new {run_prefix}_cli")

def stop_cli_and_rep_and_fetch_results(c, run_prefix):
    with c.cd("deploy"):
        c.run(f"./run_cli.sh stop {run_prefix}_cli")
        c.run(f"./run.sh stop {run_prefix}")
        c.run(f"./run_cli.sh fetch {run_prefix}_cli")
        
# TODO: make block_size a parameter
# invoke run-multiple  -a 260,300,400,500,600
@task
def run_multiple(c, async_nums):
    async_nums = async_nums.split(",")
    for i in async_nums:
        with open("./deploy/group_vars/clients.yml", "w") as f:
            f.write(f"""---
    bin_name: "hotstuff-client"
    # total number of commands
    max_iter: 2000000
    # number of concurrently outstanding requests (commands)
    max_async: {i}
    """)
        
        run_name = f"ben_4rep2cli_1000blk_4_4_8_{i}a_tls"
        run(c, run_name)
        time.sleep(18)
        stop_cli_and_rep_and_fetch_results(c, run_name)

    
        
@task
def stop(c, run_prefix= "myrun1"):
    # with c.cd("deploy"):
    #     c.run(f"./run_cli.sh stop {run_prefix}_cli")
    #     c.run(f"./run.sh stop {run_prefix}")
    ips = get_gcloud_ips(c)
    ext_ips = [ip[0] for ip in ips]
    group = ThreadingGroup(*ext_ips)
    group.run("killall -9 hotstuff-app", warn=True)
    group.run("killall -9 hotstuff-client", warn=True)

@task
def rm_testbed(c):
    ips = get_gcloud_ips(c)
    ext_ips = [ip[0] for ip in ips]
    group = ThreadingGroup(*ext_ips)
    group.run("rm -rf testbed")