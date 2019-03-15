build:
	docker build . --tag guildai/guildai

exec: build
	docker run -it guildai/guildai

push: build
	docker push guildai/guildai
