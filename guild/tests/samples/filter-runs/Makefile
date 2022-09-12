clean:
	find -name env | xargs rm -f
	find -name pip_freeze | xargs rm -f
	find -name opref | xargs sed -i -E "s/guildfile:.* (.*?) (.*)/test: '' \1 \2/"
	find -name op | xargs sed -i -E "s/PROJECT_DIR: .+/PROJECT_DIR: ''/"
