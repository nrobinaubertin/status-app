.PHONY: rock charm pack integration

STATUS_APP_CHARM_FILE ?= $(shell ls -t charm/status-app_*.charm 2>/dev/null | head -n 1)
STATUS_APP_ROCK_IMAGE ?=
STATUS_APP_BUILD_ARTIFACTS ?=

rock:
	rockcraft pack

charm:
	cd charm && charmcraft pack

pack: rock charm

integration:
	STATUS_APP_CHARM_FILE="$(STATUS_APP_CHARM_FILE)" \
	STATUS_APP_ROCK_IMAGE="$(STATUS_APP_ROCK_IMAGE)" \
	STATUS_APP_BUILD_ARTIFACTS="$(STATUS_APP_BUILD_ARTIFACTS)" \
	tox -e charm-integration
