set -eo pipefail
rabbitmqctl eval '{ true, rabbit_app_booted_and_running } = { rabbit:is_booted(node()), rabbit_app_booted_and_running }
rabbitmqctl eval '{ true, rabbit_app_booted_and_running } = { rabbit:is_booted(node()), rabbit_app_booted_and_running }'
rabbitmqctl 
rabbitmqctl eval { true, rabbit_app_booted_and_running }
rabbitmqctl eval '{ true, rabbit_app_booted_and_running }'
rabbitmqctl eval
rabbitmqctl eval '{ true, rabbit_app_booted_and_running } = { rabbit:is_booted(node()), rabbit_app_booted_and_running }, { [], no_alarms } = { rabbit:alarms(), no_alarms }, [] /= rabbit_networking:active_listeners(), rabbitmq_node_is_healthy.'
rabbitmqctl eval '{ true, rabbit_app_booted_and_running } = { rabbit:is_booted(node()), rabbit_app_booted_and_running }, { [], no_alarms } = { rabbit:alarms(), no_alarms }, [] /= rabbit_networking:active_listeners(), rabbitmq_node_is_healthy.'
exit
