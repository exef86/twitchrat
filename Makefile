
build:
	docker build -t registry.digitalocean.com/xf86/twitch-collectors:latest .

push:
	docker push registry.digitalocean.com/xf86/twitch-collectors:latest

redeploy:
	kubectl delete -n ratstats -f kubernetes/pod.yaml
	kubectl create -n ratstats -f kubernetes/pod.yaml

