##########################
### Development Tools  ###
##########################

.PHONY: dev_format
dev_format: ## Format Python code
	$(call check_venv)
	$(call print_info_section,Formatting Python code)
	$(Q)black .
	$(Q)isort .
	$(call print_success,Code formatted)

.PHONY: dev_test_feed
dev_test_feed: ## Run the test_feed.py script
	$(call check_venv)
	$(call print_info,Running test_feed.py)
	$(Q)python feed_generators/test_feed.py
	$(call print_success,Test feed completed)

.PHONY: dev_check_feeds
dev_check_feeds: ## Check health of all generated feeds
	$(call check_venv)
	$(call print_info,Checking feed health)
	$(Q)python scripts/check_feeds.py --verbose
	$(call print_success,Feed health check completed)
