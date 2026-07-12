#pytest.ini
[pytest] testpaths = tests
#Only look for tests in the 'tests' folder

    asyncio_mode = auto
#pytest - asyncio : automatically handle async test functions
#without needing @pytest.mark.asyncio on every one

        markers =
            unit : fast unit tests,
         no external dependencies
                 integration : tests that need Redis running
                                   slow : end -
                                          to - end tests that hit real APIs
#These custom markers can be used to run subsets:
#pytest - m unit        → only unit tests
#pytest - m "not slow"  → everything except slow tests

                                                   log_cli = true log_cli_level = WARNING
#Show WARNING and above logs during test runs