# config valid for current version and patch releases of Capistrano
lock "~> 3.17.1"

set :application, "tagbase-server"
set :repo_url, "https://github.com/tagbase/tagbase-server.git" # git@github.com:tagbase/tagbase-server.git"

# Default branch is :master
# ask :branch, `git rev-parse --abbrev-ref HEAD`.chomp

# Default deploy_to directory is /var/www/my_app_name
set :deploy_to, "/home/ubuntu/tagbase-server"

# Default value for :format is :airbrussh.
# set :format, :airbrussh

# You can configure the Airbrussh format using :format_options.
# These are the defaults.
# set :format_options, command_output: true, log_file: "log/capistrano.log", color: :auto, truncate: :auto

# Default value for :pty is false
set :pty, true

# Default value for :linked_files is []
# append :linked_files, "config/database.yml", 'config/master.key'

# Default value for linked_dirs is []
# append :linked_dirs, "log", "tmp/pids", "tmp/cache", "tmp/sockets", "tmp/webpacker", "public/system", "vendor", "storage"

# Default value for default_env is {}
# set :default_env, { path: "/opt/ruby/bin:$PATH" }
set :default_env, { 'COMPOSE_PROJECT_NAME': "tagbase" }

# Default value for local_user is ENV['USER']
# set :local_user, -> { `git config user.name`.chomp }

# Default value for keep_releases is 5
# set :keep_releases, 5
#
set :stages, ["staging", "production"]
set :default_stage, "staging"


# Uncomment the following to require manually verifying the host key before first deploy.
# set :ssh_options, verify_host_key: :secure

namespace :deploy do

  desc 'Create certificates for NGINX'
  task :copy_env_app do
    on roles(:app) do
      execute '(cp /home/ubuntu/tagbase-server/.env /home/ubuntu/tagbase-server/current;)'
      execute '(mkdir -p /home/ubuntu/tagbase-server/current/services/nginx/ssl;)'
      execute '(cd /home/ubuntu/tagbase-server/current/services/nginx/ssl; openssl req -x509 -nodes -newkey rsa:2048 -keyout key.pem -out cert.pem -sha256 -days 365 -subj "/C=GB/ST=London/L=London/O=Alros/OU=IT Department/CN=localhost")'
    end
  end

  desc 'Rebuild dependencies'
  task :rebuild_deps do
    on roles(:app) do
      # Your restart mechanism here, for example:
      execute '(cd /home/ubuntu/tagbase-server/current; docker-compose build --build-arg NGINX_PASS="tagbase" --build-arg NGINX_USER="tagbase" --build-arg PGBOUNCER_PORT=“6432”  --build-arg POSTGRES_PASSWORD="tagbase" --build-arg POSTGRES_PORT="5432")'

      #execute "(cd /home/ubuntu/tagbase-server/current; sudo docker-compose down; sudo docker-compose -p'tagbase' up -d)"
      execute "(cd /home/ubuntu/tagbase-server/current; sudo docker-compose down; sudo docker-compose up -d)"
    end
  end

  task :restart_app do
    on roles(:app) do
      # Your restart mechanism here, for example:
      execute "(cd /home/ubuntu/tagbase-server/current; sudo docker-compose down)"
      execute "(cd /home/ubuntu/tagbase-server/current; sudo docker-compose up -d)"
    end
  end
  after :deploy, 'deploy:copy_env_app'
  after :deploy, 'deploy:rebuild_deps'
  after :deploy, 'deploy:restart_app'
end


