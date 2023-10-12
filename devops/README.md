Installing tools
----------------
1. Ansible
2. Capistrano

Installing server tools
-----------------------
- Modify the server IP where tagbase-server will be deployed.
- Open the `devops/inventory` file and modify the IPs specified under `prod_server` and `dev_servers` tags.
- Run the following ansible command
```
ansible-playbook -i ./inventory tagserver_playbook.yaml
```

Deploying tagbase-server
------------------------
- Run the following capistrano to deploy into the staging server
```
cap staging deploy
```

