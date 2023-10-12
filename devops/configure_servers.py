import os
import subprocess
import argparse


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tagbase-server-home', type=str)
    parser.add_argument('--installation-user', type=str)
    parser.add_argument('--prod-servers', type=str, nargs='*')
    parser.add_argument('--dev-servers', type=str, nargs='*')
    parser.add_argument('--dev-servers-sshkey-path', type=str)
    parser.add_argument('--prod-servers-sshkey-path', type=str)
    return vars(parser.parse_args())


def log_tb(msg):
    print("[TAGBASE] {}".format(msg))


def create_ansible_servers_file(inventory_file_path, prod_servers, dev_servers, installation_user, dev_servers_sshkey_path, prod_servers_sshkey_path):
    with open(inventory_file_path, 'w') as inv_file:
        if prod_servers != None:
            inv_file.write("[prod_servers]\n")
        for prod_server in prod_servers:
            inv_file.write("{}\n".format(prod_server))
        inv_file.write("[prod_servers:vars]\n")
        inv_file.write("ansible_user={}\n".format(installation_user))
        inv_file.write("ansible_ssh_private_key_file={}\n".format(prod_servers_sshkey_path))

        if dev_servers != None:
            inv_file.write("[dev_servers]\n")
        for dev_server in dev_servers:
            inv_file.write("{}\n".format(dev_server))
        inv_file.write("[dev_servers:vars]\n")
        inv_file.write("ansible_user={}\n".format(installation_user))
        inv_file.write("ansible_ssh_private_key_file={}\n".format(dev_servers_sshkey_path))

    log_tb("Completed writing {}".format(inventory_file_path))


def run_ansible_inventory_file(tagserver_home, inventory_file_path):
    playbook_file_path = "{}/tagserver_playbook.yaml".format(tagserver_home)
    ansible_cmd = "ansible-playbook -i {} {} -v".format(inventory_file_path, playbook_file_path)
    subprocess.run(ansible_cmd, shell=True)
    log_tb("Completed configuring servers")


if __name__ == "__main__":
    args = handle_args()
    tagbase_server_home = args['tagbase_server_home']
    tagbase_server_devops_home = '{}/{}'.format(tagbase_server_home, 'tagbase-server/devops')
    inventory_file_path = '{}/inventory_2'.format(tagbase_server_devops_home)
    create_ansible_servers_file(inventory_file_path, args['prod_servers'], args['dev_servers'], args['installation_user'], args['dev_servers_sshkey_path'], args['prod_servers_sshkey_path'])
    #run_ansible_inventory_file(tagserver_home, inventory_file_path)
