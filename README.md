
# wipac-dev-py-setup-action
GitHub Action Package for Automating Python-Package Setup

Writes needed config (`setup.cfg`) for publishing a package to PyPI.

## Configuration Options

### Minimal (No PyPI Metadata)
This will generate the absolute minimal sections needed for making a release for your package.

1. You define:
    - `setup.cfg` with `[wipac:cicd_setup_builder]` section, like:
        ```
        [wipac:cicd_setup_builder]
        python_min = 3.6
        ```
2. Run as GitHub Action
3. You get:
    - `setup.cfg` with all the original sections *plus*
        + Fully-generated section(s):
            - `[semantic_release]`
        + Partially-generated/supplemented section(s):
            - `[metadata]`
                ```
                version = attr: my_pkg.__version__
                ```
            - `[options]`
                ```
                ...
                python_requires = >=3.6, <3.11
                packages = find:
                ```
            - `[options.package_data]`
                ```
                * = py.typed
                ```
            - `[options.packages.find]`
                ```
                exclude =
                    test
                    tests
                    doc
                    docs
                    resource
                    resources
                ```

### Enable Generating PyPI Metadata




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
   * package_dirs - space-separated list of directories to package (else, uses auto-detection)
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
          - uses: WIPACrepo/wipac-dev-py-setup-action@v1.#
    ```
