# coauthorcheck Action

Marketplace-ready GitHub Action for validating `Co-authored-by` trailers with `coauthorcheck`.

This repository is meant to be published separately from the main `coauthorcheck` Python package repo because GitHub Marketplace actions work best from a dedicated public repository with a root `action.yml`.

## Usage

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0

  - name: Validate branch commits
    uses: simoncraf/coauthorcheck-action@v0.1.0
    with:
      package-version: "0.5.0"
      range: origin/main..HEAD
```

## Inputs

- `range`: required git revision range to validate
- `config`: optional config file path
- `format`: optional output format, `text` or `json`
- `python-version`: optional Python version used inside the action
- `package-version`: optional PyPI package version to install
- `working-directory`: optional working directory for running `coauthorcheck`

## Example Workflows

Validate commits introduced by a pull request:

```yaml
name: Validate Co-authored-by trailers on PR

on:
  pull_request:
    branches:
      - main

jobs:
  validate-commits:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Validate PR commits
        uses: simoncraf/coauthorcheck-action@v0.1.0
        with:
          package-version: "0.5.0"
          range: origin/${{ github.base_ref }}..HEAD
```

Validate commits introduced by branch pushes:

```yaml
name: Validate Co-authored-by trailers

on:
  push:
    branches:
      - "feature/**"
      - "feat/**"

jobs:
  validate-commits:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Validate branch commits
        uses: simoncraf/coauthorcheck-action@v0.1.0
        with:
          package-version: "0.5.0"
          range: origin/main..HEAD
```
