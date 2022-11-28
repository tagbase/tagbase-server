# config valid for current version and patch releases of Capistrano
lock "~> 3.17.1"

set :application, "tagbase-server"
set :repo_url, "git@github.com:tagbase/tagbase-server.git"

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

  task :copy_env_app do
    on roles(:app) do
      execute '(cp /home/ubuntu/tagbase-server/.env /home/ubuntu/tagbase-server/current;)'
    end
  end

  desc 'Rebuild dependencies'
  task :rebuild_deps do
    on roles(:app) do
      # Your restart mechanism here, for example:
      execute '(cd /home/ubuntu/tagbase-server/current; sudo docker-compose build)'
      #execute (cd /home/ubuntu/tagbase-server; docker-compose down; docker-compose up -d)
    end
  end

  task :restart_app do
    on roles(:app) do
      # Your restart mechanism here, for example:
      execute "(cd /home/ubuntu/tagbase-server/current; sudo docker-compose -p'tagbase' down)"
      execute "(cd /home/ubuntu/tagbase-server/current; sudo docker-compose -p'tagbase' up -d)"
    end
  end
  after :deploy, 'deploy:copy_env_app'
  after :deploy, 'deploy:rebuild_deps'
  after :deploy, 'deploy:restart_app'
end


