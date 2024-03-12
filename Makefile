
buildprod:
	docker build -t registry.digitalocean.com/xf86/twitchrat:latest .

builddev:
	docker build -t registry.digitalocean.com/xf86/twitchrat-dev:latest .

pushprod:
	docker push registry.digitalocean.com/xf86/twitchrat:latest

pushdev:
	docker push registry.digitalocean.com/xf86/twitchrat-dev:latest

rundev: builddev
	docker run -ti --rm registry.digitalocean.com/xf86/twitchrat:latest -s quin69 --influxdb-database quin69chat

proddeploy:
	kubectl delete -n ratstats -f kubernetes/pod.yaml || true
	kubectl create -n ratstats -f kubernetes/pod.yaml

devdeploy: builddev pushdev
	kubectl delete -n ratstats -f kubernetes/pod-dev.yaml || true
	kubectl create -n ratstats -f kubernetes/pod-dev.yaml

