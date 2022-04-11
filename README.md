
# wipac-dev-py-setup-action
GitHub Action Package for Automating Python-Package Setup

Writes needed config to publish a package to PyPI.

## Steps to Use

1. Update setup.cfg with `[wipac:cicd_setup_builder]` section:
    ```
     [wipac:cicd_setup_builder]
     pypi_name = wipac-dev-tools
     python_min = 3.6
     keywords_spaced = python tools utilities
    ```

   Required:
   * pypi_name - PyPI package name
   * python_min - minimum Python version

   Optional:
   * package_dirs - space-separated list of directories to package
   * python_max - maximum Python version
   * keywords_spaced - space-separated keyword list

   Python package dependencies go in [options] section:
    ```
     [options]
     install_requires =
        package-a
        package-b
    ```
2. Use as a step in a GitHub Action:
    ```
      py-setup:
        runs-on: ubuntu-latest
        steps:
          - name: checkout
            uses: actions/checkout@v3
            with:
              token: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
          - uses: WIPACrepo/wipac-dev-py-setup-action@v1
    ```
